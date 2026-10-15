"""Held-out calibration utilities; fitting alone never confers admission."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import softmax


def probabilities(p, y=None):
    p = np.asarray(p, dtype=float)
    if (
        p.ndim != 2
        or not p.size
        or not np.isfinite(p).all()
        or (p < 0).any()
        or not np.allclose(p.sum(1), 1)
    ):
        raise ValueError("Expected normalized finite probability rows")
    if y is not None:
        y = np.asarray(y)
        if (
            y.shape != (len(p),)
            or not np.issubdtype(y.dtype, np.integer)
            or (y < 0).any()
            or (y >= p.shape[1]).any()
        ):
            raise ValueError("Invalid target labels")
    return p


def ece(p, y, bins=10):
    p = probabilities(p, y)
    confidence, correct = p.max(1), p.argmax(1) == np.asarray(y)
    groups = np.minimum((confidence * bins).astype(int), bins - 1)
    return sum(
        abs(confidence[groups == i].mean() - correct[groups == i].mean()) * (groups == i).mean()
        for i in range(bins)
        if np.any(groups == i)
    )


def disjoint_makers(training, heldout):
    if not heldout or set(training) & set(heldout):
        raise ValueError("Calibration requires nonempty held-out makers")


@dataclass(frozen=True)
class Temperature:
    temperature: float
    dataset: str

    @classmethod
    def fit(cls, p, y, *, training_makers, calibration_makers, dataset):
        disjoint_makers(training_makers, calibration_makers)
        p = probabilities(p, y)
        if len(calibration_makers) != len(p):
            raise ValueError("Calibration maker keys must align with rows")
        logits = np.log(np.clip(p, 1e-15, 1))

        def loss(log_t):
            q = softmax(logits / np.exp(log_t), axis=1)
            return -np.log(q[np.arange(len(y)), y]).mean()

        fit = minimize_scalar(loss, bounds=(-4, 4), method="bounded")
        if not fit.success:
            raise ValueError("Temperature fit failed")
        return cls(float(np.exp(fit.x)), dataset)

    def apply(self, p):
        return softmax(np.log(np.clip(probabilities(p), 1e-15, 1)) / self.temperature, axis=1)


def prior_shift(p, training_prior, *, iterations=200, tolerance=1e-9):
    p = probabilities(p)
    prior = np.asarray(training_prior, dtype=float)
    if (
        prior.shape != (p.shape[1],)
        or not np.isfinite(prior).all()
        or (prior <= 0).any()
        or not np.isclose(prior.sum(), 1)
    ):
        raise ValueError("Training prior needs positive support on every class")
    target = prior.copy()
    for _ in range(iterations):
        q = p * target / prior
        q /= q.sum(1, keepdims=True)
        next_target = q.mean(0)
        if np.max(np.abs(next_target - target)) < tolerance:
            return q, next_target
        target = next_target
    raise ValueError("Prior-shift EM did not converge")


def contextual(p, content_free):
    p = probabilities(p)
    bias = probabilities(content_free).mean(0)
    if bias.shape != (p.shape[1],) or (bias == 0).any():
        raise ValueError("Content-free calibration lacks class support")
    q = p / bias
    return q / q.sum(1, keepdims=True)


def stack(predictions, y, *, training_makers, calibration_makers):
    disjoint_makers(training_makers, calibration_makers)
    ps = np.stack([probabilities(p, y) for p in predictions])
    if len(calibration_makers) != ps.shape[1]:
        raise ValueError("Calibration maker keys must align")

    def loss(a):
        p = np.einsum("m,mnk->nk", softmax(a), ps)
        return -np.log(np.clip(p[np.arange(len(y)), y], 1e-15, 1)).mean()

    result = minimize(loss, np.zeros(len(ps)), method="L-BFGS-B")
    if not result.success:
        raise ValueError("Stacking fit failed")
    return softmax(result.x)


def gate(p, baseline, y):
    p, baseline = probabilities(p, y), probabilities(baseline, y)
    if baseline.shape != p.shape:
        raise ValueError("Calibration comparison shapes differ")
    truth = np.eye(p.shape[1])[y]
    score = float(np.mean(np.sum((p - truth) ** 2, axis=1) / 2))
    base = float(np.mean(np.sum((baseline - truth) ** 2, axis=1) / 2))
    error = float(ece(p, y))
    return {
        "passed": error < 0.05 and score <= base,
        "ece": error,
        "half_brier": score,
        "baseline_half_brier": base,
    }
