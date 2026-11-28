"""Supervise the two registered Round 38 GPU queues, with exact native exit witnesses."""

import argparse
import contextlib
import gzip
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import rapid_gpu as gpu
import word_table_lane as lane

MANIFEST = "83534f034bd19546448fad6e0437ecd4d4397ebb0b576ec9ddd3ee2ace331ce2"
SPARK = ("Q35", "Q36")
WINDOWS = ("G12r", "G16", "G14r", "G13r")


def check(root, old):
    gpu.check_stop(old)
    if (root / "STOP").exists():
        raise RuntimeError("Round 38 STOP")


def need_rows(old, manifest):
    groups = []
    for name, expected in (("ed", 24850), ("envent", 6600)):
        file = old / "inputs" / (name + ".jsonl.gz")
        gpu.require_pin(file, manifest["files"][file.name])
        with gzip.open(file, "rt", encoding="utf8") as stream:
            rows = [json.loads(line) for line in stream]
        if len(rows) != expected or any(set(r) != {"id", "text"} for r in rows):
            raise ValueError("Need input census or columns differ")
        groups.append(rows)
    if len({r["id"] for rows in groups for r in rows}) != 31450:
        raise ValueError("Repeated input identifier")
    return groups


def sample(items, salt, count):
    return sorted(items, key=lambda row: gpu.marks.digest(salt + row["id"]))[:count]


def spark_work(root, old, job, out, guard, groups):
    width = gpu.job_width(old)
    if job == "Q35":
        gpu.reader_arm(out, groups[0] + groups[1], "B", "need", width, guard, job, "B")
        return lane.read(out / "B/complete.json")
    prefix = root / "jobs/Q35"
    verified(prefix, lane.read(out / "owner.json")["registration"])
    items = sample(groups[0], "Q36:23:", 1000) + sample(groups[1], "Q36:23:", 500)
    # TP80 uses this same flock for its one-thread vector preparation.
    while True:
        guard.check()
        try:
            with lane.lease(old / "TP61-vector-cpu.lock"):
                try:
                    gpu.reader_arm(out, items, "C", "need", 1, guard, job, "C", 3500)
                except RuntimeError as exc:
                    if str(exc) != "Reader C leaves less than 15 GB available":
                        raise
                    lane.write(out / "C/skipped.json", {"reason": str(exc)})
            break
        except lane.Busy:
            time.sleep(15)
    probe = sample(items, "Q36:reword:23:", 1000)
    for kind in ("need2", "need3"):
        gpu.reader_arm(out, probe, "B", kind, width, guard, job, kind, 3500)
    return {
        p.parent.name: lane.read(p)
        for p in sorted(out.glob("*/*.json"))
        if p.name in {"complete.json", "skipped.json"}
    }


def verified(out, registration):
    released = lane.read(out / "released.json")
    owner = lane.read(out / "owner.json")
    if (
        released["exitCode"]
        or not released["childWaited"]
        or not released["sharedLeaseReacquired"]
        or released["owner"] != owner
        or owner["registration"] != registration
    ):
        raise ValueError("Prior job has no exact successful release")
    gpu.require_pin(
        out / "receipt.json", lane.read(out / "complete.json")["sourceReceiptPin"]
    )


def run(root, old, job, registration, cfg):
    check(root, old)
    with lane.lease(gpu.lock_path(old)):
        if lane.core.api("ps")["models"]:
            raise lane.Busy("Another resident is present")
        gpu.require_pin(old / "inputs/inputs.json", MANIFEST)
        if cfg["prompts"] != {
            k: gpu.marks.protocol(k) for k in ("need", "need2", "need3")
        }:
            raise ValueError("Need protocol differs from registration")
        out = root / "jobs" / job
        out.mkdir(parents=True, exist_ok=False)
        owner = {
            **lane.identity(),
            "job": job,
            "registration": registration,
            "at": lane.now(),
            "commit": cfg["commit"],
        }
        lane.write(out / "owner.json", owner)
        try:
            with lane.core.Guard(
                out, 48, deadline=time.monotonic() + gpu.END - time.time()
            ) as thermal:

                class Guard:
                    def check(self):
                        check(root, old)
                        lane.Checks(old, out, thermal).check()

                guard = Guard()
                if job in SPARK:
                    guard.check()
                    groups = need_rows(old, lane.read(old / "inputs/inputs.json"))
                    result = spark_work(root, old, job, out, guard, groups)
                else:
                    from day_resume import workstation

                    result = workstation(root, old, job, out, guard, thermal, cfg)
                thermal.check()
                check(root, old)
            files = {
                p.relative_to(out).as_posix(): lane.pin(p)
                for p in sorted(out.rglob("*"))
                if p.is_file()
            }
            lane.write(
                out / "receipt.json",
                {
                    "status": "complete",
                    "owner": owner,
                    "result": result,
                    "artifacts": files,
                },
            )
            lane.write(
                out / "complete.json",
                {"sourceReceiptPin": lane.pin(out / "receipt.json")},
            )
        except Exception as exc:
            lane.write(
                out / "failed.json",
                {"owner": owner, "error": str(exc), "at": lane.now()},
            )
            raise


def serve(root, old, registration, queue):
    machine = "workstation" if os.name == "nt" else "spark"
    with lane.lease(root / (machine + "-dispatch.lock")):
        lane.write(
            root / (machine + "-dispatcher.json"),
            {**lane.identity(), "at": lane.now(), "registration": registration},
        )
        for job in queue:
            out = root / "jobs" / job
            if out.exists():
                verified(out, registration)
                continue
            while True:
                check(root, old)
                proc = subprocess.Popen(
                    [
                        sys.executable,
                        "-B",
                        __file__,
                        str(root),
                        str(old),
                        registration,
                        job,
                    ]
                )
                if os.name == "nt":
                    import psutil
                    from rapid_windows_follow import Process

                    while proc.poll() is None and not (out / "owner.json").is_file():
                        time.sleep(0.2)
                    if (out / "owner.json").exists():
                        owner = lane.read(out / "owner.json")
                        with contextlib.closing(
                            Process(owner["pid"], owner["createdTicks"])
                        ) as native:
                            if (
                                owner["pid"] != proc.pid
                                and psutil.Process(owner["pid"]).ppid() != proc.pid
                            ):
                                raise ValueError(
                                    "Worker does not belong to its launcher"
                                )
                            native_code = native.wait(lambda: None)
                        if native_code != proc.wait():
                            raise ValueError("Worker and launcher exits disagree")
                code = proc.wait()
                if code == 74 and not out.exists():
                    time.sleep(15)
                    continue
                break
            owner = lane.read(out / "owner.json")
            if (
                (os.name != "nt" and proc.pid != owner["pid"])
                or owner["job"] != job
                or owner["registration"] != registration
            ):
                raise ValueError("Worker identity differs")
            while True:
                try:
                    with lane.lease(gpu.lock_path(old)):
                        lane.write(
                            out / "released.json",
                            {
                                "owner": owner,
                                "at": lane.now(),
                                "exitCode": code,
                                "nativeExited": True,
                                "childWaited": True,
                                "sharedLeaseReacquired": True,
                            },
                        )
                    break
                except lane.Busy:
                    time.sleep(15)
            verified(out, registration)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("old", type=Path)
    parser.add_argument("registration")
    parser.add_argument("action")
    args = parser.parse_args()
    lane.settings()
    root, old = args.root.resolve(), args.old.resolve()
    registration = root / ("workstation.json" if os.name == "nt" else "spark.json")
    gpu.require_pin(registration, args.registration)
    cfg = lane.read(registration)
    folder = Path(__file__).resolve().parent
    if folder.name != cfg["commit"]:
        sys.exit("Wrong code snapshot")
    for name, digest in cfg["code"].items():
        gpu.require_pin(folder / name, digest)
    queue = WINDOWS if os.name == "nt" else SPARK
    if args.action == "serve":
        serve(root, old, args.registration, queue)
    elif args.action in queue:
        try:
            run(root, old, args.action, args.registration, cfg)
        except lane.Busy:
            sys.exit(74)
    else:
        sys.exit("Wrong host or job")
