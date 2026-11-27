"""Project aggregate counts from the retained October rehearsal and November fold receipts."""

import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project():
    reader = Path(".local/engine-readings")
    receipt_path = reader / "reading-receipt.json"
    model_path = reader / "coauthor-internal-model.json"
    (demo,) = (
        item for item in load(receipt_path) if item["name"] == "coauthor-internal"
    )
    model = load(model_path)
    choices = sum(model["counts"].values())
    if choices != len(model["train_ids"]) or demo["public_release"] is not False:
        raise ValueError("Original internal fit or receipt differs")
    folds = []
    for index in range(4):
        path = Path(f".local/trigger/tp23-base-fold-{index}-completion.json")
        audit = load(path)
        if not audit["foldOnly"] or not audit["originalFoldOrderAndTruthVerified"]:
            raise ValueError("Unverified base fold")
        source = Path(audit["job"]) / "receipt.json"
        if sha(source) != audit["sourceReceiptPin"]:
            raise ValueError("Original fold receipt differs")
        folds.append(
            {
                "fold": index,
                "heldOutLines": audit["heldoutShape"][0],
                "developmentAuc": audit["developmentAuc"],
                "sourceReceiptPin": sha(source),
            }
        )
    access_path = Path(".local/rapid-20261127/sources-in-place.json")
    access = load(access_path)
    return {
        "heldAccess": {
            "sparkInPlace": access["sparkOpenMountForSources"],
            "sourceRowsRead": access["sourceRowsRead"],
            "rawCopies": access["rawCopies"],
            "receiptPin": sha(access_path),
        },
        "coauthor": {
            "sessions": 1,
            "writers": len(model["counts"]),
            "decisions": demo["decisions"],
            "corrections": demo["corrections"],
            "fittedChoices": choices,
            "readingReceiptPin": sha(receipt_path),
            "fitReceiptPin": sha(model_path),
        },
        "baseFolds": folds,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    dest = Path("engine/validation/r48-legacy-2026-11.json")
    payload = json.dumps(project(), indent=2, allow_nan=False) + "\n"
    if args.check:
        if dest.read_text("utf8") != payload:
            raise SystemExit("Legacy aggregate differs")
    else:
        dest.write_text(payload, encoding="utf8", newline="\n")
