"""Counted entry point for subsequent R37 readouts while the earlier queue is frozen."""

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

from rapid_cpu_dispatch import ROOT
from rapid_cpu_dispatch import check as packet_check
from word_table_lane import now, pin, read, write


def run(plan, expected):
    if pin(plan) != expected:
        raise ValueError("Supplement registration differs")
    cfg = read(plan)
    if cfg["stage"] != "TP73-B-repeat" or cfg["attempt"] not in ("a", "b", "c"):
        raise ValueError("Unknown supplement or attempt")
    for name, digest in cfg["files"].items():
        if pin(Path(name)) != digest:
            raise ValueError("Registered supplement input changed: " + Path(name).name)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "2"
    sys.path.insert(0, str(Path("engine").resolve()))
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard

    benchmark_priority(2)
    counted_spec = importlib.util.spec_from_file_location(
        "counted", Path("scripts/engine-two-day-job.py")
    )
    counted = importlib.util.module_from_spec(counted_spec)
    counted_spec.loader.exec_module(counted)
    out = ROOT / (cfg["stage"] + "-" + cfg["attempt"])
    out.mkdir(exist_ok=False)
    deadline = min(time.time() + 8 * 3600, cfg["endUTCSeconds"])

    def check():
        packet_check()
        guard()
        if (out / "STOP").exists() or time.time() >= deadline:
            raise RuntimeError("Owner STOP or registered deadline")

    try:
        with counted.lease(
            Path("../SoundingLine/sounding-line").resolve(),
            out,
            card="ToMpathy-" + cfg["stage"],
        ):
            check()
            import rapid_author_repeat

            result = rapid_author_repeat.prepare(out, check)
            check()
            write(
                out / "receipt.json",
                {
                    "card": cfg["stage"],
                    "at": now(),
                    "status": "complete",
                    "registrationPin": expected,
                    "result": result,
                },
            )
            write(
                out / "complete.json", {"sourceReceiptPin": pin(out / "receipt.json")}
            )
    except Exception as exc:
        write(out / "failed.json", {"at": now(), "reason": str(exc)})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("registration", type=Path)
    parser.add_argument("sha256")
    args = parser.parse_args()
    run(args.registration, args.sha256)
