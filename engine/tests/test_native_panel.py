import hashlib
import json

import pytest

from tompathy_engine.adapters.native_panel import convert, from_manifest, timestamp
from tompathy_engine.adapters.panel import ingest
from tompathy_engine.ledger.ids import digest, maker_id
from tompathy_engine.ledger.schema import schema_hash
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


def multipref_row():
    return {
        "comparison_id": 42,
        "prompt_id": "published-prompt",
        "text": "Prompt",
        "completion_a": "One answer",
        "completion_b": "Another answer",
        "normal_worker_annotations": [
            {
                "evaluator": "released-label-007",
                "timestamp": "2024-05-22 12:38:48.027304",
                "time_spent": 12,
                "overall_pref": "B-is-clearly-better",
                "reason": "Original annotation",
                "confidence": 3,
            }
        ],
        "expert_worker_annotations": [],
    }


def test_source_ids_raw_annotations_license_and_pins_survive(tmp_path):
    row = multipref_row()
    m = manifest("multipref", timezone="UTC", timezone_evidence="Constructed timezone witness")
    exchange, receipt = convert([row], m)
    item = exchange["rows"][0]
    assert item["id"] == digest([42, "normal_worker_annotations", "released-label-007", "overall"])
    source = item["native_source"]
    assert source["ids"] == {
        "comparison_id": 42,
        "prompt_id": "published-prompt",
        "evaluator": "released-label-007",
    }
    assert source["record_index"] == 0 and source["record_sha256"] == digest(row)
    assert source["observed"] == row["normal_worker_annotations"][0]
    assert (
        exchange["codebook"] == m["codebook"]
        and exchange["license_evidence"] == m["license_evidence"]
    )
    assert exchange["mapping"]["timezone_evidence"] == m["timezone_evidence"]
    assert receipt["exchange_hash"] == digest(exchange)
    assert receipt["ledger_schema_hash"] == schema_hash()
    assert len(receipt["implementation_hash"]) == 64 and not receipt["scientific_admission"]
    ledger = Ledger(tmp_path)
    report = ingest(exchange, ledger)
    decision = ledger.rows("Decision")[0]
    assert decision.maker_id == maker_id("multipref", "released-label-007")
    assert decision.context["source_observation_id"] == item["id"]
    assert decision.context["native_source"]["ids"] == source["ids"]
    assert "observed" not in decision.context["native_source"]
    assert decision.outcome["native_observation"] == source["observed"]
    assert report["row_audit"][0]["decision_id"] == decision.decision_id
    assert report["row_audit"][0]["exclusion"] is None
    ingest(exchange, ledger)
    assert len(ledger.rows("Decision")) == 1
    item["native_source"]["observed"]["reason"] = "Changed export"
    assert row["normal_worker_annotations"][0]["reason"] == "Original annotation"


def test_chronology_witness_is_retained_and_unknown_dates_stay_excluded(tmp_path):
    row = multipref_row()
    raw, _ = convert([row], manifest("multipref"))
    report = ingest(raw, Ledger(tmp_path / "undated"))
    assert report["row_audit"][0]["exclusion"] == "missing_chronology"
    assert report["row_audit"][0]["native_source"]["ids"]["evaluator"] == "released-label-007"
    key = raw["rows"][0]["id"]
    witness = {
        "t_open": "2024-05-22T12:38:36.027304+00:00",
        "t_resolve": "2024-05-22T12:38:48.027304+00:00",
        "evidence": "Constructed independent event-window witness",
    }
    dated, _ = convert([row], manifest("multipref", chronology={key: witness}))
    assert dated["rows"][0]["chronology_witness"] == witness
    ledger = Ledger(tmp_path / "dated")
    assert ingest(dated, ledger)["row_audit"][0]["chronology_witness"] == witness
    assert ledger.rows("Decision")[0].outcome["chronology_witness"] == witness


@pytest.mark.parametrize("mutation", ["blank", "naive", "reversed", "unknown", "contradictory"])
def test_bad_chronology_witness_refuses(mutation):
    row = multipref_row()
    raw, _ = convert([row], manifest("multipref"))
    key = raw["rows"][0]["id"]
    witness = {
        "t_open": "2024-05-22T12:38:36.027304+00:00",
        "t_resolve": "2024-05-22T12:38:48.027304+00:00",
        "evidence": "Test witness",
    }
    if mutation == "blank":
        witness["evidence"] = "  "
    if mutation == "naive":
        witness["t_open"] = "2024-05-22T12:38:36.027304"
    if mutation == "reversed":
        witness["t_open"] = "2025-01-01T00:00:00Z"
    if mutation == "unknown":
        key = "not-a-source-observation"
    if mutation == "contradictory":
        witness["t_resolve"] = "2024-05-22T13:00:00Z"
    with pytest.raises(ValueError, match="chronology"):
        convert(
            [row],
            manifest(
                "multipref", timezone="UTC", timezone_evidence="Fixture", chronology={key: witness}
            ),
        )


@pytest.mark.parametrize("value", ["2024-11-03T01:30:00", "2024-03-10T02:30:00"])
def test_named_timezone_does_not_guess_dst_fold_or_gap(value):
    m = manifest("multipref", timezone="America/New_York", timezone_evidence="Fixture")
    assert timestamp(value, m) is None
    assert timestamp("2024-11-03T01:30:00-04:00", m) == "2024-11-03T05:30:00+00:00"
    assert timestamp("2024-11-04T01:30:00", m) == "2024-11-04T06:30:00+00:00"


def test_missing_duration_is_unknown_and_invalid_duration_refuses():
    row = multipref_row()
    m = manifest("multipref", timezone="UTC", timezone_evidence="Fixture")
    row["normal_worker_annotations"][0]["time_spent"] = None
    exchange, _ = convert([row], m)
    assert exchange["rows"][0]["t_open"] is None
    assert exchange["rows"][0]["t_resolve"] is not None
    for duration in [-1, "nan", "inf"]:
        row["normal_worker_annotations"][0]["time_spent"] = duration
        with pytest.raises(ValueError, match="duration"):
            convert([row], m)


def test_movielens_timestamp_never_fabricates_decision_window(tmp_path):
    row = {
        "userId": 7,
        "movieId": 11,
        "isSeen": 1,
        "tstamp": "1670476480",
        "userElicitRating": "4.5",
    }
    exchange, _ = convert([row], manifest("movielens-beliefs"))
    item = exchange["rows"][0]
    assert item["t_open"] is None and item["t_resolve"] is None
    assert item["taken"] == "4.5" and item["action"] == "rate"
    assert item["native_source"]["ids"] == {"userId": 7, "movieId": 11, "tstamp": "1670476480"}
    ledger = Ledger(tmp_path / "unknown")
    report = ingest(exchange, ledger)
    assert report["excluded"] == {"missing_chronology": 1}
    assert not ledger.rows("Decision")
    witness = {
        "t_open": "2022-12-08T04:34:30Z",
        "t_resolve": "2022-12-08T04:34:40Z",
        "evidence": "Constructed opening/resolution witness, not released MovieLens metadata",
    }
    dated, _ = convert([row], manifest("movielens-beliefs", chronology={item["id"]: witness}))
    ledger = Ledger(tmp_path / "witnessed")
    assert ingest(dated, ledger)["usable_decisions"] == 1
    assert ledger.rows("Decision")[0].action == "rate"


def test_interface_keeps_original_ledger_schema():
    from tompathy_engine.interface import contract

    interface = contract()
    assert interface["native_panel"]["format"] == "tompathy-native-panel-2"
    assert (
        interface["ledger_schema_hash"]
        == "ab5c4f63f66693da9b3be0cf33598e1a244b25f6b7ad0538ef2c92ee7a9c49c7"
    )


def test_native_export_refuses_duplicate_observation_ids():
    m = manifest("multipref")
    m["expected_source_rows"] = 2
    with pytest.raises(ValueError, match="Duplicate native observation"):
        convert([multipref_row(), multipref_row()], m)


def test_prism_survey_exclusion_keeps_mapping_to_retained_preference(tmp_path):
    row = {
        "user_id": "released-user-09",
        "stated_prefs": {"helpfulness": 77},
        "generated_datetime": "2024-01-01",
    }
    exchange, _ = convert(
        [row],
        manifest(
            "prism",
            record_kind="survey",
            preference_scales={"helpfulness": [1, 100]},
            scale_evidence="Constructed scale witness",
        ),
    )
    ledger = Ledger(tmp_path)
    trace = ingest(exchange, ledger)["row_audit"][0]
    assert trace["exclusion"] == "missing_chronology" and trace["decision_id"] is None
    assert trace["stated_preference_ids"] == [ledger.rows("StatedPreference")[0].pref_id]
    assert trace["native_source"]["ids"]["user_id"] == row["user_id"]
    assert exchange["mapping"]["scale_evidence"] == "Constructed scale witness"


def test_explicit_rating_still_cannot_train_text_choice_model(tmp_path):
    from tompathy_engine.eval.ledger import choices

    row = {
        "id": 9,
        "rater_id": "source-rater",
        "item_id": 17,
        "answer_timestamp": "1670476480",
        "answer_time_ms": "2000",
        "context": "Context",
        "response": "Response",
        "Q2_test": "No",
    }
    exchange, _ = convert([row], manifest("dices", target="Q2_test"))
    ledger = Ledger(tmp_path)
    ingest(exchange, ledger)
    assert len(ledger.rows("Decision")) == 1
    assert not choices(ledger, domain="preferences")
