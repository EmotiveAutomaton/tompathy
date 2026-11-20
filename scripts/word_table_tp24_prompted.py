"""Assemble TP24's first 6,250 saved B forecasts locally, without scoring targets."""
import argparse
import json
import os
import sys
from pathlib import Path

for setting in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[setting] = "2"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import numpy as np
from tompathy_engine.eval.readers.word_panels import (
    FEATURES,
    Q1_SOURCE,
    READER_IDS,
    SELECTION,
    Mirror,
    pinned,
    read,
    sha256,
)

BASE = ROOT / ".local/word-table"
INTAKE = "d341f467c063197375e8dea2b7da016a6783f4e873b7f067f6269d5eafb9be5e"
Q2_SOURCE = "d9191c98961ab62cb44ccde1e0a6e4a3f054cfaf0ebf3b62a59882fb13e178ee"


def original_rows(pilot, receipt, ids):
    protocol = receipt["protocol"]
    files = pinned(pilot / "artifacts.json", receipt["artifactsPin"])["files"]
    if (protocol["version"] != 2 or tuple(protocol["features"]) != tuple(FEATURES)
            or receipt["row"]["kind"] != "reader-pilot" or receipt["row"]["texts"] != len(ids)
            or receipt["row"]["model"]["digest"] != READER_IDS["B"]):
        raise ValueError("Original corrected B first-pass protocol differs")
    rows = np.full((len(ids), len(FEATURES)), np.nan)
    for index, ident in enumerate(ids):
        name = f"row-{index:04d}.json"
        row = pinned(pilot / name, files[name])
        if (row["id"], row["index"], row["modelPin"]) != (ident, index, READER_IDS["B"]):
            raise ValueError("Original B answer differs from its registered report")
        try:
            raw = json.loads(row["response"]["response"])
        except (KeyError, TypeError, ValueError):
            raw = None
        valid = (isinstance(raw, dict) and set(raw) == set(FEATURES)
                 and all(type(raw[key]) is int and 1 <= raw[key] <= 5 for key in FEATURES))
        values = [raw[key] for key in FEATURES] if valid else None
        if values != row["values"]:
            raise ValueError("Original B raw and parsed answers disagree")
        if valid:
            rows[index] = values
    if int(np.isfinite(rows).all(axis=1).sum()) != receipt["row"]["valid"]:
        raise ValueError("Original B validity count differs")
    return rows


def assemble(directory):
    directory = directory.resolve()
    if directory.parent != BASE.resolve() or directory.exists():
        raise ValueError("Use a fresh direct child of the private study directory")
    intake = pinned(BASE / "TP24-mixed-intake-a.json", INTAKE)
    pilot = ROOT / ".local/nine-channel/spark/sp1-v2-reader-b-pilot-a"
    previous = pinned(pilot / "receipt.json", intake["priorPilotPin"])
    panels = pinned(BASE / "intake-a/reserved-ids.json", SELECTION)
    q1 = Mirror(BASE / "verified-spark-Q1-a", "Q1")
    q2 = Mirror(BASE / "verified-spark-Q2-a", "Q2")
    terminal = read(BASE / "Q2-transfer-a.json")
    if (q1.pin != Q1_SOURCE or q2.pin != Q2_SOURCE or not terminal["priorFlockReleased"]
            or not terminal["nativeExited"] or terminal["sourceReceiptPin"] != q2.pin):
        raise ValueError("Original Q1/Q2 terminal evidence differs")
    roster = BASE / "intake-a/spark"
    manifest = pinned(roster / "source.json", q2.receipt["entry"]["sourcePin"])
    ids = {"SP1": panels["sp1"], "Q1": panels["F1"],
           "Q2": [r["id"] for r in pinned(roster / "Q2.json", manifest["jobs"]["Q2"]["filePin"])]}
    all_ids = [ident for cohort in ids.values() for ident in cohort]
    if ({k: len(v) for k, v in ids.items()} != {"SP1": 500, "Q1": 350, "Q2": 5400}
            or len(set(all_ids)) != 6250 or set(all_ids) & set(panels["F2"])):
        raise ValueError("Duplicate, missing or reserved report in opening TP24 data")
    protocol = previous["protocol"]
    options = {"num_ctx": protocol["context"], "num_predict": protocol["outputTokens"],
               "num_thread": protocol["numericalThreads"], "seed": protocol["seed"],
               "temperature": protocol["temperature"]}
    arrays = {"SP1": original_rows(pilot, previous, ids["SP1"])}
    schema = q1.receipt["roles"]["B"]["binding"]["schemaPin"]
    for name, mirror in (("Q1", q1), ("Q2", q2)):
        summary = read(mirror.artifact("B/complete.json"))
        binding = summary["binding"]
        if (binding != mirror.receipt["roles"]["B"]["binding"] or binding["modelPin"] != READER_IDS["B"]
                or binding["promptPin"] != protocol["promptPin"] or binding["options"] != options
                or binding["schemaPin"] != schema or binding["think"] != protocol["thinking"]):
            raise ValueError("The opening panels use different reader settings")
        arrays[name] = mirror.answers("", "B", ids[name], FEATURES, lambda: None)
    directory.mkdir(exist_ok=False)
    archive = directory / "prompted.npz"
    with archive.open("xb") as stream:
        np.savez_compressed(stream, reportIds=np.asarray(all_ids), features=np.asarray(FEATURES),
                            cohorts=np.concatenate([np.repeat(k, len(v)) for k, v in ids.items()]),
                            ratings=np.vstack(list(arrays.values())))
    result = {"stage": "TP24 initial prompted input", "sourceReceiptPins": {
                  "SP1": intake["priorPilotPin"], "Q1": q1.pin, "Q2": q2.pin},
              "selectionPin": SELECTION, "modelPin": READER_IDS["B"], "promptPin": protocol["promptPin"],
              "schemaPin": schema, "options": options, "features": list(FEATURES), "archivePin": sha256(archive),
              "cohorts": {k: {"attempted": len(v), "valid": int(np.isfinite(v).all(axis=1).sum())}
                          for k, v in arrays.items()},
              "reservedIncluded": 0, "newInference": False, "writerRatingsRead": False}
    with (directory / "receipt.json").open("x", encoding="utf8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(assemble(parser.parse_args().directory)))
