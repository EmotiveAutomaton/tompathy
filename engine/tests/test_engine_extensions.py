import json
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from test_pipeline import corrected, gates

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.features.augment import Features
from tompathy_engine.features.records import inputs
from tompathy_engine.ledger.ids import digest
from tompathy_engine.ledger.provenance import provenance_for
from tompathy_engine.ledger.schema import ContextEvent, schema_hash
from tompathy_engine.models.backbone import Choice
from tompathy_engine.models.calibration_record import calibrate
from tompathy_engine.models.goal_producer import produce
from tompathy_engine.models.pipeline import Pipeline, fit_pipeline
from tompathy_engine.models.prototypes import discover
from tompathy_engine.packet.build import build_packet
from tompathy_engine.transcribe.batteries import constructed
from tompathy_engine.transcribe.cache import Cache


def themed(tmp_path):
    ledger, capture, labels, until = corrected(tmp_path)
    labels.question_records["Q10"] = {
        **labels.question_records["Q8"],
        "question_id": "Q10",
        "admission_id": "constructed-Q10",
    }
    for key, data in inputs(ledger, domain="writing", until=until).items():
        answer = ["danger"] if len(data["text"]) > 10 else ["care"]
        if key in labels.labels:
            labels.labels[key].answers["Q10"] = answer
        else:
            from tompathy_engine.features.records import Label

            labels.labels[key] = Label(input_hash=digest(data), answers={"Q10": answer})
    return (
        ledger,
        capture,
        fit_pipeline(
            ledger, population="writing-v0", until=until, labels=labels, questions=["Q10"]
        ),
    )


def test_theme_drives_and_zero_record_prior_remain_separate(tmp_path):
    ledger, capture, pipeline = themed(tmp_path)
    packet = build_packet(
        capture,
        ledger=ledger,
        model=pipeline,
        admissions=gates("joint-preferences", "drive-recipes"),
    )
    drives = [h for h in packet["hypotheses"] if h.get("interpretation") == "drive"]
    assert drives and all(h["support"]["semantics"] == "relative" for h in drives)
    assert not any(h["icon"] == "seeking" for h in drives)
    fresh = make_capture(
        ["Danger alone is not motive."], "https://example.org/fresh", "Fresh", capture["capturedAt"]
    )
    plain = build_packet(fresh, ledger=ledger, model=pipeline, admissions=gates("drive-recipes"))
    assert not plain["hypotheses"]
    borrowed = build_packet(
        fresh, ledger=ledger, model=pipeline, admissions=gates("population-prior", "drive-recipes")
    )
    assert len(borrowed["hypotheses"]) == 7
    assert all(
        i["makerRecords"] == 0 and i["shrinkage"] == 0 for i in borrowed["population"]["items"]
    )
    assert "currentAttention" not in borrowed and not borrowed["process"]["nodes"]
    for name, p in (("drives", packet), ("borrowed", borrowed)):
        (tmp_path / (name + ".json")).write_text(json.dumps(p))


def test_optional_features_bind_to_inputs_and_survive_model_roundtrip(tmp_path):
    ledger, _, labels, until = corrected(tmp_path)
    source = inputs(ledger, domain="writing", until=until, full_context=True)
    features = Features(
        domain="writing",
        until=until,
        ledger_schema_hash=schema_hash(),
        names=["constructed-entity-count"],
        model_pins={"entities": "a" * 64},
        rows={
            k: {"input_hash": digest(v), "values": [float("Short" in v["text"])]}
            for k, v in source.items()
        },
    )
    fitted = fit_pipeline(
        ledger, population="writing-v0", until=until, labels=labels, extra_features=features
    )
    restored = Pipeline.model_validate_json(fitted.model_dump_json())
    restored.verify(ledger, at=until)
    assert restored.features[-1] == "constructed-entity-count"
    next(iter(restored.extra_features.rows.values())).input_hash = "f" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        restored.verify(ledger, at=until)


def test_inspection_events_require_exact_capture_coordinates(tmp_path):
    ledger, capture, _, _ = corrected(tmp_path)
    session = ledger.rows("Session")[0]
    row = ContextEvent(
        event_id="inspection",
        session_id=session.session_id,
        kind="other",
        t=session.t_start + timedelta(seconds=1),
        payload={
            "capture_revision": capture["revision"],
            "region": capture["regions"][0]["id"],
            "inspection_kind": "dwell",
            "duration_ms": 1200,
        },
    )
    ledger.append([row], provenance_for([row], "constructed", digest("inspection")))
    packet = build_packet(capture, ledger=ledger, admissions=gates("attention"))
    assert any(h["label"] == "Recorded dwell" for h in packet["hypotheses"])
    changed = make_capture(["Different text"], capture["source"], "Changed", capture["capturedAt"])
    assert "currentAttention" not in build_packet(
        changed, ledger=ledger, admissions=gates("attention")
    )


def test_goal_producer_is_cached_and_links_depths(tmp_path):
    class Backend:
        model_id = "constructed-goal-model"

        @property
        def settings(self):
            return {"seed": 0}

        calls = 0

        def complete(self, prompt, schema):
            self.calls += 1
            return {
                "text": json.dumps(
                    {
                        "label": "Explain",
                        "description": "An explanatory hypothesis",
                        "support": 0.6,
                        "cue_match": 0,
                        "cue_ids": [],
                    }
                )
            }

    capture = make_capture(
        ["First.", "Second."], "https://example.org/goals", "Goals", "2026-01-01T00:00:00Z"
    )
    backend, cache = Backend(), Cache(tmp_path / "cache.sqlite")
    first = produce(capture, None, backend, cache, maker="m")
    second = produce(capture, None, backend, cache, maker="m")
    assert backend.calls == 3 and first == second
    assert first.candidates[-1].depth > first.candidates[0].depth
    with pytest.raises(ValueError, match="bound"):
        produce(capture, None, backend, cache, maker="m", maximum_calls=1)


def test_calibration_final_makers_cannot_fit_parameters():
    def rows(prefix):
        return [
            {
                "id": prefix + str(i),
                "maker": prefix,
                "p": [0.6, 0.4],
                "baseline": [0.5, 0.5],
                "y": i % 2,
            }
            for i in range(20)
        ]

    payload = {
        "dataset": "constructed",
        "source_hash": "a" * 64,
        "training_makers": ["train"],
        "calibration": rows("cal"),
        "test": rows("test"),
    }
    for key, date in (("calibration", "2026-01-02"), ("test", "2026-01-03")):
        for row in payload[key]:
            row.update(
                training_latest="2026-01-01T00:00:00Z",
                opened=date + "T00:00:00Z",
                resolved=date + "T00:00:01Z",
            )
    result = calibrate(payload)
    altered = json.loads(json.dumps(payload))
    for row in altered["test"]:
        row["y"] = 0
    assert calibrate(altered)["parameters"] == result["parameters"]
    altered["test"][0]["maker"] = "cal"
    with pytest.raises(ValueError, match="held-out"):
        calibrate(altered)


def test_prototypes_and_batteries_are_reproducible():
    offsets = {"a": np.array([1.0, 0]), "b": np.array([-1.0, 0]), "c": np.array([1.0, 0.1])}
    np.testing.assert_allclose(discover(offsets), discover(dict(reversed(list(offsets.items())))))
    for q in [f"Q{i}" for i in range(1, 11) if i != 2]:
        items = constructed(q)
        assert len(items) == len({r["id"] for r in items}) == 200
        assert {"negation", "paraphrase"} <= set().union(*(r["tags"] for r in items))
    with pytest.raises(ValueError, match="spaCy"):
        constructed("Q2")


@pytest.mark.parametrize("method", ["svi", "nuts"])
def test_cpu_posterior_both_paths_use_only_earlier_examples(method):
    pytest.importorskip("numpyro")
    from tompathy_engine.models.bayesian import fit

    at = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        Choice(
            str(i),
            "m" + str(i % 2),
            at + timedelta(seconds=i),
            at + timedelta(seconds=i),
            np.array([[0.0, 0.0], [1.0, 0.0]]),
            i % 2,
        )
        for i in range(13)
    ]
    result = fit(
        rows, until=at + timedelta(seconds=12), method=method, warmup=10, samples=12, steps=20
    )
    assert len(result["train_ids"]) == 12 and "12" not in result["train_ids"]
    assert result["active_features"] == [True, False]
    assert np.isfinite(result["summary"]["predictability"]["mean"]).all()


def test_expertise_uses_censored_revision_outcomes(tmp_path):
    from types import SimpleNamespace

    from tompathy_engine.adapters.history import ingest_history
    from tompathy_engine.ledger.store import Ledger
    from tompathy_engine.packet.contract import Packet
    from tompathy_engine.packet.process_signals import apply_signals

    capture = make_capture(
        ["E"],
        "https://en.wikipedia.org/wiki/Constructed_expertise",
        "Expertise",
        "2026-01-10T00:00:00Z",
    )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    texts = ["base", "A", "B", "C", "D", "C", "D", "C", "E"]
    payload = {
        "artifact_id": capture["id"],
        "source_uri": capture["source"],
        "license": "CC0-1.0",
        "license_evidence": "Constructed",
        "revisions": [
            {
                "id": str(i),
                "parents": [str(i - 1)] if i else [],
                "maker": "a" if i < 8 else "b",
                "t": (start + timedelta(hours=i if i < 8 else 72)).isoformat(),
                "text": text,
            }
            for i, text in enumerate(texts)
        ],
    }
    ledger = Ledger(tmp_path)
    ingest_history(payload, ledger, adapter="wikipedia")
    revision_rows = sorted(ledger.rows("Revision"), key=lambda r: r.t)
    kept_type = {r.revision_id for r in revision_rows[1:4]}
    by_correction = {c.correction_id: c.revision_id for c in ledger.rows("Correction")}
    labels = SimpleNamespace(
        answers=lambda kind, ident, slot: {
            "Q8": "typo" if by_correction[ident] in kept_type else "wording"
        },
        require=lambda q: "constructed-" + q,
    )
    packet = build_packet(capture, ledger=ledger)
    used = apply_signals(
        packet,
        ledger,
        gates("expertise"),
        domain="writing",
        tier="T1",
        pipeline=SimpleNamespace(labels=labels),
    )
    assert "constructed-expertise" in used
    assert any(h["label"] == "Candidate expertise: typo" for h in packet["hypotheses"])
    Packet.model_validate(packet)
    early = make_capture(["C"], capture["source"], "Early", "2026-01-01T08:00:00Z")
    packet = build_packet(early, ledger=ledger)
    assert not apply_signals(
        packet,
        ledger,
        gates("expertise"),
        domain="writing",
        tier="T1",
        pipeline=SimpleNamespace(labels=labels),
    )


def test_display_bound_preserves_references_and_reports_omissions():
    from tompathy_engine.packet.bounds import bound
    from tompathy_engine.packet.contract import Packet

    capture = make_capture(
        ["Constructed."], "https://example.org/bounds", "Bound", "2026-01-01T00:00:00Z"
    )
    packet = build_packet(capture)
    for i in range(1002):
        packet["hypotheses"].append(
            {
                "id": str(i),
                "kind": "process",
                "interpretation": "historical-event",
                "label": "Event",
                "description": "Constructed event",
                "makers": [packet["makers"][0]["id"]],
                "regions": [],
                "status": "observed",
                "evidence": [packet["evidence"][0]["id"]],
            }
        )
        packet["process"]["nodes"].append(str(i))
        if i:
            packet["process"]["edges"].append(
                {"from": str(i - 1), "to": str(i), "relationship": "Earlier event"}
            )
    bound(packet)
    Packet.model_validate(packet)
    assert len(packet["hypotheses"]) == 1000 and "omitted 2" in packet["provider"]["method"]
