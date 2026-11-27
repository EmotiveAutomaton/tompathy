"""Counted entry point for the direct TP67 agency analysis."""

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

from rapid_cpu_dispatch import ROOT, check
from word_table_lane import now, pin, read, write


def run(plan, digest):
    cfg = read(plan)
    if (
        pin(plan) != digest
        or cfg["stage"] != "TP67-agency"
        or cfg["attempt"] not in ("a", "b", "c")
    ):
        raise ValueError("Unregistered direct agency study")
    for name, expected in cfg["files"].items():
        if pin(Path(name)) != expected:
            raise ValueError("A registered agency input changed: " + Path(name).name)
    for k in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[k] = "2"
    sys.path.insert(0, str(Path("engine").resolve()))
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard

    benchmark_priority(2)
    spec = importlib.util.spec_from_file_location(
        "counted", Path("scripts/engine-two-day-job.py")
    )
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    work = ROOT / (cfg["stage"] + "-" + cfg["attempt"])
    work.mkdir(exist_ok=False)
    deadline = min(cfg["endUTCSeconds"], time.time() + 8 * 3600)

    def guard_job():
        check()
        if (
            (plan.parent / "STOP").exists()
            or (work / "STOP").exists()
            or time.time() >= deadline
        ):
            raise RuntimeError("Owner STOP or agency deadline")
        write(work / "heartbeat.json", {"at": now(), "headroom": guard()})

    try:
        with counted.lease(
            Path("../SoundingLine/sounding-line").resolve(),
            work,
            card="ToMpathy-TP67-agency",
        ):
            guard_job()
            from rapid_pride_agency import prepare

            result = prepare(work, guard_job)
            guard_job()
            write(
                work / "receipt.json",
                {
                    "status": "complete",
                    "card": cfg["stage"],
                    "at": now(),
                    "registrationPin": digest,
                    "result": result,
                },
            )
            write(
                work / "complete.json", {"sourceReceiptPin": pin(work / "receipt.json")}
            )
    except Exception as exc:
        write(work / "failed.json", {"at": now(), "reason": str(exc)})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("sha256")
    args = parser.parse_args()
    run(args.plan, args.sha256)
