"""Compile witnessed CoAuthor episodes; never turn accept into endorsement."""

import math
from datetime import UTC, datetime

from ..ledger.ids import digest, maker_id
from ..ledger.provenance import provenance_for
from ..ledger.schema import (
    Artifact,
    Correction,
    Cost,
    Decision,
    Maker,
    Option,
    Revision,
    Session,
    StatedGoal,
)
from .quill import delta_ops, text_of, units
from .relations import project
from .replay import replay


def _time(ms):
    if isinstance(ms, bool) or not isinstance(ms, (int, float)) or not math.isfinite(ms):
        raise ValueError("Missing or non-finite event timestamp")
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def census(events):
    result = replay(events)
    valid, excluded = [], []
    for episode in result["events"]:
        try:
            if not episode["usable"]:
                raise ValueError(episode["exclusion"] or "Document reconstruction failed")
            projection = project(episode, events)
            valid.append((episode, projection))
        except (ValueError, UnicodeError, AssertionError) as exc:
            excluded.append({"ordinal": episode["ordinal"], "reason": str(exc)})
    return result, valid, excluded


def compile_session(events, *, source_id, writer, prompt, source_hash, ledger, prompt_id=None):
    """Compile a session into records. Caller batches append and deduplicates Makers.

    Census excludes broken reconstruction/correspondence. Chronology is an
    additional gate; malformed clocks cannot silently turn source order into time.
    """
    result, episodes, excluded = census(events)
    times = [_time(e.get("eventTimestamp", e.get("timestamp"))) for e in events]
    if not times or times != sorted(times):
        raise ValueError("Nonmonotone or empty session chronology")
    if not result["reconstructed"]:
        raise ValueError("Session did not reconstruct")
    who = maker_id("coauthor", writer)
    sid = digest(["coauthor", source_id])
    aid = f"coauthor:session:{sid}"
    goal = digest([sid, "assignment"])
    revision = digest([aid, "final", result["final_document"]])
    rows = [
        Maker(
            maker_id=who,
            source_dataset="coauthor",
            identity="pseudonymous",
            display_label="CoAuthor writer",
            identity_basis=["Within-dataset worker ID"],
        ),
        Artifact(
            artifact_id=aid,
            maker_ids=[who],
            kind="session",
            source_uri=aid,
            revisions=[revision],
            tier="T2",
        ),
        Session(
            session_id=sid,
            maker_id=who,
            artifact_id=aid,
            t_start=times[0],
            t_end=times[-1],
            stated_goal_ids=[goal] if prompt else [],
        ),
        Revision(
            revision_id=revision,
            artifact_id=aid,
            maker_id=who,
            t=times[-1],
            content_ref=ledger.put_text(result["final_document"]),
            stated_goal_ids=[goal] if prompt else [],
        ),
    ]
    if prompt:
        rows.append(
            StatedGoal(
                goal_id=goal,
                maker_id=who,
                scope="session",
                scope_id=sid,
                text=prompt,
                source="assignment",
                t=times[0],
            )
        )
    previous = None
    for decision_index, (episode, projection) in enumerate(episodes):
        start, stop = episode["ordinal"], episode["cutoff_ordinal"]
        resolves = [
            i
            for i in range(start + 1, stop)
            if events[i].get("eventName") in ("suggestion-select", "suggestion-close")
        ]
        action = episode["decision"]
        resolution = resolves[-1] if resolves and action != "ignore" else None
        inserted = [
            (
                i,
                sum(
                    len(units(o["insert"]))
                    for o in delta_ops(events[i].get("textDelta"))
                    if "insert" in o
                ),
            )
            for i in range((resolution or start) + 1, stop)
            if events[i].get("eventSource") == "user"
        ]
        inserted = [(i, n) for i, n in inserted if n]
        if action == "ignore" and inserted:
            resolution = inserted[0][0]
        latency = None if resolution is None else (times[resolution] - times[start]).total_seconds()
        cursor = events[start].get("currentCursor")
        if type(cursor) is not int or not 0 <= cursor <= len(units(episode["document"])):
            excluded.append({"ordinal": start, "reason": "Missing or invalid UTF-16 cursor"})
            continue
        document = text_of(units(episode["document"])[:cursor])
        ident = digest([sid, start])
        options = [
            Option(
                option_id=f"{ident}:{o['index']}",
                origin="ai",
                position=j,
                content_ref=ledger.put_text(o["original"]),
            )
            for j, o in enumerate(episode["options"])
        ]
        options.append(Option(option_id=f"{ident}:own", origin="maker", position=len(options)))
        taken = None
        if episode["logged_index_agrees"]:
            taken = f"{ident}:{episode['selected_index']}"
        # Resolve only when the whole episode is available: edit versus accept
        # is a terminal label, not known at the instant of suggestion selection.
        rows.append(
            Decision(
                decision_id=ident,
                maker_id=who,
                session_id=sid,
                t_open=times[start],
                t_resolve=times[min(stop, len(times) - 1)],
                options=options,
                taken=taken,
                action=action,
                cost=Cost(latency_s=latency, chars_typed=sum(n for _, n in inserted)),
                context={
                    "document_ref": ledger.put_text(document),
                    "decision_index": decision_index,
                    "previous_handling": previous,
                    "prompt_id": prompt_id or (digest(prompt) if prompt else "unknown"),
                    "source_ordinal": start,
                    "matched_option_indices": episode["matched_option_indices"],
                },
                outcome={"reviewed": "unknown", "understood": "unknown", "endorsed": "unknown"},
            )
        )
        if action == "edit":
            matches = episode["matched_option_indices"]
            if matches:
                before = next(o["original"] for o in episode["options"] if o["index"] == matches[0])
                fragment = next(f for f in projection["facts"] if f["slot"] == "entry")
                after = "".join(episode["end_document"][a:b] for a, b in fragment["exact_spans"])
                rows.append(
                    Correction(
                        correction_id=digest([ident, "edit"]),
                        maker_id=who,
                        decision_id=ident,
                        before_ref=ledger.put_text(before),
                        after_ref=ledger.put_text(after),
                        t=times[min(stop, len(times) - 1)],
                    )
                )
        previous = action
    return rows, provenance_for(rows, "coauthor", source_hash), excluded
