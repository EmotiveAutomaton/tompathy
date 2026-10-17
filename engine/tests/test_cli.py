import hashlib
import json

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.cli import main
from tompathy_engine.ledger.ids import digest
from tompathy_engine.packet.contract import Packet


def test_cli_capture_analyze_population_registry(tmp_path, capsys):
    capture = make_capture(
        ["A constructed CLI reading."],
        "https://example.org/cli",
        "CLI fixture",
        "2026-01-01T00:00:00Z",
    )
    source = tmp_path / "capture.json"
    source.write_text(json.dumps(capture))
    ledger = tmp_path / "ledger"
    main(["ingest", "--adapter", "capture", "--source", str(source), "--ledger", str(ledger)])
    packet = tmp_path / "packets" / "reading.json"
    main(
        [
            "analyze",
            "--ledger",
            str(ledger),
            "--artifact",
            capture["id"],
            "--capture",
            str(source),
            "--out",
            str(packet),
        ]
    )
    parsed = Packet.model_validate_json(packet.read_text())
    assert parsed.artifact.id == capture["id"] and not parsed.hypotheses
    summary = tmp_path / "population.json"
    main(
        [
            "population",
            "build",
            "--ledger",
            str(ledger),
            "--id",
            "writing-v0",
            "--out",
            str(summary),
        ]
    )
    assert json.loads(summary.read_text())["makersPooled"] == 0
    main(
        [
            "registry",
            "publish",
            "--packets",
            str(packet.parent),
            "--out",
            str(tmp_path / "registry"),
        ]
    )
    assert len(list((tmp_path / "registry" / "index").glob("*.json"))) == 1


def test_native_cli_delivers_pinned_exchange_and_row_audit(tmp_path, capsys):
    source = tmp_path / "source.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": 101,
                "rater_id": "constructed-rater",
                "item_id": "constructed-item",
                "answer_timestamp": "1670476480",
                "answer_time_ms": "2000",
                "context": "Constructed context",
                "response": "Constructed answer",
                "Q2_test": "No",
            }
        )
        + "\n",
        encoding="utf8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "dataset": "dices",
                "file": source.name,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "expected_source_rows": 1,
                "source_uri": "https://example.org/constructed",
                "codebook": "Constructed Q2_test safety rating",
                "license_evidence": "Original fixture",
                "target": "Q2_test",
            }
        ),
        encoding="utf8",
    )
    out = tmp_path / "exchange.json"
    main(
        [
            "native-panel",
            "--manifest",
            str(manifest),
            "--out",
            str(out),
            "--ledger",
            str(tmp_path / "ledger"),
        ]
    )
    exchange = json.loads(out.read_text())
    receipt = json.loads(out.with_suffix(".json.receipt.json").read_text())
    assert receipt["exchange_hash"] == digest(exchange)
    assert receipt["ledger"]["row_audit"][0]["native_source"]["ids"]["id"] == 101
    assert receipt["ledger"]["usable_decisions"] == 1
    interface_path = tmp_path / "interface.json"
    main(["interface", "--out", str(interface_path)])
    interface = json.loads(interface_path.read_text())
    assert receipt["implementation_hash"] == interface["implementation_hash"]
    assert receipt["ledger_schema_hash"] == interface["ledger_schema_hash"]
