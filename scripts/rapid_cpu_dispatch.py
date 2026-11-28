"""Run the registered TP62 blocks serially and give the verified Q24 return the next slot."""

import subprocess
import sys
import time
from pathlib import Path

from word_table_lane import identity, lease, now, pin, read, write

ROOT = Path(".local/rapid-20261127")
VERIFIER = Path(".local/readers/verify-job.py")
BLOCKS = tuple(f"TP62-block-{i:02d}" for i in range(10))


def check():
    if time.time() >= 1795968000 or any(
        (p / "STOP").is_file() for p in (ROOT, Path(".local/week-20261122"))
    ):
        raise RuntimeError("Owner STOP or registered cutoff")


def confirmed(out):
    proof = read(out / "exit-verification.json")
    if not all(
        proof.get(k)
        for k in (
            "nativeExited",
            "releaseMatches",
            "localLeaseAbsent",
            "sharedLeaseAbsent",
        )
    ):
        raise ValueError("Cannot advance past an unverified release")
    source = pin(out / "receipt.json")
    if read(out / "complete.json") != {"sourceReceiptPin": source}:
        raise ValueError("Source receipt differs")
    return source


def capacity():
    """Read the same reservation and free-memory inputs as the scoring lease."""
    for folder in (
        Path("engine").resolve(),
        Path("../SoundingLine/sounding-line").resolve(),
    ):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
    from runners.drive.cards.week5_policy_v2 import (
        lease_paths,
        memory_reserve,
        shared_reservation,
    )
    from tompathy_engine.eval.back_half.resources import headroom

    paths = lease_paths()
    available = headroom()
    slots = 8 - int(shared_reservation()["active"])
    required = 14 + memory_reserve(paths)
    free = not Path(".local/bench/two-day-scoring.lock").exists()
    return {
        "at": now(),
        "headroom": available,
        "counted": len(paths),
        "capacity": slots,
        "requiredGiB": required,
        "localFree": free,
        "eligible": free and len(paths) < slots and min(available.values()) >= required,
    }


def execute(card):
    out = ROOT / (card + "-a")
    if not out.exists():
        check()
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().with_name("rapid_cpu.py")),
                card,
                "a",
            ],
            check=False,
        )
        if result.returncode:
            raise RuntimeError(
                f"{card} stopped. Preserve its private output for review."
            )
    if not (out / "complete.json").exists():
        raise ValueError(f"Existing partial output at {out}")
    if not (out / "exit-verification.json").exists():
        subprocess.run(
            [sys.executable, str(VERIFIER), str(out), "--exit"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    return confirmed(out)


def run():
    from rapid_head_check import bound

    confirmed(ROOT / "TP62-first-a")
    bound(
        Path(__file__).resolve().with_name("rapid_content.py"),
        "8e26f964a48326dd07cae0acaee17a6aaa69e7c0fb0b904d3beef5f29af355ba",
    )
    ctl = ROOT / "cpu-queue"
    ctl.mkdir(exist_ok=True)
    with lease(ctl / "dispatcher.lock"):
        worker = identity()
        write(
            ctl / "owner.json",
            {"owner": worker, "at": now(), "codePin": pin(Path(__file__))},
        )
        try:
            done = {}
            for card in BLOCKS:
                if (ROOT / "Q24-transfer.json").is_file() and "TP73-TP51" not in done:
                    done["TP73-TP51"] = execute("TP73-TP51")
                done[card] = execute(card)
                write(ctl / "progress.json", {"at": now(), "verified": done})
            if "TP73-TP51" not in done and (ROOT / "Q24-transfer.json").is_file():
                done["TP73-TP51"] = execute("TP73-TP51")
            write(
                ctl / "complete.json", {"at": now(), "verified": done, "owner": worker}
            )
        except Exception as exc:
            write(
                ctl / "stopped.json", {"at": now(), "owner": worker, "reason": str(exc)}
            )
            raise


if __name__ == "__main__":
    run()
