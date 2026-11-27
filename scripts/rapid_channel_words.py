"""TP64. Source-specific label discrimination from the fixed ten outputs."""

import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd
from rapid_head_check import bound, pin, read
from tompathy_engine.eval.readers.affect_data import ed_situations, go_comments
from tompathy_engine.eval.readers.person_halves import hashed, summary
from tompathy_engine.eval.readers.tp28 import MAP, SECONDARY
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp39 import saved
from week_pride_inputs import FROZEN, SOURCE
from week_word_profiles import INPUT, RECEIPT
from word_table_lane import write

DATA = Path(".local/readers/data")
OUTPUTS = tuple(CHANNELS) + ("PRIDE",)
DISPLAY = {"PANIC/GRIEF": "SADNESS", "LUST": "wanting", "PLAY": "amusement"}
FIXED = {
    ("go", "LUST"): ("optimism", "excitement"),
    ("ed", "PRIDE"): ("joyful", "excited"),
}


def labels(channel, source, words):
    own = (
        {w for w in ("proud", "pride") if w in words}
        if channel == "PRIDE"
        else set(MAP[channel][source])
        | {w for w, k in SECONDARY.get(source, {}).items() if k == channel}
    )
    return [i for i, w in enumerate(words) if w in own]


def auc(labels, scores, owners):
    """Bootstrap tied-score concordance with complete writers as sampling units."""
    truth = np.asarray(labels, dtype=bool)
    scores = np.asarray(scores, dtype=float)
    if (
        scores.shape != truth.shape
        or not np.isfinite(scores).all()
        or len(owners) != len(truth)
    ):
        raise ValueError("AUC needs one finite score and one writer per labeled text")
    n = int(truth.sum())
    unique, inverse = np.unique(owners, return_inverse=True)
    result = {"positive": n, "negative": len(truth) - n, "writers": len(unique)}
    if n == 0 or n == len(truth) or len(unique) < 2:
        return {**result, "value": None, "interval": None, "validDraws": 0}
    order = np.argsort(scores, kind="stable")
    y = truth[order]
    keys = inverse[order]
    starts = np.r_[0, 1 + np.flatnonzero(np.diff(scores[order]) != 0)]
    rng = np.random.default_rng(23)

    def calculate(weights):
        w = weights[:, keys]
        a = np.add.reduceat(w * y, starts, axis=1)
        b = np.add.reduceat(w * ~y, starts, axis=1)
        denom = a.sum(1) * b.sum(1)
        numer = (a * (np.cumsum(b, axis=1) - 0.5 * b)).sum(1)
        return np.divide(numer, denom, out=np.full(len(w), np.nan), where=denom > 0)

    point = calculate(np.ones((1, len(unique)), dtype=float))[0]
    boot = np.concatenate(
        [
            calculate(
                rng.multinomial(
                    len(unique), np.full(len(unique), 1 / len(unique)), size=32
                )
            )
            for _ in range(63)
        ]
    )[:2000]
    valid = boot[np.isfinite(boot)]
    stats = {**result, **summary(point, valid)}
    if len(valid) > 1:
        se = float(valid.std(ddof=1))
        lo, hi = stats["interval"]
        stats["standardError"] = se
        stats["nearPoint70"] = min(abs(lo - 0.7), abs(hi - 0.7)) <= se
        stats["intervalClearsPoint70"] = lo > 0.7
        stats["intervalBelowPoint70"] = hi < 0.7
        stats["pAbovePoint70"] = (
            1 + int(np.count_nonzero(valid - point >= point - 0.7))
        ) / (len(valid) + 1)
        stats["pBelowPoint70"] = (
            1 + int(np.count_nonzero(valid - point <= point - 0.7))
        ) / (len(valid) + 1)
    return stats


def sources(name):
    cfg = read(bound(INPUT / "receipt.json", RECEIPT))
    meta = cfg["sources"][name]
    with np.load(
        bound(INPUT / (name + ".npz"), meta["filePin"]), allow_pickle=False
    ) as f:
        keys = f["ids"].astype(str)
        scores = f["scores"][:, :10]
        truth = f["truth"].astype(bool)
        words = f["words"].astype(str).tolist()
    orig = read(bound(FROZEN / "receipt.json", SOURCE))
    if name == "ed":
        frame, intake = ed_situations(DATA / "empathetic-dialogues")
        if intake != orig["sources"]["ed"]:
            raise ValueError("Chat intake differs")
    elif name == "go":
        frame, _, _, info = go_comments(DATA / "go-emotions")
        if info["intakePin"] != orig["sources"]["go"]["intakePin"]:
            raise ValueError("Forum intake differs")
    else:
        path = DATA / "crowd-enVent2023/corpus/crowd-enVent_generation.tsv"
        bound(path, orig["sources"]["envent"]["files"]["generation"])
        frame = pd.read_csv(
            path,
            sep="\t",
            quoting=csv.QUOTE_NONE,
            dtype=str,
            keep_default_na=False,
            usecols=["text_id", "prolific_id", "hidden_emo_text"],
        ).rename(
            columns={
                "text_id": "id",
                "prolific_id": "writer",
                "hidden_emo_text": "text",
            }
        )
    frame = frame.set_index("id", verify_integrity=True).loc[keys]
    writers = frame.writer.to_numpy(str)
    texts = frame.text.to_numpy(str)
    keep = np.ones(len(keys), dtype=bool)
    new_writer = keep.copy()
    exclusions = {
        "tenSourceRows": meta["tenUnits"],
        "withReleasedLabels": len(keys),
        "fitReports": 0,
        "unknownWriter": 0,
    }
    if name == "envent":
        with np.load(
            saved(FROZEN, "envent-targets.npz", orig), allow_pickle=False
        ) as f:
            if not np.array_equal(f["ids"].astype(str), keys):
                raise ValueError("Event fit membership differs")
            train = f["train"].astype(bool)
        if train.sum() != 1199:
            raise ValueError("Different PRIDE fit")
        keep &= ~train
        new_writer = ~np.isin(writers, writers[train])
        exclusions["fitReports"] = int(train.sum())
    elif name == "go":
        keep &= frame.writer_known.to_numpy(bool)
        exclusions["unknownWriter"] = int((~keep).sum())
    if (
        not np.isfinite(scores).all()
        or cfg["columns"][:10] != list(OUTPUTS)
        or len(set(keys)) != len(keys)
        or (writers[keep] == "").any()
    ):
        raise ValueError("Incomplete source alignment")
    return (
        keys[keep],
        writers[keep],
        texts[keep],
        truth[keep],
        scores[keep],
        words,
        new_writer[keep],
        exclusions,
    )


def contrast(scores, own, other, keep, literal, avoid, writers, check):
    # Exclude comments bearing both labels in a binary comparison.
    selected = keep & (own ^ other)
    measures = {}
    for key, mask in [
        ("all", selected),
        ("withoutWord", selected & ~((own & literal) | (other & avoid))),
    ]:
        check()
        measures[key] = auc(own[mask], scores[mask], writers[mask])
    return measures


def head_table(source, writers, texts, truth, scores, words, new_writer, check):
    order = sorted(set(writers), key=lambda k: hashed("TP64:neighbor:23:", k))
    choose = np.isin(writers, order[: len(order) // 2])
    matches = [
        re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.IGNORECASE)
        for word in words
    ]
    literal = np.array([[q.search(str(t)) is not None for q in matches] for t in texts])
    table = {}
    for j, channel in enumerate(OUTPUTS):
        check()
        ind = labels(channel, source, words)
        entry = {"ownLabels": [words[k] for k in ind]}
        table[DISPLAY.get(channel, channel)] = entry
        if not ind:
            entry["unavailable"] = "No registered own word in this source."
            continue
        # Some event writers contributed different reports to the original PRIDE fit.
        permitted = (
            new_writer
            if source == "envent" and channel == "PRIDE"
            else np.ones(len(choose), bool)
        )
        own = truth[:, ind].any(1)
        mentions = (truth[:, ind] & literal[:, ind]).any(1)
        means = {}
        for k, word in enumerate(words):
            mask = choose & permitted & ~own & truth[:, k]
            if k not in ind and mask.any():
                means[word] = float(scores[mask, j].mean())
        picked = sorted(means, key=lambda word: (-means[word], word))[:2]
        entry["selectedNeighbors"] = picked
        entry["availableWriters"] = len(set(writers[permitted]))
        for kind, neighbors, keep in [
            ("fixed", FIXED.get((source, channel), ()), permitted),
            ("selected", picked, permitted & ~choose),
        ]:
            entry[kind] = {}
            if not neighbors:
                entry[kind + "Unavailable"] = (
                    "No pair specified or selectable for this source and output."
                )
            for word in neighbors:
                if word not in words:
                    continue
                k = words.index(word)
                entry[kind][word] = contrast(
                    scores[:, j],
                    own,
                    truth[:, k],
                    keep,
                    mentions,
                    literal[:, k],
                    writers,
                    check,
                )
    return table


def shame(source, keys, writers, truth, words, new_writer, check):
    orig = read(bound(FROZEN / "receipt.json", SOURCE))
    with np.load(
        saved(FROZEN, "go_plus_envent-profile-head.npz", orig), allow_pickle=False
    ) as head:
        active = head["active"]
        pos = np.flatnonzero(active == CHANNELS.index("SHAME"))
        if len(pos) != 1:
            raise ValueError("The joint head does not carry SHAME")
        theta = head["parameters"][:, pos[0]]
    with np.load(saved(FROZEN, source + "-targets.npz", orig), allow_pickle=False) as f:
        ids = f["ids"].astype(str)
        train = f["train"].astype(bool)
        if source == "go":
            unseen = f["test"] & ~train
        else:
            unseen = ~train
    held = ids[unseen]
    index = pd.Index(held).get_indexer(keys)
    if (index < 0).any() or len(held) != {"go": 11571, "envent": 5401}[source]:
        raise ValueError("A fitted report entered the SHAME rescore")
    from scipy.special import expit

    with np.load(saved(FROZEN, "vectors.npz", orig), allow_pickle=False) as data:
        values = expit(data[source][unseen].astype(float) @ theta[:-1] + theta[-1])
    check()
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite joint SHAME forecasts")
    ans = {
        "rows": len(values),
        "withLabelsAndWriter": len(keys),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "median": float(np.median(values)),
        "varying": bool(np.ptp(values) > 0),
    }
    positive = [i for i, w in enumerate(words) if w in ("shame", "guilt")]
    if positive:
        y = truth[:, positive].any(1)
        ans["reportHeldOut"] = auc(y, values[index], writers)
        ans["writerHeldOut"] = auc(
            y[new_writer], values[index][new_writer], writers[new_writer]
        )
    else:
        ans["unavailable"] = (
            "The released forum vocabulary has no shame or guilt gold label."
        )
    return ans


def readings(table):
    def assess(values, direction):
        if not values or any(v.get("standardError") is None for v in values):
            return {
                "comparisons": len(values),
                "verdict": "Unresolved: missing labeled evidence.",
            }
        test = (
            "intervalBelowPoint70" if direction == "below" else "intervalClearsPoint70"
        )
        p = "pBelowPoint70" if direction == "below" else "pAbovePoint70"
        opposite = (
            "intervalClearsPoint70" if direction == "below" else "intervalBelowPoint70"
        )
        near = any(v["nearPoint70"] for v in values)
        if near:
            verdict = "Unresolved under the one-standard-error rule."
        elif all(v[test] for v in values):
            verdict = (
                "All observed intervals clear the bar in the registered direction."
            )
        elif any(v[opposite] for v in values):
            verdict = (
                "At least one observed interval is clear in the opposite direction."
            )
        else:
            verdict = "Unresolved at the registered bar."
        return {
            "comparisons": len(values),
            "jointP": max(v[p] for v in values),
            "nearBar": near,
            "verdict": verdict,
        }

    want = table["go"]["heads"]["wanting"]["fixed"]
    results = {
        "forumWanting": {
            k: assess([want[w][k] for w in ("optimism", "excitement")], "below")
            for k in ("all", "withoutWord")
        },
        "playOutsideForumAmusement": {
            "verdict": "Unresolved. Other source vocabularies lack a registered PLAY word and no equivalence margin was specified."
        },
    }
    for channel in ("SEEKING", "RAGE", "FEAR", "SADNESS", "DISGUST", "PRIDE"):
        arm = {}
        for src, r in table.items():
            selected = r["heads"][channel].get("selected", {})
            if len(selected) == 2:
                arm[src] = {
                    k: assess([v[k] for v in selected.values()], "above")
                    for k in ("all", "withoutWord")
                }
        results[channel] = arm
    return results


def prepare(out, check):
    filename = Path("engine/validation/readers-tp59-2026-11.json")
    profiles = read(filename)
    if profiles["inputReceiptPin"] != RECEIPT or profiles["card"] != "TP59":
        raise ValueError("The published profiles do not match the aligned inputs")
    original = read(bound(FROZEN / "receipt.json", SOURCE))
    table = {}
    for src in ("ed", "envent", "go"):
        keys, writers, texts, truth, scores, words, new, counts = sources(src)
        counts.update(assessedReports=len(keys), assessedWriters=len(set(writers)))
        answer = {
            "census": counts,
            "heads": head_table(src, writers, texts, truth, scores, words, new, check),
        }
        if src in ("envent", "go"):
            answer["jointShame"] = shame(src, keys, writers, truth, words, new, check)
        # Use the maximum mean among the ten named outputs of each published TP59 label.
        rows = profiles["sources"][src]["labels"]
        peak = {k: max(v["mean"][:10]) for k, v in rows.items()}
        order = sorted(peak, key=lambda k: (peak[k], k))
        answer["tp59Loudest"] = [
            {"word": k, "peak": peak[k]} for k in reversed(order[-3:])
        ]
        answer["tp59Quietest"] = [{"word": k, "peak": peak[k]} for k in order[:3]]
        table[src] = answer
        write(out / (src + ".json"), answer)
    return {
        "card": "TP64",
        "inputReceiptPin": RECEIPT,
        "tp30ReceiptPin": SOURCE,
        "tp59Pin": pin(filename),
        "tp30GoTrainingRows": original["intake"]["go_train"],
        "sources": table,
        "readings": readings(table),
        "scope": "Within-source assigned labels. Model readings on forum desire describe wanting or wishing.",
    }
