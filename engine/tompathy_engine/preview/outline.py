"""Descriptive locations of non-recurring departures; no model calls or admission."""
from functools import lru_cache
from math import ceil

from .surface import source_holdouts, words

NOTE = "may track rare words and topic changes; untested at paragraph-group level"


@lru_cache(maxsize=1500)
def content_words(text, held):
    tokens = [{"start": 0, "end": len(text), "nats": 0.0}] if text else []
    return sum(w["content"] and not w["held"] for w in words(text, tokens, held))


def update_attention_density(packet):
    covered = set(packet.get("preview", {}).get("coverage") or [])
    regions = {r["id"]: r for r in packet["artifact"]["regions"]}
    counts = {rid: content_words(regions[rid]["anchor"]["exact"], tuple(source_holdouts(regions[rid]))) for rid in covered if rid in regions}
    departures = {h["id"]: {s["region"] for s in h.get("spans", []) if s["region"] in covered}
                  for h in packet["hypotheses"] if h.get("finding") in {"departure-phrase", "departure-sentence"} and h["kind"] == "attention"}
    departures = {key: value for key, value in departures.items() if value}
    rate = len(departures) / sum(counts.values()) if sum(counts.values()) else 0.0
    ranked = []
    for node in packet.get("goalHierarchy", {}).get("nodes", []):
        if node.get("level") != "paragraph":
            continue
        read = set(node["regions"]) <= covered
        w = sum(counts.get(rid, 0) for rid in set(node["regions"]))
        d = sum(bool(spans & set(node["regions"])) for spans in departures.values())
        node.update(attentionDensity=100 * d / w if read and w else None,
                    attentionShare=d / len(departures) if read and departures else 0.0 if read and w else None,
                    divergence=False,
                    attentionEvidence={"evidenceStatus": "unvalidated", "basis": "text-surface", "ledgerRows": [],
                                       "coverage": "read" if read and w else "not-read", "description": NOTE})
        if read and w:
            ranked.append(((d + 50 * rate) / (w + 50), node, d, w))
    # Deterministic rank cutoff: ties do not paint an entire flat page.
    ranked.sort(key=lambda row: (-row[0], row[1]["id"]))
    for _, node, d, w in ranked[:ceil(len(ranked) / 10)]:
        if d and d / w > rate:
            node["divergence"] = True
