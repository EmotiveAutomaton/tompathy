"""TP12 correction with a frozen policy; raw counts never become page shares."""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import nnls


@dataclass(frozen=True)
class AggregationPolicy:
    prior: float
    minimum: int
    bootstrap: int = 1000
    seed: int = 20261114

    def __post_init__(self):
        if self.prior < 1 or not np.isfinite(self.prior) or self.minimum < 1:
            raise ValueError('Invalid fixed aggregation policy')
        if self.bootstrap < 100:
            raise ValueError('At least 100 sentence resamples required')


def error_table(counts, smoothing=0.5):
    c = np.asarray(counts, dtype=float)
    if c.ndim != 2 or c.shape[0] != c.shape[1] or not np.isfinite(c).all():
        raise ValueError('Error counts must be a finite square matrix')
    if (c < 0).any() or (c.sum(axis=1) == 0).any() or smoothing < 0:
        raise ValueError('Each key label needs held-out support')
    c = c + smoothing
    return c / c.sum(axis=1, keepdims=True)


def correct(counts, table, prior=0.0):
    """NNLS in count units; symmetric prior adds pseudo-counts after inversion."""
    c, m = np.asarray(counts, float), np.asarray(table, float)
    if (c.ndim != 1 or m.shape != (len(c), len(c)) or not np.isfinite(m).all()
            or not np.isfinite(c).all() or (c < 0).any() or (m < 0).any()
            or not np.allclose(m.sum(axis=1), 1) or c.sum() <= 0
            or not np.isfinite(prior) or prior < 0):
        raise ValueError('Invalid correction inputs')
    x, _ = nnls(m.T, c)
    x += prior
    if x.sum() <= 0:
        raise ValueError('No identifiable corrected mass')
    return x / x.sum()


def shares(predictions, table, policy, *, neutral=None, groups=None):
    """Correct including no-emotion, then condition on feeling-carrying sentences.

    The interval reflects sentence resampling conditional on a fixed error table;
    it does not estimate uncertainty in the error table itself.
    """
    m = np.asarray(table, float)
    p = np.asarray(predictions, dtype=int)
    k = len(m)
    if p.ndim != 1 or (p < 0).any() or (p >= k).any():
        raise ValueError('Prediction outside label table')
    if len(p) < policy.minimum:
        return None
    if neutral is not None and not 0 <= neutral < k:
        raise ValueError('Unknown neutral label')
    if groups is not None and any(not g or any(i < 0 or i >= k for i in g) for g in groups):
        raise ValueError('Invalid aggregate label group')

    def estimate(rows):
        x = correct(np.bincount(rows, minlength=k), m, policy.prior - 1)
        if neutral is not None:
            x[neutral] = 0
            if x.sum() < 1e-10:
                return None
            x /= x.sum()
        return np.asarray([x[g].sum() for g in groups]) if groups is not None else x

    value = estimate(p)
    if value is None or (neutral is not None and np.all(p == neutral)):
        return None
    rng = np.random.default_rng(policy.seed)
    samples = [estimate(rng.choice(p, len(p))) for _ in range(policy.bootstrap)]
    # An all-neutral resample makes the conditional estimand undefined; withhold.
    if any(s is None for s in samples):
        return None
    bounds = np.quantile(samples, [.025, .975], axis=0)
    return [{'value': float(v), 'interval': [float(min(bounds[0, i], v)),
             float(max(bounds[1, i], v))], 'of': 'sentences read as carrying a feeling',
             'method': 'corrected'} for i, v in enumerate(value)]
