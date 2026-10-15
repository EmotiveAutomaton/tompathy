"""Admitted process and attention hypotheses with exact historical witnesses."""

from collections import Counter, defaultdict
from datetime import UTC, datetime

from ..adapters.capture import utf16_length
from ..ledger.ids import digest
from ..models.source_trust import SourceObservation, trajectory


def support(value, meaning):
    return {"value": float(value), "scale": [0, 1], "semantics": "relative", "meaning": meaning}


def apply_modules(packet, ledger, admissions, *, domain, tier, pipeline=None):
    if tier == "T0":
        return []
    enabled = set(admissions.enabled(domain))
    at = datetime.fromisoformat(packet["artifact"]["capturedAt"])
    aid = packet["artifact"]["id"]
    stable = {m.maker_id for m in ledger.rows("Maker") if m.identity != "unknown"}
    makers = {m["id"] for m in packet["makers"]} & stable
    sessions = {s.session_id: s for s in ledger.rows("Session") if s.artifact_id == aid}
    revisions = {
        r.revision_id: r for r in ledger.rows("Revision") if r.artifact_id == aid and r.t < at
    }
    decisions = {
        d.decision_id: d
        for d in ledger.rows("Decision")
        if d.session_id in sessions and d.t_resolve < at and d.maker_id in makers
    }
    corrections = [
        c
        for c in ledger.rows("Correction")
        if c.t < at
        and c.maker_id in makers
        and (c.revision_id in revisions or c.decision_id in decisions)
    ]
    used = set()
    literal_used = False
    evidence_ids = {e["id"] for e in packet["evidence"]}

    def witness(row, kind):
        ident = getattr(row, kind + "_id")
        eid = digest([kind + "-witness", ident])
        if eid not in evidence_ids:
            text = (
                "Before: "
                + ledger.get_text(row.before_ref)[:700]
                + "\nAfter: "
                + ledger.get_text(row.after_ref)[:700]
                if kind == "correction"
                else f"Recorded {row.action} among {len(row.options)} alternatives."
            )
            t = row.t if kind == "correction" else row.t_resolve
            packet["evidence"].append(
                {
                    "id": eid,
                    "source": "ledger:" + kind + ":" + ident,
                    "excerpt": text,
                    "capturedAt": t.isoformat().replace("+00:00", "Z"),
                    "relationship": "Source-scoped historical witness",
                }
            )
            evidence_ids.add(eid)
        return eid

    def process(key, maker, label, description, evidence, value, meaning):
        hid = digest(["process-module", aid, key, maker])
        packet["hypotheses"].append(
            {
                "id": hid,
                "kind": "process",
                "interpretation": "repertoire",
                "label": label,
                "description": description,
                "makers": [maker],
                "regions": [],
                "status": "hypothesis",
                "evidence": evidence,
                "support": support(value, meaning),
            }
        )
        packet["process"]["nodes"].append(hid)

    if "habits" in enabled:
        groups = defaultdict(list)
        for d in decisions.values():
            groups[(d.maker_id, "handling", d.action)].append(d)
            groups[
                (d.maker_id, "source clock", f"{d.t_open.astimezone(UTC).hour:02d}:00 UTC")
            ].append(d)
        for c in corrections:
            phrase = " ".join(ledger.get_text(c.after_ref).split())
            if 12 <= len(phrase) <= 100:
                groups[(c.maker_id, "phrase", phrase)].append(c)
        if pipeline and pipeline.labels:
            for c in corrections:
                answer = pipeline.labels.answers("Correction", c.correction_id, "edit")
                if "Q8" in answer and answer["Q8"] != "unclear":
                    groups[(c.maker_id, "edit", answer["Q8"])].append(c)
        totals = Counter()
        for (maker, group, label), rows in groups.items():
            totals[(maker, group)] += len(rows)
        for (maker, group, label), rows in sorted(groups.items()):
            if len(rows) < 3:
                continue
            count = totals[(maker, group)]
            process(
                [group, label],
                maker,
                "Recurring " + label,
                f"Recorded {len(rows)} times among {count} observed {group} events in this artifact. "
                "Repetition alone does not establish intention or expertise.",
                [
                    witness(r, "correction" if group in {"edit", "phrase"} else "decision")
                    for r in rows[-8:]
                ],
                len(rows) / count,
                "Observed frequency in this bounded record; relative repertoire hypothesis",
            )
            used.add("habits")
            literal_used |= group == "edit"

    if "source-trust" in enabled:
        rows = [
            d
            for d in decisions.values()
            if any(o.origin == "ai" for o in d.options)
            and d.action in {"accept", "edit", "dismiss", "ignore"}
        ]
        # Explicit availability is mandatory. An outcome without its observation
        # time cannot influence earlier propensity estimates.
        observations = []
        for d in rows:
            quality = d.outcome.get("source_quality")
            available = d.outcome.get("source_quality_available")
            observations.append(
                SourceObservation(
                    d.decision_id,
                    d.session_id,
                    d.t_resolve,
                    d.action in {"accept", "edit"},
                    quality if available else None,
                    datetime.fromisoformat(available) if available else None,
                    d.t_open,
                )
            )
        tracks = defaultdict(list)
        for point in trajectory(observations, until=at):
            tracks[point["session"]].append(point)
        for sid, points in tracks.items():
            maker = sessions[sid].maker_id
            last = points[-1]
            process(
                ["source-use", sid],
                maker,
                "Session source-use trajectory",
                "Relative acceptance propensity before each recorded response: "
                + "; ".join(f"{p['t']}: {p['acceptance_propensity']:.3f}" for p in points[-12:])
                + ". Earlier-only random-walk estimate. Acceptance is not endorsement or source reliability.",
                [witness(decisions[p["decision"]], "decision") for p in points[-8:]],
                last["acceptance_propensity"],
                "Relative session acceptance propensity; not calibrated trust",
            )
            used.add("source-trust")

    if "attention" in enabled:
        focused = defaultdict(list)
        regions = packet["artifact"]["regions"]
        for c in corrections:
            text = ledger.get_text(c.after_ref).strip()
            # A fragment must have one exact surviving location. Deleted or
            # ambiguous historical fragments remain unlocated witnesses.
            matched = [r for r in regions if len(text) >= 3 and text in r["anchor"]["exact"]]
            if len(matched) == 1:
                focused[(c.maker_id, matched[0]["id"])].append(c)
        frames = []
        totals = Counter()
        for (maker, region), rows in focused.items():
            totals[maker] += len(rows)
        for (maker, rid), rows in sorted(focused.items()):
            region = next(r for r in regions if r["id"] == rid)
            hid = digest(["edit-focus", maker, rid])
            relative = support(
                len(rows) / totals[maker],
                "Share of exactly located corrections; edit focus is weak evidence of attention",
            )
            packet["hypotheses"].append(
                {
                    "id": hid,
                    "kind": "attention",
                    "interpretation": "current-attention",
                    "label": "Edit focus",
                    "description": f"{len(rows)} recorded corrections touch this surviving region. "
                    "This locates edits; it does not establish the maker's present mental state.",
                    "makers": [maker],
                    "regions": [rid],
                    "status": "hypothesis",
                    "support": relative,
                    "evidence": [witness(c, "correction") for c in rows[-8:]],
                }
            )
            frames.append(
                {
                    "maker": maker,
                    "span": {
                        "region": rid,
                        "start": 0,
                        "end": utf16_length(region["anchor"]["exact"]),
                    },
                    "items": [{"hypothesis": hid, "support": relative}],
                }
            )
            used.add("attention")
        if frames:
            packet["currentAttention"] = frames
    from .process_signals import apply_signals

    return (
        [admissions.require(m, domain).admission_id for m in sorted(used)]
        + ([pipeline.labels.require("Q8")] if literal_used else [])
        + apply_signals(packet, ledger, admissions, domain=domain, tier=tier, pipeline=pipeline)
    )


def apply_pipeline(packet, ledger, pipeline, admissions, *, tier, domain):
    from .preferences import apply_preferences

    pipeline.verify(
        ledger,
        at=datetime.fromisoformat(packet["artifact"]["capturedAt"]),
        implementation=admissions.implementation,
    )
    if pipeline.domain != domain:
        raise ValueError("Pipeline domain differs from capture")
    enabled = set(admissions.enabled(domain))
    used = []
    questions_used = set()
    if pipeline.extra_features:
        if "local-features" not in enabled:
            return apply_modules(
                packet, ledger, admissions, domain=domain, tier=tier, pipeline=pipeline
            )
        feature_gate = admissions.require("local-features", domain)
        if feature_gate.model_pin != digest(pipeline.extra_features.model_pins):
            raise ValueError("Local feature models differ from their admitted pins")
    if tier == "T0":
        from .prior import apply_prior

        return apply_prior(packet, pipeline, admissions, domain=domain)
    if pipeline.diagnosticity and "diagnosticity" not in enabled:
        # A weighted fit must not bypass its additional module gate.
        return apply_modules(
            packet, ledger, admissions, domain=domain, tier=tier, pipeline=pipeline
        )
    for task, module in (
        ("joint", "joint-preferences"),
        ("corrections", "corrections"),
        ("options", "literal-preferences" if pipeline.questions else "backbone-preferences"),
    ):
        if task in pipeline.fits and module in enabled:
            used += apply_preferences(
                packet,
                ledger,
                pipeline.fits[task],
                admissions,
                tier=tier,
                domain=domain,
                names=pipeline.features,
                module=module,
                verified=True,
            )
            if used:
                questions_used.update(pipeline.questions)
                if task in {"joint", "corrections"} and any(
                    k != "unknown" for k in pipeline.classifications.values()
                ):
                    questions_used.update(["Q8", "Q9"])
                from .drives import apply_drives

                used += apply_drives(
                    packet, pipeline, pipeline.fits[task], admissions, tier=tier, domain=domain
                )
            if used and pipeline.diagnosticity:
                used.append(admissions.require("diagnosticity", domain).admission_id)
            break
    if used and pipeline.extra_features:
        used.append(admissions.require("local-features", domain).admission_id)
    process_used = apply_modules(
        packet, ledger, admissions, domain=domain, tier=tier, pipeline=pipeline
    )
    used += process_used
    if used and pipeline.labels:
        used += [pipeline.labels.require(q) for q in sorted(questions_used)]
    return sorted(set(used))
