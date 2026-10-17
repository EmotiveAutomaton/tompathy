"""Build an exact-capture packet without filling evidence gaps with predictions."""

from datetime import UTC, datetime

from .. import __version__
from ..adapters.capture import validate_capture
from ..admission import Admissions
from ..ledger.ids import digest
from ..version import source_revision
from .contract import Packet


def iso(t):
    return t.astimezone(UTC).isoformat().replace("+00:00", "Z")


def build_packet(
    capture,
    *,
    ledger=None,
    scope="artifact",
    context=(),
    admissions=None,
    request_id=None,
    origin="live provider",
    model=None,
    goals=None,
):
    capture = validate_capture(capture)
    if ledger is not None:
        ledger = ledger.snapshot()
    admissions = admissions or Admissions()
    selected = [c for c in context if c.get("selected")] if scope == "context" else []
    context_ids = [c["id"] for c in selected]
    evidence = [
        {
            "id": digest([capture["revision"], r["id"]]),
            "source": capture["source"],
            "excerpt": r["anchor"]["exact"],
            "capturedAt": capture["capturedAt"],
            "relationship": "Observed final text; this alone does not establish a maker's choices or motives",
        }
        for r in capture["regions"]
    ]
    for item in selected:
        evidence.append(
            {
                "id": digest(["context", item["id"]]),
                "source": item["source"],
                "excerpt": item["excerpt"],
                "capturedAt": item["retrievedAt"],
                "relationship": "Reader-selected context; not independent verification of a claim",
            }
        )
    label = (capture.get("authors") or [{}])[0].get("label", "Unidentified creator")
    unknown = digest(["capture-maker", capture["id"]])
    makers = [
        {
            "id": unknown,
            "label": label,
            "identity": "unknown",
            "relationship": "Page attribution only; no verified identity or cross-source join",
        }
    ]
    hypotheses, process_nodes, edges = [], [], []
    tier, domain = "T0", "writing"
    if ledger is not None:
        artifacts = [a for a in ledger.rows("Artifact") if a.artifact_id == capture["id"]]
        if len(artifacts) > 1:
            raise ValueError("Ambiguous ledger artifact")
        if artifacts:
            artifact = artifacts[0]
            tier, domain = artifact.tier, artifact.domain
            source_makers = {m.maker_id: m for m in ledger.rows("Maker")}
            if artifact.maker_ids:
                makers = [
                    {
                        "id": m,
                        "label": f"Editor {list(artifact.maker_ids).index(m) + 1}" if source_makers[m].source_dataset == "wikipedia" else source_makers[m].display_label[:250],
                        **({"localLabel": source_makers[m].display_label[:250], "kind": "person"} if source_makers[m].source_dataset == "wikipedia" else {}),
                        "identity": "synthetic"
                        if source_makers[m].identity == "synthetic"
                        else "supplied"
                        if source_makers[m].identity == "supplied"
                        else "unknown",
                        "relationship": "Source-scoped ledger identity; display names are not joined",
                    }
                    for m in artifact.maker_ids
                ]
            if tier != "T0":
                cutoff = datetime.fromisoformat(capture["capturedAt"])
                revisions = sorted(
                    (
                        r
                        for r in ledger.rows("Revision")
                        if r.artifact_id == artifact.artifact_id and r.t <= cutoff
                    ),
                    key=lambda r: (r.t, r.revision_id),
                )
                # These are witnessed events, not inferred mental states. No
                # location is invented when revision text has no exact anchor.
                for revision in revisions[-300:]:
                    if revision.maker_id not in {m["id"] for m in makers} and not any(
                        m["id"] == unknown for m in makers
                    ):
                        makers.append(
                            {
                                "id": unknown,
                                "label": "Unidentified contributor",
                                "identity": "unknown",
                                "relationship": "Revision has no identified maker",
                            }
                        )
                    text = ledger.get_text(revision.content_ref)
                    ident = digest(["revision-event", revision.revision_id])
                    witness = digest([ident, "evidence"])
                    evidence.append(
                        {
                            "id": witness,
                            "source": artifact.source_uri,
                            "excerpt": text[:1500],
                            "capturedAt": iso(revision.t),
                            "relationship": "Recorded revision snapshot; timestamp is source-recorded",
                        }
                    )
                    regions = [r["id"] for r in capture["regions"] if r["anchor"]["exact"] in text]
                    hypotheses.append(
                        {
                            "id": ident,
                            "kind": "process",
                            "label": "Recorded revision",
                            "description": f"A source revision was recorded at {iso(revision.t)}. Its purpose is not inferred.",
                            "makers": [revision.maker_id]
                            if revision.maker_id in {m["id"] for m in makers}
                            else [unknown],
                            "regions": regions,
                            "status": "observed",
                            "evidence": [witness],
                            "interpretation": "historical-event",
                        }
                    )
                    process_nodes.append(ident)
                present = {
                    r.revision_id: digest(["revision-event", r.revision_id])
                    for r in revisions[-300:]
                }
                for revision in revisions[-300:]:
                    for parent in revision.parent_revision_ids:
                        if parent in present:
                            edges.append(
                                {"from_": present[parent], "to": present[revision.revision_id]}
                            )
                edges = [
                    {
                        "from": e["from_"],
                        "to": e["to"],
                        "kind": "precedes",
                        "status": "observed",
                        "relationship": "Recorded parent revision",
                        "evidence": [],
                    }
                    for e in edges
                ]
    method = (
        f"ToMpathy engine {__version__}; commit {source_revision()}; implementation {admissions.implementation}; "
        f"evidence tier {tier}; domain {domain}. Observed capture and ledger records only. "
        "Text alone does not update maker preferences. Actual contributing admission records are in provider.admissions."
    )
    packet = {
        "schemaVersion": "1.9" if any(m.get("localLabel") for m in makers) else "1.7",
        "id": digest(
            [capture["id"], capture["revision"], request_id, context_ids, admissions.implementation]
        ),
        "revision": 1,
        "artifact": capture,
        "provider": {"id": "tompathy-engine", "method": method, "admissions": []},
        "origin": origin,
        "scope": {"kind": scope, "contextIds": context_ids},
        "makers": makers,
        "hypotheses": hypotheses,
        "alternatives": [],
        "process": {
            "interpretation": "historical-production" if process_nodes else "unspecified",
            "nodes": process_nodes,
            "edges": edges,
        },
        "estimates": [
            {
                "region": r["id"],
                "uncertainty": {
                    "level": "unknown",
                    "meaning": f"{tier} evidence; no admitted estimate of motive or contribution",
                },
            }
            for r in capture["regions"]
        ],
        "evidence": evidence,
    }
    if ledger is not None:
        from ..population.build import DOMAINS, build, packet_summary
        from .events import append_events
        from .preferences import apply_preferences

        population_id = next((key for key, value in DOMAINS.items() if value == domain), None)
        if population_id:
            packet["population"] = packet_summary(
                build(ledger, population_id, until=datetime.fromisoformat(capture["capturedAt"]))
            )
        if tier != "T0":
            append_events(packet, ledger)
        from ..models.pipeline import Pipeline
        from .modules import apply_modules, apply_pipeline

        if isinstance(model, Pipeline):
            contributed = apply_pipeline(
                packet, ledger, model, admissions, tier=tier, domain=domain
            )
        else:
            contributed = apply_preferences(
                packet, ledger, model, admissions, tier=tier, domain=domain
            )
            contributed += apply_modules(packet, ledger, admissions, tier=tier, domain=domain)
        packet["provider"]["admissions"] += contributed
        if contributed:
            packet["provider"]["method"] = packet["provider"]["method"].replace(
                "Observed capture and ledger records only. ", ""
            )
            packet["id"] = digest(
                [packet["id"], model.model_dump(mode="json") if model else None, contributed]
            )
    from .goals import apply_goals

    goal_contributions = apply_goals(packet, ledger, goals, admissions, domain)
    if goal_contributions:
        packet["provider"]["admissions"] += goal_contributions
        packet["provider"]["method"] = packet["provider"]["method"].replace(
            "Observed capture and ledger records only. ", ""
        )
        packet["id"] = digest([packet["id"], goals.model_dump(mode="json"), goal_contributions])
    packet["provider"]["admissions"] = sorted(set(packet["provider"]["admissions"]))
    from .bounds import bound

    bound(packet)
    if any(m.get("localLabel") for m in packet["makers"]):
        packet["schemaVersion"] = "1.9"
    from ..preview.makers import hide_usernames
    return hide_usernames(Packet.model_validate(packet).wire())
