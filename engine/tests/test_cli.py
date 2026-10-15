import json

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.cli import main
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
