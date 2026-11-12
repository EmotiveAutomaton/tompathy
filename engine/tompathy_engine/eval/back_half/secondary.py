"""EX4 transfer check: freeze the EX1 winner and fit on EX1 only."""
import math
from collections import Counter

from ...preview.surface import WORD
from .attention import positions, score_sessions
from .metrics import fit_logistic, paired_auc, predict


def secondary_report(training, essays, reader, winner, *, smol=None, check=lambda: None):
    if winner not in {"V1","V2","V3","V5"}:
        raise ValueError("Secondary check requires the frozen EX1 exploratory winner")
    sessions = []
    seen = set()
    for essay in essays:
        if not isinstance(essay.get('session'),str) or not essay['session'] or essay['session'] in seen:
            raise ValueError("EX4 requires distinct nonempty session identities")
        seen.add(essay['session'])
        # No fabricated writer identity or arbitrary validation folds.
        labels = [{**w,"source":"writer","stop":w["stop80"],"logPause":0.} for w in essay["words"]]
        if any(type(w.get(k)) is not bool for w in labels for k in ("stop80","stop2s","insertedLater")):
            raise ValueError("EX4 requires both labels and the later-insertion flag")
        spans = {(m.start(),m.end()) for m in WORD.finditer(essay['text'])}
        locations = [(w['start'],w['end']) for w in labels]
        if not labels or len(set(locations)) != len(locations) or any(type(w[k]) is not int for w in labels for k in ('start','end')) or not set(locations) <= spans:
            raise ValueError("EX4 word spans must be unique exact source words")
        sessions.append({"session":essay["session"],"text":essay["text"],"words":labels})
    scored = score_sessions(sessions,reader,smol=smol,check=check,histories=False)
    frequency = Counter(m.group().casefold() for s in training for m in WORD.finditer(s["text"]))
    train = [(s,w) for s in training for w in s["words"] if w["source"] == "writer" and w["eligible"]]
    test = [(s,w) for s in scored for w in s["words"] if w["eligible"]]
    def features(rows, variant):
        output = []
        for s,w in rows:
            pos,initial,paragraph = positions(s["text"],w["start"])
            output.append([len(w["text"]),math.log1p(frequency[w["text"].casefold()]),pos,initial,paragraph]+([] if variant is None else [w["scores"][variant]]))
        return output
    predictions = {}
    for variant in (None,"V0",winner):
        model = fit_logistic(features(train,variant),[w["stop"] for _,w in train])
        predictions[variant] = predict(model,features(test,variant))[:,1]
    result = {"winner":winner,"selection":"frozen EX1 choice; no EX4 tuning","cluster":"session","rows":[],
        "insertedLaterWords":sum(w["insertedLater"] for _,w in test),"sessions":len(scored)}
    for variant in ("V0",winner):
        for label in ("stop80","stop2s"):
            result["rows"].append({"variant":variant,"label":label,**paired_auc([w[label] for _,w in test],predictions[None],predictions[variant],[s["session"] for s,_ in test])})
    return result
