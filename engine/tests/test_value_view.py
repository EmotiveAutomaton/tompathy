import copy

import pytest

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.packet.value_view import WorkValueView, build_value_view
from tompathy_engine.preview.build import build_preview


def packet():
    capture = make_capture(["An ordinary final paragraph."], "https://example.org/fixture", "Constructed view", "2026-10-18T00:00:00Z")
    return build_packet(capture)


def test_final_text_is_hollow_and_preview_does_not_recover_drive_tips():
    result = packet()
    assert result["schemaVersion"] == "1.10"
    assert result["valueView"]["evidenceTier"] == "T0"
    assert len(result["valueView"]["rows"]) == 1
    assert not result["valueView"]["tips"]
    preview = build_preview(result)
    assert preview["valueView"]["provenance"] == "structure-only"
    assert not preview["valueView"]["feeds"]
    Packet.model_validate(preview)


def test_recorded_history_rows_without_inferred_tips():
    result = packet()
    result["provider"]["mode"] = "preview"
    view = build_value_view(result, history={"revisions": [{"id":"constructed-1", "t":"2026-10-17T12:00:00Z"}, {"id":"constructed-2", "t":"2026-10-18T12:00:00Z"}]})
    assert view["evidenceTier"] == "production" and len(view["rows"]) == 2
    assert not view["tips"] and not view["coSupport"]
    assert view["firstMissingLink"].startswith("No admitted comparison")
    WorkValueView.model_validate(view)


def test_forged_tips_and_unresolved_rows_fail_closed():
    result = packet()
    original = copy.deepcopy(result)
    result["valueView"]["rows"][0]["region"] = "not-here"
    with pytest.raises(ValueError, match="row source"):
        Packet.model_validate(result)
    view = original["valueView"]
    view["tips"] = [{"id":"forged", "label":"CARE", "support":1, "interval":[.5,1.5], "status":"drawn", "hypothesis":"forged"}]
    with pytest.raises(ValueError, match="Structure-only"):
        WorkValueView.model_validate(view)
    view.update(evidenceTier="production", provenance="admitted")
    with pytest.raises(ValueError, match="admitted contrast"):
        Packet.model_validate(original)
