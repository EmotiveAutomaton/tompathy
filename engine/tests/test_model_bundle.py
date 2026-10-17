from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from test_admission import record

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.admission import Admissions
from tompathy_engine.ledger.ids import digest
from tompathy_engine.ledger.provenance import provenance_for
from tompathy_engine.ledger.schema import Artifact, Decision, Maker, Option, Session
from tompathy_engine.ledger.store import Ledger
from tompathy_engine.models.bundle import Bundle, fit_bundle
from tompathy_engine.packet.build import build_packet


def fixture(tmp_path):
    ledger = Ledger(tmp_path)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    capture = make_capture(
        ["A constructed choice record."],
        "https://example.org/model-fixture",
        "Constructed fit",
        "2026-02-01T00:00:00Z",
    )
    rows = [
        Artifact(
            artifact_id=capture["id"],
            maker_ids=["short", "long"],
            kind="session",
            source_uri=capture["source"],
            tier="T2",
        )
    ]
    for maker, selected in [("short", "a"), ("long", "b")]:
        rows += [
            Maker(
                maker_id=maker,
                source_dataset="constructed",
                identity="synthetic",
                display_label=maker,
            ),
            Session(
                session_id=maker,
                maker_id=maker,
                artifact_id=capture["id"],
                t_start=start,
                t_end=start + timedelta(days=1),
            ),
        ]
        for i in range(24):
            t = start + timedelta(minutes=i)
            rows.append(
                Decision(
                    decision_id=f"{maker}-{i}",
                    maker_id=maker,
                    session_id=maker,
                    t_open=t,
                    t_resolve=t,
                    options=[
                        Option(
                            option_id="a",
                            origin="system",
                            position=i % 2,
                            content_ref=ledger.put_text("Short."),
                        ),
                        Option(
                            option_id="b",
                            origin="system",
                            position=1 - i % 2,
                            content_ref=ledger.put_text("Longer" + "r" * (40 + i) + "."),
                        ),
                    ],
                    # A stochastic tendency, not complete separation (whose
                    # Gaussian interval correctly remains wide).
                    taken=selected if i % 5 else ("b" if selected == "a" else "a"),
                    action="choose",
                )
            )
    ledger.append(rows, provenance_for(rows, "constructed", digest("fixture")))
    return ledger, capture


def test_fit_roundtrip_admission_and_packet(tmp_path):
    ledger, capture = fixture(tmp_path)
    bundle = fit_bundle(ledger, population="writing-v0", until=datetime(2026, 1, 2, tzinfo=UTC))
    restored = Bundle.model_validate_json(bundle.model_dump_json())
    cases = restored.verify(ledger, at=datetime(2026, 2, 1, tzinfo=UTC))
    np.testing.assert_allclose(
        bundle.predictor().predict("short", cases[0].features),
        restored.predictor().predict("short", cases[0].features),
        rtol=0,
        atol=1e-12,
    )
    plain = build_packet(capture, ledger=ledger, model=bundle)
    assert not any(h["kind"] == "value" for h in plain["hypotheses"])
    assert len(plain["process"]["nodes"]) == 48
    gates = Admissions(
        [record(module="backbone-preferences", implementation_hash=bundle.implementation_hash)]
    )
    packet = build_packet(capture, ledger=ledger, model=restored, admissions=gates)
    values = [h for h in packet["hypotheses"] if h["kind"] == "value"]
    assert values and all(h["support"]["semantics"] == "relative" and h["evidence"] for h in values)
    assert packet["schemaVersion"] == "1.8"
    for h in values:
        estimate = h["preferenceEstimate"]
        assert estimate["interval"]["lower"] <= estimate["value"] <= estimate["interval"]["upper"]
        assert estimate["interval"]["level"] == 0.95
        assert estimate["reference"] == 0
        assert "preferenceTrace" not in h
    assert all(h["interpretation"] == "preference" for h in values)
    assert packet["population"]["makersPooled"] == 2
    assert all(
        0 < item["shrinkage"] < 1 and item["makerRecords"] == 24
        for item in packet["population"]["items"]
    )
    assert "constructed-test-only" in packet["provider"]["admissions"]


def test_model_rejects_future_changed_ledger_and_wrong_pin(tmp_path):
    ledger, capture = fixture(tmp_path)
    bundle = fit_bundle(ledger, population="writing-v0", until=datetime(2026, 1, 2, tzinfo=UTC))
    with pytest.raises(ValueError, match="after the capture"):
        bundle.verify(ledger, at=datetime(2026, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="pin mismatch"):
        bundle.verify(ledger, at=datetime(2026, 2, 1, tzinfo=UTC), implementation="a" * 64)
    bundle.input_hash = "a" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        bundle.verify(ledger, at=datetime(2026, 2, 1, tzinfo=UTC))
    # Even a supplied model and admission cannot manufacture T0 maker evidence.
    gates = Admissions(
        [record(module="backbone-preferences", implementation_hash=bundle.implementation_hash)]
    )
    assert not build_packet(capture, admissions=gates, model=bundle)["hypotheses"]
