import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.ledger.ids import canonical
from tompathy_engine.serve.app import create_app, load_token

TOKEN = "a" * 64
ORIGIN = "chrome-extension://" + "b" * 32
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Origin": ORIGIN, "Content-Type": "application/json"}


def body(request_id="fixture"):
    return {
        "requestId": request_id,
        "scope": "artifact",
        "context": [],
        "artifact": make_capture(
            ["🌞" + "a" * 77, "Next"], "https://example.org", "Fixture", "2026-01-01T00:00:00Z"
        ),
    }


def test_auth_origin_and_exact_packet():
    with TestClient(
        create_app(token=TOKEN, origins=[ORIGIN]), base_url="http://127.0.0.1"
    ) as client:
        assert client.get("/v1/health").status_code == 401
        assert (
            client.get(
                "/v1/health", headers=HEADERS | {"Origin": "https://other.example"}
            ).status_code
            == 403
        )
        response = client.get("/v1/health", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["admittedModules"] == []
        assert response.headers["access-control-allow-origin"] == ORIGIN
        response = client.post("/v1/analyze", headers=HEADERS, content=canonical(body()))
        assert response.status_code == 200
        assert response.json()["artifact"] == body()["artifact"]
        assert response.headers["cache-control"] == "no-store"
        assert (
            client.post("/v1/analyze", headers=HEADERS, content=canonical(body())).status_code
            == 409
        )


def test_streaming_and_request_bound():
    with TestClient(
        create_app(token=TOKEN, origins=[ORIGIN]), base_url="http://127.0.0.1"
    ) as client:
        response = client.post(
            "/v1/analyze",
            headers=HEADERS | {"Accept": "text/event-stream"},
            content=canonical(body()),
        )
        assert response.status_code == 200
        assert "event: packet\n" in response.text
        assert "text/event-stream" in response.headers["content-type"]
        response = client.post(
            "/v1/analyze",
            headers=HEADERS | {"Content-Type": "application/json"},
            content=b" " * 2_000_001,
        )
        assert response.status_code == 413


def test_cancellation_interrupts_worker_and_releases_slot():
    def slow_builder(request, job):
        for _ in range(200):
            job.progress("Fixture work")
            time.sleep(0.01)
        raise AssertionError("Cancellation did not reach the worker")

    with (
        TestClient(
            create_app(token=TOKEN, origins=[ORIGIN], builder=slow_builder),
            base_url="http://127.0.0.1",
        ) as client,
        ThreadPoolExecutor(max_workers=1) as worker,
    ):
        future = worker.submit(
            client.post, "/v1/analyze", headers=HEADERS, content=canonical(body())
        )
        for _ in range(100):
            result = client.delete("/v1/analyze/fixture", headers=HEADERS)
            if result.status_code == 200:
                break
            time.sleep(0.01)
        assert result.status_code == 200
        assert future.result(timeout=3).status_code == 409


def test_session_token_persists_and_is_not_in_health(tmp_path):
    path = tmp_path / "token"
    token = load_token(path)
    assert len(token) == 64 and load_token(path) == token
    with TestClient(create_app(token=token), base_url="http://127.0.0.1") as client:
        response = client.get("/v1/health", headers={"Authorization": f"Bearer {token}"})
        assert token not in response.text
