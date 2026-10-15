from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from tompathy_engine.models.calibration import (
    Temperature,
    contextual,
    ece,
    gate,
    prior_shift,
    stack,
)
from tompathy_engine.models.corrections import classification
from tompathy_engine.models.diagnosticity import diagnosticity, weights
from tompathy_engine.models.goal_tree import GoalCandidate as Goal
from tompathy_engine.models.goal_tree import governing_cover
from tompathy_engine.models.source_trust import SourceObservation, trajectory


def test_literal_corrections_never_turn_surface_edits_into_values():
    assert classification("wording", "yes") == "unknown"
    assert classification("typo", "yes", labels_admitted=True) == "process"
    assert classification("tone", "no", labels_admitted=True) == "process"
    assert classification("tone", "yes", labels_admitted=True) == "preference"


def test_weight_double_count_and_log_evidence():
    assert diagnosticity(0.5, 0.5) == 0
    assert diagnosticity(0.8, 0.2) == pytest.approx(np.log(4))
    assert weights([-1, 0, 1], 0, -1)[0] > weights([-1, 0, 1], 0, -1)[-1]
    with pytest.raises(ValueError, match="both"):
        weights([0], 0, 1, utility_features=["latency_s"])


def test_calibration_needs_heldout_makers_and_evaluates_its_gate():
    p = np.tile([[0.9, 0.1], [0.1, 0.9]], (10, 1))
    y = np.tile([0, 1], 10)
    with pytest.raises(ValueError, match="held-out"):
        Temperature.fit(
            p, y, training_makers=["same"], calibration_makers=["same"] * 20, dataset="fixture"
        )
    model = Temperature.fit(
        p, y, training_makers=["train"], calibration_makers=["held"] * 20, dataset="fixture"
    )
    q = model.apply(p)
    assert ece(q, y) < ece(p, y)
    assert gate(q, p, y)["passed"]
    shifted, prior = prior_shift(p, [0.5, 0.5])
    assert np.allclose(shifted, p)
    assert np.allclose(prior, [0.5, 0.5])
    assert np.allclose(contextual(p, [[0.5, 0.5]]), p)
    mixture = stack(
        [p, np.full_like(p, 0.5)], y, training_makers=["train"], calibration_makers=["held"] * 20
    )
    assert mixture[0] > 0.99


def test_governing_goal_covers_all_leaves_at_first_join_or_parallel_cover():
    leaves = {"a", "b"}
    candidates = [
        Goal("broad", frozenset(leaves), 8, 1, 1),
        Goal("specific", frozenset(leaves), 2, 0.5, 0.2),
    ]
    assert governing_cover(leaves, candidates, root_reliability=1)["governing"] == ["specific"]
    parallel = [Goal("one", frozenset({"a"}), 1, 0.6), Goal("two", frozenset({"b"}), 1, 0.7)]
    assert governing_cover(leaves, parallel)["governing"] == ["one", "two"]
    assert governing_cover(leaves, parallel[:1])["status"] == "unknown"


def test_source_quality_never_leaks_session_final_survival_into_past():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    first = SourceObservation("one", "s", t, True, -1, t + timedelta(hours=1))
    second = SourceObservation("two", "s", t + timedelta(minutes=1), False)
    clean = SourceObservation("one", "s", t, True)
    assert trajectory([first, second], until=t + timedelta(minutes=2)) == trajectory(
        [clean, second], until=t + timedelta(minutes=2)
    )
    other = SourceObservation("three", "other", t + timedelta(minutes=2), True)
    assert (
        trajectory([first, second, other], until=t + timedelta(minutes=3))[-1][
            "acceptance_propensity"
        ]
        == 0.5
    )
