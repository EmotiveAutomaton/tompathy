"""Known-answer controls for item keying, writer inclusion, tied ranks and orientation bands."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_blend import auc_draws, train
from rapid_outside import (
    KEYS,
    controls,
    correlations,
    fit_table,
    tables,
    writer_traits,
    writer_values,
)


def test_scoring_keys_and_unambiguous_writer_membership():
    people = np.array(["a", "b", "c", "d"])
    frame = pd.DataFrame({"prolific_id": ["a", "a", "b", "c", "d"]})
    for pos, neg in KEYS.values():
        frame[pos] = [5, 5, 7, 3, 1]
        frame[neg] = [2, 2, 1, 5, 7]
    frame.loc[1, "critical"] = 4
    frame.loc[2, "conventional"] = np.nan
    scores, census = writer_traits(frame, people)
    assert scores[0, 0] == 5.5 and scores[3, 3] == 1 and scores[1, 2] == 7
    assert np.isnan(scores[0, 1]) and np.isnan(scores[1, -1])
    assert census["Agreeableness"] == {"available": 3, "missingItem": 0, "conflictingItem": 1}
    assert census["Openness"]["missingItem"] == 1


def test_label_offsets_cancel_and_weighted_sampling_keeps_ties():
    x = np.array([[1.0, 0], [101.0, 6], [2.0, 0], [102.0, 6], [3.0, 1], [103.0, 9]])
    owner = np.repeat(np.arange(3), 2)
    feeling = np.tile([0, 1], 3)
    w = writer_values(x, feeling, owner)
    shifted = x + np.array([[2, 9], [5000, -1300]])[feeling]
    np.testing.assert_allclose(w, writer_values(shifted, feeling, owner))
    y = np.array([[1.0, 2], [1.0, 2], [4.0, 0]])
    value, draws = fit_table(w, y, lambda: None, nboot=15)
    np.testing.assert_allclose(value, correlations(w, y))
    assert np.isclose(value[1, 0], 1) and np.isclose(value[1, 1], -1)
    assert draws.shape == (15, 2, 2)


def test_same_null_families_and_explicit_per_trait_and_family_bars():
    g = np.random.default_rng(24)
    vectors = g.normal(size=(48, 8))
    w = np.eye(8)[:3]
    y = g.normal(size=(48, 5))
    y[:3, 1] = np.nan
    sets = controls(vectors, w, y, lambda: None, nsets=7)
    v, draws = fit_table(vectors @ w.T, y, lambda: None, nboot=35)
    census = {t: {"available": int(np.isfinite(y[:, j]).sum())} for j, t in enumerate(KEYS)}
    bars, cells = tables(v, draws, sets, ["a", "b", "c"], census)
    for name, f in sets.items():
        assert f.shape == (7, 3, 5)
        assert np.isclose(bars[name]["family"], np.quantile(f.max(axis=(1, 2)), 0.95))
        assert np.isclose(bars[name]["trait"]["Openness"], np.quantile(f[:, :, 4], 0.975))
    assert cells["c"]["Agreeableness"]["writers"] == 45


def test_paired_auc_recomputes_tied_scores_under_whole_writer_multiplicities():
    from sklearn.metrics import roc_auc_score

    y = np.array([1, 0, 1, 0, 1, 0, 0, 1], bool)
    owner = np.repeat(np.arange(4), 2)
    x = np.array([1.0, 1.0, 3.0, 2.0, 3.0, 2.0, 4.0, 3.0])
    weights = np.array([[1, 1, 1, 1], [0, 2, 1, 1], [3, 1, 0, 0]], float)
    result = auc_draws(y, x, owner, weights, lambda: None)
    for i, w in enumerate(weights):
        assert np.isclose(result[i], roc_auc_score(y, x, sample_weight=w[owner]))
    coef, _ = train(x[:, None], y.astype(float), lambda: None)
    assert np.isfinite(coef).all() and coef[0] > 0
