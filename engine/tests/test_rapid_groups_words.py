"""Constructed controls for the Round 37 grouping and label comparisons."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_agreement import classification, kappas, original_gates
from rapid_blog_selection import choose_losses, choose_openings
from rapid_card_record import agreement_text, group_text, live_line
from rapid_channel_words import auc, contrast, labels
from rapid_group_return import N, cell, floor_count, rotation
from rapid_marks import template
from rapid_sentence_contrasts import NAMES, fit
from rapid_sentence_data import classes


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


def test_within_report_contrast_removes_position_and_report_level():
    parent = np.repeat(np.arange(4), 3)
    position = np.tile([0.0, 0.5, 1.0], 4)
    cls = np.array([1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0])
    raw = 2.5 * cls + 30 * position + 100 * parent
    y = np.tile(raw[:, None], (1, len(NAMES)))
    w = np.ones((101, 4), int)
    out = fit(cls, (1,), (0,), y, parent, np.arange(4), position, w, lambda: None)
    assert np.isclose(out["outputs"]["worry"]["value"], 2.5)
    assert out["reportsWithBothClasses"] == 4
    assert classes(None) == (-1, -1)
    assert classes({"change": True, "when": "ongoing", "whose": "writer"}) == (3, 1)


def test_fixed_reader_reliability_bins_and_joint_validity():
    matrices = np.array([[[10, 0], [0, 10]], [[5, 5], [5, 5]], [[5, 0], [0, 0]]])
    k = kappas(matrices)
    np.testing.assert_allclose(k, [1, 0, np.nan], equal_nan=True)
    assert [classification(x) for x in (None, 0.399, 0.4, 0.599, 0.6)] == [
        "not used",
        "not used",
        "weak",
        "weak",
        "usable",
    ]
    marks = np.full((4, 3, 2), -1)
    marks[:, 0] = [[0, 0], [1, 1], [2, 2], [1, 1]]
    marks[:3, 1] = marks[:3, 0]
    assert original_gates(marks)["when"] == {"kappa": 1.0, "status": "usable", "valid": 3}


def test_blog_threshold_distinguishes_saved_windows_from_the_seeded_sentence_sample():
    scores = {f"p{i}": i / 41 for i in range(41)}
    chosen, n = choose_losses(scores)
    assert set(chosen) == {"p38", "p39", "p40"} and n["eligible"] == 41
    posts = {a: [a + str(i) for i in range(80)] for a in ("a", "b", "c")}
    sample, n = choose_openings({"a": 80, "b": 90, "c": 60}, posts)
    assert len(sample) == 40 and n == 2 and len(set(sample)) == 40
    _, _, validate = template("loss")
    assert validate({"loss": False, "kind": "death"}) is None
    assert validate({"loss": True, "kind": "other_or_unspecified"})["loss"]


def test_group_report_keeps_chat_and_blog_order_when_receipt_keys_are_sorted():
    rng = np.random.default_rng(21)
    controls = rng.normal(size=(8, 5, N + 4))
    blog = cell(np.zeros((5, N + 4)), controls, controls)
    chat = cell(np.ones((5, N + 4)), controls, controls)
    _, _, family = group_text({"sources": {"blog": {"full": blog}, "chat": {"full": chat}}})
    first = chat["groups"]["map"]["rot"]["marginAboveBand"]["value"]
    second = blog["groups"]["map"]["rot"]["marginAboveBand"]["value"]
    assert family["TP70.1"]["estimate"].index(f"{first:.3f}") < family["TP70.1"]["estimate"].index(
        f"{second:.3f}"
    )
    assert family["TP70.2"]["p"] is None


def test_report_distinguishes_partial_reliability_and_an_idle_card_lane():
    field = {"value": 0.5, "interval": [0.45, 0.55], "CW": "weak", "jointlyValid": 100}
    _, _, m = agreement_text(
        {"sources": {"all": {"B/W": dict.fromkeys(("when", "whose", "change"), field)}}}
    )
    assert m["TP77.analyst"]["p"] is None and "awaits" in m["TP77.analyst"]["verdict"]
    state = {
        "checkedAt": "2026-11-27T18:00:00+00:00",
        "spark": {"state": "running", "job": "Q27", "rows": 7, "total": 20},
        "workstation": {
            "gpu": {"state": "running", "job": "G12"},
            "card": None,
            "cardIdleReason": "paused after a verified stop",
        },
    }
    assert "Q27 (7/20)" in live_line(state) and "paused after a verified stop" in live_line(state)
