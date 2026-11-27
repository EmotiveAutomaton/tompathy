"""TP67's prospectively specified units for the analyst's one-fifth-SD prediction.

Use the population SD of PRIDE across the two eligible groups within each
word. Re-estimate that scale on the same whole-writer draw as the raw contrast.
"""

import numpy as np
from rapid_blend import estimate
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, read
from rapid_word_contrasts import draws, grouped_mean, ratios
from word_table_lane import write


def scaled(values, writers, left, right, weight):
    use = left | right
    people = np.unique(writers[use])
    difference = grouped_mean(values, writers, left, people, weight) - grouped_mean(
        values, writers, right, people, weight
    )
    code = np.searchsorted(people, writers[use])
    n = weight @ np.bincount(code)
    # Center once before computing the second moment to preserve small variances.
    centered = values[use] - values[use].mean()
    mean = ratios(weight @ np.bincount(code, weights=centered), n)
    second = ratios(weight @ np.bincount(code, weights=centered**2), n)
    sd = np.sqrt(np.maximum(second - mean**2, 0))
    return difference, sd, ratios(difference, sd)


def prepare(out, check):
    original = ROOT / "TP67-original-a"
    bridge = ROOT / "TP69-a"
    h = confirmed(original)
    original_table = read(original / "receipt.json")["result"]
    if original_table["sourceReceiptPin"] != confirmed(bridge):
        raise ValueError("The original split and the saved forecast source differ")
    h_bridge = read(bridge / "receipt.json")["result"]["futureJoinPin"]
    with np.load(
        bound(bridge / "pride-responsibility.npz", h_bridge), allow_pickle=False
    ) as z:
        values, words, writers, own, other = [
            z[k] for k in ("pride", "word", "writer", "own", "other")
        ]
    valid = np.isfinite(own) & np.isfinite(other)
    results = {}
    for name, row in original_table["reports"].items():
        check()
        selected = (words == name) & valid
        left = selected & (own > other)
        right = selected & (own < other)
        if (int(left.sum()), int(right.sum())) != (row["own"], row["other"]):
            raise ValueError("Saved group counts differ")
        if min(row["own"], row["other"]) < 50:
            results[name] = {"reason": row["reason"]}
            continue
        weight = draws(len(np.unique(writers[left | right])))
        raw, sd, effect = scaled(values, writers, left, right, weight)
        if not np.allclose(
            raw[0], row["difference"]["value"], rtol=0, atol=1e-10
        ) or not np.allclose(
            estimate(raw)["interval"], row["difference"]["interval"], rtol=0, atol=1e-10
        ):
            raise ValueError("The scale uses a different raw contrast or writer draw")
        if not np.isfinite(effect[0]):
            results[name] = {
                "reason": "PRIDE has zero within-word variance on the eligible reports."
            }
            continue
        results[name] = {
            "withinWordSD": float(sd[0]),
            "ownMinusOtherInSD": estimate(effect),
            "distanceBelowOneFifth": estimate(0.2 - effect),
        }
    result = {
        "card": "TP67-scale",
        "inputReceiptPin": h,
        "words": results,
        "draws": 2000,
        "scale": "PRIDE standard deviation among eligible own and other reports within each word, recomputed in each whole-writer draw.",
    }
    write(out / "table.json", result)
    return result
