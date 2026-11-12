"""Constructed software checks. No human corpus or reader admission."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.adapters.coauthor_events import attach_timeline, extract_changes
from tompathy_engine.adapters.replay import replay
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import build_preview, render_deviation
from tompathy_engine.preview.claims import departure_labels, load_snapshot, resolve_packet
from tompathy_engine.preview.outline import update_attention_density
from tompathy_engine.preview.surface import deviation_map
from tompathy_engine.preview.timeline import match_region, relink_timeline, wikipedia_timeline
from tompathy_engine.transcribe.admission import battery
from tompathy_engine.transcribe.question_profile import QuestionProfile, empty_theme_battery
from tompathy_engine.transcribe.runner import Transcriber

ROOT = Path(__file__).resolve().parents[2]


def base(texts=None):
    return build_preview(build_packet(make_capture(texts or ["A quiet light glows."], "https://example.org/week", "Test", "2026-10-25T12:00:00Z")))


def test_all_twelve_ev4_received_bytes():
    receipt = json.loads((ROOT / "docs/claims/EV4_DELIVERY_20261023.json").read_text(encoding="utf8"))
    assert len(receipt["files"]) == 12
    for name, expected in receipt["files"].items():
        assert hashlib.sha256((ROOT / "docs/sounding-line-engine-features-2026-10-20" / name).read_bytes()).hexdigest() == expected


def test_claims_require_exact_reader_and_definition_and_revoke_saved_badges():
    snapshot = load_snapshot()
    preview = {"departureDefinition": "5f3ad0a:surface-departure-v1", "readers": [{"id": "fixture", "revision": "test", "sha256": "a" * 64, "backend": "software test"}]}
    phrase = {"kind": "process", "finding": "departure-phrase"}
    assert departure_labels(phrase, preview, snapshot)["evidenceStatus"] == "unvalidated"
    for row in snapshot["rows"][:2]:
        row["reader"] = preview["readers"][0]
    labels = departure_labels(phrase, preview, snapshot)
    assert labels["evidenceStatus"] == "field-tested" and len(labels["ledgerRows"]) == 2
    assert departure_labels(phrase | {"finding": "departure-sentence"}, preview, snapshot)["evidenceStatus"] == "unvalidated"
    wrong = deepcopy(preview); wrong["readers"][0]["backend"] = "different precision"
    assert departure_labels(phrase, wrong, snapshot)["evidenceStatus"] == "unvalidated"
    packet = {"preview": preview, "hypotheses": [phrase | labels | {"id": "phrase"}], "currentAttention": [{"hypothesis": "phrase", **labels}]}
    assert resolve_packet(packet, snapshot)["hypotheses"][0]["evidenceStatus"] == "field-tested"
    assert packet["currentAttention"][0]["evidenceStatus"] == "field-tested"
    snapshot["rows"][0]["supersededBy"] = "retracted"
    assert resolve_packet(packet, snapshot)["hypotheses"][0]["evidenceStatus"] == "unvalidated"
    assert packet["currentAttention"][0]["evidenceStatus"] == "unvalidated"


def test_malformed_claim_snapshot_fails_closed(tmp_path, monkeypatch):
    import tompathy_engine.preview.claims as module
    path = tmp_path / "claims.json"
    monkeypatch.setattr(module, "SNAPSHOT", path)
    for value in ([], {"schema": "tompathy.claims.v1", "rows": [{}], "globalFindings": []}):
        path.write_text(json.dumps(value), encoding="utf8")
        assert module.load_snapshot() == {"rows": [], "globalFindings": []}


class Reader:
    identity: ClassVar[dict] = {"id": "fixture", "revision": "test", "sha256": "a" * 64, "backend": "software test"}

    def score(self, text, context="", check=lambda: None):
        # Stated per-character losses, deliberately high for the rare term.
        return [{"start": i, "end": i + 1, "nats": 12.0 if "zyzzyva" in text else 1.0} for i in range(len(text))]


def test_phrase_sentence_collision_keeps_sentence_marker_and_stable_identity():
    packet = base(["cobalt"])
    reader = Reader()
    result = deviation_map(packet["artifact"], reader)
    assert {r["finding"] for r in result["attention"]} == {"departure-phrase", "departure-sentence"}
    render_deviation(packet, reader, result, ["p1"])
    items = [h for h in packet["hypotheses"] if h.get("finding")]
    assert len(items) == 1 and items[0]["finding"] == "departure-sentence"
    assert items[0]["evidenceStatus"] == "unvalidated" and items[0]["ledgerRows"] == []
    old_id = items[0]["id"]
    render_deviation(packet, reader, result, ["p1"])
    assert [h["id"] for h in packet["hypotheses"] if h.get("finding")] == [old_id]
    Packet.model_validate(packet)


def groups(packet):
    packet["goalHierarchy"] = {"nodes": [{"id": f"group-{r['id']}", "maker": packet["makers"][0]["id"],
        "label": "Constructed group", "description": "Software fixture", "level": "paragraph", "regions": [r["id"]], "evidence": [],
        "evidenceStatus": "unvalidated", "basis": "model-judgment"} for r in packet["artifact"]["regions"]]}


def test_density_counts_hypotheses_not_frames_and_unread_is_not_zero():
    packet = base(["quiet paper light room " * 8 for _ in range(9)])
    groups(packet)
    packet["preview"]["coverage"] = [f"p{i}" for i in range(1, 9)]
    item = deepcopy(packet["hypotheses"][0])
    packet["hypotheses"] = [item | {"id": f"d{i}", "kind": "attention", "interpretation": "current-attention", "finding": "departure-phrase", "regions": ["p1"], "spans": [{"region": "p1", "start": i * 6, "end": i * 6 + 5}]} for i in range(3)]
    update_attention_density(packet)
    nodes = packet["goalHierarchy"]["nodes"]
    assert sum(n["divergence"] for n in nodes) == 1
    assert nodes[0]["attentionDensity"] == 100 * 3 / 32 and nodes[0]["attentionShare"] == 1
    assert nodes[-1]["attentionDensity"] is None and nodes[-1]["attentionEvidence"]["coverage"] == "not-read"
    packet["hypotheses"] = []
    update_attention_density(packet)
    assert not any(n["divergence"] for n in nodes)


@pytest.mark.xfail(strict=True, reason="Known confound: no pinned frequency residualisation; rare topic words can dominate density")
def test_rare_topic_repetition_does_not_dominate_density():
    packet = base(["zyzzyva zyzzyva zyzzyva " * 12] + ["quiet paper light room " * 9 for _ in range(8)])
    groups(packet)
    reader = Reader()
    result = deviation_map(packet["artifact"], reader)
    render_deviation(packet, reader, result, [r["id"] for r in packet["artifact"]["regions"]])
    update_attention_density(packet)
    assert not packet["goalHierarchy"]["nodes"][0]["divergence"]


def test_wiki_timeline_citations_unlocated_privacy_and_schema():
    packet = base(["A quiet [12] light glows. Keep [sic] exactly."])
    groups(packet)
    assert match_region("quiet light", packet["artifact"]["regions"]) == "p1"
    assert match_region("Keep exactly", packet["artifact"]["regions"]) is None
    history = {"revisions": [
        {"id": "10", "maker": "private-editor", "label": "private-editor", "t": "2026-10-24T10:00:00Z", "text": "A quiet light glows.", "parents": ["9"], "parent_text_witness": {"revision": "9", "text": "A glows."}},
        {"id": "11", "maker": "private-editor", "t": "2026-10-24T11:00:00Z", "text": "private-editor inserted deleted material", "parents": ["10"]}]}
    wikipedia_timeline(packet, history)
    timeline = packet["attentionTimeline"]
    assert any(e["located"] and e["node"] == "group-p1" for e in timeline)
    assert any(not e["located"] and e["node"] is None for e in timeline)
    assert "private-editor" not in json.dumps(packet["evidence"])
    Packet.model_validate(packet)
    broken = deepcopy(packet); broken["attentionTimeline"][0]["node"] = "missing"
    with pytest.raises(ValueError, match="timeline node"):
        Packet.model_validate(broken)
    broken = deepcopy(packet); broken["attentionTimeline"][0]["unexpected"] = 1
    with pytest.raises(ValueError):
        Packet.model_validate(broken)
    packet.pop("goalHierarchy"); relink_timeline(packet)
    assert all(e["node"] is None for e in timeline)


def test_five_hundred_revision_excerpts_stay_bounded_after_redaction():
    packet = base(["A quiet light glows."])
    history = {"revisions": [{"id": str(i), "maker": "x", "t": "2026-10-24T10:00:00Z",
        "text": "x " * 300, "parents": ["before-" + str(i)],
        "parent_text_witness": {"revision": "before-" + str(i), "text": ""}} for i in range(500)]}
    wikipedia_timeline(packet, history)
    excerpts = [e["excerpt"] for e in packet["evidence"] if "#revision=" in e["source"]]
    assert len(excerpts) == len(packet["attentionTimeline"]) == 500
    assert all(len(e) <= 320 and "x" not in e for e in excerpts)
    Packet.model_validate(packet)
    assert len(json.dumps(packet, ensure_ascii=False)) < 2_000_000


def test_coauthor_exact_deltas_survivors_deletions_and_unicode_map():
    events = [
        {"eventName": "system-initialize", "currentDoc": "Prompt\n", "eventTimestamp": 1000},
        {"eventName": "text-insert", "eventTimestamp": 2000, "textDelta": {"ops": [{"retain": 7}, {"insert": "gone"}]}},
        {"eventName": "text-delete", "eventTimestamp": 3000, "textDelta": {"ops": [{"retain": 7}, {"delete": 4}]}},
        {"eventName": "suggestion-open", "eventTimestamp": 4000, "currentSuggestions": [{"index": 0, "original": "x", "trimmed": "x"}]},
        {"eventName": "text-insert", "eventTimestamp": 5000, "textDelta": {"ops": [{"retain": 7}, {"insert": "  😀  hello\n"}]}}]
    result = extract_changes(events)
    assert result["deltas"] == replay(events)["deltas"] == 3
    assert result["final_document"] == "Prompt\n  😀  hello\n"
    assert result["capture"]["regions"][1]["anchor"]["exact"] == "😀 hello"
    assert result["changes"][0]["regions"] == result["changes"][1]["regions"] == []
    assert result["changes"][2]["regions"] == ["p2"]
    assert result["menus"][0]["step"] == 3
    packet = attach_timeline(build_preview(build_packet(result["capture"])), result)
    assert [e["located"] for e in packet["attentionTimeline"]] == [False, False, True]
    Packet.model_validate(packet)


def test_new_question_pins_are_separate_and_fixed_cpu_pin_unchanged(monkeypatch):
    import tompathy_engine.transcribe.question_profile as module
    backend = SimpleNamespace(model_id="software-test", settings={"profile": "live-gpu-2"})
    legacy = Transcriber(backend, None); old = legacy.pin
    profile = QuestionProfile(backend, None)
    q1, q10 = profile.pin_for("Q1"), profile.pin_for("Q10")
    monkeypatch.setattr(module, "Q10", module.Q10 + " Changed fixture.")
    assert profile.pin_for("Q1") == q1 and profile.pin_for("Q10") != q10
    assert legacy.pin == old == legacy.pin_for("Q1")
    with pytest.raises(ValueError, match="live-gpu-2"):
        QuestionProfile(SimpleNamespace(settings={}), None)


def test_empty_theme_battery_is_frozen_and_reports_empty_accuracy():
    items = empty_theme_battery()
    assert items == json.loads((ROOT / "engine/validation/q10-empty-v2.items.json").read_text(encoding="utf8"))
    assert len(items) == 200 and sum(i["expected"] == [] for i in items) == 40
    class Oracle:
        pin = "software-test"
        requires_empty_theme_gate = True
        def ask(self, question_id, *, text, **kwargs):
            return {"answer": next(i["expected"] for i in items if i["text"] == text)}
    receipt = battery(Oracle(), "Q10", items)
    assert receipt["empty_accuracy"] == 1 and receipt["protocol"] == "q10-empty-v2"
    assert receipt["passed"]  # Oracle software test, never a saved reader admission.
    with pytest.raises(ValueError, match="40 theme-free"):
        battery(Oracle(), "Q10", [dict(i, id=str(n)) for n, i in enumerate(items[:160] + items[:40])])
