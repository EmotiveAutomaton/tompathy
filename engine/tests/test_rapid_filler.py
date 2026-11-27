"""G15 must select the original date halves and preserve each reused W response."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from rapid_filler_inputs import historic, select_by_date
from word_table_lane import core


def test_whole_authors_keep_two_seeded_halves_and_cli_knows_every_fresh_stage():
    rows = [{"id": str(i), "day": str(i // 6), "opening": str(i)} for i in range(24)]
    first = select_by_date(rows)
    assert first == select_by_date(list(reversed(rows)))
    assert len(first) == 20 and len({r["id"] for _, r in first}) == 20
    assert max(r["day"] for h, r in first if h == 0) < min(r["day"] for h, r in first if h == 1)
    assert select_by_date(rows[:15]) == []
    from rapid_next_cards import FILLER_INPUTS, SCALE_STAGES

    result = subprocess.check_output(
        [sys.executable, str(SCRIPTS / "rapid_cpu.py"), "--help"], text=True
    )
    assert all(stage in result for stage in (*FILLER_INPUTS, *SCALE_STAGES))


def test_reuse_checks_identity_and_raw_response():
    protocol = {"job": "G11", "prompt": "x", "schema": {}, "secondKey": None, "modelPin": "m"}
    row = {
        "index": 5,
        "id": "p",
        "binding": {"job": "G11", "modelPin": "m"},
        "response": {"response": json.dumps(dict.fromkeys(core.FEATURES, 3))},
        "values": [3] * 8,
    }
    assert historic(row, {"id": "p"}, protocol, 5) == [3] * 8
    with pytest.raises(ValueError):
        historic(row, {"id": "other"}, protocol, 5)
    with pytest.raises(ValueError):
        historic({**row, "values": [4] * 8}, {"id": "p"}, protocol, 5)


def test_gpu_roster_skips_historical_missing_and_preserves_order(tmp_path):
    from rapid_filler_gpu import compact, new_items
    from rapid_marks import digest

    texts = {digest(t): t for t in ("ok", "too long", "next")}
    roster = [
        {"id": "old", "ordinal": 0, "reuse": {"values": None}},
        *[{"id": str(i), "ordinal": 0, "opening": key} for i, key in enumerate(texts)],
    ]
    index, calls = new_items(roster, texts, "", {"num_ctx": 70, "num_predict": 1})
    assert index == [("historical", None), ("new", 0), ("context", None), ("new", 1)]
    assert [r["id"] for r in calls] == ["0", "2"]
    (tmp_path / "W").mkdir()
    (tmp_path / "W/from-000000.json").write_text(
        json.dumps([{"id": "0", "response": "[1]", "values": [1]}])
    )
    report = compact(tmp_path, roster, index, calls, lambda v: v)
    assert (
        report["availableRows"],
        report["newResponses"],
        report["valid"],
        report["wholeAuthors"],
    ) == (3, 1, 1, 0)
    with pytest.raises(ValueError):
        new_items(roster, dict.fromkeys(texts, "changed"), "", {"num_ctx": 70, "num_predict": 1})
