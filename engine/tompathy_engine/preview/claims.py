"""One pinned claim snapshot; missing/superseded evidence fails closed."""
import json
from copy import deepcopy
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parents[3] / "docs/claims/SNAPSHOT.json"


def load_snapshot():
    try:
        value = json.loads(SNAPSHOT.read_text(encoding="utf8"))
        if (isinstance(value, dict) and value.get("schema") == "tompathy.claims.v1"
                and isinstance(value.get("rows"), list) and isinstance(value.get("globalFindings"), list)
                and all(isinstance(row, dict) and all(isinstance(row.get(key), str)
                        for key in ("ledgerId", "wording", "controlStatus", "source")) for row in value["rows"])
                and all(isinstance(row, dict) and isinstance(row.get("source"), str) for row in value["globalFindings"])):
            return value
    except (OSError, ValueError):
        pass
    return {"rows": [], "globalFindings": []}


def citation(row):
    return {key: row[key] for key in ("ledgerId", "wording", "controlStatus", "source")}


def licensed(row, preview):
    reader = row.get("reader")
    return bool(row.get("fieldEligible") and row.get("controlStatus") == "passes"
                and not row.get("supersededBy") and isinstance(reader, dict)
                and all(isinstance(reader.get(key), str) and reader[key] for key in ("id", "revision", "sha256", "backend"))
                and row.get("definition") == preview.get("departureDefinition")
                and any(all(actual.get(key) == reader.get(key) for key in ("id", "revision", "sha256", "backend"))
                        for actual in preview.get("readers", [])))


def departure_labels(item, preview, snapshot=None):
    snapshot = load_snapshot() if snapshot is None else snapshot
    ids = ["S15-EV1-PAUSES-V1"] + (["S15-EV2-SIGNATURES-V1"] if item["kind"] == "process" else [])
    rows = [row for row in snapshot["rows"] if row["ledgerId"] in ids]
    eligible = item.get("finding") == "departure-phrase" and len(rows) == len(ids) and all(licensed(row, preview) for row in rows)
    return {"evidenceStatus": "field-tested" if eligible else "unvalidated",
            "ledgerRows": [citation(row) for row in rows] if item.get("finding") == "departure-phrase" else []}


def resolve_packet(packet, snapshot=None):
    """Downgrade stale saved statuses, without altering measurements or gates."""
    snapshot = load_snapshot() if snapshot is None else snapshot
    lookup = {row["ledgerId"]: row for row in snapshot["rows"]}
    phrases = {h["id"] for h in packet.get("hypotheses", []) if isinstance(h.get("id"), str) and h.get("finding") == "departure-phrase" and h.get("kind") in {"attention", "process"}}
    def visit(value):
        if isinstance(value, dict):
            if value.get("evidenceStatus") == "field-tested":
                rows = value.get("ledgerRows", [])
                phrase = value.get("finding") == "departure-phrase" and value.get("kind") in {"attention", "process"} or value.get("hypothesis") in phrases
                if not phrase or not rows or any(row.get("ledgerId") not in lookup or citation(lookup[row["ledgerId"]]) != row
                                   or not licensed(lookup[row["ledgerId"]], packet.get("preview", {})) for row in rows):
                    value["evidenceStatus"] = "unvalidated"
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(packet)
    if packet.get("globalFindings"):
        current = {f["source"]: f for f in snapshot["globalFindings"]}
        packet["globalFindings"] = [deepcopy(current.get(f["source"], f)) for f in packet["globalFindings"]]
    return packet
