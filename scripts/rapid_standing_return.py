"""Bind the completed standing panels to the two original workers and the common roster."""

import argparse
import json
import shlex
import subprocess
import time
from pathlib import Path

from rapid_collect import collect, inventory
from rapid_cpu_dispatch import ROOT, check
from word_table_lane import identity, lease, now, pin, read, write

REMOTE = "/home/agent/tompathy-open/rapid-20261127"
COLLECTOR = REMOTE + "/tools/254b5f5eeca922744adb085662850f4d39fcaa7f/rapid_collect.py"
COLLECTOR_SHA = "9e2b53ea86406eeccd114f3b3834d8e666c69c8fe68509ec596755faacf14d0d"
REG = "2aaa9e0fc722a48e40e854b61dddc9b9c2a03828233e2c0fc3175afdcffa7f6a"
WINDOWS_JOB = ROOT / "jobs/G12"


def state_spark():
    # Read only this commission's markers. Do not start an archive during the C panel.
    source = """import json
from pathlib import Path
r=Path('/home/agent/tompathy-open/rapid-20261127/jobs')
def has(job, name): return (r/job/name).is_file()
p=r/'Q28/progress.json'
d=json.loads(p.read_bytes()) if p.is_file() else {}
print(json.dumps({'q27Release':has('Q27','released.json'),'q27Failed':has('Q27','failed.json'),
    'q28Started':has('Q28','owner.json'),'q28Release':has('Q28','released.json'),
    'q28Failed':has('Q28','failed.json'),'q28Left':d.get('total',6600)-d.get('rows',0),
    'q32Done':has('Q32','released.json'),'q32Started':has('Q32','owner.json')}))
"""
    response = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=15",
            "spark",
            "python3",
            "-",
        ],
        input=source,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    return json.loads(response.stdout)


def spark_window(state):
    if not state["q27Release"]:
        return False
    if state["q27Failed"]:
        raise RuntimeError("Q27 stopped; preserve its partial rows")
    if state["q32Done"]:
        return True
    if state["q32Started"]:
        return False
    # Q32 follows Q28. A late observer waits through C if B has almost finished.
    return state["q28Failed"] or (not state["q28Release"] and state["q28Left"] >= 1500)


def windows(plan):
    from rapid_lane_state import live

    release = read(WINDOWS_JOB / "released.json")
    owner = read(WINDOWS_JOB / "owner.json")
    witness = read(ROOT / "workstation-follow/watching.json")
    if (
        owner != plan["W"]
        or owner != witness["native"]
        or release["owner"] != owner
        or release["wrapper"] != witness["shim"]
        or release["witnessedBy"] != witness["observer"]
        or not all(
            release[k] for k in ("childWaited", "sharedLeaseReacquired", "nativeExited")
        )
        or live(owner)
        or live(witness["shim"])
    ):
        raise ValueError("G12 native exit or GPU lease proof differs")
    if release["exitCode"]:
        return memory_prefix(owner, release)
    source, files = inventory(WINDOWS_JOB)
    return {
        "sourceReceiptPin": source,
        "owner": owner,
        "releasePin": pin(WINDOWS_JOB / "released.json"),
        "mirror": WINDOWS_JOB.as_posix(),
        "fileCount": len(files),
        "nativeExited": True,
        "ownedGpuLockReleased": True,
    }


def memory_prefix(owner, release):
    """Admit only the original G12 floor stop via the verified DU manifest."""
    prefix = ROOT.parent / "day-20261128/jobs/G12r/W-prefix.json"
    proof = read(prefix)
    failed = read(WINDOWS_JOB / "failed.json")
    if (
        failed["owner"] != owner
        or failed["error"] != "Available commit reached the 8 GiB floor"
        or proof["job"] != "G12"
        or owner["registration"] != REG
        or proof["firstOrdinal"] != 0
        or proof["nextOrdinal"] != len(proof["files"])
        or proof["original"]["owner.json"] != pin(WINDOWS_JOB / "owner.json")
        or proof["original"]["failed.json"] != pin(WINDOWS_JOB / "failed.json")
        or proof["original"]["released.json"] != pin(WINDOWS_JOB / "released.json")
        or release["owner"] != owner
        or not release["nativeExited"]
    ):
        raise ValueError("DU prefix is not bound to the witnessed stopped worker")
    return {
        "status": "memory-prefix",
        "sourceReceiptPin": pin(prefix),
        "manifest": str(prefix),
        "mirror": str(WINDOWS_JOB),
        "owner": owner,
        "nativeExited": True,
        "ownedGpuLockReleased": True,
        "releasePin": pin(WINDOWS_JOB / "released.json"),
        "nextOrdinal": proof["nextOrdinal"],
        "valid": proof["valid"],
        "sources": proof["sources"],
    }


def confirm_spark(plan):
    cmd = "sha256sum " + shlex.quote(COLLECTOR)
    actual = subprocess.check_output(
        ["ssh", "-o", "BatchMode=yes", "spark", cmd], text=True, timeout=30
    ).split()
    if actual != [COLLECTOR_SHA, COLLECTOR]:
        raise ValueError("Remote job verifier differs from its committed source")
    entry = collect("Q27", COLLECTOR)
    owner = entry["owner"]
    if (
        any(owner[k] != v for k, v in plan["B"].items())
        or owner["job"] != "Q27"
        or owner["registration"] != REG
    ):
        raise ValueError("Original Q27 owner differs")
    if not (
        entry["nativeExited"]
        and entry["ownedFlockReleased"]
        and entry["release"]["sharedLeaseReacquired"]
    ):
        raise ValueError("Missing Spark exit or lease release")
    return {
        "sourceReceiptPin": entry["sourceReceiptPin"],
        "mirror": entry["mirror"],
        "fileCount": entry["files"],
        "archiveSha256": entry["sha256"],
        "nativeExited": True,
        "ownedGpuLockReleased": True,
    }


def watch(registration, expected):
    plan = read(registration)
    if (
        pin(registration) != expected
        or pin(Path(__file__)) != plan["watcher"]
        or pin(Path(__file__).with_name("rapid_collect.py")) != plan["localCollector"]
        or pin(ROOT / "registration.json") != REG
        or pin(ROOT / "workstation-follow/watching.json") != plan["witness"]
    ):
        raise ValueError("Standing return or original GPU registration differs")
    ctl = registration.parent
    if (ctl / "armed.json").exists():
        raise FileExistsError("Standing-panel observer already exists")
    with lease(ctl / "observer.lock"):
        me = identity()
        write(
            ctl / "armed.json", {"owner": me, "registrationPin": expected, "at": now()}
        )
        try:
            a = b = None
            io_errors = 0
            while a is None or b is None:
                check()
                if (ctl / "STOP").exists():
                    raise RuntimeError("Owner stopped standing result collection")
                if b is None and (WINDOWS_JOB / "released.json").is_file():
                    b = windows(plan)
                    write(ctl / "workstation.json", b)
                if a is None:
                    try:
                        state = state_spark()
                    except (subprocess.SubprocessError, OSError) as exc:
                        io_errors += 1
                        write(
                            ctl / "transport.json",
                            {
                                "at": now(),
                                "consecutive": io_errors,
                                "errorType": type(exc).__name__,
                            },
                        )
                        if io_errors >= 3:
                            raise
                    else:
                        io_errors = 0
                        if spark_window(state):
                            a = confirm_spark(plan)
                            write(ctl / "spark.json", a)
                if a is None or b is None:
                    time.sleep(120)
            write(
                ctl / "complete.json",
                {"at": now(), "owner": me, "registrationPin": expected, "B": a, "W": b},
            )
        except BaseException as exc:
            write(ctl / "stopped.json", {"at": now(), "owner": me, "reason": str(exc)})
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("registration", type=Path)
    parser.add_argument("sha256")
    args = parser.parse_args()
    watch(args.registration, args.sha256)
