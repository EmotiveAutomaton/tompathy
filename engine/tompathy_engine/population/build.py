"""Domain-scoped observed population summaries; no inferred drives from text."""

from collections import Counter

from .. import __version__
from ..admission import implementation_hash
from ..ledger.ids import digest

DOMAINS = {"writing-v0": "writing", "preferences-v0": "preferences", "chess-v0": "chess"}


def build(ledger, population_id, *, until=None):
    if population_id not in DOMAINS:
        raise ValueError("Unknown domain-tagged population")
    domain = DOMAINS[population_id]
    artifacts = {a.artifact_id: a for a in ledger.rows("Artifact") if a.domain == domain}
    sessions = {s.session_id: s for s in ledger.rows("Session") if s.artifact_id in artifacts}
    decisions = [
        d
        for d in ledger.rows("Decision")
        if d.session_id in sessions and (until is None or d.t_resolve < until)
    ]
    counts = Counter(d.maker_id for d in decisions)
    revision_makers = {
        r.maker_id
        for r in ledger.rows("Revision")
        if r.artifact_id in artifacts
        and artifacts[r.artifact_id].tier != "T0"
        and r.maker_id is not None
        and (until is None or r.t < until)
    }
    makers = set(counts) | revision_makers
    sources = sorted({m.source_dataset for m in ledger.rows("Maker") if m.maker_id in makers})
    description = (
        f"Observed {domain} ledger: {len(makers)} source-scoped maker identities and {len(decisions)} decisions. "
        + ("Sources: " + ", ".join(sources) + ". " if sources else "")
        + "These counts describe available records. No admitted population estimate of drives or values is loaded."
    )
    return {
        "populationId": population_id,
        "domain": domain,
        "makersPooled": len(makers),
        "description": description,
        "decisions": len(decisions),
        "artifacts": len(artifacts),
        "tiers": dict(Counter(a.tier for a in artifacts.values())),
        "depthHistogram": dict(Counter(counts.get(m, 0) for m in makers)),
        "recordsHash": digest(sorted(d.decision_id for d in decisions)),
        "until": until.isoformat() if until else None,
        "engineVersion": __version__,
        "implementationHash": implementation_hash(),
        "items": [],
        "estimateStatus": "unavailable: awaiting admitted population model",
    }


def packet_summary(population):
    return {k: population[k] for k in ("populationId", "makersPooled", "description", "items")}
