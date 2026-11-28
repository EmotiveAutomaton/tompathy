"""TP63's registered reader-B supplement, using the original writer and null reference."""

import csv
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, read
from rapid_marks import core, digest
from rapid_outside import (
    GENERATION,
    KEYS,
    fit_table,
    table_cells,
    writer_traits,
    writer_values,
)
from week_pride_inputs import FROZEN, SOURCE
from word_table_lane import write

Q28 = "7c5f8d44e34a0cb34def2fd86987044df80f163d1d97d89cb4de61e428ec08c1"
ORIGINAL = "0e1675b77740d6e9c552365f67bb3ad0503dc56e5d680bdaefcf90f147df8a3f"


def prepare(out, check):
    original = ROOT / "TP63-original-a"
    if confirmed(original) != ORIGINAL:
        raise ValueError("TP63 original writer panel differs")
    previous = read(original / "receipt.json")["result"]
    archive = read(ROOT / "Q28-transfer.json")
    if (
        archive["sourceReceiptPin"] != Q28
        or not archive["nativeExited"]
        or not archive["ownedFlockReleased"]
    ):
        raise ValueError("Unverified Q28 transfer")
    source = Path(archive["mirror"])
    receipt = read(bound(source / "receipt.json", Q28))
    names = list(core.FEATURES)
    intake = read(bound(FROZEN / "receipt.json", SOURCE))
    fields = [
        "text_id",
        "emotion",
        "prolific_id",
        *(field for pair in KEYS.values() for field in pair),
    ]
    frame = pd.read_csv(
        bound(GENERATION, intake["sources"]["envent"]["files"]["generation"]),
        sep="\t",
        quoting=csv.QUOTE_NONE,
        usecols=fields,
        dtype=str,
        keep_default_na=False,
    )
    ids = [
        hashlib.sha256(("R37:23:envent:" + i).encode()).hexdigest()
        for i in frame.text_id
    ]
    summary = read(
        bound(source / "B/complete.json", receipt["artifacts"]["B/complete.json"])
    )
    protocol = read(bound(source / "B/protocol.json", summary["protocolPin"]))
    if (
        protocol["schema"]["required"] != names
        or protocol["inputPin"] != summary["inputPin"]
    ):
        raise ValueError("The registered feature order or binding differs")
    if (
        len(ids) != 6600
        or len(set(ids)) != len(ids)
        or summary["inputPin"] != digest("\n".join(ids))
    ):
        raise ValueError("The pinned report set or order differs")
    values = []
    for pos, expected in enumerate(ids):
        if pos % 100 == 0:
            check()
        path = f"B/from-{pos:06d}.json"
        (row,) = read(bound(source / path, receipt["artifacts"][path]))
        features = row["values"]
        if (
            row["id"] != expected
            or type(features) is not list
            or len(features) != len(names)
        ):
            raise ValueError("Incomplete or misaligned Q28 response")
        if not all(type(v) is int and 1 <= v <= 5 for v in features):
            raise ValueError("Feature outside the frozen Q28 response scale")
        values.append(features)
    if summary["valid"] != len(values) or summary["rows"] != len(values):
        raise ValueError("Q28 validity and rows differ")
    owners, writer = np.unique(frame.prolific_id.to_numpy(str), return_inverse=True)
    _, feeling = np.unique(frame.emotion.to_numpy(str), return_inverse=True)
    traits, census = writer_traits(frame, owners)
    if census != previous["targets"] or len(owners) != previous["writers"]:
        raise ValueError("Recalled-event writer cohort differs from the original table")
    r, draws = fit_table(
        writer_values(np.array(values, dtype=float), feeling, writer), traits, check
    )
    rows = table_cells(r, draws, previous["bars"], names, census)
    for feat in rows.values():
        for trait, cell in feat.items():
            if cell["value"] is not None:
                historical = [
                    abs(table[trait]["value"])
                    for table in previous["outputs"].values()
                    if table[trait]["value"] is not None
                ]
                cell["leadsColumn"] &= abs(cell["value"]) >= max(historical)
    result = {
        "originalReceipt": ORIGINAL,
        "readerReceipt": Q28,
        "readerProtocol": summary["protocolPin"],
        "reports": len(values),
        "writers": len(owners),
        "targets": census,
        "bootstrapDraws": len(draws),
        "bars": previous["bars"],
        "outputs": rows,
    }
    write(out / "table.json", result)
    return result
