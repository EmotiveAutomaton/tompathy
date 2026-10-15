"""Bounded serial Wikipedia revision fetch and explicit reconstruction witnesses."""

import time
from datetime import datetime, timedelta
from urllib.parse import unquote, urlsplit

import httpx

from ..ledger.ids import text_hash
from .history import ingest_history


def fetch_history(url, *, artifact_id, limit=20, cancel=None, client=None):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.port
        or not parsed.hostname
        or not parsed.hostname.endswith(".wikipedia.org")
        or not parsed.path.startswith("/wiki/")
        or parsed.query
        or parsed.fragment
        or not 1 <= limit <= 500
    ):
        raise ValueError("Use an HTTPS Wikipedia article URL and 1–500 revisions")
    owned = client is None
    client = client or httpx.Client(
        timeout=20,
        follow_redirects=False,
        trust_env=False,
        headers={"User-Agent": "ToMpathyEngine/0.1 (https://github.com/EmotiveAutomaton/tompathy)"},
    )
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "revisions",
        "titles": unquote(parsed.path[6:]).replace("_", " "),
        "rvslots": "main",
        "rvprop": "ids|timestamp|user|userid|comment|content|flags|tags",
        "rvlimit": min(limit, 50),
    }
    revisions = []
    try:
        while len(revisions) < limit:
            if cancel and cancel():
                raise InterruptedError("Wikipedia fetch cancelled")
            response = client.get(f"https://{parsed.hostname}/w/api.php", params=params)
            response.raise_for_status()
            if len(response.content) > 16_000_000:
                raise ValueError("Wikipedia response exceeds bound")
            data = response.json()
            if "error" in data:
                raise ValueError("Wikipedia rejected the revision request")
            pages = data.get("query", {}).get("pages", [])
            if len(pages) != 1 or "missing" in pages[0]:
                raise ValueError("Article was not uniquely resolved")
            revisions.extend(pages[0].get("revisions", []))
            if "continue" not in data or len(revisions) >= limit:
                break
            params.update(data["continue"])
            time.sleep(0.1)
    finally:
        if owned:
            client.close()
    snapshots = []
    for row in reversed(revisions[:limit]):
        text = row.get("slots", {}).get("main", {}).get("content")
        if text is None or "userhidden" in row:
            raise ValueError("Suppressed revision cannot be reconstructed or attributed")
        snapshots.append(
            {
                "id": str(row["revid"]),
                "parents": [str(row["parentid"])] if row.get("parentid") else [],
                "maker": str(row.get("userid")) if row.get("userid") else row.get("user"),
                "label": row.get("user", "Unidentified editor"),
                "unstable_identity": "anon" in row,
                "t": row["timestamp"],
                "summary": row.get("comment", ""),
                "text": text,
                "bot": True if "bot" in row or "bot" in row.get("tags", []) else "unknown",
            }
        )
    return {
        "artifact_id": artifact_id,
        "source_uri": url,
        "license": "CC-BY-SA-4.0",
        "license_evidence": "https://en.wikipedia.org/wiki/Wikipedia:Copyrights",
        "revisions": snapshots,
    }


def revert_outcomes(snapshots):
    """Hash restoration proxy; absence is censored without a full 48-hour window."""
    rows = sorted(snapshots, key=lambda r: r["t"])
    parsed = [(r, datetime.fromisoformat(r["t"]), text_hash(r["text"])) for r in rows]
    result = {}
    for i, (row, t, _) in enumerate(parsed):
        if not i:
            result[row["id"]] = None
            continue
        prior = parsed[i - 1][2]
        end = t + timedelta(hours=48)
        matches = [
            when for _, when, content in parsed[i + 1 :] if t <= when <= end and content == prior
        ]
        result[row["id"]] = (
            {"reverted_within_48h": True, "observed_at": matches[0].isoformat()}
            if matches
            else (
                {"reverted_within_48h": False, "observed_at": end.isoformat()}
                if parsed[-1][1] >= end
                else None
            )
        )
    return result


def ingest(payload, ledger):
    receipt = ingest_history(payload, ledger, adapter="wikipedia")
    receipt["revert_proxy"] = revert_outcomes(payload["revisions"])
    return receipt
