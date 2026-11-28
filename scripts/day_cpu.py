"""Round 38 one-card CPU dispatcher, using the original counted admission and exit witness."""

import argparse
import importlib.util
import math
import numbers
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
DAY = ROOT / ".local/day-20261128"
PACKET = ROOT / "TOMPATHY_0.3_ENGINE_ONE_DAY_PACKET_2026-11-28.md"
LIMIT = 1795968000
for env in (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
):
    os.environ[env] = "2"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from word_table_lane import identity, lease, now, pin, read, write


def differences(first, second, path="result"):
    if (
        isinstance(first, dict)
        and isinstance(second, dict)
        and first.keys() == second.keys()
    ):
        return [
            v
            for key in first
            for v in differences(first[key], second[key], path + "." + key)
        ]
    if (
        isinstance(first, list)
        and isinstance(second, list)
        and len(first) == len(second)
    ):
        return [
            v
            for i, (a, b) in enumerate(zip(first, second, strict=True))
            for v in differences(a, b, f"{path}[{i}]")
        ]
    if isinstance(first, numbers.Real) and isinstance(second, numbers.Real):
        if (
            math.isfinite(first)
            and math.isfinite(second)
            and abs(first - second) <= 0.001
        ):
            return []
    elif first == second:
        return []
    return [path]


def check():
    if time.time() >= LIMIT or any(
        (p / "STOP").is_file()
        for p in (
            DAY,
            DAY / "TP81-a",
            ROOT / ".local/rapid-20261127",
            ROOT / ".local/week-20261122",
        )
    ):
        raise RuntimeError("Owner stop or cutoff")


def work(out, plan):
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard

    benchmark_priority(2)

    def guard_card():
        check()
        guard()

    spec = importlib.util.spec_from_file_location(
        "counted", Path(__file__).with_name("engine-two-day-job.py")
    )
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    if out.exists():
        raise FileExistsError("Preserve earlier attempt")
    out.mkdir()
    try:
        with counted.lease(
            ROOT.parent / "SoundingLine/sounding-line", out, card="ToMpathy-TP81"
        ):
            guard_card()
            import day_ceiling_a
            import day_ceiling_b
            import numpy as np
            from day_ceiling_inputs import prepare

            source = prepare(out, guard_card)
            write(out / "input.json", source)
            file = out / "TP81-inputs.npz"
            results = []
            for label, build in (
                ("a", day_ceiling_a.build),
                ("b", day_ceiling_b.analyze),
            ):
                if pin(file) != source["pin"]:
                    raise ValueError("Shared inputs changed")
                with np.load(file, allow_pickle=False) as data:
                    result = build(dict(data), guard_card)
                write(out / ("build-" + label + ".json"), result)
                results.append(result)
            delta = differences(*results)
            write(out / "comparison.json", {"tolerance": 0.001, "differences": delta})
            if delta:
                raise ValueError("DZ disagreement. See comparison.json")
            guard_card()
            write(
                out / "receipt.json",
                {
                    "card": "TP81",
                    "at": now(),
                    "source": source,
                    "registration": plan,
                    "buildA": pin(out / "build-a.json"),
                    "buildB": pin(out / "build-b.json"),
                    "comparison": pin(out / "comparison.json"),
                },
            )
            write(
                out / "complete.json", {"sourceReceiptPin": pin(out / "receipt.json")}
            )
    except Exception as exc:
        write(out / "failed.json", {"at": now(), "reason": str(exc)})
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("serve", "work"))
    p.add_argument("plan")
    args = p.parse_args()
    from rapid_cpu_dispatch import capacity
    from tompathy_engine.eval.back_half.resources import benchmark_priority

    benchmark_priority(2)
    source = DAY / "TP81-plan.json"
    if pin(source) != args.plan:
        raise ValueError("Registration changed")
    cfg = read(source)
    script = Path(__file__).resolve()
    if script.parents[1].name != cfg["commit"] or pin(PACKET) != cfg["packetPin"]:
        raise ValueError("Wrong snapshot or study packet")
    for name, expected in cfg["code"].items():
        if pin(script.parents[1] / name) != expected:
            raise ValueError("Pinned CPU dependency differs: " + name)
    out = DAY / "TP81-a"
    if args.action == "work":
        work(out, args.plan)
        return
    ctl = DAY / "TP81-admission"
    ctl.mkdir(exist_ok=True)
    with lease(ctl / "observer.lock"):
        if out.exists() or (ctl / "armed.json").exists():
            raise ValueError("An admission observer or job has already been recorded")
        write(ctl / "armed.json", {"owner": identity(), "at": now(), "plan": args.plan})
        try:
            while True:
                check()
                state = capacity()
                write(ctl / "capacity.json", state)
                if state["eligible"]:
                    break
                time.sleep(60)
            subprocess.run(
                [sys.executable, "-B", str(script), "work", args.plan], check=True
            )
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / ".local/readers/verify-job.py"),
                    str(out),
                    "--exit",
                ],
                check=True,
            )
            write(
                ctl / "complete.json",
                {"at": now(), "receiptPin": pin(out / "receipt.json")},
            )
        except Exception as exc:
            write(ctl / "stopped.json", {"at": now(), "error": str(exc)})
            raise


if __name__ == "__main__":
    main()
