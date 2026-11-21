"""Single ModernBERT engineering continuation for the November 20 Spark ladder."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/agent/tompathy-open/word-table-20261120")
JOB = "G2-modernbert-a"
ORIGINAL = "91f2681cfc76e8a79116a6d38c32bf68bbec31dcef24dc8eefb0cb447cb82267"
SOURCE = "51c188e92b3473af802af78fd3ec4b10baceef0b13fc783516c4ef3c445194fe"
PACKAGE = "945ad3f651f683c11e72d19d804b1cff097308dcffa01057635cba038f875164"
LOCK = Path("/home/agent/gpu.lock")


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def exited(folder, *, has_dispatch=True):
    """A release file precedes actual exit. Accept only the exact released process."""
    if not (folder / "released.json").exists():
        return False
    owner = read(folder / "owner.json")
    release = read(folder / "released.json")
    if owner != release["owner"] or not release["descriptorClosed"] or owner["lock"] != str(LOCK):
        raise ValueError("Unexpected Spark release")
    if owner["bootId"] != Path("/proc/sys/kernel/random/boot_id").read_text().strip():
        raise ValueError("Spark reboot requires host review")
    proc = Path("/proc") / str(owner["pid"]) / "stat"
    if proc.exists() and proc.read_text().rsplit(") ", 1)[1].split()[19] == owner["startTicks"]:
        return False
    if has_dispatch:
        with (ROOT / "events.jsonl").open(encoding="utf8") as f:
            matches = [e for line in f if line.strip() and (e := json.loads(line))["event"] == "exit"
                       and e["job"] == owner["job"] and e["pid"] == owner["pid"]]
        if not matches:
            return False
        if matches[-1]["code"] != release["nativeExitCode"]:
            raise ValueError("Dispatcher exit differs from release")
    return True


def preflight(lane):
    reg = ROOT / "followups" / JOB
    cfg = read(reg / "execution.json")
    directory = Path(__file__).resolve().parent
    if (not re.fullmatch("[a-f0-9]{40}", cfg["commit"]) or directory != ROOT / "code" / cfg["commit"]
            or not {"word_table_g2_repair.py", "word_table_fine_runtime.py"} <= set(cfg["codePins"])):
        raise ValueError("Unregistered recovery program")
    for name, expected in cfg["codePins"].items():
        if Path(name).name != name or digest(directory / name) != expected:
            raise ValueError("Recovery snapshot differs")
    parent = ROOT / "jobs/G2"
    receipt = read(parent / "receipt.json")
    transfer = read(reg / "parent-transfer.json")
    if (digest(parent / "receipt.json") != ORIGINAL or receipt["status"] != "failed"
            or read(parent / "failed.json")["receiptPin"] != ORIGINAL or not exited(parent)
            or transfer["sourceReceiptPin"] != ORIGINAL or transfer["owner"] != receipt["owner"]
            or not transfer["nativeExited"] or not transfer["priorFlockReleased"]
            or transfer["verifiedFiles"] != 26937 or transfer["terminal"] != "failed.json"):
        raise ValueError("Original G2 exit and verified mirrored inventory are required")
    entry = read(ROOT / "queue.json")["jobs"]["G2"]
    if entry != receipt["entry"] or entry["commit"] != "992b1b683b434914ffe39e2b75f2ec5a5c35506c":
        raise ValueError("Original Spark registration changed")
    for name, pin in entry["codePins"].items():
        if name != "word_table_fine_runtime.py" and cfg["codePins"].get(name) != pin:
            raise ValueError("Scientific helper changed")
    _, binding = lane.check_entry(ROOT, "G2", entry)
    last = parent / "rung-2"
    if digest(last / "source.json") != SOURCE or any(p.is_file() for p in last.glob("seed-*/**/*")):
        raise ValueError("Expected the original encoder and zero durable ModernBERT training examples")
    header = ROOT / "repairs/g2-python-headers-a"
    headers = read(header / "verified.json")
    package, = header.glob("*.deb")
    include = header / "unpacked/usr/include"
    if (digest(package) != PACKAGE or headers["packagePin"] != PACKAGE or not headers["compiledAndLinked"]
            or digest(include / "python3.12/Python.h") != "729ef157f6026e6e1b3104593f87dddc597c3b83b60c7c2965878c62a56c6f7d"):
        raise ValueError("Exact locally extracted development headers are required")
    os.environ["CPATH"] = f"{include}/python3.12:{include}"
    return cfg, binding, last


def stop():
    return (ROOT / "STOP").exists() or (ROOT / "followups" / JOB / "STOP").exists()


def predecessors():
    return all(exited(ROOT / "jobs" / job) for job in ("Q6", "Q7"))


def worker(lane):
    from word_table_fine_runtime import run
    cfg, binding, last = preflight(lane)
    if stop() or not predecessors():
        return 74
    folder = ROOT / "jobs" / JOB
    try:
        with lane.lease(LOCK):
            if stop() or not predecessors():
                return 74
            folder.mkdir(exist_ok=False)
            owner = dict(lane.identity(), at=lane.now(), lock=str(LOCK), job=JOB, commit=cfg["commit"])
            lane.write(folder / "owner.json", owner)
            receipt = {"job": JOB, "lane": "spark", "owner": owner, "status": "running",
                           "parentReceiptPin": ORIGINAL, "entry": cfg, "scienceEntry": binding}
            lane.write(folder / "receipt.json", receipt)
            status = 1
            try:
                with lane.core.Guard(folder, float("inf")) as thermal:
                    guard = lane.Checks(ROOT, folder, thermal)
                    guard.check()
                    rows = run(ROOT, folder, binding, lane.core, guard, restored_modernbert=last)
                    guard.check()
                receipt.update(status="complete", ended=lane.now(), rows=rows)
                lane.write(folder / "receipt.json", receipt)
                lane.write(folder / "complete.json", {"receiptPin":digest(folder / "receipt.json")})
                status = 0
            except Exception as exc:  # noqa: BLE001 -- preserve terminal evidence for unexpected library errors too
                receipt.update(status="failed", ended=lane.now(), reason=str(exc))
                lane.write(folder / "receipt.json", receipt)
                lane.write(folder / "failed.json", {"receiptPin":digest(folder / "receipt.json")})
    except lane.Busy:
        return 74
    lane.write(folder / "released.json", {"owner": owner, "descriptorClosed": True,
                                              "nativeExitCode": status, "at": lane.now()})
    return status


def main():
    import word_table_lane as lane
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "standby", "worker"))
    action = parser.parse_args().action
    lane.settings()
    if action == "worker":
        return worker(lane)
    preflight(lane)
    if action == "check":
        return 0
    reg = ROOT / "followups" / JOB
    with lane.lease(reg / "standby.lock"):
        if (ROOT / "jobs" / JOB).exists():
            raise ValueError("Preserve the previous attempt")
        lane.write(reg / "standby.json", {"owner": lane.identity(), "at": lane.now(), "waitsFor": ["Q6","Q7"]})
        while not stop():
            if predecessors():
                proc = subprocess.Popen([sys.executable, __file__, "worker"])
                code = proc.wait()
                if code != 74:
                    lane.write(reg / "supervisor-exit.json", {"at": lane.now(), "pid": proc.pid, "code": code})
                    return code
            time.sleep(90)
        lane.write(reg / "standby-stopped.json", {"at":lane.now()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
