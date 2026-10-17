from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from test_admission import record
from test_pipeline import corrected, gates

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.admission import Admissions, implementation_hash
from tompathy_engine.eval.pipeline import evaluate
from tompathy_engine.ledger.ids import digest
from tompathy_engine.models.goals import GoalInputs
from tompathy_engine.models.pipeline import fit_pipeline
from tompathy_engine.models.source_trust import SourceObservation, trajectory
from tompathy_engine.packet.build import build_packet
from tompathy_engine.serve.app import create_app
from tompathy_engine.workflow import analyze_history


def test_goals_need_separate_producer_pin_and_exact_inputs():
    capture = make_capture(
        ["A stated example."], "https://example.org/goals", "Goals", "2026-02-01T00:00:00Z"
    )
    maker = digest(["capture-maker", capture["id"]])
    pin = digest("constructed-goal-producer")
    goal = GoalInputs(
        capture_hash=digest(capture),
        root_cues_hash=digest([]),
        generator_pin=pin,
        candidates=[
            {
                "id": "candidate",
                "maker": maker,
                "label": "Explain the example",
                "description": "Constructed explanatory goal.",
                "regions": [capture["regions"][0]["id"]],
                "depth": 1,
                "support": 0.6,
            }
        ],
    )
    assert "goalHierarchy" not in build_packet(capture, goals=goal)
    admissions = Admissions(
        [
            record(module=m, model_pin=pin, implementation_hash=implementation_hash())
            for m in ("goal-candidates", "goal-tree")
        ]
    )
    packet = build_packet(capture, goals=goal, admissions=admissions)
    assert packet["goalHierarchy"]["nodes"]
    assert packet["hypotheses"][0]["interpretation"] == "governing-purpose"
    assert packet["process"]["nodes"] == []
    assert "currentAttention" not in packet
    goal.generator_pin = "f" * 64
    with pytest.raises(ValueError, match="model pin"):
        build_packet(capture, goals=goal, admissions=admissions)


def test_attention_uses_exact_location_and_does_not_invent_t0(tmp_path):
    ledger, capture, labels, until = corrected(tmp_path)
    # Preserve the artifact identity while supplying a new exact capture.
    viewed = make_capture(
        ["Short."], capture["source"], "Exact surviving text", capture["capturedAt"]
    )
    assert viewed["id"] == capture["id"]
    model = fit_pipeline(ledger, population="writing-v0", until=until, labels=labels)
    packet = build_packet(
        viewed, ledger=ledger, model=model, admissions=gates("attention", "habits")
    )
    assert packet["currentAttention"]
    assert all(h["label"] == "Where edits concentrated" for h in packet["hypotheses"] if h["kind"] == "attention")
    assert "currentAttention" not in build_packet(viewed, admissions=gates("attention"))


def test_module_evaluation_is_chronological_and_maker_held_out(tmp_path):
    ledger, _, labels, _ = corrected(tmp_path)
    until = datetime(2026, 1, 1, 0, 3, tzinfo=UTC)
    rows, receipt = evaluate(
        ledger,
        domain="writing",
        until=until,
        labels=labels,
        modules=("backbone", "corrections", "joint", "prototypes", "correction-augmented"),
        heldout_makers=["short"],
    )
    assert receipt["decisions"] == 3 and len(rows) == 15
    assert all("short" not in r["training_makers"] for r in rows)
    assert all(r["training_latest"] is None or r["training_latest"] < r["opened"] for r in rows)
    assert all(abs(sum(r["probabilities"]) - 1) < 1e-10 for r in rows)
    assert rows[0]["probabilities"] == [0.5, 0.5]
    with pytest.raises(ValueError, match="limit"):
        evaluate(ledger, domain="writing", until=until, maximum_targets=1)


def test_source_prediction_does_not_see_overlapping_or_simultaneous_outcomes():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        SourceObservation("a", "s", t + timedelta(seconds=10), True, opened=t),
        SourceObservation(
            "b", "s", t + timedelta(seconds=20), False, opened=t + timedelta(seconds=5)
        ),
        SourceObservation(
            "c", "s", t + timedelta(seconds=30), True, opened=t + timedelta(seconds=20)
        ),
    ]
    points = trajectory(rows, until=t + timedelta(minutes=1))
    assert points[0]["acceptance_propensity"] == 0.5
    assert points[1]["acceptance_propensity"] == 0.5
    assert (
        points[2]["acceptance_propensity"] > 0.5
    )  # a resolved; b exactly simultaneous is excluded.


def test_history_snapshots_cancel_and_service_opt_in(tmp_path):
    capture = make_capture(
        ["The new text."],
        "https://en.wikipedia.org/wiki/Example",
        "Example",
        "2026-02-01T00:00:00Z",
    )
    payload = {
        "artifact_id": capture["id"],
        "source_uri": capture["source"],
        "license": "CC-BY-SA-4.0",
        "license_evidence": "constructed source",
        "revisions": [
            {"id": "1", "maker": "a", "t": "2026-01-01T00:00:00Z", "text": "The old text."},
            {
                "id": "2",
                "parents": ["1"],
                "maker": "a",
                "t": "2026-01-02T00:00:00Z",
                "text": "The new text.",
            },
        ],
    }
    packet, receipt = analyze_history(
        capture, directory=tmp_path, admissions=Admissions(), payload=payload
    )
    assert receipt["corrections"] and not receipt["fit_created"]
    assert packet["process"]["nodes"] and not packet["provider"]["admissions"]
    _, again = analyze_history(
        capture, directory=tmp_path, admissions=Admissions(), payload=payload
    )
    assert again["snapshot"] == receipt["snapshot"]
    with pytest.raises(InterruptedError):
        analyze_history(
            capture,
            directory=tmp_path,
            admissions=Admissions(),
            payload=payload,
            cancel=lambda: True,
        )
    token = "d" * 64
    with TestClient(create_app(token=token), base_url="http://127.0.0.1") as client:
        response = client.post(
            "/v1/analyze",
            headers={"Authorization": "Bearer " + token},
            json={
                "requestId": "history",
                "artifact": capture,
                "scope": "artifact",
                "history": "wikipedia",
            },
        )
        assert response.status_code == 422
        assert "disabled" in response.json()["detail"]


def test_history_runs_bound_transcription_fit_and_packet_without_overwriting(tmp_path):
    class Reader:
        pin = digest("constructed-history-reader")

        def __init__(self):
            self.admissions = {
                q: {
                    "question_id": q,
                    "transcriber_pin": self.pin,
                    "passed": True,
                    "status": "admitted",
                    "items": 200,
                    "valid_rate": 1.0,
                    "accuracy": 1.0,
                    "per_label": {"\"yes\"": 1.0, "\"no\"": 1.0},
                    "per_family": {"family-0": 1.0, "family-1": 1.0},
                    "best_constant": 0.5,
                    "battery_hash": digest(q),
                    "admission_id": "constructed-history-" + q,
                }
                for q in ("Q8", "Q9")
            }

        def ask(self, q, **kwargs):
            return {"answer": "wording" if q == "Q8" else "yes"}

    capture = make_capture(
        ["A long constructed sentence."],
        "https://en.wikipedia.org/wiki/Constructed",
        "Constructed",
        "2026-02-01T00:00:00Z",
    )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    revisions = []
    for trial in range(24):
        for maker in ("a", "b"):
            for actor, text in (
                ("reset", "Z" * 32),
                (maker, "A" * 60 if (maker == "a") != (trial % 5 == 0) else "B" * 5),
            ):
                i = len(revisions)
                revisions.append(
                    {
                        "id": str(i),
                        "parents": [str(i - 1)] if i else [],
                        "maker": actor,
                        "t": (start + timedelta(minutes=i)).isoformat(),
                        "text": text,
                    }
                )
    payload = {
        "artifact_id": capture["id"],
        "source_uri": capture["source"],
        "license": "CC0-1.0",
        "license_evidence": "Constructed original",
        "revisions": revisions,
    }
    packet, receipt = analyze_history(
        capture,
        directory=tmp_path,
        admissions=gates("corrections"),
        payload=payload,
        reader=Reader(),
    )
    assert receipt["fit_created"] and receipt["transcription_ran"]
    assert any(h["kind"] == "value" for h in packet["hypotheses"])
    again, second = analyze_history(
        capture,
        directory=tmp_path,
        admissions=gates("corrections"),
        payload=payload,
        reader=Reader(),
    )
    assert packet == again and receipt["run"] == second["run"]
