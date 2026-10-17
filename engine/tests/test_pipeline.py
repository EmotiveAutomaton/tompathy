from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from test_admission import record
from test_model_bundle import fixture

from tompathy_engine.admission import Admissions, implementation_hash
from tompathy_engine.features.records import Labels, inputs, subject
from tompathy_engine.ledger.ids import digest
from tompathy_engine.ledger.provenance import provenance_for
from tompathy_engine.ledger.schema import Correction, schema_hash
from tompathy_engine.models.pipeline import Pipeline, fit_pipeline
from tompathy_engine.packet.build import build_packet


def corrected(tmp_path):
    ledger, capture = fixture(tmp_path)
    rows = []
    for d in ledger.rows("Decision"):
        before, after = d.options if d.maker_id == "long" else list(reversed(d.options))
        if int(d.decision_id.split("-")[-1]) % 5 == 0:
            before, after = after, before
        rows.append(
            Correction(
                correction_id="c-" + d.decision_id,
                maker_id=d.maker_id,
                decision_id=d.decision_id,
                before_ref=before.content_ref,
                after_ref=after.content_ref,
                t=d.t_resolve + timedelta(seconds=1),
            )
        )
    ledger.append(rows, provenance_for(rows, "constructed", digest("corrections")))
    until = datetime(2026, 1, 2, tzinfo=UTC)
    source = inputs(ledger, domain="writing", until=until)
    pin = digest("constructed-transcriber")
    records = {
        q: {
            "question_id": q,
            "transcriber_pin": pin,
            "passed": True,
            "status": "admitted",
            "items": 200,
            "valid_rate": 1.0,
            "accuracy": 1.0,
            "per_label": {"\"yes\"": 1.0, "\"no\"": 1.0},
            "per_family": {"family-0": 1.0, "family-1": 1.0},
            "best_constant": 0.5,
            "battery_hash": digest(q),
            "admission_id": "constructed-battery-" + q,
        }
        for q in ("Q8", "Q9")
    }
    labels = Labels(
        domain="writing",
        until=until,
        transcriber_pin=pin,
        ledger_schema_hash=schema_hash(),
        question_records=records,
        labels={
            subject("Correction", c.correction_id, "edit"): {
                "input_hash": digest(source[subject("Correction", c.correction_id, "edit")]),
                "answers": {"Q8": "wording", "Q9": "yes"},
            }
            for c in rows
        },
    )
    return ledger, capture, labels, until


def gates(*modules):
    return Admissions(
        [
            record(
                module=m, admission_id="constructed-" + m, implementation_hash=implementation_hash()
            )
            for m in modules
        ]
    )


def test_correction_to_reading_and_roundtrip(tmp_path):
    ledger, capture, labels, until = corrected(tmp_path)
    fitted = fit_pipeline(ledger, population="writing-v0", until=until, labels=labels)
    restored = Pipeline.model_validate_json(fitted.model_dump_json())
    rows = restored.verify(ledger, at=datetime(2026, 2, 1, tzinfo=UTC))
    assert len(rows["corrections"]) == 48
    assert len(rows["joint"]) == 96
    x = rows["options"][0].features
    augmented = fitted.predict("long", x, at=until, task="correction-augmented")
    assert not np.allclose(augmented, fitted.predict("long", x, at=until, task="options"))
    with pytest.raises(ValueError, match="cutoff"):
        fitted.predict("long", x, at=until - timedelta(seconds=1), task="correction-augmented")
    np.testing.assert_allclose(fitted.fits["corrections"].beta, restored.fits["corrections"].beta)
    plain = build_packet(capture, ledger=ledger, model=restored)
    assert not any(h["kind"] == "value" for h in plain["hypotheses"])
    packet = build_packet(
        capture, ledger=ledger, model=restored, admissions=gates("corrections", "habits")
    )
    assert any(h["kind"] == "value" and h["evidence"] for h in packet["hypotheses"])
    assert any(h.get("interpretation") == "repertoire" for h in packet["hypotheses"])
    assert "constructed-battery-Q8" in packet["provider"]["admissions"]
    assert all(h.get("interpretation") != "drive" for h in packet["hypotheses"])


def test_process_and_unknown_edits_never_train_preferences(tmp_path):
    ledger, _, labels, until = corrected(tmp_path)
    for i, value in enumerate(labels.labels.values()):
        value.answers = {"Q8": "grammar" if i % 2 else "wording", "Q9": "no"}
    pipeline = fit_pipeline(ledger, population="writing-v0", until=until, labels=labels)
    assert "corrections" not in pipeline.fits
    assert set(pipeline.classifications.values()) == {"process"}
    pipeline = fit_pipeline(ledger, population="writing-v0", until=until)
    assert "corrections" not in pipeline.fits
    assert set(pipeline.classifications.values()) == {"unknown"}


def test_label_and_fit_tampering_is_rejected(tmp_path):
    ledger, capture, labels, until = corrected(tmp_path)
    model = fit_pipeline(ledger, population="writing-v0", until=until, labels=labels)
    with pytest.raises(ValueError, match="cutoff"):
        model.verify(ledger, at=until - timedelta(days=1))
    first = next(iter(model.labels.labels.values()))
    first.input_hash = "f" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        build_packet(capture, ledger=ledger, model=model, admissions=gates("corrections"))
    labels.question_records["Q9"]["accuracy"] = 0.2
    with pytest.raises(ValueError, match="battery"):
        labels.verify(ledger)


def test_snapshot_stays_pinned_during_append(tmp_path):
    ledger, _, _labels, until = corrected(tmp_path)
    snapshot = ledger.snapshot()
    row = ledger.rows("Correction")[0].model_copy(update={"correction_id": "later", "t": until})
    ledger.append([row], provenance_for([row], "constructed", digest("later")))
    assert len(snapshot.rows("Correction")) == 48
    assert len(ledger.rows("Correction")) == 49


def test_unstable_identity_does_not_become_a_personal_profile(tmp_path):
    from tompathy_engine.models.pipeline import cases

    ledger, _, labels, until = corrected(tmp_path)
    view = ledger.snapshot()
    unknown = view.rows("Maker")[0]
    unknown.identity = "unknown"
    options, corrections, _, excluded = cases(view, domain="writing", until=until, labels=labels)
    assert all(r.maker != unknown.maker_id for r in options + corrections)
    assert any("unstable identity" in reason for reason in excluded.values())
