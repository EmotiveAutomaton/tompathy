import pytest
from replay_fixtures import fixtures

from tompathy_engine.adapters.coauthor import compile_session
from tompathy_engine.ledger.ids import digest
from tompathy_engine.ledger.store import Ledger


@pytest.mark.parametrize("case", fixtures()[:4], ids=lambda c: c["key"])
def test_compile_witnessed_episodes(case, tmp_path):
    events = case["lines"]
    for i, event in enumerate(events):
        event["eventTimestamp"] = 1700000000000 + 1000 * i
        event["currentCursor"] = len("Workshop 0: ") + 2
    ledger = Ledger(tmp_path)
    rows, provenance, exclusions = compile_session(
        events,
        source_id=case["key"],
        writer="one",
        prompt="Write a story",
        source_hash=digest(events),
        ledger=ledger,
    )
    assert not exclusions
    ledger.append(rows, provenance)
    decision = ledger.rows("Decision")[0]
    assert decision.action == case["target"]["handling"]
    assert decision.outcome["endorsed"] == "unknown"
    if decision.action in {"accept", "edit"}:
        assert 0 <= decision.outcome["episode_retention_fraction"] <= 1
        assert 0 <= decision.outcome["session_retention_fraction"] <= 1
        assert decision.outcome["source_quality_available"] == decision.t_resolve.isoformat()
    assert len(decision.options) == 2
    assert len(ledger.rows("Correction")) == (decision.action == "edit")


def test_bad_chronology_refuses_even_when_text_replays(tmp_path):
    events = fixtures()[0]["lines"]
    for i, event in enumerate(events):
        event["eventTimestamp"] = 1700000000000 - 1000 * i
    with pytest.raises(ValueError, match="chronology"):
        compile_session(
            events,
            source_id="a",
            writer="one",
            prompt="Story",
            source_hash=digest(events),
            ledger=Ledger(tmp_path),
        )


def test_hashed_prompt_is_not_goal_text(tmp_path):
    events = fixtures()[0]["lines"]
    for i, event in enumerate(events):
        event["eventTimestamp"] = 1700000000000 + 1000 * i
        event["currentCursor"] = len("Workshop 0: ") + 2
    ledger = Ledger(tmp_path)
    rows, provenance, _ = compile_session(
        events,
        source_id="prompt-id-only",
        writer="one",
        prompt=None,
        prompt_id="f" * 64,
        source_hash=digest(events),
        ledger=ledger,
    )
    ledger.append(rows, provenance)
    assert not ledger.rows("StatedGoal")
    assert ledger.rows("Decision")[0].context["prompt_id"] == "f" * 64
    assert not ledger.rows("Session")[0].stated_goal_ids
