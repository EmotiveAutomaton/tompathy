"""Independent TP81 calculation by ordered blocks of observations and direct writer resampling."""

import math

import numpy as np


def analyze(table, check):
    group = table["person"]
    order = np.argsort(group, kind="stable")
    _, n = np.unique(group[order], return_counts=True)
    g = len(n)
    cut = np.r_[0, n.cumsum()[:-1]]

    def center(a):
        result = a.copy()
        for f in np.unique(table["feeling"]):
            use = table["feeling"] == f
            result[use] -= a[use].mean(0)
        return result

    def reduce(y):
        z = y[order]
        avg = np.add.reduceat(z, cut, axis=0) / n[:, None]
        sq = np.add.reduceat((z - np.repeat(avg, n, axis=0)) ** 2, cut, axis=0)
        return avg, sq

    def reliability(count, avg, wss):
        N = count.sum()
        m = len(count)
        grand = np.average(avg, axis=0, weights=count)
        b = ((avg - grand) ** 2 * count[:, None]).sum(0) / (m - 1)
        v = wss.sum(0) / (N - m)
        scale = (N - np.dot(count, count) / N) / (m - 1)
        signal = np.maximum((b - v) / scale, 0)
        ratio = signal / (v + signal)
        meanrel = signal / (signal + v * np.mean(1 / count))
        diagnostic = np.maximum(0, (b - v) / b)
        return ratio, meanrel, diagnostic

    y = center(np.column_stack((table["x"] @ table["w"].T, table["worry"])))
    m, s = reduce(y)
    ic, rr, plain = reliability(n, m, s)
    resampled = []
    for i, who in enumerate(table["draws"]):
        if i % 50 == 0:
            check()
        resampled.append(reliability(n[who], m[who], s[who])[1])
    ci = np.percentile(resampled, [2.5, 97.5], axis=0).T
    half = []
    mask = n >= 2
    for idx in table["orders"]:
        rank = np.arange(len(idx)) - np.repeat(cut, n)
        take = rank < np.repeat(n // 2, n)
        selected = y[idx]
        a = (
            np.add.reduceat(selected * take[:, None], cut, axis=0)[mask]
            / (n[mask] // 2)[:, None]
        )
        b = (
            np.add.reduceat(selected * (~take)[:, None], cut, axis=0)[mask]
            / ((n[mask] + 1) // 2)[:, None]
        )
        coeff = np.array(
            [np.corrcoef(i, j)[0, 1] for i, j in zip(a.T, b.T, strict=True)]
        )
        half.append(2 * coeff / (1 + coeff))
    raw, adjusted, sizes = [], [], []
    for j in range(5):
        values = table["pairs"][:, j, :]
        values = values[np.isfinite(values).all(1)]
        coeff = float(np.corrcoef(values[:, 0], 8 - values[:, 1])[0, 1])
        raw.append(coeff)
        adjusted.append(2 * coeff / (1 + coeff) if coeff > 0 else 0)
        sizes.append(len(values))
    null = []
    # Center raw vectors once; a linear projection commutes with subtracting group means.
    vectors = center(table["x"])
    for h in table["rot"]:
        check()
        means, ss = reduce(vectors @ h.T)
        null.append(reliability(n, means, ss)[1])
    grids = {}
    for key, t in {
        "items": adjusted,
        "retestMean": [0.72] * 5,
        "retestLow": [0.62] * 5,
        "retestHigh": [0.77] * 5,
    }.items():
        ceilings = []
        bounds = []
        targets = []
        for j, r in enumerate(rr):
            c = []
            b = []
            target = []
            for k, tval in enumerate(t):
                mx = math.sqrt(tval * r)
                c.append(mx)
                interval = table["bounds"][j, k]
                b.append(
                    min(1, max(abs(interval[0]), abs(interval[1])) / mx) if mx else 1.0
                )
                if tval > 0.09 and ic[j] > 0:
                    target.append(
                        max(1, math.ceil((1 / ic[j] - 1) / ((tval / 0.09) - 1)))
                    )
                else:
                    target.append(None)
            ceilings.append(c)
            bounds.append(b)
            targets.append(target)
        grids[key] = {
            "ceilings": ceilings,
            "bounds": bounds,
            "reportsNeeded": targets,
            "belowPointTwo": int(sum(v < 0.2 for line in ceilings for v in line)),
            "nullStands": int(sum(v < 0.3 for line in bounds for v in line)),
        }
    c = grids["items"]["belowPointTwo"]
    return {
        "outputs": table["names"].tolist(),
        "traits": table["traits"].tolist(),
        "writers": g,
        "reports": len(group),
        "oneReport": int(sum(n == 1)),
        "splitWriters": int(sum(mask)),
        "traitWriters": sizes,
        "icc": ic.tolist(),
        "reliability": rr.tolist(),
        "plain": plain.tolist(),
        "writerInterval": ci.tolist(),
        "splitHalf": np.average(half, axis=0).tolist(),
        "itemCorrelation": raw,
        "itemReliability": adjusted,
        "rotatedBands": np.percentile(null, [2.5, 50, 97.5], axis=0).T.tolist(),
        "grids": grids,
        "thread": "holds" if c >= 73 else "misses",
        "analyst": "holds" if c > 100 else "misses",
    }
