"""Reproduce the existing 234-target handling baseline without research imports.

Inputs stay at caller-supplied local paths. Output contains only scores, hashed
keys, fit cutoffs and source hashes. This is a port check, not fresh admission.
"""

import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.special import softmax

from ..models.reference import ACTIONS, features, global_fit, intercept_fit, matrix, proper


def reproduce(training, targets, progress=lambda _: None):
    targets = [r for r in targets if not r["pilot"]]
    wanted = {r["writer"] for r in targets}
    histories = {r["key"]: r for config in training.values() for r in config["history"]}
    history = sorted(histories.values(), key=lambda r: (r["open_at"], r["key"]))
    results, fits = [], []
    for writer, config in training.items():
        if writer not in wanted:
            continue
        own = sorted(config["history"], key=lambda r: (r["open_at"], r["key"]))
        calibration = own[max(4, int(0.8 * len(own))) :]
        if not calibration:
            raise ValueError("Empty earlier calibration slice")
        split = min(r["open_at"] for r in calibration)
        past = [r for r in history if r["resolved_at"] < split]
        x = matrix(past, False)
        y = np.array([ACTIONS.index(r["handling"]) for r in past])
        weights = global_fit(x, y)
        ownpast = [r for r in past if r["writer"] == writer]
        ox = matrix(ownpast, False)
        oy = np.array([ACTIONS.index(r["handling"]) for r in ownpast])
        cx = np.array(
            [
                features(r, [p for p in ownpast if p["resolved_at"] <= r["open_at"]], False)
                for r in calibration
            ]
        )
        cy = np.array([ACTIONS.index(r["handling"]) for r in calibration])
        candidates = []
        for penalty in (0.01, 0.1, 1.0, 10.0):
            residual = intercept_fit(ox @ weights, oy, np.ones(len(oy)), penalty)
            probabilities = softmax(cx @ weights + residual, axis=1)
            candidates.append(
                (np.mean([proper(p, t)["half_brier"] for p, t in zip(probabilities, cy)]), penalty)
            )
        penalty = min(candidates)[1]
        past = [r for r in history if r["resolved_at"] <= config["cutoff"]]
        x = matrix(past, False)
        y = np.array([ACTIONS.index(r["handling"]) for r in past])
        weights = global_fit(x, y)
        ownpast = [r for r in past if r["writer"] == writer]
        ox = matrix(ownpast, False)
        oy = np.array([ACTIONS.index(r["handling"]) for r in ownpast])
        selected = [r for r in targets if r["writer"] == writer]
        if any(r["open_at"] < config["cutoff"] for r in selected):
            raise ValueError("Training cutoff follows target opening")
        tx = np.array([features(r, ownpast, False) for r in selected])
        residual = intercept_fit(ox @ weights, oy, np.ones(len(oy)), penalty)
        probabilities = softmax(tx @ weights + residual, axis=1)
        population = np.bincount(y, minlength=4) + 1.0
        population /= population.sum()
        for row, p in zip(selected, probabilities):
            label = ACTIONS.index(row["handling"])
            results.append(
                {
                    "key": row["key"],
                    "writer": writer,
                    "prompt": row["prompt"],
                    "probabilities": {"B-mixlogit": p.tolist(), "B-pop": population.tolist()},
                    "scores": {"B-mixlogit": proper(p, label), "B-pop": proper(population, label)},
                }
            )
        fits.append({"writer": writer, "cutoff": config["cutoff"], "penalty": penalty})
        progress(len(fits))
    return results, fits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    results, fits = reproduce(
        json.loads(args.training.read_text(encoding="utf8")),
        json.loads(args.targets.read_text(encoding="utf8")),
        lambda n: print(f"Reproduced {n} makers", flush=True),
    )
    summary = {
        "targets": len(results),
        "makers": len(fits),
        "seconds": time.monotonic() - start,
        "source_hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (args.training, args.targets)
        },
        "scores": {},
    }
    for arm in ("B-mixlogit", "B-pop"):
        by_maker = defaultdict(list)
        for r in results:
            by_maker[r["writer"]].append(r["scores"][arm]["half_brier"])
        summary["scores"][arm] = {
            "half_brier": float(np.mean([r["scores"][arm]["half_brier"] for r in results])),
            "equal_maker_half_brier": float(np.mean([np.mean(v) for v in by_maker.values()])),
        }
    if args.reference:
        reference = {r["key"]: r for r in json.loads(args.reference.read_text(encoding="utf8"))}
        if set(reference) != {r["key"] for r in results}:
            raise ValueError("Reference target identities differ")
        error = max(
            abs(r["scores"][a]["half_brier"] - reference[r["key"]]["scores"][a]["half_brier"])
            for r in results
            for a in ("B-mixlogit", "B-pop")
        )
        summary["max_reference_half_brier_error"] = error
        summary["reference_tolerance_pass"] = error <= 0.0005
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    print(json.dumps(summary, indent=2))
    if summary.get("reference_tolerance_pass") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
