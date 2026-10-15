"""Portable, held-out forecast calibration. Never calibrates value/drive claims."""

from datetime import datetime

import numpy as np

from ..admission import implementation_hash
from ..ledger.ids import digest
from .calibration import Temperature, contextual, disjoint_makers, gate, prior_shift, stack


def calibrate(payload, *, method="temperature"):
    """Three maker-disjoint sets: model training, calibration fitting, final test.

    Forecast rows are witnessed exports with id, maker, time, p, y and baseline.
    Stacking additionally takes component predictions; contextual calibration
    takes content-free forecasts. No labels in the final test fit parameters.
    """
    train = payload["training_makers"]
    calibration, test = payload["calibration"], payload["test"]

    def time(value):
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError("Calibration timestamps require timezones")
        return result

    for row in [*calibration, *test]:
        if not time(row["training_latest"]) < time(row["opened"]) <= time(row["resolved"]):
            raise ValueError("Calibration forecasts must precede their outcomes")
    if (
        not calibration
        or not test
        or max(time(r["resolved"]) for r in calibration) >= min(time(r["opened"]) for r in test)
    ):
        raise ValueError("Calibration fitting must finish before the final test starts")
    cm, tm = [r["maker"] for r in calibration], [r["maker"] for r in test]
    disjoint_makers(train, cm)
    disjoint_makers([*train, *cm], tm)
    ids = [r["id"] for r in [*calibration, *test]]
    if len(set(ids)) != len(ids) or not payload.get("dataset") or not payload.get("source_hash"):
        raise ValueError("Calibration needs unique examples and pinned source provenance")
    p = np.array([r["p"] for r in calibration])
    y = np.array([r["y"] for r in calibration])
    target = np.array([r["p"] for r in test])
    if method == "temperature":
        fitted = Temperature.fit(
            p, y, training_makers=train, calibration_makers=cm, dataset=payload["dataset"]
        )
        params = {"temperature": fitted.temperature}
        q = fitted.apply(target)
    elif method == "prior-shift":
        prior = np.asarray(payload["training_prior"], dtype=float)
        _, shifted = prior_shift(p, prior)
        params = {"training_prior": prior.tolist(), "target_prior": shifted.tolist()}
        q = target * shifted / prior
        q /= q.sum(1, keepdims=True)
    elif method == "contextual":
        bias = np.asarray(payload["content_free"], dtype=float)
        q = contextual(target, bias)
        params = {"content_free": bias.tolist()}
    elif method == "stacking":
        weights = stack(
            payload["calibration_components"], y, training_makers=train, calibration_makers=cm
        )
        components = np.asarray(payload["test_components"], dtype=float)
        if components.shape != (len(weights), len(test), target.shape[1]):
            raise ValueError("Test component predictions do not align")
        q = np.einsum("m,mnk->nk", weights, components)
        params = {"weights": weights.tolist()}
    else:
        raise ValueError("Unsupported calibration method")
    result = gate(q, [r["baseline"] for r in test], np.array([r["y"] for r in test]))
    return {
        "format": "tompathy-calibration-1",
        "method": method,
        "parameters": params,
        "dataset": payload["dataset"],
        "input_hash": digest(payload),
        "implementation_hash": implementation_hash(),
        "estimand": "offered-option forecast",
        "calibration_makers": sorted(set(cm)),
        "test_makers": sorted(set(tm)),
        "test_ids": [r["id"] for r in test],
        "predictions": q.tolist(),
        "gate": result,
        "admission": "requires independent scientific admission",
    }
