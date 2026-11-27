"""Known-answer checks for sentence centres, duration matching and comparative word profiles."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_short_order import centres, matched, peaks
from rapid_word_contrasts import draws, linear_lifts, profiles


def test_fixed_sentence_examples_and_length_composition():
    position = np.array([0, 0.5, 1])
    y = np.array([[[0, 10, 4], [0, 1, 4], [7, 0, 4]]], dtype=float)
    out = centres(y, position)
    assert out[0, 0] == 1 and out[0, 1] < 0.1 and out[0, 2] == 0.5
    assert peaks(y, position)[0, 0]
    owner = np.arange(4)
    counts = np.array([[1, 1, 1, 1], [1, 0, 2, 1], [1, 1, 0, 2]], dtype=float)
    short = np.tile([1, 1, 1, 0, 0, 0, 0], (4, 1))
    long = np.tile([-2, -2, 0, 1, 1, 0, 0], (4, 1))
    strata = {
        2: (owner, np.array([1, 1, 1, 0], bool), short),
        3: (owner, np.array([0, 0, 0, 1], bool), long),
    }
    result, dropped = matched(strata, counts, lambda: None)
    assert not dropped
    assert result["sadnessMinusFear"]["difference"]["value"] == 0
    assert result["sadnessMinusFear"]["loss"]["value"] == 0.25
    assert result["fearEarlySadnessLate"]["matchedLossTexts"] == 1


def test_word_lift_recomputes_the_full_roster_standard_deviation():
    v = np.array([0.0, 1.0, 2.0, 1.0, 4.0, 3.0, 7.0, 6.0])
    label = np.repeat([0, 1], 4)
    values = np.column_stack([v, v, 2 * v, v])
    result = profiles(values, label, np.arange(8), ["a", "b"], draws(8), lambda: None)
    assert np.isclose(
        result["b"]["Respect"]["lift"]["value"], (v[4:].mean() - v[:4].mean()) / v.std()
    )
    assert result["a"]["RespectMinusacceptance"]["value"] == 0
    rng = np.random.default_rng(4)
    base = rng.normal(size=(8, 4))
    coef = np.eye(4)
    nulls = linear_lifts(base, label, ["a", "b"], coef, lambda: None, nsets=12)
    scores = base @ coef.mean(0)
    assert np.isclose(nulls["a"]["trained"], (scores[:4].mean() - scores[4:].mean()) / scores.std())
