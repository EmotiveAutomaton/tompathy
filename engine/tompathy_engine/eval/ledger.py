"""Observed ledger -> model inputs; outcome dictionaries are never features."""

import numpy as np

from ..features.deterministic import option_features
from ..models.backbone import Choice
from ..models.reference import ACTIONS, features


def handling_records(ledger, *, domain="writing"):
    artifacts = {a.artifact_id: a for a in ledger.rows("Artifact")}
    sessions = {s.session_id: s for s in ledger.rows("Session")}
    out = []
    for row in sorted(ledger.rows("Decision"), key=lambda r: (r.t_open, r.decision_id)):
        if (
            artifacts[sessions[row.session_id].artifact_id].domain != domain
            or row.action not in ACTIONS
        ):
            continue
        out.append(
            {
                "key": row.decision_id,
                "writer": row.maker_id,
                "session": row.session_id,
                "prompt": row.context.get("prompt_id", "unknown"),
                "open_at": row.t_open.isoformat(),
                "resolved_at": row.t_resolve.isoformat(),
                "handling": row.action,
                "document": ledger.get_text(row.context["document_ref"])
                if row.context.get("document_ref")
                else "",
                "menu": [
                    ledger.get_text(o.content_ref)
                    for o in row.options
                    if o.origin == "ai" and o.content_ref
                ],
                "decision_index": row.context.get("decision_index", 0),
                "previous_handling": row.context.get("previous_handling"),
                "effort": {
                    "decide_seconds": row.cost.latency_s,
                    "chars_typed_after": row.cost.chars_typed or 0,
                },
            }
        )
    return out


def choices(ledger, *, domain="writing", task="options"):
    stable = {m.maker_id for m in ledger.rows("Maker") if m.identity != "unknown"}
    if task == "handling":
        from datetime import datetime

        out = []
        for r in handling_records(ledger, domain=domain):
            if r["writer"] not in stable:
                continue
            x = features(r, [], False)
            # Four declared handling actions, with action-specific contextual utilities.
            matrix = np.zeros((4, 4 * len(x)))
            for action in range(4):
                matrix[action, action * len(x) : (action + 1) * len(x)] = x
            out.append(
                Choice(
                    r["key"],
                    r["writer"],
                    datetime.fromisoformat(r["open_at"]),
                    datetime.fromisoformat(r["resolved_at"]),
                    matrix,
                    ACTIONS.index(r["handling"]),
                    r["prompt"],
                )
            )
        return out
    if task != "options":
        raise ValueError("Unknown choice task")
    artifacts = {a.artifact_id: a for a in ledger.rows("Artifact")}
    sessions = {s.session_id: s for s in ledger.rows("Session")}
    rows = []
    for r in ledger.rows("Decision"):
        if (
            artifacts[sessions[r.session_id].artifact_id].domain != domain
            or r.taken is None
            or r.action == "rate"
            or r.maker_id not in stable
        ):
            continue
        context = (
            ledger.get_text(r.context["document_ref"]) if r.context.get("document_ref") else ""
        )
        # Do not mix text-menu features into a chess model; a domain adapter
        # must supply its explicit pre-decision move features.
        if domain == "chess":
            if not all(o.features for o in r.options):
                continue
            names = sorted(r.options[0].features)
            if any(sorted(o.features) != names for o in r.options):
                raise ValueError("Inconsistent offered move features")
            x = [[o.features[n] for n in names] for o in r.options]
        else:
            x = []
            for o in r.options:
                f = option_features(
                    ledger.get_text(o.content_ref) if o.content_ref else "", context, o.position
                )
                x.append(list(f.values()))
        rows.append(
            Choice(
                r.decision_id,
                r.maker_id,
                r.t_open,
                r.t_resolve,
                np.array(x),
                next(i for i, o in enumerate(r.options) if o.option_id == r.taken),
                r.context.get("prompt_id", "unknown"),
            )
        )
    return rows
