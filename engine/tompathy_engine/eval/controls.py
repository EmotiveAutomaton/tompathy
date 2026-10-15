"""Declared perturbations preserve within-maker control units."""

from dataclasses import replace

import numpy as np


def shuffle_weights(cases, *, seed):
    rows = sorted(cases, key=lambda r: r.id)
    rng = np.random.default_rng(seed)
    result = []
    for maker in sorted({r.maker for r in rows}):
        own = [r for r in rows if r.maker == maker]
        values = rng.permutation([r.weight for r in own])
        result.extend(replace(r, weight=float(w)) for r, w in zip(own, values, strict=True))
    return result
