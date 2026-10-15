import pytest
from replay_fixtures import fixtures

from tompathy_engine.adapters.quill import apply_delta, units
from tompathy_engine.adapters.replay import replay


@pytest.mark.parametrize("case", fixtures(), ids=lambda c: c["key"])
def test_64_constructed_records(case):
    result = replay(case["lines"])
    assert result["reconstructed"]
    assert result["events"][0]["end_document"] == case["event"]["end_document"]
    assert case["target"]["attributes"] == {
        "reviewed": "unknown",
        "endorsed": "unknown",
        "understood": "unknown",
    }


def test_utf16_surrogate_split_and_overflow_refuse():
    doc = units("🌞x")
    with pytest.raises(UnicodeError):
        apply_delta(doc, [None] * len(doc), {"ops": [{"delete": 1}]})
    with pytest.raises(ValueError):
        apply_delta(doc, [None] * len(doc), {"ops": [{"retain": 99}]})


def test_selection_without_insertion_does_not_establish_acceptance():
    rows = fixtures()[0]["lines"][:3]
    result = replay(rows)
    assert not result["events"][0]["usable"]
    assert result["events"][0]["review"] == "unknown"


def test_reopening_does_not_invent_another_decision():
    rows = fixtures()[2]["lines"]
    rows.insert(
        3, {"eventName": "suggestion-reopen", "currentSuggestions": rows[1]["currentSuggestions"]}
    )
    result = replay(rows)
    assert len(result["events"]) == 1
    assert result["events"][0]["reopens"] == 1
    assert result["events"][0]["decision"] == "ignore"
