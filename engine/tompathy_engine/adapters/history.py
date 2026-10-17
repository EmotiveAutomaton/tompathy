"""Shared revision compiler: diff witnesses, never invented choice menus."""

from datetime import datetime
from difflib import SequenceMatcher

from ..ledger.ids import digest, maker_id
from ..ledger.provenance import provenance_for
from ..ledger.schema import Artifact, Correction, Evidence, Maker, Revision, StatedGoal

LICENSES = {"MIT", "Apache-2.0", "CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0"}


def diff_hunks(before, after):
    """Character edits reconstruct exactly, including newlines and Unicode."""
    if max(len(before), len(after)) > 10000:
        left, right = before.splitlines(keepends=True), after.splitlines(keepends=True)
        offsets = [0]
        for line in left:
            offsets.append(offsets[-1] + len(line))
        return [
            (offsets[a], offsets[b], "".join(right[c:d]))
            for op, a, b, c, d in SequenceMatcher(None, left, right, autojunk=False).get_opcodes()
            if op != "equal"
        ]
    return [
        (a, b, after[c:d])
        for op, a, b, c, d in SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
        if op != "equal"
    ]


def apply_hunks(before, hunks):
    end, parts = 0, []
    for a, b, replacement in hunks:
        if not end <= a <= b <= len(before):
            raise ValueError("Overlapping or invalid diff hunks")
        parts.extend([before[end:a], replacement])
        end = b
    return "".join(parts) + before[end:]


def witnessed_parent(item, texts):
    parents = [str(parent) for parent in item.get("parents", [])]
    if len(parents) != 1:
        return None
    witness = item.get("parent_text_witness")
    if witness is not None:
        if witness.get("revision") != parents[0] or not isinstance(witness.get("text"), str):
            raise ValueError("Parent text witness does not match the recorded parent")
        if parents[0] in texts and texts[parents[0]] != witness["text"]:
            raise ValueError("Parent text witnesses conflict")
    return texts.get(parents[0], witness["text"] if witness else None)


def ingest_history(payload, ledger, *, adapter, cancel=lambda: False):
    if payload["license"] not in LICENSES or not payload.get("license_evidence"):
        raise ValueError("History needs an allowlisted license and its evidence")
    snapshots = payload["revisions"]
    if not snapshots or len(snapshots) > 10000:
        raise ValueError("Expected a bounded nonempty revision history")
    artifact_id = payload["artifact_id"]
    source = payload["source_uri"]
    rows, makers, revisions, texts = [], {}, {}, {}
    for item in snapshots:
        if cancel():
            raise InterruptedError("History compilation cancelled")
        key = str(item["id"])
        if key in revisions or not isinstance(item["text"], str):
            raise ValueError("Duplicate revision or nontext content")
        ident = maker_id(adapter, str(item["maker"])) if item.get("maker") is not None else None
        if ident and ident not in makers:
            makers[ident] = Maker(
                maker_id=ident,
                source_dataset=adapter,
                identity="unknown" if item.get("unstable_identity") else "pseudonymous",
                display_label=item.get("label", "Source contributor"),
                identity_basis=["Source-scoped revision attribution"]
                + (
                    ["Unstable IP identity; not assumed to identify one person"]
                    if item.get("unstable_identity")
                    else []
                ),
            )
        t = datetime.fromisoformat(item["t"])
        revision_id = digest([adapter, artifact_id, key])
        parents = [str(x) for x in item.get("parents", [])]
        missing = [p for p in parents if p not in revisions]
        if any(p in {str(r["id"]) for r in snapshots} for p in missing):
            raise ValueError("Revision history must place parents before children")
        goal_ids = []
        if item.get("summary") and ident:
            goal_id = digest([revision_id, "stated-goal"])
            rows.append(
                StatedGoal(
                    goal_id=goal_id,
                    maker_id=ident,
                    scope="revision",
                    scope_id=revision_id,
                    text=item["summary"],
                    source="commit_message" if adapter == "git" else "edit_summary",
                    t=t,
                )
            )
            goal_ids.append(goal_id)
        revision = Revision(
            revision_id=revision_id,
            artifact_id=artifact_id,
            maker_id=ident,
            t=t,
            parent_revision_ids=[revisions[p].revision_id for p in parents if p in revisions],
            content_ref=ledger.put_text(item["text"]),
            stated_goal_ids=goal_ids,
        )
        for parent in parents[:1] if len(parents) == 1 else []:
            before = witnessed_parent(item, texts)
            if before is None or ident is None:
                continue
            after = item["text"]
            hunks = diff_hunks(before, after)
            if apply_hunks(before, hunks) != after:
                raise ValueError("Revision reconstruction failed")
            for index, (a, b, replacement) in enumerate(hunks):
                rows.append(
                    Correction(
                        correction_id=digest([revision_id, "hunk", index]),
                        maker_id=ident,
                        revision_id=revision_id,
                        before_ref=ledger.put_text(before[a:b]),
                        after_ref=ledger.put_text(replacement),
                        t=t,
                        stated_reason=item.get("summary"),
                    )
                )
        rows.append(revision)
        rows.append(
            Evidence(
                evidence_id=digest([revision_id, "source"]),
                source_uri=source,
                excerpt=item["text"][:1500],
                captured_at=t,
                relationship=f"Recorded {adapter} revision {key}; omitted boundary parents: {len(missing)}; "
                f"bot flag: {item.get('bot', 'unknown')}; license: {payload['license']}",
            )
        )
        revisions[key], texts[key] = revision, item["text"]
    rows.extend(makers.values())
    rows.append(
        Artifact(
            artifact_id=artifact_id,
            maker_ids=sorted(makers),
            kind="article",
            source_uri=source,
            revisions=[r.revision_id for r in revisions.values()],
            tier="T1",
        )
    )
    if cancel():
        raise InterruptedError("History compilation cancelled")
    ledger.append_new(rows, provenance_for(rows, adapter, digest(payload)))
    coverage = {
        m: {
            "revisions": sum(r.maker_id == m for r in revisions.values()),
            "summaries": sum(
                r.maker_id == m and bool(r.stated_goal_ids) for r in revisions.values()
            ),
        }
        for m in makers
    }
    return {
        "artifact_id": artifact_id,
        "tier": "T1",
        "revisions": len(revisions),
        "corrections": sum(isinstance(r, Correction) for r in rows),
        "summary_coverage": coverage,
        "license": payload["license"],
        "license_evidence": payload["license_evidence"],
    }
