import math

import numpy as np


def proper(probabilities, taken):
    p = np.asarray(probabilities, dtype=float)
    if p.ndim != 1 or not len(p) or not 0 <= taken < len(p) or not np.isfinite(p).all():
        raise ValueError("Malformed forecast")
    if np.any(p < 0) or not np.isclose(p.sum(), 1, atol=1e-10):
        raise ValueError("Forecast is not a probability distribution")
    y = np.eye(len(p))[taken]
    return {
        "half_brier": float(0.5 * np.sum((p - y) ** 2)),
        "log_loss": -math.log(p[taken]) if p[taken] > 0 else math.inf,
    }
