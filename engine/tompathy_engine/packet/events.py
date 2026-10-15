"""Witnessed choice and correction events, with no inferred mental purpose."""

from datetime import datetime

from ..ledger.ids import digest


def append_events(packet, ledger):
    artifact = packet["artifact"]
    cutoff = datetime.fromisoformat(artifact["capturedAt"])
    sessions = {s.session_id for s in ledger.rows("Session") if s.artifact_id == artifact["id"]}
    revisions = {
        r.revision_id
        for r in ledger.rows("Revision")
        if r.artifact_id == artifact["id"] and r.t <= cutoff
    }
    decisions = {
        d.decision_id: d
        for d in ledger.rows("Decision")
        if d.session_id in sessions and d.t_resolve <= cutoff
    }
    makers = {m["id"] for m in packet["makers"]}
    events = [
        (d.t_resolve, "decision", d.decision_id, d)
        for d in decisions.values()
        if d.maker_id in makers
    ]
    events += [
        (c.t, "correction", c.correction_id, c)
        for c in ledger.rows("Correction")
        if c.t <= cutoff
        and c.maker_id in makers
        and (c.decision_id in decisions or c.revision_id in revisions)
    ]
    for t, kind, ident, record in sorted(events, key=lambda row: row[:3])[-600:]:
        hid, eid = digest([kind + "-event", ident]), digest([kind + "-witness", ident])
        if kind == "decision":
            chosen = next((o for o in record.options if o.option_id == record.taken), None)
            text = ledger.get_text(chosen.content_ref) if chosen and chosen.content_ref else ""
            description = f"Recorded {record.action} among {len(record.options)} offered alternatives at {t.isoformat()}."
            if record.cost.latency_s is not None:
                description += f" Recorded decision latency: {record.cost.latency_s:g} seconds."
            description += " Acceptance does not establish endorsement, understanding or motive."
            excerpt = description + (
                " Selected text: " + text[:1500] if text else " No selected text is available."
            )
        else:
            text = ledger.get_text(record.after_ref)
            description = (
                f"Recorded correction at {t.isoformat()}. Its reason remains unestablished."
            )
            excerpt = (
                "Before: " + ledger.get_text(record.before_ref)[:1000] + "\nAfter: " + text[:1000]
            )
            parent = (
                digest(["decision-event", record.decision_id])
                if record.decision_id
                else digest(["revision-event", record.revision_id])
            )
            if parent in packet["process"]["nodes"]:
                packet["process"]["edges"].append(
                    {
                        "from": parent,
                        "to": hid,
                        "kind": "revises",
                        "status": "observed",
                        "evidence": [eid],
                        "relationship": "Correction linked by the source record",
                    }
                )
        packet["evidence"].append(
            {
                "id": eid,
                "source": "ledger:" + kind + ":" + ident,
                "excerpt": excerpt,
                "capturedAt": t.isoformat().replace("+00:00", "Z"),
                "relationship": "Observed source-scoped event; motives are not inferred",
            }
        )
        packet["hypotheses"].append(
            {
                "id": hid,
                "kind": "process",
                "interpretation": "historical-event",
                "label": "Recorded " + kind,
                "description": description,
                "makers": [record.maker_id],
                "regions": [r["id"] for r in artifact["regions"] if r["anchor"]["exact"] in text],
                "status": "observed",
                "evidence": [eid],
            }
        )
        packet["process"]["nodes"].append(hid)
    if packet["process"]["nodes"]:
        packet["process"]["interpretation"] = "historical-production"
