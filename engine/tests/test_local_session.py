import json

import httpx
import pytest

from tompathy_engine.transcribe.backends import local


def setup(monkeypatch, tmp_path, *, occupied=False, filled=False, unload_fails=False, gpu=False):
    state = {"resident": occupied, "calls": [], "unloads": 0}
    def handler(request):
        path = request.url.path
        if path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "m", "digest": "pin"}]})
        if path == "/api/ps":
            if state.get("unknown"):
                return httpx.Response(200, json={})
            return httpx.Response(200, json={"models": [{"name": "m", "digest": "pin", "size_vram": 0}] if state["resident"] else []})
        body = json.loads(request.content)
        if "prompt" not in body:
            state["unloads"] += 1
            state["resident"] = unload_fails
            return httpx.Response(200, json={"done": True})
        state["calls"].append(body)
        state["resident"] = bool(body["keep_alive"])
        return httpx.Response(200, json={"done": True, "response": '{"answer":"yes"}', "prompt_eval_count": 8000 if filled else 20})
    client = httpx.Client
    monkeypatch.setattr(local.httpx, "Client", lambda **kw: client(transport=httpx.MockTransport(handler), **kw))
    backend = local.LocalBackend(url="http://127.0.0.1:19873", model="m", model_digest="pin", num_thread=2, gpu=gpu, gpu_lock=tmp_path / "gpu.lock")
    backend._lock = tmp_path / "endpoint.lock"
    return backend, state


def test_warm_session_pin_and_release(monkeypatch, tmp_path):
    backend, state = setup(monkeypatch, tmp_path, gpu=True)
    with backend.session():
        for _ in range(2):
            backend.complete("text", {})
            assert (tmp_path / "gpu.lock").exists() and state["unloads"] == 0
    assert state["unloads"] == 1 and not backend._lock.exists() and not (tmp_path / "gpu.lock").exists()
    assert all(body["options"]["num_ctx"] == 8192 and body["options"]["num_thread"] == 2 for body in state["calls"])
    assert backend.settings["keep_alive"] == 120


def test_foreign_model_not_evicted(monkeypatch, tmp_path):
    backend, state = setup(monkeypatch, tmp_path, occupied=True)
    with pytest.raises(RuntimeError, match="unowned"):
        backend.complete("text", {})
    assert state["unloads"] == 0 and not state["calls"] and not backend._lock.exists()


def test_context_refused_before_and_after_call(monkeypatch, tmp_path):
    backend, state = setup(monkeypatch, tmp_path, filled=True)
    with pytest.raises(ValueError, match="context"):
        backend.complete("x" * 24577, {})
    assert not state["calls"]
    with pytest.raises(ValueError, match="truncated"):
        backend.complete("small", {})
    assert not state["resident"] and not backend._lock.exists()


def test_uncertain_unload_retains_gpu_lease(monkeypatch, tmp_path):
    backend, _ = setup(monkeypatch, tmp_path, unload_fails=True, gpu=True)
    with pytest.raises(RuntimeError, match="unverified"):
        backend.complete("small", {})
    assert backend._lock.exists() and (tmp_path / "gpu.lock").exists()


def test_missing_residency_metadata_never_confirms_unload(monkeypatch, tmp_path):
    backend, state = setup(monkeypatch, tmp_path, gpu=True)
    with pytest.raises(RuntimeError, match="unknown"), backend.session():
        backend.complete("small", {})
        state["unknown"] = True
    assert backend._lock.exists() and (tmp_path / "gpu.lock").exists()
