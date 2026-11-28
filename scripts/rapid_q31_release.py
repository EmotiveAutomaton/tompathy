"""Release the Round 37 filler only after Q31 exits and its priority successors lack a source."""

import argparse
import hashlib
import json
import os
import select
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path("/home/agent/tompathy-open/rapid-20261127")
WEEK = ROOT.parent / "week-20261122"
FILLER = WEEK / "jobs/Q24b"
PREVIOUS = ROOT / "jobs/Q31"
CONTROL = ROOT / "after-Q31-filler"
MARKER = WEEK / "priority.pending"
END = 1795968000


def read(p):
    return json.loads(p.read_bytes())


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(name, value):
    with (CONTROL / name).open("x", encoding="utf8") as f:
        json.dump(dict(at=datetime.now(UTC).isoformat(), **value), f)


def mount_pin():
    mounts = subprocess.check_output(
        ["findmnt", "-rn", "-o", "TARGET,SOURCE,FSTYPE"], text=True
    )
    # Only filesystem topology matters. Container mount IDs change independently.
    network = sorted(
        line
        for line in mounts.splitlines()
        if line.rsplit(" ", 1)[-1]
        in ("cifs", "smb3", "nfs", "nfs4", "9p", "fuse.sshfs")
    )
    return hashlib.sha256("\n".join(network).encode()).hexdigest()


def live(owner):
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


def check():
    if time.time() >= END or any(
        (p / "STOP").exists()
        for p in (
            ROOT,
            WEEK,
            FILLER,
            PREVIOUS,
            CONTROL,
            ROOT.parent / "person-teacher-20261121",
            ROOT.parent / "person-teacher-20261121/cb",
            ROOT.parent / "word-table-20261120",
        )
    ):
        raise RuntimeError("Registered cutoff or STOP")


def released(owner):
    terminal = read(PREVIOUS / "released.json")
    source = PREVIOUS / "receipt.json"
    receipt = read(source)
    h = sha(source)
    if (
        live(owner)
        or read(PREVIOUS / "owner.json") != owner
        or receipt["owner"] != owner
        or receipt["status"] != "complete"
        or terminal["owner"] != owner
        or terminal["exitCode"] != 0
        or not terminal["childWaited"]
        or not terminal["sharedLeaseReacquired"]
        or read(PREVIOUS / "complete.json") != {"sourceReceiptPin": h}
        or (PREVIOUS / "failed.json").exists()
    ):
        raise ValueError("Q31 needs review before releasing its priority")
    return h


def priority_ready(plan):
    return (
        mount_pin() != plan["mountPin"]
        or any((ROOT / "jobs" / name).exists() for name in ("Q30", "Q33"))
        or (CONTROL / "SOURCE_READY").exists()
        or (FILLER / "YIELD").exists()
    )


def handoff(plan, expected):
    import fcntl

    if sha(plan) != expected or plan.parent != CONTROL:
        raise ValueError("Handoff registration differs")
    cfg = read(plan)
    q, f = cfg["Q31"], cfg["Q24b"]
    if (
        q["job"] != "Q31"
        or f["job"] != "Q24b"
        or sha(ROOT / "Q31-registration.json") != q["registration"]
        or sha(Path(__file__)) != cfg["scriptPin"]
        or q != read(PREVIOUS / "owner.json")
        or f != read(FILLER / "owner.json")
        or not live(f)
        or not live(q)
        or MARKER.read_bytes() != b"Round37-Q26\n"
        or sha(MARKER) != cfg["markerPin"]
        or priority_ready(cfg)
    ):
        raise ValueError(
            "Registered predecessor, parked filler or source availability differs"
        )
    fd = os.pidfd_open(q["pid"])
    try:
        if not live(q):
            raise ValueError("Predecessor changed while attaching")
        check()
        save(
            "armed.json",
            {
                "planPin": expected,
                "pid": os.getpid(),
                "startTicks": Path("/proc/self/stat")
                .read_text()
                .rsplit(")", 1)[1]
                .split()[19],
                "bootId": q["bootId"],
            },
        )
        monitor = select.poll()
        monitor.register(fd, select.POLLIN)
        while not monitor.poll(60000):
            check()
    finally:
        os.close(fd)
    for _ in range(120):
        check()
        if (PREVIOUS / "released.json").is_file():
            break
        time.sleep(1)
    source = released(q)
    with Path("/home/agent/gpu.lock").open("rb") as lock:
        while True:
            check()
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(15)
        check()
        if not live(f) or read(FILLER / "owner.json") != f or priority_ready(cfg):
            raise ValueError(
                "Priority eligibility or parked filler changed; review the successor"
            )
        if (
            MARKER.is_symlink()
            or sha(MARKER) != cfg["markerPin"]
            or MARKER.stat().st_ino != cfg["markerInode"]
        ):
            raise ValueError("Priority marker changed")
        previous = WEEK / "priority.round37-q31-released"
        if previous.exists():
            raise FileExistsError("Prior filler handoff exists")
        MARKER.rename(previous)
        save(
            "released.json",
            {
                "Q31ReceiptPin": source,
                "fillerOwner": f,
                "archivedMarkerPin": sha(previous),
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("pin")
    args = parser.parse_args()
    try:
        handoff(args.plan, args.pin)
    except Exception as exc:
        if not (CONTROL / "failed.json").exists():
            save("failed.json", {"reason": str(exc)})
        raise
