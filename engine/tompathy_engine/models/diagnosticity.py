"""Latency-weight proposals with maker-held-out and shuffled controls."""

from dataclasses import replace

import numpy as np
from scipy.special import expit

from .backbone import Backbone


def diagnosticity(mark_probability_a, mark_probability_b):
    if not 0 < mark_probability_a <= 1 or not 0 < mark_probability_b <= 1:
        raise ValueError("Finite log diagnosticity needs positive mark probabilities")
    return abs(float(np.log(mark_probability_a) - np.log(mark_probability_b)))


def weights(z, a, b, *, utility_features=()):
    if any("latency" in name or "decide_seconds" in name for name in utility_features):
        raise ValueError("Latency cannot enter both utilities and diagnosticity weights")
    z = np.asarray(z, dtype=float)
    if not np.isfinite(z).all() or not np.isfinite([a, b]).all():
        raise ValueError("Nonfinite diagnosticity parameters")
    return expit(a + b * z)


def fit(cases, standardized_latency, *, until, utility_features=(), seed=0, useful_margin=0.001):
    rows = sorted((r for r in cases if r.resolved < until), key=lambda r: (r.opened, r.id))
    makers = sorted({r.maker for r in rows})
    if len(makers) < 3:
        raise ValueError("Diagnosticity cross-fitting needs at least three makers")
    z = np.array([standardized_latency[r.id] for r in rows])
    shuffled = z.copy()
    rng = np.random.default_rng(seed)
    for maker in makers:
        ix = np.array([i for i, r in enumerate(rows) if r.maker == maker])
        shuffled[ix] = rng.permutation(z[ix])

    def score(a, b, latencies):
        ws = weights(latencies, a, b, utility_features=utility_features)
        losses = []
        for maker in makers:
            held = [r for r in rows if r.maker == maker]
            # Both maker separation and chronology: no future labels from peers.
            for target in held:
                train = [
                    replace(r, weight=float(ws[i]))
                    for i, r in enumerate(rows)
                    if r.maker != maker and r.resolved < target.opened
                ]
                model = Backbone.fit(
                    train, until=target.opened, dimensions=target.features.shape[1]
                )
                losses.append(
                    -np.log(max(1e-300, model.predict(maker, target.features)[target.taken]))
                )
        return float(np.mean(losses))

    # Fixed preregisterable grid; do not tune this grid after examining test data.
    candidates = [(score(a, b, z), a, b) for a in (-1.0, 0.0, 1.0) for b in (-1.0, 0.0, 1.0)]
    loss, a, b = min(candidates)
    shuffled_loss = score(a, b, shuffled)
    return {
        "a": a,
        "b": b,
        "crossfit_log_loss": loss,
        "shuffled_log_loss": shuffled_loss,
        "useful_margin": useful_margin,
        "control_passed": shuffled_loss - loss >= useful_margin,
        "status": "requires independent admission",
        "seed": seed,
    }
