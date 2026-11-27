"""TP59 engine return: descriptive word profiles in each original source."""
import json
from pathlib import Path

import numpy as np

from cb_inputs import pin
from tompathy_engine.eval.readers.tp28 import finite_list, profiles

INPUT = Path(".local/week-20261122/TP59-inputs-b")
RECEIPT = "3363ef0882b8fa35f4a28fd9000fe439eea61aa778c56bd5fed02169e78831ce"


def prepare(out, check):
    if pin(INPUT / "receipt.json") != RECEIPT:
        raise ValueError("TP59 input receipt changed")
    inputs = json.loads((INPUT / "receipt.json").read_bytes())
    result = {}
    for source, info in inputs["sources"].items():
        check()
        path = INPUT / (source + ".npz")
        if pin(path) != info["filePin"]:
            raise ValueError("Aligned TP59 inputs changed")
        with np.load(path, allow_pickle=False) as data:
            words, scores, truth = data["words"].tolist(), data["scores"], data["truth"]
        if scores.shape != (info["matched"], len(inputs["columns"])) or truth.shape != (len(scores), len(words)):
            raise ValueError("Expected aligned label and output matrices")
        means, lifts, intervals, draws = profiles(scores, truth, check=check)
        result[source] = {
            "units": len(scores),
            "labels": {
                word: dict(n=int(truth[:, i].sum()), mean=finite_list(means[i]),
                           lift=finite_list(lifts[i]), interval=[finite_list(pair) for pair in intervals[i]],
                           finiteDraws=draws[i].tolist())
                for i, word in enumerate(words)
            },
        }
    return dict(card="TP59", inputReceiptPin=RECEIPT, columns=inputs["columns"], sources=result,
                method="TP28 within-source labeled-minus-other mean divided by source SD. "
                       "95% percentile interval from 2,000 unit resamples, seed 23. "
                       "A multi-label comment contributes once per applicable label. "
                       "Human ratings are separate. Pooling belongs to theory.")
