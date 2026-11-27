"""TP69 and the original TP67 comparison on the same source-bound chat reports."""

from pathlib import Path

import numpy as np
from rapid_blend import estimate, fixed
from rapid_content import Q21, WEEK
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from scipy.special import expit
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28, q6_features, saved
from tompathy_engine.packs.trigger import FEATURES, TAGS
from week_competence import PARTS
from word_table_lane import write

RESPECT = ("status", "approval", "competition", "honor")
COLS = ("Competence", "Respect", "acceptance", "goal support")


def draws(n):
    return np.vstack(
        (
            np.ones(n),
            np.random.default_rng(23).multinomial(n, np.full(n, 1 / n), size=2000),
        )
    )


def ratios(numerator, denominator):
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan, dtype=float),
        where=denominator > 0,
    )


def profiles(values, label, writer, words, weight, check):
    n = weight.shape[1]

    def sums(idx, table):
        out = np.zeros((n, table.shape[1]))
        np.add.at(out, writer[idx], table[idx])
        return weight @ out

    full = np.ones(len(label), bool)
    total = weight @ np.bincount(writer, minlength=n)
    overall = sums(full, values)
    sd = np.sqrt(
        np.maximum(
            ratios(sums(full, values**2), total[:, None])
            - ratios(overall, total[:, None]) ** 2,
            0,
        )
    )
    out = {}
    for i, word in enumerate(words):
        check()
        idx = label == i
        num = weight @ np.bincount(writer[idx], minlength=n)
        part = sums(idx, values)
        avg = ratios(part, num[:, None])
        lift = ratios(avg - ratios(overall - part, (total - num)[:, None]), sd)
        row = {
            name: {"mean": estimate(avg[:, j]), "lift": estimate(lift[:, j])}
            for j, name in enumerate(COLS)
        }
        for j, k in ((0, 1), (1, 2)):
            diff = lift[:, j] - lift[:, k]
            row[COLS[j] + "Minus" + COLS[k]] = {
                **estimate(diff, 0.5 if diff[0] >= 0 else -0.5),
                "pointAtLeastHalfSD": bool(abs(diff[0]) >= 0.5),
            }
        out[word] = {
            "texts": int(idx.sum()),
            "writers": len(np.unique(writer[idx])),
            **row,
        }
    return out


def linear_lifts(vectors, label, words, w, check, nsets=1000):
    x = vectors - vectors.mean(0)
    covariance = x.T @ x / len(x)
    differences = np.vstack(
        [x[label == i].mean(0) - x[label != i].mean(0) for i in range(len(words))]
    )

    def evaluate(v):
        sd = np.sqrt(np.einsum("ij,ij->i", v @ covariance, v))
        if np.any(sd <= 0):
            raise ValueError("Constant Respect direction on the common roster")
        return differences @ v.T / sd

    trained = evaluate(w.mean(0, keepdims=True))[:, 0]
    out = {
        str(word): {"trained": float(value)}
        for word, value in zip(words, trained, strict=True)
    }
    for kind in ("iso", "rot"):
        trial = []
        for i in range(nsets):
            check()
            trial.append(heads(w, "TP69", kind, i).mean(0))
        null = evaluate(np.stack(trial))
        for j, word in enumerate(words):
            out[word][kind] = {
                "band": np.quantile(null[j], [0.025, 0.5, 0.975]).tolist(),
                "percentile": float(
                    100
                    * (
                        np.sum(null[j] < trained[j])
                        + 0.5 * np.sum(null[j] == trained[j])
                    )
                    / nsets
                ),
            }
    return out


def respect(out, check):
    source, archive = fixed()
    with archive as d:
        x, person, label, words = [
            d[k] for k in ("vectors", "writer", "label", "wordNames")
        ]
    ed, intake = ed_situations(Path(".local/readers/data/empathetic-dialogues"))
    if not np.array_equal(words[label], ed.label.to_numpy(str)) or not np.array_equal(
        person, np.unique(ed.writer.to_numpy(str), return_inverse=True)[1]
    ):
        raise ValueError("Chat writer, word or ordering differs")
    base = Path(".local/nine-channel/tp28-a")
    prev = read(bound(base / "receipt.json", TP28))
    if prev["sources"]["ed"]["identity"] != intake or prev["protocol"]["tags"] != list(
        TAGS
    ):
        raise ValueError("TP28 source roster or field names differ")
    saved_tags = saved(base, "ed/scores.npz", prev)
    verify_order(saved_tags, ed.id)
    with np.load(saved_tags, allow_pickle=False) as t:
        tag = t["scores"].astype(float)
    with np.load(
        bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD),
        allow_pickle=False,
    ) as h:
        w = h["weights"]
        if np.max(np.abs(expit(x @ w.T + h["bias"]) - tag)) > 1e-5:
            raise ValueError("Linear tag and saved forecasts differ")
    features, q6 = q6_features(ed, Path(".local/word-table"), check)
    a = read(WEEK / "Q21-transfer.json")
    folder = Path(a["mirror"])
    r = read(bound(folder / "receipt.json", Q21))
    if not a["nativeExited"] or not a["priorFlockReleased"]:
        raise ValueError("Q21 release is unverified")
    with np.load(
        bound(folder / "ed-ten.npz", r["outputs"]["ed-ten.npz"]), allow_pickle=False
    ) as q:
        pride = q["ten"][:, -1]
    if pride.shape != (len(ed),) or not np.isfinite(pride).all():
        raise ValueError("Incomplete PRIDE predictions")
    bridge = out / "pride-responsibility.npz"
    with bridge.open("xb") as f:
        np.savez_compressed(
            f,
            pride=pride,
            writer=person,
            word=words[label],
            own=features[:, FEATURES.index("self_responsblt")],
            other=features[:, FEATURES.index("other_responsblt")],
        )
    raw = features[:, [FEATURES.index(k) for k in PARTS]]
    keep = np.isfinite(raw).all(1) & np.isfinite(tag).all(1)
    if not np.all(raw[keep].std(0) > 0):
        raise ValueError("Constant component of the Competence reading")
    parts = (raw[keep] - raw[keep].mean(0)) / raw[keep].std(0)
    idx = [TAGS.index(k) for k in RESPECT]
    obs = np.column_stack(
        (
            parts.mean(1),
            tag[keep][:, idx].mean(1),
            tag[keep, TAGS.index("belonging")],
            raw[keep, 0],
        )
    )
    owners, code = np.unique(person[keep], return_inverse=True)
    file = profiles(obs, label[keep], code, words, draws(len(owners)), check)
    ref = linear_lifts(x[keep], label[keep], words, w[idx], check)
    result = {
        "card": "TP69",
        "sourceDesignPin": source,
        "sourcePins": {"TP28": TP28, "Q21": Q21, "Q6": q6},
        "sourceReports": len(ed),
        "reports": int(keep.sum()),
        "writers": len(owners),
        "profiles": file,
        "linearRespect": ref,
        "draws": 2000,
        "setsPerFamily": 1000,
        "futureJoinPin": pin(bridge),
        "productionAdmission": False,
    }
    write(out / "table.json", result)
    return result


def grouped_mean(pride, person, mask, authors, weight):
    codes = np.searchsorted(authors, person[mask])
    return ratios(
        weight @ np.bincount(codes, weights=pride[mask], minlength=len(authors)),
        weight @ np.bincount(codes, minlength=len(authors)),
    )


def standing(out, check):
    earlier = ROOT / "TP69-a"
    h = confirmed(earlier)
    r = read(earlier / "receipt.json")["result"]
    with np.load(
        bound(earlier / "pride-responsibility.npz", r["futureJoinPin"]),
        allow_pickle=False,
    ) as z:
        pride, word, person, own, other = [
            z[k] for k in ("pride", "word", "writer", "own", "other")
        ]
    valid = np.isfinite(own) & np.isfinite(other)
    table = {}
    for name, n in (
        ("proud", 867),
        ("impressed", 805),
        ("confident", 785),
        ("grateful", 815),
    ):
        check()
        idx = word == name
        if idx.sum() != n:
            raise ValueError("Standing word roster differs")
        a = idx & valid & (own > other)
        b = idx & valid & (own < other)
        ans = {
            "total": n,
            "own": int(a.sum()),
            "other": int(b.sum()),
            "ties": int((idx & valid & (own == other)).sum()),
            "invalid": int((idx & ~valid).sum()),
        }
        if min(a.sum(), b.sum()) >= 50:
            authors = np.unique(person[a | b])
            weight = draws(len(authors))
            left, right = (
                grouped_mean(pride, person, side, authors, weight) for side in (a, b)
            )
            ans.update(
                writers=len(authors),
                ownMean=estimate(left),
                otherMean=estimate(right),
                difference=estimate(left - right),
            )
        else:
            ans["reason"] = "Fewer than 50 reports on at least one side."
        table[name] = ans
    result = {
        "card": "TP67-original",
        "sourceReceiptPin": h,
        "reports": table,
        "draws": 2000,
        "scope": "B’s original responsibility ratings; the direct standing-mark comparison is pending.",
        "productionAdmission": False,
    }
    write(out / "table.json", result)
    return result
