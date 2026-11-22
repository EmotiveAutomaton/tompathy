"""TP46. Paired loss from omitting tags and replication of each author's leading need."""

import json
from pathlib import Path

import numpy as np
from cb_inputs import digest, pin
from tompathy_engine.eval.readers.person_halves import (
    correlations,
    ranks,
    resamples,
    summary,
)
from tompathy_engine.packs.trigger import TAGS

GROUPS = {
    "Competence": ["curiosity"],
    "Meaning": ["order", "savings", "serenity"],
    "familyAndContact": ["family", "contact"],
    "belongingTag": ["belonging"],
    "Respect": ["status", "approval", "power", "competition", "honor"],
    "Compassion": ["idealism"],
    "Body": ["food", "rest", "health", "tranquility"],
    "unplaced": ["romance", "indep"],
}
MERGED = ["family", "contact", "idealism"]


def standard(x):
    sd = x.std(axis=0)
    return np.divide(x - x.mean(axis=0), sd, out=np.zeros_like(x), where=sd > 0)


def matching_scores(x, y, reliability):
    squared = reliability**2
    penalty = squared / (2 * (1 - squared))
    return (
        (x * (reliability / (1 - squared))) @ y.T
        - ((x * x) @ penalty)[:, None]
        - ((y * y) @ penalty)[None, :]
    )


def omission_hits(left, right, fold, groups, check):
    """Fit each column's TP43 reliability on other authors and reuse identical candidate pools."""
    left, right = standard(left), standard(right)
    hits = {name: np.empty(len(left), float) for name in ["baseline", "all", *groups]}
    for f in (0, 1):
        held = fold == f
        if min(held.sum(), (~held).sum()) < 2:
            raise ValueError("Two populated author folds required")
        a, b = left[held], right[held]
        r = correlations(left[~held], right[~held], np.ones((1, (~held).sum())))[0]
        r = np.clip(np.nan_to_num(r), 0, 0.95)

        check()
        baseline = matching_scores(a[:, :358], b[:, :358], r[:358])
        hits["baseline"][held] = ranks(baseline) <= 10
        all_columns = np.arange(358, 377)
        hits["all"][held] = (
            ranks(baseline + matching_scores(a[:, 358:], b[:, 358:], r[358:])) <= 10
        )
        for name, omitted in groups.items():
            check()
            remaining = np.delete(all_columns, omitted)
            hits[name][held] = (
                ranks(
                    baseline
                    + matching_scores(a[:, remaining], b[:, remaining], r[remaining])
                )
                <= 10
            )
    return hits


def highest_need(left, right, groups, weights, check):
    halves = []
    for v in (left, right):
        z = standard(v)
        levels = np.column_stack(
            [
                z[:, [TAGS.index(tag) for tag in tags]].mean(1)
                for tags in groups.values()
            ]
        )
        # Equal maxima share credit across their tied labels, including under random dealing.
        leaders = levels == levels.max(1)[:, None]
        halves.append(leaders / leaders.sum(1)[:, None])
    a, b = halves
    paired = (a * b).sum(1)
    rng = np.random.default_rng(23)
    shuffled = np.zeros(len(a))
    for i in range(1000):
        if i % 50 == 0:
            check()
        shuffled += (a * b[rng.permutation(len(b))]).sum(1) / 1000
    diff = paired - shuffled
    return {
        "groups": list(groups),
        "paired": float(paired.mean()),
        "dealt": float(shuffled.mean()),
        "difference": summary(diff.mean(), weights @ diff / len(diff)),
        "deals": 1000,
    }


def prepare(out, check):
    root = Path(".local/week-20261122/TP45-profiles-a")
    receipt = json.loads((root / "receipt.json").read_bytes())
    source = pin(root / "receipt.json")
    file = root / "every-date-full.npz"
    if (
        source != json.loads((root / "complete.json").read_bytes())["sourceReceiptPin"]
        or pin(file) != receipt["profileFiles"][file.name]
        or receipt["tags"] != list(TAGS)
    ):
        raise ValueError("Verified all-opening profiles required")
    with np.load(file, allow_pickle=False) as data:
        a, b, fold = data["left"], data["right"], data["fold"]
    if (
        a.shape != b.shape
        or a.shape != (len(fold), 434)
        or not (np.isfinite(a).all() and np.isfinite(b).all())
    ):
        raise ValueError("Incomplete profiles")
    groups = {
        **GROUPS,
        "familyContactCompassion": MERGED,
        **{"tag/" + t: [t] for t in TAGS},
    }
    indices = {k: [TAGS.index(t) for t in group] for k, group in groups.items()}
    # One seeded permutation without replacement preserves group sizes, overlaps and singletons.
    order = sorted(range(len(TAGS)), key=lambda i: digest("TP46:placebo:23:" + str(i)))
    controls = {k: [order[i] for i in g] for k, g in indices.items()}

    def hits(start, omit):
        cols = np.r_[0:358, start : start + 19]
        return omission_hits(a[:, cols], b[:, cols], fold, omit, check)

    tag, placebo = hits(396, indices), hits(415, controls)
    w = resamples(len(a))

    def stat(values):
        return summary(values.mean(), w @ values / len(a))

    full = stat(tag["all"] - tag["baseline"])
    table = {}
    for k in groups:
        loss = tag["all"] - tag[k]
        size_control = placebo["all"] - placebo[k]
        table[k] = {
            "withoutStep": stat(tag[k] - tag["baseline"]),
            "loss": stat(loss),
            "placeboLoss": stat(size_control),
            "adjustedLoss": stat(loss - size_control),
        }
    separate = {k: v for k, v in GROUPS.items() if k != "unplaced"}
    merged = {
        k: v for k, v in separate.items() if k not in ("familyAndContact", "Compassion")
    }
    merged["familyContactCompassion"] = MERGED
    highest = {
        name: highest_need(a[:, 396:415], b[:, 396:415], group, w, check)
        for name, group in [("separate", separate), ("merged", merged)]
    }
    estimates = {k: table[k]["adjustedLoss"]["value"] for k in separate}
    rest = max(v for k, v in estimates.items() if k not in ("Body", "Respect"))
    rank_pass = min(estimates["Body"], estimates["Respect"]) > rest and all(
        table[k]["adjustedLoss"]["interval"][0] > 0 for k in ("Body", "Respect")
    )
    lo, hi = table["belongingTag"]["adjustedLoss"]["interval"]
    return {
        "card": "TP46",
        "source": source,
        "authors": len(a),
        "fullStep": full,
        "placeboFullStep": stat(placebo["all"] - placebo["baseline"]),
        "omissions": table,
        "placeboColumns": controls,
        "highestNeed": highest,
        "respectAndBodyPass": rank_pass,
        "belongingPass": bool(lo <= 0 <= hi < full["value"] / 4),
        "highestNeedPass": {
            k: v["difference"]["interval"][0] > 0 for k, v in highest.items()
        },
    }
