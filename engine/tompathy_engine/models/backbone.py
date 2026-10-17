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


def _newton_finish(objective, hessian, x, max_steps=20, target=1e-10):
    f, g = objective(x)
    steps = 0
    while steps < max_steps and np.isfinite(f) and np.isfinite(g).all() and np.max(np.abs(g)) > target:
        step = np.linalg.solve(hessian(x), -g)
        t, noise = 1.0, 1e-12 * max(1.0, abs(f))
        while t >= 2.0 ** -30:
            candidate = x + t * step
            fn, gn = objective(candidate)
            if np.isfinite(fn) and np.isfinite(gn).all() and (
                fn <= f + 1e-4 * t * (g @ step)
                or (fn <= f + noise and np.max(np.abs(gn)) < np.max(np.abs(g)))
            ):
                x, f, g = candidate, fn, gn
                steps += 1
                break
            t /= 2
        else:
            break
    return x, steps


def _fit(rows, center, penalty, initial=None, *, maxiter=500):
    center = np.asarray(center, dtype=float)
    if center.ndim != 1 or not center.size or not np.isfinite(center).all():
        raise ValueError("MAP center must be a finite vector")
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("MAP certification requires a positive finite penalty")
    if any(r.features.shape[1] != len(center) for r in rows):
        raise ValueError("MAP feature dimension mismatch")
    denominator = sum(r.weight for r in rows)
    if denominator <= 0:
        return np.zeros_like(center), {"optimizer_message": "no weighted rows", "iterations": 0,
                                      "newton_steps": 0, "certified_gap": 0.0,
                                      "gap_tolerance": 1e-9, "objective": 0.0,
                                      "gradient_max": 0.0, "accepted_by": "strong-convexity-certificate"}

    def objective(offset):
        loss, grad = penalty * (offset @ offset), 2 * penalty * offset
        for row in rows:
            logits = row.features @ (center + offset)
            loss += row.weight * (logsumexp(logits) - logits[row.taken])
            p = softmax(logits)
            grad += row.weight * (p @ row.features - row.features[row.taken])
        return float(loss), grad

    def hessian(offset):
        matrix = 2 * penalty * np.eye(len(center))
        for row in rows:
            p = softmax(row.features @ (center + offset))
            centered = row.features - p @ row.features
            matrix += row.weight * (centered.T * p) @ centered
        return matrix

    start = np.zeros_like(center) if initial is None else np.asarray(initial, dtype=float)
    if start.shape != center.shape or not np.isfinite(start).all():
        raise ValueError("MAP initial point must match its finite center")
    result = minimize(
        objective,
        start,
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": maxiter},
    )
    if not np.isfinite(result.x).all():
        raise ValueError(f"MAP fit failed: {result.message}")
    x, steps = _newton_finish(objective, hessian, result.x)
    f, g = objective(x)
    bound, tolerance = float(g @ g) / (4 * penalty), 1e-9 * max(1.0, abs(f))
    # A successful optimizer flag alone is not a convergence certificate.
    if not (np.isfinite(x).all() and np.isfinite(f) and np.isfinite(g).all()
            and np.isfinite(bound) and bound <= tolerance):
        raise ValueError(f"MAP fit failed: {result.message}; certified gap {bound:.3e}")
    return x, {"optimizer_message": str(result.message), "optimizer_success": bool(result.success),
               "iterations": int(result.nit), "newton_steps": steps, "certified_gap": bound,
               "gap_tolerance": tolerance, "objective": f, "gradient_max": float(np.max(np.abs(g))),
               "accepted_by": "strong-convexity-certificate"}


@dataclass
class Backbone:
    beta: np.ndarray
    until: datetime
    offsets: dict[str, np.ndarray] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    penalties: dict[str, float] = field(default_factory=dict)
    information_shares: dict[str, float] = field(default_factory=dict)
    conditional_intervals: dict[str, np.ndarray] = field(default_factory=dict)
    conditional_covariances: dict[str, np.ndarray] = field(default_factory=dict)
    train_ids: tuple[str, ...] = ()
    fit_receipts: dict[str, dict] = field(default_factory=dict)

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
        beta, receipt = _fit(rows, np.zeros(d), 0.005)
        model = cls(beta=beta, until=until, train_ids=tuple(r.id for r in rows),
                    fit_receipts={"population": receipt})
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
                    prior, receipt = _fit(historical, np.zeros(d), 0.005)
                    model.fit_receipts[f"{maker}:historical-population"] = receipt
                    candidates = []
                    for value in (0.01, 0.1, 1.0, 10.0):
                        offset, receipt = _fit(ownpast, prior, value)
                        model.fit_receipts[f"{maker}:trial:{value}"] = receipt
                        losses = [
                            logsumexp(r.features @ (prior + offset))
                            - r.features[r.taken] @ (prior + offset)
                            for r in calibration
                        ]
                        candidates.append((float(np.mean(losses)), value))
                    penalty = min(candidates)[1]
            model.offsets[maker], receipt = _fit(own, model.beta, penalty)
            model.fit_receipts[f"{maker}:offset"] = receipt
            model.counts[maker] = len(own)
            model.penalties[maker] = penalty
            information = np.zeros((d, d))
            for row in own:
                p = softmax(row.features @ (model.beta + model.offsets[maker]))
                mean = p @ row.features
                centered = row.features - mean
                information += row.weight * (centered.T * p) @ centered
            covariance = np.linalg.inv(information + 2 * penalty * np.eye(d))
            model.conditional_covariances[maker] = covariance
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
