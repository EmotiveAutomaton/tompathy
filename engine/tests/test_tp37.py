import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from tompathy_engine.eval.readers.tp37 import (
    dimension_tables,
    rank_counts,
    rank_curve,
    rotate,
    standardized,
)


def test_two_fixed_rank_rules_stop_at_different_boundaries():
    losses = np.tile([1.0, 0.8, 0.81, 0.7], (5, 1))
    assert rank_counts(losses) == (3, 1)
    assert rank_counts(np.ones((5, 7))) == (0, 0)


def test_writer_held_out_curve_matches_the_reference_form():
    rng = np.random.default_rng(53)
    x = rng.normal(size=(300, 6))
    y = np.argmax(x[:, :3] + rng.normal(size=(300, 3)), axis=1)
    writers = np.repeat(np.arange(60), 5)
    checkpoints = {}

    def save_fold(fold, held_out, losses, effective_rank):
        checkpoints[fold] = (held_out.copy(), losses.copy(), effective_rank)

    loss, assigned, ranks = rank_curve(x, y, writers, lambda: None, save_fold=save_fold)
    assert ranks == [2] * 5
    for fold, (train, test) in enumerate(GroupKFold(5).split(x, y, writers)):
        assert np.all(assigned[test] == fold) and not set(writers[train]) & set(writers[test])
        saved_ids, saved_losses, saved_rank = checkpoints[fold]
        np.testing.assert_array_equal(saved_ids, test)
        np.testing.assert_array_equal(saved_losses, loss[fold])
        assert saved_rank == ranks[fold]
        prior = np.bincount(y[train]) / len(train)
        train_x = standardized(x[train])
        test_x = (x[test] - x[train].mean(0)) / x[train].std(0)
        lda = LinearDiscriminantAnalysis().fit(train_x, y[train])
        expected = [log_loss(y[test], np.tile(prior, (len(test), 1)))]
        for rank in (1, 2):
            mdl = LogisticRegression(penalty=None, max_iter=500).fit(
                lda.transform(train_x)[:, :rank], y[train]
            )
            expected.append(log_loss(y[test], mdl.predict_proba(lda.transform(test_x)[:, :rank])))
        np.testing.assert_allclose(loss[fold], expected, rtol=1e-12)


def test_rotated_tables_match_direct_correlations_and_word_means():
    rng = np.random.default_rng(32)
    x = standardized(rng.normal(size=(120, 4)))
    y = np.tile(np.arange(3), 40)
    z = rotate(x, x[:, :2] + 0.1 * rng.normal(size=(120, 2)), y)
    axes = dimension_tables(
        x,
        z,
        y,
        np.repeat(np.arange(24), 5),
        ["r1", "r2", "r3", "r4"],
        ["a", "b", "c"],
        lambda: None,
    )
    for j, axis in enumerate(axes):
        direct = np.array([np.corrcoef(x[:, k], z[:, j])[0, 1] for k in range(4)])
        assert direct[np.argmax(np.abs(direct))] >= 0
        np.testing.assert_allclose([v["estimate"] for v in axis["ratings"].values()], direct)
        np.testing.assert_allclose(
            [v["estimate"] for v in axis["words"].values()], [z[y == k, j].mean() for k in range(3)]
        )
        assert all(v["finiteDraws"] == 2000 for v in axis["ratings"].values())
