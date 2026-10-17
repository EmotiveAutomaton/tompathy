"""Bounded local goal judgments and exact fixed-Qwen technique notes."""

import json
from copy import deepcopy
from math import ceil

from ..ledger.ids import digest
from ..models.goal_producer import SCHEMA, TEMPLATE
from ..models.goals import Candidate
from ..transcribe.runner import Transcriber
from .build import hypothesis, relative

QUESTIONS = ("Q1", "Q3", "Q4", "Q5", "Q7")
NAMES = {"Q1": "Topic continuity", "Q3": "Register", "Q4": "Tone change", "Q5": "Dialogue", "Q7": "Contradiction"}


def stepped(steps):
    """Keep the synchronous API for offline callers; live scheduling uses steps."""
    def run(*args, **kwargs):
        for _ in steps(*args, **kwargs):
            pass
    run.steps = steps
    return run


def advance(packet, ident, completed, total, unit):
    next(m for m in packet["preview"]["modules"] if m["id"] == ident).update(
        completed=completed, total=total, unit=unit)


def fixed_reader(backend, cache, admissions=()):
    # Earlier Sounding Line receipts have a different pin and weaker gate.
    # Keep them archived; only fresh engine receipts can earn a tested badge.
    from .fixed_backend import DIGEST, OPTIONS, RUNTIME
    if backend.model_digest != DIGEST or any(backend.settings.get(k) != v for k, v in OPTIONS.items()) or backend.settings.get("runtime") != RUNTIME:
        raise ValueError("Fixed-reader model/runtime/settings differ from its configured identity")
    return Transcriber(backend, cache, admissions)


def techniques(reader):
    @stepped
    def run(packet, check, publish):
        regions = packet["artifact"]["regions"]
        completed = 0
        advance(packet, "techniques", 0, min(20, len(regions)) * len(QUESTIONS), "checks")
        for index, region in enumerate(regions[:20]):
            text = region["anchor"]["exact"]
            if len(text) > 12000:
                continue
            context = regions[index - 1]["anchor"]["exact"] if index else ""
            for question in QUESTIONS:
                receipt = reader.admissions.get(question)
                from ..transcribe.admission import metrics_pass
                if receipt and (not receipt.get("passed") or not metrics_pass(receipt, question)):
                    continue
                check()
                with reader.backend.checking(check):
                    result = reader.ask(question, context=context, text=text, admission_test=True)
                tested = bool(receipt and receipt.get("transcriber_pin") == reader.pin and metrics_pass(receipt, question))
                hypothesis(packet, ["technique", region["id"], question], f"{NAMES[question]}: {result['answer']}",
                           f"{question}, original fixed Qwen 3.5 9B reader. {"Lab-tested on templated items" if tested else "Untested under the engine gate"}; no natural-data admission. Reader pin {reader.pin}. Context is the preceding paragraph's last 1,200 characters.",
                           regions=[region["id"]], basis="text-surface", evidence_status="constructed-tested" if tested else "unvalidated")
                completed += 1
                advance(packet, "techniques", completed, min(20, len(regions)) * len(QUESTIONS), "checks")
                publish()
                yield
        module = next(m for m in packet["preview"]["modules"] if m["id"] == "techniques")
        module["detail"] = f"{completed} literal calls, bounded at 100; first {min(20, len(regions))} of {len(regions)} paragraphs considered. Paragraphs over 12,000 characters are skipped without truncation. Q6 and Q10 disabled. Constructed tests do not establish natural-text accuracy."
    # Admission receipts change which calls run and how their evidence is labeled.
    # Raw answer caches retain the reader pin; rendered packets must also pin gates.
    run.identity = digest([reader.pin, reader.admissions])
    run.metrics = getattr(reader.backend, "metrics", {})
    return run


def goals(backend, cache):
    @stepped
    def run(packet, check, publish):
        capture = packet["artifact"]
        regions = capture["regions"]
        groups = goal_groups(regions, packet["preview"].get("priorityRegion"))
        advance(packet, "goals", 0, len(groups) + 1, "groups")
        cues = [{"goal_id": "page-title", "text": capture["title"]}]
        cues += [{"goal_id": f"heading-{r['id']}", "text": r["anchor"]["exact"]} for r in regions if 1 <= r.get("pageHint", {}).get("heading", 99) <= 3]
        if capture.get("metaDescription"):
            cues.append({"goal_id": "meta-description", "text": capture["metaDescription"]})
        if packet["preview"].get("latestSummary"):
            cues.append({"goal_id": "latest-revision-summary", "text": packet["preview"]["latestSummary"]})
        # Bounded cue list, with truncation explicit in the resulting description.
        cues = cues[:30]
        schema = deepcopy(SCHEMA)
        schema["properties"]["cue_ids"].update(maxItems=min(5, len(cues)), items={"type": "string", "enum": [c["goal_id"] for c in cues]})
        schema["properties"]["label"]["maxLength"] = 120
        schema["properties"]["description"]["maxLength"] = 600
        prompt = TEMPLATE + " Keep the label under twelve words and the description under forty words. cue_ids must contain exact supplied goal_id values; if empty, cue_match must be zero."
        maker = packet["makers"][0]["id"]
        children = []
        packet.setdefault("goalHierarchy", {"nodes": []})
        nodes = packet["goalHierarchy"]["nodes"]
        for index, selected in enumerate(groups + [regions]):
            check()
            governing = index == len(groups)
            if governing and (not children or "governing-call" in packet["preview"].get("budgetDrops", [])):
                break
            call_schema = deepcopy(schema)
            data = {"root_cues": cues, "root_cue_reliability": {"value": .6, "status": "assumed"}, "scope": "governing" if governing else "local"}
            if governing:
                data["local_candidates"] = [{"id": c["id"], "label": c["label"], "description": c["description"][:500], "regions": c["regions"]} for c in children]
                call_schema["properties"]["covered_ids"] = {"type": "array", "description": "Only local candidates that this governing purpose explains; leave unrelated candidates uncovered.", "items": {"type": "string", "enum": [c["id"] for c in children]}, "uniqueItems": True, "maxItems": len(children)}
                call_schema["required"].append("covered_ids")
            else:
                data["regions"] = [{"id": r["id"], "text": r["anchor"]["exact"]} for r in selected]
            serialized = json.dumps(data, ensure_ascii=True)
            if len(serialized) > 24000:
                continue  # Explicit coverage count below; never silently truncate target text.
            key = digest(["preview-goals-lenses-v3", backend.model_id, backend.settings, prompt, call_schema, data])
            result = cache.get(key)
            if result is None:
                with backend.checking(check):
                    result = json.loads(backend.complete(prompt + "\n" + serialized, call_schema)["text"])
            if not isinstance(result, dict) or set(result) != set(call_schema["required"]):
                raise ValueError("Goal judgment does not match its constrained schema")
            covered = result.get("covered_ids", [])
            if not isinstance(covered, list) or any(not isinstance(i, str) for i in covered) or len(set(covered)) != len(covered) or not set(covered) <= {c["id"] for c in children}:
                raise ValueError("Governing cover cites an unavailable local candidate")
            candidate = Candidate(id=key, maker=maker, regions=[r["id"] for r in selected], depth=2 if governing else 1, **{k: v for k, v in result.items() if k != "covered_ids"})
            if not set(candidate.cue_ids) <= {c["goal_id"] for c in cues} or candidate.cue_match and not candidate.cue_ids:
                raise ValueError("Goal judgment cites an unavailable root cue")
            cache.put(key, result)
            used = "; ".join(c["text"] for c in cues if c["goal_id"] in candidate.cue_ids)
            description = candidate.description
            if governing:
                description += " Governing judgment uses the local candidate summaries. Root cues cited: " + (used[:700] or "none") + "."
            h = hypothesis(packet, ["goal", key], candidate.label, description, kind="goal", regions=candidate.regions,
                           basis="model-judgment", support=relative(candidate.support, "The model's own rating; uncalibrated, not independent support."))
            h["interpretation"] = "governing-purpose" if governing else "local-goal"
            node = {"id": h["id"], "maker": maker, "label": h["label"], "description": h["description"], "regions": h["regions"], "evidence": h["evidence"], "basis": "model-judgment", "evidenceStatus": "unvalidated", "level": "document" if governing else "paragraph"}
            nodes.append(node)
            if governing:
                for child in children:
                    if child["id"] in covered:
                        child["parentId"] = node["id"]
                uncovered = [c["id"] for c in children if c["id"] not in covered]
                if len(uncovered) > len(children) / 3:
                    packet["preview"]["goalLenses"] = [[node["id"], *covered], uncovered]
            else:
                children.append(node)
            advance(packet, "goals", index + 1, len(groups) + 1, "groups")
            publish()
            yield
        if not nodes:
            packet.pop("goalHierarchy", None)
        next(m for m in packet["preview"]["modules"] if m["id"] == "goals")["detail"] = f"{len(children)} of {len(groups)} adjacent paragraph groups judged, plus governing cover when its input fits. Inputs over 24,000 serialized characters were omitted. At most 21 calls. Root cues limited to title, first 29 headings/meta-description entries."
    run.identity = digest([backend.model_id, backend.settings, "preview-goals-lenses-v3"])
    run.metrics = getattr(backend, "metrics", {})
    return run


def goal_groups(regions, priority=None):
    """One small early group, then at most 19 contiguous groups; no text dropped."""
    if not regions:
        return []
    first = next((i for i, r in enumerate(regions) if r["id"] == priority), 0)
    runs = [regions[:first], regions[first + 1:]]
    size = max(1, ceil(max(1, len(regions) - 1) / (18 if all(runs) else 19)))
    groups = [run[i:i + size] for run in runs for i in range(0, len(run), size)]
    return [[regions[first]], *groups]
