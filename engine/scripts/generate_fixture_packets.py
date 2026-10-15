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
        (args.out / f"{name}.json").write_text(json.dumps(packet, indent=2, ensure_ascii=True) + "\n", encoding="utf8", newline="\n")
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
    (args.out / "constructed-preferences.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf8", newline="\n")
    from test_engine_extensions import themed
    from test_pipeline import gates as pipeline_gates
    from tompathy_engine.models.goals import GoalInputs
    from tompathy_engine.ledger.ids import digest
    from tompathy_engine.admission import implementation_hash
    themed_ledger, themed_capture, pipeline = themed(Path(tempfile.mkdtemp(prefix="engine-themes-", dir=args.work.resolve())))
    advanced = build_packet(themed_capture, ledger=themed_ledger, model=pipeline,
                            admissions=pipeline_gates("joint-preferences", "drive-recipes", "habits", "attention"),
                            origin="synthetic example")
    fresh = make_capture(["Danger in a text does not establish motive."], "https://example.org/borrowed", "Borrowed prior example", themed_capture["capturedAt"])
    borrowed = build_packet(fresh, ledger=themed_ledger, model=pipeline,
                            admissions=pipeline_gates("population-prior", "drive-recipes"), origin="synthetic example")
    maker = digest(["capture-maker", fresh["id"]])
    pin = digest("constructed-goal-producer")
    goals = GoalInputs(capture_hash=digest(fresh), root_cues_hash=digest([]), generator_pin=pin,
                      candidates=[dict(id="explain", maker=maker, label="Explain the boundary", description="Constructed explanatory goal hypothesis.",
                                       regions=[fresh["regions"][0]["id"]], depth=1, support=.6)])
    goal_packet = build_packet(fresh, goals=goals, origin="synthetic example",
                              admissions=Admissions([record(module=m, model_pin=pin, implementation_hash=implementation_hash()) for m in ("goal-candidates", "goal-tree")]))
    for name, value in [("constructed-pipeline", advanced), ("constructed-prior", borrowed), ("constructed-goals", goal_packet)]:
        (args.out / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf8", newline="\n")
    print("Generated seven constructed engine packets")


if __name__ == "__main__":
    main()
