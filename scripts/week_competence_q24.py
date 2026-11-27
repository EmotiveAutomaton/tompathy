"""TP51 blog extension from a terminal Q24 prefix and the saved Q20 opening tags."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from cb_inputs import pin
from week_competence import FEATURES, TAGS, source_table
from week_people import WEEK, rows
from week_q24_inputs import Q20
from week_q24_return import verify_local

Q20_RESULT = "d7520ece843c5805b26be7b746c452eedc09b71940b263ed241251bed33bcaef"


def align(compact, joins, count, check):
    """Join by post ID. Several distinct posts may share a Q20 opening."""
    indices = {}
    features = np.full((count, len(FEATURES)), np.nan)
    for ordinal, (author_index, post, values, _) in enumerate(compact):
        if ordinal >= count or post in indices:
            raise ValueError("Unexpected or repeated Q24 post")
        indices[post] = (ordinal, author_index)
        if values is not None:
            features[ordinal] = values
    if len(indices) != count:
        raise ValueError("Q24 count differs")
    owners, days = [None] * count, [None] * count
    openings = defaultdict(list)
    author_keys = {}
    for index, row in enumerate(joins):
        if index % 2048 == 0:
            check()
        match = indices.get(row["id"])
        if match is None:
            continue
        pos, group = match
        author = row["author"]
        if (owners[pos] is not None or not row["qualifies"] or not row["opening"]
                or author_keys.setdefault(group, author) != author):
            raise ValueError("Q24 post or author binding differs")
        owners[pos], days[pos] = author, row["day"]
        openings[row["opening"]].append(pos)
    if None in owners or None in days or len(set(author_keys.values())) != len(author_keys):
        raise ValueError("Missing or ambiguous author/date join")
    return features, np.asarray(owners), np.asarray(days), openings


def prepare(directory, receipt_pin, check):
    if pin(directory / "receipt.json") != receipt_pin:
        raise ValueError("Q24 receipt differs from the verified Spark copy")
    q24 = verify_local(directory, WEEK)
    check()
    audit = json.loads((WEEK / "Q20-transfer.json").read_bytes())
    root = Path(audit["mirror"])
    src = WEEK / "Q20-inputs-a"
    joins = src / "local-joins.jsonl.gz"
    if (not audit["nativeExited"] or not audit["priorFlockReleased"]
            or audit["sourceReceiptPin"] != Q20_RESULT or pin(root / "receipt.json") != Q20_RESULT
            or pin(src / "receipt.json") != Q20
            or pin(joins) != json.loads((src / "receipt.json").read_bytes())["joinsPin"]):
        raise ValueError("Verified Q20 scores and original joins required")
    features, owners, days, openings = align(
        rows(directory / "whole-authors.jsonl.gz"), rows(joins), q24["rows"], check
    )
    tags = np.empty((len(owners), len(TAGS)))
    seen = set()
    for name, expected in sorted(audit["files"].items()):
        if not name.startswith("scores-") or not name.endswith(".npz"):
            continue
        check()
        if pin(root / name) != expected:
            raise ValueError("Changed Q20 score file")
        with np.load(root / name, allow_pickle=False) as saved:
            take = [(i, key) for i, key in enumerate(saved["ids"].tolist()) if key in openings]
            if not take:
                continue
            scores = saved["tags"]
            for i, key in take:
                if key in seen or not np.isfinite(scores[i]).all() or scores[i].shape != (len(TAGS),):
                    raise ValueError("Invalid or duplicate opening score")
                tags[openings[key]] = scores[i]
                seen.add(key)
    if len(seen) != len(openings):
        raise ValueError("Missing Q20 scores")
    return {
        "card": "TP51-Q24", "q24": q24, "q20": Q20_RESULT, "q20Inputs": Q20,
        "blog": source_table(tags, features, owners, range(len(owners)), days, check),
    }
