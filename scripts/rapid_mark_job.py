"""Run a source-registered mark analysis in the packet's counted workstation slot."""

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
    cfg = read(plan)
    if (
        pin(plan) != expected
        or cfg["stage"]
        not in {
            "TP77-standing",
            "TP61-highest",
            "TP61-date-matching",
            "TP75-lookahead-inputs",
        }
        or cfg["attempt"] not in ("a", "b", "c")
    ):
        raise ValueError("Unregistered mark analysis")
    if any(pin(Path(f)) != h for f, h in cfg["files"].items()):
        raise ValueError("A frozen mark-analysis input differs")
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
    spec = importlib.util.spec_from_file_location(
        "counted", Path("scripts/engine-two-day-job.py")
    )
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    end = min(time.time() + 8 * 3600, 1795968000)
    out = ROOT / (cfg["stage"] + "-" + cfg["attempt"])
    out.mkdir(exist_ok=False)

    def check():
        packet_check()
        guard()
        if (out / "STOP").exists() or time.time() >= end:
            raise RuntimeError("Owner STOP or mark analysis deadline")

    try:
        with counted.lease(
            Path("../SoundingLine/sounding-line").resolve(),
            out,
            card="ToMpathy-" + cfg["stage"],
        ):
            check()
            if cfg["stage"] == "TP75-lookahead-inputs":
                from rapid_lookahead import prepare
            elif cfg["stage"] == "TP61-date-matching":
                from rapid_date_matching import prepare
            elif cfg["stage"] == "TP61-highest":
                from rapid_highest_need import prepare
            else:
                from rapid_standing_agreement import prepare

            result = prepare(out, check)
            check()
            write(
                out / "receipt.json",
                {
                    "at": now(),
                    "status": "complete",
                    "card": cfg["stage"],
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
