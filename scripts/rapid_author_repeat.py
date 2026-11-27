"""TP73. Compare B's dated half means with the frozen TP61 heads on the same posts."""

from collections import Counter
from itertools import groupby
from pathlib import Path

import numpy as np
from rapid_filler_inputs import Q24
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_worry_repeat import (
    PREP,
    ROOT,
    ROSTER,
    WEEK,
    distribution,
    moments,
    repeats,
    vector_return,
)
from tompathy_engine.eval.readers.person_halves import correlations, resamples, summary
from tompathy_engine.eval.readers.week_curve import nested_indices
from week_people import rows
from week_q24_inputs import Q20
from word_table_lane import core, write

SIZES = (10, 20)


def matched_halves(posts, sides):
    ids = [r["id"] for r in posts]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate post in a dated author roster")
    positions = nested_indices([r["day"] for r in posts], ids)
    ordered = [[posts[i] for i in positions[h]] for h in (0, 1)]
    unused = [] if any(ordered) else posts
    for part, reference in zip([*ordered, unused], sides, strict=True):
        if [r["opening"] for r in part] != [r[0] for r in reference]:
            raise ValueError("Posts contributing to B and the vector means differ")
    return ordered


def select(owners, check):
    handoff = read(ROOT / "Q24-transfer.json")
    folder = Path(handoff["mirror"])
    receipt = read(bound(folder / "receipt.json", Q24))
    if handoff["receiptPin"] != Q24 or not all(
        (
            handoff["nativeExited"],
            handoff["priorFlockReleased"],
            receipt["nativeExited"],
            receipt["priorLocksReleased"],
        )
    ):
        raise ValueError("A verified whole-author Q24 return is required")
    saved = {}
    author_sizes = Counter()
    valid = 0
    for ordinal, post, values, _ in rows(
        bound(folder / "whole-authors.jsonl.gz", receipt["compactPin"])
    ):
        if post in saved:
            raise ValueError("Duplicate Q24 post")
        if values is not None:
            if len(values) != len(core.FEATURES) or any(
                type(v) is not int or not 1 <= v <= 5 for v in values
            ):
                raise ValueError("Invalid saved B feature")
            valid += 1
        saved[post] = (ordinal, values)
        author_sizes[ordinal] += 1
    if (len(saved), valid) != (receipt["rows"], receipt["valid"]) or set(
        author_sizes
    ) != set(range(receipt["wholeAuthors"])):
        raise ValueError("Q24 inventory differs")

    joins = WEEK / "Q20-inputs-a"
    cfg = read(bound(joins / "receipt.json", Q20))
    source = rows(bound(joins / "local-joins.jsonl.gz", cfg["joinsPin"]))
    roster = iter(rows(bound(ROOT / "TP61-roster-a/author-order.jsonl.gz", ROSTER)))
    selected = {k: [] for k in SIZES}
    counts = {k: {"tooShort": 0, "missingBAnswer": 0} for k in SIZES}
    seen = set()
    index = 0
    for author, items in groupby(source, key=lambda r: r["author"]):
        group = list(items)
        if not group[0]["qualifies"]:
            continue
        check()
        expected, sides = next(roster)
        if (
            expected != author
            or index >= len(owners)
            or owners[index] != author
            or not all(r["qualifies"] for r in group)
        ):
            raise ValueError("TP61 and source author order differs")
        row = index
        index += 1
        posts = [r for r in group if r["opening"]]
        known = [saved[r["id"]][0] for r in posts if r["id"] in saved]
        if not known:
            continue
        ordinal = known[0]
        if (
            len(known) != len(posts)
            or len(posts) != author_sizes[ordinal]
            or set(known) != {ordinal}
            or ordinal in seen
        ):
            raise ValueError("Partial or mixed Q24 author")
        seen.add(ordinal)
        halves = matched_halves(posts, sides)
        for k in SIZES:
            if min(map(len, halves)) < k:
                counts[k]["tooShort"] += 1
                continue
            values = [[saved[r["id"]][1] for r in half[:k]] for half in halves]
            if any(v is None for side in values for v in side):
                counts[k]["missingBAnswer"] += 1
                continue
            selected[k].append((row, np.mean(values, axis=1)))
    if (
        index != len(owners)
        or next(roster, None) is not None
        or seen != set(author_sizes)
    ):
        raise ValueError("Incomplete vector or Q24 author roster")
    for k in SIZES:
        if len(selected[k]) + sum(counts[k].values()) != len(seen):
            raise ValueError(
                "Selected and excluded authors do not account for the return"
            )
    return selected, counts, len(seen)


def paired_direction(left, right, author_weights):
    """Column j uses the same author draw j as reader B and one matched null head."""
    if left.shape != right.shape or left.T.shape != author_weights.shape:
        raise ValueError("Misaligned paired bootstrap")
    weight = author_weights.T / author_weights.sum(axis=1)
    a = left - np.sum(weight * left, axis=0)
    b = right - np.sum(weight * right, axis=0)
    denom = np.sqrt(np.sum(weight * a**2, axis=0) * np.sum(weight * b**2, axis=0))
    return np.divide(
        np.sum(weight * a * b, axis=0),
        denom,
        out=np.full_like(denom, np.nan),
        where=denom > 0,
    )


def prepare(out, check):
    folder, vectors = vector_return()

    def load(name, key):
        with np.load(
            bound(folder / name, vectors["files"][name]), allow_pickle=False
        ) as data:
            return data[key]

    index_path = bound(
        folder / "author-index.npz", vectors["files"]["author-index.npz"]
    )
    with np.load(index_path, allow_pickle=False) as ix:
        owners = ix["authors"].astype(str)
        available = {
            k: np.column_stack([ix[f"k{k}-{h}"] for h in (0, 1)]) for k in SIZES
        }
    selected, excluded, whole = select(owners, check)
    with np.load(
        bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD),
        allow_pickle=False,
    ) as source:
        w = source["weights"].astype(float)
    if w.shape != (19, 384):
        raise ValueError("Unrecognized TP61 head geometry")
    designs = {}
    for k, records in selected.items():
        if len(records) < 2:
            raise ValueError("Insufficient complete authors for dated repeat")
        idx, means = zip(*records, strict=True)
        idx = np.array(idx)
        if not (available[k][idx] == k).all():
            raise ValueError("Frozen vector means use a different number of openings")
        left, right = [load(f"mean-k{k}-{h}.npz", "x")[idx] for h in (0, 1)]
        if not np.isfinite(left).all() or not np.isfinite(right).all():
            raise ValueError("Nonfinite frozen vectors")
        b0, b1 = np.moveaxis(np.asarray(means), 1, 0)
        c0, c1 = left @ w.T, right @ w.T
        gram = moments(left, right)
        pop = np.ones((1, len(idx)))
        tag_r = correlations(c0, c1, pop)[0]
        if not np.allclose(repeats(gram, w), tag_r, atol=1e-10, rtol=0):
            raise ValueError("Linear control calculation failed its direct check")
        boot = resamples(len(idx), 2000)
        b_draws = []
        for batch in np.array_split(boot, 40):
            check()
            b_draws.append(correlations(b0, b1, batch))
        forecasts = out / f"paired-authors-k{k}.npz"
        with forecasts.open("xb") as f:
            np.savez_compressed(f, vectorIndex=idx, left=b0, right=b1)
        designs[k] = {
            "left": left,
            "right": right,
            "gram": gram,
            "boot": boot,
            "b": correlations(b0, b1, pop)[0],
            "draws": np.vstack(b_draws),
            "trained": tag_r,
            "forecastPin": pin(forecasts),
        }

    # Two full cycles through the 1,000 rotations, choosing an individual head per draw.
    columns = np.random.default_rng(73).integers(0, len(w), size=(2, 1000))
    panels = {k: {} for k in SIZES}
    paired_null = {k: np.full(2000, np.nan) for k in SIZES}
    files = {}
    for family in ("iso", "rot"):
        for k in SIZES:
            panels[k][family] = np.empty((1000, len(w)))
        for start in range(0, 1000, 25):
            check()
            draws = []
            for i in range(start, start + 25):
                controls = heads(w, "TP61", family, i)
                for k, design in designs.items():
                    panels[k][family][i] = repeats(design["gram"], controls)
                if family == "rot":
                    draws.append(controls[columns[:, i]])
            if family == "rot":
                ix = np.r_[start : start + 25, 1000 + start : 1000 + start + 25]
                directions = np.concatenate(np.moveaxis(np.stack(draws), 1, 0))
                for k, design in designs.items():
                    paired_null[k][ix] = paired_direction(
                        design["left"] @ directions.T,
                        design["right"] @ directions.T,
                        design["boot"][ix],
                    )
            path = out / f"{family}-{start:04d}.npz"
            with path.open("xb") as f:
                np.savez(
                    f, **{f"k{k}": panels[k][family][start : start + 25] for k in SIZES}
                )
            files[path.name] = pin(path)
            write(out / "progress.json", {"family": family, "setsSaved": start + 25})

    result = {}
    for k, design in designs.items():
        pair = paired_null[k]
        features = {}
        for j, feature in enumerate(core.FEATURES):
            b = design["b"][j]
            row = {"B": summary(b, design["draws"][:, j])}
            for family, panel in panels[k].items():
                row[family] = (
                    None
                    if not np.isfinite(b)
                    else {
                        "individual": distribution(panel.ravel(), b),
                        "setMedian": distribution(np.median(panel, axis=1), b),
                    }
                )
            delta = b - np.median(panels[k]["rot"])
            differences = design["draws"][:, j] - pair
            ok = np.isfinite(differences)
            row["BMinusRandomRotatedHead"] = summary(delta, differences)
            row["BMinusRandomRotatedHead"].update(
                upperTail=float(
                    (1 + np.count_nonzero(differences[ok] >= 0)) / (1 + ok.sum())
                )
                if ok.any()
                else None,
                spread=float(np.std(differences[ok], ddof=1)) if ok.sum() > 1 else None,
            )
            features[feature] = row
        result[str(k)] = {
            "authors": len(design["left"]),
            "excluded": excluded[k],
            "features": features,
            "trainedMedianLinearTagRepeat": float(np.median(design["trained"])),
            "privatePairedMeansPin": design["forecastPin"],
        }
    return {
        "card": "TP73-B-repeat",
        "wholeAuthors": whole,
        "k": result,
        "draws": 2000,
        "setsPerFamily": 1000,
        "headsPerSet": len(w),
        "sourceB": Q24,
        "q20Inputs": Q20,
        "vectorReturn": PREP,
        "roster": ROSTER,
        "tagHeads": HEAD,
        "privateControlShards": files,
    }
