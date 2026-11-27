"""TP77. Registered unweighted Cohen kappa on the jointly valid original sentences."""

import numpy as np
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, read
from tompathy_engine.eval.readers.person_halves import summary
from word_table_lane import write


def classification(value):
    if value is None or value < 0.40:
        return "not used"
    return "usable" if value >= 0.60 else "weak"


def kappas(t):
    count = t.sum(axis=(1, 2))
    observed = np.trace(t, axis1=1, axis2=2) * count
    expected = (t.sum(1) * t.sum(2)).sum(1)
    den = count**2 - expected
    return np.divide(
        observed - expected, den, out=np.full(len(t), np.nan), where=den > 0
    )


def original_gates(marks):
    a, b = marks[:, 0, 0], marks[:, 1, 0]
    ok = (a >= 0) & (b >= 0)
    out = {}
    for key, x, y, n in (
        ("change", np.sign(a), np.sign(b), 2),
        ("when", a, b, 4),
        ("whose", marks[:, 0, 1], marks[:, 1, 1], 3),
    ):
        table = np.zeros((n, n), dtype=np.int64)
        np.add.at(table, (x[ok], y[ok]), 1)
        value = kappas(table[None])[0]
        k = float(value) if np.isfinite(value) else None
        out[key] = {"kappa": k, "status": classification(k), "valid": int(ok.sum())}
    return out


def pair(a, b, writers, n, weights, check):
    ok = (a >= 0) & (b >= 0)
    counts = np.zeros((weights.shape[1], n, n), dtype=np.int64)
    np.add.at(counts, (writers[ok], a[ok], b[ok]), 1)
    table = counts.sum(0)
    measured = kappas(table[None])[0]
    draws = []
    for w in np.array_split(weights, 20):
        check()
        draws.extend(kappas((w @ counts.reshape(len(counts), -1)).reshape(-1, n, n)))
    stat = summary(measured, np.asarray(draws))
    return {
        **stat,
        "jointlyValid": int(ok.sum()),
        "roster": len(ok),
        "table": table.tolist(),
        "reader1Only": int(np.sum((a >= 0) & (b < 0))),
        "reader2Only": int(np.sum((b >= 0) & (a < 0))),
        "bothMissing": int(np.sum((a < 0) & (b < 0))),
    }


def tables(marks, owners, stage, subset, check):
    from rapid_sentence_data import CLASSES, WHO

    result = {}
    for i, j, key in ((0, 1, "B/W"), (0, 2, "B/C"), (1, 2, "W/C")):
        take = subset if j == 1 else subset & (stage == "Q11")
        _, person = np.unique(owners[take], return_inverse=True)
        n = int(person.max()) + 1
        weights = np.random.default_rng(23).multinomial(n, np.full(n, 1 / n), size=2000)
        # Float multiplication avoids integer overflow when summing the table across resamples.
        weights = weights.astype(float)
        when1, when2 = marks[take, i, 0], marks[take, j, 0]
        fields = {
            "when": (when1, when2, CLASSES),
            "change": (np.sign(when1), np.sign(when2), ("no", "yes")),
            "whose": (marks[take, i, 1], marks[take, j, 1], WHO),
        }
        out = {}
        for field, (a, b, levels) in fields.items():
            val = pair(a, b, person, len(levels), weights, check)
            val["levels"] = list(levels)
            if j == 1:
                val["CW"] = classification(val["value"])
            out[field] = val
        result[key] = out
    return result


def prepare(out, check):
    folder = ROOT / "TP65-inputs-a"
    source = confirmed(folder)
    r = read(folder / "receipt.json")["result"]
    with np.load(
        bound(folder / "aligned.npz", r["files"]["aligned.npz"]), allow_pickle=False
    ) as d:
        parent, marks = d["parents"], d["marks"]
        src = d["source"][parent]
        owners = np.char.add(np.char.add(src, ":"), d["writer"][parent])
        stage = d["stage"][parent]
    result = {
        k: tables(marks, owners, stage, mask, check)
        for k, mask in (
            ("all", np.ones(len(marks), bool)),
            ("ed", src == "ed"),
            ("envent", src == "envent"),
        )
    }
    write(out / "tables.json", result)
    return {
        "card": "TP77-original",
        "alignedReceiptPin": source,
        "sources": result,
        "modelReceiptPins": r["marks"],
        "limits": "B/W defines mark usability on the common original roster. The B/C and W/C checks use the Q11 subset.",
    }
