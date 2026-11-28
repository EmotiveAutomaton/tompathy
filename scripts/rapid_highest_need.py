"""TP61(a) repeat of the highest linear group on paired blog-author date halves."""

import hashlib

import numpy as np
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_worry_repeat import PREP, ROOT, ROSTER, WEEK, distribution, vector_return
from week_need_losses import GROUPS, TAGS
from word_table_lane import write

SCALE = "93f8416f1a83c622460ae864b975350f4b4220374895a187358a51a282b0f6ce"
TP46 = "37ff959e4166418a9080d443632f137b0cf9b8e76d65e07b732d9a43e50bd401"
PLACED = {name: tags for name, tags in GROUPS.items() if name != "unplaced"}


def allocation(family, i):
    seed = hashlib.sha256(f"TP61:groups:{family}:{i}".encode()).digest()[:8]
    order = np.random.default_rng(int.from_bytes(seed, "big")).permutation(len(TAGS))
    sizes = [len(v) for v in PLACED.values()]
    return np.split(order[: sum(sizes)], np.cumsum(sizes)[:-1])


def leaders(halves, covariance, directions, groups):
    variance = np.einsum("ij,ij->i", directions @ covariance, directions)
    grouped = []
    for indices in groups:
        valid = indices[variance[indices] > 0]
        if not len(valid):
            raise ValueError("No varying directions in a highest-need group")
        grouped.append((directions[valid] / np.sqrt(variance[valid, None])).mean(0))
    values = halves @ np.stack(grouped).T
    maximum = values == values.max(axis=-1, keepdims=True)
    return maximum / maximum.sum(axis=-1, keepdims=True)


def statistic(pair, weights):
    left, right = pair
    weights = weights / weights.sum(axis=-1, keepdims=True)
    observed = weights @ (left * right).sum(axis=1)
    dealt = ((weights @ left) * (weights @ right)).sum(axis=-1)
    return np.stack([observed, dealt, observed - dealt], axis=-1)


def inputs():
    folder, source = vector_return()
    scale = ROOT / "TP61-scale-return-a"
    transfer = read(scale / "transfer.json")
    r = read(bound(scale / "receipt.json", SCALE))
    if not (
        transfer["nativeExited"]
        and transfer["cpuLeaseReacquired"]
        and transfer["receipt"] == r
        and transfer["files"]["receipt.json"] == SCALE
        and (r["source"], r["roster"]) == (PREP, ROSTER)
    ):
        raise ValueError("Verified calibration return required")
    with np.load(bound(scale / "scale.npz", r["scalePin"]), allow_pickle=False) as f:
        mean, cov = f["mean"], f["covariance"]

    def saved(name):
        return np.load(bound(folder / name, source["files"][name]), allow_pickle=False)

    with saved("author-index.npz") as f:
        counts = np.stack([f["date0"], f["date1"]])
        keep = (counts > 0).all(0)
    halves = []
    for i in range(2):
        with saved(f"mean-date{i}.npz") as f:
            halves.append(f["x"][keep])
    halves = np.stack(halves)
    counts = counts[:, keep]
    if (r["authors"], r["openings"]) != (int(keep.sum()), int(counts.sum())):
        raise ValueError("Occurrence counts differ from the dated vector return")
    roundtrip = np.einsum("han,ha->n", halves, counts) / counts.sum()
    np.testing.assert_allclose(mean, roundtrip, rtol=0, atol=1e-12)
    with np.load(
        bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD),
        allow_pickle=False,
    ) as f:
        weights = f["weights"].astype(float)
    previous = read(bound(WEEK / "TP46-a/receipt.json", TP46))["highestNeed"][
        "separate"
    ]
    if weights.shape != (len(TAGS), 384) or not np.isfinite(halves).all():
        raise ValueError("Unexpected dated profiles or tag-head dimensions")
    return halves - mean, cov, weights, r, previous


def prepare(out, check):
    from tompathy_engine.eval.readers.person_halves import resamples, summary

    halves, cov, w, scale, previous = inputs()
    indexes = [np.asarray([TAGS.index(t) for t in group]) for group in PLACED.values()]
    n = halves.shape[1]
    equal = np.ones(n)
    pair = leaders(halves, cov, w, indexes)
    point = statistic(pair, equal)
    draws = []
    for batch in np.array_split(resamples(n), 40):
        check()
        draws.append(statistic(pair, batch))
    draws = np.concatenate(draws)
    names = ["paired", "dealt", "difference"]
    trained = {name: summary(point[i], draws[:, i]) for i, name in enumerate(names)}
    bands = {}
    files = {}
    for family in ("iso", "rot"):
        rows = []
        for i in range(1000):
            if i % 10 == 0:
                check()
            pair = leaders(
                halves, cov, heads(w, "TP61", family, i), allocation(family, i)
            )
            rows.append(statistic(pair, equal))
            if (i + 1) % 50 == 0:
                dest = out / f"{family}-{i - 49:04d}.npy"
                with dest.open("xb") as f:
                    np.save(f, np.stack(rows[-50:]), allow_pickle=False)
                files[dest.name] = pin(dest)
                write(out / "progress.json", {"family": family, "sets": i + 1})
        arr = np.stack(rows)
        bands[family] = {
            name: distribution(arr[:, i], point[i]) for i, name in enumerate(names)
        }
    result = {
        "authors": n,
        "openings": scale["openings"],
        "distinctOpenings": scale["distinct"],
        "vectorReceipt": PREP,
        "scaleReceipt": SCALE,
        "TP46Receipt": TP46,
        "headPin": HEAD,
        "groups": {
            ("acceptance" if k == "belongingTag" else k): len(v)
            for k, v in PLACED.items()
        },
        "draws": len(draws),
        "setsPerFamily": 1000,
        "trained": trained,
        "controls": bands,
        "originalTP46": {k: previous[k] for k in ("paired", "dealt")},
    }
    write(out / "shards.json", files)
    write(out / "table.json", result)
    return result
