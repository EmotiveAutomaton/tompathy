"""Optional fixed-prototype few-shot offset; no automatic prototype discovery."""

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax


def fit_mix(cases, *, maker, prototypes, population, until, residual_penalty=10.0):
    prototypes, population = (
        np.asarray(prototypes, dtype=float),
        np.asarray(population, dtype=float),
    )
    if (
        prototypes.ndim != 2
        or population.shape != (prototypes.shape[1],)
        or not np.isfinite(prototypes).all()
        or not np.isfinite(population).all()
        or residual_penalty <= 0
    ):
        raise ValueError("Invalid prototype vectors or prior")
    rows = [r for r in cases if r.maker == maker and r.resolved < until]
    k, d = prototypes.shape
    if not rows:
        return {"weights": np.full(k, 1 / k), "offset": np.zeros(d), "records": 0}

    def objective(v):
        offset = softmax(v[:k]) @ prototypes + v[k:]
        return (
            sum(
                logsumexp(r.features @ (population + offset))
                - r.features[r.taken] @ (population + offset)
                for r in rows
            )
            + residual_penalty * (v[k:] @ v[k:])
            + 0.01 * (v[:k] @ v[:k])
        )

    result = minimize(objective, np.zeros(k + d), method="L-BFGS-B")
    if not result.success:
        raise ValueError("Prototype fit failed")
    return {
        "weights": softmax(result.x[:k]),
        "offset": softmax(result.x[:k]) @ prototypes + result.x[k:],
        "records": len(rows),
    }
