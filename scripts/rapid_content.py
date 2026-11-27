"""TP62. Assigned words across held-out writers and writers across held-out words."""

import hashlib
import re
import warnings
from pathlib import Path

import numpy as np
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

WEEK = Path(".local/week-20261122")
Q21 = "574e724abfdeafbe0ce067a495f21142cc0a557f9a560a1cf796ae816f1e8695"
CHANNEL = "0280d3b4739466b020e91ab0f21ce2c7ad17435ff8cbfe000c8f497d32b0c9a1"
PRIDE = "b28a4354eb385122d2733087318b814271d52af29db976b06a321114fca1973b"
TOKENS = re.compile(r"[a-z]+")
STEMS = {
    "afraid": ("afraid",),
    "angry": ("angry", "angri", "anger"),
    "annoyed": ("annoy",),
    "anticipating": ("anticipat",),
    "anxious": ("anxi",),
    "apprehensive": ("apprehen",),
    "ashamed": ("asham", "shame"),
    "caring": ("care", "caring"),
    "confident": ("confiden",),
    "content": ("content",),
    "devastated": ("devastat",),
    "disappointed": ("disappoint",),
    "disgusted": ("disgust",),
    "embarrassed": ("embarrass",),
    "excited": ("excit",),
    "faithful": ("faith",),
    "furious": ("furi", "fury"),
    "grateful": ("gratefu", "gratitud"),
    "guilty": ("guilt",),
    "hopeful": ("hope", "hoping"),
    "impressed": ("impress",),
    "jealous": ("jealous",),
    "joyful": ("joy",),
    "lonely": ("lone",),
    "nostalgic": ("nostalg",),
    "prepared": ("prepar",),
    "proud": ("proud", "pride"),
    "sad": ("sad",),
    "sentimental": ("sentiment",),
    "surprised": ("surpris",),
    "terrified": ("terrifi", "terrify", "terror"),
    "trusting": ("trust",),
}


def order(prefix, value):
    return hashlib.sha256((prefix + str(value)).encode()).digest()


def design():
    from tompathy_engine.eval.readers.affect_data import ed_situations
    from tompathy_engine.eval.readers.tp39 import saved
    from week_pride_inputs import FROZEN, SOURCE

    receipt = read(bound(FROZEN / "receipt.json", SOURCE))
    frame, intake = ed_situations(Path(".local/readers/data/empathetic-dialogues"))
    if intake["intakePin"] != receipt["sources"]["ed"]["intakePin"]:
        raise ValueError("Original chat source differs")
    with np.load(
        saved(FROZEN, "ed-profile-forecasts.npz", receipt), allow_pickle=False
    ) as ids:
        if not np.array_equal(ids["ids"].astype(str), frame.id.to_numpy(str)):
            raise ValueError("Original ordered forecast IDs differ")
    with np.load(saved(FROZEN, "vectors.npz", receipt), allow_pickle=False) as data:
        vectors = data["ed"].astype(np.float64)
    model = WEEK / "TP58-candidate-b/payload/models"
    with (
        np.load(bound(model / "tags.npz", HEAD)) as tags,
        np.load(bound(model / "channels.npz", CHANNEL)) as channels,
        np.load(bound(model / "pride.npz", PRIDE)) as pride,
    ):
        c = channels["parameters"]
        if not np.array_equal(channels["active"], np.arange(9)):
            raise ValueError("Chat requires the original nine active output columns")
        weights = np.vstack([tags["weights"], c[:-1].T, pride["theta"][:-1]])
        bias = np.r_[tags["bias"], c[-1], pride["theta"][-1]]
    transfer = read(WEEK / "Q21-transfer.json")
    original = Path(transfer["mirror"])
    q21 = read(bound(original / "receipt.json", Q21))
    if not transfer["nativeExited"] or not transfer["priorFlockReleased"]:
        raise ValueError("Q21 release is not verified")
    with np.load(
        bound(original / "ed-ten.npz", q21["outputs"]["ed-ten.npz"])
    ) as original_ten:
        gap = float(
            np.max(
                np.abs(
                    expit(vectors @ weights[19:].T + bias[19:]) - original_ten["ten"]
                )
            )
        )
    if not np.isfinite(gap) or gap > 1e-5:
        raise ValueError(f"Ten-output identity differs; maximum probability gap {gap}")
    active = np.ptp(vectors @ weights.T, axis=0) > 0
    words, label = np.unique(frame.label.to_numpy(str), return_inverse=True)
    people, person, count = np.unique(
        frame.writer.to_numpy(str), return_inverse=True, return_counts=True
    )
    if (len(words), len(people), int((count >= 8).sum())) != (32, 810, 336) or set(
        words
    ) != set(STEMS):
        raise ValueError("Original chat census differs")
    folds = np.empty(len(people), dtype=int)
    folds[
        sorted(range(len(people)), key=lambda i: order("TP62:writer:23:", people[i]))
    ] = np.arange(len(people)) % 5
    profile = set(sorted(words, key=lambda v: order("TP62:word:23:", v))[:16])
    word_train = np.asarray([v in profile for v in frame.label])
    keep = np.asarray(
        [
            not any(t.startswith(STEMS[w]) for t in TOKENS.findall(s.casefold()))
            for s, w in zip(frame.text, frame.label, strict=True)
        ]
    )
    return (
        vectors,
        weights[active],
        label,
        person,
        folds[person],
        word_train,
        count >= 8,
        keep,
        {
            "source": SOURCE,
            "sourceIntake": intake["intakePin"],
            "headPins": [HEAD, CHANNEL, PRIDE],
            "tenSource": Q21,
            "maxTenProbabilityGap": gap,
            "active": np.flatnonzero(active).tolist(),
            "writers": len(people),
            "eligibleWriters": int((count >= 8).sum()),
            "words": len(words),
            "profileWords": sorted(profile),
            "texts": len(label),
            "wordFreeTexts": int(keep.sum()),
        },
    )


def scale(reference, rows):
    sd = reference.std(0)
    sd[sd == 0] = 1
    return (rows - reference.mean(0)) / sd


def measure(scores, labels, people, folds, profile, eligible, mask, check):
    accs, nfold = [], []
    for fold in range(5):
        check()
        train, test = mask & (folds != fold), mask & (folds == fold)
        x = scale(scores[train], scores)
        model = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(x[train], labels[train])
        accs.append(float(np.mean(model.predict(x[test]) == labels[test])))
        nfold.append(int(test.sum()))
    train, test = mask & eligible[people] & profile, mask & eligible[people] & ~profile
    owners = np.intersect1d(np.unique(people[train]), np.unique(people[test]))
    train &= np.isin(people, owners)
    test &= np.isin(people, owners)
    x = scale(scores[train], scores)
    centers = np.stack([x[train & (people == p)].mean(0) for p in owners])
    y = x[test]
    norm_c, norm_y = np.linalg.norm(centers, axis=1), np.linalg.norm(y, axis=1)
    if not len(y) or not np.all(norm_y > 0) or not np.all(norm_c > 0):
        raise ValueError("Undefined writer distance")
    centers /= norm_c[:, None]
    hits = sum(
        int(np.sum(owners[np.argmax((a / b[:, None]) @ centers.T, axis=1)] == targets))
        for a, b, targets in zip(
            np.array_split(y, 16),
            np.array_split(norm_y, 16),
            np.array_split(people[test], 16),
            strict=True,
        )
    )
    return {
        "wordAccuracy": float(np.mean(accs)),
        "wordFoldAccuracy": accs,
        "wordFoldRows": nfold,
        "writerAccuracy": hits / len(y),
        "writerHits": hits,
        "writerTexts": len(y),
        "writerCandidates": len(owners),
    }


def run(out, check, sets):
    from word_table_lane import write

    v, w, label, person, fold, profile, eligible, keep, meta = design()
    check()
    write(out / "design.json", meta)
    paths = {}
    for kind, i in sets:
        check()
        x = v @ (w if kind == "trained" else heads(w, "TP62", kind, i)).T
        key = f"{kind}-{i:03d}"
        result = {
            name: measure(x, label, person, fold, profile, eligible, mask, check)
            for name, mask in (
                ("all", np.ones(len(keep), bool)),
                ("withoutAssignedStem", keep),
            )
        }
        dest = out / (key + ".json")
        write(dest, {"family": kind, "index": i, "rows": result})
        paths[dest.name] = pin(dest)
    return {
        "meta": meta,
        "files": paths,
        "measuredSets": len(sets),
        "requiredSets": 401,
    }
