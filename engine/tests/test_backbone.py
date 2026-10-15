from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from tompathy_engine.eval.scoring import proper
from tompathy_engine.models.backbone import Backbone, Choice


def data():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Choice(
            str(i),
            "one" if i < 10 else "two",
            t + timedelta(seconds=2 * i),
            t + timedelta(seconds=2 * i + 1),
            np.eye(2),
            int(i % 5 == 0),
        )
        for i in range(20)
    ]


def test_population_positive_control_and_unseen_maker():
    rows = data()
    fit = Backbone.fit(rows, until=rows[-1].resolved + timedelta(seconds=1))
    assert 0.7 < fit.predict("unseen", np.eye(2))[0] < 0.9
    assert fit.shrinkage("unseen") == 0
    assert fit.predict("one", np.eye(2)).sum() == pytest.approx(1)


def test_future_labels_are_not_training_evidence():
    rows = data()
    cutoff = rows[10].opened
    fit = Backbone.fit(rows, until=cutoff)
    future_changed = rows[:10] + [
        Choice(r.id, r.maker, r.opened, r.resolved, r.features, 1 - r.taken) for r in rows[10:]
    ]
    second = Backbone.fit(future_changed, until=cutoff)
    assert fit.train_ids == second.train_ids
    np.testing.assert_array_equal(fit.beta, second.beta)
    with pytest.raises(ValueError, match="precedes"):
        fit.predict("one", np.eye(2), at=rows[0].opened)


def test_input_order_and_option_permutation_invariant():
    rows = data()
    cutoff = rows[-1].resolved + timedelta(seconds=1)
    a = Backbone.fit(rows, until=cutoff)
    b = Backbone.fit(list(reversed(rows)), until=cutoff)
    np.testing.assert_array_equal(a.beta, b.beta)
    np.testing.assert_allclose(
        a.predict("one", np.eye(2))[::-1], a.predict("one", np.eye(2)[::-1]), atol=1e-12
    )


def test_empty_prior_uniform_and_scores_retain_infinity():
    fit = Backbone.fit([], until=data()[0].opened, dimensions=3)
    np.testing.assert_allclose(fit.predict("new", np.eye(3)), np.ones(3) / 3)
    assert proper([0, 1], 0) == {"half_brier": 1.0, "log_loss": float("inf")}
    with pytest.raises(ValueError):
        proper([0.8, 0.8], 0)
