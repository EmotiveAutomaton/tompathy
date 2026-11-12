"""TP4 paired pilot: answer-section removal, existing goal call and TF-IDF ranks."""
import math
import re
from collections import Counter
from time import monotonic

import numpy as np

from ...adapters.capture import utf16_slice
from ...ledger.ids import digest
from ...models.goals import Candidate
from ...preview.judgments import goal_call
from ...preview.surface import WORD, summarize_deviation, words

REMOVED = {"motivation","abstract","simple summary"}


def without_answers(text, sections):
    spans = sorted((r["start"],r["end"]) for r in sections if r["kind"].strip().casefold() in REMOVED)
    if not any(r["kind"].casefold() == "motivation" for r in sections):
        raise ValueError("Pinned Motivation offsets required")
    previous, parts = 0,[]
    for start,end in spans:
        if type(start) is not int or type(end) is not int or not previous <= start < end <= len(text):
            raise ValueError("Invalid or overlapping answer-section offsets")
        parts.append(text[previous:start])
        previous = end
    parts.append(text[previous:])
    # EIP metadata may use an indented continuation for description.
    return re.sub(r"(?mi)^description\s*:[^\n]*(?:\n[ \t]+[^\n]*)*\n?", "", "".join(parts))


def pilot_inputs(text, sections, title, headings, reader, check=lambda: None):
    body = without_answers(text,sections)
    cues = [{"goal_id":"page-title","text":title}] + [{"goal_id":f"heading-{i}","text":h["text"]} for i,h in enumerate(headings)
        if 1 <= h["level"] <= 3 and not any(s["kind"].casefold() in REMOVED and s["start"] <= h["start"] < s["end"] for s in sections)]
    tokens = reader.score(body,check=check)
    table = {"region":"pilot-body","text":body,"words":words(body,tokens)}
    attention = summarize_deviation([table],check)["attention"]
    selected = sorted((r for r in attention if r["finding"] == "departure-sentence"),key=lambda r:r["start"])
    fragments,total = [],0
    for row in selected:
        sentence = utf16_slice(body,row["start"],row["end"])[:250]
        cost = len(sentence)+(1 if fragments else 0)
        if total+cost > 6000:
            break
        fragments.append(sentence)
        total += cost
    return {"body":body[:12000],"departures":"\n".join(fragments),"cues-only":""},cues[:30]


def rank_motivation(statement, candidates, true_id):
    if len(candidates) != 50 or len({c["id"] for c in candidates}) != 50 or true_id not in {c["id"] for c in candidates}:
        raise ValueError("Task needs exactly 50 distinct pinned candidates including truth")
    bags = [Counter(m.group().casefold() for m in WORD.finditer(c["text"])) for c in candidates]
    vocabulary = sorted(set().union(*bags))
    if not vocabulary:
        raise ValueError("Empty candidate vocabulary")
    idf = np.array([math.log(51/(1+sum(w in b for b in bags)))+1 for w in vocabulary])
    matrix = np.array([[b[w] for w in vocabulary] for b in bags])*idf
    query = Counter(m.group().casefold() for m in WORD.finditer(statement))
    vector = np.array([query[w] for w in vocabulary])*idf
    norm = np.linalg.norm(matrix,axis=1)*np.linalg.norm(vector)
    similarities = np.divide(matrix@vector,norm,out=np.zeros(50),where=norm>0)
    order = sorted(range(50),key=lambda i:(-similarities[i],candidates[i]["id"]))
    rank = next(i+1 for i,j in enumerate(order) if candidates[j]["id"] == true_id)
    return {"top1":int(rank == 1),"reciprocalRank":1/rank,"rank":rank,"ties":"candidate ID order"}


def pilot_sample(tasks, seed=20261111):
    rng = np.random.default_rng(seed)
    selected = []
    for repo in ("peps","eips"):
        group = sorted((t for t in tasks if t["repository"] == repo),key=lambda t:t["id"])
        if len(group) < 20:
            raise ValueError("Pilot requires 20 eligible documents per repository")
        selected.extend(group[i] for i in rng.permutation(len(group))[:20])
    return selected


def pilot_document(task, inputs, cues, backend, cache, *, check=lambda: None, completed=None, on_progress=lambda _: None):
    pin = digest([task,inputs,cues,backend.model_id,backend.settings])
    if completed and completed.get("inputPin") != pin:
        raise ValueError("Saved pilot document differs from its exact input/reader pin")
    outcomes = dict(completed["readers"]) if completed else {}
    for name,text in inputs.items():
        if name in outcomes:
            continue
        check()
        calls = getattr(backend,"metrics",{}).get("calls",0)
        start = monotonic()
        key,result = goal_call(backend,cache,cues,text,check=check)
        candidate = Candidate(id=key,maker="pilot",regions=[task["id"]],depth=1,**result)
        if not set(candidate.cue_ids) <= {c["goal_id"] for c in cues} or candidate.cue_match and not candidate.cue_ids:
            raise ValueError("Pilot goal cites unavailable evidence")
        cache.put(key,result)
        outcomes[name] = {**rank_motivation(candidate.label+" "+candidate.description,task["candidates"],task["truth"]),
            "seconds":monotonic()-start,"callKey":key,
            "inferenceMeasured":getattr(backend,"metrics",{}).get("calls",0) > calls}
        on_progress({"id":task["id"],"author":task["author"],"inputPin":pin,"readers":dict(outcomes)})
    return {"id":task["id"],"author":task["author"],"inputPin":pin,"readers":outcomes}


def pilot_summary(paired, draws=2000, seed=20261111):
    if not paired or any(set(p["readers"]) != {"body","departures","cues-only"} for p in paired):
        raise ValueError("Only fully paired documents enter the pilot summary")
    authors = sorted({p["author"] for p in paired})
    if len(authors) < 2:
        raise ValueError("Need at least two author clusters")
    rng = np.random.default_rng(seed)
    banks = [[p for p in paired if p["author"] == a] for a in authors]
    samples = [[p for i in rng.integers(len(banks),size=len(banks)) for p in banks[i]] for _ in range(draws)]
    result = {"documents":len(paired),"authors":len(authors),"readers":{},"differences":{},"pilot":True}
    for name in ("body","departures","cues-only"):
        stats = {}
        for metric in ("top1","reciprocalRank"):
            stats[metric] = {"mean":float(np.mean([p["readers"][name][metric] for p in paired])),
                "interval":np.quantile([np.mean([p["readers"][name][metric] for p in sample]) for sample in samples],[.025,.975]).tolist()}
        measured = [p["readers"][name]["seconds"] for p in paired if p["readers"][name].get("inferenceMeasured") is True]
        stats["secondsPerCall"] = float(np.mean(measured)) if measured else None
        stats["timedInferenceCalls"] = len(measured)
        stats["cachedCallsWithoutTiming"] = len(paired)-len(measured)
        result["readers"][name] = stats
    for reference in ("body","cues-only"):
        result["differences"][reference] = {}
        for metric in ("top1","reciprocalRank"):
            boot = [float(np.mean([p["readers"]["departures"][metric]-p["readers"][reference][metric] for p in sample])) for sample in samples]
            se = float(np.std(boot,ddof=1))
            result["differences"][reference][metric] = {"gain":float(np.mean([p["readers"]["departures"][metric]-p["readers"][reference][metric] for p in paired])),
                "interval":np.quantile(boot,[.025,.975]).tolist(),"pairedSE":se,
                "projectedDocumentsFor005":math.ceil(len(paired)*(2.8*se/.05)**2) if se > 0 else None,
                "projectionAssumption":"normal approximation, 80% power, two-sided 5%, same author clustering; unstable pilot estimate"}
    return result
