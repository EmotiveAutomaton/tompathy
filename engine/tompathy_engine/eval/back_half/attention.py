"""TP2/TP5: fixed writer folds, text-only scoring and paired history contrasts."""
import math
import re
from collections import Counter

import numpy as np

from ...preview.surface import WORD, words
from .data import history_contexts
from .metrics import fit_logistic, predict, registered_row
from .protocol import PROTOCOL, receipt

# Unpunctuated lines are sentences too; the live display regex omits them.
SENTENCE = re.compile(r'[^.!?\n]+(?:[.!?]+|(?=\n)|$)')


def scaled(rows):
    values = [w["nats"] for w in rows if w["content"] and not w["held"]]
    if not values:
        raise ValueError("No eligible content words")
    median = float(np.median(values))
    iqr = float(np.quantile(values, .75)-np.quantile(values, .25))
    return [(w["nats"]-median)/iqr if iqr > 1e-12 else 0. for w in rows]


def positions(text, start):
    sentences = list(SENTENCE.finditer(text))
    sentence = next((s for s in sentences if s.start() <= start < s.end()), None)
    if sentence is None:
        raise ValueError("Word is outside sentence segmentation")
    preceding = list(WORD.finditer(text, sentence.start(), start))
    paragraph = text.rfind("\n", 0, start)+1
    return len(preceding), not preceding, not text[paragraph:start].strip()


def score_sessions(sessions, reader, *, check=lambda: None, smol=None, histories=True, contexts=None):
    contexts = (history_contexts(sessions, reader) if histories else {}) if contexts is None else contexts
    tables = []
    for session in sessions:
        check()
        text = session["text"]
        tokens = reader.score(text, check=check)
        normal = words(text, tokens)
        mapped = {(w["start"],w["end"]): i for i,w in enumerate(normal)}
        variants = {"V0": scaled(normal), "V1": [w["nats"] for w in normal]}
        if getattr(reader, "entropy", False):
            variants["V5"] = [next(t["entropy"] for t in tokens if t["end"] > w["start"] and t["start"] < w["end"]) for w in normal]
        if smol:
            second = words(text, smol.score(text, check=check))
            if [(w["start"],w["end"]) for w in second] != list(mapped):
                raise ValueError("Exploratory readers have different word coverage")
            variants["V2"] = scaled(second)
            variants["V3"] = [(a+b)/2 for a,b in zip(variants["V0"],variants["V2"],strict=True)]
        history = contexts.get(session["session"], {"eligible": False})
        raw_history = {}
        if history["eligible"]:
            for key, name in (("own","V4"),("other","V6")):
                if not history[key]:
                    continue
                other = words(text, reader.score(text, history[key], check))
                if [(w["start"],w["end"]) for w in other] != list(mapped):
                    raise ValueError("History changes target word coverage")
                variants[name] = scaled(other)
                raw_history[name] = [w["nats"] for w in other]
        rows = []
        for label in session["words"]:
            index = mapped.get((label["start"],label["end"]))
            if index is None:
                raise ValueError("Exported word has no complete token-loss coverage")
            word = normal[index]
            position, initial, paragraph = positions(text, word["start"])
            rows.append({**label, "text": word["text"], "eligible": word["content"] and not word["held"],
                "position": position, "sentenceStart": initial, "paragraphStart": paragraph,
                "scores": {v: values[index] for v,values in variants.items()},
                "historyNats": {v: values[index] for v,values in raw_history.items()}})
        tables.append({**session, "words": rows, "history": history})
    return tables


def word_forecast(tables, variants=(), *, own_set=True, require=()):
    selected = [s for s in tables if all(all(v in w["scores"] for v in require) for w in s["words"])]
    rows = [(s,w) for s in selected for w in s["words"] if w["source"] == "writer" and type(w["stop"]) is bool and (not own_set or w["eligible"])]
    if not rows or len({s["fold"] for s,_ in rows}) != 5:
        raise ValueError("Attention evaluation requires eligible words in all five writer folds")
    forecasts = np.zeros(len(rows))
    for fold in range(5):
        frequency = Counter(m.group().casefold() for s in tables if s["fold"] != fold for m in WORD.finditer(s["text"]))
        features = [[len(w["text"]), math.log1p(frequency[w["text"].casefold()]), w["position"],
            w["sentenceStart"], w["paragraphStart"], *(w["scores"][v] for v in variants)] for _,w in rows]
        x = np.asarray(features, dtype=float)
        y = np.array([w["stop"] for _,w in rows], dtype=int)
        train = np.array([s["fold"] != fold for s,_ in rows])
        forecasts[~train] = predict(fit_logistic(x[train],y[train]),x[~train])[:,1]
    return rows, forecasts


def attention_report(tables, *, engine_pin, data_pin):
    rows, base = word_forecast(tables)
    _, v0 = word_forecast(tables, ["V0"])
    result = receipt("attention", status="complete", engine_pin=engine_pin, data_pin=data_pin, evidence="natural-writing")
    result["rows"] = [registered_row("1",[w["stop"] for _,w in rows],base,v0,[s["writer"] for s,_ in rows],"attention")]
    for ident, reference, require in (("2",["V0"],["V4"]),("3",["V6"],["V4","V6"])):
        try:
            if ident == "3" and any(all("V4" in w["scores"] for w in s["words"]) and not all("V6" in w["scores"] for w in s["words"]) for s in tables):
                raise ValueError("Matched donor context missing in the row-2 cohort; row 3 cannot silently change sessions")
            subset, left = word_forecast(tables, reference, require=require)
            _, right = word_forecast(tables,["V4"],require=require)
            row = registered_row(ident,[w["stop"] for _,w in subset],left,right,[s["writer"] for s,_ in subset],"attention")
            row["sessions"] = len({s["session"] for s,_ in subset})
            result["rows"].append(row)
        except ValueError as exc:
            result["rows"].append({"id":ident,"status":"unavailable","reason":str(exc)})
    all_stops = [w for s in tables for w in s["words"] if w["source"] == "writer" and w["stop"]]
    result["stopsOutsideOwnSet"] = sum(not w["eligible"] for w in all_stops)/len(all_stops) if all_stops else None
    result["exploratory"] = []
    for variant in ("V1","V2","V3","V5"):
        if not all(variant in w["scores"] for _,w in rows):
            result["exploratory"].append({"variant":variant,"status":"unavailable"})
            continue
        _, score = word_forecast(tables,[variant])
        row = registered_row("1",[w["stop"] for _,w in rows],base,score,[s["writer"] for s,_ in rows],"attention")
        row.update(variant=variant,registered=False)
        result["exploratory"].append(row)
    available = [r for r in result["exploratory"] if "gain" in r]
    result["exploratoryWinner"] = max(available,key=lambda r:r["gain"])["variant"] if available else None
    all_rows, all_base = word_forecast(tables,own_set=False)
    _, raw = word_forecast(tables,["V1"],own_set=False)
    from .metrics import paired_auc
    result["V1AllWords"] = paired_auc([w["stop"] for _,w in all_rows],all_base,raw,[s["writer"] for s,_ in all_rows])
    return result


def sentence_rows(tables):
    output = []
    for session in tables:
        for index, span in enumerate(SENTENCE.finditer(session["text"])):
            selected = [w for w in session["words"] if span.start() <= w["start"] < span.end()]
            counts = Counter(w["source"] for w in selected)
            if not selected or counts["prompt"] or counts["unknown"]:
                continue
            source, count = counts.most_common(1)[0]
            if count/len(selected) < .9:
                continue
            nats = [w["scores"]["V1"] for w in selected]
            features = {"A0": float(np.mean(nats)), "A1": float(np.std(nats))}
            for v,name in (("V4","A2"),("V6","A2other")):
                if all(v in w["historyNats"] for w in selected):
                    features[name] = float(np.mean([w["scores"]["V1"]-w["historyNats"][v] for w in selected]))
            output.append({"writer":session["writer"],"session":session["session"],"genre":session["genre"],"fold":session["fold"],
                "label":int(source == "suggestion"), "base":[len(selected),index,selected[0]["paragraphStart"]],"scores":features})
    return output


def involvement_report(tables, *, engine_pin, data_pin):
    from .metrics import cross_fit
    all_rows = sentence_rows(tables)
    result = receipt("ai-involvement",status="complete",engine_pin=engine_pin,data_pin=data_pin,evidence="natural-writing")
    result["countsByWriterGenre"] = [{"writer":writer,"genre":genre,"sentences":count} for (writer,genre),count in sorted(Counter((r["writer"],r["genre"]) for r in all_rows).items())]
    for ident,left_keys,right_keys in (("1",[],["A0","A1"]),("2",["A0","A1"],["A0","A1","A2"]),("3",["A0","A1","A2other"],["A0","A1","A2"])):
        if ident == "3" and any("A2" in r["scores"] and "A2other" not in r["scores"] for r in all_rows):
            result["rows"].append({"id":ident,"status":"unavailable","reason":"Matched donor context missing in row-2 cohort"})
            continue
        rows = [r for r in all_rows if all(k in r["scores"] for k in set(left_keys+right_keys))]
        if len({r["fold"] for r in rows}) != PROTOCOL["folds"]:
            result["rows"].append({"id":ident,"status":"unavailable","reason":"Missing eligible sentences/folds"})
            continue
        y,f = [r["label"] for r in rows],[r["fold"] for r in rows]
        a,b = [cross_fit([r["base"]+[r["scores"][k] for k in keys] for r in rows],y,f)[:,1] for keys in (left_keys,right_keys)]
        result["rows"].append(registered_row(ident,y,a,b,[r["writer"] for r in rows],"ai-involvement"))
    if not result["rows"] or "gain" not in result["rows"][0]:
        result["status"] = "insufficient-support"
    return result


def binding_parity(old, new):
    """The TP1 binding check uses the same frozen TP2 row and observations."""
    from ...ledger.ids import digest
    from .metrics import paired_auc
    def cohort(tables):
        return digest([{k:s[k] for k in ("session","writer","fold","text")} | {
            "words":[{k:w.get(k) for k in ("start","end","source","stop","eligible")} for w in s["words"]]} for s in tables])
    if cohort(old) != cohort(new):
        raise ValueError("Binding parity requires identical data, folds and word eligibility")
    rows,left = word_forecast(old,["V0"])
    _,right = word_forecast(new,["V0"])
    difference = paired_auc([w["stop"] for _,w in rows],left,right,[s["writer"] for s,_ in rows])
    return {**difference,"maximumAbsoluteAucDifference":.005,"passes":abs(difference["gain"]) <= .005,
        "defaultChanged":False,"definition":"Same registered row-1 mean within-writer AUC; baseline identical"}
