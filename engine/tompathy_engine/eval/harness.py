"""Per-decision proper scores; inference statistics remain in Sounding Line."""

import time
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import softmax

from ..models.reference import ACTIONS, features, intercept_fit


def handling_prequential(records, *, until=None, cancel=lambda: False, progress=lambda _: None):
    """Exact warm-start population MAP and personal intercept fits per target.

    Personal penalties are selected against each maker's earlier calibration
    slice, using a separate fit whose cutoff precedes that slice. No current
    latency, outcome, or future handling label is a feature.
    """
    rows = sorted(records, key=lambda r: (r["open_at"], r["key"]))
    if len({r["key"] for r in rows}) != len(rows):
        raise ValueError("Duplicate handling records")
    if not rows:
        return [], {"decisions": 0, "seconds": 0}
    for r in rows:
        opened, resolved = (
            datetime.fromisoformat(r["open_at"]),
            datetime.fromisoformat(r["resolved_at"]),
        )
        if opened.tzinfo is None or resolved.tzinfo is None or opened > resolved:
            raise ValueError("Handling input lacks valid chronology")
    opens = np.array([datetime.fromisoformat(r["open_at"]).timestamp() for r in rows])
    resolves = np.array([datetime.fromisoformat(r["resolved_at"]).timestamp() for r in rows])
    # Previous handling is used only when that episode has already resolved.
    xrows, by_maker = [], {}
    for i, row in enumerate(rows):
        history = [
            j
            for j in by_maker.get(row["writer"], [])
            if resolves[j] < opens[i] and rows[j].get("session") == row.get("session")
        ]
        safe = {**row, "previous_handling": rows[history[-1]]["handling"] if history else None}
        xrows.append(features(safe, [], False))
        by_maker.setdefault(row["writer"], []).append(i)
    x = np.array(xrows)
    y = np.array([ACTIONS.index(r["handling"]) for r in rows])
    weights = np.zeros((x.shape[1], 4))
    output = []
    start = time.monotonic()
    previous_ix = None

    def population_fit(ix, initial):
        if not len(ix):
            return np.zeros_like(initial)
        xx, yy = x[ix], y[ix]

        def objective(v):
            w = v.reshape(initial.shape)
            p = softmax(xx @ w, axis=1)
            loss = -np.log(np.maximum(p[np.arange(len(yy)), yy], 1e-300)).mean() + 0.005 * np.sum(
                w[1:] ** 2
            )
            p[np.arange(len(yy)), yy] -= 1
            grad = xx.T @ (p / len(yy))
            grad[1:] += 0.01 * w[1:]
            return float(loss), grad.ravel()

        result = minimize(
            objective, initial.ravel(), jac=True, method="L-BFGS-B", options={"maxiter": 500}
        )
        if not result.success:
            raise ValueError("Prequential population MAP failed")
        return result.x.reshape(initial.shape)

    penalty_cache = {}
    for i, target in enumerate(rows):
        if cancel():
            raise InterruptedError("Prequential evaluation cancelled")
        if until is not None and datetime.fromisoformat(target["open_at"]) >= until:
            continue
        ix = np.flatnonzero(resolves < opens[i])
        if previous_ix is None or not np.array_equal(previous_ix, ix):
            weights = population_fit(ix, weights)
            previous_ix = ix
        own = np.array([j for j in by_maker[target["writer"]] if resolves[j] < opens[i]], dtype=int)
        penalty = 1.0
        # Calibrate at geometric history milestones and retain that earlier
        # selected penalty until the next milestone. Every observation still
        # enters both final MAP fits as soon as it is resolved.
        milestone = 2 ** int(np.log2(len(own))) if len(own) >= 8 else 0
        if milestone:
            key = (target["writer"], milestone)
            if key not in penalty_cache:
                calibration = own[:milestone][max(4, int(0.8 * milestone)) :]
                split = opens[calibration[0]]
                past = np.flatnonzero(resolves < split)
                personal = np.array([j for j in own if resolves[j] < split], dtype=int)
                if len(personal):
                    prior = population_fit(past, np.zeros_like(weights))
                    scores = []
                    for value in (0.01, 0.1, 1.0, 10.0):
                        u = intercept_fit(
                            x[personal] @ prior, y[personal], np.ones(len(personal)), value
                        )
                        p = softmax(x[calibration] @ prior + u, axis=1)
                        scores.append(
                            (
                                float(
                                    np.mean(
                                        0.5 * np.sum((p - np.eye(4)[y[calibration]]) ** 2, axis=1)
                                    )
                                ),
                                value,
                            )
                        )
                    penalty_cache[key] = min(scores)[1]
                else:
                    penalty_cache[key] = 1.0
            penalty = penalty_cache[key]
        offset = (
            intercept_fit(x[own] @ weights, y[own], np.ones(len(own)), penalty)
            if len(own)
            else np.zeros(4)
        )
        p = softmax(x[i] @ weights + offset)
        base = np.bincount(y[ix], minlength=4) + 1.0
        base /= base.sum()
        for module, values in (("backbone", p), ("population", base)):
            output.append(
                {
                    "decision": target["key"],
                    "maker": target["writer"],
                    "prompt": target["prompt"],
                    "opened": target["open_at"],
                    "resolved": target["resolved_at"],
                    "module": module,
                    "probabilities": values.tolist(),
                    "taken": int(y[i]),
                    "training_records": len(ix),
                    "half_brier": float(0.5 * np.sum((values - np.eye(4)[y[i]]) ** 2)),
                    "log_loss": float(-np.log(values[y[i]])),
                    "penalty": penalty,
                }
            )
        if (i + 1) % 250 == 0:
            progress({"decisions": i + 1, "seconds": time.monotonic() - start})
    return output, {
        "decisions": len(output) // 2,
        "seconds": time.monotonic() - start,
        "mode": "prequential exact MAP; earlier geometric calibration milestones",
        "admission": "not established",
    }


def write_scores(rows, path):
    pd.DataFrame(rows).to_parquet(path, index=False)
