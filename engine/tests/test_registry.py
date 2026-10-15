import json
from copy import deepcopy

import pytest

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.ledger.ids import text_hash
from tompathy_engine.packet.build import build_packet
from tompathy_engine.registry.publish import publish


def packet(text="First revision."):
    return build_packet(
        make_capture([text], "https://example.org/writing", "Test", "2026-01-01T00:00:00Z"),
        origin="synthetic example",
    )


def test_index_buckets_exact_revisions_and_immutable_packets(tmp_path):
    first, second = packet(), packet("Second revision.")
    publish([first], tmp_path)
    publish([second], tmp_path)
    key = text_hash(first["artifact"]["id"])
    rows = json.loads((tmp_path / "index" / (key[:4] + ".json")).read_text())
    assert rows[0]["artifact_id_hash"] == key
    assert set(rows[0]["revisions"]) == {
        first["artifact"]["revision"],
        second["artifact"]["revision"],
    }
    assert publish([first], tmp_path)["action"] == "local-files-only"
    changed = deepcopy(first)
    changed["provider"]["method"] = "Changed analysis"
    with pytest.raises(ValueError, match="already occupies"):
        publish([changed], tmp_path)


def test_registry_refuses_context_and_private_sources(tmp_path):
    p = packet()
    p["scope"] = {"kind": "context", "contextIds": ["secret"]}
    with pytest.raises(ValueError, match="Context-conditioned"):
        publish([p], tmp_path)
    p = build_packet(
        make_capture(
            ["Internal fixture"], "coauthor:session:synthetic", "Test", "2026-01-01T00:00:00Z"
        )
    )
    with pytest.raises(ValueError, match="Private"):
        publish([p], tmp_path)
    assert publish([p], tmp_path, private=True)["private"]
