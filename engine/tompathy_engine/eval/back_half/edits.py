"""TP3: exact engine hunks, nested editor folds and a gated Q8 cascade."""
from collections import Counter
from time import monotonic

import numpy as np

from ...adapters.history import diff_hunks
from ...features.deterministic import edit_features
from ...ledger.ids import digest
from .metrics import cross_fit, fit_logistic, predict

CATEGORIES = ("typo or spelling", "grammar", "clarity", "added content", "removed content")
Q8_MAP = {"typo":"typo or spelling", "grammar":"grammar", "wording":"clarity", "tone":"clarity",
          "add content":"added content", "remove content":"removed content", "reorder":"other", "format":"other", "unclear":"other"}


def eligible_edits(rows, feature_names):
    if not feature_names or len(set(feature_names)) != len(feature_names) or set(feature_names) & {"reason", "comment", "category", "user", "fold", "post", "site", "time"}:
        raise ValueError("Frozen, non-label feature definitions required")
    accepted, counts, writers, ids = [], Counter(), {}, set()
    for row in rows:
        if row["id"] in ids or type(row["fold"]) is not int or row["fold"] not in range(5) or row["category"] not in CATEGORIES:
            raise ValueError("Invalid edit identity/category/fold")
        ids.add(row["id"])
        if row["writer"] in writers and writers[row["writer"]] != row["fold"]:
            raise ValueError("An editor crosses folds")
        writers[row["writer"]] = row["fold"]
        if not row.get("postId"):
            raise ValueError("CC BY-SA attribution requires post ID")
        band = "over-10000" if max(len(row["before"]),len(row["after"])) > 10000 else "up-to-10000"
        counts[band+":total"] += 1
        hunks = diff_hunks(row["before"],row["after"])
        if len(hunks) != 1:
            counts[band+":not-single-hunk"] += 1
            continue
        start,end,replacement = hunks[0]
        if max(end-start,len(replacement)) > 12000:
            counts[band+":over-12000-hunk"] += 1
            continue
        extra = [float(row["features"][name]) for name in feature_names]
        if not np.isfinite(extra).all():
            raise ValueError("Nonfinite supplied feature")
        start_time = monotonic()
        features = [*edit_features(row["before"],row["after"]).values(),*extra]
        accepted.append({**row,"replaced":row["before"][start:end],"replacement":replacement,"x":features,
            "engineFeatureSeconds":monotonic()-start_time})
        counts[band+":kept"] += 1
    return accepted, dict(counts)


def threshold(probabilities, labels):
    p,y = np.asarray(probabilities),np.asarray(labels)
    confidence, guesses = p.max(axis=1),p.argmax(axis=1)
    correct = (guesses < 2) == (y < 2)
    for value in sorted(set(confidence)):
        mask = confidence >= value
        if correct[mask].mean() >= .95:
            return float(value)
    return None


def classifier(rows):
    x = np.asarray([r["x"] for r in rows])
    y = np.asarray([CATEGORIES.index(r["category"]) for r in rows])
    folds = np.asarray([r["fold"] for r in rows])
    if set(folds) != set(range(5)):
        raise ValueError("Edit classifier requires five editor folds")
    outputs, gates, timings = np.zeros((len(rows),5)), {}, {}
    for fold in range(5):
        train,test = folds != fold,folds == fold
        # Threshold selection never sees the held-out editor fold.
        nested = cross_fit(x[train],y[train],folds[train],classes=5)
        gates[str(fold)] = threshold(nested,y[train])
        model = fit_logistic(x[train],y[train],classes=5)
        start = monotonic()
        outputs[test] = predict(model,x[test])
        timings[str(fold)] = (monotonic()-start)/int(test.sum())
    return outputs,gates,timings


def sample_edits(rows, seed=20261111):
    rng = np.random.default_rng(seed)
    selected = []
    for category in CATEGORIES:
        indices = sorted((i for i,r in enumerate(rows) if r["category"] == category),key=lambda i:str(rows[i]["id"]))
        selected.extend(rng.permutation(indices)[:200].tolist())
    return rng.permutation(selected).tolist()


def sample_coverage(rows, indices):
    return {category:{"eligible":sum(r['category'] == category for r in rows),
        "sampled":sum(rows[i]['category'] == category for i in indices),
        "byFold":{str(f):sum(rows[i]['category'] == category and rows[i]['fold'] == f for i in indices) for f in range(5)}}
        for category in CATEGORIES}


def sample_pin(rows, indices):
    return digest([[str(rows[i]['id']),digest([rows[i]['replaced'],rows[i]['replacement']])] for i in indices])


def first_call_projection(rows, indices, completed, reader_pin, data_pin):
    initial = indices[:50]
    if not initial or any(str(rows[i]['id']) not in completed for i in initial):
        raise ValueError("First-call projection requires the entire initial sample")
    measured = [completed[str(rows[i]['id'])] for i in initial]
    if any(r.get('readerPin') != reader_pin for r in measured):
        raise ValueError("Projection reader differs from completed calls")
    timed = all(r.get('inferenceMeasured') is True for r in measured)
    return {'schema':'tompathy.q8-projection.v1','completed':len(initial),'requested':len(indices),
        'samplePin':sample_pin(rows,indices),'readerPin':reader_pin,'dataPin':data_pin,
        'initialCallsPin':digest(measured),'allInferenceTimed':timed,
        'projectedSeconds':sum(r['seconds'] for r in measured)/len(measured)*len(indices) if timed else None,
        'definition':'Seeded sample order across categories and folds; projection is uncertain, not a deadline'}


def scores(truth, answers):
    if not truth or len(truth) != len(answers) or any(a not in {*CATEGORIES,"other","unclear"} for a in answers):
        raise ValueError("Invalid reason predictions")
    f1 = []
    for category in CATEGORIES:
        tp = sum(t == category and a == category for t,a in zip(truth,answers,strict=True))
        denom = sum(t == category for t in truth) + sum(a == category for a in answers)
        f1.append(2*tp/denom if denom else 0.)
    correct = [a != "unclear" and (t in CATEGORIES[:2]) == (a in CATEGORIES[:2]) for t,a in zip(truth,answers,strict=True)]
    return {"macroF1":float(np.mean(f1)),"twoWayAccuracy":float(np.mean(correct)),"edits":len(truth)}


def q8_sample(reader, rows, indices, *, check=lambda: None, on_projection=lambda _: None, completed=None):
    """Use the existing literal call; never enable Q9/correction_steps.

    Completed records are private receipts supplied by the caller for resumption.
    Cache hits with no saved timing remain explicitly unusable for speed claims.
    """
    output = dict(completed or {})
    for index in indices:
        row = rows[index]
        old = output.get(str(row["id"]))
        if old and (old.get("readerPin") != reader.pin or old.get("inputPin") != digest([row["replaced"],row["replacement"]])):
            raise ValueError("Saved Q8 call pin or hunk differs")
    for index in indices:
        row = rows[index]
        if str(row["id"]) in output:
            continue
        check()
        calls = getattr(reader.backend,"metrics",{}).get("calls",0)
        start = monotonic()
        with reader.backend.checking(check):
            answer = reader.ask("Q8",context="",text=row["replacement"],before=row["replaced"],admission_test=True)["answer"]
        if answer not in Q8_MAP:
            raise ValueError("Unexpected Q8 answer")
        output[str(row["id"])] = {"raw":answer,"category":Q8_MAP[answer],"seconds":monotonic()-start,
            "inferenceMeasured":getattr(reader.backend,"metrics",{}).get("calls",0) > calls,"readerPin":reader.pin,
            "inputPin":digest([row["replaced"],row["replacement"]])}
        if len(output) == 50:
            measured = [r["seconds"] for r in output.values() if r["inferenceMeasured"]]
            on_projection({"completed":50,"requested":len(indices),"projectedSeconds":float(np.mean(measured))*len(indices) if measured else None})
    return output


def compare_cascade(rows, probabilities, gates, timings, measured):
    selected = [i for i,r in enumerate(rows) if str(r["id"]) in measured]
    if not selected:
        raise ValueError("No paired direct-reader observations")
    truth = [rows[i]["category"] for i in selected]
    direct = ["unclear" if measured[str(rows[i]["id"])]["raw"] == "unclear" else measured[str(rows[i]["id"])]["category"] for i in selected]
    result = {"direct":scores(truth,direct), "feature":scores(truth,[CATEGORIES[int(probabilities[i].argmax())] for i in selected]), "cascadeEligible":False}
    if any(gates[str(rows[i]["fold"])] is None for i in selected):
        result["reason"] = "No training-only threshold reaches 95% in every evaluated fold"
        return result
    feature_cost_known = all(type(rows[i].get(key)) in (float,int) and np.isfinite(rows[i][key]) and rows[i][key] >= 0
        for i in selected for key in ("engineFeatureSeconds","featureSeconds"))
    answers,total = [],0.
    for index,d in zip(selected,direct,strict=True):
        row = rows[index]
        confident = probabilities[index].max() >= gates[str(row["fold"])]
        answers.append(CATEGORIES[int(probabilities[index].argmax())] if confident else d)
        total += timings[str(row["fold"])] + (row['engineFeatureSeconds']+row['featureSeconds'] if feature_cost_known else 0) + (0 if confident else measured[str(row["id"])]["seconds"])
    result["cascade"] = scores(truth,answers)
    if not feature_cost_known:
        result["reason"] = "Supplied feature computation costs are unmeasured; no cascade speed qualification"
        return result
    if not all(measured[str(rows[i]["id"])]["inferenceMeasured"] for i in selected):
        result["reason"] = "Cached calls lack original inference timing; speed qualification unavailable"
        return result
    direct_time = float(np.mean([measured[str(rows[i]["id"])]["seconds"] for i in selected]))
    result.update(directSecondsPerEdit=direct_time,cascadeSecondsPerEdit=total/len(selected),
        cascadeEligible=result["cascade"]["twoWayAccuracy"] >= result["direct"]["twoWayAccuracy"]-.02 and total/len(selected) <= direct_time/2,
        defaultEnabled=False)
    return result
