import json
from copy import deepcopy

import pytest

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet


def capture():
    return make_capture(
        ["A careful choice. 🌞", "Danger is the topic, not a measured motive."],
        "https://example.org/constructed",
        "Constructed fixture",
        "2026-01-01T00:00:00Z",
    )


def test_t0_no_invented_values_attention_or_history():
    source = capture()
    packet = build_packet(source, origin="synthetic example")
    assert packet["artifact"] == source
    assert packet["hypotheses"] == []
    assert packet["process"]["nodes"] == []
    assert "currentAttention" not in packet
    assert "population" not in packet
    assert packet["provider"]["admissions"] == []
    assert Packet.model_validate(packet).wire() == packet


def test_only_selected_context_and_scope_survive():
    items = [
        {
            "id": "a",
            "source": "fixture:context",
            "excerpt": "One observation",
            "retrievedAt": "2026-01-01T00:00:00Z",
            "selected": True,
        },
        {
            "id": "b",
            "source": "fixture:unselected",
            "excerpt": "Must not enter",
            "retrievedAt": "2026-01-01T00:00:00Z",
            "selected": False,
        },
    ]
    packet = build_packet(capture(), scope="context", context=items)
    assert packet["scope"]["contextIds"] == ["a"]
    assert "Must not enter" not in json.dumps(packet)
    plain = build_packet(capture(), context=items)
    assert "One observation" not in json.dumps(plain)


def test_mirror_rejects_bad_capture_and_dangling_evidence():
    packet = build_packet(capture())
    bad = deepcopy(packet)
    bad["artifact"]["revision"] = "wrong"
    with pytest.raises(ValueError):
        Packet.model_validate(bad)
    bad = deepcopy(packet)
    bad["hypotheses"] = [
        {
            "id": "h",
            "kind": "value",
            "label": "Unlicensed",
            "description": "",
            "makers": [packet["makers"][0]["id"]],
            "regions": [],
            "status": "hypothesis",
            "evidence": ["missing"],
        }
    ]
    with pytest.raises(ValueError, match="Unresolved"):
        Packet.model_validate(bad)


def test_emit_packet_for_authoritative_node_parity(tmp_path):
    # CI validates generated outputs as well as the checked-in packet fixture.
    packet = build_packet(capture(), origin="synthetic example")
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(packet), encoding="utf8")
    assert Packet.model_validate_json(path.read_text()).wire() == packet
