"""TP61(c). Same-author word contrasts on TP47's saved openings in linear coordinates."""

import gzip
import json

import numpy as np
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_worry_repeat import PREP, ROOT, ROSTER, WEEK, distribution, vector_return
from tompathy_engine.eval.readers.person_halves import summary
from tompathy_engine.eval.readers.tp41 import adjusted
from week_word_departures import WORDS
from word_table_lane import write

TP47 = "148073beb4ad1beb82335d57bdafef31effe60870b3f0e0e69a49b4835ddb5bd"


def four_cells(check):
    folder, source = vector_return()
    x = np.empty((source["tp47Openings"], 384), dtype=np.float32)
    masks = np.empty(len(x), dtype=int)
    index = {}
    for name, digest in sorted(source["files"].items()):
        if not name.startswith("tp47-"):
            continue
        check()
        with np.load(bound(folder / name, digest), allow_pickle=False) as f:
            ids = f["ids"].astype(str)
            start = len(index)
            ix = slice(start, start + len(ids))
            x[ix], masks[ix] = f["x"], f["masks"]
            index.update((k, start + j) for j, k in enumerate(ids))
            if len(index) != ix.stop:
                raise ValueError("Duplicate opening in TP47 transfer")
    if len(index) != len(x) or not np.isfinite(x).all():
        raise ValueError("Incomplete TP47 opening vectors")
    cells = {w: [] for w in WORDS}
    n = 0
    with gzip.open(
        bound(ROOT / "TP61-roster-a/author-order.jsonl.gz", ROSTER),
        "rt",
        encoding="utf8",
    ) as f:
        for i, line in enumerate(f):
            if i % 100 == 0:
                check()
            _, sides = json.loads(line)
            if not (sides[0] and sides[1]):
                continue
            half = [
                np.asarray([index[k] for k, _, _ in side if k in index], dtype=int)
                for side in sides[:2]
            ]
            for j, word in enumerate(WORDS):
                parts = [
                    ix[cond]
                    for ix in half
                    for cond in ((masks[ix] & (1 << j)) != 0, masks[ix] == 0)
                ]
                weight = min(map(len, parts))
                if weight >= 2:
                    cells[word].append(
                        (n, weight, [x[v].mean(0, dtype=float) for v in parts])
                    )
            n += 1
    old = read(bound(WEEK / "TP47-a/receipt.json", TP47))
    if n != old["pairedAuthors"] or any(
        len(cells[k]) != old["words"][k]["authors"] for k in WORDS
    ):
        raise ValueError("TP47 paired cohorts differ")
    return cells, n


def components(cells, weights):
    p1, n1, p2, n2 = cells
    scale = np.mean([np.var(x, axis=0) for x in cells], axis=0) ** 0.5
    if np.any(scale <= 0):
        raise ValueError("Constant direction in TP47 cells")
    return adjusted(
        weights,
        (p1 - n1) / scale,
        (p2 - n2) / scale,
        (p1 + n1) / (2 * scale),
        (p2 + n2) / (2 * scale),
    )


def quadratics(cells, weights):
    p1, n1, p2, n2 = cells
    a, b, x, y = p1 - n1, p2 - n2, (p1 + n1) / 2, (p2 + n2) / 2
    p = weights / weights.sum()

    def cov(u, v):
        return (u - p @ u).T @ ((v - p @ v) * p[:, None])

    scale = sum((v - v.mean(0)).T @ (v - v.mean(0)) for v in cells) / (4 * len(weights))
    return np.stack([scale, cov(a, b), cov(x, y), (cov(a, y) + cov(b, x)) / 2])


def projected(covs, w):
    scale, raw, level, cross = np.einsum("hij,ij->hj", covs @ w.T, w.T)
    if np.any(scale <= 0):
        raise ValueError("Invalid directional scale")
    raw, level, cross = raw / scale, level / scale, cross / scale
    var = raw - np.divide(cross**2, level, out=np.zeros_like(raw), where=level > 1e-6)
    return var.mean(), level.mean()


def prepare(out, check):
    cells, total = four_cells(check)
    with np.load(bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD)) as f:
        trained_weights = f["weights"].astype(float)
    weights = np.random.default_rng(23).multinomial(
        total, np.full(total, 1 / total), size=2000
    )
    gram = {}
    results = {}
    estimates = {}
    for word, records in cells.items():
        check()
        owners, support, values = zip(*records, strict=True)
        values = np.moveaxis(np.asarray(values), 1, 0)
        support = np.asarray(support)
        gram[word] = quadratics(values, support)
        scores = values @ trained_weights.T
        var, level = components(scores, support[None, :])
        pair = np.array([var.mean(), level.mean()])
        if not np.allclose(
            projected(gram[word], trained_weights), pair, rtol=1e-9, atol=1e-11
        ):
            raise ValueError("Direct TP47 calculation disagrees with moment projection")
        draws = []
        for batch in np.array_split(weights[:, owners] * support, 40):
            check()
            ok = batch.sum(1) > 0
            v = np.full((len(batch), 2), np.nan)
            if ok.any():
                a, b = components(scores, batch[ok])
                v[ok] = np.column_stack((a.mean(1), b.mean(1)))
            draws.append(v)
        vv = np.vstack([pair, *draws])
        share = np.divide(
            vv[:, 0], vv[:, 1], out=np.full(len(vv), np.nan), where=vv[:, 1] > 0
        )
        estimates[word] = vv[:, 0]
        results[word] = {
            "authors": len(owners),
            "registered": len(owners) >= 200,
            "variance": summary(vv[0, 0], vv[1:, 0]),
            "share": summary(share[0], share[1:]),
        }
    common = ("sad", "angry", "afraid", "happy")
    contrast = estimates["anxious"] - np.mean([estimates[k] for k in common], axis=0)
    diff = {"trained": summary(contrast[0], contrast[1:])}
    files = {}
    for family in ("iso", "rot"):
        vals = []
        for j in range(1000):
            if j % 5 == 0:
                check()
            w = heads(trained_weights, "TP61", family, j)
            vals.append([projected(gram[k], w) for k in WORDS])
            if (j + 1) % 25 == 0:
                path = out / f"{family}-{j - 24:04d}.npy"
                with path.open("xb") as f:
                    np.save(f, np.asarray(vals[-25:]), allow_pickle=False)
                files[path.name] = pin(path)
                write(out / "progress.json", {"family": family, "sets": j + 1})
        values = np.asarray(vals)
        for i, word in enumerate(WORDS):
            value, level = values[:, i, :].T
            valid = level > 0
            results[word][family] = {
                "variance": distribution(value, results[word]["variance"]["value"]),
                "positiveLevelSets": int(valid.sum()),
            }
            target = results[word]["share"]["value"]
            if valid.any() and target is not None:
                results[word][family]["share"] = distribution(
                    value[valid] / level[valid], target
                )
        difference = values[:, WORDS.index("anxious"), 0] - values[
            :, [WORDS.index(k) for k in common], 0
        ].mean(1)
        diff[family] = distribution(difference, contrast[0])
    return {
        "card": "TP61(c)",
        "originalReceiptPin": TP47,
        "vectorReceiptPin": PREP,
        "tagHeadPin": HEAD,
        "pairedAuthors": total,
        "words": results,
        "anxiousMinusCommon": diff,
        "privateShards": files,
        "setsPerFamily": 1000,
    }
