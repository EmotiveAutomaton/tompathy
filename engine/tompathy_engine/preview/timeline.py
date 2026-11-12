"""Bounded edit-location timeline. Revision gaps are not writing pauses."""
import re
from urllib.parse import quote

from ..adapters.capture import normalize
from ..adapters.history import diff_hunks, witnessed_parent
from ..ledger.ids import digest, maker_id

CITATION = re.compile(r"\[(?:\d+(?:\s*[,–-]\s*\d+)*|[a-z]|note\s+\d+|citation needed)\]", re.IGNORECASE)


def match_region(text, regions):
    target = normalize(CITATION.sub("", text))
    if len(target) < 3:
        return None
    matches = []
    for region in regions:
        clean = normalize(CITATION.sub("", region["anchor"]["exact"]))
        if target in clean:
            # Multiple occurrences within one region are also ambiguous.
            matches.extend([region["id"]] * clean.count(target))
    return matches[0] if len(matches) == 1 else None


def entry(maker, step, t, region, evidence):
    return {"maker": maker, "step": step, "t": t, "located": region is not None,
            "region": region, "node": None, "evidence": [evidence], "evidenceStatus": "unvalidated",
            "basis": "history", "description": "weak evidence of attention"}


def relink_timeline(packet):
    nodes = [n for n in packet.get("goalHierarchy", {}).get("nodes", []) if n.get("level") == "paragraph"]
    for item in packet.get("attentionTimeline", []):
        candidates = [n for n in nodes if item["region"] in n["regions"]]
        # Two lenses can disagree: don't quietly choose one producer's reading.
        item["node"] = candidates[0]["id"] if len(candidates) == 1 else None


def wikipedia_timeline(packet, history):
    known, timeline = {}, []
    makers = {m["id"] for m in packet["makers"]}
    names = {str(r[k]) for r in history["revisions"] for k in ("maker", "label") if r.get(k)}
    total = 0
    for step, revision in enumerate(history["revisions"]):
        before = witnessed_parent(revision, known)
        known[str(revision["id"])] = revision["text"]
        changes = diff_hunks(before, revision["text"]) if before is not None else [(0, 0, "")]
        if not changes:
            continue
        who = maker_id("wikipedia", str(revision.get("maker")))
        if who not in makers:
            who = packet["makers"][0]["id"]
        eid = digest(["attention-revision", packet["artifact"]["id"], str(revision["id"])])
        excerpts = "\n".join(replacement or (before or "")[a:b] for a, b, replacement in changes)
        for name in sorted(names, key=len, reverse=True):
            excerpts = re.sub(re.escape(name), "[contributor]", excerpts, flags=re.IGNORECASE)
        packet["evidence"].append({"id": eid, "source": packet["artifact"]["source"] + "#revision=" + quote(str(revision["id"]), safe=""),
                                   "excerpt": excerpts[:320], "capturedAt": revision["t"], "relationship": "Changed fragment; location is weak evidence of attention, not an editor's plan."})
        missing = False
        for _, _, replacement in changes:
            region = match_region(replacement, packet["artifact"]["regions"])
            if region:
                total += 1
                if len(timeline) < 2000:
                    timeline.append(entry(who, step, revision["t"], region, eid))
            else:
                missing = True
        if missing:
            total += 1
            if len(timeline) < 2000:
                timeline.append(entry(who, step, revision["t"], None, eid))
    packet["attentionTimeline"] = timeline
    packet["preview"]["timelineCoverage"] = {"emitted": len(timeline), "total": total}
    relink_timeline(packet)
