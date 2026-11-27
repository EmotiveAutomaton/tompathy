"""Select G15 openings from the verified whole-author Q24 return and reuse exact G11 calls."""

import gzip
import json
from collections import defaultdict
from itertools import groupby
from pathlib import Path

from rapid_cpu_dispatch import ROOT
from rapid_head_check import bound, pin, read
from rapid_marks import digest
from tompathy_engine.eval.readers.week_curve import nested_indices
from week_people import WEEK, rows
from week_q24_inputs import Q20
from word_table_lane import core, write

OLD = Path(".local/person-teacher")
Q24 = "9403c28730500a1e9a1f5597b4d1c19423774464ffb4d10c1c24de6b2148fcd2"
G11 = "847c6d8ccb85d8e3a383a02f42f8b0decba252f8ae0058dcbdba9bb3ada52d48"
G11B = "552821297f48b1dc818f97e936d4940fd3904e7cd94985a68d1efac816dd4077"
INPUT = "5aee698be9386f138e63859befe713ed18c784c719eac128b3b1adc1b15a1f16"
PROTOCOLS = (
    "4c957e9a8383b4c74991c5f6e43c3afe76ab91f8f5ee163c2dd128d2270bd2c3",
    "31086e3481da36fe3b4953f93d77e0a38be7d12fabf504c3ea4caed8a13549ec",
)
FIELDS = (
    "role",
    "modelPin",
    "options",
    "think",
    "prompt",
    "promptPin",
    "schema",
    "schemaPin",
)


def select_by_date(group):
    ids = [r["id"] for r in group]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicated post within a whole author")
    left, right = nested_indices([r["day"] for r in group], ids)
    if min(len(left), len(right)) < 10:
        return []
    return [
        (half, group[i])
        for half, positions in enumerate((left, right))
        for i in positions[:10]
    ]


def historic(row, source, protocol, index):
    binding = {
        k: v for k, v in protocol.items() if k not in ("prompt", "schema", "secondKey")
    }
    if row["index"] != index or row["id"] != source["id"] or row["binding"] != binding:
        raise ValueError("Historical W row binding differs")
    response = row.get("response")
    try:
        parsed = (
            core.valid_features(json.loads(response["response"]))
            if response is not None
            else None
        )
    except (ValueError, KeyError, TypeError):
        parsed = None
    if parsed != row["values"]:
        raise ValueError("Historical W values disagree with its saved response")
    return parsed


def old_study():
    a, b = (OLD / "jobs" / k for k in ("G11", "G11-b"))
    read(bound(a / "receipt.json", G11))
    receipt = read(bound(b / "receipt.json", G11B))
    proof = read(b / "exit-verification.json")
    if (
        not proof["nativeExited"]
        or proof["sourceReceiptPin"] != G11B
        or proof["releasePin"] != pin(b / "released.json")
        or read(b / "complete.json")["receiptPin"] != G11B
        or receipt["sourceReceiptPin"] != G11
        or receipt["status"] != "cutoff"
    ):
        raise ValueError("G11 cutoff and original row inventory are required")
    protocols = [
        read(bound(p / "W/protocol.json", h))
        for p, h in zip((a, b), PROTOCOLS, strict=True)
    ]
    if any(protocols[0][k] != protocols[1][k] for k in FIELDS):
        raise ValueError("Prefix and suffix W settings differ")
    source = read(bound(OLD / "cb/inputs.json", INPUT))["blogs"]
    calls = read(bound(OLD / "cb/blogs.json", source["posts"]))
    prefix = receipt["prefixRows"]
    completed = receipt["totalDurableRows"]
    if (
        not 0 < prefix < completed <= len(calls)
        or receipt["suffixRows"] != completed - prefix
    ):
        raise ValueError("G11 prefix and suffix bounds differ")
    calls = calls[:completed]
    keys = {v["id"]: i for i, v in enumerate(calls)}
    by_text = {}
    for i, v in enumerate(calls):
        by_text.setdefault(digest(v["text"]), i)
    if len(keys) != completed:
        raise ValueError("Ambiguous historical post")
    inventory = read(bound(b / "prefix-pins.json", receipt["prefixInventoryPin"]))
    return (a, b), protocols, calls, keys, by_text, prefix, inventory


def prepare(out, check):
    audit = read(ROOT / "Q24-transfer.json")
    mirror = Path(audit["mirror"])
    q24 = read(bound(mirror / "receipt.json", Q24))
    if (
        audit["receiptPin"] != Q24
        or not audit["nativeExited"]
        or not audit["priorFlockReleased"]
        or not q24["nativeExited"]
        or not q24["priorLocksReleased"]
    ):
        raise ValueError("Q24 exact native exit and lease releases required")
    compact = bound(mirror / "whole-authors.jsonl.gz", q24["compactPin"])
    counts = defaultdict(int)
    group_of = {}
    for ordinal, post, _, _ in rows(compact):
        if post in group_of:
            raise ValueError("Duplicate Q24 post")
        group_of[post] = ordinal
        counts[ordinal] += 1
    if len(group_of) != q24["rows"] or set(counts) != set(range(q24["wholeAuthors"])):
        raise ValueError("Q24 return does not cover complete author ordinals")
    q20 = WEEK / "Q20-inputs-a"
    cfg = read(bound(q20 / "receipt.json", Q20))
    selected = []
    seen = set()
    short = 0
    for _, raw in groupby(
        rows(bound(q20 / "local-joins.jsonl.gz", cfg["joinsPin"])),
        key=lambda r: r["author"],
    ):
        check()
        group = [
            {k: r[k] for k in ("id", "day", "opening")}
            for r in raw
            if r["id"] in group_of and r["qualifies"] and r["opening"]
        ]
        if not group:
            continue
        idx = group_of[group[0]["id"]]
        if (
            idx in seen
            or len(group) != counts[idx]
            or any(group_of[r["id"]] != idx for r in group)
        ):
            raise ValueError("Original Q20 author or posting dates differ")
        seen.add(idx)
        chosen = select_by_date(group)
        short += int(not chosen)
        selected.extend((idx, half, r) for half, r in chosen)
    if seen != set(counts):
        raise ValueError("Missing whole author from original input")
    selected.sort(
        key=lambda item: item[0]
    )  # Preserve the seeded order inside each half.
    folders, protocols, calls, keys, by_text, prefix, inventory = old_study()
    reuse = {}
    origins = {"samePost": 0, "sameOpening": 0, "new": 0}
    target = out / "openings.jsonl.gz"
    with gzip.open(target, "xt", encoding="utf8", newline="\n") as f:
        for pos, (author, half, post) in enumerate(selected):
            if pos % 100 == 0:
                check()
            task = {
                "id": post["id"],
                "opening": post["opening"],
                "ordinal": author,
                "half": half,
            }
            i = keys.get(post["id"])
            kind = "samePost" if i is not None else "sameOpening"
            if i is None:
                i = by_text.get(post["opening"])
            if i is None:
                origins["new"] += 1
            else:
                if digest(calls[i]["text"]) != post["opening"]:
                    raise ValueError("Historical input bytes differ on the same post")
                if i not in reuse:
                    suffix = int(i >= prefix)
                    j = i - prefix if suffix else i
                    source = folders[suffix] / "W" / f"row-{j:06d}.json"
                    sha = pin(source)
                    if not suffix and inventory[source.name] != sha:
                        raise ValueError("Original W prefix row changed")
                    value = historic(read(source), calls[i], protocols[suffix], j)
                    reuse[i] = {
                        "job": folders[suffix].name,
                        "index": j,
                        "rowPin": sha,
                        "values": value,
                    }
                task["reuse"] = reuse[i]
                origins[kind] += 1
            f.write(json.dumps(task, separators=(",", ":")) + "\n")
    ans = {
        "card": "G15-inputs",
        "q24ReceiptPin": Q24,
        "q20InputPin": Q20,
        "g11ReceiptPins": [G11, G11B],
        "protocolPins": list(PROTOCOLS),
        "sameReaderSettings": {k: protocols[0][k] for k in FIELDS},
        "rosterPin": pin(target),
        "shards": cfg["shards"],
        "wholeAuthors": len(seen),
        "eligibleAuthors": len(seen) - short,
        "fewerThanTenInEitherHalf": short,
        "posts": len(selected),
        "reuse": origins,
    }
    if len(selected) != 20 * ans["eligibleAuthors"] or sum(origins.values()) != len(
        selected
    ):
        raise ValueError("G15 selection or reuse census differs")
    write(out / "selection.json", ans)
    return ans
