"""Local-only, integrity-checked real-run cache. Never a substitute reading."""

import json
from datetime import UTC, datetime
from pathlib import Path

from ..ledger.ids import digest


def keeps_progress(candidate, previous):
    """Keep the last good checkpoint until exact-cache replay has caught up."""
    old, new = previous.get("preview", {}), candidate.get("preview", {})
    modules = {m["id"]: m for m in new.get("modules", [])}
    return all(m["id"] in modules and
               (m["status"] != "complete" or modules[m["id"]]["status"] == "complete") and
               (modules[m["id"]].get("completed") or 0) >= (m.get("completed") or 0)
               for m in old.get("modules", [])) and \
        set(old.get("coverage") or []) <= set(new.get("coverage") or []) and \
        {n["id"] for n in (previous.get("goalHierarchy") or {}).get("nodes", [])} <= \
        {n["id"] for n in (candidate.get("goalHierarchy") or {}).get("nodes", [])} and \
        ((new.get("payoff") or {}).get("sentencesScored") or 0) >= ((old.get("payoff") or {}).get("sentencesScored") or 0)


def read(root, kind, key, max_age=None):
    if not root:
        return None
    path = Path(root) / kind / (key + ".json")
    if not path.exists() or path.stat().st_size > 32_000_000:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf8"))
        if value["key"] != key or digest(value["data"]) != value["sha256"]:
            return None
        if max_age is not None and (datetime.now(UTC) - datetime.fromisoformat(value["at"])).total_seconds() > max_age:
            return None
        return value
    except (ValueError, KeyError):
        return None


def write(root, kind, key, data):
    if not root:
        return
    folder = Path(root) / kind
    folder.mkdir(parents=True, exist_ok=True)
    value = {"key": key, "sha256": digest(data), "data": data, "at": datetime.now(UTC).isoformat().replace("+00:00", "Z")}
    temporary = folder / (key + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=True), encoding="utf8")
    temporary.replace(folder / (key + ".json"))
