"""Q32. Match the registered reader and wording panels to B's original standing marks."""

from pathlib import Path

import numpy as np
from rapid_cpu_dispatch import ROOT
from rapid_head_check import bound, read
from rapid_marks import CHOICES, digest, protocol
from rapid_standing_agreement import SOURCES, authors, decode, table
from rapid_standing_return import REG
from word_table_lane import write

RECEIPTS = {
    "Q27": "0df9eaea92fb4757dac8c9d04ccccf8986a2f96916a3081c6e1b159e4fbdcd9e",
    "Q32": "c95a62ab78bc0bd069534c12db35d4b55a9056bc953f3044e9ccd969ac7e5be6",
}


def selected_marks(job, arm, reader, kind, roster, selection, cfg, check):
    transfer = read(ROOT / (job + "-transfer.json"))
    if (
        transfer["sourceReceiptPin"] != RECEIPTS[job]
        or not transfer["nativeExited"]
        or not transfer["ownedFlockReleased"]
    ):
        raise ValueError("Unverified standing-panel transfer")
    folder = Path(transfer["mirror"])
    receipt = read(bound(folder / "receipt.json", RECEIPTS[job]))
    files = receipt["artifacts"]
    terminal = read(
        bound(folder / arm / "complete.json", files[arm + "/complete.json"])
    )
    settings = read(bound(folder / arm / "protocol.json", terminal["protocolPin"]))
    if (receipt["result"] if job == "Q27" else receipt["result"][arm]) != terminal or (
        len(roster) != terminal["rows"]
        or settings["width"] != 1
        or digest("\n".join(roster)) != terminal["inputPin"]
        or settings["inputPin"] != terminal["inputPin"]
        or [settings["model"], settings["modelPin"]] != cfg["readers"][reader]
        or not all(settings[k] == v for k, v in protocol(kind).items())
        or settings["think"] is not False
        or settings["options"]["temperature"] != 0
        or settings["options"]["seed"] != 23
    ):
        raise ValueError("Panel roster, submitted protocol or model differs")
    lookup = {s: i for i, s in enumerate(roster)}
    output = {}
    for j, s in enumerate(selection):
        if j % 100 == 0:
            check()
        file = f"{arm}/from-{lookup[s]:06d}.json"
        (row,) = read(bound(folder / file, files[file]))
        if row["id"] != s:
            raise ValueError("Misaligned standing response")
        output[s] = decode(row)
    if (
        len(selection) == len(roster)
        and sum(v[0] >= 0 for v in output.values()) != terminal["valid"]
    ):
        raise ValueError("Standing validity count differs")
    return output, terminal["protocolPin"]


def prepare(out, check):
    cfg = read(bound(ROOT / "registration.json", REG))
    manifest = read(bound(ROOT / "inputs/inputs.json", cfg["inputManifest"]))
    ids, writers, corpora, _ = authors(manifest)
    panel = [
        s
        for src in SOURCES
        for s in sorted(
            (s for s, c in zip(ids, corpora, strict=True) if c == src),
            key=lambda s: digest("Q32:23:" + s),
        )[:500]
    ]
    reword = sorted(panel, key=lambda s: digest("Q32:reword:23:" + s))[:1000]
    owner = dict(zip(ids, writers, strict=True))
    panels = {}
    protocols = {}
    for job, arm, reader, kind, roster, selection in (
        ("Q27", "B", "B", "standing", ids, panel),
        ("Q32", "C", "C", "standing", panel, panel),
        ("Q32", "standing2", "B", "standing2", reword, reword),
        ("Q32", "standing3", "B", "standing3", reword, reword),
    ):
        panels[arm], protocols[arm] = selected_marks(
            job, arm, reader, kind, roster, selection, cfg, check
        )
    results = {}
    for first, second, subset in (
        ("B", "C", panel),
        ("B", "standing2", reword),
        ("B", "standing3", reword),
        ("standing2", "standing3", reword),
    ):
        a = np.array([panels[first][s] for s in subset])
        b = np.array([panels[second][s] for s in subset])
        groups = np.array([owner[s] for s in subset])
        cells = {}
        for i, (field, levels) in enumerate(CHOICES.items()):
            cell = table(a[:, i], b[:, i], groups, levels, check)
            cell["firstOnly"] = cell.pop("BOnly")
            cell["secondOnly"] = cell.pop("WOnly")
            for key in (
                "CW",
                "atOrAboveUsable",
                "atOrBelowUsable",
                "atOrBelowWeakFloor",
            ):
                cell.pop(key, None)
            cells[field] = cell
        results[f"{first}/{second}"] = cells
    result = {
        "readerReceipts": RECEIPTS,
        "protocols": protocols,
        "draws": 2000,
        "tables": results,
        "inputManifest": cfg["inputManifest"],
    }
    write(out / "table.json", result)
    return result
