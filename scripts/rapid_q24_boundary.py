"""Wake on the original Q24 process exit and export its verified whole-author prefix."""

import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
from pathlib import Path

WEEK = Path("/home/agent/tompathy-open/week-20261122")
RAPID = Path("/home/agent/tompathy-open/rapid-20261127")
EXPORTER = "bb173b8f2403d53f7c3ee2beb3f7e03c808fb61875ce04a9f811e78fd3c9fd17"
ORIGINAL = WEEK / "prepared/38ab94888e265cd393575a2be6c10ea2a16a3269/week_q24_return.py"
DEST = WEEK / "Q24-return-20261127-a"
OWNER = (2789591, "44235912", "17b89c07-ca2a-4328-be23-1079536e9232")


def pin(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def remote():
    import fcntl

    with (RAPID / "Q24-export.lock").open("ab") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        owner = read(WEEK / "jobs/Q24/owner.json")
        actual = owner["pid"], str(owner["startTicks"]), owner["bootId"]
        if (
            actual != OWNER
            or Path("/proc/sys/kernel/random/boot_id").read_text().strip() != OWNER[2]
        ):
            raise ValueError("The original Q24 worker or boot differs")
        if pin(ORIGINAL) != EXPORTER:
            raise ValueError("Original registered exporter differs")
        pid = owner["pid"]
        try:
            fd = os.pidfd_open(pid)
        except ProcessLookupError:
            fd = None
        if fd is not None:
            try:
                stat = Path("/proc") / str(pid) / "stat"
                if (
                    stat.exists()
                    and stat.read_text().rsplit(")", 1)[1].split()[19] == OWNER[1]
                ):
                    events = select.poll()
                    events.register(fd, select.POLLIN)
                    events.poll()
            finally:
                os.close(fd)
        if not DEST.exists():
            subprocess.run(
                [sys.executable, str(ORIGINAL), "export", str(DEST)],
                stdout=subprocess.DEVNULL,
                check=True,
            )
        receipt = read(DEST / "receipt.json")
        if (
            not receipt["nativeExited"]
            or not receipt["priorLocksReleased"]
            or receipt["owner"] != owner
            or pin(DEST / "whole-authors.jsonl.gz") != receipt["compactPin"]
        ):
            raise ValueError("Export did not verify")
        print(pin(DEST / "receipt.json"), flush=True)


def receive(root, commit):
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Expected a committed supervisor")
    root = root.resolve()
    remote_script = f"{RAPID.as_posix()}/tools/{commit}/rapid_q24_boundary.py"
    response = subprocess.check_output(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ServerAliveInterval=45",
            "spark",
            "/home/agent/venvs/engine/bin/python",
            remote_script,
            "wait-export",
        ],
        text=True,
    ).strip()
    if len(response) != 64 or any(c not in "0123456789abcdef" for c in response):
        raise ValueError("Missing remote receipt hash")
    mirror = root / "Q24-return-a"
    mirror.mkdir(exist_ok=True)
    for name in ("receipt.json", "whole-authors.jsonl.gz"):
        dest = mirror / name
        if not dest.exists():
            partial = mirror / (name + ".partial")
            subprocess.run(
                [
                    "scp",
                    "-q",
                    "-o",
                    "BatchMode=yes",
                    "spark:" + DEST.as_posix() + "/" + name,
                    str(partial),
                ],
                check=True,
            )
            expected = (
                response
                if name == "receipt.json"
                else read(mirror / "receipt.json")["compactPin"]
            )
            if pin(partial) != expected:
                raise ValueError("Transferred Q24 file differs")
            partial.rename(dest)
    if pin(mirror / "receipt.json") != response:
        raise ValueError("Different Q24 terminal source")
    import week_q24_return as original

    if pin(Path(original.__file__)) != EXPORTER:
        raise ValueError("Workstation verifier differs from the registered exporter")
    verified = original.verify_local(mirror, root.parent / "week-20261122")
    result = dict(
        **verified,
        mirror=str(mirror),
        verifier=EXPORTER,
        nativeExited=True,
        priorFlockReleased=True,
    )
    audit = root / "Q24-transfer.json"
    if audit.exists():
        if read(audit) != result:
            raise ValueError("Existing local audit disagrees")
    else:
        with audit.open("x", encoding="utf8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    print(json.dumps(verified), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["receive", "wait-export"])
    parser.add_argument("--root", type=Path, default=Path(".local/rapid-20261127"))
    parser.add_argument("--commit")
    args = parser.parse_args()
    if args.action == "wait-export":
        remote()
    else:
        receive(args.root, args.commit)
