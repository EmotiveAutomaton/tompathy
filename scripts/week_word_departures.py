"""TP47. Eight word-presence contrasts across date halves of the same blog authors."""

import itertools
import json
import re

import numpy as np
from cb_inputs import digest, pin
from tompathy_engine.eval.readers.person_halves import summary
from tompathy_engine.eval.readers.tp41 import adjusted
from tompathy_engine.eval.readers.week_curve import nested_indices
from tompathy_engine.eval.readers.word_panels import pinned
from tompathy_engine.packs.trigger import TAGS
from week_people import WEEK, rows

WORDS = ("sad", "angry", "afraid", "proud", "happy", "lonely", "anxious", "ashamed")
FORMS = dict(
    zip(
        (
            "sadness",
            "anger",
            "scared",
            "pride",
            "happiness",
            "loneliness",
            "anxiety",
            "shame",
        ),
        range(8),
        strict=True,
    )
)
FORMS.update({word: i for i, word in enumerate(WORDS)})
PATTERN = re.compile(r"\b(?:" + "|".join(FORMS) + r")\b")


def matches(text):
    return sum(1 << j for j in {FORMS[m] for m in PATTERN.findall(text.casefold())})


def author_cells(tags, masks, halves):
    cells = {}
    for j, word in enumerate(WORDS):
        values = []
        minimum = len(tags)
        for ix in halves:
            for selected in ((masks[ix] & (1 << j)) != 0, masks[ix] == 0):
                n = int(selected.sum())
                minimum = min(n, minimum)
                if n >= 2:
                    values.append(tags[np.asarray(ix)[selected]].mean(0))
        if minimum >= 2:
            cells[word] = minimum, values
    return cells


def prepare(out, check):
    from pathlib import Path

    prep = WEEK / "Q20-inputs-a"
    cfg = pinned(
        prep / "receipt.json",
        "84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54",
    )
    audit = json.loads((WEEK / "Q20-transfer.json").read_bytes())
    mirror = Path(audit["mirror"])
    terminal = pinned(mirror / "receipt.json", audit["sourceReceiptPin"])
    if not (
        audit["nativeExited"]
        and audit["priorFlockReleased"]
        and terminal["status"] == "complete"
    ):
        raise ValueError("Q20 terminal verification required")
    joins = prep / "local-joins.jsonl.gz"
    if pin(joins) != cfg["joinsPin"]:
        raise ValueError("Opening joins changed")
    index = {}
    for r in rows(joins):
        if r["qualifies"] and r["opening"]:
            index.setdefault(r["opening"], len(index))
    tags = np.full((len(index), 19), np.nan)
    masks = np.full(len(index), -1, dtype=np.int16)
    for name, h in cfg["shards"].items():
        check()
        path = prep / "spark-inputs" / name
        if pin(path) != h:
            raise ValueError("Changed opening text shard")
        for key, text in rows(path):
            if key in index:
                ix = index[key]
                if masks[ix] != -1 or digest(text) != key:
                    raise ValueError("Duplicate or changed opening")
                masks[ix] = matches(text)
    for path in sorted(mirror.glob("scores-*.npz")):
        check()
        if pin(path) != audit["files"][path.name]:
            raise ValueError("Changed Q20 readings")
        with np.load(path) as d:
            for key, v in zip(d["ids"], d["tags"], strict=True):
                if key in index:
                    ix = index[key]
                    if np.isfinite(tags[ix]).any():
                        raise ValueError("Duplicate opening reading")
                    tags[ix] = v
    if not np.isfinite(tags).all() or (masks < 0).any():
        raise ValueError("Incomplete opening readings or text")
    groups = {word: [] for word in WORDS}
    count = 0
    for _, group in itertools.groupby(rows(joins), key=lambda r: r["author"]):
        check()
        valid = [r for r in group if r["qualifies"] and r["opening"]]
        if not valid:
            continue
        ix = [index[r["opening"]] for r in valid]
        halves = nested_indices([r["day"] for r in valid], [r["id"] for r in valid])
        if not all(len(side) for side in halves):
            continue
        for word, (support, means) in author_cells(tags[ix], masks[ix], halves).items():
            groups[word].append((count, support, means))
        count += 1
    # Common whole-author draws preserve overlap among words with different eligible authors.
    rng = np.random.default_rng(23)
    weights = rng.multinomial(count, np.full(count, 1 / count), size=2000)
    weights = np.vstack((np.ones(count, dtype=int), weights))
    tables, estimates = {}, {}
    for word, entries in groups.items():
        cell = tables[word] = {
            "authors": len(entries),
            "registered": len(entries) >= 200,
        }
        if len(entries) < 2:
            continue
        owners, support, means = zip(*entries, strict=True)
        p1, n1, p2, n2 = np.moveaxis(np.asarray(means), 1, 0)
        cell["crowdMeanContrast"] = ((p1 - n1 + p2 - n2) / 2).mean(0).tolist()
        scale = np.sqrt(np.mean([arr.var(0) for arr in (p1, n1, p2, n2)], axis=0))
        if (scale <= 0).any():
            cell["unavailable"] = "A tag has zero within-cell scale"
            continue
        effects = []
        levels = []
        for w in np.array_split(weights, 40):
            check()
            draw = w[:, owners] * support
            keep = draw.sum(1) > 0
            val = np.full(len(w), np.nan)
            level = val.copy()
            if keep.any():
                v, l = adjusted(
                    draw[keep],
                    (p1 - n1) / scale,
                    (p2 - n2) / scale,
                    (p1 + n1) / (2 * scale),
                    (p2 + n2) / (2 * scale),
                )
                val[keep] = v.mean(1)
                level[keep] = l.mean(1)
            effects.extend(val)
            levels.extend(level)
        val, level = np.asarray(effects), np.asarray(levels)
        share = np.divide(val, level, out=np.full_like(val, np.nan), where=level > 0)
        estimates[word] = val
        cell.update(
            variance=summary(val[0], val[1:]), share=summary(share[0], share[1:])
        )
        interval = cell["variance"]["interval"]
        cell["passes"] = (
            bool(interval and interval[0] > 0) if cell["registered"] else None
        )
    comparison = None
    common = ["sad", "angry", "afraid", "happy"]
    if all(w in estimates for w in ["anxious", *common]):
        diff = estimates["anxious"] - np.mean([estimates[w] for w in common], axis=0)
        comparison = summary(diff[0], diff[1:])
    return {
        "card": "TP47",
        "source": audit["sourceReceiptPin"],
        "tags": list(TAGS),
        "pairedAuthors": count,
        "words": tables,
        "anxiousMinusCommon": comparison,
    }
