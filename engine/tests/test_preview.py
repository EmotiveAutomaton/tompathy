from copy import deepcopy
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import build_preview
from tompathy_engine.preview.habits import describe
from tompathy_engine.preview.surface import words
from tompathy_engine.registry.publish import publish
from tompathy_engine.serve.app import create_app


def capture():
    return make_capture(["We build the future. We build the future. But why?", '“We build the future.” A quiet ending.'], "https://example.org/essay", "Essay", "2026-10-16T00:00:00Z")


def test_preview_separate_complete_labels_and_empty_states():
    base = build_packet(capture(), request_id="fixed")
    before = deepcopy(base)
    partials = []
    result = build_preview(base, partial=partials.append)
    assert base == before == build_packet(capture(), request_id="fixed")
    assert result["provider"]["mode"] == "preview"
    assert all(h["basis"] and h["evidenceStatus"] for h in result["hypotheses"])
    assert not any(h["kind"] == "value" for h in result["hypotheses"])
    assert {m["id"]: m["status"] for m in result["preview"]["modules"]}["deviation"] == "unavailable"
    assert partials and all(Packet.model_validate(p) for p in partials)
    for field in ("basis", "evidenceStatus"):
        broken = deepcopy(result)
        del broken["hypotheses"][0][field]
        with pytest.raises(ValueError, match="Preview items require"):
            Packet.model_validate(broken)
    broken = deepcopy(result)
    broken["hypotheses"][0]["support"] = {"value": .5, "scale": [0, 1], "semantics": "probability", "meaning": "test", "calibration": "test", "candidateSet": "x"}
    with pytest.raises(ValueError, match="Preview support must be relative"):
        Packet.model_validate(broken)


def test_habits_do_not_mix_quotes_or_invent_population():
    result = describe(capture())
    assert result["quotedWords"] == 4
    assert result["repeats"][0]["count"] == 2
    assert result == describe(capture())


def test_surface_alignment_and_holdouts():
    text = "Hello Alice 123 `code` world. New day."
    tokens = [{"start": i, "end": i + 1, "nats": 1.} for i in range(len(text))]
    result = {w["text"]: w for w in words(text, tokens)}
    assert not result["Hello"]["held"]
    assert result["Alice"]["held"] and result["123"]["held"] and result["code"]["held"]
    assert not result["New"]["held"]
    assert result["world"]["nats"] == 7  # word plus its trailing period and space


def test_preview_registry_refused_even_for_private_registry(tmp_path):
    packet = build_preview(build_packet(capture()))
    with pytest.raises(ValueError, match="stay local"):
        publish([packet], tmp_path, private=True)
    assert not list(tmp_path.iterdir())


def test_mode_off_exact_service_result():
    token = "a" * 64
    with TestClient(create_app(token=token), base_url="http://127.0.0.1") as client:
        body = {"requestId": "same", "artifact": capture(), "scope": "artifact", "mode": "admitted"}
        response = client.post("/v1/analyze", json=body, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == build_packet(capture(), request_id="same")


def test_cancel_does_not_become_module_failure():
    from tompathy_engine.serve.app import Cancelled
    def check():
        raise Cancelled()
    with pytest.raises(Cancelled):
        build_preview(build_packet(capture()), check=check)


class FixtureReader:
    identity: ClassVar = {"id": "software-test-reader", "revision": "fixture", "sha256": "a" * 64, "backend": "test double; not a demonstration reading"}

    def score(self, text, context="", check=lambda: None):
        check()
        return [{"start": i, "end": i + 1, "nats": (i % 7 + 1) / 3} for i in range(len(text))]


def test_phrase_and_sentence_frames_preserve_all_overlaps():
    packet = build_preview(build_packet(capture()), readers=[FixtureReader()])
    assert next(m for m in packet["preview"]["modules"] if m["id"] == "deviation")["status"] == "complete"
    frames = packet["currentAttention"]
    assert frames and all(item["evidenceStatus"] == "unvalidated" for f in frames for item in f["items"])
    Packet.model_validate(packet)
    expected = {h["id"] for h in packet["hypotheses"] if h["kind"] == "attention"}
    assert expected == {item["hypothesis"] for f in frames for item in f["items"]}


def test_exact_fixed_reader_identity_is_not_a_production_admission(tmp_path):
    from tompathy_engine.preview.fixed_backend import FixedQwen
    from tompathy_engine.preview.judgments import fixed_reader
    from tompathy_engine.transcribe.cache import Cache
    reader = fixed_reader(FixedQwen("http://127.0.0.1:9999"), Cache(tmp_path / "cache.sqlite"))
    assert not reader.admissions
    reader.backend.settings["seed"] = 1
    with pytest.raises(ValueError, match="differ"):
        fixed_reader(reader.backend, reader.cache)


def test_budget_keeps_only_validated_partial_results():
    from tompathy_engine.preview.build import BudgetExceeded, hypothesis
    def techniques(packet, check, publish):
        hypothesis(packet, "complete", "Completed literal", "Software fixture")
        publish()
        hypothesis(packet, "unfinished", "Unfinished literal", "Must not escape")
        raise BudgetExceeded()
    result = build_preview(build_packet(capture()), technique_runner=techniques)
    labels = {h["label"] for h in result["hypotheses"]}
    assert "Completed literal" in labels and "Unfinished literal" not in labels
    assert next(m for m in result["preview"]["modules"] if m["id"] == "techniques")["status"] == "skipped"


def test_invalid_module_output_cannot_destroy_the_completed_reading():
    def invalid(packet, check, publish):
        packet["hypotheses"].extend([deepcopy(packet["hypotheses"][0])] * 1001)
    packet = build_preview(build_packet(capture()), technique_runner=invalid)
    Packet.model_validate(packet)
    assert next(m for m in packet["preview"]["modules"] if m["id"] == "habits")["status"] == "complete"
    assert next(m for m in packet["preview"]["modules"] if m["id"] == "techniques")["status"] == "failed"


def test_history_failure_preserves_preview_but_not_admitted_path(tmp_path):
    def fail(*args, **kwargs):
        raise ValueError("No licensed history")
    token = "a" * 64
    with TestClient(create_app(token=token, history_dir=tmp_path, history_fetcher=fail), base_url="http://127.0.0.1") as client:
        body = {"requestId": "preview", "artifact": capture(), "scope": "artifact", "history": "wikipedia", "mode": "preview"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/v1/analyze", json=body, headers=headers)
        assert response.status_code == 200
        assert next(m for m in response.json()["preview"]["modules"] if m["id"] == "history")["status"] == "unavailable"
        body.update(requestId="admitted", mode="admitted")
        assert client.post("/v1/analyze", json=body, headers=headers).status_code == 422


def test_real_run_cache_timestamp_and_input_invalidation(tmp_path):
    token = "a" * 64
    with TestClient(create_app(token=token, preview_cache=tmp_path), base_url="http://127.0.0.1") as client:
        body = {"requestId": "first", "artifact": capture(), "scope": "artifact", "mode": "preview"}
        headers = {"Authorization": f"Bearer {token}"}
        first = client.post("/v1/analyze", json=body, headers=headers).json()
        assert "cachedAt" not in first["preview"]
        body["requestId"] = "second"
        second = client.post("/v1/analyze", json=body, headers=headers).json()
        assert second["preview"]["cachedAt"] and first["hypotheses"] == second["hypotheses"]
        body["requestId"] = "third"
        body["artifact"]["title"] = "A changed root cue"
        third = client.post("/v1/analyze", json=body, headers=headers).json()
        assert "cachedAt" not in third["preview"]
        body.update(requestId="backup", preferCache=True)
        body["artifact"]["capturedAt"] = "2026-10-16T01:00:00Z"
        backup = client.post("/v1/analyze", json=body, headers=headers).json()
        assert backup["preview"]["cachedAt"] and backup["hypotheses"] == third["hypotheses"]
        body.update(requestId="missing-backup")
        body["artifact"]["title"] = "Never analyzed"
        missing = client.post("/v1/analyze", json=body, headers=headers)
        assert missing.status_code == 422 and "No matching cached" in missing.text


def test_declared_tool_evidence_and_local_username_privacy(tmp_path):
    from tompathy_engine.adapters.github import trailers
    from tompathy_engine.admission import Admissions
    from tompathy_engine.workflow import analyze_history
    author = "Source Person"
    declarations = trailers("Explain the garden\n\nCo-authored-by: Claude <noreply@anthropic.com>\nCo-authored-by: Human <human@example.org>")
    assert len(declarations) == 1 and declarations[0]["label"] == "Claude"
    artifact = capture()
    rows = [{"id": "a", "parents": [], "text": "The garden.", "maker": "person-1", "label": author, "t": "2026-10-14T01:00:00Z", "summary": "Source Person drafts"},
            {"id": "b", "parents": ["a"], "text": "The quiet garden.", "maker": "person-1", "label": author, "t": "2026-10-15T01:00:00Z", "summary": "Source Person edits", "declared_tools": declarations}]
    history = {"artifact_id": artifact["id"], "source_uri": artifact["source"], "license": "MIT", "license_evidence": "https://example.org/license", "revisions": rows, "declaredAiCommitShare": .5}
    base, _ = analyze_history(artifact, directory=tmp_path, admissions=Admissions(), payload=history, adapter="git")
    result = build_preview(base, history=history, history_adapter="git")
    person = next(m for m in result["makers"] if m.get("kind") == "person")
    tool = next(m for m in result["makers"] if m.get("kind") == "model")
    assert person["localLabel"] == author and person["label"] == "Contributor 1"
    assert tool["decisions"]["drafted"] == 1 and tool["evidence"][0]["tier"] == "declared"
    assert author not in result["preview"]["latestSummary"]
    assert result["makers"][0]["kind"] == "unknown"
    Packet.model_validate(result)


def test_code_holdouts_use_utf16_source_ranges_and_reject_out_of_bounds():
    from tompathy_engine.preview.surface import source_holdouts, words
    artifact = make_capture(["A 🌱 grows near sampleCode and water."], "https://example.org/code", "Code", "2026-10-16T00:00:00Z")
    region = artifact["regions"][0]
    text = region["anchor"]["exact"]
    start = text.index("sampleCode")
    region["codeSpans"] = [{"start": start + 1, "end": start + 11}]
    tokens = [{"start": i, "end": i + 1, "nats": 1.} for i in range(len(text))]
    scored = words(text, tokens, source_holdouts(region))
    assert next(w for w in scored if w["text"] == "sampleCode")["held"]
    assert not next(w for w in scored if w["text"] == "water")["held"]
    Packet.model_validate(build_packet(artifact))
    region["codeSpans"][0]["end"] = 999
    with pytest.raises(ValueError, match="Code span"):
        build_packet(artifact)


def test_future_revisions_do_not_enter_preview_maker_counts_or_root_cues(tmp_path):
    from tompathy_engine.admission import Admissions
    from tompathy_engine.workflow import analyze_history
    artifact = capture()
    history = {"artifact_id": artifact["id"], "source_uri": artifact["source"], "license": "MIT", "license_evidence": "https://example.org/license", "revisions": [
        {"id": "before", "parents": [], "text": "Before", "maker": "m", "label": "Writer", "t": "2026-10-15T00:00:00Z", "summary": "Earlier edit"},
        {"id": "after", "parents": ["before"], "text": "After", "maker": "m", "label": "Writer", "t": "2026-10-17T00:00:00Z", "summary": "Future edit", "declared_tools": [{"kind": "model", "label": "Claude", "detail": "Declared future contribution"}]},
    ]}
    base, _ = analyze_history(artifact, directory=tmp_path, admissions=Admissions(), payload=history, adapter="git")
    result = build_preview(base, history=history, history_adapter="git")
    assert result["preview"]["latestSummary"] == "Earlier edit"
    assert result["preview"]["github"]["commits"] == 1
    assert result["preview"]["github"]["declaredAiCommitShare"] == 0
    assert not any(m.get("kind") == "model" for m in result["makers"])


def test_parent_text_witness_records_changes_without_inventing_parent_revision(tmp_path):
    from tompathy_engine.adapters.history import ingest_history
    from tompathy_engine.ledger.store import Ledger
    artifact = capture()
    revision = {"id": "child", "parents": ["unlisted-tree-parent"], "text": "The quiet garden.", "maker": "m", "label": "Writer",
                "t": "2026-10-15T00:00:00Z", "summary": "Clarify", "parent_text_witness": {"revision": "unlisted-tree-parent", "text": "The garden."}}
    history = {"artifact_id": artifact["id"], "source_uri": artifact["source"], "license": "MIT", "license_evidence": "https://example.org/license", "revisions": [revision]}
    ledger = Ledger(tmp_path / "ledger")
    receipt = ingest_history(history, ledger, adapter="git")
    assert receipt["corrections"] > 0 and receipt["revisions"] == 1
    assert len(ledger.rows("Revision")) == 1
    revision["parent_text_witness"]["revision"] = "a-different-parent"
    with pytest.raises(ValueError, match="witness"):
        ingest_history(history, Ledger(tmp_path / "bad"), adapter="git")


def test_completed_correction_pair_survives_the_next_call_budget(tmp_path):
    from contextlib import nullcontext

    from tompathy_engine.admission import Admissions
    from tompathy_engine.preview.build import BudgetExceeded
    from tompathy_engine.workflow import analyze_history

    class Reader:
        calls = 0

        @property
        def backend(self):
            return self

        def checking(self, check):
            return nullcontext()

        def ask(self, question, **kwargs):
            self.calls += 1
            if self.calls > 2:
                raise BudgetExceeded()
            return {"answer": "add content" if question == "Q8" else "yes"}

    artifact = capture()
    history = {"artifact_id": artifact["id"], "source_uri": artifact["source"], "license": "MIT", "license_evidence": "https://example.org/license", "revisions": [
        {"id": "a", "parents": [], "maker": "m", "text": "A garden.", "t": "2026-10-14T00:00:00Z"},
        {"id": "b", "parents": ["a"], "maker": "m", "text": "A quiet garden.", "t": "2026-10-15T00:00:00Z"},
        {"id": "c", "parents": ["b"], "maker": "m", "text": "A quiet green garden.", "t": "2026-10-15T01:00:00Z"},
    ]}
    base, _ = analyze_history(artifact, directory=tmp_path, payload=history, adapter="git", admissions=Admissions())
    result = build_preview(base, history=history, history_adapter="git", correction_reader=Reader())
    assert next(m for m in result["preview"]["modules"] if m["id"] == "corrections")["status"] == "skipped"
    assert next(m for m in result["makers"] if m["kind"] == "person")["decisions"]["edited"] == 1
    assert len([h for h in result["hypotheses"] if h["basis"] == "corrections"]) == 1
    Packet.model_validate(result)
