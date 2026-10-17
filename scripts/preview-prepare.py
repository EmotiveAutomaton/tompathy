"""Explicit, bounded CPU cache preparation for an exact saved browser capture.

This measures reader outputs, not human behavior or research admission. It does
not start services or make network calls. Subsequent ordinary previews reuse the
same exact score-call caches and produce their own validated packets.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from tompathy_engine.adapters.capture import validate_capture
from tompathy_engine.preview.readers import LocalReader
from tompathy_engine.preview.surface import deviation_map, compare_readers

parser = argparse.ArgumentParser()
parser.add_argument("capture")
parser.add_argument("--seconds", type=int, default=900)
parser.add_argument("--out", default="evidence/preview-preparation.json")
args = parser.parse_args()
if not 30 <= args.seconds <= 3600:
    raise ValueError("Preparation budget must be 30–3,600 seconds")
capture = validate_capture(json.loads(Path(args.capture).read_text(encoding="utf8")))
start = monotonic()
report = {"startedAt": datetime.now(UTC).isoformat(), "revision": capture["revision"], "source": capture["source"],
          "words": sum(len(r["anchor"]["exact"].split()) for r in capture["regions"]), "budgetSeconds": args.seconds,
          "scientificAdmission": False}

def check():
    if monotonic() - start >= args.seconds:
        raise TimeoutError("Preparation budget reached; completed score calls remain cached")

try:
    readers = [LocalReader(Path(".local/preview-readers") / name, ".local/preview-score-cache") for name in ("qwen", "smol")]
    report["readers"] = [reader.identity for reader in readers]
    print("Preparing whole-capture Qwen departures", flush=True)
    result = deviation_map(capture, readers[0], check)
    report["departureSeconds"] = monotonic() - start
    report["statistics"] = result["statistics"]
    print("Preparing whole-capture two-reader comparison", flush=True)
    report["agreement"] = compare_readers(capture, readers, check)
    report["completed"] = True
except TimeoutError as error:
    report.update(completed=False, limit=str(error))
finally:
    report["seconds"] = monotonic() - start
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"readers", "statistics", "agreement"}}, indent=2), flush=True)
