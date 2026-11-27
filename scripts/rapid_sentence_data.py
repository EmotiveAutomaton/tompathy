"""Verify the original sentence roster, ten outputs, worry and each stored reader label once."""

import json
from pathlib import Path

import numpy as np
from rapid_head_check import bound, pin, read
from tompathy_engine.eval.readers.tp31_teacher import valid_label
from tompathy_engine.eval.readers.tp39 import SUPPORT
from tompathy_engine.eval.readers.tp40 import MANIFEST, load_labels, verified_job
from week_display import PT, sources
from word_table_lane import write

WORK = Path(".local/rapid-20261127")
Q21 = "574e724abfdeafbe0ce067a495f21142cc0a557f9a560a1cf796ae816f1e8695"
Q34 = "d1194417e2159f036f5856889427106c0f8aa4d4f6782dcfb8be68d53167da5c"
CLASSES = ("none", "ahead", "already", "ongoing")
WHO = ("nobody", "writer", "someone_else")


def classes(row):
    if row is None:
        return -1, -1
    return CLASSES.index(row["when"]), WHO.index(row["whose"])


def c_marks(items, h, check):
    audit = read(PT / "Q14-transfer-a.json")
    public = read(Path("engine/validation/readers-q14-bs-2026-11.json"))
    folder = Path(audit["mirror"])
    r = read(bound(folder / "receipt.json", public["sourceReceiptPin"]))
    if (
        audit["sourceReceiptPin"] != public["sourceReceiptPin"]
        or not audit["nativeExited"]
        or not audit["priorFlockReleased"]
        or r["status"] != "complete"
        or r["attempt"] != 3
    ):
        raise ValueError("Original C pilot is incomplete")
    inventory = read(bound(PT / "Q14-transfer-a-pins.json", audit["inventoryPin"]))
    binding = r["summary"]["binding"]
    if (
        binding["inputPin"] != h
        or binding["role"] != "C"
        or binding["modelPin"]
        != "8b9d11d807c57feb1e2ecb0d6cbf40334c37dcc3523bed5540af4f927f112a37"
    ):
        raise ValueError("C label source differs")
    values = []
    for i, item in enumerate(items):
        if i % 128 == 0:
            check()
        name = f"C/row-{i:06d}.json"
        row = read(bound(folder / name, inventory[name]))
        try:
            value = valid_label(json.loads(row["response"]["response"]))
        except (ValueError, TypeError, KeyError):
            value = None
        if (
            row["id"] != item["id"]
            or row["index"] != i
            or row["binding"] != binding
            or row["values"] != value
        ):
            raise ValueError("C response differs from original row")
        values.append(value)
    return values, audit["sourceReceiptPin"]


def prepare(out, check):
    roster = read(bound(PT / "inputs/manifest.json", MANIFEST))
    support = read(bound(PT / "tp39-support.json", SUPPORT))
    entries = read(bound(PT / "private-parents.json", support["parentsPin"]))
    idx = {r[0]: i for i, r in enumerate(entries)}
    if len(idx) != 30900 or len(idx) != len(entries):
        raise ValueError("Incorrect original parent roster")
    q21, a = sources()
    aud = read(WORK / "Q34-b-transfer.json")
    q34 = Path(aud["mirror"])
    worry = read(bound(q34 / "receipt.json", Q34))
    if (
        a["sourceReceiptPin"] != Q21
        or aud["sourceReceiptPin"] != Q34
        or not aud["nativeExited"]
        or not aud["ownedFlockReleased"]
        or worry["status"] != "complete"
    ):
        raise ValueError("Require both verified frozen-reader returns")
    marks = {k: verified_job(PT, k) for k in ("Q11", "Q12", "G4")}
    source_pins = {k: pin(v[0] / "receipt.json") for k, v in marks.items()}
    files = {}
    chunks = []
    parent_counts = np.zeros(len(idx), int)
    for block in ("Q11", "Q12"):
        h = roster["files"][block]
        items = read(bound(PT / "inputs" / (block + ".json"), h))
        b = load_labels(block, block, "B", items, h, marks[block], check)
        w = load_labels("G4", block, "W", items, h, marks["G4"], check)
        if block == "Q11":
            c, source_pins["Q14"] = c_marks(items, h, check)
        else:
            c = [None] * len(items)
        triples = np.asarray(
            [
                [classes(br), classes(wr), classes(cr)]
                for br, wr, cr in zip(b, w, c, strict=True)
            ],
            np.int8,
        )
        labels = []
        for i in range(0, len(items), 100):
            check()
            name = f"{block}-{i:07d}.npz"
            with (
                np.load(bound(q21 / name, a["files"][name]), allow_pickle=False) as t,
                np.load(
                    bound(q34 / name, worry["artifacts"][name]), allow_pickle=False
                ) as z,
            ):
                y = np.column_stack((t["ten"], z["worry"].reshape(-1)))
            if y.shape != (min(100, len(items) - i), 11) or not np.isfinite(y).all():
                raise ValueError("Sentence-level fixed forecast coverage differs")
            labels.append(y)
        parents = np.array([idx[r["parent"]] for r in items])
        ordinal = np.zeros(len(items), int)
        for i, (j, row) in enumerate(zip(parents, items, strict=True)):
            if entries[j][1] != row["source"] or entries[j][5] != block:
                raise ValueError("Original writer or source binding differs")
            ordinal[i] = parent_counts[j]
            parent_counts[j] += 1
        chunks.append((parents, ordinal, triples, np.vstack(labels)))
        write(
            out / "progress.json",
            {"stage": block, "sentences": sum(len(x[0]) for x in chunks)},
        )
    if parent_counts.sum() != 51557 or not (parent_counts > 0).all():
        raise ValueError("Incomplete original sentence alignment")
    dest = out / "aligned.npz"
    parents, ordinal, role_marks, forecasts = [
        np.concatenate(x) for x in zip(*chunks, strict=True)
    ]
    with dest.open("xb") as f:
        np.savez_compressed(
            f,
            parents=parents,
            ordinal=ordinal,
            marks=role_marks,
            forecasts=forecasts,
            counts=parent_counts,
            source=np.array([r[1] for r in entries]),
            original=np.array([str(r[2]) for r in entries]),
            writer=np.array([str(r[3]) for r in entries]),
            word=np.array([r[4] for r in entries]),
            stage=np.array([r[5] for r in entries]),
        )
    files[dest.name] = pin(dest)
    return {
        "card": "TP65-inputs",
        "files": files,
        "marks": source_pins,
        "ten": Q21,
        "worry": Q34,
        "parents": support["parentsPin"],
        "manifest": MANIFEST,
        "sentences": 51557,
        "reports": len(entries),
    }
