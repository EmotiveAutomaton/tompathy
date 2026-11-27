"""TP63. Cleared writer-level reader outputs against the five specified self-ratings."""

import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rapid_content import PRIDE, Q21, WEEK
from rapid_cpu_dispatch import ROOT
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_sentence_data import Q34
from scipy.special import expit
from scipy.stats import rankdata
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28, saved
from tompathy_engine.packs.trigger import TAGS
from week_pride_inputs import FROZEN, SOURCE
from word_table_lane import write

KEYS = {
    "Extraversion": ("extravert", "quiet"),
    "Agreeableness": ("sympathetic", "critical"),
    "Conscientiousness": ("dependable", "disorganized"),
    "Emotional stability": ("calm", "anxious"),
    "Openness": ("open", "conventional"),
}
GENERATION = Path(
    ".local/readers/data/crowd-enVent2023/corpus/crowd-enVent_generation.tsv"
)
REG = "2aaa9e0fc722a48e40e854b61dddc9b9c2a03828233e2c0fc3175afdcffa7f6a"
OPTIONS = {
    "LUST": "wanting",
    "PLAY": "amusement",
    "PANIC/GRIEF": "SADNESS",
    "belonging": "acceptance",
}


def writer_traits(frame, owners):
    """One unambiguous released value per item per person, including fractional source averages."""
    fields = [key for pair in KEYS.values() for key in pair]
    raw = frame[fields].replace(
        {"": np.nan, "NA": np.nan, "N/A": np.nan, "nan": np.nan}
    )
    items = raw.apply(pd.to_numeric, errors="raise")
    if ((items < 1) | (items > 7)).any().any():
        raise ValueError("Source item falls outside the documented scale")
    grouped = items.groupby(frame["prolific_id"], sort=True)
    low, high = grouped.min().reindex(owners), grouped.max().reindex(owners)
    values = []
    census = {}
    for trait, (plus, minus) in KEYS.items():
        pair = [plus, minus]
        missing = low[pair].isna().any(axis=1)
        conflict = (high[pair] - low[pair]).abs().max(axis=1) > 1e-9
        score = ((low[plus] + 8 - low[minus]) / 2).mask(conflict | missing)
        values.append(score.to_numpy(float))
        census[trait] = {
            "available": int(score.notna().sum()),
            "missingItem": int(missing.sum()),
            "conflictingItem": int(conflict.sum()),
        }
    return np.column_stack(values), census


def means(values, codes):
    labels = np.bincount(codes)
    result = np.zeros((len(labels), values.shape[1]), dtype=float)
    np.add.at(result, codes, values)
    return result / labels[:, None]


def writer_values(values, feeling, writer):
    return means(values - means(values, feeling)[feeling], writer)


def norm_ranks(x):
    ranks = rankdata(x, axis=0, method="average")
    ranks -= ranks.mean(axis=0)
    den = np.linalg.norm(ranks, axis=0)
    return np.divide(ranks, den, out=np.full_like(ranks, np.nan), where=den > 0)


def correlations(x, y):
    return norm_ranks(x).T @ norm_ranks(y)


def subsets(targets):
    groups = {}
    for j in range(targets.shape[1]):
        idx = np.flatnonzero(np.isfinite(targets[:, j]))
        if len(idx) < 3:
            raise ValueError("Fewer than three writers with a trait pair")
        groups.setdefault(idx.tobytes(), (idx, []))[1].append(j)
    return list(groups.values())


def fit_table(outputs, traits, check, nboot=2000, seed=23):
    r = np.full((outputs.shape[1], traits.shape[1]), np.nan)
    draws = np.full((nboot, *r.shape), np.nan)
    for idx, js in subsets(traits):
        x = outputs[idx]
        y = traits[np.ix_(idx, js)]
        r[:, js] = correlations(x, y)
        rng = np.random.default_rng(seed)
        for b in range(nboot):
            if b % 25 == 0:
                check()
            chosen = rng.integers(len(idx), size=len(idx))
            draws[b][:, js] = correlations(x[chosen], y[chosen])
    return r, draws


def controls(vectors, weights, traits, check, nsets=200):
    masks = [
        (idx, js, norm_ranks(traits[np.ix_(idx, js)])) for idx, js in subsets(traits)
    ]
    all_sets = {}
    for kind in ("iso", "rot"):
        values = np.empty((nsets, len(weights), traits.shape[1]))
        for i in range(nsets):
            check()
            x = vectors @ heads(weights, "TP63", kind, i).T
            for idx, js, ty in masks:
                values[i][:, js] = norm_ranks(x[idx]).T @ ty
        if not np.isfinite(values).all():
            raise ValueError("A trait or a registered control has no variance")
        all_sets[kind] = np.abs(values)
    return all_sets


def model_data():
    original = read(bound(FROZEN / "receipt.json", SOURCE))
    report = bound(GENERATION, original["sources"]["envent"]["files"]["generation"])
    columns = [
        "text_id",
        "prolific_id",
        "emotion",
        *(k for pair in KEYS.values() for k in pair),
    ]
    frame = pd.read_csv(
        report,
        sep="\t",
        quoting=csv.QUOTE_NONE,
        usecols=columns,
        dtype=str,
        keep_default_na=False,
    )
    if (
        len(frame) != 6600
        or frame.text_id.duplicated().any()
        or frame.prolific_id.eq("").any()
    ):
        raise ValueError("Released report identity or writer field differs")
    with np.load(
        saved(FROZEN, "envent-profile-forecasts.npz", original), allow_pickle=False
    ) as f:
        ids = f["ids"].astype(str)
    if len(ids) != len(frame) or set(ids) != set(frame.text_id):
        raise ValueError("Stored event forecasts do not cover the released reports")
    ordered = frame.set_index("text_id", verify_integrity=True).loc[ids].reset_index()
    owners, person = np.unique(ordered.prolific_id.to_numpy(str), return_inverse=True)
    labels, event = np.unique(ordered.emotion.to_numpy(str), return_inverse=True)
    if (len(owners), len(labels)) != (2379, 13):
        raise ValueError("Unexpected writer or assigned-feeling roster")
    with np.load(saved(FROZEN, "vectors.npz", original), allow_pickle=False) as f:
        x = f["envent"].astype(float)
    with np.load(
        saved(FROZEN, "go_only-profile-head.npz", original), allow_pickle=False
    ) as head:
        ch = head["parameters"]
        active = head["active"].astype(int)
    models = WEEK / "TP58-candidate-b/payload/models"
    with (
        np.load(bound(models / "tags.npz", HEAD), allow_pickle=False) as tag,
        np.load(bound(models / "pride.npz", PRIDE), allow_pickle=False) as pride,
    ):
        w = np.vstack((tag["weights"], ch[:-1].T, pride["theta"][:-1]))
        b = np.r_[tag["bias"], ch[-1], pride["theta"][-1]]
    linear = x @ w.T + b
    tp28 = Path(".local/nine-channel/tp28-a")
    tp28_r = read(bound(tp28 / "receipt.json", TP28))
    path = saved(tp28, "envent/scores.npz", tp28_r)
    verify_order(path, ids)
    audit = read(WEEK / "Q21-transfer.json")
    q = Path(audit["mirror"])
    qr = read(bound(q / "receipt.json", Q21))
    if not audit["nativeExited"] or not audit["priorFlockReleased"]:
        raise ValueError("Unverified Q21 source release")
    with (
        np.load(path, allow_pickle=False) as tags,
        np.load(
            bound(q / "envent-ten.npz", qr["outputs"]["envent-ten.npz"]),
            allow_pickle=False,
        ) as ten,
    ):
        ten_values = ten["ten"]
        inactive = np.setdiff1d(np.arange(9), active)
        if np.any(np.ptp(ten_values[:, inactive], axis=0) != 0):
            raise ValueError("An omitted event channel varies")
        saved_scores = np.column_stack(
            (tags["scores"], ten_values[:, active], ten_values[:, -1])
        )
    gap = float(np.max(np.abs(expit(linear) - saved_scores)))
    if not np.isfinite(gap) or gap > 0.00001:
        raise ValueError("Event linear head binding differs from saved scores")
    names = list(TAGS) + [CHANNELS[j] for j in active] + ["PRIDE"]
    keep = np.ptp(saved_scores, axis=0) > 0
    omitted = [CHANNELS[j] for j in inactive] + [
        n for n, k in zip(names, keep, strict=True) if not k
    ]
    names = [OPTIONS.get(n, n) for n, k in zip(names, keep, strict=True) if k]
    traits, census = writer_traits(ordered, owners)
    return (
        frame,
        ids,
        writer_values(x, event, person),
        w[keep],
        traits,
        names,
        census,
        event,
        person,
        omitted,
        gap,
    )


def worry_values(frame, ids):
    cfg = read(bound(ROOT / "registration.json", REG))
    manifest = read(bound(ROOT / "inputs/inputs.json", cfg["inputManifest"]))
    audit = read(ROOT / "Q34-b-transfer.json")
    folder = Path(audit["mirror"])
    rec = read(bound(folder / "receipt.json", Q34))
    if (
        not audit["nativeExited"]
        or not audit["ownedFlockReleased"]
        or audit["sourceReceiptPin"] != Q34
        or rec["result"]["parts"]["envent"] != 6600
    ):
        raise ValueError("Q34 terminal return differs")
    source = ROOT / "inputs/envent.jsonl.gz"
    with gzip.open(
        bound(source, manifest["files"][source.name]), "rt", encoding="utf8"
    ) as f:
        opaque = [json.loads(row)["id"] for row in f]
    expected = [
        hashlib.sha256(("R37:23:envent:" + i).encode()).hexdigest()
        for i in frame.text_id
    ]
    if opaque != expected:
        raise ValueError("Q34 report order differs")
    scores = []
    for start in range(0, len(ids), 100):
        name = f"envent-{start:07d}.npz"
        with np.load(
            bound(folder / name, rec["artifacts"][name]), allow_pickle=False
        ) as f:
            scores.extend(f["worry"].ravel())
    series = pd.Series(scores, index=frame.text_id).reindex(ids).to_numpy(float)
    if series.shape != (6600,) or not np.isfinite(series).all():
        raise ValueError("Invalid worry forecast return")
    return series


def tables(values, draws, bands, names, census):
    traits = list(KEYS)
    bars = {}
    for kind, null in bands.items():
        bars[kind] = {
            "family": float(np.quantile(null.max(axis=(1, 2)), 0.95)),
            "trait": dict(
                zip(traits, np.quantile(null, 0.975, axis=(0, 1)).tolist(), strict=True)
            ),
        }
    result = {}
    for i, name in enumerate(names):
        result[name] = {}
        for j, t in enumerate(traits):
            point = values[i, j]
            sample = draws[:, i, j]
            sample = sample[np.isfinite(sample)]
            if not np.isfinite(point) or len(sample) < 2:
                result[name][t] = {
                    "value": None,
                    "reason": "No rank variation",
                    "writers": census[t]["available"],
                }
                continue
            lo, hi = np.quantile(sample, [0.025, 0.975])
            se = float(sample.std(ddof=1))
            direction = 1 if point >= 0 else -1
            ends = np.sort(direction * np.array([lo, hi]))
            ref = bars["rot"]
            thresholds = [0, ref["family"], ref["trait"][t]]
            result[name][t] = {
                "value": float(point),
                "interval": [float(lo), float(hi)],
                "standardError": se,
                "writers": census[t]["available"],
                "validDraws": len(sample),
                "pointAboveRotFamily": bool(abs(point) > ref["family"]),
                "pointAboveRotTrait": bool(abs(point) > ref["trait"][t]),
                "intervalExcludesZero": bool(lo > 0 or hi < 0),
                "nearBar": any(
                    float(np.min(np.abs(ends - bar))) <= se for bar in thresholds
                ),
                "leadsRow": bool(abs(point) >= np.nanmax(np.abs(values[i, :]))),
                "leadsColumn": bool(abs(point) >= np.nanmax(np.abs(values[:, j]))),
                "twoSidedP": min(
                    1.0,
                    2
                    * min(
                        1 + np.count_nonzero(sample <= 0),
                        1 + np.count_nonzero(sample >= 0),
                    )
                    / (len(sample) + 1),
                ),
            }
    return bars, result


def prepare(out, check):
    frame, ids, x, w, traits, names, census, feel, person, omitted, gap = model_data()
    check()
    worry = writer_values(worry_values(frame, ids)[:, None], feel, person)
    observed = np.column_stack((x @ w.T, worry))
    r, draws = fit_table(observed, traits, check)
    sets = controls(x, w, traits, check)
    bars, result = tables(r, draws, sets, [*names, "worry"], census)
    ans = {
        "card": "TP63-original",
        "sourceForecastPin": SOURCE,
        "tagsReceipt": TP28,
        "tenReceipt": Q21,
        "worryReceipt": Q34,
        "protocolPin": pin(Path("docs/exchange/result-sheets/TP63.md")),
        "reports": len(ids),
        "writers": len(x),
        "targets": census,
        "linearProbabilityMaxGap": gap,
        "constantColumnsOmitted": omitted,
        "bootstrapDraws": len(draws),
        "nullSetsPerFamily": 200,
        "nullHeadsPerSet": len(w),
        "bars": bars,
        "outputs": result,
        "worryControl": "Reference bands use the need encoder; the separate worry encoder has no matched saved vectors here.",
        "essayArm": "No held essay trait fields.",
        "readerFeatures": "Pending verified Q28.",
        "productionAdmission": False,
    }
    write(out / "table.json", ans)
    return ans
