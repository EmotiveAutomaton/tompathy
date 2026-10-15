"""Verify the original replay census; report chronology as a separate gate."""

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path

from ..adapters.coauthor import census


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    roster = json.loads(args.roster.read_text(encoding="utf8"))
    counts, writers = Counter(), set()
    chronology_excluded_sessions = 0
    chronology_excluded_decisions = 0
    start = time.monotonic()
    for index, item in enumerate(roster):
        path = (args.source_root / item["path"]).resolve()
        if not path.is_relative_to(args.source_root.resolve()):
            raise ValueError("Source path escapes declared root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["source_sha256"]:
            raise ValueError("Pinned raw source changed")
        events = [json.loads(line) for line in raw.decode("utf8").splitlines()]
        result, episodes, excluded = census(events)
        counts["sessions"] += 1
        counts["attempted"] += len(result["events"])
        counts["excluded"] += len(excluded)
        counts["usable"] += len(episodes)
        counts.update(e["decision"] for e, _ in episodes)
        writers.add(item["writer"])
        times = [float(e["eventTimestamp"]) for e in events]
        if any(not math.isfinite(t) for t in times) or times != sorted(times):
            chronology_excluded_sessions += 1
            chronology_excluded_decisions += len(episodes)
        if (index + 1) % 100 == 0:
            print(f"Replayed {index + 1}/{len(roster)} sessions", flush=True)
    summary = {
        "counts": counts,
        "writers": len(writers),
        "chronology_excluded_sessions": chronology_excluded_sessions,
        "chronology_excluded_decisions": chronology_excluded_decisions,
        "seconds": time.monotonic() - start,
        "scope": "Port consistency with historically exposed source; not new scientific admission",
    }
    summary["original_census_pass"] = (
        counts["sessions"] == 1445
        and counts["usable"] == 16959
        and counts["excluded"] == 39
        and len(writers) == 61
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    print(json.dumps(summary, indent=2))
    if not summary["original_census_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
