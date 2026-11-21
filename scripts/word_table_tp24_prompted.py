"""Assemble the initial or Q5-extended TP24 reader-B inputs from saved forecasts."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

for setting in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[setting] = "2"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import numpy as np
from tompathy_engine.eval.readers.word_panels import (
    CROSSWALK,
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
INITIAL_RECEIPT = "16b1c6aea0e8f0c58eb2fe22fdc2b5bd2520c83b54babcc5b87bf291b0fdb140"


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


def fresh_destination(directory):
    directory = directory.resolve()
    if directory.parent != BASE.resolve() or directory.exists():
        raise ValueError("Use a fresh direct child of the private study directory")
    return directory


def save_archive(directory, ids, cohorts, ratings, metadata):
    with tempfile.TemporaryDirectory(dir=directory.parent) as temporary:
        ready = Path(temporary)/"ready"
        ready.mkdir()
        archive = ready/"prompted.npz"
        with archive.open("xb") as stream:
            np.savez_compressed(stream, reportIds=np.asarray(ids), features=np.asarray(FEATURES),
                                cohorts=cohorts, ratings=ratings)
        result = {**metadata, "archivePin": sha256(archive)}
        with (ready/"receipt.json").open("x", encoding="utf8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
        ready.rename(directory)
    return result


def assemble(directory):
    directory = fresh_destination(directory)
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
    metadata = {"stage": "TP24 initial prompted input", "sourceReceiptPins": {
                  "SP1": intake["priorPilotPin"], "Q1": q1.pin, "Q2": q2.pin},
              "selectionPin": SELECTION, "modelPin": READER_IDS["B"], "promptPin": protocol["promptPin"],
              "schemaPin": schema, "options": options, "features": list(FEATURES), "archivePin": None,
              "cohorts": {k: {"attempted": len(v), "valid": int(np.isfinite(v).all(axis=1).sum())}
                          for k, v in arrays.items()},
              "reservedIncluded": 0, "newInference": False, "writerRatingsRead": False}
    return save_archive(directory, all_ids, np.concatenate([np.repeat(k, len(v)) for k, v in ids.items()]),
                        np.vstack(list(arrays.values())), metadata)


def extend(directory, transfer):
    directory = fresh_destination(directory)
    transfer = transfer.resolve()
    if transfer.parent != BASE.resolve():
        raise ValueError("Use the private Q5 transfer verification")
    proof = read(transfer)
    mirror_path = (ROOT/proof["mirror"]).resolve()
    if mirror_path.parent != BASE.resolve():
        raise ValueError("Q5 mirror lies outside the private study directory")
    q5 = Mirror(mirror_path, "Q5")
    if (not proof["nativeExited"] or not proof["priorFlockReleased"] or proof["status"] != "complete"
            or proof["owner"] != q5.receipt["owner"] or proof["sourceReceiptPin"] != q5.pin):
        raise ValueError("Verified Q5 exit, GPU release and receipt required")

    initial = BASE/"tp24-prompted-initial-a"
    previous = pinned(initial/"receipt.json", INITIAL_RECEIPT)
    archive = initial/"prompted.npz"
    if sha256(archive) != previous["archivePin"]:
        raise ValueError("The initial archive no longer matches its receipt")
    panels = pinned(BASE/"intake-a/reserved-ids.json", SELECTION)
    ids = panels["F2"]
    crosswalk = pinned(BASE/"F2-release-local/local-original-id-map.json", CROSSWALK)
    if set(ids) != set(crosswalk) or len(ids) != 350 or len(set(crosswalk.values())) != 350:
        raise ValueError("F2 original and opaque IDs must match one-to-one")
    selection_pin = sha256(q5.artifact("development-selection.json"))
    delivery = read(BASE/"F2-release-local/release-monitor.json")
    if delivery.get("receipt", {}).get("selectionPin") != selection_pin:
        raise ValueError("Held-out delivery must bind the frozen Q5 development choice")
    arm = "F2-standard"
    summary = read(q5.artifact(f"{arm}/B/complete.json"))
    binding = summary["binding"]
    if (q5.receipt["roles"][arm] != summary or binding["think"] is not False
            or any(binding[key] != previous[key] for key in ("modelPin", "promptPin", "schemaPin", "options"))):
        raise ValueError("Q5's standard eight-feature reader differs from the original input")
    added = q5.answers(arm, "B", [crosswalk[k] for k in ids], FEATURES, lambda: None)
    with np.load(archive, allow_pickle=False) as saved:
        prior_ids, prior_cohorts, prior_ratings = saved["reportIds"], saved["cohorts"], saved["ratings"]
        if (saved["features"].tolist() != list(FEATURES) or prior_ids.shape != (6250,)
                or len(set(prior_ids)) != 6250 or set(prior_ids).intersection(ids)
                or prior_cohorts.shape != (6250,) or prior_ratings.shape != (6250,len(FEATURES))):
            raise ValueError("Initial feature order, cohort or report identities differ")
    metadata = {**previous, "stage": "TP24 extended prompted input", "reservedIncluded": 350,
                "initialReceiptPin": INITIAL_RECEIPT, "initialArchivePin": previous["archivePin"],
                "q5TransferPin": sha256(transfer), "q5TransferFile": transfer.name, "developmentSelectionPin": selection_pin,
                "sourceReceiptPins": {**previous["sourceReceiptPins"], "Q5": q5.pin},
                "cohorts": {**previous["cohorts"], "Q5": {"attempted": len(ids), "valid": summary["valid"]}}}
    return save_archive(directory, np.concatenate([prior_ids, ids]), np.concatenate([prior_cohorts, np.repeat("Q5",350)]),
                        np.vstack([prior_ratings, added]), metadata)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--q5-transfer", type=Path, help="Extend the saved initial archive after verified Q5 completion")
    args = parser.parse_args()
    result = extend(args.directory, args.q5_transfer) if args.q5_transfer else assemble(args.directory)
    print(json.dumps(result))
