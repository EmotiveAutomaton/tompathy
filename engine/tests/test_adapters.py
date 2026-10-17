from datetime import UTC, datetime

import httpx
import pytest

from tompathy_engine.adapters.git import ingest as git_ingest
from tompathy_engine.adapters.history import apply_hunks, diff_hunks
from tompathy_engine.adapters.lichess import ingest as chess_ingest
from tompathy_engine.adapters.panel import ingest as panel_ingest
from tompathy_engine.adapters.wiki import fetch_history, revert_outcomes
from tompathy_engine.adapters.wiki import ingest as wiki_ingest
from tompathy_engine.ledger.store import Ledger


def history():
    return {
        "artifact_id": "fixture-history",
        "source_uri": "https://example.org/essay",
        "license": "CC-BY-4.0",
        "license_evidence": "Constructed fixture permission",
        "revisions": [
            {
                "id": "one",
                "maker": "same@example.org",
                "label": "A",
                "t": "2026-01-01T00:00:00Z",
                "text": "A 😀 line.\r\n",
                "summary": "Initial",
            },
            {
                "id": "two",
                "parents": ["one"],
                "maker": "same@example.org",
                "label": "A",
                "t": "2026-01-02T00:00:00Z",
                "text": "A 😀 clearer line.\n",
                "summary": "Clarify",
            },
        ],
    }


def test_git_reconstruction_and_idempotence(tmp_path):
    data = history()
    ledger = Ledger(tmp_path)
    receipt = git_ingest(data, ledger)
    assert receipt["revisions"] == 2 and receipt["corrections"] > 0
    assert not ledger.rows("Decision")
    assert len(ledger.rows("StatedGoal")) == 2
    git_ingest(data, ledger)
    assert len(ledger.rows("Revision")) == 2
    data["license"] = "Unknown"
    with pytest.raises(ValueError, match="license"):
        git_ingest(data, ledger)
    for before, after in [("😀\r\nx", "😀 changed\nx"), ("x\n" * 10000, "x\n" * 9999 + "end")]:
        assert apply_hunks(before, diff_hunks(before, after)) == after


def test_wiki_boundaries_identity_summary_and_censoring(tmp_path):
    data = history()
    data["revisions"][0]["parents"] = ["outside-window"]
    data["revisions"][0]["unstable_identity"] = True
    data["revisions"][1]["maker"] = "different-id"
    receipt = wiki_ingest(data, Ledger(tmp_path))
    assert receipt["revert_proxy"] == {"one": None, "two": None}
    data["revisions"].append(
        {
            "id": "three",
            "maker": "c",
            "parents": ["two"],
            "t": "2026-01-02T01:00:00Z",
            "text": data["revisions"][0]["text"],
        }
    )
    assert revert_outcomes(data["revisions"])["two"]["reverted_within_48h"] is True
    assert len(receipt["summary_coverage"]) == 2


def test_wiki_api_contract_refuses_suppressed_and_private_urls():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "query": {
                    "pages": [
                        {
                            "revisions": [
                                {
                                    "revid": 2,
                                    "parentid": 1,
                                    "userid": 7,
                                    "user": "Editor",
                                    "timestamp": "2026-01-02T00:00:00Z",
                                    "comment": "clarify",
                                    "slots": {"main": {"content": "Observed text"}},
                                }
                            ]
                        }
                    ]
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        data = fetch_history(
            "https://en.wikipedia.org/wiki/Empathy", artifact_id="capture-id", client=client
        )
        assert data["revisions"][0]["text"] == "Observed text"
        assert data["revisions"][0]["bot"] == "unknown"
        assert calls[0].url.params["rvslots"] == "main"
        for url in [
            "http://en.wikipedia.org/wiki/Empathy",
            "https://en.wikipedia.org.evil.test/wiki/Empathy",
            "https://127.0.0.1/wiki/Test",
        ]:
            with pytest.raises(ValueError):
                fetch_history(url, artifact_id="id", client=client)


def test_panel_preserves_ties_and_missing_times_as_exclusions(tmp_path):
    payload = {
        "dataset": "dices",
        "source_uri": "https://example.org/fixture",
        "source_sha256": "a" * 64,
        "codebook": "Constructed field map, no real respondents",
        "expected_rows": 3,
        "rows": [
            {
                "id": "one",
                "maker": "m",
                "options": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}],
                "taken": "a",
                "t_open": "2026-01-01T00:00:00Z",
                "t_resolve": "2026-01-01T00:01:00Z",
            },
            {"id": "two", "maker": "m", "taken": "a"},
            {
                "id": "three",
                "maker": "m",
                "tie": True,
                "t_open": "2026-01-01T00:00:00Z",
                "t_resolve": "2026-01-01T00:01:00Z",
            },
        ],
    }
    result = panel_ingest(payload, Ledger(tmp_path))
    assert result["usable_decisions"] == 1
    assert result["excluded"] == {"missing_chronology": 1, "unresolved_or_tie": 1}
    assert result["depth_histogram"] == {1: 1}
    payload["expected_rows"] = 4
    with pytest.raises(ValueError, match="row count"):
        panel_ingest(payload, Ledger(tmp_path))


def test_lichess_legal_moves_and_clock_deltas(tmp_path):
    pgn = """[Event "Constructed clock fixture"]
[Site "https://lichess.org/fixture"]
[White "WhiteFixture"]
[Black "BlackFixture"]
[Result "*"]
[UTCDate "2026.01.01"]
[UTCTime "00:00:00"]
[TimeControl "60+1"]

1. e4 { [%clk 0:00:59] } e5 { [%clk 0:00:58] } 2. Nf3 { [%clk 0:00:57] } *
"""
    ledger = Ledger(tmp_path)
    result = chess_ingest(pgn, ledger)
    rows = sorted(ledger.rows("Decision"), key=lambda r: r.context["ply"])
    assert result["moves"] == 3 and len(rows[0].options) == 20
    assert [r.cost.latency_s for r in rows] == [2, 3, 3]
    assert rows[-1].t_resolve == datetime(2026, 1, 1, 0, 0, 8, tzinfo=UTC)
    assert "post_move_engine_score" not in rows[0].context
    assert (
        chess_ingest(pgn.replace("{ [%clk 0:00:59] }", ""), Ledger(tmp_path / "missing"))["moves"]
        == 0
    )
