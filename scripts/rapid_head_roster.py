"""Prepare only the opaque joins and registered within-author order for TP61."""

import gzip
import itertools
import json
from collections import Counter

from rapid_head_check import bound, pin, read

INPUT = "84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54"


def prepare(out, check):
    from tompathy_engine.eval.readers.week_curve import nested_indices
    from week_people import WEEK, rows
    from week_worry_language import post_status

    source = WEEK / "Q20-inputs-a"
    cfg = read(bound(source / "receipt.json", INPUT))
    joins = bound(source / "local-joins.jsonl.gz", cfg["joinsPin"])
    original = WEEK / "TP52-a/receipt.json"
    baseline = read(
        bound(original, read(original.parent / "complete.json")["sourceReceiptPin"])
    )
    path = out / "author-order.jsonl.gz"
    counts = Counter()
    seen = set()
    with gzip.open(path, "xt", encoding="utf8") as stream:
        for i, (author, group) in enumerate(
            itertools.groupby(rows(joins), key=lambda row: row["author"])
        ):
            if i % 100 == 0:
                check()
            group = list(group)
            if not group[0]["qualifies"]:
                continue
            if author in seen or any(not row["qualifies"] for row in group):
                raise ValueError("Unstable author membership")
            seen.add(author)
            items = [row for row in group if row["opening"]]
            sides = nested_indices([r["day"] for r in items], [r["id"] for r in items])
            eligible = [
                i for i, row in enumerate(items) if post_status(row) == "eligible"
            ]
            rates = {
                i: items[i]["suffixFirstPerson"] / items[i]["suffixWords"]
                for i in eligible
            }
            rate_sides = nested_indices(
                [items[i]["day"] for i in eligible], [items[i]["id"] for i in eligible]
            )
            rate_half = {
                eligible[j]: h for h, side in enumerate(rate_sides) for j in side
            }
            if sides[0] or sides[1]:
                if sorted(sides[0] + sides[1]) != list(range(len(items))):
                    raise ValueError("Incomplete TP45 partition")
                orders = [*sides, []]
            else:
                orders = [[], [], list(range(len(items)))]
            # Ranks are implicit in each date half's sequence. The only suffix value leaving
            # the workstation is the original normalized first-person count.
            compact = [
                [[items[j]["opening"], rates.get(j), rate_half.get(j)] for j in order]
                for order in orders
            ]
            stream.write(json.dumps([author, compact], separators=(",", ":")) + "\n")
            counts.update(
                authors=1,
                datedPosts=len(group),
                openings=len(items),
                eligible=len(eligible),
                tenPostAuthors=int(len(eligible) >= 10),
            )
    expected = {
        "authors": cfg["counts"]["qualifyingAuthors"],
        "datedPosts": cfg["counts"]["datedPosts"],
        "openings": cfg["counts"]["qualifyingOpenings"],
        "eligible": baseline["postCounts"]["eligible"],
        "tenPostAuthors": baseline["tenPostAuthors"],
    }
    if dict(counts) != expected or path.stat().st_size >= 1_000_000_000:
        raise ValueError("Original TP45/TP52 counts or transfer limit differ")
    return {
        "sourceReceiptPin": INPUT,
        "joinsPin": cfg["joinsPin"],
        "baselinePin": pin(original),
        "counts": dict(counts),
        "archivePin": pin(path),
        "bytes": path.stat().st_size,
        "columns": [
            "opaque author",
            "TP45 ordered date halves and unsplit openings",
            "opening ID",
            "normalized suffix first-person count",
            "TP52 date half",
        ],
    }
