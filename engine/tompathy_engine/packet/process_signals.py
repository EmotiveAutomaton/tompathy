"""Outcome-associated repertoire and explicitly located inspection events."""

import itertools
from collections import defaultdict
from datetime import datetime

from ..adapters.capture import utf16_length
from ..adapters.wiki import revert_outcomes
from ..ledger.ids import digest


def apply_signals(packet, ledger, admissions, *, domain, tier, pipeline):
    from .modules import support

    if tier == "T0":
        return []
    enabled = set(admissions.enabled(domain))
    capture = packet["artifact"]
    at = datetime.fromisoformat(capture["capturedAt"])
    sessions = {s.session_id: s for s in ledger.rows("Session") if s.artifact_id == capture["id"]}
    stable = {m.maker_id for m in ledger.rows("Maker") if m.identity != "unknown"}
    makers = {m["id"] for m in packet["makers"]} & stable
    used = set()
    if "attention" in enabled and tier == "T2":
        # This exchange requires an exact capture revision and region. Cursor or
        # dwell events in old document coordinates are never silently relocated.
        for event in ledger.rows("ContextEvent"):
            p = event.payload
            if (
                event.session_id not in sessions
                or event.t >= at
                or p.get("capture_revision") != capture["revision"]
            ):
                continue
            maker = sessions[event.session_id].maker_id
            region = next((r for r in capture["regions"] if r["id"] == p.get("region")), None)
            kind = p.get("inspection_kind")
            if (
                maker not in makers
                or region is None
                or kind not in {"dwell", "cursor-revisit", "opened-unused"}
            ):
                continue
            duration = p.get("duration_ms")
            if duration is not None and (
                not isinstance(duration, (int, float)) or not 0 <= duration <= 86400000
            ):
                raise ValueError("Inspection duration outside its recorded bounds")
            eid, hid = (
                digest(["inspection-witness", event.event_id]),
                digest(["inspection", event.event_id]),
            )
            packet["evidence"].append(
                {
                    "id": eid,
                    "source": "ledger:context-event:" + event.event_id,
                    "excerpt": f"Recorded {kind}"
                    + (f" for {duration:g} ms." if duration is not None else "."),
                    "capturedAt": event.t.isoformat().replace("+00:00", "Z"),
                    "relationship": "Source-recorded inspection event with exact capture coordinates",
                }
            )
            value = support(
                1.0, "Located inspection event; relative presence, not strength of a mental state"
            )
            packet["hypotheses"].append(
                {
                    "id": hid,
                    "kind": "attention",
                    "interpretation": "current-attention",
                    "label": "Recorded " + kind,
                    "description": "A recorded interaction locates inspection of this region. It does not establish understanding or endorsement.",
                    "makers": [maker],
                    "regions": [region["id"]],
                    "status": "hypothesis",
                    "support": value,
                    "evidence": [eid],
                }
            )
            packet.setdefault("currentAttention", []).append(
                {
                    "maker": maker,
                    "span": {
                        "region": region["id"],
                        "start": 0,
                        "end": utf16_length(region["anchor"]["exact"]),
                    },
                    "items": [{"hypothesis": hid, "support": value}],
                }
            )
            used.add("attention")
    if (
        "expertise" in enabled
        and pipeline
        and pipeline.labels
        and ".wikipedia.org/wiki/" in capture["source"]
    ):
        revisions = sorted(
            [r for r in ledger.rows("Revision") if r.artifact_id == capture["id"] and r.t < at],
            key=lambda r: (r.t, r.revision_id),
        )
        # Hash-restoration proxy assumes a continuous chain, and censors the
        # newest 48 hours. A bounded gap is not evidence that an edit survived.
        if any(
            previous.revision_id not in current.parent_revision_ids
            for previous, current in itertools.pairwise(revisions)
        ):
            return [admissions.require(m, domain).admission_id for m in sorted(used)]
        outcomes = revert_outcomes(
            [
                {"id": r.revision_id, "t": r.t.isoformat(), "text": ledger.get_text(r.content_ref)}
                for r in revisions
            ]
        )
        groups, totals = defaultdict(dict), defaultdict(dict)
        for c in ledger.rows("Correction"):
            outcome = outcomes.get(c.revision_id)
            if not outcome or c.maker_id not in makers:
                continue
            label = pipeline.labels.answers("Correction", c.correction_id, "edit").get("Q8")
            if not label or label == "unclear":
                continue
            kept = not outcome["reverted_within_48h"]
            groups[(c.maker_id, label)][c.revision_id] = kept
            totals[c.maker_id][c.revision_id] = kept
        for (maker, label), rows in groups.items():
            other = [v for key, v in totals[maker].items() if key not in rows]
            kept = sum(rows.values())
            if len(rows) < 3 or len(other) < 3 or kept / len(rows) <= sum(other) / len(other):
                continue
            eid, hid = (
                digest(["expertise-witness", maker, label, rows]),
                digest(["expertise", maker, label, rows]),
            )
            packet["evidence"].append(
                {
                    "id": eid,
                    "source": capture["source"],
                    "excerpt": f"{kept}/{len(rows)} {label} revisions avoid hash restoration within 48h; {sum(other)}/{len(other)} other revisions do. Revision IDs: "
                    + ", ".join(sorted(rows)),
                    "capturedAt": capture["capturedAt"],
                    "relationship": "Censored 48-hour hash-restoration proxy; does not measure truth, quality or intention",
                }
            )
            packet["hypotheses"].append(
                {
                    "id": hid,
                    "kind": "process",
                    "interpretation": "repertoire",
                    "label": "Candidate expertise: " + label,
                    "description": "This recurring edit type has a higher observed survival fraction than this maker's other observed edit types. The association does not establish intended expertise or causal improvement.",
                    "makers": [maker],
                    "regions": [],
                    "status": "hypothesis",
                    "evidence": [eid],
                    "support": support(
                        kept / len(rows),
                        "Observed survival fraction; uncalibrated candidate expertise",
                    ),
                }
            )
            packet["process"]["nodes"].append(hid)
            used.add("expertise")
    return [admissions.require(m, domain).admission_id for m in sorted(used)] + (
        [pipeline.labels.require("Q8")] if "expertise" in used else []
    )
