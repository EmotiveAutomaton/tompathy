"""Start the registered sentence stage when the preceding native GPU supervisor exits."""

import argparse
import contextlib
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

FROZEN = "3d76451faa466a9c0cd5653f31034efad417fd96"
REG = "86477edf7ee5b3f26ed8dc79d14469522375fc36677cfa57946a64539b13ece7"
PRIOR = "2aaa9e0fc722a48e40e854b61dddc9b9c2a03828233e2c0fc3175afdcffa7f6a"


def linux_live(owner):
    if Path("/proc/sys/kernel/random/boot_id").read_text().strip() != owner["bootId"]:
        return False
    try:
        fields = (
            (Path("/proc") / str(owner["pid"]) / "stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()
        )
    except FileNotFoundError:
        return False
    return fields[0] != "Z" and fields[19] == str(owner["startTicks"])


def wait_predecessor(owner, check):
    if os.name == "nt":
        from rapid_windows_follow import Process

        with contextlib.closing(Process(owner["pid"], owner["createdTicks"])) as p:
            if p.wait(check) != 0:
                raise ValueError("Predecessor supervisor stopped with an error")
        return
    if not linux_live(owner):
        raise ValueError("Predecessor is absent before its release")
    fd = os.pidfd_open(owner["pid"])
    try:
        if not linux_live(owner):
            raise ValueError("Predecessor identity changed while opening its pidfd")
        watch = select.poll()
        watch.register(fd, select.POLLIN)
        while not watch.poll(60000):
            check()
    finally:
        os.close(fd)


def run(
    root,
    prepare_only=False,
    blog_registration=None,
    filler_registration=None,
    released_workstation=False,
    after_g14_stop=False,
    memory_stop_pins=None,
):
    import hashlib
    import json

    if filler_registration and (blog_registration or os.name != "nt"):
        raise ValueError("G15 is a separate workstation registration")
    if after_g14_stop and (
        os.name != "nt"
        or not released_workstation
        or blog_registration
        or filler_registration
    ):
        raise ValueError("Only G13-Q29 can follow the verified G14 memory stop")
    if memory_stop_pins and (
        os.name != "nt"
        or not released_workstation
        or after_g14_stop
        or not (blog_registration or filler_registration)
        or len(memory_stop_pins) != 2
        or not all(re.fullmatch("[0-9a-f]{64}", p) for p in memory_stop_pins)
    ):
        raise ValueError(
            "A released workstation stage and both exact memory-stop file hashes are required"
        )
    if after_g14_stop:
        memory_stop_pins = (
            "56e6c128806ede0aa60b3595d760a5249d80e71df675717324289c458af613e9",
            "4014a51add3281982cdd459e230c7d0e0488ae3f4b0489e74f827617cde7e923",
        )
    if filler_registration:
        cfgpath = root / "G15-registration.json"
    else:
        cfgpath = root / (
            "Q31-registration.json" if blog_registration else "Q29-registration.json"
        )
    expected = filler_registration or blog_registration or REG
    raw = cfgpath.read_bytes()
    if (
        not re.fullmatch("[0-9a-f]{64}", expected)
        or hashlib.sha256(raw).hexdigest() != expected
    ):
        raise ValueError("The staged GPU registration differs")
    cfg = json.loads(raw)
    frozen = cfg["commit"] if blog_registration or filler_registration else FROZEN
    predecessor_registration = REG if blog_registration else PRIOR
    if filler_registration:
        predecessor_registration = hashlib.sha256(
            (root / "Q31-registration.json").read_bytes()
        ).hexdigest()
    if (
        not re.fullmatch("[0-9a-f]{40}", frozen)
        or cfg["commit"] != frozen
        or cfg["parentRegistration"]
        != (predecessor_registration if filler_registration else PRIOR)
    ):
        raise ValueError("Invalid registered code revision or parent")
    code = root / "code" / frozen
    sys.path.insert(0, str(code))
    import rapid_gpu as worker
    import rapid_sentences
    import tp31_teacher

    lane = worker.lane
    lane.settings()
    for name, h in cfg["code"].items():
        if Path(name).name != name:
            raise ValueError("A code file is outside the frozen snapshot")
        worker.require_pin(code / name, h)
    win = os.name == "nt"
    machine, prior, job = (
        ("workstation", "G14", "G13-Q29") if win else ("spark", "Q32", "Q29")
    )
    if filler_registration:
        prior, job = "G13-Q31", "G15"
        folder = root / cfg["inputStage"]
        worker.require_pin(folder / "receipt.json", cfg["inputReceiptPin"])
        worker.require_pin(folder / "selection.json", cfg["selectionPin"])
        intake = lane.read(folder / "selection.json")
        if (
            intake != lane.read(folder / "receipt.json")["result"]
            or intake["sameReaderSettings"]["promptPin"]
            != worker.marks.protocol("features")["promptPin"]
        ):
            raise ValueError("G15 source or original prompt differs")
        roster = {
            "authors": intake["eligibleAuthors"],
            "posts": intake["posts"],
            "reuse": intake["reuse"],
        }
    elif blog_registration:
        from rapid_blog_gpu import calendar

        prior, job = ("G13-Q29", "G13-Q31") if win else ("Q29", "Q31")
        selection = root / "Q31-selection.json"
        worker.require_pin(selection, cfg["selectionPin"])
        directory = (
            root.parent / "week-20261122/Q20-inputs-a/spark-inputs"
            if win
            else worker.WEEK / "Q20-inputs"
        )
        _, _, roster = calendar(
            lane.read(selection),
            directory,
            tp31_teacher.sentences,
            lambda: worker.check_stop(root),
        )
        if roster != cfg["roster"] or cfg["prompts"] != {
            k: worker.marks.protocol(k) for k in ("loss", "sentence")
        }:
            raise ValueError("The blog roster or prompt differs")
    else:
        isear = (
            root.parent / ("person-teacher" if win else "person-teacher-20261121")
        ) / "cb/isear.json"
        _, _, roster = rapid_sentences.prepare(root, isear, tp31_teacher.sentences)
        if (
            roster != cfg["sentences"]
            or worker.marks.protocol("sentence") != cfg["prompt"]
        ):
            raise ValueError("Staged sentence order, content or prompt differs")
    if prepare_only:
        return {
            "verifiedFiles": len(cfg["code"]),
            "roster": roster,
            "registration": expected,
        }
    suffix = (
        "-filler-follow"
        if filler_registration
        else "-blog-follow"
        if blog_registration
        else "-sentence-follow"
    )
    if released_workstation and not win:
        raise ValueError("Release-only continuation belongs to the workstation")
    route = (
        f"-after-{prior}-stop"
        if memory_stop_pins
        else ("-after-G12-stop" if released_workstation else "")
    )
    ctl = root / (machine + suffix + route)
    ctl.mkdir(exist_ok=True)
    with lane.lease(ctl / "dispatcher.lock"):
        target = root / "jobs" / job
        if target.exists():
            raise FileExistsError("Preserve the existing sentence job")
        if released_workstation:
            previous = root / "jobs" / prior
            predecessor = lane.read(previous / "released.json")["owner"]
        elif blog_registration or filler_registration:
            previous_ctl = "-blog-follow" if filler_registration else "-sentence-follow"
            proof = lane.read(root / (machine + previous_ctl) / "armed.json")
            if (
                proof["job"] != prior
                or proof["registration"] != predecessor_registration
            ):
                raise ValueError("Unknown preceding sentence supervisor")
            predecessor = proof["owner"]
        elif win:
            proof = lane.read(root / "workstation-follow/watching.json")
            worker.require_pin(
                Path(__file__).with_name("rapid_windows_follow.py"),
                proof["observerPin"],
            )
            predecessor = proof["observer"]
        else:
            predecessor = lane.read(root / "attempts/Q34-b/repair.json")["supervisor"]
        identity = lane.identity()

        def check():
            worker.check_stop(root)
            if (ctl / "STOP").exists():
                raise RuntimeError("Owner STOP on sentence follow-up")

        check()
        lane.write(
            ctl / "armed.json",
            {
                "at": lane.now(),
                "owner": identity,
                "predecessor": predecessor,
                "predecessorJob": prior,
                "job": job,
                "registration": expected,
                "codePin": lane.pin(Path(__file__)),
            },
        )
        try:
            previous = root / "jobs" / prior
            if not (previous / "released.json").exists():
                wait_predecessor(predecessor, check)
            old_owner = lane.read(previous / "owner.json")
            release = lane.read(previous / "released.json")
            if (
                release["owner"] != old_owner
                or release["exitCode"] != int(bool(memory_stop_pins))
                or not release["sharedLeaseReacquired"]
                or old_owner["job"] != prior
                or old_owner["registration"] != predecessor_registration
                or not release["childWaited"]
            ):
                raise ValueError("Cannot advance beyond an unverified predecessor")
            if memory_stop_pins:
                from rapid_windows_follow import Process

                worker.require_pin(previous / "failed.json", memory_stop_pins[0])
                worker.require_pin(previous / "released.json", memory_stop_pins[1])
                failure = lane.read(previous / "failed.json")
                if (
                    failure["owner"] != old_owner
                    or failure["error"] != "Available commit reached the 8 GiB floor"
                    or (previous / "complete.json").exists()
                    or (previous / "receipt.json").exists()
                ):
                    raise ValueError(
                        "Predecessor failure differs from the witnessed memory stop"
                    )
                try:
                    handle = Process(old_owner["pid"], old_owner["createdTicks"])
                except OSError as exc:
                    if exc.winerror != 87:
                        raise
                except ValueError:
                    pass  # The original creation time no longer occupies this PID.
                else:
                    with contextlib.closing(handle):
                        if handle.dll.WaitForSingleObject(handle.handle, 0) != 0:
                            raise ValueError("The original worker has not exited")
                # All successor jobs use the same pinned W model. Its completed
                # G14 pilot is also available when a later arm stops during loading.
                pilot = root / "jobs/G14/W/first100.json"
                resident = lane.read(pilot)["residentBytes"] / 2**30
                while True:
                    check()
                    available = lane.commit_free_gib()
                    models = lane.core.api("ps")["models"]
                    lane.write(
                        ctl / "capacity.json",
                        {
                            "at": lane.now(),
                            "commitGiB": available,
                            "lastResidentGiB": resident,
                            "residentModels": len(models),
                        },
                    )
                    if available > 8 + resident and not models:
                        break
                    time.sleep(60)
            else:
                worker.require_pin(
                    previous / "receipt.json",
                    lane.read(previous / "complete.json")["sourceReceiptPin"],
                )
                if lane.read(previous / "receipt.json")["owner"] != old_owner:
                    raise ValueError("Predecessor source and native owner differ")
            if not win and linux_live(old_owner):
                raise ValueError("Predecessor worker is still running")
            with lane.lease(root / (machine + "-dispatch.lock")):
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
                if not win:
                    env["PYTHONPATH"] = str(worker.WEEK / "deps")
                while True:
                    check()
                    p = subprocess.Popen(
                        [
                            sys.executable,
                            str(code / "rapid_gpu.py"),
                            str(root),
                            expected,
                            job,
                        ],
                        env=env,
                    )
                    while not (target / "owner.json").exists() and p.poll() is None:
                        time.sleep(0.5)
                    if (target / "owner.json").exists():
                        break
                    if p.wait() != 74 or target.exists():
                        raise ValueError(
                            "Sentence worker could not establish ownership"
                        )
                    time.sleep(15)
                owner = lane.read(target / "owner.json")
                if (owner["job"], owner["registration"], owner["commit"]) != (
                    job,
                    expected,
                    frozen,
                ):
                    raise ValueError("Sentence worker registration differs")
                if win:
                    import psutil
                    from rapid_windows_follow import Process

                    with contextlib.closing(
                        Process(owner["pid"], owner["createdTicks"])
                    ) as native:
                        if (
                            owner["pid"] != p.pid
                            and psutil.Process(owner["pid"]).ppid() != p.pid
                        ):
                            raise ValueError("Native worker is not the launched child")
                        lane.write(
                            ctl / "watching.json",
                            {"at": lane.now(), "owner": owner, "wrapperPid": p.pid},
                        )
                        # The final filler may be writing its cutoff receipt after its last call.
                        # Observing this child's exit never extends its scoring clock.
                        status = native.wait(
                            (lambda: None) if filler_registration else check
                        )
                        if p.wait() != status:
                            raise ValueError(
                                "Native worker and venv launcher exits differ"
                            )
                else:
                    if p.pid != owner["pid"] or not linux_live(owner):
                        raise ValueError("Spark native worker identity differs")
                    lane.write(
                        ctl / "watching.json", {"at": lane.now(), "owner": owner}
                    )
                    status = p.wait()
                    if linux_live(owner):
                        raise ValueError("Spark worker did not exit")
                if status == 0:
                    worker.require_pin(
                        target / "receipt.json",
                        lane.read(target / "complete.json")["sourceReceiptPin"],
                    )
                    if lane.read(target / "receipt.json")["owner"] != owner:
                        raise ValueError("Terminal receipt owner differs")
                elif lane.read(target / "failed.json")["owner"] != owner:
                    raise ValueError("Failure receipt owner differs")
                while True:
                    try:
                        with lane.lease(worker.lock_path(root)):
                            lane.write(
                                target / "released.json",
                                {
                                    "owner": owner,
                                    "exitCode": status,
                                    "childWaited": True,
                                    "sharedLeaseReacquired": True,
                                    "at": lane.now(),
                                },
                            )
                        break
                    except lane.Busy:
                        if not filler_registration:
                            check()
                        time.sleep(5)
                if status:
                    raise RuntimeError(
                        "Sentence worker stopped, see its preserved receipt"
                    )
                lane.write(
                    ctl / "complete.json",
                    {
                        "at": lane.now(),
                        "job": job,
                        "sourceReceiptPin": lane.pin(target / "receipt.json"),
                    },
                )
        except Exception as exc:
            lane.write(
                ctl / "stopped.json",
                {"at": lane.now(), "reason": str(exc), "observer": identity},
            )
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--released-workstation", action="store_true")
    parser.add_argument("--after-g14-stop", action="store_true")
    parser.add_argument(
        "--after-memory-stop", nargs=2, metavar=("FAILURE_PIN", "RELEASE_PIN")
    )
    registrations = parser.add_mutually_exclusive_group()
    registrations.add_argument("--blog-registration")
    registrations.add_argument("--filler-registration")
    args = parser.parse_args()
    proof = run(
        args.root.resolve(),
        args.verify_only,
        args.blog_registration,
        args.filler_registration,
        args.released_workstation,
        args.after_g14_stop,
        args.after_memory_stop,
    )
    if proof:
        print(proof)
