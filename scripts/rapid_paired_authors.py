"""Bind the B/W paired author cohort from Q24, G11 and the terminal G15 prefix."""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_filler_gpu import new_items, originals
from rapid_filler_inputs import Q24
from rapid_head_check import bound, pin, read
from rapid_marks import digest, template
from week_people import rows
from word_table_lane import core

REG = "17094852b30f0b78c4ff030e9624b1d09564498574521cfcd5b65b9eec61c7cc"
RELEASE = "9dad62136fca5e825fba6b02e79821430f4ee5caff19f02cb9ab6d486c432a43"
FAILURE = "ba49cd8797c3e7af531b569af17e6b45069f5774520cc9c7d4ce3f1ae1ca101b"


def prepare(out, check):
    cfg = read(bound(ROOT / "G15-registration.json", REG))
    stage = ROOT / "jobs/G15"
    owner = read(stage / "owner.json")
    stop = read(bound(stage / "failed.json", FAILURE))
    release = read(bound(stage / "released.json", RELEASE))
    if not (
        owner == release["owner"] == stop["owner"]
        and owner["registration"] == REG
        and release["exitCode"] == 1
        and release["sharedLeaseReacquired"]
        and release["childWaited"]
    ):
        raise ValueError("Unverified G15 memory stop")
    if confirmed(ROOT / cfg["inputStage"]) != cfg["inputReceiptPin"]:
        raise ValueError("Unverified G15 input stage")
    selection, roster, texts = originals(ROOT, cfg, check)
    intake = read(stage / "intake.json")
    if (
        intake["binding"] != cfg["modelSettings"]
        or intake["rosterPin"] != selection["rosterPin"]
        or cfg["modelSettings"] != selection["sameReaderSettings"]
    ):
        raise ValueError("G15 model or original G11 reuse binding differs")
    index, calls = new_items(
        roster, texts, intake["binding"]["prompt"], intake["binding"]["options"]
    )
    del texts
    if (
        digest("\n".join(x["id"] for x in calls)) != intake["orderedNewIds"]
        or len(calls) != intake["new"]
    ):
        raise ValueError("G15 call order differs")
    parser = template("features")[2]
    new = []
    for j, f in enumerate(sorted((stage / "W").glob("from-*.json"))):
        if f.name != f"from-{j:06d}.json":
            raise ValueError("Incomplete G15 durable prefix")
        (row,) = read(f)
        try:
            v = parser(json.loads(row["response"]))
        except (TypeError, ValueError):
            v = None
        if row["values"] != v or row["id"] != calls[j]["id"]:
            raise ValueError("G15 response or position differs")
        new.append(v)
    handoff = read(ROOT / "Q24-transfer.json")
    mirror = Path(handoff["mirror"])
    receipt = read(bound(mirror / "receipt.json", Q24))
    if (
        handoff["receiptPin"] != Q24
        or not handoff["nativeExited"]
        or not handoff["priorFlockReleased"]
    ):
        raise ValueError("Unverified Q24 return")
    b = {}
    for i, (ordinal, post, values, _) in enumerate(
        rows(bound(mirror / "whole-authors.jsonl.gz", receipt["compactPin"]))
    ):
        if i % 4096 == 0:
            check()
        if post in b:
            raise ValueError("Duplicate Q24 post")
        b[post] = (ordinal, values)
    if len(b) != receipt["rows"]:
        raise ValueError("Incomplete Q24 return")
    paired = []
    keys = []
    postids = []
    ordinals = []
    cohort = []
    census = Counter()
    sources = Counter()
    size = 20
    for start in range(0, len(roster), size):
        check()
        group = roster[start : start + size]
        if (
            len({r["ordinal"] for r in group}) != 1
            or [r["half"] for r in group] != [0] * 10 + [1] * 10
        ):
            raise ValueError("Rows span authors or different date halves")
        ordinal = group[0]["ordinal"]
        values = []
        historical = True
        for row, (kind, j) in zip(group, index[start : start + size], strict=True):
            bowner, bv = b[row["id"]]
            if bowner != ordinal:
                raise ValueError("B/W author mismatch")
            wv = None
            if kind == "historical":
                wv = row["reuse"]["values"]
            elif kind == "new" and j < len(new):
                wv = new[j]
            elif kind == "context":
                sources["contextUnavailable"] += 1
            if kind != "historical":
                historical = False
            if bv is None or wv is None:
                continue
            if any(
                len(x) != len(core.FEATURES)
                or any(type(v) is not int or not 1 <= v <= 5 for v in x)
                for x in (bv, wv)
            ):
                raise ValueError("Invalid eight-feature rating")
            values.append([bv, wv])
            sources["validPairsAllOpenings"] += 1
        if len(values) != size:
            census["incomplete"] += 1
            continue
        paired.append(values)
        ordinals.append(ordinal)
        cohort.append(historical)
        keys.append([v["opening"] for v in group])
        postids.append([v["id"] for v in group])
        census["complete"] += 1
        census["historicalComplete"] += int(historical)
    if census["incomplete"] + census["complete"] != selection["eligibleAuthors"]:
        raise ValueError("Matched author census differs")
    path = out / "paired.npz"
    with path.open("xb") as f:
        np.savez_compressed(
            f,
            values=np.array(paired, dtype=np.int8).reshape(
                -1, 20, 2, len(core.FEATURES)
            ),
            opening=np.array(keys, dtype="U64").reshape(-1, 20),
            post=np.array(postids, dtype="U64").reshape(-1, 20),
            ordinal=np.array(ordinals, dtype=int),
            historical=np.array(cohort, dtype=bool),
        )
    return {
        "cohort": dict(census),
        "coverage": dict(sources),
        "newDurable": len(new),
        "eligibleAuthors": selection["eligibleAuthors"],
        "BReceipt": Q24,
        "G15Release": RELEASE,
        "roster": selection["rosterPin"],
        "pairedPin": pin(path),
    }
