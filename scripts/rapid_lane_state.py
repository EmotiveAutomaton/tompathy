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


def windows():
    root = Path(".local/rapid-20261127")
    active = []
    for pat in (
        "TP70-block-*-a",
        "TP70-return-?",
        "TP64-?",
        "TP65-?",
        "TP65-inputs-?",
        "TP77-original-?",
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
        print(
            json.dumps(
                gpu(root, ("Q26", "Q27", "Q28", "Q32", "Q29", "Q31", "Q30", "Q33"))
            )
        )
    else:
        print(json.dumps(get()))
