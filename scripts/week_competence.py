"""TP51. Separate within-writer association from cross-half stable covariance."""

import json
from pathlib import Path

import numpy as np
from cb_features import verified_q19
from cb_inputs import BASE, digest, pin
from cb_tables import FROZEN, scored_batches
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.person_halves import resamples, summary
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28, q6_features, saved
from tompathy_engine.eval.readers.word_panels import pinned
from tompathy_engine.packs.trigger import FEATURES, TAGS

PARTS = ("goal_support", "self_responsblt", "standards")
NAMES = (*TAGS, *PARTS, "competence")


def paired_measures(values, groups, halves, check):
    """Sums of centered products within writers and symmetrized covariance across their halves."""
    # Only accumulate the pairs needed for the table, its marginal variances, and partialling.
    pairs = sorted(
        {
            tuple(sorted((i, j)))
            for i in range(len(NAMES))
            for j in [
                i,
                NAMES.index("curiosity"),
                NAMES.index("status"),
                *range(len(TAGS), len(NAMES)),
            ]
        }
    )
    first, second = np.asarray(pairs).T
    left = []
    right = []
    within = []
    paired = []
    for idx, h in zip(groups, halves, strict=True):
        v = values[idx]
        centered = v - v.mean(0)
        within.append((centered[:, first] * centered[:, second]).sum(0))
        if (h == 0).any() and (h == 1).any():
            left.append(v[h == 0].mean(0))
            right.append(v[h == 1].mean(0))
            paired.append(True)
        else:
            left.append(np.zeros(v.shape[1]))
            right.append(np.zeros(v.shape[1]))
            paired.append(False)
    a, b = np.asarray(left), np.asarray(right)
    products = (a[:, first] * b[:, second] + b[:, first] * a[:, second]) / 2
    covs = [[], []]
    weights = np.vstack((np.ones(len(groups)), resamples(len(groups))))
    for w in np.array_split(weights, 32):
        check()
        covs[0].append(w @ within)
        w = w * np.asarray(paired)
        with np.errstate(invalid="ignore", divide="ignore"):
            p = w / w.sum(1, keepdims=True)
        ma, mb = p @ a, p @ b
        covs[1].append(
            p @ products
            - (ma[:, first] * mb[:, second] + mb[:, first] * ma[:, second]) / 2
        )
    output = {}
    contrasts = {}
    for name, collection in zip(("within", "between"), covs, strict=True):
        samples = np.vstack(collection)

        def cov(x, y, samples=samples):
            return samples[
                :, pairs.index(tuple(sorted((NAMES.index(x), NAMES.index(y)))))
            ]

        def corr(x, y, hold=False, cov=cov):
            xx, xy, yy = cov(x, x), cov(x, y), cov(y, y)
            with np.errstate(divide="ignore", invalid="ignore"):
                if hold:
                    zz = cov("status", "status")
                    zz = np.where(zz > 0, zz, np.nan)
                    xz, yz = cov(x, "status"), cov(y, "status")
                    xx, xy, yy = xx - xz * xz / zz, xy - xz * yz / zz, yy - yz * yz / zz
                return xy / np.sqrt(
                    np.where(xx > 0, xx, np.nan) * np.where(yy > 0, yy, np.nan)
                )

        def ci(v):
            return summary(v[0], v[1:])

        results = {
            tag: {
                target: ci(corr(tag, target))
                for target in ("competence", *PARTS, "curiosity")
            }
            for tag in TAGS
        }
        results["independenceHoldingStatus"] = ci(corr("indep", "competence", True))
        output[name] = results
        if name == "between":
            body = {"food", "rest", "health", "tranquility"}
            averages = [
                np.mean(
                    [corr(t, "competence") for t in TAGS if (t in body) == in_body],
                    axis=0,
                )
                for in_body in (True, False)
            ]
            contrasts["bodyLessOther"] = ci(averages[0] - averages[1])
            for other in ("status", "approval", "savings"):
                contrasts["powerLess" + other.title()] = ci(
                    corr("power", "competence") - corr(other, "competence")
                )

    def verdict(row, criterion):
        value = row["value"]
        return None if value is None else bool(criterion(value))

    between = output["between"]
    partial = between["independenceHoldingStatus"]["interval"]
    verdicts = {
        "curiosityWithinNegative": verdict(
            output["within"]["curiosity"]["competence"], lambda x: x < 0
        ),
        "curiosityBetweenAtLeastPointThree": verdict(
            between["curiosity"]["competence"], lambda x: x >= 0.3
        ),
        "competitionUnderPointThree": verdict(
            between["competition"]["competence"], lambda x: x < 0.3
        ),
        "independencePositive": verdict(
            between["indep"]["competence"], lambda x: x > 0
        ),
        "independenceHoldingStatusIncludesZero": None
        if partial is None
        else partial[0] <= 0 <= partial[1],
        "bodyAboveOthers": verdict(contrasts["bodyLessOther"], lambda x: x > 0),
    }
    for tag in ("savings", "status", "approval"):
        verdicts[tag + "PositiveUnderPointThree"] = verdict(
            between[tag]["competence"], lambda x: 0 < x < 0.3
        )
        key = "powerLess" + tag.title()
        verdicts[key] = verdict(contrasts[key], lambda x: x < 0)
    return {
        "withinAuthors": len(groups),
        "betweenAuthors": sum(paired),
        "readings": output,
        "contrasts": contrasts,
        "perLineVerdicts": verdicts,
    }


def source_table(tags, features, owners, ids, dates, check):
    n = len(owners)
    if (
        tags.shape != (n, len(TAGS))
        or features.shape != (n, len(FEATURES))
        or len(ids) != n
        or (dates is not None and len(dates) != n)
    ):
        raise ValueError("Misaligned tag, feature or author rows")
    owner_groups = {}
    parts = features[:, [FEATURES.index(p) for p in PARTS]]
    for i, owner in enumerate(owners):
        if np.isfinite(parts[i]).all() and np.isfinite(tags[i]).all():
            owner_groups.setdefault(owner, []).append(i)
    groups = [np.array(idx) for idx in owner_groups.values() if len(idx) >= 5]
    support = {
        "sourceAuthors": len(set(owners)),
        "sourceRows": len(owners),
        "eligibleAuthors": len(groups),
        "eligibleRows": sum(map(len, groups)),
    }
    if len(groups) < 2:
        return {"support": support, "status": "insufficient writers"}
    fit = parts[np.concatenate(groups)]
    scale = fit.std(0)
    if not np.all(scale > 0):
        return {"support": support, "status": "constant reader component"}
    z = (parts - fit.mean(0)) / scale
    values = np.column_stack((tags, z, z.mean(1)))
    halves = []
    for idx in groups:
        if dates is None:
            order = sorted(
                range(len(idx)), key=lambda j: digest("TP39:23:" + str(ids[idx[j]]))
            )
            h = np.ones(len(idx), int)
            h[order[: len(idx) // 2]] = 0
        else:
            days = np.unique(dates[idx])
            h = (~np.isin(dates[idx], days[: len(days) // 2])).astype(int)
        halves.append(h)
    return {"support": support, **paired_measures(values, groups, halves, check)}


def prepare(out, check):
    local = Path(".local")
    ed, identity = ed_situations(local / "readers/data/empathetic-dialogues")
    old = local / "nine-channel/tp28-a"
    receipt = pinned(old / "receipt.json", TP28)
    if receipt["sources"]["ed"]["identity"] != identity or receipt["protocol"][
        "tags"
    ] != list(TAGS):
        raise ValueError("Chat source differs")
    path = saved(old, "ed/scores.npz", receipt)
    verify_order(path, ed.id)
    with np.load(path) as f:
        tags = f["scores"].astype(float)
    features, q6 = q6_features(ed, local / "word-table", check)
    # The handoff specifies the earlier TP39 panel. Require five usable texts within that panel.
    selected = ed.groupby("writer").id.transform("count").to_numpy() >= 8
    feat, owners, _, audit = verified_q19()
    complete = json.loads((FROZEN / "complete.json").read_bytes())
    public = json.loads(Path("engine/validation/readers-tp43-all-2026-11.json").read_bytes())
    source = pinned(BASE / "TP43-all/receipt.json", public["sourceReceiptPin"])
    if (
        source["status"] != "complete"
        or source["registeredInputs"] != pin(BASE / "inputs.json")
        or source["frozenResult"] != pin(FROZEN / "complete.json")
    ):
        raise ValueError("Frozen blog source differs")
    posts = json.loads((BASE / "blogs.json").read_bytes())
    meta = json.loads((BASE / "blog-meta.json").read_bytes())
    n = len(owners)
    if (
        len(posts) != complete["counts"]["blogs"]
        or [r["id"] for r in posts[:n]] != [r[0] for r in meta[:n]]
        or owners.tolist() != [r[1] for r in meta[:n]]
    ):
        raise ValueError("Reader B and frozen blog rows differ")
    blog_tags = np.empty((n, len(TAGS)))
    start = 0
    if n:
        for _, v in scored_batches("blogs", posts):
            check()
            take = min(len(v), n - start)
            blog_tags[start : start + take] = v[:take, : len(TAGS)]
            start += take
            if start == n:
                break
    if start != n:
        raise ValueError("Missing frozen tags for the Q19 author prefix")
    return {
        "card": "TP51",
        "q6": q6,
        "q19": audit["source"],
        "tags": TP28,
        "frozen": source["frozenResult"],
        "chat": source_table(
            tags[selected],
            features[selected],
            ed.writer.to_numpy()[selected],
            ed.id.to_numpy()[selected],
            None,
            check,
        ),
        "blog": source_table(
            blog_tags,
            feat,
            owners,
            [r[0] for r in meta[:n]],
            np.array([r[2] for r in meta[:n]]),
            check,
        ),
    }
