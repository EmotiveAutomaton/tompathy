"""Constructed controls for the Round 37 grouping and label comparisons."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_channel_words import auc, contrast, labels
from rapid_group_return import N, cell, floor_count, rotation


def test_tied_auc_and_formerly_degenerate_bootstrap():
    stats = auc([1, 0, 1, 0], [1, 0, 1, 1], ["a", "a", "b", "b"])
    assert stats["value"] == 0.75
    assert stats["validDraws"] == 2000
    assert auc([1, 1], [0, 1], ["a", "b"])["value"] is None
    assert labels("PLAY", "envent", ["joy", "sadness"]) == []


def test_multilabel_cooccurrence_and_own_word_exclusion():
    stats = contrast(
        np.array([0.0, 1.0, 1.0, 0.0, 0.5]),
        np.array([0, 1, 1, 0, 1], bool),
        np.array([1, 0, 0, 1, 1], bool),
        np.ones(5, bool),
        np.array([0, 1, 0, 0, 0], bool),
        np.array([1, 0, 0, 0, 0], bool),
        np.array(["a", "a", "b", "b", "c"]),
        lambda: None,
    )
    assert (stats["all"]["positive"], stats["all"]["negative"]) == (2, 2)
    assert stats["withoutWord"]["positive"] == stats["withoutWord"]["negative"] == 1


def test_leading_floor_stops_at_first_gap_and_descriptive_rotation():
    assert floor_count(np.array([3, 1, 2]), np.array([2, 1.5, 1])) == 1
    assert "tags" not in rotation(np.eye(N), 1)
    result = rotation(np.diag(np.r_[3.0, 2.0, np.ones(N - 2)]), 2)
    assert sum(v["component"] is not None for v in result["tags"].values()) == 2


def test_distinct_controls_and_paired_excess_use_the_same_draws():
    rng = np.random.default_rng(23)
    rot = rng.normal(size=(41, 6, N + 4))
    iso = rot + 1
    point = np.zeros((6, N + 4))
    point[:, N] = 8
    point[:, N + 1] = 12
    out = cell(point, iso, rot)
    assert out["groups"]["map"]["rot"]["aboveBand"]
    assert out["groups"]["map"]["rot"]["orientationP"] == 1 / 42
    assert out["groups"]["map"]["iso"]["median"] != out["groups"]["map"]["rot"]["median"]
    assert out["excessComparisons"]["threadMinusMap"]["positive"]
    assert sum(out["floors"]["rot"]["resampleCounts"]) == 5
