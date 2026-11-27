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
            elif card == "TP61-repeat":
                import rapid_worry_repeat as study

                result = study.prepare(out, check)
            elif card == "TP61-words":
                import rapid_word_repeat as study

                result = study.prepare(out, check)
            elif card == "TP62-first":
                import rapid_content as study

                result = study.run(out, check, [("trained", 0), ("iso", 0), ("rot", 0)])
            elif card.startswith("TP62-block-"):
                import rapid_content as study
                import rapid_nulls

                first = LOCAL / "TP62-first-a"
                if (
                    pin(first / "receipt.json")
                    != "3f48e3ff2698f1d106259c8496da5e012bd83aa25e8582ff46af57bb2ab0e637"
                ):
                    raise ValueError("The registered first block differs")
                if (
                    pin(Path(study.__file__))
                    != "8e26f964a48326dd07cae0acaee17a6aaa69e7c0fb0b904d3beef5f29af355ba"
                    or pin(Path(rapid_nulls.__file__))
                    != "f33f6b66e9d4d53604fc41b4a5f5c401ee9345144433f3b3aa16d6f1f068f8ff"
                ):
                    raise ValueError("The inspected science implementation differs")
                block = int(card.rsplit("-", 1)[-1])
                indices = range(1 + 20 * block, min(21 + 20 * block, 200))
                result = study.run(
                    out, check, [(k, i) for i in indices for k in ("iso", "rot")]
                )
                if result["meta"] != study.read(first / "design.json"):
                    raise ValueError("The fixed chat roster or design differs")
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
        "card",
        choices=[
            "TP61-chat-check",
            "TP61-roster",
            "TP61-repeat",
            "TP61-words",
            "TP62-first",
            "TP73-TP51",
            *(f"TP62-block-{i:02d}" for i in range(10)),
        ],
    )
    p.add_argument("attempt", choices=["a", "b", "c"])
    args = p.parse_args()
    run(args.card, args.attempt)
