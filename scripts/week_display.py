"""Writer-disjoint word leaders and agreed sentence contrasts from the verified ten-output job."""

import json
from pathlib import Path

import numpy as np
from cb_inputs import digest, pin
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.person_halves import resamples, summary
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28, saved
from tompathy_engine.eval.readers.tp40 import MANIFEST, load_labels, verified_job
from tompathy_engine.eval.readers.word_panels import pinned
from tompathy_engine.packs.trigger import TAGS
from week_pride_inputs import FROZEN, SOURCE

WEEK = Path(".local/week-20261122")
PT = Path(".local/person-teacher")
STANDING = {"content", "faithful", "nostalgic", "sentimental", "trusting"}
NAMES = [*CHANNELS, "PRIDE"]


def sources():
    audit = json.loads((WEEK / "Q21-transfer.json").read_bytes())
    src = Path(audit["mirror"])
    if (
        not audit["nativeExited"]
        or not audit["priorFlockReleased"]
        or pin(src / "receipt.json") != audit["sourceReceiptPin"]
    ):
        raise ValueError("Verified ten-output source required")
    return src, audit


def word_levels(out, check):
    src, audit = sources()
    frame, ident = ed_situations(".local/readers/data/empathetic-dialogues")
    old = Path(".local/nine-channel/tp28-a")
    r = pinned(old / "receipt.json", TP28)
    if (
        ident != r["sources"]["ed"]["identity"]
        or r["protocol"]["tags"] != list(TAGS)
        or pin(src / "ed-ten.npz") != audit["files"]["ed-ten.npz"]
    ):
        raise ValueError("Forecast binding differs")
    path = saved(old, "ed/scores.npz", r)
    verify_order(path, frame.id)
    with np.load(path) as f, np.load(src / "ed-ten.npz") as d:
        tags = f["scores"].astype(float)
        channels = d["ten"]
    old_channels = pinned(FROZEN / "receipt.json", SOURCE)
    with np.load(saved(FROZEN, "ed-profile-forecasts.npz", old_channels)) as ref:
        if (
            not np.array_equal(ref["ids"], frame.id)
            or not np.array_equal(channels[:, :9], ref["probabilities"])
            or tags.shape != (len(frame), len(TAGS))
            or channels.shape != (len(frame), 10)
            or not np.isfinite(tags).all()
            or not np.isfinite(channels).all()
        ):
            raise ValueError("Incomplete or misaligned tag and channel readings")
    words, word = np.unique(frame.label, return_inverse=True)
    people, w = np.unique(frame.writer, return_inverse=True)
    order = sorted(range(len(people)), key=lambda j: digest("TP50:writer:" + people[j]))
    side = np.zeros(len(people), int)
    side[order[1::2]] = 1
    matrices = [tags, channels]
    # Sufficient statistics let each resample redo the training-side scaling and leader selection.
    stats = []
    counts = np.zeros((len(people), len(words)))
    np.add.at(counts, (w, word), 1)
    for v in matrices:
        sums = np.zeros((*counts.shape, v.shape[1]))
        sq = np.zeros((len(people), v.shape[1]))
        np.add.at(sums, (w, word), v)
        np.add.at(sq, w, v**2)
        stats.append((sums, sq))
    weights = np.vstack((np.ones(len(people)), resamples(len(people))))
    table = []
    leaders = {}
    for chunk in np.array_split(weights, 80):
        check()
        result = np.zeros((len(chunk), len(words), 2))
        for fold in (0, 1):
            mask = side == fold
            train_n = chunk[:, mask] @ counts[mask]
            test_n = chunk[:, ~mask] @ counts[~mask]
            for col, (sums, sq) in enumerate(stats):
                tr, te = [
                    (chunk[:, m] @ sums[m].reshape(m.sum(), -1)).reshape(
                        len(chunk), len(words), -1
                    )
                    for m in (mask, ~mask)
                ]
                n = train_n.sum(1)[:, None]
                avg = tr.sum(1) / n
                sd = np.sqrt(np.maximum(0, (chunk[:, mask] @ sq[mask]) / n - avg**2))
                sd[:, np.ptp(matrices[col], axis=0) == 0] = 0
                with np.errstate(invalid="ignore", divide="ignore"):
                    z = (tr / train_n[:, :, None] - avg[:, None, :]) / sd[:, None, :]
                    pred = (te / test_n[:, :, None] - avg[:, None, :]) / sd[:, None, :]
                # Constant heads cannot lead. A missing word leaves that draw undefined.
                best = np.where(np.isfinite(z), z, -np.inf).argmax(axis=2)
                val = np.take_along_axis(pred, best[:, :, None], axis=2)[:, :, 0]
                val[~np.isfinite(z).any(2)] = np.nan
                result[:, :, col] += val / 2
                if not table:
                    names = TAGS if col == 0 else NAMES
                    leaders[f"{fold}/{col}"] = [names[j] for j in best[0]]
        table.extend(result)
    values = np.asarray(table)
    stand = np.isin(words, list(STANDING))
    dif = values[:, stand].mean(1) - values[:, ~stand].mean(1)
    series = [values[:, stand, 0].mean(1), dif[:, 1], dif[:, 1] - dif[:, 0]]
    rows = {
        name: summary(v[0], v[1:])
        for name, v in zip(
            ("standingTags", "channelDifference", "channelLessTagDifference"), series
        )
    }
    pass_all = all(
        row["interval"]
        and (row["interval"][0] > 0 if k == "standingTags" else row["interval"][1] < 0)
        for k, row in rows.items()
    )
    states = {}
    if pass_all:
        peaks = []
        for v in matrices:
            active = v.std(0) > 0
            z = ((v[:, active] - v[:, active].mean(0)) / v[:, active].std(0)).max(1)
            peaks.append(z > np.median(z))
        t, c = peaks
        for i, key in enumerate(words):
            states[key] = {
                label: float(val[word == i].mean())
                for label, val in [
                    ("bothLow", ~t & ~c),
                    ("needInBand", t & ~c),
                    ("bothHigh", t & c),
                    ("channelOnlyUnassigned", ~t & c),
                ]
            }
    return {
        "card": "TP50",
        "source": audit["sourceReceiptPin"],
        "writers": len(people),
        "words": words.tolist(),
        "chosen": leaders,
        "checks": rows,
        "proposed": pass_all,
        "states": states,
        "byWord": {
            k: [summary(v[0], v[1:]) for v in values[:, i].T]
            for i, k in enumerate(words)
        },
    }


def move_table(diff, check):
    """Bootstrap paired report differences and retain unavailable outputs as missing."""
    estimates = np.full((2001, len(NAMES)), np.nan)
    active = np.isfinite(diff).all(axis=0)
    if len(diff):
        estimates[0] = diff.mean(0)
        rng = np.random.default_rng(23)
        for start in range(1, len(estimates), 25):
            check()
            weights = rng.multinomial(
                len(diff), np.full(len(diff), 1 / len(diff)), size=25
            )
            estimates[start : start + 25] = weights @ diff / len(diff)
    j = NAMES.index("DISGUST")
    contrast = np.full(len(estimates), np.nan)
    if len(diff) and active[j]:
        contrast = estimates[:, j] - np.median(estimates[:, active], axis=1)
    outputs = {
        name: summary(v[0], v[1:]) for name, v in zip(NAMES, estimates.T, strict=True)
    }
    comparison = summary(contrast[0], contrast[1:])
    above = [
        name
        for name, row in outputs.items()
        if row["interval"] and row["interval"][0] > 0
    ]
    return {
        "outputs": outputs,
        "disgustMinusMedian": comparison,
        "positiveIntervals": above,
        "allTenPositive": len(above) == 10,
        "disgustLeast": bool(
            len(diff) and active.all() and estimates[0, j] == min(estimates[0])
        ),
        "disgustBelowMedian": bool(
            comparison["interval"] and comparison["interval"][1] < 0
        ),
    }


def moves(out, check):
    src, audit = sources()
    m = pinned(PT / "inputs/manifest.json", MANIFEST)
    rows = []
    for block in ("Q11", "Q12"):
        h = m["files"][block]
        items = pinned(PT / "inputs" / (block + ".json"), h)
        labels = [
            load_labels(j, block, r, items, h, verified_job(PT, j), check)
            for j, r in [(block, "B"), ("G4", "W")]
        ]
        arrays = []
        for i in range(0, len(items), 100):
            check()
            name = f"{block}-{i:07d}.npz"
            if pin(src / name) != audit["files"][name]:
                raise ValueError("Sentence output changed")
            with np.load(src / name) as f:
                values = f["ten"]
                if (
                    values.shape != (min(100, len(items) - i), 10)
                    or not np.isfinite(values).all()
                ):
                    raise ValueError("Missing or invalid sentence readings")
                arrays.append(values)
        for item, v, b, w in zip(items, np.concatenate(arrays), *labels, strict=True):
            status = (
                int(b["change"])
                if b is not None and w is not None and b["change"] == w["change"]
                else -1
            )
            rows.append(
                (item["source"], item["parent"], len(item["text"].split()), status, v)
            )
    grouped = {}
    pieces = {}
    for source in ("ed", "envent"):
        subset = [(p, n, s, v) for srcname, p, n, s, v in rows if srcname == source]
        parent, idx = np.unique([r[0] for r in subset], return_inverse=True)
        pos = np.arange(len(idx))
        lo = np.full(len(parent), len(idx))
        hi = np.full(len(parent), -1)
        np.minimum.at(lo, idx, pos)
        np.maximum.at(hi, idx, pos)
        design = np.column_stack(
            (np.ones(len(idx)), [r[1] for r in subset], pos == lo[idx], pos == hi[idx])
        )
        status = np.array([r[2] for r in subset])
        y = np.stack([r[3] for r in subset])
        sd = y.std(axis=0)
        active = sd > 0
        adj = y - design @ np.linalg.lstsq(design, y, rcond=None)[0]
        sides = [np.bincount(idx[status == s], minlength=len(parent)) for s in (0, 1)]
        keep = (sides[0] > 0) & (sides[1] > 0)
        for label, v in [("raw", y), ("adjusted", adj)]:
            means = []
            for s in (0, 1):
                total = np.zeros((len(parent), 10))
                np.add.at(total, idx[status == s], v[status == s])
                means.append(total[keep] / sides[s][keep, None])
            diff = np.full(means[0].shape, np.nan)
            diff[:, active] = (means[1][:, active] - means[0][:, active]) / sd[active]
            pieces[source, label] = diff
        grouped[source] = {"reports": int(keep.sum()), "sentences": len(idx)}
    tables = {}
    for source in ("ed", "envent", "pooled"):
        tables[source] = {}
        for label in ("raw", "adjusted"):
            diff = (
                np.concatenate([pieces[s, label] for s in grouped])
                if source == "pooled"
                else pieces[source, label]
            )
            tables[source][label] = move_table(diff, check)
    return {
        "card": "TP49",
        "source": audit["sourceReceiptPin"],
        "coverage": grouped,
        "tables": tables,
    }
