import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from tompathy_engine.ledger.ids import digest, maker_id
from tompathy_engine.ledger.provenance import provenance_for
from tompathy_engine.ledger.schema import Artifact, Decision, Maker, Option, Session
from tompathy_engine.ledger.store import Ledger


def fixture_rows():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Maker(
            maker_id="fixture:a",
            source_dataset="fixture",
            identity="synthetic",
            display_label="Same name",
        ),
        Artifact(
            artifact_id="a",
            maker_ids=["fixture:a"],
            kind="session",
            source_uri="fixture:a",
            tier="T2",
        ),
        Session(
            session_id="s",
            maker_id="fixture:a",
            artifact_id="a",
            t_start=t,
            t_end=t + timedelta(minutes=1),
        ),
        Decision(
            decision_id="d",
            maker_id="fixture:a",
            session_id="s",
            t_open=t,
            t_resolve=t + timedelta(seconds=3),
            action="choose",
            taken="o1",
            options=[Option(option_id="o1", origin="env", position=0)],
        ),
    ]


def provenance(rows):
    return provenance_for(rows, "constructed", digest("constructed"))


def test_atomic_round_trip_and_duplicate_refusal(tmp_path):
    ledger = Ledger(tmp_path)
    rows = fixture_rows()
    ledger.append(rows, provenance(rows))
    assert ledger.rows("Decision") == [rows[-1]]
    with pytest.raises(ValueError, match="Duplicate"):
        ledger.append(rows, provenance(rows))
    assert len(ledger.rows("Decision")) == 1
    assert len(list((tmp_path / "batches").iterdir())) == 1


def test_missing_provenance_and_references_do_not_append(tmp_path):
    ledger = Ledger(tmp_path)
    rows = fixture_rows()
    with pytest.raises(ValueError, match="provenance"):
        ledger.append(rows, [])
    with pytest.raises(ValueError, match="Unresolved"):
        ledger.append(rows[1:], provenance(rows[1:]))
    assert ledger.all() == []


def test_session_bounds_and_unknown_fields(tmp_path):
    rows = fixture_rows()
    rows[-1].t_resolve += timedelta(days=1)
    with pytest.raises(ValueError, match="chronology"):
        Ledger(tmp_path).append(rows, provenance(rows))
    with pytest.raises(ValidationError):
        Decision.model_validate(dict(rows[-1].model_dump(), latent_drives=[1, 0]))


def test_taken_and_naive_time_refuse():
    data = fixture_rows()[-1].model_dump()
    with pytest.raises(ValidationError, match="Taken option"):
        Decision.model_validate(dict(data, taken="never-offered"))
    with pytest.raises(ValidationError, match="timezone"):
        Decision.model_validate(dict(data, t_open=datetime(2026, 1, 1)))


def test_content_addressed_unicode_and_tampering(tmp_path):
    ledger = Ledger(tmp_path)
    text = "🌞\nA café with\tspace\r\n"
    ref = ledger.put_text(text)
    assert ledger.put_text(text) == ref
    assert ledger.get_text(ref) == text
    assert len(list(ledger.blobs.iterdir())) == 1
    with pytest.raises(ValueError):
        ledger.get_text("../schema.json")
    import zstandard

    (ledger.blobs / (ref + ".zst")).write_bytes(zstandard.compress(b"changed"))
    with pytest.raises(ValueError, match="hash mismatch"):
        ledger.get_text(ref)


def test_pin_and_pending_batch(tmp_path):
    ledger = Ledger(tmp_path)
    (ledger.batches / ".pending-crash").mkdir()
    assert ledger.all() == []
    (tmp_path / "schema.json").write_text(json.dumps({"schema_version": "0"}))
    with pytest.raises(ValueError, match="mismatch"):
        Ledger(tmp_path)


def test_ids_are_canonical_and_source_scoped():
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})
    assert maker_id("first", "same-person") != maker_id("second", "same-person")
    with pytest.raises(ValueError):
        digest(float("nan"))
