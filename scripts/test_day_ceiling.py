"""Exercise both TP81 builds on an unbalanced, partly singleton constructed cohort."""

import json

import numpy as np
from day_ceiling_a import build
from day_ceiling_b import analyze
from day_cpu import differences


def test_unbalanced_known_trait_and_independent_rebuild():
    rng = np.random.default_rng(884)
    n = np.tile([1, 2, 3, 5], 24)
    g = np.repeat(np.arange(len(n)), n)
    rng.shuffle(g)
    x = rng.normal(size=(len(g), 4)) + rng.normal(size=(len(n), 4))[g]
    items = rng.uniform(1, 7, (len(n), 5, 2))
    items[:, 0, 1] = 8 - items[:, 0, 0]
    items[0, 1, :] = np.nan
    w = rng.normal(size=(3, 4))
    d = {
        "x": x,
        "w": w,
        "rot": rng.normal(size=(3, 3, 4)),
        "worry": x[:, 0],
        "person": g,
        "feeling": np.arange(len(g)) % 5,
        "pairs": items,
        "orders": np.argsort(g[None, :] + rng.random((3, len(g))), axis=1),
        "draws": rng.integers(0, len(n), (21, len(n))),
        "bounds": np.tile([-0.21, 0.09], (4, 5, 1)),
        "names": np.array(list("abcd")),
        "traits": np.array(list("ABCDE")),
    }
    a, b = build(d, lambda: None), analyze(d, lambda: None)
    assert not differences(a, b)
    assert (
        a["itemReliability"][0] == 1
        and a["oneReport"] == 24
        and a["traitWriters"][1] == 95
    )
    assert (
        abs(
            a["grids"]["items"]["bounds"][0][0]
            - min(1, 0.21 / a["grids"]["items"]["ceilings"][0][0])
        )
        < 1e-10
    )
    json.dumps(a, allow_nan=False)
    json.dumps(b, allow_nan=False)
