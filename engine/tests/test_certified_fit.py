from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.special import softmax

from tompathy_engine.models import backbone


def fixture():
    with np.load(Path(__file__).parent / "fixtures/ghost-t1-failed-fit.npz") as raw:
        at = datetime(2026, 1, 1, tzinfo=UTC)
        rows = [backbone.Choice(str(i), "constructed", at, at, raw[f"features_{i}"], int(taken), weight=float(raw["weights"][i]))
                for i, taken in enumerate(raw["taken"])]
        return rows, raw["center"], float(raw["penalty"])


def test_ghost_failure_rescued_permutation_and_direct_newton():
    rows, center, penalty = fixture()
    fit, receipt = backbone._fit(rows, center, penalty)
    rescued, short = backbone._fit(rows, center, penalty, maxiter=1)
    assert receipt["certified_gap"] <= receipt["gap_tolerance"]
    assert short["newton_steps"] > 0 and short["certified_gap"] <= short["gap_tolerance"]
    np.testing.assert_allclose(fit, rescued, atol=1e-10, rtol=0)
    # Independent Newton implementation, no L-BFGS or production finishing code.
    x = np.zeros_like(center)
    for _ in range(20):
        gradient = 2 * penalty * x
        hessian = 2 * penalty * np.eye(len(x))
        for row in rows:
            p = softmax(row.features @ (center + x))
            gradient += row.weight * (p @ row.features - row.features[row.taken])
            hessian += row.weight * row.features.T @ (np.diag(p) - np.outer(p, p)) @ row.features
        x -= np.linalg.solve(hessian, gradient)
        if np.max(np.abs(gradient)) < 1e-10:
            break
    np.testing.assert_allclose(fit, x, atol=1e-8, rtol=0)
    random = np.random.default_rng(17)
    for _ in range(20):
        shuffled = []
        for row in rows:
            order = random.permutation(len(row.features))
            shuffled.append(backbone.Choice(row.id, row.maker, row.opened, row.resolved, row.features[order], int(np.where(order == row.taken)[0][0]), weight=row.weight))
        alternate, cert = backbone._fit(shuffled, center, penalty)
        assert cert["certified_gap"] <= cert["gap_tolerance"]
        for row in rows:
            np.testing.assert_allclose(softmax(row.features @ (center + fit)), softmax(row.features @ (center + alternate)), atol=1e-9, rtol=0)


def test_nonfinite_success_and_bad_penalty_refused(monkeypatch):
    rows, center, penalty = fixture()
    monkeypatch.setattr(backbone, "minimize", lambda *a, **k: SimpleNamespace(x=np.array([np.nan, 0]), success=True, message="success", nit=1))
    with pytest.raises(ValueError, match="MAP fit failed"):
        backbone._fit(rows, center, penalty)
    for value in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="penalty"):
            backbone._fit([], center, value)


def test_zero_weight_certificate():
    x, receipt = backbone._fit([], np.zeros(3), .005)
    assert not x.any() and receipt["certified_gap"] == 0
