"""Frozen November rows and a default-off, receipt-scoped field label."""
import math
from copy import deepcopy

from ...ledger.ids import digest

PROTOCOL = {
    "id": "tompathy-back-half-2026-11-11-v1", "seed": 20261111, "draws": 2000,
    "folds": 5, "cluster": "writer", "decision": "lower paired 95% bound exceeds bar",
    "attention": {"scope": "CoAuthor writer-typed content words after engine holdouts", "rows": {"1": .02, "2": .01, "3": 0.}},
    "ai-involvement": {"scope": "AI involvement, CoAuthor suggestions, 2021 model", "rows": {"1": .02, "2": .01, "3": 0.}},
    "edit-reasons": {"scope": "Stack Exchange single-hunk body edits, comment-derived labels", "rows": {}},
    "goals": {"scope": "PEP/EIP Motivation ranking pilot, abstract and summary removed", "rows": {}},
    "exploratorySelection": "largest row-1 gain among V1, V2, V3, V5; ties in that order",
    "regularization": "standardized logistic L2=1, unpenalized intercept; fitted inside writer folds",
}
PROTOCOL_PIN = digest(PROTOCOL)


def receipt(capability, *, status="waiting-for-data", engine_pin=None, data_pin=None, rows=(), evidence="not-run"):
    if capability not in {"attention", "ai-involvement", "edit-reasons", "goals"}:
        raise ValueError("Unknown benchmark capability")
    value = {"schema": "tompathy.benchmark.v1", "capability": capability, "protocol": PROTOCOL_PIN,
        "scope": PROTOCOL[capability]["scope"], "status": status, "enginePin": engine_pin,
        "dataPin": data_pin, "evidence": evidence, "rows": deepcopy(list(rows)), "productionAdmission": False}
    return value


def field_status(capability, result, *, enabled=False, engine_pin=None, data_pin=None):
    """No packet caller enables this flag. Old receipts cannot license new readers."""
    if enabled is not True or capability not in {"attention", "ai-involvement"} or not isinstance(result, dict):
        return "unvalidated"
    expected = {"schema": "tompathy.benchmark.v1", "capability": capability, "protocol": PROTOCOL_PIN,
        "scope": PROTOCOL[capability]["scope"], "status": "complete", "evidence": "natural-writing"}
    if any(result.get(k) != v for k,v in expected.items()) or not engine_pin or not data_pin:
        return "unvalidated"
    if result.get("enginePin") != engine_pin or result.get("dataPin") != data_pin:
        return "unvalidated"
    rows = result.get("rows", [])
    primary = [r for r in rows if isinstance(r, dict) and r.get("id") == "1"]
    if len(primary) != 1:
        return "unvalidated"
    row = primary[0]
    values = [row.get("baseline"), row.get("engine"), *(row.get("interval") or [])]
    if len(values) != 4 or any(type(v) not in (float, int) or not math.isfinite(v) for v in values):
        return "unvalidated"
    baseline, engine, low, high = values
    if (not 0 <= baseline <= 1 or not 0 <= engine <= 1 or not -1 <= low <= high <= 1
            or row.get("bar") != PROTOCOL[capability]["rows"]["1"] or row.get("registered") is not True
            or row.get("clusters", 0) < 2 or not low <= engine-baseline <= high):
        return "unvalidated"
    return "field-tested" if low > row["bar"] else "unvalidated"
