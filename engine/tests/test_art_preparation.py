"""Offline completion must not mistake a cached partial reading for readiness."""
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.preview import build
from tompathy_engine.serve.app import create_app

spec = importlib.util.spec_from_file_location("art_preparation", Path(__file__).resolve().parents[2] / "scripts/engine-art-refresh.py")
preparation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparation)


@pytest.mark.parametrize("second_status", ["complete", "failed"])
def test_preparation_continues_partial_cache_and_only_finishes_usable_modules(tmp_path, monkeypatch, second_status):
    calls, reports = [], []
    original = build.build_preview
    def staged(*args, **kwargs):
        packet = original(*args, **kwargs)
        calls.append(1)
        module = next(m for m in packet["preview"]["modules"] if m["id"] == "habits")
        module["status"] = "skipped" if len(calls) == 1 else second_status
        packet["preview"]["resumable"] = len(calls) == 1
        return packet
    monkeypatch.setattr(build, "build_preview", staged)
    artifact = make_capture(["A constructed preparation test."], "https://example.org/art", "Fixture", "2026-10-18T00:00:00Z")
    headers = {"Authorization": "Bearer " + "b" * 64}
    body = {"requestId": "prepare", "artifact": artifact, "scope": "artifact", "mode": "preview"}
    with TestClient(create_app(token="b" * 64, preview_cache=tmp_path), base_url="http://127.0.0.1") as client:
        if second_status == "failed":
            with pytest.raises(RuntimeError, match="modules failed"):
                preparation.finish_cached_preview(client, body, headers, lambda: None, lambda packet, attempt: reports.append(attempt))
        else:
            saved, attempts = preparation.finish_cached_preview(client, body, headers, lambda: None, lambda packet, attempt: reports.append(attempt))
            assert attempts == 2
            assert all(m["status"] in {"complete", "unavailable"} for m in saved["preview"]["modules"])
        assert calls == [1, 1] and reports == [1, 2]
        # Partial and failed outputs remain inspectable; cache replay adds no work.
        cached = client.post("/v1/analyze", headers=headers, json=body | {"requestId": "inspect", "preferCache": True})
        assert cached.status_code == 200 and cached.json()["preview"]["cachedAt"]


def test_preparation_checks_stop_before_starting_another_pass():
    class Client:
        def post(self, *args, **kwargs):
            raise AssertionError("No request may start after stop")
    def stopped():
        raise RuntimeError("Owner stop")
    with pytest.raises(RuntimeError, match="Owner stop"):
        preparation.finish_cached_preview(Client(), {}, {}, stopped, lambda *args: None)


@pytest.mark.parametrize("offline,deadline,expected", [(False, 600, "skipped"), (True, 600, "complete"), (True, 100, "skipped")])
def test_long_cpu_call_can_finish_offline_but_live_and_overall_bounds_remain(monkeypatch, offline, deadline, expected):
    from tompathy_engine.packet.build import build_packet
    clock = [0.0]
    monkeypatch.setattr(build, "monotonic", lambda: clock[0])
    def slow_goal(packet, check, publish):
        check()
        clock[0] += 170  # Measured art-group scale, without sleeping/model calls.
        check()
    capture = make_capture(["A constructed slow call."], "https://example.org/art", "Fixture", "2026-10-18T00:00:00Z")
    result = build.build_preview(build_packet(capture), goal_runner=slow_goal, deadline=deadline, preparation=offline)
    assert next(m for m in result["preview"]["modules"] if m["id"] == "goals")["status"] == expected
    if offline:
        assert result["preview"]["budgetDrops"] == []


def test_offline_stage_mode_is_internal_and_replays_in_normal_practice(tmp_path, monkeypatch):
    seen = []
    original = build.build_preview
    def observed(*args, **kwargs):
        seen.append(kwargs["preparation"])
        return original(*args, **kwargs)
    monkeypatch.setattr(build, "build_preview", observed)
    artifact = make_capture(["A constructed offline request."], "https://example.org/art", "Fixture", "2026-10-18T00:00:00Z")
    body = {"requestId": "offline", "artifact": artifact, "scope": "artifact", "mode": "preview"}
    headers = {"Authorization": "Bearer " + "b" * 64}
    with TestClient(create_app(token="b" * 64, preview_cache=tmp_path, preview_budget=600, preview_preparation=True), base_url="http://127.0.0.1") as client:
        result = client.post("/v1/analyze", headers=headers, json=body)
        assert result.status_code == 200 and seen == [True]
    with TestClient(create_app(token="b" * 64, preview_cache=tmp_path), base_url="http://127.0.0.1") as client:
        result = client.post("/v1/analyze", headers=headers, json=body | {"requestId": "replay", "preferCache": True})
        assert result.status_code == 200 and result.json()["preview"]["cachedAt"] and seen == [True]
        assert client.post("/v1/analyze", headers=headers, json=body | {"previewPreparation": True}).status_code == 422
    with pytest.raises(ValueError, match="boolean"):
        create_app(token="b" * 64, preview_preparation="true")


@pytest.mark.parametrize("reason,thinking", [("length", ""), ("stop", "private thinking")])
def test_rejected_completion_reports_only_metadata(monkeypatch, reason, thinking):
    import httpx

    from tompathy_engine.preview.fixed_backend import FixedQwen
    backend = FixedQwen("http://127.0.0.1:9999")
    monkeypatch.setattr(backend, "inspect", lambda client: True)
    async def generate(payload):
        return httpx.Response(200, request=httpx.Request("POST", "http://127.0.0.1:9999/api/generate"),
            json={"done": True, "done_reason": reason, "thinking": thinking, "prompt_eval_count": 100,
                  "eval_count": 256, "response": "private generated text"})
    monkeypatch.setattr(backend, "generate", generate)
    with pytest.raises(ValueError, match="unfinished") as caught:
        backend.complete("Constructed fixture", {})
    assert f"done_reason={reason}" in str(caught.value) and "output_tokens=256" in str(caught.value)
    assert "private" not in str(caught.value) and backend.metrics["calls"] == 0
