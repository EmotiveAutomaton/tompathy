"""TP52. Worry in the opening and first-person language in the disjoint suffix."""

import itertools
import json
from pathlib import Path

import numpy as np
from cb_inputs import pin
from tompathy_engine.eval.readers.person_halves import correlations, resamples, summary
from tompathy_engine.eval.readers.week_curve import nested_indices
from tompathy_engine.eval.readers.word_panels import pinned
from tompathy_engine.packs.trigger import TAGS
from week_people import WEEK, rows

INPUT_PIN = "84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54"


def post_status(row):
    if not row["qualifies"] or row["words"] < 300:
        return "outside"
    if not row["opening"]:
        return "noOpening"
    opening_words = row["words"] - row["suffixWords"]
    if not 1 <= opening_words <= 150 or row["suffixFirstPerson"] < 0:
        raise ValueError("Invalid opening and suffix counts")
    return "eligible"


def author_slope(worry, rate):
    if len(worry) < 10 or np.ptp(worry) == 0 or np.ptp(rate) == 0:
        return None
    # The slope of two within-author standardized variables equals their correlation.
    return float(np.corrcoef(worry, rate)[0, 1])


def stability(left, right, check):
    n = len(left)
    result = {"authors": n, "worryMinusMedianTag": None}
    if n < 2:
        return result
    weights = np.vstack((np.ones(n), resamples(n)))
    draws = []
    for batch in np.array_split(weights, 40):
        check()
        draws.append(correlations(left, right, batch))
    estimates = np.concatenate(draws)
    result["readings"] = {
        name: summary(v[0], v[1:])
        for name, v in zip(("worry", *TAGS), estimates.T, strict=True)
    }
    diff = estimates[:, 0] - np.median(estimates[:, 1:], axis=1)
    result["worryMinusMedianTag"] = summary(diff[0], diff[1:])
    return result


def prepare(out, check):
    inputs = WEEK / "Q20-inputs-a"
    cfg = pinned(inputs / "receipt.json", INPUT_PIN)
    joins = inputs / "local-joins.jsonl.gz"
    transfer = json.loads((WEEK / "Q20-transfer.json").read_bytes())
    mirror = Path(transfer["mirror"])
    receipt = pinned(mirror / "receipt.json", transfer["sourceReceiptPin"])
    if (
        not transfer["nativeExited"]
        or not transfer["priorFlockReleased"]
        or receipt["status"] != "complete"
        or pin(joins) != cfg["joinsPin"]
    ):
        raise ValueError("Verified Q20 readings and original local joins required")
    lookup = {}
    counts = {"eligible": 0, "noOpening": 0}
    for idx, row in enumerate(rows(joins)):
        if idx % 2048 == 0:
            check()
        status = post_status(row)
        if status != "outside":
            counts[status] += 1
        if status == "eligible":
            lookup.setdefault(row["opening"], len(lookup))
    values = np.empty((len(lookup), 1 + len(TAGS)))
    seen = np.zeros(len(lookup), bool)
    for name, h in receipt["outputs"].items():
        if not name.startswith("scores-"):
            continue
        check()
        path = mirror / name
        if transfer["files"][name] != h or pin(path) != h:
            raise ValueError("Q20 score batch changed")
        with np.load(path, allow_pickle=False) as f:
            ids = f["ids"].tolist()
            keep = [i for i, k in enumerate(ids) if k in lookup]
            dest = [lookup[ids[i]] for i in keep]
            if len(set(dest)) != len(dest) or seen[dest].any():
                raise ValueError("Duplicate forecast in Q20")
            scores = np.column_stack((f["worry"].reshape(len(ids)), f["tags"]))
            if scores.shape != (len(ids), 1 + len(TAGS)):
                raise ValueError("Unexpected worry/tag columns")
            values[dest] = scores[keep]
            seen[dest] = True
    if not seen.all() or not np.isfinite(values).all():
        raise ValueError("Incomplete or nonfinite opening forecasts")
    slopes = []
    left = []
    right = []
    cohort = 0
    posts = 0
    slope_posts = 0
    for _, group in itertools.groupby(rows(joins), key=lambda r: r["author"]):
        check()
        items = [r for r in group if post_status(r) == "eligible"]
        if len(items) < 10:
            continue
        cohort += 1
        posts += len(items)
        v = values[[lookup[r["opening"]] for r in items]]
        rate = np.array([r["suffixFirstPerson"] / r["suffixWords"] for r in items])
        slope = author_slope(v[:, 0], rate)
        if slope is not None:
            slopes.append(slope)
            slope_posts += len(items)
        a, b = nested_indices([r["day"] for r in items], [r["id"] for r in items])
        if len(a) and len(b):
            left.append(v[a].mean(0))
            right.append(v[b].mean(0))
    estimate = None
    if len(slopes) >= 2:
        estimate = summary(
            np.mean(slopes), resamples(len(slopes)) @ slopes / len(slopes)
        )
    return {
        "card": "TP52",
        "source": transfer["sourceReceiptPin"],
        "inputSource": INPUT_PIN,
        "postCounts": counts,
        "tenPostAuthors": cohort,
        "tenPostCohortPosts": posts,
        "slopeAuthors": len(slopes),
        "slopePosts": slope_posts,
        "standardizedSlope": estimate,
        "stability": stability(np.asarray(left), np.asarray(right), check),
    }
