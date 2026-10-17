"""Software invariants for scheduling and progress; no scientific admission."""
from copy import deepcopy
from typing import ClassVar

import pytest

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import build_preview, hypothesis
from tompathy_engine.preview.judgments import goal_groups, stepped
from tompathy_engine.preview.surface import score_regions


def capture():
    return make_capture(["First sentence. A prior thought.", "Second passage with words.", "Third passage with words."],
                        "https://example.org/progress", "Constructed scheduler check", "2026-10-17T00:00:00Z")


def test_scheduling_yields_between_judgments_and_preserves_partial_validation():
    order, partials = [], []
    def runner(name):
        @stepped
        def run(packet, check, publish):
            for i in range(3):
                check()
                order.append((name, i))
                hypothesis(packet, [name, i], f"{name} {i}", "Constructed software fixture")
                publish()
                yield
        return run
    result = build_preview(build_packet(capture()), goal_runner=runner("goals"), technique_runner=runner("techniques"), partial=partials.append)
    assert order == [(name, i) for i in range(3) for name in ("goals", "techniques")]
    assert all(Packet.model_validate(p) for p in partials)
    assert not result["preview"]["resumable"]


def test_priority_changes_order_without_changing_causal_context():
    artifact = capture()
    calls = []
    class Reader:
        def score(self, text, context, check):
            calls.append((text, context))
            return [{"start": 0, "end": len(text), "nats": 1.0}]
    rows = list(score_regions(artifact, Reader(), priority=artifact["regions"][2]["id"]))
    assert rows[0]["region"] == artifact["regions"][2]["id"]
    assert calls[0][1] == artifact["regions"][1]["anchor"]["exact"]
    assert calls[1][1] == ""


def test_phrase_that_is_also_a_sentence_keeps_one_stable_id():
    artifact = make_capture(["Short heading", "Another short paragraph."], "https://example.org/short", "Short", "2026-10-17T00:00:00Z")
    class Reader:
        identity: ClassVar = {"id": "fixture", "revision": "fixture", "sha256": "a" * 64, "backend": "constructed software test"}
        def score(self, text, context, check):
            return [{"start": 0, "end": len(text), "nats": 1.0}]
    packet = build_preview(build_packet(artifact), readers=[Reader()])
    assert next(m for m in packet["preview"]["modules"] if m["id"] == "deviation")["status"] == "complete"
    attention = [h for h in packet["hypotheses"] if h["kind"] == "attention"]
    assert len({h["id"] for h in attention}) == len(attention)
    Packet.model_validate(packet)


def test_partial_large_passage_never_labels_unscored_suffix():
    artifact = capture()
    class Reader:
        def score_chunks(self, text, context, check):
            yield [{"start": 0, "end": 5, "nats": 1.}], False
            yield [{"start": 0, "end": len(text), "nats": 2.}], True
    rows = list(score_regions(artifact, Reader()))
    assert rows[0]["text"] == "First" and not rows[0]["complete"]
    assert rows[1]["text"] == artifact["regions"][0]["anchor"]["exact"]
    assert rows[1]["complete"]


def test_partial_word_and_blank_context_do_not_change_the_measure():
    artifact = capture()
    artifact["regions"][1]["anchor"]["exact"] = "\n"
    calls = []
    class Reader:
        def score(self, text, context, check):
            calls.append((text, context))
            return []
        def score_chunks(self, text, context, check):
            yield [{"start": 0, "end": 3, "nats": 1.}], False
    list(score_regions(artifact, Reader(), short=True, priority=artifact["regions"][2]["id"]))
    assert calls[0][1] == " A prior thought."
    assert next(score_regions(artifact, Reader()))["text"] == ""


def test_window_cache_survives_interruption_without_leaking_inference_mode(tmp_path):
    from types import SimpleNamespace

    import torch

    from tompathy_engine.preview.readers import LocalReader
    reader = LocalReader.__new__(LocalReader)
    reader.torch, reader.device, reader.cache = torch, "cpu", tmp_path
    reader.identity = {"fixture": "constructed tiny tensor, no language model"}
    reader.tokenizer = SimpleNamespace(bos_token_id=0)
    reader.encode = lambda text: {"input_ids": [0] * len(text), "offset_mapping": [(i, i + 1) for i in range(len(text))]}
    reader.metrics = {"cacheHits": 0, "forwardCalls": 0, "scoreMs": 0., "inputTokens": 0}
    reader.model = lambda tensor, use_cache, logits_to_keep: SimpleNamespace(logits=torch.zeros((1, len(logits_to_keep), 2)))
    iterator = reader.score_chunks("a" * 1025)
    partial, complete = next(iterator)
    assert len(partial) == 512 and not complete
    assert not torch.is_inference_mode_enabled()
    iterator.close()
    full = reader.score("a" * 1025)
    assert len(full) == 1025 and reader.metrics["cacheHits"] == 1
    assert reader.metrics["forwardCalls"] == 3
    assert not torch.is_inference_mode_enabled()


def test_early_goal_groups_cover_source_once_and_remain_bounded():
    for count in (1, 2, 20, 21, 328, 1500):
        regions = [{"id": str(i)} for i in range(count)]
        for priority in (0, count // 2, count - 1):
            groups = goal_groups(regions, str(priority))
            assert groups[0] == [regions[priority]]
            assert len(groups) <= 20
            assert sorted(int(r["id"]) for group in groups for r in group) == list(range(count))
            assert all([int(r["id"]) for r in group] == list(range(int(group[0]["id"]), int(group[-1]["id"]) + 1)) for group in groups)


def test_progress_cannot_exceed_work_total():
    packet = build_preview(build_packet(capture()))
    broken = deepcopy(packet)
    broken["preview"]["modules"][0].update(completed=3, total=2)
    with pytest.raises(ValueError, match="bounded"):
        Packet.model_validate(broken)


def test_clef_is_joint_unvalidated_and_cache_reuses_all_answers(tmp_path):
    from tompathy_engine.preview.clef import techniques
    from tompathy_engine.transcribe.cache import Cache
    class Backend:
        calls = 0
        identity = "fixture"
        config: ClassVar = {"revision": "software-fixture", "sha256": "a" * 64}
        metrics: ClassVar = {}
        def decide(self, state, questions, check):
            self.calls += 1
            assert len(questions) == 5
            return {key: {"choice": "unclear", "probabilities": {option: float(option == "unclear") for option in q["criteria"]}} for key, q in questions.items()}
    backend = Backend()
    runner = techniques(backend, Cache(tmp_path / "clef.sqlite"))
    first = build_preview(build_packet(capture()), technique_runner=runner)
    second = build_preview(build_packet(capture()), technique_runner=runner)
    assert backend.calls == 3
    assert first["hypotheses"] == second["hypotheses"]
    assert all(h["evidenceStatus"] == "unvalidated" for h in first["hypotheses"])


def test_clef_rejects_nonlocal_and_missing_pins():
    from tompathy_engine.preview.clef import Clef
    with pytest.raises(ValueError, match="loopback"):
        Clef({"url": "https://example.org", "model": "clef-flash", "revision": "fixture", "sha256": "a" * 64})
    with pytest.raises(ValueError, match="requires"):
        Clef({"url": "http://127.0.0.1:9000"})


@pytest.mark.parametrize("bad", [None, "missing-question", "nonfinite", "unavailable-option"])
def test_clef_systemone_wire_contract(monkeypatch, bad):
    import json

    import httpx

    from tompathy_engine.preview.clef import Clef

    original = httpx.AsyncClient
    questions = {"Q5": {"type": "choice", "instructions": "Constructed protocol check", "criteria": {"yes": "yes", "no": "no"}}}
    def response(request):
        assert request.method == "POST" and request.url == "http://127.0.0.1:9000/v1/systemone"
        payload = json.loads(request.content)
        assert payload["questions"] == questions and payload["state"] == {"text": "Constructed fixture"}
        raw = {"model": "clef-flash", "answers": {"Q5": {"choice": "yes", "probabilities": {"yes": .75, "no": .25}}}}
        if bad == "missing-question":
            raw["answers"] = {}
        elif bad == "nonfinite":
            raw["answers"]["Q5"]["probabilities"]["yes"] = float("nan")
        elif bad == "unavailable-option":
            raw["answers"]["Q5"]["choice"] = "invented"
        return httpx.Response(200, content=json.dumps(raw), headers={"Content-Type": "application/json"})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(response), **kwargs))
    backend = Clef({"url": "http://127.0.0.1:9000", "model": "clef-flash", "revision": "software-fixture", "sha256": "a" * 64})
    if bad:
        with pytest.raises(ValueError):
            backend.decide({"text": "Constructed fixture"}, questions, lambda: None)
    else:
        assert backend.decide({"text": "Constructed fixture"}, questions, lambda: None)["Q5"]["choice"] == "yes"
        assert backend.metrics["calls"] == 1


def test_compact_stream_reconstructs_valid_readings_and_checkpoint(tmp_path):
    import json
    import time

    from fastapi.testclient import TestClient

    from tompathy_engine.preview.build import BudgetExceeded
    from tompathy_engine.serve.app import create_app

    @stepped
    def runner(packet, check, publish):
        for i in range(3):
            hypothesis(packet, ["step", i], f"Step {i}", "Constructed fixture")
            publish()
            time.sleep(.1)
            yield
        raise BudgetExceeded()

    token = "b" * 64
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}
    artifact = capture()
    priority = artifact["regions"][2]["id"]
    body = {"requestId": "stream", "artifact": artifact, "scope": "artifact", "mode": "preview", "compactProgress": True, "priorityRegion": priority}
    with TestClient(create_app(token=token, preview_cache=tmp_path, preview_goals=runner), base_url="http://127.0.0.1") as client:
        response = client.post("/v1/analyze", json=body, headers=headers)
        assert response.status_code == 200 and "event: partial-update" in response.text
        previous = None
        for block in response.text.strip().split("\n\n"):
            lines = block.splitlines()
            event = lines[0].removeprefix("event: ")
            value = json.loads(lines[1].removeprefix("data: "))
            if event == "partial":
                previous = value
            elif event == "partial-update":
                previous.update(value)
                previous = {k: v for k, v in previous.items() if v is not None}
            else:
                continue
            Packet.model_validate(previous)
        body.update(requestId="cached", preferCache=True, priorityRegion="p0")
        headers.pop("Accept")
        cached = client.post("/v1/analyze", json=body, headers=headers).json()
        assert cached["preview"]["resumable"]
        assert cached["preview"]["priorityRegion"] == priority
        assert len([h for h in cached["hypotheses"] if h["label"].startswith("Step")]) == 3


def test_resume_replay_cannot_replace_a_better_checkpoint():
    from tompathy_engine.preview.cache import keeps_progress
    previous = build_preview(build_packet(capture()))
    previous["preview"]["modules"][0].update(completed=2, total=3, status="skipped")
    previous["preview"]["coverage"] = ["p0", "p1"]
    replay = deepcopy(previous)
    replay["preview"]["modules"][0]["completed"] = 1
    assert not keeps_progress(replay, previous)
    replay["preview"]["modules"][0]["completed"] = 3
    replay["preview"]["coverage"] = ["p0"]
    assert not keeps_progress(replay, previous)
    replay["preview"]["coverage"] = ["p0", "p1", "p2"]
    assert keeps_progress(replay, previous)


def test_owned_clef_cache_survives_restart_but_rejects_wrong_runtime(monkeypatch):
    import httpx

    from tompathy_engine.preview.clef import Clef

    config = {"url": "http://127.0.0.1:9000", "model": "Cloudflare/clef-flash",
              "revision": "software-fixture", "sha256": "a" * 64,
              "token": "b" * 64, "identity": "c" * 64}
    backend = Clef(config)
    assert backend.identity == Clef({**config, "url": "http://127.0.0.1:9001", "token": "d" * 64}).identity
    assert backend.identity != Clef({**config, "identity": "e" * 64}).identity
    original = httpx.AsyncClient
    def response(request):
        assert request.headers["Authorization"] == "Bearer " + "b" * 64
        return httpx.Response(200, json={"runtime": {"identity": "e" * 64}})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(response), **kwargs))
    with pytest.raises(ValueError, match="runtime identity"):
        backend.decide({}, {}, lambda: None)
    with pytest.raises(ValueError, match="256-bit"):
        Clef({**config, "token": "invalid"})


def test_offline_transport_budget_does_not_change_fixed_model_settings():
    from tompathy_engine.preview.fixed_backend import FixedQwen

    live = FixedQwen("http://127.0.0.1:9000")
    offline = FixedQwen("http://127.0.0.1:9000", timeout=300)
    assert live.timeout == 110 and offline.timeout == 300
    assert live.model_id == offline.model_id and live.settings == offline.settings
    with pytest.raises(ValueError, match="timeout"):
        FixedQwen("http://127.0.0.1:9000", timeout=601)


def test_offline_preparation_cache_loads_under_normal_live_budget(tmp_path, monkeypatch):
    import time

    from fastapi.testclient import TestClient

    from tompathy_engine.preview import build
    from tompathy_engine.serve.app import create_app

    observed = []
    original = build.build_preview
    def recording(*args, **kwargs):
        observed.append(kwargs["deadline"] - time.monotonic())
        return original(*args, **kwargs)
    monkeypatch.setattr(build, "build_preview", recording)
    headers = {"Authorization": "Bearer " + "b" * 64}
    request = {"requestId": "prepare", "artifact": capture(), "scope": "artifact", "mode": "preview"}
    with TestClient(create_app(token="b" * 64, preview_cache=tmp_path, preview_budget=600), base_url="http://127.0.0.1") as client:
        prepared = client.post("/v1/analyze", json=request, headers=headers)
        assert prepared.status_code == 200 and 590 < observed[0] <= 600
    with TestClient(create_app(token="b" * 64, preview_cache=tmp_path), base_url="http://127.0.0.1") as client:
        cached = client.post("/v1/analyze", json={**request, "requestId": "cached", "preferCache": True}, headers=headers)
        assert cached.status_code == 200 and cached.json()["preview"]["cachedAt"]
        assert len(observed) == 1  # No inference or rerender needed to load.
        assert client.post("/v1/analyze", json={**request, "previewBudget": 600}, headers=headers).status_code == 422
    with pytest.raises(ValueError, match="budget"):
        create_app(token="b" * 64, preview_budget=601)


def test_cached_agreement_progress_batches_without_dropping_rows(monkeypatch):
    from types import SimpleNamespace

    from tompathy_engine.preview import build, surface

    packet = build_preview(build_packet(capture()))
    received = []
    def rows(*args, **kwargs):
        yield from ({"complete": True} for _ in packet["artifact"]["regions"])
    def compare(artifact, tables):
        received.extend(len(table) for condition in tables.values() for table in condition)
        return {}  # Only scheduler control flow is under test here.
    monkeypatch.setattr(surface, "score_regions", rows)
    monkeypatch.setattr(surface, "agreement_from_tables", compare)
    monkeypatch.setattr(build, "monotonic", lambda: 0.)
    readers = [SimpleNamespace(identity={"fixture": i}) for i in range(2)]
    assert len(list(build.agreement_steps(packet, readers, lambda: None, lambda: None))) == 0
    assert received == [3, 3, 3, 3]
    assert next(m for m in packet["preview"]["modules"] if m["id"] == "agreement")["completed"] == 12


def test_fast_departure_replay_coalesces_but_finishes_with_identical_scores(monkeypatch):
    from tompathy_engine.preview import build

    class Reader:
        identity: ClassVar = {"id": "fixture", "revision": "fixture", "sha256": "a" * 64, "backend": "constructed software test"}
        def score(self, text, context, check):
            return [{"start": i, "end": i + 1, "nats": float(1 + i % 5)} for i in range(len(text))]
    direct = build_preview(build_packet(capture()))
    replay = deepcopy(direct)
    build.deviation(direct, Reader(), lambda: None)
    renders = []
    original = build.render_deviation
    def record(packet, reader, result, covered):
        renders.append(list(covered))
        return original(packet, reader, result, covered)
    monkeypatch.setattr(build, "render_deviation", record)
    monkeypatch.setattr(build, "monotonic", lambda: 0.)
    list(build.deviation_steps(replay, Reader(), lambda: None, lambda: None))
    assert len(renders) == 2 and len(renders[-1]) == 3
    assert replay["hypotheses"] == direct["hypotheses"]
    assert replay["currentAttention"] == direct["currentAttention"]
    assert replay["preview"]["statistics"] == direct["preview"]["statistics"]
    Packet.model_validate(replay)


def test_timeout_rollback_keeps_shared_attention_items_in_their_source_regions():
    from tompathy_engine.preview.build import BudgetExceeded

    expected = []
    @stepped
    def seed(packet, check, publish):
        frames = []
        for index, region in enumerate(packet["artifact"]["regions"][:2]):
            h = hypothesis(packet, ["shared-frame", index], "Constructed attention",
                           "Rollback fixture", kind="attention", regions=[region["id"]])
            # Partitioned frames can legitimately share the same item object.
            item = {"hypothesis": h["id"], "basis": "text-surface", "evidenceStatus": "unvalidated"}
            for start, end in ([(0, 5), (5, 10)] if index == 0 else [(0, 10)]):
                frames.append({"maker": h["makers"][0], "span": {"region": region["id"], "start": start, "end": end}, "items": [item]})
        packet["currentAttention"] = frames
        expected.extend(deepcopy(frames))
        publish()
        yield

    @stepped
    def interrupted(packet, check, publish):
        frames = packet["currentAttention"]
        # A new partition changes which positions alias the same item. Restoring
        # items in place by list position would corrupt the previous partition.
        packet["currentAttention"] = [
            {**frames[0], "span": {**frames[0]["span"], "end": 10}},
            {**frames[2], "span": {**frames[2]["span"], "end": 5}},
            {**frames[2], "span": {**frames[2]["span"], "start": 5}},
        ]
        Packet.model_validate(packet)
        raise BudgetExceeded()
        yield  # Keep the same suspended-generator interface as real modules.

    partials = []
    packet = build_preview(build_packet(capture()), goal_runner=seed,
                           technique_runner=interrupted, partial=partials.append)
    for frame in expected:
        for item in frame["items"]:
            item["entry"] = "page"
    assert packet["currentAttention"] == expected
    assert next(m for m in packet["preview"]["modules"] if m["id"] == "techniques")["status"] == "skipped"
    assert all(Packet.model_validate(p) for p in partials)
