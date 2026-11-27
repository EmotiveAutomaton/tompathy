"""Verify the exact TP61(d) exit, all 400 set outputs, and the slope-only transfer."""

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

REMOTE = "/home/agent/tompathy-open/rapid-20261127"
SOURCE = "9848dada6d2d9bddaea9590119d8bc38954844bdce618e6c69ccf9810a5f6402"
PREP = "258d14c8405973cb7db874895a18a46e054241c3638e89d39bf73aef7941f02d"


def pin(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def verify():
    import fcntl

    root = Path(REMOTE)
    out = root / "TP61-slope-a"
    r = read(out / "receipt.json")
    owner = r["owner"]
    if (
        owner != read(out / "owner.json")
        or owner["job"] != "TP61-slope"
        or owner["bootId"]
        != Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        or pin(out / "receipt.json") != SOURCE
        or read(out / "complete.json") != {"sourceReceiptPin": SOURCE}
        or r["sourceReceiptPin"] != PREP
        or r["data"] != {"posts": 85591, "authors": 2536}
    ):
        raise ValueError("Source or terminal identity differs")
    stat = Path("/proc") / str(owner["pid"]) / "stat"
    if (
        stat.exists()
        and stat.read_text().rsplit(")", 1)[1].split()[19] == owner["startTicks"]
    ):
        raise ValueError("Wait for the native worker exit")
    with (root / "TP61-vector-cpu.lock").open("rb") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        expected = {"owner.json", "receipt.json", "complete.json", "pilot.json"}
        for kind in ("iso", "rot"):
            values = []
            for i in range(200):
                name = f"{kind}-{i:03d}.json"
                expected.add(name)
                item = read(out / name)
                if (
                    item["set"] != i
                    or item["family"] != kind
                    or len(item["slopes"]) != 19
                    or item["authors"] != [2536] * 19
                    or not all(math.isfinite(x) for x in item["slopes"])
                ):
                    raise ValueError("A saved null slope is unbound or incomplete")
                values.extend(item["slopes"])
            if values != r["nullSlopes"][kind]:
                raise ValueError("Returned slopes differ from the saved sets")
        if {p.name for p in out.iterdir()} != expected:
            raise ValueError("Unexpected slope inventory")
        print(
            json.dumps(
                {
                    "sourceReceiptPin": SOURCE,
                    "setsVerified": 400,
                    "nativeExited": True,
                    "cpuLeaseReacquired": True,
                    "owner": owner,
                    "pilot": read(out / "pilot.json"),
                }
            )
        )


def receive(commit):
    if not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("Committed collector required")
    proof = json.loads(
        subprocess.check_output(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "spark",
                "/home/agent/venvs/engine/bin/python",
                f"{REMOTE}/tools/{commit}/rapid_slope_return.py",
                "verify",
            ],
            text=True,
        )
    )
    if (
        proof["sourceReceiptPin"] != SOURCE
        or not proof["nativeExited"]
        or not proof["cpuLeaseReacquired"]
    ):
        raise ValueError("Terminal proof missing")
    out = Path(".local/rapid-20261127/verified-TP61-slopes-" + SOURCE[:12])
    out.mkdir(exist_ok=True)
    path = out / "receipt.json"
    if not path.exists():
        tmp = out / "receipt.partial"
        subprocess.run(
            [
                "scp",
                "-q",
                "-o",
                "BatchMode=yes",
                "spark:" + REMOTE + "/TP61-slope-a/receipt.json",
                str(tmp),
            ],
            check=True,
        )
        if pin(tmp) != SOURCE:
            raise ValueError("Slope transfer differs")
        tmp.rename(path)
    if pin(path) != SOURCE:
        raise ValueError("Local receipt differs")
    audit = out / "transfer.json"
    if audit.exists():
        if read(audit) != proof:
            raise ValueError("Prior verification differs")
    else:
        with audit.open("x", encoding="utf8") as f:
            json.dump(proof, f, indent=2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["verify", "receive"])
    p.add_argument("--commit")
    a = p.parse_args()
    if a.action == "verify":
        verify()
    else:
        receive(a.commit)
