"""TP66 short arm. Compare within-text output order at the same exact sentence counts."""

import numpy as np
from rapid_blend import estimate
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, read
from rapid_word_contrasts import draws, ratios
from tompathy_engine.eval.readers.tp30 import CHANNELS
from word_table_lane import write

WORDS = {"ed": ("sad", "devastated", "lonely", "disappointed"), "envent": ("sadness",)}
COLUMNS = (
    "sadnessMinusFear",
    "sadnessMinusRage",
    "sadnessCentre",
    "fearCentre",
    "rageCentre",
    "fearEarlySadnessLate",
    "rageEarlySadnessLate",
)


def centres(scores, position):
    weights = scores - scores.min(1, keepdims=True)
    total = weights.sum(1)
    return np.divide(
        (weights * position[None, :, None]).sum(1),
        total,
        out=np.full_like(total, 0.5),
        where=total > 0,
    )


def peaks(scores, position):
    bins = np.where(position < 1 / 3, 0, np.where(position <= 2 / 3, 1, 2))
    by_third = np.stack(
        [
            scores[:, bins == k, :].mean(1)
            if np.any(bins == k)
            else np.full((len(scores), 3), -np.inf)
            for k in range(3)
        ],
        axis=1,
    )
    best = by_third.argmax(1)
    return np.column_stack(
        ((best[:, 1] == 0) & (best[:, 0] == 2), (best[:, 2] == 0) & (best[:, 0] == 2))
    )


def matched(strata, weights, check):
    n = weights.shape[1]
    losses = np.zeros((len(weights), len(COLUMNS)))
    controls = np.zeros_like(losses)
    sizes = np.zeros_like(losses)
    unpaired = []
    for length, (owners, loss, stats) in strata.items():
        check()
        if not loss.any() or loss.all():
            unpaired.append(
                {
                    "sentences": int(length),
                    "loss": int(loss.sum()),
                    "other": int((~loss).sum()),
                }
            )
            continue
        k = len(COLUMNS) if length >= 3 else 5
        n1 = weights @ np.bincount(owners[loss], minlength=n)
        n0 = weights @ np.bincount(owners[~loss], minlength=n)
        plus, minus = np.zeros((n, k)), np.zeros((n, k))
        np.add.at(plus, owners[loss], stats[loss, :k])
        np.add.at(minus, owners[~loss], stats[~loss, :k])
        losses[:, :k] += weights @ plus
        expected = ratios(weights @ minus, n0[:, None])
        controls[:, :k] += np.where(n1[:, None] == 0, 0, n1[:, None] * expected)
        sizes[:, :k] += n1[:, None]
    a, b = ratios(losses, sizes), ratios(controls, sizes)
    outputs = {}
    for j, name in enumerate(COLUMNS):
        if not np.isfinite(a[0, j]) or not np.isfinite(b[0, j]):
            outputs[name] = {"reason": "No matching lengths in both groups"}
            continue
        difference = estimate(a[:, j] - b[:, j])
        outputs[name] = {
            "loss": estimate(a[:, j]),
            "lengthMatchedOther": estimate(b[:, j]),
            "difference": difference,
            "matchedLossTexts": int(sizes[0, j]),
            "drawCoverage": difference["validDraws"] / (len(weights) - 1),
        }
    return outputs, unpaired


def source_table(p, ordinal, forecast, counts, words, writers, source, check):
    eligible = counts >= 2
    owners, person = np.unique(writers[eligible], return_inverse=True)
    positions = np.full(len(counts), -1, dtype=int)
    positions[eligible] = person
    losses = np.isin(words, WORDS[source])
    strata = {}
    shuffle_sum = np.zeros(100)
    shuffle_count = 0
    for length in np.unique(counts[eligible]):
        check()
        ids = np.flatnonzero(counts == length)
        mask = np.isin(p, ids)
        sorted_rows = np.flatnonzero(mask)[np.lexsort((ordinal[mask], p[mask]))]
        roster = p[sorted_rows].reshape(len(ids), length)
        if (
            not (roster == ids[:, None]).all()
            or not (
                ordinal[sorted_rows].reshape(roster.shape) == np.arange(length)
            ).all()
        ):
            raise ValueError("Sentence position or text ordering differs")
        scores = forecast[sorted_rows].reshape(len(ids), length, 3)
        pos = np.arange(length) / (length - 1)
        c = centres(scores, pos)
        values = np.column_stack(
            (c[:, 0] - c[:, 1], c[:, 0] - c[:, 2], c, peaks(scores, pos))
        )
        isloss = losses[ids]
        strata[length] = (positions[ids], isloss, values)
        if length >= 3 and isloss.any():
            v = scores[isloss]
            rng = np.random.default_rng([23, int(length), int(source == "envent")])
            ix = np.arange(len(v))[:, None]
            for b in range(100):
                if b % 25 == 0:
                    check()
                perm = np.argsort(rng.random((len(v), length)), axis=1)
                shuffle_sum[b] += peaks(v[ix, perm], pos)[:, 0].sum()
            shuffle_count += len(v)
    table, unpaired = matched(strata, draws(len(owners)), check)
    shuffled = shuffle_sum / shuffle_count if shuffle_count else None
    return {
        "writersWithEligibleTexts": len(owners),
        "comparisons": table,
        "unmatchedLengths": unpaired,
        "shuffle": {
            "draws": 100,
            "lossTexts": shuffle_count,
            "meanShare": float(shuffled.mean()) if shuffled is not None else None,
            "range": [float(shuffled.min()), float(shuffled.max())]
            if shuffled is not None
            else None,
        },
    }


def prepare(out, check):
    folder = ROOT / "TP65-inputs-a"
    h = confirmed(folder)
    r = read(folder / "receipt.json")["result"]
    with np.load(
        bound(folder / "aligned.npz", r["files"]["aligned.npz"]), allow_pickle=False
    ) as a:
        source, word, writer, counts = [
            a[k] for k in ("source", "word", "writer", "counts")
        ]
        census = {}
        for s, labels in WORDS.items():
            row = {}
            for key, group in (
                ("loss", np.isin(word, labels)),
                ("other", ~np.isin(word, labels)),
            ):
                row[key] = {}
                for name, cut in (
                    ("two", counts == 2),
                    ("three", counts == 3),
                    ("fourOrMore", counts >= 4),
                ):
                    chosen = (source == s) & group & cut
                    row[key][name] = {
                        "texts": int(chosen.sum()),
                        "writers": len(np.unique(writer[chosen])),
                    }
            census[s] = row
        write(out / "census.json", census)
        check()
        parent, ordinal = a["parents"], a["ordinal"]
        cols = [CHANNELS.index(k) for k in ("PANIC/GRIEF", "FEAR", "RAGE")]
        forecast = a["forecasts"][:, cols]
    result = {}
    for s in WORDS:
        ids = np.flatnonzero(source == s)
        select = source[parent] == s
        result[s] = source_table(
            np.searchsorted(ids, parent[select]),
            ordinal[select],
            forecast[select],
            counts[ids],
            word[ids],
            writer[ids],
            s,
            check,
        )
    ans = {
        "card": "TP66-short",
        "inputReceiptPin": h,
        "census": census,
        "sources": result,
        "wholeWriterDraws": 2000,
        "scope": "Short texts selected by assigned feeling. Sentence shuffles describe order.",
        "productionAdmission": False,
    }
    write(out / "table.json", ans)
    return ans
