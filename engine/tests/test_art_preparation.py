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
