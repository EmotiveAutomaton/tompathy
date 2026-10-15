"""Map admitted local candidates and minimal complete covers to the reader graph."""

from ..ledger.ids import digest
from .modules import support


def apply_goals(packet, ledger, goals, admissions, domain):
    if goals is None or not {"goal-candidates", "goal-tree"} <= set(admissions.enabled(domain)):
        return []
    resolved, cues = goals.resolve(
        packet["artifact"], ledger, admissions, domain, {m["id"] for m in packet["makers"]}
    )
    capture = packet["artifact"]
    cue_evidence = {}
    for cue in cues:
        eid = digest(["goal-cue", cue["goal_id"]])
        packet["evidence"].append(
            {
                "id": eid,
                "source": "ledger:stated-goal:" + cue["goal_id"],
                "excerpt": cue["text"][:2000],
                "capturedAt": cue["t"].replace("+00:00", "Z"),
                "relationship": "Stated goal; a fallible cue, not verified purpose",
            }
        )
        cue_evidence[cue["goal_id"]] = eid
    nodes = []
    for c in goals.candidates:
        hid = digest(["goal-candidate", goals.capture_hash, c.id])
        witness = [digest([capture["revision"], r]) for r in c.regions]
        witness += [cue_evidence[i] for i in c.cue_ids]
        governing = c.id in resolved[c.maker]["governing"]
        value = (1 - goals.root_reliability) * c.support + goals.root_reliability * c.cue_match
        packet["hypotheses"].append(
            {
                "id": hid,
                "kind": "goal",
                "label": c.label,
                "description": c.description,
                "interpretation": "governing-purpose" if governing else "local-goal",
                "makers": [c.maker],
                "regions": c.regions,
                "status": "hypothesis",
                "evidence": witness,
                "support": support(
                    value,
                    "Relative candidate-goal support; explanatory reconstruction, not verified history",
                ),
            }
        )
        # Strict containment and increasing depth make parent links acyclic.
        parents = [
            p
            for p in goals.candidates
            if p.maker == c.maker and p.depth > c.depth and set(c.regions) <= set(p.regions)
        ]
        if parents:
            depth = min(p.depth for p in parents)
            parents = [p for p in parents if p.depth == depth][:16]
        node = {
            "id": hid,
            "maker": c.maker,
            "label": c.label,
            "description": c.description,
            "level": "governing goal" if governing else "local goal",
            "regions": c.regions,
            "evidence": witness,
        }
        if parents:
            node["parentIds"] = [
                digest(["goal-candidate", goals.capture_hash, p.id]) for p in parents
            ]
        nodes.append(node)
    if nodes:
        packet["goalHierarchy"] = {"nodes": nodes}
        return [
            admissions.require(m, domain).admission_id for m in ("goal-candidates", "goal-tree")
        ]
    return []
