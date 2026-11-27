"""Run the registered Round 37 GPU work under the existing machine-wide lease."""

import argparse
import gzip
import json
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import rapid_marks as marks
import word_table_lane as lane

END = 1795968000
WEEK = Path("/home/agent/tompathy-open/week-20261122")
C = ("qwen3.5:122b", "8b9d11d807c57feb1e2ecb0d6cbf40334c37dcc3523bed5540af4f927f112a37")
QUEUE = {"workstation": ("G12", "G14"), "spark": ("Q26", "Q34", "Q27", "Q28", "Q32")}
HOURS = {
    "Q26": 1,
    "Q34": 1,
    "Q27": 10.8,
    "Q28": 2,
    "Q32": 2,
    "G12": 6,
    "G14": 1,
    "Q29": 3,
    "G13-Q29": None,
}
write, read, pin = lane.write, lane.read, lane.pin


def lock_path(root):
    if os.name == "nt":
        return root.parent / "word-table/workstation/gpu.lock"
    return Path("/home/agent/gpu.lock")


def require_pin(path, expected):
    if pin(path) != expected:
        raise ValueError("Registered file differs: " + path.name)


def check_stop(root):
    others = (
        [
            root.parent / "word-table",
            root.parent / "person-teacher",
            root.parent / "week-20261122",
        ]
        if os.name == "nt"
        else [
            WEEK,
            WEEK.parent / "word-table-20261120",
            WEEK.parent / "person-teacher-20261121",
            WEEK.parent / "person-teacher-20261121/cb",
        ]
    )
    if time.time() >= END or any((p / "STOP").exists() for p in [root, *others]):
        raise RuntimeError("Deadline or owner STOP")


def roster(root, manifest, job):
    names = (
        ["ed"]
        if job == "Q26"
        else ["envent"]
        if job in ("Q28", "G14", "Q34")
        else ["ed", "envent", "go"]
    )
    groups = {}
    for name in names:
        path = root / "inputs" / (name + ".jsonl.gz")
        require_pin(path, manifest["files"][path.name])
        with gzip.open(path, "rt", encoding="utf8") as stream:
            rows = [json.loads(line) for line in stream]
        if (
            len(rows) != manifest["counts"][name]
            or len({r["id"] for r in rows}) != len(rows)
            or any(set(r) != {"id", "text"} for r in rows)
        ):
            raise ValueError("Input census or field allowlist differs")
        groups[name] = rows
    if job == "Q26":
        return sorted(groups["ed"], key=lambda r: marks.digest("Q26:23:" + r["id"]))[
            :200
        ]
    if job == "Q32":
        return [
            r
            for rows in groups.values()
            for r in sorted(rows, key=lambda r: marks.digest("Q32:23:" + r["id"]))[:500]
        ]
    return [r for rows in groups.values() for r in rows]


def job_width(root):
    out = root / "jobs/Q26"
    require_pin(out / "receipt.json", read(out / "complete.json")["sourceReceiptPin"])
    if read(out / "released.json")["owner"] != read(out / "owner.json"):
        raise ValueError("Q26 release differs")
    width = read(out / "receipt.json")["result"]["selectedWidth"]
    if width not in (1, 2, 4):
        raise ValueError("Invalid Q26 result")
    return width


def reader_arm(out, items, role, kind, width, guard, job, arm, measured=None):
    folder = out / arm
    folder.mkdir()
    prompt, schema, parse = marks.template(kind)
    model, model_pin = C if role == "C" else lane.MODELS[role]
    options = {
        "temperature": 0,
        "seed": 23,
        "num_ctx": 4096,
        "num_predict": 256,
        "num_thread": 2 if role == "W" else 3,
    }
    binding = dict(
        **marks.protocol(kind),
        model=model,
        modelPin=model_pin,
        think=False,
        options=options,
        inputPin=marks.digest("\n".join(r["id"] for r in items)),
        width=width,
    )
    write(folder / "protocol.json", binding)
    lane.core.read_model(model, model_pin)
    if lane.core.api("ps")["models"]:
        raise lane.Pause("Another resident is present before this arm")

    def call(item):
        guard.check()
        before = time.monotonic()
        # A UTF-8 byte upper bound includes the wrapper and output reserve. Unsupported
        # full texts stay in their roster position with a missing measurement.
        if (
            not item["text"].strip()
            or len((prompt + item["text"]).encode()) + 256 + 64 > 4096
        ):
            return {
                "id": item["id"],
                "values": None,
                "response": None,
                "seconds": 0,
                "reason": "Empty text or full context uncertified",
            }
        raw = lane.core.guarded_generate(
            {
                "model": model,
                "prompt": prompt + item["text"],
                "format": schema,
                "stream": False,
                "think": False,
                "keep_alive": "10m",
                "options": options,
            },
            guard,
        )
        response = raw.get("response", "")
        try:
            value = parse(json.loads(response))
        except (TypeError, ValueError):
            value = None
        return {
            "id": item["id"],
            "response": response,
            "values": value,
            "seconds": time.monotonic() - before,
            "doneReason": raw.get("done_reason"),
            "inputTokens": raw.get("prompt_eval_count"),
        }

    rows = []
    owned = False
    try:
        guard.check()
        owned = True
        lane.core.guarded_generate(
            {
                "model": model,
                "prompt": "",
                "stream": False,
                "keep_alive": "10m",
                "options": options,
            },
            guard,
        )
        lane.fit_or_wait(model_pin, role)
        start = time.monotonic()
        valid = slow = 0
        durations = []
        with ThreadPoolExecutor(max_workers=width) as pool:
            for pos in range(0, len(items), width):
                guard.check()
                batch = list(pool.map(call, items[pos : pos + width]))
                write(folder / f"from-{pos:06d}.json", batch)
                rows.extend(batch)
                valid += sum(r["values"] is not None for r in batch)
                for row in batch:
                    slow = (
                        slow + 1
                        if durations
                        and row["seconds"] > 5 * statistics.median(durations[-100:])
                        else 0
                    )
                    durations.append(row["seconds"])
                if role == "W" and slow >= 20:
                    raise lane.Pause(
                        "20 consecutive requests exceeded five times the recent median"
                    )
                resident = lane.fit_or_wait(model_pin, role)
                elapsed = time.monotonic() - start
                progress = {
                    "at": lane.now(),
                    "job": job,
                    "arm": arm,
                    "rows": len(rows),
                    "total": len(items),
                    "elapsedSeconds": elapsed,
                    "valid": valid,
                    "residentBytes": resident,
                    "width": width,
                }
                if len(rows) == 100:
                    projected = elapsed * (measured or len(items)) / 100 / 3600
                    write(
                        folder / "first100.json",
                        dict(
                            **progress,
                            projectedHours=projected,
                            packetHours=HOURS[job],
                            overThreeTimes=projected > 3 * HOURS[job]
                            if HOURS[job] is not None
                            else None,
                        ),
                    )
                if len(rows) % 20 == 0 or len(rows) == len(items):
                    write(out / "progress.json", progress)
        elapsed = time.monotonic() - start
        write(
            folder / "complete.json",
            {
                "rows": len(rows),
                "valid": valid,
                "seconds": elapsed,
                "protocolPin": pin(folder / "protocol.json"),
                "inputPin": binding["inputPin"],
            },
        )
        return rows, elapsed
    finally:
        if owned and any(
            r["digest"] == model_pin for r in lane.core.api("ps")["models"]
        ):
            lane.core.read_model(model, model_pin)
            lane.core.api("generate", {"model": model, "keep_alive": 0})


def run_job(root, job, registration):
    sentence_job = job in ("Q29", "G13-Q29")
    registration_path = root / (
        "Q29-registration.json" if sentence_job else "registration.json"
    )
    require_pin(registration_path, registration)
    cfg = read(registration_path)
    script_dir = Path(__file__).resolve().parent
    for name, h in cfg["code"].items():
        require_pin(script_dir / name, h)
    if script_dir.name != cfg["commit"] or job not in (
        *QUEUE["workstation" if os.name == "nt" else "spark"],
        "G13-Q29" if os.name == "nt" else "Q29",
    ):
        raise ValueError("Snapshot or machine binding differs")
    check_stop(root)
    with lane.lease(lock_path(root)):
        if lane.core.api("ps")["models"]:
            raise lane.Busy("Shared service already has a resident")
        require_pin(root / "inputs/inputs.json", cfg["inputManifest"])
        out = root / "jobs" / job
        out.mkdir(parents=True, exist_ok=False)
        owner = dict(
            **lane.identity(),
            at=lane.now(),
            job=job,
            registration=registration,
            commit=cfg["commit"],
        )
        write(out / "owner.json", owner)
        try:
            with lane.core.Guard(
                out, 48, deadline=time.monotonic() + END - time.time()
            ) as thermal:

                class Guard:
                    def check(self):
                        lane.Checks(root, out, thermal).check()
                        check_stop(root)

                guard = Guard()
                guard.check()
                if not sentence_job:
                    items = roster(root, read(root / "inputs/inputs.json"), job)
                if sentence_job:
                    from rapid_sentence_gpu import run

                    result = run(root, out, job, cfg, guard)
                elif job == "Q26":
                    widths = {
                        w: reader_arm(
                            out,
                            items,
                            "B",
                            "standing",
                            w,
                            guard,
                            job,
                            "width-" + str(w),
                            600,
                        )
                        for w in (1, 2, 4)
                    }
                    result = marks.compare(widths)
                elif job == "Q34":
                    from rapid_worry import run

                    result = run(root, out, items, cfg, guard)
                elif job == "Q32":
                    try:
                        reader_arm(
                            out, items, "C", "standing", 1, guard, job, "C", 3500
                        )
                        c = read(out / "C/complete.json")
                    except RuntimeError as exc:
                        if str(exc) != "Reader C leaves less than 15 GB available":
                            raise
                        c = {"status": "skipped", "reason": str(exc)}
                        write(out / "C/skipped.json", c)
                    probe = sorted(
                        items, key=lambda r: marks.digest("Q32:reword:23:" + r["id"])
                    )[:1000]
                    for kind in ("standing2", "standing3"):
                        reader_arm(
                            out,
                            probe,
                            "B",
                            kind,
                            job_width(root),
                            guard,
                            job,
                            kind,
                            3500,
                        )
                    result = dict(
                        C=c,
                        **{
                            k: read(out / k / "complete.json")
                            for k in ("standing2", "standing3")
                        },
                    )
                else:
                    role = "W" if job.startswith("G") else "B"
                    kind = "features" if job in ("G14", "Q28") else "standing"
                    reader_arm(
                        out,
                        items,
                        role,
                        kind,
                        1 if role == "W" else job_width(root),
                        guard,
                        job,
                        role,
                    )
                    result = read(out / role / "complete.json")
                guard.check()
            files = {
                p.relative_to(out).as_posix(): pin(p)
                for p in sorted(out.rglob("*"))
                if p.is_file()
            }
            write(
                out / "receipt.json",
                {
                    "status": "complete",
                    "owner": owner,
                    "result": result,
                    "artifacts": files,
                    "at": lane.now(),
                },
            )
            write(
                out / "complete.json", {"sourceReceiptPin": pin(out / "receipt.json")}
            )
        except Exception as exc:
            write(
                out / "failed.json",
                {"owner": owner, "error": str(exc), "at": lane.now()},
            )
            raise


def serve(root, registration):
    machine = "workstation" if os.name == "nt" else "spark"
    with lane.lease(root / (machine + "-dispatch.lock")):
        write(
            root / (machine + "-dispatcher.json"),
            dict(**lane.identity(), at=lane.now(), registration=registration),
        )
        for job in QUEUE[machine]:
            out = root / "jobs" / job
            if (out / "released.json").is_file():
                record = read(out / "released.json")
                if (
                    record["exitCode"]
                    or record["owner"]["registration"] != registration
                ):
                    raise RuntimeError("Prior outcome needs review")
                require_pin(
                    out / "receipt.json",
                    read(out / "complete.json")["sourceReceiptPin"],
                )
                continue
            while True:
                check_stop(root)
                proc = subprocess.Popen(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        str(root),
                        registration,
                        job,
                    ]
                )
                code = proc.wait()
                if code == 74 and not out.exists():
                    time.sleep(15)
                    continue
                break
            if not (out / "owner.json").is_file():
                raise RuntimeError("Worker did not establish ownership: " + job)
            owner = read(out / "owner.json")
            if (
                owner["pid"] != proc.pid
                or owner["registration"] != registration
                or owner["job"] != job
            ):
                raise RuntimeError("Unexpected terminal identity")
            while True:
                try:
                    with lane.lease(lock_path(root)):
                        write(
                            out / "released.json",
                            {
                                "owner": owner,
                                "exitCode": code,
                                "at": lane.now(),
                                "childWaited": True,
                                "sharedLeaseReacquired": True,
                            },
                        )
                    break
                except lane.Busy:
                    check_stop(root)
                    time.sleep(5)
            if code:
                raise RuntimeError("Preserved stopped job: " + job)
            require_pin(
                out / "receipt.json", read(out / "complete.json")["sourceReceiptPin"]
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("registration")
    parser.add_argument("action")
    args = parser.parse_args()
    lane.settings()
    try:
        if args.action == "serve":
            serve(args.root.resolve(), args.registration)
        else:
            run_job(args.root.resolve(), args.action, args.registration)
    except lane.Busy:
        sys.exit(74)
