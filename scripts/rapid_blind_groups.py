"""TP70. Length-adjusted Spearman groups on chat texts and blog author means."""

import hashlib

import numpy as np
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_worry_repeat import ROOT, WEEK, vector_return
from tompathy_engine.packs.trigger import TAG_MAP_V2, TAGS
from word_table_lane import write

GROUPINGS = ("map", "thread", "print", "meaning")


def residualize(vectors, length):
    x = np.asarray(vectors, dtype=float)
    length = np.asarray(length, dtype=float)
    if (
        x.shape != (len(length), 384)
        or not np.isfinite(x).all()
        or not np.all(length > 0)
    ):
        raise ValueError("Incorrect vectors or opening lengths")
    x = x - x.mean(0)
    z = length - length.mean()
    if np.dot(z, z) <= 0:
        raise ValueError("No length variation")
    return x - z[:, None] * ((z @ x) / (z @ z))


def prepare(out, check):
    from pathlib import Path

    from tompathy_engine.eval.readers.affect_data import ed_situations
    from tompathy_engine.eval.readers.tp39 import saved
    from week_people import rows
    from week_pride_inputs import FROZEN, SOURCE

    old = read(bound(FROZEN / "receipt.json", SOURCE))
    frame, intake = ed_situations(Path(".local/readers/data/empathetic-dialogues"))
    if intake["intakePin"] != old["sources"]["ed"]["intakePin"]:
        raise ValueError("Chat source differs")
    with np.load(saved(FROZEN, "ed-profile-forecasts.npz", old)) as f:
        if not np.array_equal(f["ids"].astype(str), frame.id.to_numpy(str)):
            raise ValueError("Chat order differs")
    with np.load(saved(FROZEN, "vectors.npz", old)) as f:
        chat = residualize(f["ed"], [len(s.split()) for s in frame.text])
    _, who = np.unique(frame.writer.to_numpy(str), return_inverse=True)
    folder, source = vector_return()
    with np.load(
        bound(folder / "author-index.npz", source["files"]["author-index.npz"])
    ) as f:
        names, counts = f["authors"].astype(str), f["all"]
    ix = {k: i for i, k in enumerate(names)}
    totals = np.zeros(len(names), dtype=np.int64)
    census = np.zeros_like(totals)
    prep = WEEK / "Q20-inputs-a"
    manifest = read(
        bound(
            prep / "receipt.json",
            "84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54",
        )
    )
    for j, r in enumerate(
        rows(bound(prep / "local-joins.jsonl.gz", manifest["joinsPin"]))
    ):
        if j % 5000 == 0:
            check()
        if r["qualifies"] and r["opening"]:
            k = ix[r["author"]]
            n = r["words"] - r["suffixWords"]
            if not 1 <= n <= 150:
                raise ValueError("Invalid original opening length")
            census[k] += 1
            totals[k] += n
    if not np.array_equal(census, counts):
        raise ValueError(
            "Blog lengths use different openings from the returned vectors"
        )
    ok = counts > 0
    with np.load(bound(folder / "mean-all.npz", source["files"]["mean-all.npz"])) as f:
        blog = residualize(f["x"][ok], totals[ok] / counts[ok])
    if (len(chat), len(np.unique(who)), len(blog)) != (24850, 810, 5426):
        raise ValueError("TP70 census differs")
    files = {}
    for name, x, owner in [("chat", chat, who), ("blog", blog, np.arange(len(blog)))]:
        check()
        dataset = out / (name + ".npz")
        with dataset.open("xb") as fp:
            np.savez_compressed(fp, x=x, owner=owner)
        files[dataset.name] = pin(dataset)
    return {
        "card": "TP70-design",
        "files": files,
        "chatSource": SOURCE,
        "blogSource": pin(folder / "receipt.json"),
        "rows": {"chat": len(chat), "blog": len(blog)},
        "clusters": {"chat": len(np.unique(who)), "blog": len(blog)},
    }


def group_weights():
    sets = [
        [k for k, v in TAG_MAP_V2.items() if v == g]
        for g in sorted(set(TAG_MAP_V2.values()))
    ]
    three = [
        ["status", "approval", "competition", "honor", "belonging", "power"],
        ["family", "contact", "romance"],
        ["curiosity", "indep"],
    ]
    all_sets = [
        sets,
        three,
        [*three, ["order", "savings", "tranquility"]],
        [["order", "savings", "serenity"]],
    ]
    a, b = np.triu_indices(len(TAGS), 1)
    coefficients = []
    for i, groups in enumerate(all_sets):
        labels = {t: g for g, row in enumerate(groups) for t in row}
        if len(labels) != sum(map(len, groups)):
            raise ValueError("Overlapping tag groups")
        lab = np.array([labels.get(t, -1) for t in TAGS])
        same = (lab[a] == lab[b]) & (lab[a] >= 0)
        different = (
            ((lab[a] >= 0) ^ (lab[b] >= 0))
            if i == 3
            else ((lab[a] >= 0) & (lab[b] >= 0) & (lab[a] != lab[b]))
        )
        coefficients.append(same / same.sum() - different / different.sum())
    return np.array(coefficients), (a, b)


def unit_corr(cov):
    sd = np.sqrt(np.diag(cov))
    if not (np.isfinite(sd).all() and np.all(sd > 0)):
        raise ValueError("A rank column has zero variance")
    return cov / np.outer(sd, sd)


def weighted_corr(order, boundaries, weights):
    sw = weights[order]
    totals = np.cumsum(sw, axis=0, dtype=float)
    ranks = totals - (sw - 1) * 0.5
    for j, (starts, ends, positions, groups) in enumerate(boundaries):
        if len(starts):
            mid = (totals[starts, j] - sw[starts, j] + totals[ends, j] + 1) / 2
            ranks[positions, j] = mid[groups]
    centered = np.empty_like(ranks)
    np.put_along_axis(centered, order, ranks - (weights.sum() + 1) / 2, axis=0)
    return unit_corr((centered.T * weights) @ centered)


def score_set(x, owner, w, draws, check):
    scores = x @ w.T
    order = np.argsort(scores, axis=0, kind="stable")
    eq = np.diff(np.take_along_axis(scores, order, axis=0), axis=0) == 0
    boundaries = []
    for j in range(eq.shape[1]):
        edge = np.diff(np.r_[False, eq[:, j], False].astype(int))
        starts, ends = np.flatnonzero(edge == 1), np.flatnonzero(edge == -1)
        positions = np.flatnonzero(np.r_[eq[:, j], False] | np.r_[False, eq[:, j]])
        groups = np.repeat(np.arange(len(starts)), ends - starts + 1)
        boundaries.append((starts, ends, positions, groups))
    coef, pairs = group_weights()
    output = []
    original = None
    for i, weights in enumerate(draws):
        if i % 10 == 0:
            check()
        corr = weighted_corr(order, boundaries, weights[owner])
        vals, vec = np.linalg.eigh(corr)
        residual = unit_corr(corr - vals[-1] * np.outer(vec[:, -1], vec[:, -1]))
        if i == 0:
            original = corr
        output.append(
            [
                np.r_[vals[::-1], coef @ corr[pairs]],
                np.r_[np.linalg.eigvalsh(residual)[::-1], coef @ residual[pairs]],
            ]
        )
    return np.array(output), original


def block(out, check, index):
    from rapid_cpu_dispatch import confirmed

    design = ROOT / "TP70-design-a"
    source = confirmed(design)
    record = read(design / "receipt.json")["result"]
    if record["card"] != "TP70-design":
        raise ValueError("A verified TP70 design is required")
    with np.load(bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD)) as f:
        w = f["weights"].astype(float)
    sets = ([("trained", 0)] if index == 0 else []) + [
        (family, j)
        for j in range(index * 25, (index + 1) * 25)
        for family in ("iso", "rot")
    ]
    files = {}
    datasets = {}
    for name in ("chat", "blog"):
        with np.load(
            bound(design / (name + ".npz"), record["files"][name + ".npz"])
        ) as f:
            x, owner = f["x"], f["owner"]
        n = record["clusters"][name]
        seed = int.from_bytes(
            hashlib.sha256(("TP70:resamples:" + name).encode()).digest()[:8], "big"
        )
        draws = np.vstack(
            [
                np.ones(n, dtype=int),
                np.random.default_rng(seed).multinomial(n, np.full(n, 1 / n), size=100),
            ]
        )
        datasets[name] = x, owner, draws
    for family, j in sets:
        check()
        h = w if family == "trained" else heads(w, "TP70", family, j)
        tables = {}
        for name, (x, owner, draws) in datasets.items():
            summary, matrix = score_set(x, owner, h, draws, check)
            tables[name] = summary
            if family == "trained":
                tables[name + "Corr"] = matrix
        dest = out / f"{family}-{j:04d}.npz"
        with dest.open("xb") as stream:
            np.savez_compressed(stream, **tables)
        files[dest.name] = pin(dest)
        write(
            out / "progress.json",
            {"setsSaved": len(files), "total": len(sets), "last": dest.name},
        )
    return {
        "card": "TP70",
        "block": index,
        "designReceiptPin": source,
        "tagHeadPin": HEAD,
        "files": files,
        "rows": record["rows"],
        "clusters": record["clusters"],
        "resamples": 100,
    }
