"""TP68. Fixed chat pairs, writer-held-out logistic forecasts, and a paired word yardstick."""

from itertools import combinations
from pathlib import Path

import numpy as np
from rapid_content import STEMS
from rapid_content import design as chat_design
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, pin, read
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.metrics import roc_auc_score
from tompathy_engine.eval.readers.person_halves import summary
from tompathy_engine.eval.readers.tp28 import MAP, SECONDARY
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.packs.trigger import TAGS
from word_table_lane import write

DESIGN = ROOT / "TP68-design-a"
WORDS = (
    "afraid",
    "angry",
    "anticipating",
    "ashamed",
    "caring",
    "devastated",
    "disgusted",
    "excited",
    "furious",
    "hopeful",
    "lonely",
    "proud",
    "sad",
    "sentimental",
    "terrified",
)
TARGETS = ("embarrassed", *WORDS)
CH = (*CHANNELS, "PRIDE")
P = CH.index("PLAY")
S = CH.index("SHAME")


def design(out, check):
    from tompathy_engine.eval.readers.affect_data import ed_situations
    from tompathy_engine.eval.readers.tp39 import saved
    from week_pride_inputs import FROZEN, SOURCE

    mapped = (
        {w for d in MAP.values() for w in d["ed"]} | set(SECONDARY["ed"]) | {"proud"}
    )
    if sorted(mapped - {"embarrassed"}) != list(WORDS):
        raise ValueError("The covered word list differs from the filed protocol")
    x, w, y, person, fold, *_, meta = chat_design()
    if meta["active"] != list(range(29)) or len(TAGS) != 19 or len(CH) != 10:
        raise ValueError("All 29 original chat outputs are required")
    z = x @ w.T
    z = (z - z.mean(0)) / z.std(0)
    if not np.isfinite(z).all():
        raise ValueError("A standardized chat output has no variance")
    words = np.array(sorted(STEMS))
    if any(
        np.sum(words[y] == k) != n
        for k, n in (("embarrassed", 740), ("ashamed", 628), ("guilty", 760))
    ):
        raise ValueError("Original word counts differ")
    old = read(bound(FROZEN / "receipt.json", SOURCE))
    with np.load(
        saved(FROZEN, "ed-profile-forecasts.npz", old), allow_pickle=False
    ) as f:
        ids = f["ids"].astype(str)
    frame, intake = ed_situations(Path(".local/readers/data/empathetic-dialogues"))
    if intake["intakePin"] != meta["sourceIntake"] or not np.array_equal(
        frame.id.to_numpy(str), ids
    ):
        raise ValueError("The original chat identity differs")
    check()
    inputs = ROOT / "TP65-inputs-a"
    receipt = confirmed(inputs)
    original = read(inputs / "receipt.json")["result"]
    with np.load(
        bound(inputs / "aligned.npz", original["files"]["aligned.npz"]),
        allow_pickle=False,
    ) as a:
        parents = a["parents"]
        ordinal = a["ordinal"]
        source = a["source"]
        oldids = a["original"]
        counts = a["counts"]
        rows = source[parents] == "ed"
        index = {k: i for i, k in enumerate(ids)}
        if set(oldids[source == "ed"]) != set(index):
            raise ValueError("Incomplete sentence-to-chat join")
        post = np.asarray([index[k] for k in oldids[parents[rows]]])
        first = ordinal[rows] == 0
        last = ordinal[rows] == counts[parents[rows]] - 1
        scores = a["forecasts"][rows, P]
        if not np.array_equal(
            np.sort(post[first]), np.arange(len(ids))
        ) or not np.array_equal(np.sort(post[last]), np.arange(len(ids))):
            raise ValueError("Every chat text must have one first and last sentence")
        begins, ends = np.empty(len(ids)), np.empty(len(ids))
        begins[post[first]], ends[post[last]] = scores[first], scores[last]
        lengths = np.bincount(post, minlength=len(ids))
    path = out / "fixed.npz"
    with path.open("xb") as f:
        np.savez(
            f,
            vectors=x,
            outputs=z,
            label=y,
            writer=person,
            fold=fold,
            wordNames=words,
            playDifference=ends - begins,
            sentenceCounts=lengths,
        )
    return {
        "card": "TP68-design",
        "source": meta,
        "sentenceSource": receipt,
        "covered": list(WORDS),
        "criterion": "Five original writer folds; all 29 chat scores available.",
        "filePin": pin(path),
        "protocolPin": pin(Path("docs/exchange/result-sheets/TP68.md")),
    }


def fixed():
    h = confirmed(DESIGN)
    info = read(DESIGN / "receipt.json")["result"]
    if tuple(info["covered"]) != WORDS:
        raise ValueError("The designated comparison words changed")
    return h, np.load(bound(DESIGN / "fixed.npz", info["filePin"]), allow_pickle=False)


def train(x, y, check):
    n = len(x)
    if y.min() == y.max() or not np.isfinite(x).all():
        raise ValueError("Both outcomes and finite inputs are required")

    def objective(theta):
        check()
        z = x @ theta[:-1] + theta[-1]
        residual = (expit(z) - y) / n
        value = np.mean(np.logaddexp(0, z) - y * z) + np.sum(theta[:-1] ** 2) / (6 * n)
        return value, np.r_[x.T @ residual + theta[:-1] / (3 * n), residual.sum()]

    fit = minimize(
        objective,
        np.zeros(x.shape[1] + 1),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 2000, "ftol": 1e-10, "gtol": 1e-6, "maxls": 50},
    )
    if not fit.success:
        raise RuntimeError("Word head stopped: " + str(fit.message))
    return fit.x, int(fit.nit)


def fit_fold(out, index, check):
    source, archive = fixed()
    files = {}
    with archive as d:
        fold = d["fold"]
        labels = d["wordNames"][d["label"]]
        owner = d["writer"]
        test = fold == index
        if set(owner[test]) & set(owner[~test]):
            raise ValueError("Writer appears on both sides")
        for key, x in (
            ("vector", d["vectors"]),
            ("outputs", d["outputs"]),
            ("blend", d["outputs"][:, [19 + S, 19 + P]]),
        ):
            learn = x[~test]
            held = x[test]
            targets = ("embarrassed",) if key == "blend" else TARGETS
            for name in targets:
                check()
                theta, nit = train(learn, (labels[~test] == name).astype(float), check)
                prediction = held @ theta[:-1] + theta[-1]
                if not np.isfinite(prediction).all():
                    raise ValueError("Nonfinite held-out forecasts")
                p = out / (key + "-" + name + ".npz")
                with p.open("xb") as f:
                    np.savez_compressed(
                        f, index=np.flatnonzero(test), forecast=prediction, theta=theta
                    )
                files[p.name] = pin(p)
                write(
                    out / "progress.json",
                    {
                        "fold": index,
                        "completed": len(files),
                        "latest": key + " " + name,
                        "iterations": nit,
                    },
                )
    return {
        "card": "TP68-fold",
        "fold": index,
        "designReceiptPin": source,
        "files": files,
        "heldOut": int(test.sum()),
    }


def auc_draws(y, scores, owner, weights, check):
    """Writer-weighted concordance from tie-aware positive/negative writer pairs."""
    if not np.isfinite(scores).all() or y.all() or not y.any():
        raise ValueError("AUC requires finite predictions and both classes")
    pos = scores[y]
    who = owner[y]
    n = weights.shape[1]
    pairs = np.zeros((n, n))
    negative = scores[~y]
    negwho = owner[~y]
    for j in np.unique(negwho):
        negatives = np.sort(negative[negwho == j])
        wins = (
            np.searchsorted(negatives, pos, "left")
            + np.searchsorted(negatives, pos, "right")
        ) / 2
        pairs[:, j] = np.bincount(who, weights=wins, minlength=n)
    present = np.unique(who)
    denom = (weights @ np.bincount(who, minlength=n)) * (
        weights @ np.bincount(negwho, minlength=n)
    )
    numer = []
    for block in np.array_split(weights, 8):
        check()
        numer.append(np.sum((block[:, present] @ pairs[present]) * block, axis=1))
    result = np.divide(
        np.concatenate(numer), denom, out=np.full(len(denom), np.nan), where=denom > 0
    )
    if abs(result[0] - roc_auc_score(y, scores)) > 1e-10:
        raise ValueError("Paired weighted AUC failed its unit-weight check")
    return result


def estimate(x, bar=0.0):
    value = float(x[0])
    draws = x[1:]
    r = summary(value, draws)
    valid = draws[np.isfinite(draws)]
    if r["interval"] is not None and len(valid) > 1:
        se = float(np.std(valid, ddof=1))
        r.update(
            standardError=se,
            nearBar=min(abs(t - bar) for t in r["interval"]) <= se,
            pAboveBar=float(
                (1 + np.sum(valid - value >= value - bar)) / (len(valid) + 1)
            ),
        )
    return r


def returns(out, check):
    h, archive = fixed()
    with archive as z:
        labels = z["wordNames"][z["label"]]
        owners = z["writer"]
        folds = z["fold"]
        scores = z["outputs"][:, 19:]
        diff, length = z["playDifference"], z["sentenceCounts"]
    members = len(np.unique(owners))
    rng = np.random.default_rng(23)
    weights = np.vstack(
        (
            np.ones(members),
            rng.multinomial(members, np.full(members, 1 / members), size=2000),
        )
    )
    timing = {}
    for name in ("embarrassed", "ashamed", "guilty"):
        select = (labels == name) & (length >= 2)
        n = np.bincount(owners[select], minlength=members)
        sums = np.bincount(owners[select], weights=diff[select], minlength=members)
        den = weights @ n
        stat = np.divide(
            weights @ sums, den, out=np.full(len(weights), np.nan), where=den > 0
        )
        timing[name] = {
            "reports": int(select.sum()),
            "writers": int(np.sum(n > 0)),
            **estimate(stat),
        }
    y = labels == "embarrassed"
    blends = {}
    for a, b in combinations(range(10), 2):
        v = auc_draws(y, scores[:, a] + scores[:, b], owners, weights, check)
        blends[(a, b)] = v
    selected = tuple(sorted((P, S)))
    other = np.max(np.stack([v for k, v in blends.items() if k != selected]), axis=0)
    single = np.maximum(
        *[auc_draws(y, scores[:, j], owners, weights, check) for j in (P, S)]
    )
    table = {CH[a] + " + " + CH[b]: estimate(v, 0.5) for (a, b), v in blends.items()}
    blend = {
        "rank": 1 + int(sum(v[0] > blends[selected][0] for v in blends.values())),
        "tiedAtPoint": int(sum(v[0] == blends[selected][0] for v in blends.values())),
        "againstBestOtherPair": estimate(blends[selected] - other),
        "againstBetterSingle": estimate(blends[selected] - single),
        "pairs": table,
    }
    forecasts = {
        (k, n): np.full(len(owners), np.nan)
        for k in ("vector", "outputs")
        for n in TARGETS
    }
    forecasts["blend", "embarrassed"] = np.full(len(owners), np.nan)
    receipts = []
    for i in range(5):
        folder = ROOT / f"TP68-fold-{i}-a"
        receipts.append(confirmed(folder))
        src = read(folder / "receipt.json")["result"]
        if src["designReceiptPin"] != h or src["fold"] != i:
            raise ValueError("Fold design or identity differs")
        for (kind, name), values in forecasts.items():
            p = folder / (kind + "-" + name + ".npz")
            with np.load(bound(p, src["files"][p.name]), allow_pickle=False) as f:
                idx = f["index"]
                if (
                    not np.array_equal(idx, np.flatnonzero(folds == i))
                    or np.isfinite(values[idx]).any()
                ):
                    raise ValueError("Prediction overlap or different held-out writers")
                values[idx] = f["forecast"]
    gains = {}
    yard = {}
    for name in TARGETS:
        y = labels == name
        a, b = [
            auc_draws(y, forecasts[k, name], owners, weights, check)
            for k in ("vector", "outputs")
        ]
        gains[name] = a - b
        yard[name] = {
            "vectorAUC": estimate(a, 0.5),
            "outputsAUC": estimate(b, 0.5),
            "gain": estimate(a - b),
        }
        if name == "embarrassed":
            mixed = auc_draws(y, forecasts["blend", name], owners, weights, check)
            descr = {
                "fittedPairAUC": estimate(mixed, 0.5),
                "dedicatedMinusPair": estimate(a - mixed, 0.02),
            }
    strongest = np.max(np.stack([gains[n] for n in WORDS]), axis=0)
    lead = estimate(gains["embarrassed"] - strongest)
    ans = {
        "card": "TP68",
        "designReceiptPin": h,
        "foldReceiptPins": receipts,
        "covered": list(WORDS),
        "firstLastPlay": timing,
        "unfittedBlend": blend,
        "wordYardstick": yard,
        "leadOverCovered": lead,
        "dedicatedVsFittedPair": descr,
        "reports": len(owners),
        "writers": members,
        "draws": len(weights) - 1,
        "playCheck": "Chat has no mapped PLAY word with which to qualify the PLAY discrimination check.",
        "scope": "Assigned words and their subject matter. Where the blend ranks below first, an additional role for PLAY remains open.",
        "productionAdmission": False,
    }
    write(out / "tables.json", ans)
    return ans
