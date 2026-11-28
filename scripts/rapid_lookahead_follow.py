"""Prepare TP75's paired inputs when the exact Q31 receiving process finishes filing."""

import argparse
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

from rapid_cpu_dispatch import ROOT, VERIFIER, capacity, check, confirmed
from rapid_windows_follow import Process
from word_table_lane import identity, lease, now, pin, read, write


def follow(path, expected):
    ctl = ROOT / "TP75-lookahead-follow"
    previous = ROOT / "Q31-completion"
    cfg = read(path)
    if (
        path != ctl / "registration.json"
        or pin(path) != expected
        or cfg["stage"] != "TP75-lookahead-inputs"
        or pin(previous / "armed.json") != cfg["predecessorArmedPin"]
    ):
        raise ValueError("Unexpected TP75 predecessor or registration")
    armed = read(previous / "armed.json")
    out = ROOT / (cfg["stage"] + "-" + cfg["attempt"])

    def guard():
        check()
        if (ctl / "STOP").exists() or (previous / "stopped.json").exists():
            raise RuntimeError("TP75 STOP or failed Q31 receiver")

    with lease(ctl / "observer.lock"):
        if (ctl / "armed.json").exists() or out.exists():
            raise FileExistsError("Existing TP75 intake or observer")
        owner = identity()
        try:
            guard()
            with closing(
                Process(armed["owner"]["pid"], armed["owner"]["createdTicks"])
            ) as proc:
                write(
                    ctl / "armed.json",
                    {
                        "owner": owner,
                        "at": now(),
                        "registration": expected,
                        "predecessor": armed["owner"],
                    },
                )
                if proc.wait(guard) != 0:
                    raise RuntimeError("Q31 receiver stopped")
            guard()
            receipt = confirmed(ROOT / "TP77-Q31-a")
            if read(previous / "complete.json")["agreementReceipt"] != receipt:
                raise ValueError("Q31 agreement was not filed")
            while True:
                guard()
                state = capacity()
                write(ctl / "admission.json", state)
                if state["eligible"]:
                    break
                time.sleep(120)
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "scripts/rapid_mark_job.py",
                    str(path),
                    expected,
                ],
                check=True,
            )
            subprocess.run(
                [sys.executable, str(VERIFIER), str(out), "--exit"], check=True
            )
            write(
                ctl / "complete.json",
                {"owner": owner, "at": now(), "sourceReceiptPin": confirmed(out)},
            )
        except Exception as exc:
            write(
                ctl / "stopped.json", {"owner": owner, "at": now(), "reason": str(exc)}
            )
            raise


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("registration", type=Path)
    ap.add_argument("pin")
    args = ap.parse_args()
    follow(args.registration, args.pin)
