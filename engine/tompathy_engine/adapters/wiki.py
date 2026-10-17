"""Bounded serial Wikipedia revision fetch and explicit reconstruction witnesses."""

import html
import re
import time
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
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
        headers={key: "ToMpathyEngine/0.1 (https://github.com/EmotiveAutomaton/tompathy)" for key in ("User-Agent", "Api-User-Agent")},
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
    total_bytes = 0
    try:
        while len(revisions) < limit:
            if cancel and cancel():
                raise InterruptedError("Wikipedia fetch cancelled")
            response = client.get(f"https://{parsed.hostname}/w/api.php", params=params)
            if response.status_code in (429, 503):
                # Do not retry before the server's requested delay. Long delays
                # end this bounded request instead of blocking the live reading.
                value = response.headers.get("Retry-After", "")
                try:
                    delay = float(value) if value.isdigit() else (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
                except (ValueError, TypeError, OverflowError):
                    delay = None
                if delay is not None and delay <= 5:
                    end = time.monotonic() + max(0, delay)
                    while time.monotonic() < end:
                        if cancel and cancel():
                            raise InterruptedError("Wikipedia fetch cancelled")
                        time.sleep(min(.1, max(0, end - time.monotonic())))
                    response = client.get(f"https://{parsed.hostname}/w/api.php", params=params)
            response.raise_for_status()
            if len(response.content) > 16_000_000:
                raise ValueError("Wikipedia response exceeds bound")
            total_bytes += len(response.content)
            if total_bytes > 32_000_000:
                raise ValueError("Wikipedia history exceeds the aggregate response bound")
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
            params["rvlimit"] = min(limit - len(revisions), 50)
            time.sleep(0.1)
    finally:
        if owned:
            client.close()
    snapshots, suppressed = [], []
    for row in reversed(revisions[:limit]):
        text = row.get("slots", {}).get("main", {}).get("content")
        if text is None or "userhidden" in row:
            suppressed.append(str(row["revid"]))
            continue  # Children retain the missing parent ID: never diff across it.
        snapshots.append(
            {
                "id": str(row["revid"]),
                "parents": [str(row["parentid"])] if row.get("parentid") else [],
                "maker": str(row.get("userid")) if row.get("userid") else row.get("user"),
                "label": row.get("user", "Unidentified editor"),
                "unstable_identity": "anon" in row,
                "t": row["timestamp"],
                "summary": row.get("comment", ""),
                "tags": row.get("tags", []),
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
        "suppressedBoundaryIds": suppressed,
    }


def visible_text(text):
    """Conservative matching projection, not a MediaWiki renderer.

    Drop comments, refs, templates and media rather than inventing their rendered
    expansions. Ambiguous/deleted fragments remain unlocated.
    """
    text = re.sub(r"<!--[\s\S]*?-->|<ref\b[^>]*>[\s\S]*?</ref\s*>|<ref\b[^>]*/>", "", text, flags=re.IGNORECASE)
    for _ in range(20):
        stripped = re.sub(r"\{\{[^{}]*\}\}", "", text)
        if stripped == text:
            break
        text = stripped
    text = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\[([^]|]+)(?:\|([^]]+))?\]\]", lambda m: m[2] or m[1], text)
    text = re.sub(r"\[https?://\S+(?:\s+([^]]+))?\]", lambda m: m[1] or "", text)
    text = re.sub(r"<[^>]+>|'{2,5}|(?m:^={1,6}|={1,6}$)", "", text)
    return " ".join(html.unescape(text).split())


def revert_outcomes(snapshots):
    """Hash restoration proxy; absence is censored without a full 48-hour window."""
    rows = sorted(snapshots, key=lambda r: r["t"])
    parsed = [(r, datetime.fromisoformat(r["t"]), text_hash(r["text"])) for r in rows]
    result = {}
    for i, (row, t, _) in enumerate(parsed):
        if not i or row.get("parents") != [str(parsed[i - 1][0]["id"])]:
            result[row["id"]] = None
            continue
        prior = parsed[i - 1][2]
        end = t + timedelta(hours=48)
        contiguous = []
        parent = str(row["id"])
        for future, when, content in parsed[i + 1:]:
            if future.get("parents") != [parent]:
                break
            contiguous.append((future, when, content))
            parent = str(future["id"])
        matches = [when for _, when, content in contiguous if t <= when <= end and content == prior]
        result[row["id"]] = (
            {"reverted_within_48h": True, "observed_at": matches[0].isoformat()}
            if matches
            else (
                {"reverted_within_48h": False, "observed_at": end.isoformat()}
                if contiguous and contiguous[-1][1] >= end
                else None
            )
        )
    return result


def ingest(payload, ledger):
    receipt = ingest_history(payload, ledger, adapter="wikipedia")
    receipt["revert_proxy"] = revert_outcomes(payload["revisions"])
    return receipt
