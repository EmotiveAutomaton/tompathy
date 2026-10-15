"""Generate only constructed packet fixtures, then validate them with zod."""

import argparse
import json
from pathlib import Path
import tempfile
import sys
from datetime import UTC, datetime

from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.adapters.history import ingest_history
from tompathy_engine.ledger.store import Ledger
from tompathy_engine.packet.build import build_packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("engine/tests/fixtures/packets"))
    parser.add_argument("--work", type=Path, default=Path(".local"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True); args.work.mkdir(parents=True, exist_ok=True)
    capture = make_capture(["A deliberate revision. 🌞", "The text discusses danger; motives remain unknown."],
                           "https://example.org/engine-fixture", "Constructed engine reading", "2026-01-03T00:00:00Z")
    t0 = build_packet(capture, origin="synthetic example")
    ledger = Ledger(tempfile.mkdtemp(prefix="engine-packet-fixture-", dir=args.work.resolve()))
    ingest_history(dict(artifact_id=capture["id"], source_uri=capture["source"], license="CC0-1.0",
                        license_evidence="Original constructed fixture", revisions=[
                            dict(id="one", maker="fixture-author", label="Constructed author", t="2026-01-01T00:00:00Z", text="A revision.", summary="Draft"),
                            dict(id="two", parents=["one"], maker="fixture-author", label="Constructed author", t="2026-01-02T00:00:00Z", text="A deliberate revision. 🌞", summary="Clarify the wording")]), ledger, adapter="git")
    t1 = build_packet(capture, ledger=ledger, origin="synthetic example")
    context = build_packet(capture, scope="context", context=[dict(id="selected-fixture", source="fixture:context", excerpt="A supplied contextual observation.", retrievedAt="2026-01-02T00:00:00Z", selected=True)], origin="synthetic example")
    for name, packet in [("capture-t0", t0), ("revision-t1", t1), ("selected-context", context)]:
        (args.out / f"{name}.json").write_text(json.dumps(packet, indent=2, ensure_ascii=True) + "\n", encoding="utf8")
    # Exercise the real fit-to-packet route with explicitly constructed gates.
    # These records are never placed in a production admissions directory.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from test_model_bundle import fixture
    from test_admission import record
    from tompathy_engine.admission import Admissions
    from tompathy_engine.models.bundle import fit_bundle
    fitted_ledger, fitted_capture = fixture(Path(tempfile.mkdtemp(prefix="engine-model-fixture-", dir=args.work.resolve())))
    model = fit_bundle(fitted_ledger, population="writing-v0", until=datetime(2026, 1, 2, tzinfo=UTC))
    gates = Admissions([record(module="backbone-preferences", implementation_hash=model.implementation_hash)])
    packet = build_packet(fitted_capture, ledger=fitted_ledger, model=model, admissions=gates, origin="synthetic example")
    (args.out / "constructed-preferences.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf8")
    print("Generated four constructed engine packets")


if __name__ == "__main__":
    main()
