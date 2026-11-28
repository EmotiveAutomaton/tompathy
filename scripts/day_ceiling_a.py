"""TP81 first build, using grouped sums and resampling multiplicities."""

import numpy as np


def totals(y, group):
    total = np.zeros((group.max() + 1, y.shape[1]))
    np.add.at(total, group, y)
    return total


def moments(y, group):
    k = np.bincount(group)
    sums = totals(y, group)
    m = sums / k[:, None]
    within = totals((y - m[group]) ** 2, group)
    return k, sums, k[:, None] * m**2, within


def components(data, counts):
    k, s, b, w = data
    n = counts @ k
    people = counts.sum()
    between = (counts @ b - (counts @ s) ** 2 / n) / (people - 1)
    within = (counts @ w) / (n - people)
    eff = (n - counts @ (k**2) / n) / (people - 1)
    icc = np.clip((between - within) / (between + (eff - 1) * within), 0, 1)
    rel = icc / (icc + (1 - icc) * ((counts @ (1 / k)) / people))
    return icc, rel, np.maximum(0, 1 - within / between)


def correlation(x, y):
    x = x - x.mean(axis=0)
    y = y - y.mean(axis=0)
    return (x * y).sum(axis=0) / np.sqrt((x * x).sum(axis=0) * (y * y).sum(axis=0))


def build(d, check):
    x, w, writer, feeling = d["x"], d["w"], d["person"], d["feeling"]
    k = np.bincount(writer)
    unit = np.ones(len(k))

    def clear(y):
        return y - (totals(y, feeling) / np.bincount(feeling)[:, None])[feeling]

    x = clear(x)
    y = np.column_stack((x @ w.T, clear(d["worry"].reshape(-1, 1))))
    data = moments(y, writer)
    icc, rel, plain = components(data, unit)
    draw = []
    for n, idx in enumerate(d["draws"]):
        if n % 50 == 0:
            check()
        draw.append(components(data, np.bincount(idx, minlength=len(k)))[1])
    intervals = np.quantile(draw, [0.025, 0.975], axis=0).T
    split = []
    starts = np.r_[0, np.cumsum(k)[:-1]]
    for order in d["orders"]:
        person = writer[order]
        half = np.arange(len(order)) - starts[person] < k[person] // 2
        ok = k >= 2
        left = totals(y[order] * half[:, None], person)[ok] / (k[ok] // 2)[:, None]
        right = (
            totals(y[order] * (~half[:, None]), person)[ok]
            / (k[ok] - k[ok] // 2)[:, None]
        )
        r = correlation(left, right)
        split.append(2 * r / (1 + r))
    raw, avail = [], []
    pairs = d["pairs"]
    for a, b in pairs.transpose(1, 2, 0):
        ok = np.isfinite(a) & np.isfinite(b)
        raw.append(correlation(a[ok], 8 - b[ok]))
        avail.append(int(ok.sum()))
    raw = np.asarray(raw)
    ty = np.maximum(raw, 0) * 2 / (1 + np.maximum(raw, 0))
    rotated = []
    for weights in d["rot"]:
        check()
        rotated.append(components(moments(x @ weights.T, writer), unit)[1])
    bands = np.quantile(rotated, [0.025, 0.5, 0.975], axis=0).T
    endpoint = np.abs(d["bounds"]).max(axis=2)
    grids = {}
    for label, trait in (
        ("items", ty),
        ("retestMean", np.full(5, 0.72)),
        ("retestLow", np.full(5, 0.62)),
        ("retestHigh", np.full(5, 0.77)),
    ):
        ceiling = np.sqrt(rel[:, None] * trait)
        bound = np.minimum(
            1,
            np.divide(endpoint, ceiling, out=np.ones_like(endpoint), where=ceiling > 0),
        )
        needed = []
        for i in icc:
            needed.append(
                [
                    max(1, int(np.ceil(0.09 * (1 - i) / (i * (t - 0.09)))))
                    if i > 0 and t > 0.09
                    else None
                    for t in trait
                ]
            )
        grids[label] = {
            "ceilings": ceiling.tolist(),
            "bounds": bound.tolist(),
            "reportsNeeded": needed,
            "belowPointTwo": int((ceiling < 0.2).sum()),
            "nullStands": int((bound < 0.30).sum()),
        }
    count = grids["items"]["belowPointTwo"]
    return {
        "outputs": d["names"].tolist(),
        "traits": d["traits"].tolist(),
        "writers": len(k),
        "reports": len(y),
        "oneReport": int((k == 1).sum()),
        "splitWriters": int((k >= 2).sum()),
        "traitWriters": avail,
        "icc": icc.tolist(),
        "reliability": rel.tolist(),
        "plain": plain.tolist(),
        "writerInterval": intervals.tolist(),
        "splitHalf": np.mean(split, axis=0).tolist(),
        "itemCorrelation": raw.tolist(),
        "itemReliability": ty.tolist(),
        "rotatedBands": bands.tolist(),
        "grids": grids,
        "thread": "holds" if count >= 73 else "misses",
        "analyst": "holds" if count > 100 else "misses",
    }
