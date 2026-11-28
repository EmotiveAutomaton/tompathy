"""Return Q31 on its native exit, then run and file the registered blog agreement once."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REMOTE = Path("/home/agent/tompathy-open/rapid-20261127")
END = 1795968000
SCRIPT = "rapid_q31_receive.py"


def load(p):
    return json.loads(p.read_bytes())


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def wait(owner_pin):
    import select

    base = REMOTE / "jobs/Q31"
    ownerfile = base / "owner.json"
    if sha(ownerfile) != owner_pin:
        raise ValueError("Different Q31 owner")
    o = load(ownerfile)

    def check():
        if (
            o["job"] != "Q31"
            or Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            != o["bootId"]
            or time.time() >= END
            or any(
                (d / "STOP").exists()
                for d in (REMOTE, base, REMOTE.parent / "week-20261122")
            )
        ):
            raise RuntimeError("Cutoff, stop or host identity change")

    check()
    if not (base / "released.json").is_file():
        fd = os.pidfd_open(o["pid"])
        try:
            stat = Path("/proc") / str(o["pid"]) / "stat"
            if stat.read_text().rsplit(")", 1)[1].split()[19] != str(o["startTicks"]):
                raise ValueError("Q31 native process changed")
            watcher = select.poll()
            watcher.register(fd, select.POLLIN)
            print("attached", flush=True)
            while not watcher.poll(60000):
                check()
        finally:
            os.close(fd)
        for _ in range(120):
            check()
            if (base / "released.json").is_file():
                break
            time.sleep(1)
    else:
        print("released", flush=True)
    release = load(base / "released.json")
    source = sha(base / "receipt.json")
    if (
        release["owner"] != o
        or release["exitCode"]
        or not release["childWaited"]
        or not release["sharedLeaseReacquired"]
        or load(base / "complete.json") != {"sourceReceiptPin": source}
    ):
        raise ValueError("Original Q31 outcome or release requires review")
    print(source, flush=True)


def receive(plan, expected):
    import re

    from rapid_collect import collect
    from rapid_cpu_dispatch import ROOT, capacity, check, execute
    from word_table_lane import identity, lease, now, write

    if sha(plan) != expected or plan.parent != ROOT / "Q31-completion":
        raise ValueError("Unexpected receiver registration")
    cfg = load(plan)
    ctl = plan.parent

    def bound():
        check()
        if (ctl / "STOP").exists() or any(
            sha(Path(p)) != h for p, h in cfg["localFiles"].items()
        ):
            raise ValueError("Receiver stop or registered implementation changed")

    bound()
    with lease(ctl / "receiver.lock"):
        if (ctl / "armed.json").exists():
            raise FileExistsError("Existing Q31 completion observer")
        try:
            if not re.fullmatch("[a-f0-9]{40}", cfg["revision"]):
                raise ValueError("Invalid receiver revision")
            path = f"{REMOTE.as_posix()}/tools/{cfg['revision']}/{SCRIPT}"
            cmd = [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ServerAliveInterval=45",
                "spark",
                "/home/agent/venvs/engine/bin/python",
                "-B",
                path,
                "wait",
                cfg["ownerPin"],
            ]
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True) as p:
                if p.stdout.readline().strip() not in {"attached", "released"}:
                    raise ValueError("No remote attachment to the original job")
                write(
                    ctl / "armed.json",
                    {
                        "at": now(),
                        "owner": identity(),
                        "planPin": expected,
                        "predecessor": cfg["ownerPin"],
                    },
                )
                source = p.stdout.readline().strip()
                if p.wait() != 0 or not re.fullmatch("[a-f0-9]{64}", source):
                    raise ValueError("Q31 stopped or remote completion was interrupted")
            bound()
            record = collect("Q31", cfg["collector"])
            if source != record["sourceReceiptPin"]:
                raise ValueError("Returned aggregate differs from the original job")
            write(ctl / "collected.json", {"at": now(), "sourceReceiptPin": source})
            while True:
                bound()
                s = capacity()
                write(ctl / "admission.json", s)
                if s["eligible"]:
                    break
                time.sleep(120)
            stage = "TP77-Q31"
            result = execute(stage)
            from rapid_lane_state import get
            from rapid_panel_return import file

            file(stage, get())
            subprocess.run([sys.executable, "-B", "scripts/r48_reports.py"], check=True)
            subprocess.run(
                [sys.executable, "-B", "scripts/r48_reports.py", "--check"], check=True
            )
            write(
                ctl / "complete.json",
                {"at": now(), "BReceipt": source, "agreementReceipt": result},
            )
        except Exception as exc:
            write(ctl / "stopped.json", {"at": now(), "error": str(exc)})
            raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["wait", "receive"])
    p.add_argument("binding")
    p.add_argument("plan", type=Path, nargs="?")
    a = p.parse_args()
    if a.action == "wait":
        wait(a.binding)
    else:
        receive(a.plan, a.binding)
