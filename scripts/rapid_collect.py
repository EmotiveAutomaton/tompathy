"""Verify an exited Spark worker and every registered file before returning its result."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

LOCAL = Path(".local/rapid-20261127")
REMOTE = Path("/home/agent/tompathy-open/rapid-20261127")
CAP = 1_000_000_000
REGISTRATIONS = {
    **dict.fromkeys(("Q26", "Q34", "Q34-b", "Q27", "Q28", "Q32"), "registration.json"),
    "Q29": "Q29-registration.json",
    "Q31": "Q31-registration.json",
}


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def inventory(source):
    receipt = read(source / "receipt.json")
    if receipt["status"] != "complete" or receipt["owner"] != read(
        source / "owner.json"
    ):
        raise ValueError("Receipt status or owner differs")
    files = receipt["artifacts"]
    actual = {
        p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()
    }
    if actual != set(files) | {"complete.json", "receipt.json", "released.json"}:
        raise ValueError("Unexpected file inventory")
    for name, h in files.items():
        path = (source / name).resolve()
        if (
            not path.is_relative_to(source.resolve())
            or path.is_symlink()
            or digest(path) != h
        ):
            raise ValueError("Terminal artifact differs")
    h = digest(source / "receipt.json")
    if read(source / "complete.json") != {"sourceReceiptPin": h}:
        raise ValueError("Terminal receipt binding differs")
    return h, actual


def archive(job, registration):
    source = (
        REMOTE / "attempts/Q34-b/jobs/Q34" if job == "Q34-b" else REMOTE / "jobs" / job
    )
    owner = read(source / "owner.json")
    release = read(source / "released.json")
    if (
        digest(REMOTE / REGISTRATIONS[job]) != registration
        or owner["registration"] != registration
        or owner["job"] != job.removesuffix("-b")
        or release["owner"] != owner
        or release["exitCode"] != 0
        or not release["sharedLeaseReacquired"]
        or not release["childWaited"]
        or Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        != owner["bootId"]
    ):
        raise ValueError("Terminal ownership or registration differs")
    pid = str(owner["pid"])
    proc = Path("/proc") / pid / "stat"
    if proc.exists() and proc.read_text().rsplit(")", 1)[1].split()[19] == str(
        owner["startTicks"]
    ):
        raise ValueError("Original native worker still exists")
    gpu = Path("/home/agent/gpu.lock").stat()
    for line in Path("/proc/locks").read_text().splitlines():
        parts = line.split()
        if len(parts) > 5 and parts[1] == "FLOCK" and parts[4] == pid:
            major, minor, inode = parts[5].split(":")
            if (int(major, 16), int(minor, 16), int(inode)) == (
                os.major(gpu.st_dev),
                os.minor(gpu.st_dev),
                gpu.st_ino,
            ):
                raise ValueError("Original owner holds GPU lease")
    h, files = inventory(source)
    if sum((source / n).stat().st_size for n in files) >= CAP:
        raise ValueError("Use a reviewed multipart export")
    target = REMOTE / (job + "-" + h + ".tgz")
    if not target.exists():
        tmp = target.with_suffix(".partial")
        with tarfile.open(tmp, "x:gz", compresslevel=1) as t:
            for n in sorted(files):
                t.add(source / n, arcname=n, recursive=False)
        tmp.rename(target)
    return {
        "file": target.name,
        "bytes": target.stat().st_size,
        "sha256": digest(target),
        "sourceReceiptPin": h,
        "files": len(files),
        "owner": owner,
        "release": release,
    }


def collect(job, remote_script):
    marker = LOCAL / (job + "-transfer.json")
    if marker.exists():
        return read(marker)
    if not re.fullmatch(
        r"/home/agent/tompathy-open/rapid-20261127/tools/[0-9a-f]{40}/rapid_collect\.py",
        remote_script,
    ):
        raise ValueError("Committed remote tool required")
    registration = digest(LOCAL / REGISTRATIONS[job])
    response = subprocess.check_output(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "spark",
            "python3",
            remote_script,
            "archive",
            job,
            registration,
        ]
    )
    record = json.loads(response)
    h = record["sourceReceiptPin"]
    if (
        not re.fullmatch("[a-f0-9]{64}", h)
        or record["file"] != job + "-" + h + ".tgz"
        or record["bytes"] >= CAP
    ):
        raise ValueError("Unexpected remote archive")
    path = LOCAL / record["file"]
    if not path.is_file():
        temp = path.with_suffix(".downloading")
        subprocess.run(
            ["scp", "-B", "spark:" + REMOTE.as_posix() + "/" + path.name, str(temp)],
            check=True,
        )
        if digest(temp) != record["sha256"]:
            raise ValueError("Transferred bytes differ")
        temp.rename(path)
    if digest(path) != record["sha256"] or path.stat().st_size != record["bytes"]:
        raise ValueError("Local archive differs")
    dest = LOCAL / ("verified-" + job + "-" + h[:12])
    dest.mkdir(exist_ok=True)
    seen = set()
    with tarfile.open(path, "r:gz") as t:
        for m in t:
            p = (dest / m.name).resolve()
            if (
                not m.isfile()
                or not p.is_relative_to(dest.resolve())
                or ":" in m.name
                or "\\" in m.name
                or m.name in seen
            ):
                raise ValueError("Unexpected archive member")
            seen.add(m.name)
            if not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                with t.extractfile(m) as source, p.open("xb") as f:
                    shutil.copyfileobj(source, f)
    actual, files = inventory(dest)
    if (
        actual != h
        or files != seen
        or len(seen) != record["files"]
        or read(dest / "released.json") != record["release"]
        or read(dest / "owner.json") != record["owner"]
    ):
        raise ValueError("Returned inventory or release differs")
    record.update(mirror=dest.as_posix(), nativeExited=True, ownedFlockReleased=True)
    marker.write_text(json.dumps(record, indent=2) + "\n", encoding="utf8")
    return record


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["archive", "collect"])
    p.add_argument("job", choices=tuple(REGISTRATIONS))
    p.add_argument("binding")
    a = p.parse_args()
    print(json.dumps((archive if a.action == "archive" else collect)(a.job, a.binding)))
