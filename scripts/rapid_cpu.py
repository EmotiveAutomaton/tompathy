"""One counted local analysis, with the same shared reservation and memory policy as TP45."""

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local/rapid-20261127"
sys.path.insert(0, str(ROOT / "engine"))


def run(card, attempt):
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "2"
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard
    from word_table_lane import now, pin, write

    benchmark_priority(2)
    spec = importlib.util.spec_from_file_location(
        "counted", ROOT / "scripts/engine-two-day-job.py"
    )
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    out = LOCAL / (card + "-" + attempt)
    out.mkdir(exist_ok=False)
    end = min(time.time() + 8 * 3600, 1795968000)
    packet = ROOT / "TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-27.md"
    if (
        pin(packet)
        != "ca67d5b9f490c7ab08969213facaf982e0e52762f6f038215e471f6eb3ae4a48"
    ):
        raise ValueError("Round 37 packet differs")

    def check():
        guard()
        if time.time() >= end or any(
            (p / "STOP").exists() for p in (out, LOCAL, ROOT / ".local/week-20261122")
        ):
            raise RuntimeError("Owner STOP or analysis deadline")

    try:
        with counted.lease(
            ROOT.parent / "SoundingLine/sounding-line", out, card="ToMpathy-" + card
        ):
            check()
            if card == "TP61-chat-check":
                import rapid_head_check as study

                result = study.chat()
            elif card == "TP61-roster":
                import rapid_head_roster as study

                result = study.prepare(out, check)
            elif card == "TP62-first":
                import rapid_content as study

                result = study.run(out, check, [("trained", 0), ("iso", 0), ("rot", 0)])
            elif card == "TP73-TP51":
                import week_competence_q24 as study
                from rapid_collect import read

                handoff = read(LOCAL / "Q24-transfer.json")
                result = study.prepare(
                    Path(handoff["mirror"]), handoff["receiptPin"], check
                )
            check()
            write(
                out / "receipt.json",
                {
                    "card": card,
                    "status": "complete",
                    "at": now(),
                    "packetPin": pin(packet),
                    "codePin": pin(Path(study.__file__)),
                    "result": result,
                },
            )
            write(
                out / "complete.json", {"sourceReceiptPin": pin(out / "receipt.json")}
            )
    except Exception as exc:
        write(out / "failed.json", {"card": card, "at": now(), "reason": str(exc)})
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "card", choices=["TP61-chat-check", "TP61-roster", "TP62-first", "TP73-TP51"]
    )
    p.add_argument("attempt", choices=["a", "b", "c"])
    args = p.parse_args()
    run(args.card, args.attempt)
