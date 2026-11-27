"""Register Q31's two post rosters from the original window forecasts and joins."""

import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rapid_head_check import Q20, bound, pin, read
from rapid_head_roster import INPUT
from rapid_sentences import digest
from week_people import WEEK, rows
from word_table_lane import write


def choose_losses(scores):
    """Take the highest twentieth of eligible posts; cap using an outcome-independent hash."""
    ordered = sorted(scores, key=lambda k: (-scores[k], digest("Q31:loss-tie:23:" + k)))
    n = math.ceil(len(ordered) / 20)
    selected = sorted(ordered[:n], key=lambda k: digest("Q31:loss-cap:23:" + k))[:6000]
    return selected, {
        "eligible": len(ordered),
        "topTwentieth": n,
        "selected": len(selected),
        "lowestInTwentieth": float(scores[ordered[n - 1]]) if n else None,
    }


def choose_openings(counts, posts):
    eligible = [
        author for author, n in counts.items() if n >= 80 and len(posts[author]) >= 20
    ]
    people = sorted(eligible, key=lambda k: digest("Q31:author:23:" + k))[:500]
    return [
        (a, p)
        for a in people
        for p in sorted(posts[a], key=lambda k: digest("Q31:post:23:" + k))[:20]
    ], len(eligible)


def prepare(out, check):
    from rapid_blog_gpu import calendar
    from tompathy_engine.eval.readers.tp30 import CHANNELS
    from tompathy_engine.eval.readers.tp31_teacher import sentences

    prior = WEEK / "Q20-inputs-a"
    cfg = read(bound(prior / "receipt.json", INPUT))
    audit = read(WEEK / "Q20-transfer.json")
    mirror = Path(audit["mirror"])
    if (
        audit["sourceReceiptPin"] != Q20
        or not audit["nativeExited"]
        or not audit["priorFlockReleased"]
    ):
        raise ValueError("The original blog inference did not verify")
    old = read(bound(mirror / "receipt.json", Q20))
    by_author = defaultdict(list)
    counts = Counter()
    opening = {}
    eligible = {}
    sadness = {}
    for i, r in enumerate(rows(bound(prior / "local-joins.jsonl.gz", cfg["joinsPin"]))):
        if i % 8192 == 0:
            check()
        if not r["qualifies"]:
            continue
        author, post = r["author"], r["id"]
        counts[author] += 1
        if not r["opening"]:
            continue
        if post in opening:
            raise ValueError("Duplicate qualified blog post")
        by_author[author].append(post)
        opening[post] = r["opening"]
        if len(r["windows"]) >= 6:
            eligible[post] = r["windows"]
            for k in r["windows"]:
                if k is None:
                    raise ValueError("Missing saved window")
                sadness[k] = None
    col = CHANNELS.index("PANIC/GRIEF")
    for name, h in old["outputs"].items():
        if not name.startswith("scores-"):
            continue
        check()
        with np.load(bound(mirror / name, h), allow_pickle=False) as f:
            values = f["channels"][:, col]
            for k, value in zip(f["ids"].astype(str), values, strict=True):
                if k in sadness:
                    if sadness[k] is not None or not np.isfinite(value):
                        raise ValueError(
                            "Multiple or nonfinite SADNESS forecasts for a window"
                        )
                    sadness[k] = float(value)
    if any(s is None for s in sadness.values()):
        raise ValueError("Saved SADNESS is missing for an eligible window")
    scores = {p: sum(sadness[k] for k in win) / len(win) for p, win in eligible.items()}
    loss, census = choose_losses(scores)
    sample, author_count = choose_openings(counts, by_author)
    if len(sample) != 10000 or len({p for _, p in sample}) != 10000 or not loss:
        raise ValueError("Incomplete Q31 roster")
    # The reader receives only opaque task and content keys. All dates, authors and window joins stay local.
    loss_pairs = [[digest("Q31:a:" + p), opening[p]] for p in loss]
    sample_pairs = [[digest("Q31:b:" + p), opening[p]] for _, p in sample]
    plan = {"loss": loss_pairs, "sample": sample_pairs, "shards": cfg["shards"]}
    write(out / "selection.json", plan)
    write(
        out / "local-joins.json",
        {
            "loss": [
                [k, p, eligible[p]] for (k, _), p in zip(loss_pairs, loss, strict=True)
            ],
            "sample": [
                [k, p, a] for (k, _), (a, p) in zip(sample_pairs, sample, strict=True)
            ],
        },
    )
    _, _, roster = calendar(plan, prior / "spark-inputs", sentences, check)
    return {
        "card": "Q31-inputs",
        "selectionPin": pin(out / "selection.json"),
        "joinPin": pin(out / "local-joins.json"),
        "q20Result": Q20,
        "q20Inputs": INPUT,
        "loss": census,
        "qualifiedAt80": author_count,
        "sampleAuthors": 500,
        "samplePosts": 10000,
        "roster": roster,
    }
