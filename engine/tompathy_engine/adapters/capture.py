"""Exact browser capture handling, including ECMAScript whitespace and UTF-16."""

import hashlib
import re
from copy import deepcopy
from datetime import datetime

from ..ledger.ids import digest, maker_id
from ..ledger.provenance import provenance_for
from ..ledger.schema import Artifact, Evidence, Maker, Revision

# ECMAScript WhiteSpace + LineTerminator, unlike Python's broader Unicode \s.
_SPACE = re.compile(
    r"[\u0009-\u000d\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+"
)


def normalize(text: str) -> str:
    return _SPACE.sub(" ", text).strip(" ")


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def utf16_slice(text: str, start: int, end: int) -> str:
    return text.encode("utf-16-le", errors="surrogatepass")[start * 2 : end * 2].decode(
        "utf-16-le", errors="surrogatepass"
    )


def browser_hash(text: str) -> str:
    # TextEncoder replaces unpaired UTF-16 surrogates with U+FFFD.
    repaired = text.encode("utf-16-le", errors="surrogatepass").decode(
        "utf-16-le", errors="replace"
    )
    return hashlib.sha256(repaired.encode("utf-8")).hexdigest()


def make_capture(texts: list[str], source: str, title: str, captured_at: str) -> dict:
    clean = [s for s in map(normalize, texts) if s][:1500]
    text = "\n\n".join(clean)
    regions, start = [], 0
    for index, exact in enumerate(clean):
        end = start + utf16_length(exact)
        regions.append(
            {
                "id": f"p{index + 1}",
                "anchor": {
                    "exact": exact,
                    "index": index,
                    "start": start,
                    "prefix": utf16_slice(text, max(0, start - 80), start),
                    "suffix": utf16_slice(text, end, end + 80),
                },
            }
        )
        start = end + 2
    return {
        "id": source.split("#")[0],
        "revision": browser_hash(text),
        "title": title,
        "source": source,
        "capturedAt": captured_at,
        "truncated": len(texts) > 1500,
        "regions": regions,
    }


def validate_capture(artifact: dict) -> dict:
    regions = artifact["regions"]
    if not 1 <= len(regions) <= 1500:
        raise ValueError("Capture requires 1..1500 regions")
    ids = [r["id"] for r in regions]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate capture regions")
    expected = make_capture(
        [r["anchor"]["exact"] for r in regions],
        artifact["source"],
        artifact["title"],
        artifact["capturedAt"],
    )
    if artifact["revision"] != expected["revision"] or artifact["id"] != expected["id"]:
        raise ValueError("Capture ID or revision hash differs from its content")
    for actual, calculated in zip(regions, expected["regions"]):
        if actual["anchor"] != calculated["anchor"]:
            raise ValueError("Capture anchor differs from normalized UTF-16 text")
    return deepcopy(artifact)


def ingest(artifact: dict, ledger):
    artifact = validate_capture(artifact)
    text = "\n\n".join(r["anchor"]["exact"] for r in artifact["regions"])
    source_hash = browser_hash(text)
    ident = maker_id("capture", artifact["id"])
    # Page metadata is an attribution claim, not a cross-source identity join.
    authors = artifact.get("authors", [])
    label = authors[0]["label"] if len(authors) == 1 else "Unidentified creator"
    captured = datetime.fromisoformat(artifact["capturedAt"])
    revision = digest([artifact["id"], artifact["revision"]])
    rows = [
        Maker(
            maker_id=ident,
            source_dataset="capture",
            identity="unknown",
            display_label=label,
            identity_basis=["Page attribution only; identity unverified"],
        ),
        Artifact(
            artifact_id=artifact["id"],
            maker_ids=[ident],
            kind="article",
            source_uri=artifact["source"],
            revisions=[revision],
            tier="T0",
        ),
        Revision(
            revision_id=revision,
            artifact_id=artifact["id"],
            t=captured,
            content_ref=ledger.put_text(text),
        ),
        Evidence(
            evidence_id=digest([revision, "capture"]),
            source_uri=artifact["source"],
            excerpt=text[:2000],
            captured_at=captured,
            relationship="Observed final text at capture time; no production history",
        ),
    ]
    ledger.append_new(rows, provenance_for(rows, "capture", source_hash))
    return {"artifact_id": artifact["id"], "tier": "T0", "decisions": 0, "revisions": 1}
