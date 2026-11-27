"""Land source-bound Round 37 aggregates. Private reader answers stay in the job."""

import argparse
import json
from pathlib import Path

from rapid_display import prepare
from tompathy_engine.eval.evidence import append
from word_table_lane import pin, read

ROOT = Path(".local/rapid-20261127")
PUBLIC = Path("engine/validation")


def put(path, value):
    data = (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Preserve the existing result at " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data)


def display():
    result = prepare()
    predecessor = result.pop("sourceReceiptPin")
    files = [
        "scripts/rapid_display.py",
        "engine/tompathy_engine/packet/research_labels.py",
        "engine/tompathy_engine/packet/build.py",
        "engine/tompathy_engine/eval/readers/trigger_export.py",
        "src/core/bottom-box.ts",
        "src/core/export-privacy.ts",
        "src/core/need-view.ts",
        "src/components/NeedLandscape.tsx",
        "src/components/ResearchReadings.tsx",
    ]
    receipt = ROOT / "TP71-a/receipt.json"
    put(
        receipt,
        {
            "status": "complete",
            "sourceTP60ReceiptPin": predecessor,
            "result": result,
            "code": {f: pin(Path(f)) for f in files},
        },
    )
    h = pin(receipt)
    public = PUBLIC / "readers-tp71-2026-11.json"
    ledger = "E-TP71-20261127"
    put(
        public,
        {
            **result,
            "sourceTP60ReceiptPin": predecessor,
            "sourceReceiptPin": h,
            "ledger": ledger,
        },
    )
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ledger,
            "date": "2026-11-27",
            "family": "Round 37 display contract",
            "claims": ["W1"],
            "question": "Which public reading names and groups does the approved display use?",
            "data": public.as_posix(),
            "estimate": {
                "sourceReceiptPin": h,
                "sourceTP60AggregatePin": result["sourceAggregatePin"],
            },
            "interval": "Retains the original 304 tag-specific reliability entries and their intervals.",
            "bar": "Engineering contract and compatibility checks. No scientific pass bar.",
            "verdict": "Filed under R47 and CZ.",
            "limit": "Display and export wording only.",
        },
    )
    return {"public": public.as_posix(), "sourceReceiptPin": h, "sha256": pin(public)}


def throughput():
    from rapid_marks import compare

    transfer = read(ROOT / "Q26-transfer.json")
    base = Path(transfer["mirror"])
    h = transfer["sourceReceiptPin"]
    if (
        not transfer["nativeExited"]
        or not transfer["ownedFlockReleased"]
        or pin(base / "receipt.json") != h
    ):
        raise ValueError("Verified return required")
    receipt = read(base / "receipt.json")
    widths = {}
    pilots = {}
    for width in (1, 2, 4):
        folder = base / f"width-{width}"
        rows = [r for batch in sorted(folder.glob("from-*.json")) for r in read(batch)]
        widths[width] = (rows, read(folder / "complete.json")["seconds"])
        pilots[width] = read(folder / "first100.json")["elapsedSeconds"]
    result = compare(widths)
    if json.loads(json.dumps(result)) != receipt["result"]:
        raise ValueError(
            "Stored throughput comparison differs from returned individual answers"
        )
    public = PUBLIC / "readers-q26-throughput-2026-11.json"
    put(
        public,
        {
            "job": "Q26",
            "texts": 200,
            "modelPin": read(base / "width-1/protocol.json")["modelPin"],
            "promptPin": read(base / "width-1/protocol.json")["promptPin"],
            "first100Seconds": pilots,
            "result": result,
            "sourceReceiptPin": h,
            "verifiedFiles": transfer["files"],
            "scope": "Local structured output throughput and agreement. Invalid serial outputs cannot qualify a width.",
        },
    )
    return {"public": public.as_posix(), "sourceReceiptPin": h, "sha256": pin(public)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("result", choices=["TP71", "Q26"])
    choice = p.parse_args().result
    print(json.dumps((display if choice == "TP71" else throughput)()))
