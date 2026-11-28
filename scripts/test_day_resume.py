"""Regression fixtures for the saved W prefix. No model is called."""

import json
from pathlib import Path

import pytest
from day_resume import scan


def test_preserves_invalid_replies_and_original_ordinals(tmp_path):
    items = [{"id": str(i)} for i in range(4)]
    for pos, response, value in [
        (1, "???", None),
        (2, '{"need":"body","change":"loss"}', {"need": "body", "change": "loss"}),
    ]:
        (tmp_path / f"from-{pos:06}.json").write_text(
            json.dumps([{"id": str(pos), "response": response, "values": value}])
        )
    proof = scan(tmp_path, items, "need", 1)
    assert (proof["nextOrdinal"], proof["valid"], len(proof["files"])) == (3, 1, 2)
    (tmp_path / "from-000002.json").rename(tmp_path / "from-000003.json")
    with pytest.raises(ValueError, match="gap"):
        scan(tmp_path, items, "need", 1)


def test_rejects_changed_stored_value(tmp_path: Path):
    (tmp_path / "from-000000.json").write_text(
        '[{"id":"x","response":"bad","values":{"need":"none","change":"neither"}}]'
    )
    with pytest.raises(ValueError, match="parsed"):
        scan(tmp_path, [{"id": "x"}], "need")
