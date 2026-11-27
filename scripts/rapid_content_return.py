"""Join TP62's completed, nonoverlapping fits without running a predictor."""

import numpy as np
from rapid_cpu_dispatch import BLOCKS, ROOT, confirmed
from rapid_head_check import bound, read

FIRST = "3f48e3ff2698f1d106259c8496da5e012bd83aa25e8582ff46af57bb2ab0e637"
CODE = "8e26f964a48326dd07cae0acaee17a6aaa69e7c0fb0b904d3beef5f29af355ba"
ARMS = ("all", "withoutAssignedStem")


def collect():
    completion = read(ROOT / "cpu-queue/complete.json")["verified"]
    pins = {"TP62-first": FIRST, **{k: completion[k] for k in BLOCKS}}
    measured = {}
    design = read(ROOT / "TP62-first-a/design.json")
    for card, source in pins.items():
        folder = ROOT / (card + "-a")
        if confirmed(folder) != source:
            raise ValueError("Verified block differs: " + card)
        receipt = read(folder / "receipt.json")
        result = receipt["result"]
        if (receipt["card"], receipt["codePin"], receipt["status"]) != (
            card,
            CODE,
            "complete",
        ) or result["meta"] != design:
            raise ValueError("The design changed across blocks")
        files = result["files"]
        if len(files) != result["measuredSets"] or result["requiredSets"] != 401:
            raise ValueError("Incomplete control block")
        for name, digest in files.items():
            row = read(bound(folder / name, digest))
            key = row["family"], row["index"]
            if key in measured or name != f"{key[0]}-{key[1]:03d}.json":
                raise ValueError("Missing or duplicate fit identity")
            if set(row["rows"]) != set(ARMS):
                raise ValueError("Incomplete fit")
            measured[key] = row["rows"]
    expected = {("trained", 0)} | {(k, i) for k in ("iso", "rot") for i in range(200)}
    if measured.keys() != expected:
        raise ValueError("Both complete 200-set families are required")
    return pins, design, measured


def comparison(values, trained, direction):
    values = np.asarray(values, dtype=float)
    if (
        not np.isfinite(trained)
        or not np.isfinite(values).all()
        or values.shape != (200,)
    ):
        raise ValueError(
            "A comparison needs 200 finite measurements and the trained value"
        )
    less, ties = int(np.sum(values < trained)), int(np.sum(values == trained))
    tail = len(values) - less if direction == "greater" else less + ties
    low, median, high = np.percentile(values, [2.5, 50, 97.5])
    return {
        "sets": len(values),
        "low": float(low),
        "median": float(median),
        "high": float(high),
        "trainedPercentile": 100 * (less + 0.5 * ties) / len(values),
        "tied": ties,
        "tailCountIncludingTies": tail,
        "orientationP": (tail + 1) / (len(values) + 1),
        "position": "above"
        if trained > high
        else "below"
        if trained < low
        else "inside",
    }


def prepare():
    pins, design, measured = collect()
    trained = measured["trained", 0]
    rows = {}
    for population in ARMS:
        reference = trained[population]
        row = {}
        for key, direction in (("wordAccuracy", "greater"), ("writerAccuracy", "less")):
            families = {}
            for k in ("iso", "rot"):
                fits = [measured[k, i][population] for i in range(200)]
                for fit in [reference, *fits]:
                    for fixed in ("wordFoldRows", "writerCandidates", "writerTexts"):
                        if fit[fixed] != reference[fixed]:
                            raise ValueError("A null fit used a different cohort")
                    if not np.isclose(
                        fit["wordAccuracy"], np.mean(fit["wordFoldAccuracy"])
                    ) or (
                        fit["writerAccuracy"] != fit["writerHits"] / fit["writerTexts"]
                    ):
                        raise ValueError(
                            "Saved aggregate contradicts its component counts"
                        )
                families[k] = comparison(
                    [f[key] for f in fits], reference[key], direction
                )
            row[key] = {"trained": reference[key], **families}
        rows[population] = {
            "rows": row,
            "wordAboveRotBand": row["wordAccuracy"]["rot"]["position"] == "above",
            "writerBelowRotMedian": reference["writerAccuracy"]
            < row["writerAccuracy"]["rot"]["median"],
            "jointOrientationP": max(x["rot"]["orientationP"] for x in row.values()),
        }
    return {
        "blockReceipts": pins,
        "design": design,
        "trained": trained,
        "comparison": rows,
        "randomization": "One-sided ranks against 200 independent seeded orientations, with ties included and the observed orientation added. The joint p is the largest component p. The analyst prediction includes both text populations.",
        "uncertainty": "Bands describe variation across control sets on the fixed texts. The saved fits retained fold accuracies and total writer hits. Writer-cluster sampling intervals and their one-standard-error boundary check are unavailable.",
    }
