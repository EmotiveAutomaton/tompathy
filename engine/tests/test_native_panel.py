import hashlib
import json

import pytest

from tompathy_engine.adapters.native_panel import convert, from_manifest
from tompathy_engine.adapters.panel import ingest
from tompathy_engine.ledger.store import Ledger


def manifest(dataset, **kw):
    return dict(
        dataset=dataset,
        expected_source_rows=1,
        source_uri="https://example.org/data",
        source_sha256="a" * 64,
        codebook="constructed codebook",
        license_evidence="constructed",
        **kw,
    )


def test_multipref_preserves_annotations_ties_and_naive_time(tmp_path):
    a = {
        "evaluator": "one",
        "timestamp": "2024-05-22 12:38:48.027304",
        "time_spent": 12,
        "overall_pref": "A-is-clearly-better",
    }
    r = {
        "comparison_id": "c",
        "prompt_id": "p",
        "text": "Prompt",
        "completion_a": "A",
        "completion_b": "B",
        "normal_worker_annotations": [a, dict(a, evaluator="two", overall_pref="Tie")],
        "expert_worker_annotations": [],
    }
    exchange, receipt = convert([r], manifest("multipref"))
    assert receipt["normalized_observation_units"] == 2
    assert ingest(exchange, Ledger(tmp_path / "missing"))["usable_decisions"] == 0
    exchange, _ = convert([r], manifest("multipref", timezone="UTC", timezone_evidence="fixture"))
    ledger = Ledger(tmp_path / "present")
    result = ingest(exchange, ledger)
    assert result["usable_decisions"] == 1
    assert result["excluded"] == {"unresolved_or_tie": 1}
    assert ledger.rows("Decision")[0].context["prompt_id"] == "p"


def test_prism_does_not_borrow_conversation_time(tmp_path):
    r = {
        "conversation_id": "c",
        "user_id": "u",
        "generated_datetime": "2024-01-01",
        "conversation_history": [
            {"turn": 1, "role": "user", "content": "Question"},
            {
                "turn": 1,
                "role": "model",
                "content": "Answer",
                "if_chosen": True,
                "within_turn_id": 0,
            },
        ],
    }
    exchange, _ = convert([r], manifest("prism"))
    assert ingest(exchange, Ledger(tmp_path))["excluded"] == {"missing_chronology": 1}


def test_dices_is_a_rating_not_preference_between_answers(tmp_path):
    r = {
        "id": "r",
        "rater_id": "u",
        "item_id": "i",
        "answer_timestamp": "1670476480",
        "answer_time_ms": "2000",
        "context": "Context",
        "response": "Response",
        "Q2_test": "No",
    }
    exchange, _ = convert([r], manifest("dices", target="Q2_test"))
    ledger = Ledger(tmp_path)
    ingest(exchange, ledger)
    d = ledger.rows("Decision")[0]
    assert d.action == "rate" and d.taken == "No"
    assert (d.t_resolve - d.t_open).total_seconds() == 2


def test_movielens_separates_expected_from_experienced(tmp_path):
    r = {
        "userId": "u",
        "movieId": "m",
        "isSeen": "0",
        "tstamp": "1670476480",
        "userPredictRating": "4.5",
        "userCertainty": "3",
        "userElicitRating": "-1",
        "systemPredictRating": "2.0",
    }
    exchange, _ = convert([r], manifest("movielens-beliefs"))
    ledger = Ledger(tmp_path)
    ingest(exchange, ledger)
    assert not ledger.rows("Decision")
    prefs = ledger.rows("StatedPreference")
    assert len(prefs) == 2 and {p.value for p in prefs} == {4.5, 3}


def test_native_bytes_and_path_are_checked(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text(
        json.dumps(
            {
                "info": {"id": "p", "post": "Prompt"},
                "summaries": [{"text": "a"}, {"text": "b"}],
                "worker": "w",
                "choice": 1,
            }
        )
    )
    m = manifest("summarize-from-feedback", file=source.name)
    m["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(m))
    exchange, _ = from_manifest(path)
    assert exchange["rows"][0]["taken"] == "1"
    source.write_text("{}")
    with pytest.raises(ValueError, match="pin"):
        from_manifest(path)
    m["file"] = "../escape.jsonl"
    path.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="escapes"):
        from_manifest(path)


def test_prism_survey_preserves_explicit_scales_without_borrowing_dates(tmp_path):
    row = {
        "user_id": "one",
        "stated_prefs": {"helpfulness": 77, "other_text": None},
        "generated_datetime": "2024-01-01",
    }
    m = manifest(
        "prism",
        record_kind="survey",
        preference_scales={"helpfulness": [1, 100]},
        scale_evidence="constructed scale witness",
    )
    exchange, _ = convert([row], m)
    ledger = Ledger(tmp_path)
    ingest(exchange, ledger)
    pref = ledger.rows("StatedPreference")[0]
    assert pref.value == 77 and pref.scale == [1, 100] and pref.t is None
