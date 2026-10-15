from copy import deepcopy

import pytest

from tompathy_engine.adapters.capture import ingest, make_capture, normalize, validate_capture
from tompathy_engine.ledger.ids import canonical
from tompathy_engine.ledger.store import Ledger


def test_js_whitespace_and_surrogate_anchors():
    assert normalize("\ufeff a\u00a0b \u0085 ") == "a b \u0085"
    capture = make_capture(
        ["🌞\tday", "\ufeffnight\r\n sky"],
        "https://example.org/a#part",
        "Test",
        "2026-01-01T00:00:00Z",
    )
    assert capture["regions"][1]["anchor"]["start"] == 8
    assert capture["regions"][1]["anchor"]["prefix"] == "🌞 day\n\n"
    assert validate_capture(capture) == capture
    changed = deepcopy(capture)
    changed["regions"][1]["anchor"]["start"] -= 1
    with pytest.raises(ValueError, match="anchor"):
        validate_capture(changed)


def test_t0_creates_no_choices_attention_or_preferences(tmp_path):
    ledger = Ledger(tmp_path)
    capture = make_capture(
        ["Danger, fear and anger."], "https://example.org", "Danger", "2026-01-01T00:00:00Z"
    )
    result = ingest(capture, ledger)
    assert result["tier"] == "T0"
    assert ledger.rows("Decision") == []
    assert ledger.rows("StatedPreference") == []
    assert ledger.rows("StatedGoal") == []
    assert ledger.rows("Maker")[0].identity == "unknown"


def test_js_prefix_can_slice_a_surrogate_and_remains_valid_json():
    import json

    capture = make_capture(
        ["🌞" + "a" * 77, "Next"], "https://example.org", "Test", "2026-01-01T00:00:00Z"
    )
    assert ord(capture["regions"][1]["anchor"]["prefix"][0]) == 0xDF1E
    assert json.loads(canonical(capture)) == capture
    assert validate_capture(capture) == capture
