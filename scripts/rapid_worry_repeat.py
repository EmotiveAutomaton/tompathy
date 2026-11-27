"""TP61(b). Worry and linear head repeat on TP52's original dated halves."""

import gzip
import json
from pathlib import Path

import numpy as np
from rapid_head_check import HEAD, Q20, bound, pin, read
from rapid_nulls import heads
from word_table_lane import write

ROOT = Path(".local/rapid-20261127")
WEEK = Path(".local/week-20261122")
PREP = "258d14c8405973cb7db874895a18a46e054241c3638e89d39bf73aef7941f02d"
TP52 = "2f7236ded4408f4da09edcbcca63f57f9419aa4cd27f034064d49c4edf97577b"
ROSTER = "325e50a56fd4d84da7d58321c39a88567e5907770bdaaa1b7ba064442710eff2"


def vector_return():
    transfer = read(ROOT / "TP61-vector-transfer.json")
    folder = Path(transfer["mirror"])
    source = read(bound(folder / "receipt.json", PREP))
    if not (
        transfer["nativeExited"]
        and transfer["cpuLeaseReacquired"]
        and transfer["receiptPin"] == PREP
    ) or (
        source["q20SourceReceiptPin"],
        source["rosterPin"],
    ) != (Q20, ROSTER):
        raise ValueError("Verified TP61 vector return required")
    return folder, source


def worry_halves(owners, counts, check):
    handoff = read(WEEK / "Q20-transfer.json")
    mirror = Path(handoff["mirror"])
    source = read(bound(mirror / "receipt.json", Q20))
    if not handoff["nativeExited"] or not handoff["priorFlockReleased"]:
        raise ValueError("Verified original Q20 output required")
    ids = {}
    parts = []
    path = bound(ROOT / "TP61-roster-a/author-order.jsonl.gz", ROSTER)
    with gzip.open(path, "rt", encoding="utf8") as f:
        for i, line in enumerate(f):
            name, sides = json.loads(line)
            if i >= len(owners) or name != owners[i]:
                raise ValueError("TP52 author order differs")
            half = [[], []]
            if counts[i].all():
                for side in sides:
                    for key, rate, h in side:
                        if rate is not None and h is not None:
                            half[h].append(ids.setdefault(key, len(ids)))
            if list(map(len, half)) != counts[i].tolist():
                raise ValueError("Worry opening counts disagree with vector means")
            parts.append(half)
    if len(parts) != len(owners):
        raise ValueError("Incomplete TP52 roster")
    values = np.full(len(ids), np.nan)
    for name, digest in source["outputs"].items():
        if not name.startswith("scores-"):
            continue
        check()
        if handoff["files"].get(name) != digest:
            raise ValueError("Original transfer inventory differs")
        with np.load(bound(mirror / name, digest), allow_pickle=False) as f:
            keys = f["ids"].astype(str)
            take = [j for j, key in enumerate(keys) if key in ids]
            if not take:
                continue
            dest = np.array([ids[keys[j]] for j in take])
            if len(np.unique(dest)) != len(dest) or np.isfinite(values[dest]).any():
                raise ValueError("Duplicated saved worry forecast")
            values[dest] = f["worry"].reshape(len(keys))[take]
    if not np.isfinite(values).all():
        raise ValueError("Missing saved worry forecasts")
    return np.asarray(
        [[values[a].mean(), values[b].mean()] for a, b in parts if a and b]
    )


def moments(left, right):
    left = left - left.mean(0)
    right = right - right.mean(0)
    return left.T @ left, left.T @ right, right.T @ right


def repeats(gram, weights):
    a, ab, b = [np.einsum("ij,ij->i", weights @ g, weights) for g in gram]
    if not np.all((a > 0) & (b > 0)):
        raise ValueError("Constant author-level head")
    return ab / np.sqrt(a * b)


def distribution(values, target):
    lo, median, hi = np.percentile(values, [2.5, 50, 97.5])
    return {
        "low": float(lo),
        "median": float(median),
        "high": float(hi),
        "trainedPercentile": float(
            100 * (np.mean(values < target) + 0.5 * np.mean(values == target))
        ),
        "position": "above" if target > hi else "below" if target < lo else "inside",
    }


def prepare(out, check):
    from tompathy_engine.eval.readers.person_halves import (
        correlations,
        resamples,
        summary,
    )

    folder, source = vector_return()

    def load(name, field):
        with np.load(
            bound(folder / name, source["files"][name]), allow_pickle=False
        ) as f:
            return f[field]

    with np.load(
        bound(folder / "author-index.npz", source["files"]["author-index.npz"])
    ) as index:
        owners = index["authors"].astype(str)
        counts = np.column_stack([index[f"worry{h}"] for h in (0, 1)])
    keep = (counts > 0).all(axis=1)
    if keep.sum() != 2527 or len(owners) != 5428:
        raise ValueError("Wrong original TP52 cohort")
    left, right = [load(f"mean-worry{h}.npz", "x")[keep] for h in (0, 1)]
    worry = worry_halves(owners, counts, check)
    with np.load(bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD)) as f:
        w = f["weights"].astype(float)
    old = read(bound(WEEK / "TP52-a/receipt.json", TP52))["stability"]
    a, b = (
        np.column_stack([worry[:, 0], left @ w.T]),
        np.column_stack([worry[:, 1], right @ w.T]),
    )
    actual = correlations(a, b, np.ones((1, len(a))))[0]
    cov = moments(left, right)
    if not np.allclose(repeats(cov, w), actual[1:], atol=1e-10, rtol=0):
        raise ValueError("Projected repeat contradicts direct round trip")
    if abs(actual[0] - old["readings"]["worry"]["value"]) > 1e-7:
        raise ValueError("Saved worry repeat did not reproduce")
    results = []
    for batch in np.array_split(resamples(len(a)), 40):
        check()
        results.append(correlations(a, b, batch))
    bootstrap = np.concatenate(results)
    trained_delta = actual[0] - np.median(actual[1:])
    trained = {
        "worry": summary(actual[0], bootstrap[:, 0]),
        "medianLinearTag": summary(
            np.median(actual[1:]), np.median(bootstrap[:, 1:], axis=1)
        ),
        "worryMinusMedianLinearTag": summary(
            trained_delta, bootstrap[:, 0] - np.median(bootstrap[:, 1:], axis=1)
        ),
        "originalWorryMinusMedianSquashedTag": old["worryMinusMedianTag"],
    }
    files, nulls = {}, {}
    for family in ("iso", "rot"):
        vectors = []
        for i in range(1000):
            if i % 10 == 0:
                check()
            values = repeats(cov, heads(w, "TP61", family, i))
            vectors.append(values)
            if (i + 1) % 50 == 0:
                shard = out / f"{family}-{i - 49:04d}.npy"
                with shard.open("xb") as f:
                    np.save(f, np.stack(vectors[-50:]), allow_pickle=False)
                files[shard.name] = pin(shard)
                write(out / "progress.json", {"family": family, "sets": i + 1})
        arr = np.stack(vectors)
        medians = np.median(arr, axis=1)
        nulls[family] = {
            "sets": len(arr),
            "headsPerSet": arr.shape[1],
            "fixedWorryMinusMedian": distribution(actual[0] - medians, trained_delta),
            "medianHeadRepeat": distribution(medians, np.median(actual[1:])),
            "individualHeadRepeatAgainstWorry": distribution(arr.ravel(), actual[0]),
        }
    return {
        "card": "TP61(b)",
        "authors": len(a),
        "vectorReceiptPin": PREP,
        "worryReceiptPin": TP52,
        "tagHeadPin": HEAD,
        "nulls": nulls,
        "trained": trained,
        "privateShards": files,
        "interpretation": "Compare the same worry reading minus the median of 19 trained or random linear heads. Individual random repeats are also shown relative to worry. Heads within a set share one orientation.",
    }
