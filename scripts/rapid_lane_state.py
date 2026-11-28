"""Read only the registered Round 37 native identities, terminal flags and row counters."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def read(path):
    return json.loads(path.read_bytes())


def live(owner):
    if os.name == "nt":
        from rapid_windows_follow import Process

        try:
            p = Process(
                owner["pid"], owner.get("createdTicks", owner.get("created_ticks"))
            )
        except (ValueError, OSError):
            return False
        try:
            return p.dll.WaitForSingleObject(p.handle, 0) == 258
        finally:
            p.close()
    if Path("/proc/sys/kernel/random/boot_id").read_text().strip() != owner.get(
        "bootId"
    ):
        return False
    try:
        info = (
            (Path("/proc") / str(owner["pid"]) / "stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()
        )
    except FileNotFoundError:
        return False
    return info[0] != "Z" and info[19] == str(owner["startTicks"])


def gpu(root, jobs):
    last = None
    for k in reversed(jobs):
        path = root / "jobs" / k
        if not (path / "owner.json").is_file():
            continue
        owner = read(path / "owner.json")
        if owner["job"] != k:
            raise ValueError("Recorded GPU job name differs")
        if live(owner):
            progress = (
                read(path / "progress.json")
                if (path / "progress.json").exists()
                else {}
            )
            return {
                "state": "running",
                "job": k,
                **{
                    p: progress[p]
                    for p in ("rows", "total", "valid", "at", "arm")
                    if p in progress
                },
            }
        if last is None:
            last = {
                "state": "stopped"
                if (path / "failed.json").exists()
                else "between jobs",
                "last": k,
                "released": (path / "released.json").exists(),
            }
    return last or {"state": "no verified ToMpathy worker"}


def spark(root):
    priority = gpu(root, ("Q26", "Q27", "Q28", "Q32", "Q29", "Q31", "Q30", "Q33"))
    if priority["state"] == "running":
        return priority
    week = root.parent / "week-20261122"
    out = week / "jobs/Q24b"
    if not (out / "owner.json").is_file():
        return priority
    owner = read(out / "owner.json")
    if owner["job"] != "Q24b" or not live(owner):
        return priority
    if (week / "priority.pending").exists() or (out / "YIELD").exists():
        return {**priority, "parked": "Q24b"}
    lease = Path("/home/agent/gpu.lock").stat()
    held = False
    for line in Path("/proc/locks").read_text().splitlines():
        f = line.split()
        if len(f) < 6 or f[1] != "FLOCK" or f[4] != str(owner["pid"]):
            continue
        major, minor, inode = f[5].split(":")
        if (int(major, 16), int(minor, 16), int(inode)) == (
            os.major(lease.st_dev),
            os.minor(lease.st_dev),
            lease.st_ino,
        ):
            held = True
            break
    if not held:
        return {"state": "dispatcher active between GPU leases", "last": "Q24b"}
    progress = read(out / "progress.json") if (out / "progress.json").is_file() else {}
    return {
        "state": "running",
        "job": "Q24b",
        **{
            k: v
            for k, v in progress.items()
            if k in ("rows", "total", "at", "wholeAuthors")
        },
    }


def windows():
    root = Path(".local/rapid-20261127")
    active = []
    for pat in (
        "TP70-block-*-a",
        "TP70-return-?",
        "TP64-?",
        "TP65-?",
        "TP65-inputs-?",
        "TP77-*-?",
        "TP65-Q29-?",
        "TP73-paired*-?",
        "Q31-inputs-?",
        "TP63-*-?",
        "G15-inputs-?",
        "TP72-rehearsal-?",
    ):
        for f in root.glob(pat):
            if (f / "released.json").exists() or not (f / "owner.json").exists():
                continue
            owner = read(f / "owner.json")
            if live(owner["native"]):
                active.append(f.name)
    if len(active) > 1:
        raise ValueError("More than one registered card scorer appears active")
    reason = "between registered stages"
    if not active:
        for name in (
            "group-queue",
            "post-groups",
            "sentence-card-queue",
            "outside-card-queue",
        ):
            job = root / name
            if (job / "stopped.json").exists() and not (job / "complete.json").exists():
                reason = f"paused after {name} reported a stop"
                break
        else:
            if (root / "sentence-card-queue/complete.json").exists() and not (
                root / "outside-card-queue/armed.json"
            ).exists():
                reason = "waiting for the next prepared card after the sentence studies"
    if (
        not active
        and (root / "TP72-counted-wait/awaiting-prior.json").is_file()
        and not any(
            (root / "TP72-counted-wait" / name).is_file()
            for name in ("complete.json", "stopped.json")
        )
    ):
        reason = "waiting for counted CPU and memory admission for the sealed-bundle rehearsal"
    for stage, label in (
        ("TP77-wordings", "Q32 wording comparisons"),
        ("TP77-Q29", "Q29 sentence agreement"),
    ):
        wait = root / (stage + "-counted-wait")
        if (
            not active
            and (wait / "armed.json").is_file()
            and not any(
                (wait / name).is_file() for name in ("complete.json", "stopped.json")
            )
            and live(read(wait / "armed.json")["owner"])
        ):
            reason = "waiting for counted memory admission for " + label
            break
    return {
        "gpu": gpu(root, ("G12", "G14", "G13-Q29", "G13-Q31", "G15")),
        "card": active[0] if active else None,
        "cardIdleReason": None if active else reason,
    }


def get():
    p = Path(__file__).resolve()
    reply = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=12",
            "spark",
            "python3",
            "-",
            "--spark",
        ],
        input=p.read_bytes(),
        capture_output=True,
        timeout=45,
        check=True,
    )
    return {
        "workstation": windows(),
        "spark": json.loads(reply.stdout),
        "checkedAt": datetime.now(UTC).isoformat(),
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["--spark"]:
        root = Path("/home/agent/tompathy-open/rapid-20261127")
        print(json.dumps(spark(root)))
    else:
        print(json.dumps(get()))
