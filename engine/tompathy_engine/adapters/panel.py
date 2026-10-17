"""Explicit panel exchange format; source codebooks own field mappings.

Missing annotation times are excluded from chronological decisions. Ties and
unavailable identities are not resolved by guessing. Original row units and
per-label depths are reported separately from any claim about people.
"""

from collections import Counter
from copy import deepcopy
from datetime import datetime

from ..ledger.ids import digest, maker_id
from ..ledger.provenance import provenance_for
from ..ledger.schema import (
    Artifact,
    Cost,
    Decision,
    Maker,
    Option,
    Session,
    StatedGoal,
    StatedPreference,
)

DATASETS = {
    "community-alignment",
    "prism",
    "multipref",
    "dices",
    "summarize-from-feedback",
    "movielens-beliefs",
}


def ingest(payload, ledger):
    dataset = payload["dataset"]
    if dataset not in DATASETS or not payload.get("codebook") or not payload.get("source_sha256"):
        raise ValueError(
            "Panel import needs a named source, pinned bytes and a field-mapping codebook"
        )
    if len(payload["rows"]) != payload["expected_rows"]:
        raise ValueError("Panel row count differs from dataset card/manifest")
    rows, makers, depths, excluded, keys = [], {}, Counter(), Counter(), set()
    audit = []
    for item in payload["rows"]:
        key = str(item["id"])
        if key in keys:
            raise ValueError("Duplicate panel source row")
        keys.add(key)
        source = deepcopy(item.get("native_source", {}))
        trace = {
            "observation_id": key,
            "source_maker_label": item.get("maker"),
            "native_source": source,
            "chronology_witness": deepcopy(item.get("chronology_witness")),
            "decision_id": None,
            "stated_preference_ids": [],
            "exclusion": None,
        }
        audit.append(trace)
        if item.get("maker") is None or not str(item["maker"]).strip():
            excluded["missing_identity"] += 1
            trace["exclusion"] = "missing_identity"
            continue
        maker = maker_id(dataset, str(item["maker"]))
        makers[maker] = Maker(
            maker_id=maker,
            source_dataset=dataset,
            identity="pseudonymous",
            display_label="Panel participant",
            identity_basis=[payload["codebook"]],
        )
        for index, preference in enumerate(item.get("stated_preferences", [])):
            trace["stated_preference_ids"].append(digest([dataset, key, "stated", index]))
            rows.append(
                StatedPreference(
                    pref_id=digest([dataset, key, "stated", index]),
                    maker_id=maker,
                    attribute=preference["attribute"],
                    value=preference["value"],
                    scale=preference["scale"],
                    source=preference["source"],
                    t=preference.get("t"),
                )
            )
        if not item.get("t_open") or not item.get("t_resolve"):
            excluded["missing_chronology"] += 1
            trace["exclusion"] = "missing_chronology"
            continue
        if item.get("tie") or item.get("taken") is None:
            excluded["unresolved_or_tie"] += 1
            trace["exclusion"] = "unresolved_or_tie"
            continue
        start = datetime.fromisoformat(item["t_open"])
        end = datetime.fromisoformat(item["t_resolve"])
        artifact = digest([dataset, key, "artifact"])
        session = digest([dataset, key, "session"])
        options = [
            Option(
                option_id=str(o["id"]),
                origin=o.get("origin", "system"),
                content_ref=ledger.put_text(o["text"]),
                position=i,
            )
            for i, o in enumerate(item["options"])
        ]
        goal_ids = []
        if item.get("prompt_by_maker") and item.get("prompt"):
            goal = digest([dataset, key, "prompt"])
            rows.append(
                StatedGoal(
                    goal_id=goal,
                    maker_id=maker,
                    scope="session",
                    scope_id=session,
                    text=item["prompt"],
                    source="request",
                    t=start,
                )
            )
            goal_ids.append(goal)
        rows.extend(
            [
                Artifact(
                    artifact_id=artifact,
                    maker_ids=[maker],
                    kind="other",
                    source_uri=payload["source_uri"],
                    tier="T2",
                    domain="preferences",
                ),
                Session(
                    session_id=session,
                    maker_id=maker,
                    artifact_id=artifact,
                    t_start=start,
                    t_end=end,
                    stated_goal_ids=goal_ids,
                ),
                Decision(
                    decision_id=digest([dataset, key]),
                    maker_id=maker,
                    session_id=session,
                    t_open=start,
                    t_resolve=end,
                    options=options,
                    taken=str(item["taken"]),
                    action=item.get("action", "choose"),
                    cost=Cost(latency_s=item.get("latency_s")),
                    context={
                        "prompt": item.get("prompt", ""),
                        "codebook": payload["codebook"],
                        "document_ref": ledger.put_text(item.get("prompt", "")),
                        "prompt_id": str(item.get("prompt_id", digest(item.get("prompt", "")))),
                        "source_observation_id": key,
                        "source_maker_label": item["maker"],
                        "native_source": {k: v for k, v in source.items() if k != "observed"},
                        "source_metadata": {
                            "source_sha256": payload["source_sha256"],
                            "manifest_hash": payload.get("manifest_hash"),
                            "license_evidence": deepcopy(payload.get("license_evidence")),
                            "mapping": deepcopy(payload.get("mapping", {})),
                        },
                    },
                    # Raw votes/reasons/confidence are post-choice observations,
                    # never pre-choice features or silently inferred intentions.
                    outcome={
                        "native_observation": source.get("observed", {}),
                        "chronology_witness": deepcopy(item.get("chronology_witness")),
                    },
                ),
            ]
        )
        depths[maker] += 1
        trace["decision_id"] = digest([dataset, key])
    rows.extend(makers.values())
    ledger.append_new(rows, provenance_for(rows, "panel:" + dataset, payload["source_sha256"]))
    return {
        "source_rows": len(payload["rows"]),
        "usable_decisions": sum(depths.values()),
        "maker_labels": len(makers),
        "depth_histogram": dict(Counter(depths.get(m, 0) for m in makers)),
        "excluded": dict(excluded),
        "codebook": payload["codebook"],
        "row_audit": audit,
    }
