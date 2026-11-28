"""TP65. Within-report, position-adjusted class differences with whole-writer uncertainty."""

import csv
from pathlib import Path

import numpy as np
import pandas as pd
from rapid_agreement import original_gates
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, read
from rapid_sentence_data import CLASSES
from tompathy_engine.eval.readers.person_halves import summary
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp40 import MANIFEST
from week_display import PT
from week_teacher_read import rank_interval
from word_table_lane import write

NAMES = tuple("SADNESS" if c == "PANIC/GRIEF" else c for c in CHANNELS) + (
    "PRIDE",
    "worry",
)
FIELDS = ("predict_event", "predict_conseq")
PAIRS = {
    "changeMinusNeither": ((1, 2), (0,)),
    "aheadMinusNeither": ((1,), (0,)),
    "landedMinusNeither": ((2,), (0,)),
    "aheadMinusLanded": ((1,), (2,)),
}


def slopes(m, outputs):
    xx, xp, pp = m[:, 0], m[:, 1], m[:, 2]
    xy, py = np.split(m[:, 3:], 2, axis=1)
    adjusted = np.divide(xp, pp, out=np.zeros_like(xp), where=pp > 1.0e-12)
    den = xx - adjusted * xp
    stable = den > 1.0e-10 * np.maximum(1.0, xx)
    return np.divide(
        xy - adjusted[:, None] * py,
        den[:, None],
        out=np.full((len(m), outputs), np.nan),
        where=stable[:, None],
    )


def fit(
    labels,
    positive,
    negative,
    score,
    parent,
    writer,
    position,
    weights,
    check,
    names=NAMES,
):
    if score.ndim != 2 or score.shape[1] != len(names):
        raise ValueError("Output names and score columns differ")
    eligible = np.isin(labels, (*positive, *negative))
    if not eligible.any():
        return {"eligibleSentences": 0, "outputs": {}}
    y, place = score[eligible], position[eligible]
    x = np.isin(labels[eligible], positive).astype(float)
    group, p = np.unique(parent[eligible], return_inverse=True)
    who, owner = np.unique(writer[group], return_inverse=True)
    n = np.bincount(p)
    total = np.bincount(p, weights=x)
    data = np.column_stack((x, place, y))
    avg = np.zeros((len(group), data.shape[1]))
    np.add.at(avg, p, data)
    centered = data - avg[p] / n[p, None]
    x, place, y = centered[:, 0], centered[:, 1], centered[:, 2:]
    moments = np.column_stack(
        (x * x, x * place, place * place, x[:, None] * y, place[:, None] * y)
    )
    per_writer = np.zeros((len(weights[0]), moments.shape[1]))
    np.add.at(per_writer, who[owner[p]], moments)
    result = []
    for w in np.array_split(weights, 40):
        check()
        result.append(slopes(w @ per_writer, y.shape[1]))
    values = np.concatenate(result)
    outputs = {}
    for j, name in enumerate(names):
        a = values[:, j]
        finite = a[1:][np.isfinite(a[1:])]
        r = summary(a[0], finite)
        if np.isfinite(a[0]) and len(finite) > 1:
            se = float(finite.std(ddof=1))
            r.update(
                standardError=se,
                nearZero=min(abs(v) for v in r["interval"]) <= se,
                pAboveZero=(1 + int(np.count_nonzero(finite - a[0] >= a[0])))
                / (len(finite) + 1),
                pBelowZero=(1 + int(np.count_nonzero(finite - a[0] <= a[0])))
                / (len(finite) + 1),
            )
        outputs[name] = r
    mixed = (total > 0) & (total < n)
    return {
        "eligibleSentences": int(eligible.sum()),
        "eligibleReports": len(group),
        "reportsWithBothClasses": int(mixed.sum()),
        "writersWithBothClasses": len(set(who[owner[mixed]])),
        "outputs": outputs,
    }


def prepare(out, check):
    source = ROOT / "TP65-inputs-a"
    receipt = confirmed(source)
    info = read(source / "receipt.json")["result"]
    if info["sentences"] != 51557 or info["reports"] != 30900:
        raise ValueError("The sentence roster differs")
    with np.load(
        bound(source / "aligned.npz", info["files"]["aligned.npz"]), allow_pickle=False
    ) as d:
        parent, ordinal, marks, score, counts, src, original, writer = (
            d[k]
            for k in (
                "parents",
                "ordinal",
                "marks",
                "forecasts",
                "counts",
                "source",
                "original",
                "writer",
            )
        )
    if (
        marks.shape != (51557, 3, 2)
        or score.shape != (51557, len(NAMES))
        or not np.isfinite(score).all()
    ):
        raise ValueError("Incomplete marks or forecasts")
    pos = ordinal / np.maximum(1, counts[parent] - 1)
    both = (marks[:, 0, :] == marks[:, 1, :]).all(1) & (marks[:, 0, 0] >= 0)
    gates = original_gates(marks)
    unavailable = any(gates[k]["status"] == "not used" for k in ("change", "when"))
    descriptive = any(gates[k]["status"] == "weak" for k in ("change", "when"))
    sources = {}
    for s in ("ed", "envent"):
        select = src[parent] == s
        writers, codes = np.unique(writer[src == s], return_inverse=True)
        owners = np.full(len(src), -1)
        owners[src == s] = codes
        rng = np.random.default_rng(23)
        weights = np.vstack(
            (
                np.ones(len(writers), int),
                rng.multinomial(
                    len(writers), np.full(len(writers), 1 / len(writers)), size=2000
                ),
            )
        )
        table = {}
        for name, cls in (
            ("B", marks[:, 0, 0]),
            ("W", marks[:, 1, 0]),
            ("agreement", np.where(both, marks[:, 0, 0], -1)),
        ):
            c = cls[select]
            tab = {
                "counts": {
                    **{k: int(np.sum(c == i)) for i, k in enumerate(CLASSES)},
                    "outside": int(np.sum(c < 0)),
                },
                "reports": int(np.sum(src == s)),
                "writers": len(writers),
                "contrasts": {},
            }
            for key, (plus, minus) in PAIRS.items():
                if unavailable or (
                    name == "agreement" and gates["whose"]["status"] == "not used"
                ):
                    tab["contrasts"][key] = {
                        "status": "Withheld under CW",
                        "outputs": {},
                    }
                    continue
                tab["contrasts"][key] = fit(
                    c,
                    plus,
                    minus,
                    score[select],
                    parent[select],
                    owners,
                    pos[select],
                    weights,
                    check,
                )
            table[name] = tab
        sources[s] = table
        write(out / (s + ".json"), table)
    calendar = read(bound(PT / "inputs/manifest.json", MANIFEST))
    path = Path(
        ".local/readers/data/crowd-enVent2023/corpus/crowd-enVent_generation.tsv"
    )
    bound(path, calendar["sourcePins"]["envent"])
    frame = pd.read_csv(
        path,
        sep="\t",
        quoting=csv.QUOTE_NONE,
        dtype=str,
        usecols=["text_id", "prolific_id", *FIELDS],
    ).set_index("text_id", verify_integrity=True)
    frame = frame.loc[original[src == "envent"]]
    if not np.array_equal(frame.prolific_id.to_numpy(str), writer[src == "envent"]):
        raise ValueError("The foresight table uses different writers")
    bad = np.bincount(parent, weights=marks[:, 0, 0] < 0, minlength=len(src)) > 0
    share = (
        np.bincount(parent, weights=marks[:, 0, 0] == 1, minlength=len(src)) / counts
    )
    share = share[src == "envent"].copy()
    share[bad[src == "envent"]] = np.nan
    foresight = {
        name: rank_interval(
            share,
            pd.to_numeric(frame[name], errors="raise").to_numpy(float),
            frame.prolific_id.to_numpy(str),
            check,
        )
        for name in FIELDS
        if gates["when"]["status"] != "not used"
    }
    return {
        "card": "TP65",
        "alignedReceiptPin": receipt,
        "sources": sources,
        "foresight": foresight,
        "reader": "B",
        "CW": gates,
        "interpretation": "Withheld under CW"
        if unavailable
        else "Descriptive under CW"
        if descriptive
        else "Eligible for the registered comparisons",
        "sensitivity": ["W", "B/W exact agreement"],
        "bootstrapDraws": 2000,
        "pendingSources": ["Q29", "Q31", "Q30 if accessible"],
        "productionAdmission": False,
    }
