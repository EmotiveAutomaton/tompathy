"""Receiving-side integrity and scope checks, not a rerun of human-data studies."""
import hashlib
import json
from pathlib import Path

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.preview.build import build_preview
from tompathy_engine.preview.findings import findings

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "docs/sounding-line-engine-features-2026-10-20"


def test_received_table_hashes_source_pointers_and_control_flags():
    manifest = json.loads((DELIVERY / "MANIFEST.json").read_text(encoding="utf8"))
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((DELIVERY / name).read_bytes()).hexdigest() == expected, name
    table = json.loads((DELIVERY / "ENGINE_FEATURE_TABLE.json").read_text(encoding="utf8"))
    assert table["schema"] == "sounding-line.engine-feature-table.v1"
    rows = {row["id"]: row for row in table["rows"]}
    assert len(rows) == len(table["rows"]) == 21
    for row in rows.values():
        source = row["source"]
        assert source["sha256"] == manifest["files"][source["path"]]
        target = json.loads((DELIVERY / source["path"]).read_text(encoding="utf8"))
        for part in source["json_pointer"].split("/")[1:]:
            key = part.replace("~1", "/").replace("~0", "~")
            target = target[int(key)] if isinstance(target, list) else target[key]
        assert target is not None
    for name in ("EV3.final", "EV3.typed"):
        assert rows[name]["badge"] is None
        assert "chance_centered_fake_reference_bias" in rows[name]["control_flags"]
    assert table["engine_pin"] == "5f3ad0a304727fff5e1a6beca592e786ee71b181"


def test_aggregate_results_preserve_numbers_without_admitting_page_claims():
    returned = {f["source"]: f for f in findings()}
    for source, filename in (("EV1", "EV1_PAUSES_V1.json"), ("EV2", "EV2_SIGNATURES_V1.json")):
        primary = json.loads((DELIVERY / filename).read_text(encoding="utf8"))["summary"]["primary"]
        finding = returned[f"Sounding Line {source}"]
        assert finding["number"] == primary["effect"]
        assert finding["interval"] == [primary["ci_low"], primary["ci_high"]]
        assert finding["evidenceStatus"] == "descriptive"
        assert "1112368530dca2b7ed4e8223704be9506048ec16" in finding["link"]
    capture = make_capture(["A constructed page for checking scope, not human evidence."],
                           "https://example.org/scope", "Scope", "2026-10-23T00:00:00Z")
    packet = build_preview(build_packet(capture))
    assert packet["provider"]["admissions"] == []
    assert packet["valueView"]["tips"] == []
    assert not any(h["evidenceStatus"] == "admitted" for h in packet["hypotheses"])
    assert not any(h["kind"] == "value" for h in packet["hypotheses"])
