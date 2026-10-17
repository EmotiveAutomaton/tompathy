"""Integration controls for the October 17 packet; no research admission."""
import json
from contextlib import nullcontext
from typing import ClassVar

import httpx
import pytest
from fastapi.testclient import TestClient
from test_admission import record

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.adapters.wiki import fetch_history, revert_outcomes, visible_text
from tompathy_engine.admission import Admissions
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import BudgetExceeded, build_preview
from tompathy_engine.preview.judgments import goals
from tompathy_engine.preview.makers import correction_steps
from tompathy_engine.preview.surface import score_regions, words
from tompathy_engine.serve.app import create_app
from tompathy_engine.transcribe.cache import Cache


def capture():
    return make_capture(["A garden grows.", "A train arrives.", "A ship leaves."],
                        "https://example.org/fixture", "Software fixture", "2026-10-17T00:00:00Z")


class GoalBackend:
    model_id = "software-test-only"
    settings: ClassVar = {"fixture": True}

    def checking(self, _):
        return nullcontext()

    def complete(self, prompt, schema):
        data = json.loads(prompt.split("\n", 1)[1])
        result = {"label": "Constructed candidate", "description": "Software fixture, not inference.", "support": .5, "cue_match": 0, "cue_ids": []}
        if "covered_ids" in schema["properties"]:
            result["covered_ids"] = [data["local_candidates"][0]["id"]]
        return {"text": json.dumps(result)}


def test_uncovered_goals_keep_separate_lenses_and_parity_fixture(tmp_path):
    result = build_preview(build_packet(capture()), goal_runner=goals(GoalBackend(), Cache(tmp_path / "goals.sqlite")))
    lenses = result["preview"]["goalLenses"]
    assert list(map(len, lenses)) == [2, 2]
    nodes = {n["id"]: n for n in result["goalHierarchy"]["nodes"]}
    assert all("parentId" not in nodes[ident] for ident in lenses[1])
    assert nodes[lenses[0][1]]["parentId"] == lenses[0][0]
    assert all(n["entry"] == "page" for n in nodes.values())
    assert result["preview"]["rootCueStatus"] == "assumed"
    assert len(result["globalFindings"]) == 5
    Packet.model_validate(result)


def test_budget_sheds_optional_stages_in_order_and_keeps_habits():
    def exhausted(packet, check, publish):
        raise BudgetExceeded()
    result = build_preview(build_packet(capture()), goal_runner=exhausted, technique_runner=exhausted)
    assert result["preview"]["budgetDrops"] == ["payoff-layer-2", "second-reader"]
    assert next(m for m in result["preview"]["modules"] if m["id"] == "habits")["status"] == "complete"


def test_shared_byte_spans_include_trailing_separators_and_partial_unicode():
    text = "café, 😀 arrives."
    tokens = [{"start": i, "end": i + 1, "nats": 1.} for i in range(len(text))]
    aligned = words(text, tokens)
    assert aligned[0]["byteEnd"] == len("café, 😀 ".encode())
    assert aligned[1]["byteStart"] == aligned[0]["byteEnd"]
    assert sum(w["nats"] for w in aligned) == len(text)

    class Partial:
        def score_chunks(self, text, previous, check):
            # Crosses the interior of the second word; must defer that word.
            yield [{"start": 0, "end": 11, "nats": 10.}], False
            yield [{"start": 0, "end": len(text), "nats": 15.}], True
    artifact = make_capture([text], "https://example.org/partial", "Partial", "2026-10-17T00:00:00Z")
    rows = list(score_regions(artifact, Partial()))
    assert [w["text"] for w in rows[0]["words"]] == ["café"]
    assert [w["text"] for w in rows[1]["words"]] == ["café", "arrives"]


def test_suppressed_revision_is_a_boundary_not_an_invented_diff():
    def revision(ident, parent, text):
        return {"revid": ident, "parentid": parent, "userid": 1, "user": "Fixture", "timestamp": f"2026-10-0{ident}T00:00:00Z", "slots": {"main": {"content": text}}}
    rows = [revision(3, 2, "A"), {"revid": 2, "parentid": 1, "userhidden": True}, revision(1, 0, "A")]
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"query": {"pages": [{"revisions": rows}]}}))) as client:
        data = fetch_history("https://en.wikipedia.org/wiki/Fixture", artifact_id="fixture", client=client)
    assert data["suppressedBoundaryIds"] == ["2"]
    assert data["revisions"][1]["parents"] == ["2"]
    assert revert_outcomes(data["revisions"]) == {"1": None, "3": None}
    assert visible_text("{{Hidden}} '''A''' [[Place|garden]] <ref>citation</ref> &amp; [[File:x.png|thumb|image]]") == "A garden &"


def test_retry_after_is_honored_once_and_long_wait_is_refused():
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(429, headers={"Retry-After": "0"}) if len(seen) == 1 else httpx.Response(200, json={"query": {"pages": [{"revisions": []}]}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        fetch_history("https://en.wikipedia.org/wiki/Fixture", artifact_id="fixture", client=client)
    assert len(seen) == 2
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(429, headers={"Retry-After": "120"}))) as client, pytest.raises(httpx.HTTPStatusError):
        fetch_history("https://en.wikipedia.org/wiki/Fixture", artifact_id="fixture", client=client)


def test_health_explains_refused_admission():
    gates = Admissions([record()], implementation="b" * 64)
    with TestClient(create_app(token="a" * 64, admissions=gates), base_url="http://127.0.0.1") as client:
        health = client.get("/v1/health", headers={"Authorization": "Bearer " + "a" * 64}).json()
    assert health["admittedModules"] == []
    assert "pin does not match" in health["refusedModules"]["corrections"]


def test_failed_correction_question_is_never_called():
    class FailedReader:
        admissions: ClassVar = {"Q8": {"passed": False}}
    with pytest.raises(ValueError, match="stays off"):
        list(correction_steps({}, {}, FailedReader(), lambda: None, lambda: None))
