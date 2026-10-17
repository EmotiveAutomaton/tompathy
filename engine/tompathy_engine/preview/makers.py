"""Evidence-first makers. No statistical authorship classification."""

import re
from collections import defaultdict

from ..adapters.history import diff_hunks, witnessed_parent
from ..ledger.ids import digest, maker_id


def hide_usernames(packet):
    """Keep usernames solely in the local reveal field; never rewrite anchors."""
    names = sorted(((m["localLabel"], m["label"]) for m in packet["makers"] if m.get("localLabel")), key=lambda pair: -len(pair[0]))
    def visit(value, key=""):
        if key in {"localLabel", "artifact", "span", "spans", "revisions", "id", "source", "revision", "excerpt"}:
            return value
        if isinstance(value, str):
            for name, alias in names:
                value = re.sub(r"(?<!\w)" + re.escape(name) + r"(?!\w)", lambda _, alias=alias: alias, value)
            return value
        if isinstance(value, list):
            return [visit(child) for child in value]
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        return value
    return visit(packet)


def decorate(packet, history=None, adapter="wikipedia"):
    packet["schemaVersion"] = "1.9"
    if not history:
        for maker in packet["makers"]:
            maker.update(kind="unknown", evidence=[], label="Author (unresolved)", relationship="No generative provenance was found in this capture. Page bylines do not establish a creation process.")
        return
    stats, texts = {}, {}
    for revision in history["revisions"]:
        ident = maker_id(adapter, str(revision["maker"])) if revision.get("maker") is not None else None
        if ident:
            record = stats.setdefault(ident, {"bytes": 0, "revisions": [], "bot": False, "label": revision.get("label", "Unidentified editor"), "summaries": []})
            record["revisions"].append(str(revision["id"]))
            record["bot"] |= revision.get("bot") is True
            if revision.get("summary"):
                record["summaries"].append(revision["summary"])
            before = witnessed_parent(revision, texts)
            if before is not None:
                record["bytes"] += sum(len(before[a:b].encode("utf8")) + len(replacement.encode("utf8")) for a, b, replacement in diff_hunks(before, revision["text"]))
        texts[str(revision["id"])] = revision["text"]
    order = sorted(stats, key=lambda ident: (-stats[ident]["bytes"], ident))
    for maker in packet["makers"]:
        row = stats.get(maker["id"])
        if row is None:
            maker.update(kind="unknown", evidence=[], label="Author (unresolved)", relationship="No attributable history at or before this capture.")
            continue
        maker.update(label=f"{'Editor' if adapter == 'wikipedia' else 'Contributor'} {order.index(maker['id']) + 1}", localLabel=row["label"][:250],
                     kind="bot" if row["bot"] else "person", bytesChanged=row["bytes"], revisions=row["revisions"][-500:],
                     evidence=[{"tier": "declared", "source": "Wikipedia revision attribution" if adapter == "wikipedia" else "Git commit attribution",
                                "detail": "Source-scoped attribution, not a verified identity. " + ("Explicit bot flag present." if row["bot"] else "No explicit bot flag supplied."), "evidenceStatus": "unvalidated"}])
    packet["makers"].sort(key=lambda m: (-m.get("bytesChanged", 0), m["id"]))
    # Whole-page surface readings cannot be assigned to the last or biggest editor.
    unresolved = {"id": digest(["surface-maker", packet["artifact"]["id"]]), "label": "Artifact (unattributed text)", "identity": "unknown", "kind": "unknown", "evidence": [],
                  "relationship": "Whole-page surface descriptions; no word-level authorship is inferred from revision counts."}
    packet["makers"].insert(0, unresolved)
    if adapter == "git":
        tools = {}
        for revision in history["revisions"]:
            for tool in revision.get("declared_tools", []):
                ident = digest(["declared-git-tool", packet["artifact"]["id"], tool["label"]])
                maker = tools.setdefault(ident, {"id": ident, "label": tool["label"], "identity": "supplied", "kind": tool["kind"],
                                                 "relationship": "Unsigned, editable commit declaration; not proof of use or word-level authorship.",
                                                 "evidence": [], "decisions": {"drafted": 0}, "revisions": []})
                if revision["id"] not in maker["revisions"]:
                    maker["revisions"].append(revision["id"])
                    maker["decisions"]["drafted"] += 1
                witness = {"tier": "declared", "source": "git trailer", "detail": tool["detail"], "evidenceStatus": "unvalidated"}
                if witness not in maker["evidence"] and len(maker["evidence"]) < 100:
                    maker["evidence"].append(witness)
        packet["makers"].extend(tools.values())
        packet["preview"]["github"] = {"quotaRemaining": history.get("quotaRemaining"), "commits": len(history["revisions"]),
                                         "declaredAiCommitShare": sum(bool(r.get("declared_tools")) for r in history["revisions"]) / len(history["revisions"])}
        for maker in packet["makers"]:
            if maker["id"] in stats:
                maker["decisions"] = {"commits": len(stats[maker["id"]]["revisions"])}
    summaries = [r.get("summary") for r in history["revisions"] if r.get("summary")]
    if summaries:
        packet["preview"]["latestSummary"] = summaries[-1][:2000]
    if adapter == "wikipedia":
        from ..adapters.wiki import revert_outcomes
        reverts = revert_outcomes(history["revisions"])
        for maker in packet["makers"]:
            if maker["id"] in stats:
                maker["decisions"] = {"reverted": sum(bool(reverts.get(r) and reverts[r]["reverted_within_48h"]) for r in stats[maker["id"]]["revisions"])}
        latest_tags = history["revisions"][-1].get("tags", [])
        if latest_tags:
            packet["preview"]["latestSummary"] = (packet["preview"].get("latestSummary", "") + " Source revision tags: " + ", ".join(latest_tags))[:2000]


def correction_steps(packet, history, reader, check, publish, adapter="wikipedia"):
    from ..transcribe.admission import metrics_pass
    from .build import hypothesis
    for question in ("Q8", "Q9"):
        receipt = getattr(reader, "admissions", {}).get(question)
        if receipt and (not receipt.get("passed") or not metrics_pass(receipt, question)):
            raise ValueError(f"{question} failed the engine question gate; correction classification stays off")
    texts, counts, directions = {}, defaultdict(lambda: {"edited": 0, "housekeeping": 0}), defaultdict(lambda: defaultdict(int))
    calls = 0
    emitted = set()
    observed = {m["id"]: sorted({e for h in packet["hypotheses"] if m["id"] in h["makers"] for e in h["evidence"]}) for m in packet["makers"]}

    def flush():
        packet["hypotheses"] = [h for h in packet["hypotheses"] if h["id"] not in emitted]
        packet["process"]["nodes"] = [n for n in packet["process"]["nodes"] if n not in emitted]
        emitted.clear()
        for maker in packet["makers"]:
            ident = maker["id"]
            if ident not in counts:
                continue
            maker["decisions"] = {**maker.get("decisions", {}), **counts[ident]}
            for label, count in sorted(directions[ident].items(), key=lambda row: (-row[1], row[0]))[:2]:
                h = hypothesis(packet, ["correction-direction", ident, label], f"{label}: {count}",
                               "Direction counted only among completed fixed-reader classifications (Q8 outside typo/grammar/unclear, Q9 yes). Partial coverage; an unvalidated correction description, not an inferred value or verified intent.", basis="corrections", regions=[])
                h["makers"], h["evidence"] = [ident], observed[ident]
                emitted.add(h["id"])
        next(m for m in packet["preview"]["modules"] if m["id"] == "corrections")["detail"] = f"{calls} completed literal calls, capped at 100. Counts cover completed Q8/Q9 pairs only; unclassified changes remain unknown."
        publish()

    for revision in history["revisions"]:
        check()
        ident = maker_id(adapter, str(revision["maker"])) if revision.get("maker") is not None else None
        before = witnessed_parent(revision, texts)
        if ident and before is not None:
            for a, b, replacement in diff_hunks(before, revision["text"]):
                if calls + 2 > 100 or max(b - a, len(replacement)) > 12000:
                    continue
                check()
                with reader.backend.checking(check):
                    q8 = reader.ask("Q8", context="", text=replacement, before=before[a:b], admission_test=True)["answer"]
                    check()
                    q9 = reader.ask("Q9", context="", text=replacement, before=before[a:b], admission_test=True)["answer"]
                calls += 2
                if q8 in {"typo", "grammar"}:
                    counts[ident]["housekeeping"] += 1
                elif q8 != "unclear" and q9 == "yes":
                    counts[ident]["edited"] += 1
                    # Observable edit direction; never convert text themes to values.
                    direction = "Added content" if len(replacement) > b - a else "Removed content" if len(replacement) < b - a else "Replaced content"
                    directions[ident][direction] += 1
                flush()
                yield
        texts[str(revision["id"])] = revision["text"]
    flush()
    return calls


def correction_notes(*args, **kwargs):
    for _ in correction_steps(*args, **kwargs):
        pass
