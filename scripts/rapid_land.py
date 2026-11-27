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


def slope():
    import numpy as np
    from rapid_slope_return import PREP, SOURCE

    source = ROOT / ("verified-TP61-slopes-" + SOURCE[:12])
    r = read(source / "receipt.json")
    verified = read(source / "transfer.json")
    if (
        pin(source / "receipt.json") != SOURCE
        or r["sourceReceiptPin"] != PREP
        or verified["sourceReceiptPin"] != SOURCE
        or verified["setsVerified"] != 400
        or not verified["nativeExited"]
        or not verified["cpuLeaseReacquired"]
    ):
        raise ValueError("Verified two-family slope return required")
    old = Path(".local/week-20261122/TP52-a/receipt.json")
    if pin(old) != "2f7236ded4408f4da09edcbcca63f57f9419aa4cd27f034064d49c4edf97577b":
        raise ValueError("Original worry result differs")
    trained = read(old)["standardizedSlope"]
    target = trained["value"]
    if target != r["registeredTrainedSlope"]:
        raise ValueError("Trained slope differs from the registered source")
    comparison = {}
    for kind in ("iso", "rot"):
        x = np.asarray(r["nullSlopes"][kind], dtype=float)
        if x.shape != (3800,) or not np.isfinite(x).all():
            raise ValueError("All 200 sets of 19 finite slopes are required")
        comparison[kind] = {
            "sets": 200,
            "headsPerSet": 19,
            "band": np.quantile(x, [0.025, 0.975]).tolist(),
            "median": float(np.median(x)),
            "p995": float(np.quantile(x, 0.995)),
            "maximum": float(x.max()),
            "atLeastTrained": int(np.sum(x >= target)),
            "percentile": float(
                (np.sum(x < target) + 0.5 * np.sum(x == target)) / len(x)
            ),
        }
    public = PUBLIC / "readers-tp61-slope-2026-11.json"
    ledger = "E-TP61-D-20261127"
    put(
        public,
        {
            "card": "TP61(d)",
            "sourceReceiptPin": SOURCE,
            "vectorReceiptPin": PREP,
            "trainedReceiptPin": pin(old),
            "trained": trained,
            "cohort": r["data"],
            "comparison": comparison,
            "ledger": ledger,
            "scope": r["scope"],
            "productionAdmission": False,
        },
    )
    complete = all(
        v["atLeastTrained"] == 0 and target > v["p995"] for v in comparison.values()
    )
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ledger,
            "date": "2026-11-27",
            "family": "Round 37 random-head controls",
            "claims": ["P2", "P3", "P5"],
            "question": "Does the original opening-worry slope exceed every random base-vector head on the same disjoint suffixes?",
            "data": public.as_posix(),
            "estimate": {
                "standardizedSlope": target,
                "nulls": comparison,
                "sourceReceiptPin": SOURCE,
            },
            "interval": {
                "trainedWriterInterval": trained["interval"],
                "nullBandPercentiles": [2.5, 97.5],
            },
            "bar": "Above percentile 99.5 in both families, with zero null heads reaching the trained slope.",
            "verdict": "Both clauses met."
            if complete
            else "The registered joint condition misses.",
            "limit": "The trained and null heads use different encoders. This contrast cannot isolate the trained direction or establish an inference about a person.",
        },
    )
    return {
        "public": public.as_posix(),
        "sourceReceiptPin": SOURCE,
        "sha256": pin(public),
        "comparison": comparison,
    }


def whole_author_competence():
    from tompathy_engine.packet.research_labels import tag_keys

    out = ROOT / "TP73-TP51-a"
    h = pin(out / "receipt.json")
    if h != "2026a5d89fa3182c1cf9e63c9bf95ce55bfae330bed5fe3c95cbd9f042be3c1c" or read(
        out / "complete.json"
    ) != {"sourceReceiptPin": h}:
        raise ValueError("TP73 source differs")
    proof = read(out / "exit-verification.json")
    if not all(
        proof.get(k)
        for k in (
            "nativeExited",
            "releaseMatches",
            "sharedLeaseAbsent",
            "localLeaseAbsent",
        )
    ):
        raise ValueError("TP73 release differs")
    raw = read(out / "receipt.json")["result"]
    q24 = raw["q24"]
    if (
        q24["receiptPin"] != read(ROOT / "Q24-transfer.json")["receiptPin"]
        or q24["wholeAuthors"] != 2993
    ):
        raise ValueError("TP73 is not bound to the original Q24 export")
    blog = raw["blog"]
    blog["readings"] = {k: tag_keys(table) for k, table in blog["readings"].items()}
    if (blog["support"]["sourceAuthors"], blog["support"]["sourceRows"]) != (
        q24["wholeAuthors"],
        q24["rows"],
    ):
        raise ValueError("Source cohort differs")
    public = PUBLIC / "readers-tp73-competence-2026-11.json"
    ledger = "E-TP73-TP51-20261127"
    put(
        public,
        {
            "card": "TP73",
            "arm": "TP51 blog extension",
            "sourceReceiptPin": h,
            "q24ReceiptPin": q24["receiptPin"],
            "q20ReceiptPin": raw["q20"],
            "originalExport": {
                "rows": q24["rows"],
                "valid": q24["valid"],
                "wholeAuthors": q24["wholeAuthors"],
            },
            "ledger": ledger,
            "blog": blog,
            "productionAdmission": False,
        },
    )
    curiosity = {
        k: blog["readings"][k]["curiosity"]["competence"] for k in ("between", "within")
    }
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ledger,
            "date": "2026-11-27",
            "family": "Round 37 whole-author panel",
            "claims": ["N1"],
            "question": "How do the prespecified tag and competence contrasts behave across and within blog authors?",
            "data": public.as_posix(),
            "estimate": {k: v["value"] for k, v in curiosity.items()},
            "interval": {k: v["interval"] for k, v in curiosity.items()},
            "bar": "Curiosity–competence correlation at least 0.30 between authors and negative within authors.",
            "verdict": "Both registered curiosity contrasts miss.",
            "limit": "One reader and a selected set of authors with enough openings. Matched CU controls are pending.",
        },
    )
    return {"public": public.as_posix(), "sourceReceiptPin": h, "sha256": pin(public)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("result", choices=["TP71", "Q26", "TP61-d", "TP73-TP51"])
    choice = p.parse_args().result
    print(
        json.dumps(
            {
                "TP71": display,
                "Q26": throughput,
                "TP61-d": slope,
                "TP73-TP51": whole_author_competence,
            }[choice]()
        )
    )
