"""Separate preview orchestration; the admitted packet builder is not changed."""

from copy import deepcopy
from datetime import UTC, datetime
from itertools import pairwise
from time import monotonic

from ..ledger.ids import digest
from ..packet.contract import Packet
from .habits import describe

NOTICE = "Research preview: these are the engine's guesses. Each one says what it's based on and whether it has been tested."
LABELS = {"evidenceStatus": "unvalidated", "basis": "text-surface"}


class BudgetExceeded(Exception):
    pass


def relative(value, meaning, scale=(0, 1)):
    return {"value": value, "scale": list(scale), "semantics": "relative", "meaning": meaning}


def hypothesis(packet, key, label, description, *, kind="process", regions=None, basis="text-surface", evidence_status="unvalidated", support=None, spans=None):
    regions = regions if regions is not None else [r["id"] for r in packet["artifact"]["regions"]]
    ident = digest([packet["artifact"]["revision"], "preview-v1", key])
    item = {
        "id": ident, "kind": kind, "label": label[:250], "description": description[:4000],
        "makers": [packet["makers"][0]["id"]], "regions": regions,
        "status": "hypothesis", "evidence": [e["id"] for e in packet["evidence"] if e["id"] in {digest([packet["artifact"]["revision"], rid]) for rid in regions}],
        "basis": basis, "evidenceStatus": evidence_status,
        "interpretation": {"process": "repertoire", "attention": "current-attention", "goal": "local-goal", "value": "value"}[kind],
    }
    if support is not None:
        item["support"] = support
    if spans:
        item["spans"] = spans
    packet["hypotheses"].append(item)
    if kind == "process":
        packet["process"]["nodes"].append(ident)
    return item


def habits(packet, check):
    values = describe(packet["artifact"], check)
    regions = packet["artifact"]["regions"]
    for repeat in values["repeats"]:
        matching = [r["id"] for r in regions if repeat["label"] in r["anchor"]["exact"].lower()]
        hypothesis(packet, ["repeat", repeat["label"]], repeat["label"],
                   f"Occurs {repeat['count']} times outside recognizable quotation marks; mean {repeat['baseline']:.2f} in 12 seeded shuffles of this page's unquoted words. This describes the text, not a stable personal habit.", regions=matching)
    hypothesis(packet, "rhythm", "Sentence rhythm",
               f"{values['sentenceCount']} sentences outside recognizable quotations; mean {values['sentenceMean']:.1f} words, standard deviation {values['sentenceSpread']:.1f}. {values['quotedWords']} quoted words held apart. Sentence and quotation boundaries are heuristic.")
    for key, label in (("connectives", "Connectives"), ("punctuation", "Punctuation")):
        if values[key]:
            hypothesis(packet, key, label, "; ".join(f"{k}: {v}" for k, v in values[key].items()) + ". Counts outside recognizable quotation marks, in this page only.")


def render_deviation(packet, reader, result, covered):
    if reader.identity not in packet["preview"]["readers"]:
        packet["preview"]["readers"].append(reader.identity)
    old = {h["id"] for h in packet["hypotheses"] if h.get("description", "").startswith("Where this text went somewhere")}
    packet["hypotheses"] = [h for h in packet["hypotheses"] if h["id"] not in old]
    packet["process"]["nodes"] = [ident for ident in packet["process"]["nodes"] if ident not in old]
    for frame in packet.get("currentAttention", []):
        frame["items"] = [i for i in frame["items"] if i["hypothesis"] not in old]
    packet["currentAttention"] = [f for f in packet.get("currentAttention", []) if f["items"]]
    packet["preview"]["statistics"] = result["statistics"]
    packet["preview"]["coverage"] = covered
    coverage = f"Finished {len(covered)} of {len(packet['artifact']['regions'])} passages. Rankings and normalization cover processed text only, including any partial passage, and can change as coverage expands. "
    scale = (min(-1, *(row["departure"] for row in result["attention"])), max(1, *(row["departure"] for row in result["attention"])))
    emitted = set()
    for row in result["attention"]:
        key = (row["region"], row["start"], row["end"])
        # A short phrase can also be its entire sentence. It has one source
        # span and must keep one stable hypothesis, even as rankings change.
        if key in emitted:
            continue
        emitted.add(key)
        span = {"region": row["region"], "start": row["start"], "end": row["end"]}
        matching = [r for r in packet["artifact"]["regions"] if r["id"] in covered and row["text"].casefold() in r["anchor"]["exact"].casefold()]
        sections = {r.get("pageHint", {}).get("section") or r["id"] for r in matching}
        recurring = row["departure"] > 0 and len(sections) >= 2
        score = relative(row["departure"], "Departure from this page's median content-word surprisal, in page interquartile ranges; not a probability.", scale)
        item = hypothesis(packet, ["departure", row["region"], row["start"], row["end"]], ("Signature: " if recurring else "") + row["text"],
                          f"Where this text went somewhere a typical writer wouldn't. A proxy for the author's choices; not measured attention. Departure {row['departure']:.3f}; {reader.identity['id']} at {reader.identity['revision']}, file manifest SHA-256 {reader.identity['sha256']}.",
                          kind="process" if recurring else "attention", regions=[r["id"] for r in matching] if recurring else [row["region"]], support=score, spans=[span])
        item["description"] += (" Signature (habit or deliberate style). Recurrence across this page's sections stands in for recurrence across a writer's work; paragraph regions are used when section metadata is absent. What would move this estimate: under time pressure, which way would they go? Probe untested (Ghost N11 pending)." if recurring else " Where attention likely went; untested. What would move this estimate: after a source fails them, do they check it more? Probe pending (D39/N15).")
        item["description"] += " " + coverage
        if not recurring:
            packet.setdefault("currentAttention", []).append({"maker": item["makers"][0], "span": span, "items": [{"hypothesis": item["id"], "support": score, **LABELS}]})
    partition_attention(packet)
    return result


def deviation(packet, reader, check):
    from .surface import deviation_map
    return render_deviation(packet, reader, deviation_map(packet["artifact"], reader, check), [r["id"] for r in packet["artifact"]["regions"]])


def deviation_steps(packet, reader, check, publish):
    from .judgments import advance
    from .surface import score_regions, summarize_deviation
    rows = []
    rendered_at = None
    total = len(packet["artifact"]["regions"])
    advance(packet, "deviation", 0, total, "passages")
    for row in score_regions(packet["artifact"], reader, check, priority=packet["preview"].get("priorityRegion")):
        rows = [r for r in rows if r["region"] != row["region"]] + [row]
        covered = [r["region"] for r in rows if r["complete"]]
        advance(packet, "deviation", len(covered), total, "passages")
        # A code-only passage is valid coverage, but has no content-word statistic.
        if (rendered_at is None or monotonic() - rendered_at >= .75 or len(covered) == total) and any(w["content"] and not w["held"] for r in rows for w in r["words"]):
            render_deviation(packet, reader, summarize_deviation(rows, check), covered)
            rendered_at = monotonic()
        publish()
        yield


def agreement_steps(packet, readers, check, publish):
    from .judgments import advance
    from .surface import agreement_from_tables, score_regions
    tables = {condition: [[], []] for condition in ("short", "full")}
    total = len(packet["artifact"]["regions"]) * 4
    completed = 0
    advance(packet, "agreement", 0, total, "passage readings")
    since_yield = monotonic()
    for condition in tables:
        for index, reader in enumerate(readers):
            if reader.identity not in packet["preview"]["readers"]:
                packet["preview"]["readers"].append(reader.identity)
            for row in score_regions(packet["artifact"], reader, check, short=condition == "short"):
                if row["complete"]:
                    tables[condition][index].append(row)
                    completed += 1
                advance(packet, "agreement", completed, total, "passage readings")
                publish()
                # Replaying many cached rows should not revalidate/copy the
                # entire essay after each tiny progress increment. Slow model
                # work still yields immediately; fast replay yields within
                # 50 ms or 16 completed rows. Every published packet is validated.
                if monotonic() - since_yield >= .05 or completed % 16 == 0:
                    yield
                    since_yield = monotonic()
    packet["preview"]["agreement"] = agreement_from_tables(packet["artifact"], tables)
    publish()


def partition_attention(packet):
    """Represent overlapping phrase/sentence findings as non-overlapping frames.

    Preserve each finding's own source span on its hypothesis. Frame partitions
    carry all findings covering that interval, compatible with the existing UI.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for frame in packet.get("currentAttention", []):
        groups[(frame["maker"], frame["span"]["region"])].append(frame)
    frames = []
    for (maker, region), group in groups.items():
        cuts = sorted({offset for frame in group for offset in (frame["span"]["start"], frame["span"]["end"])})
        for start, end in pairwise(cuts):
            items = {item["hypothesis"]: item for frame in group if frame["span"]["start"] <= start and frame["span"]["end"] >= end for item in frame["items"]}
            if items:
                if len(items) > 40:
                    raise ValueError("Attention overlap exceeds the explicit frame bound")
                frames.append({"maker": maker, "span": {"region": region, "start": start, "end": end}, "items": list(items.values())})
    packet["currentAttention"] = frames


def build_preview(base, *, readers=(), goal_runner=None, technique_runner=None, history=None, history_adapter="wikipedia", correction_reader=None, progress=lambda _: None, partial=lambda _: None, check=lambda: None, deadline=None, history_error=None, priority_region=None):
    deadline = deadline if deadline is not None else monotonic() + 165
    packet = deepcopy(base)
    packet["schemaVersion"] = "1.8"
    packet["id"] = digest([base["id"], "research-preview-v1", [r.identity for r in readers]])
    packet["provider"].update(mode="preview", previewNotice=NOTICE)
    packet["provider"]["method"] = "Research preview; surface descriptions and local reader judgments. " + packet["provider"]["method"][:850]
    # Even an upstream admitted packet must not turn topic features into drive
    # measurements in the preview. Retain separately fitted feature preferences.
    mapped = {h["id"] for h in packet["hypotheses"] if h.get("preferenceEstimate", {}).get("quantity") == "Revealed-theme contrast from population"}
    packet["hypotheses"] = [h for h in packet["hypotheses"] if h["id"] not in mapped]
    if packet.get("population"):
        packet["population"]["items"] = [row for row in packet["population"]["items"] if row["hypothesis"] not in mapped]
    # Existing observed records are evidence, not validation of psychological inference.
    for row in packet["hypotheses"]:
        row.update(evidenceStatus="unvalidated", basis=("choices" if row.get("preferenceEstimate") else "population") if row["kind"] == "value" else "history")
    for node in packet.get("goalHierarchy", {}).get("nodes", []):
        node.update(evidenceStatus="unvalidated", basis="model-judgment")
    for frame in packet.get("currentAttention", []):
        for item in frame["items"]:
            item.update(evidenceStatus="unvalidated", basis="history")
    # Do not rebrand a calibrated probability as a preview confidence.
    def relative_only(value):
        if isinstance(value, dict):
            if value.get("semantics") == "probability":
                value["semantics"] = "relative"
                value["meaning"] = "Relative support in research preview; no probability claim."
                value.pop("calibration", None)
            for child in value.values():
                relative_only(child)
        elif isinstance(value, list):
            for child in value:
                relative_only(child)
    relative_only(packet)
    modules = [
        {"id": "habits", "title": "Text habits", "status": "pending", "detail": "This page's repeated phrasing, rhythm and punctuation."},
        {"id": "deviation", "title": "Deviation map", "status": "pending", "detail": "Local population reader; not measured attention."},
        {"id": "agreement", "title": "Two readers", "status": "pending", "detail": "Compare short and full context; agreement is not correctness."},
        {"id": "payoff", "title": "Payoff map", "status": "pending", "detail": "Earlier context, shuffled controls and novel spans; not measured enjoyment."},
        {"id": "techniques", "title": "Technique notes", "status": "pending", "detail": "Q1, Q3, Q4, Q5 and Q7 only."},
        {"id": "goals", "title": "Goal tree", "status": "pending", "detail": "Local judgments with stated root cues."},
        {"id": "values", "title": "Core values", "status": "complete" if packet.get("population", {}).get("items") else "unavailable", "detail": "Choices, content corrections, stated goals and revision history would move these estimates. No numerical drive prior is supplied; text topics are never converted to drives."},
    ]
    packet["preview"] = {"modules": modules, "readers": [], "rootCueReliability": .6, "rootCueStatus": "assumed", "budgetDrops": []}
    from .findings import findings
    packet["globalFindings"] = findings()
    if priority_region in {r["id"] for r in packet["artifact"]["regions"]}:
        packet["preview"]["priorityRegion"] = priority_region
    from .judgments import goal_groups
    packet["preview"]["layoutGroups"] = [[r["id"] for r in group] for group in goal_groups(packet["artifact"]["regions"], priority_region)]
    from .makers import correction_steps, decorate
    if history:
        history = deepcopy(history)
        cutoff = datetime.fromisoformat(packet["artifact"]["capturedAt"])
        history["revisions"] = [r for r in history["revisions"] if datetime.fromisoformat(r["t"]) <= cutoff]
        if not history["revisions"]:
            history = None
    decorate(packet, history, adapter=history_adapter)
    if history:
        modules.append({"id": "corrections", "title": "Content corrections", "status": "pending", "detail": "Content and housekeeping labels; no inferred values."})
        packet["preview"]["historySource"] = "github" if history_adapter == "git" else "wikipedia"
    if history_error:
        modules.append({"id": "history", "title": "Source history", "status": "unavailable", "detail": history_error})

    metric_sources = [*readers, goal_runner, technique_runner]
    metric_sources = [s for i, s in enumerate(metric_sources) if s is not None and hasattr(s, "metrics") and all(getattr(other, "metrics", None) is not s.metrics for other in metric_sources[:i])]
    metric_starts = [dict(s.metrics) for s in metric_sources]
    validated = None
    last_sent = 0.0
    last_signature = None
    def publish(force=False):
        nonlocal validated, last_sent, last_signature
        check()
        signature = (len(packet["hypotheses"]), len(packet.get("goalHierarchy", {}).get("nodes", [])), tuple(m["status"] for m in modules))
        # Coalesce cached replay/progress. Validate every observable packet and
        # preserve a rollback point, without copying the entire essay per token.
        if not force and validated is not None and signature == last_signature and monotonic() - last_sent < .75:
            return
        packet["preview"]["timings"] = {f"reader{i}.{key}": max(0, value - metric_starts[i].get(key, 0)) for i, source in enumerate(metric_sources) for key, value in source.metrics.items()}
        from .makers import hide_usernames
        visible = hide_usernames(Packet.model_validate(packet).wire())
        validated = deepcopy(packet)
        partial(visible)
        last_sent, last_signature = monotonic(), signature

    def restore(target, source):
        # Preserve objects held by other suspended generators during rollback.
        if isinstance(target, dict) and isinstance(source, dict):
            for key in list(target):
                if key not in source:
                    del target[key]
            for key, value in source.items():
                # Partitioned attention frames share item objects. Their list
                # positions can change between snapshots, so in-place restoration
                # would overwrite an item still used by another source region.
                # No suspended module retains references to this rendered tree.
                if key == "currentAttention":
                    target[key] = deepcopy(value)
                elif key in target and isinstance(value, (dict, list)) and isinstance(target[key], type(value)):
                    restore(target[key], value)
                else:
                    target[key] = deepcopy(value)
        elif isinstance(target, list) and isinstance(source, list):
            originals = {}
            for item in target:
                if isinstance(item, dict) and "id" in item:
                    originals.setdefault(item["id"], item)
            replacement = []
            for index, item in enumerate(source):
                old = originals.get(item.get("id")) if isinstance(item, dict) and "id" in item else target[index] if index < len(target) else None
                if isinstance(item, (dict, list)) and isinstance(old, type(item)):
                    restore(old, item)
                    replacement.append(old)
                else:
                    replacement.append(deepcopy(item))
            target[:] = replacement

    def synchronous(operation):
        operation()
        yield

    active = []
    def enqueue(ident, factory, absent):
        module = next(m for m in modules if m["id"] == ident)
        if factory is None:
            module.update(status="unavailable", detail=absent)
            return
        state = {"module": module, "spent": 0.0}
        stage_seconds = 25 if ident == "agreement" else 60 if ident == "payoff" else 45 if history and ident in {"corrections", "techniques"} else 90
        def bounded():
            check()
            if monotonic() >= min(deadline, state.get("until", deadline)):
                raise BudgetExceeded()
        state.update(iterator=factory(bounded), limit=stage_seconds)
        active.append(state)

    def runner_steps(runner, bounded):
        if hasattr(runner, "steps"):
            return runner.steps(packet, bounded, publish)
        return synchronous(lambda: runner(packet, bounded, publish))

    enqueue("habits", lambda bounded: synchronous(lambda: habits(packet, bounded)), "")
    enqueue("deviation", (lambda bounded: deviation_steps(packet, readers[0], bounded, publish)) if readers else None,
            "Install and pin Qwen2.5-0.5B locally to enable the deviation map. Analysis never downloads a model.")
    enqueue("goals", (lambda bounded: runner_steps(goal_runner, bounded)) if goal_runner else None,
            "No local goal producer is configured. A title alone does not establish the maker's purpose.")
    enqueue("techniques", (lambda bounded: runner_steps(technique_runner, bounded)) if technique_runner else None,
            "No local technique reader is configured. Exact fixed-reader badges require their matching receipts.")
    enqueue("agreement", (lambda bounded: agreement_steps(packet, readers[:2], bounded, publish)) if len(readers) >= 2 else None,
            "Install and pin SmolLM2-360M alongside Qwen to compare readers.")
    from .payoff import payoff_steps
    enqueue("payoff", (lambda bounded: payoff_steps(packet, readers[0], bounded, publish)) if readers else None,
            "The pinned local population reader must be installed before payoff can be scored.")
    if history:
        enqueue("corrections", (lambda bounded: correction_steps(packet, history, correction_reader, bounded, publish, adapter=history_adapter)) if correction_reader else None,
                "No exact fixed-Qwen correction reader is configured. Observed revisions remain available.")
    publish()
    def shed_optional():
        order = ["payoff-layer-2", "second-reader", "techniques-after-30", "governing-call"]
        drops = packet["preview"]["budgetDrops"]
        if len(drops) < len(order):
            drops.append(order[len(drops)])
    try:
        while active:
            for state in active.copy():
                check()
                module = state["module"]
                start = monotonic()
                if module["id"] == "agreement" and "second-reader" in packet["preview"]["budgetDrops"]:
                    module.update(status="skipped", detail="Second reader deferred by the measured live time budget; completed scores remain cached.")
                    state["iterator"].close()
                    active.remove(state)
                    publish()
                    continue
                if start >= deadline or state["spent"] >= state["limit"]:
                    shed_optional()
                    module.update(status="skipped", detail="Paused at the time budget. Continue reading reuses exact completed calls; unfinished work remains unknown.")
                    state["iterator"].close()
                    active.remove(state)
                    publish()
                    continue
                module["status"] = "running"
                if state["spent"] == 0:
                    progress(module["title"])
                state["until"] = min(deadline, start + state["limit"] - state["spent"])
                publish()
                try:
                    next(state["iterator"])
                    check()
                    Packet.model_validate(packet)
                except StopIteration:
                    module["status"] = "complete"
                    active.remove(state)
                except Exception as exc:
                    check()  # Cancellation must escape, never become a module failure.
                    restore(packet, validated)
                    if isinstance(exc, BudgetExceeded):
                        shed_optional()
                    module.update(status="skipped" if isinstance(exc, BudgetExceeded) else "failed",
                                  detail="Paused at the time budget. Continue reading reuses completed work." if isinstance(exc, BudgetExceeded) else f"{module['title']} could not finish ({type(exc).__name__}); completed results remain available.")
                    state["iterator"].close()
                    active.remove(state)
                    if not isinstance(exc, BudgetExceeded):
                        import logging
                        logging.getLogger("tompathy_engine").exception("Preview module %s failed", module["id"])
                state["spent"] += monotonic() - start
                module["elapsedMs"] = round(state["spent"] * 1000, 2)
                publish()
    finally:
        for state in active:
            state["iterator"].close()
    packet["preview"]["resumable"] = any(m["status"] == "skipped" for m in modules)
    packet["preview"]["completedAt"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    from .makers import hide_usernames
    return hide_usernames(Packet.model_validate(packet).wire())
