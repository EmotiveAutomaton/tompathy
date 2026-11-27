import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_author_repeat import matched_halves, paired_direction

from tompathy_engine.eval.readers.person_halves import correlations
from tompathy_engine.eval.readers.week_curve import nested_indices


def test_join_checks_both_dated_rank_and_undated_openings():
    posts = [{"id": str(i), "opening": f"opening{i}", "day": str(i // 2)} for i in range(8)]
    expected = nested_indices([r["day"] for r in posts], [r["id"] for r in posts])
    sides = [[[posts[i]["opening"], None, None] for i in indices] for indices in expected] + [[]]
    ordered = matched_halves(list(reversed(posts)), sides)
    assert [[r["id"] for r in side] for side in ordered] == [
        [str(i) for i in indices] for indices in expected
    ]
    with pytest.raises(ValueError, match="differ"):
        matched_halves(posts, [sides[0][::-1], sides[1], []])
    assert matched_halves(posts[:1], [[], [], [[posts[0]["opening"], None, None]]]) == [[], []]
    with pytest.raises(ValueError, match="Duplicate"):
        matched_halves(posts + posts[:1], sides)


def test_pair_uses_each_draw_with_its_assigned_control_including_constants():
    rng = np.random.default_rng(10)
    left = rng.normal(size=(23, 8))
    right = rng.normal(size=(23, 8)) + left / 3
    left[:, 1] = 0
    boot = rng.multinomial(23, np.full(23, 1 / 23), size=8).astype(float)
    expected = correlations(left, right, boot).diagonal()
    assert np.allclose(paired_direction(left, right, boot), expected, equal_nan=True)
    with pytest.raises(ValueError, match="Misaligned"):
        paired_direction(left[:10], right, boot)


def test_prediction_requires_every_feature_at_both_sizes_and_retains_an_undefined_cell():
    from copy import deepcopy

    from rapid_repeat_return import describe
    from word_table_lane import core

    cell = {
        "B": {"value": -0.3, "interval": [-0.4, -0.2]},
        "rot": {"individual": {"position": "below", "low": 0.1, "high": 0.2}},
        "BMinusRandomRotatedHead": {
            "value": -0.45,
            "upperTail": 0.002,
            "interval": [-0.5, -0.35],
            "spread": 0.04,
            "validDraws": 2000,
        },
    }
    entry = {
        "authors": 100,
        "excluded": {"tooShort": 2, "missingBAnswer": 1},
        "features": {f: deepcopy(cell) for f in core.FEATURES},
    }
    result = {"k": {"10": deepcopy(entry), "20": deepcopy(entry)}, "draws": 2000}
    assert "All 16" in describe(result)[2]["verdict"]
    one = result["k"]["20"]["features"][core.FEATURES[-1]]
    one["BMinusRandomRotatedHead"].update(value=0.3, interval=[0.2, 0.4], upperTail=0.91)
    one["rot"]["individual"]["position"] = "above"
    mark = describe(result)[2]
    assert mark["against"] and mark["p"] == 0.91
    one["rot"] = None
    mark = describe(result)[2]
    assert mark["p"] is None and "Unresolved" in mark["verdict"]
