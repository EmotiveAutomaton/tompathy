"""Pooled multinomial choice over the alternatives actually available.

MAP estimates have no automatic probability-calibration or value interpretation.
The utility scale is fixed (lambda=1): unrestricted personal coefficients and a
free lambda are not separately identified. Held-out calibration owns rescaling.
"""

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax


@dataclass(frozen=True)
class Choice:
    id: str
    maker: str
    opened: datetime
    resolved: datetime
    features: np.ndarray
    taken: int
    prompt: str = ""
    weight: float = 1.0

    def __post_init__(self):
        x = np.asarray(self.features, dtype=float)
        object.__setattr__(self, "features", x)
        if x.ndim != 2 or min(x.shape) < 1 or not np.isfinite(x).all():
            raise ValueError("Options need a finite feature matrix")
        if not 0 <= self.taken < len(x):
            raise ValueError("Taken index outside offered alternatives")
        if (
            self.opened.tzinfo is None
            or self.resolved.tzinfo is None
            or self.opened > self.resolved
        ):
            raise ValueError("Invalid aware choice chronology")
        if not np.isfinite(self.weight) or not 0 <= self.weight <= 1:
            raise ValueError("Diagnosticity weight outside [0,1]")


def _fit(rows, center, penalty, initial=None):
    denominator = sum(r.weight for r in rows)
    if denominator <= 0:
        return np.zeros_like(center)

    def objective(offset):
        loss, grad = penalty * (offset @ offset), 2 * penalty * offset
        for row in rows:
            logits = row.features @ (center + offset)
            loss += row.weight * (logsumexp(logits) - logits[row.taken])
            p = softmax(logits)
            grad += row.weight * (p @ row.features - row.features[row.taken])
        return float(loss), grad

    result = minimize(
        objective,
        np.zeros_like(center) if initial is None else initial,
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 500},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise ValueError(f"MAP fit failed: {result.message}")
    return result.x


@dataclass
class Backbone:
    beta: np.ndarray
    until: datetime
    offsets: dict[str, np.ndarray] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    penalties: dict[str, float] = field(default_factory=dict)
    information_shares: dict[str, float] = field(default_factory=dict)
    conditional_intervals: dict[str, np.ndarray] = field(default_factory=dict)
    train_ids: tuple[str, ...] = ()

    @classmethod
    def fit(cls, cases, *, until: datetime, dimensions: int | None = None):
        if until.tzinfo is None:
            raise ValueError("Fit cutoff needs a timezone")
        # Strict cutoff excludes simultaneous resolutions with unknown ordering.
        rows = sorted((r for r in cases if r.resolved < until), key=lambda r: (r.opened, r.id))
        if len({r.id for r in rows}) != len(rows):
            raise ValueError("Duplicate choices would double-count evidence")
        d = rows[0].features.shape[1] if rows else dimensions
        if not d or any(r.features.shape[1] != d for r in rows):
            raise ValueError("Feature dimension mismatch or absent empty-model dimension")
        model = cls(
            beta=_fit(rows, np.zeros(d), 0.005), until=until, train_ids=tuple(r.id for r in rows)
        )
        for maker in sorted({r.maker for r in rows}):
            own = [r for r in rows if r.maker == maker]
            penalty = 1.0
            split_index = max(4, int(0.8 * len(own)))
            calibration = own[split_index:]
            if calibration:
                cutoff = min(r.opened for r in calibration)
                historical = [r for r in rows if r.resolved < cutoff]
                ownpast = [r for r in historical if r.maker == maker]
                if ownpast:
                    prior = _fit(historical, np.zeros(d), 0.005)
                    candidates = []
                    for value in (0.01, 0.1, 1.0, 10.0):
                        offset = _fit(ownpast, prior, value)
                        losses = [
                            logsumexp(r.features @ (prior + offset))
                            - r.features[r.taken] @ (prior + offset)
                            for r in calibration
                        ]
                        candidates.append((float(np.mean(losses)), value))
                    penalty = min(candidates)[1]
            model.offsets[maker] = _fit(own, model.beta, penalty)
            model.counts[maker] = len(own)
            model.penalties[maker] = penalty
            information = np.zeros((d, d))
            for row in own:
                p = softmax(row.features @ (model.beta + model.offsets[maker]))
                mean = p @ row.features
                centered = row.features - mean
                information += row.weight * (centered.T * p) @ centered
            covariance = np.linalg.inv(information + 2 * penalty * np.eye(d))
            model.information_shares[maker] = float(np.trace(information @ covariance) / d)
            radius = 1.96 * np.sqrt(np.diag(covariance))
            model.conditional_intervals[maker] = np.column_stack(
                (model.offsets[maker] - radius, model.offsets[maker] + radius)
            )
        return model

    def predict(self, maker, features, *, at=None):
        if at is not None and at < self.until:
            raise ValueError("Prediction precedes training cutoff")
        x = np.asarray(features, dtype=float)
        if x.ndim != 2 or x.shape[1] != len(self.beta) or not len(x) or not np.isfinite(x).all():
            raise ValueError("Prediction requires finite offered feature rows")
        return softmax(x @ (self.beta + self.offsets.get(maker, np.zeros_like(self.beta))))

    def shrinkage(self, maker):
        # Mean local information share in parameter space; conditional on beta.
        # This is a curvature approximation, not a fraction of authorship or a
        # calibrated interval for a person's values.
        return self.information_shares.get(maker, 0.0)
