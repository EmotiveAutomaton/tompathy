"""CI. Writer-held-out selection among three fixed change summaries after a Q14 ruling."""

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from cb_inputs import digest, pin
from tompathy_engine.eval.readers.person_halves import resamples, summary
from tompathy_engine.eval.readers.tp31_teacher import valid_label
from tompathy_engine.eval.readers.tp39 import SUPPORT
from tompathy_engine.eval.readers.tp40 import MANIFEST, load_labels, verified_job
from tompathy_engine.eval.readers.word_panels import pinned, read

MARKS = ["changeShare", "anyChange", "alreadyShare"]
TARGETS = ["suddenness", "event_duration", "emotion_duration"]
ROOT = Path(".local/person-teacher")


def rank_interval(x, y, person, check):
    """Weighted midranks with all ties recomputed inside each whole-writer draw."""
    good = np.isfinite(x) & np.isfinite(y)
    x, y, person = x[good], y[good], person[good]
    people, owner = np.unique(person, return_inverse=True)
    blank = {
        "value": None,
        "interval": None,
        "validDraws": 0,
        "reports": len(x),
        "writers": len(people),
    }
    if min(len(np.unique(x)), len(np.unique(y)), len(people)) < 2:
        return blank
    _, a = np.unique(x, return_inverse=True)
    _, b = np.unique(y, return_inverse=True)
    freq = np.zeros((len(people), a.max() + 1, b.max() + 1))
    np.add.at(freq, (owner, a, b), 1)
    result = []
    for w in np.array_split(
        np.vstack((np.ones(len(people)), resamples(len(people)))), 40
    ):
        check()
        t = (w @ freq.reshape(len(people), -1)).reshape(len(w), *freq.shape[1:])
        n = t.sum(axis=(1, 2))
        a, b = t.sum(2), t.sum(1)
        u = a.cumsum(1) - (a + n[:, None]) / 2
        v = b.cumsum(1) - (b + n[:, None]) / 2
        with np.errstate(invalid="ignore", divide="ignore"):
            result.extend(
                (t * u[:, :, None] * v[:, None, :]).sum((1, 2))
                / np.sqrt((a * u * u).sum(1) * (b * v * v).sum(1))
            )
    return dict(
        summary(result[0], np.array(result[1:])), reports=len(x), writers=len(people)
    )


def prepare(out, check):
    q14 = read(ROOT / "Q14-transfer-a.json")
    folder = Path(q14["mirror"])
    r = pinned(folder / "receipt.json", q14["sourceReceiptPin"])
    public = read(Path("engine/validation/readers-q14-bs-2026-11.json"))
    if (
        r["status"] != "complete"
        or not q14["nativeExited"]
        or not q14["priorFlockReleased"]
        or public["sourceReceiptPin"] != q14["sourceReceiptPin"]
        or r["attempt"] != 3
    ):
        raise ValueError("A verified scientific Q14 decision is required")
    decision = pinned(folder / "decision.json", r["decisionPin"])["passes"]
    if type(decision) is not bool:
        raise ValueError("Invalid Q14 verdict")
    inventory = pinned(ROOT / "Q14-transfer-a-pins.json", q14["inventoryPin"])
    manifest = pinned(ROOT / "inputs/manifest.json", MANIFEST)
    meta = pinned(
        ROOT / "private-parents.json",
        pinned(ROOT / "tp39-support.json", SUPPORT)["parentsPin"],
    )
    parents = {p: (str(i), str(w)) for p, s, i, w, _, _ in meta if s == "envent"}
    labels = {role: defaultdict(list) for role in ("B", "C", "W")}
    for job in ("Q11", "Q12"):
        h = manifest["files"][job]
        items = pinned(ROOT / "inputs" / (job + ".json"), h)
        for role in ("B", "W"):
            source = job if role == "B" else "G4"
            vals = load_labels(
                source, job, role, items, h, verified_job(ROOT, source), check
            )
            for row, value in zip(items, vals, strict=True):
                if row["source"] == "envent":
                    labels[role][row["parent"]].append(value)
        if job == "Q11":
            binding = r["summary"]["binding"]
            if (
                binding["inputPin"] != h
                or binding["role"] != "C"
                or binding["modelPin"]
                != "8b9d11d807c57feb1e2ecb0d6cbf40334c37dcc3523bed5540af4f927f112a37"
            ):
                raise ValueError("Reader C binding differs")
            for i, item in enumerate(items):
                if item["source"] != "envent":
                    continue
                name = f"C/row-{i:06d}.json"
                row = pinned(folder / name, inventory[name])
                if (
                    row["id"] != item["id"]
                    or row["index"] != i
                    or row["binding"] != binding
                ):
                    raise ValueError("Reader C row mismatch")
                value = row["values"]
                if value is not None and valid_label(value) != value:
                    raise ValueError("Invalid stored reader C marks")
                labels["C"][item["parent"]].append(value)
    file = Path(
        ".local/readers/data/crowd-enVent2023/corpus/crowd-enVent_generation.tsv"
    )
    if pin(file) != manifest["sourcePins"]["envent"]:
        raise ValueError("Writer ratings differ")
    data = pd.read_csv(
        file,
        sep="\t",
        quoting=3,
        dtype=str,
        usecols=["text_id", "prolific_id", *TARGETS],
    ).set_index("text_id")
    duration = {
        "I had none": 0,
        "seconds": 1,
        "minutes": 2,
        "hours": 3,
        "days": 4,
        "weeks": 5,
    }
    for col in TARGETS[1:]:
        if set(data[col].dropna()) - duration.keys():
            raise ValueError("Unknown duration category")
        data[col] = data[col].map(duration)
    data = data.loc[[i for i, w in parents.values()]]
    writers = data.prolific_id.to_numpy(str)
    if writers.tolist() != [w for i, w in parents.values()]:
        raise ValueError("Writer join differs")
    order = sorted(set(writers), key=lambda w: digest("TP53:writer:" + w))
    dev = np.isin(writers, order[::2])
    ratings = data[TARGETS].to_numpy(float)
    tables = {}
    scores = {}
    gates = {}
    for role, reader_marks in labels.items():
        v = np.full((len(data), 3), np.nan)
        for i, p in enumerate(parents):
            s = reader_marks.get(p)
            if s and all(row is not None for row in s):
                changed = [row["change"] for row in s]
                v[i] = (
                    np.mean(changed),
                    any(changed),
                    np.mean([row["when"] == "already" for row in s]),
                )
        scores[role] = v
        tables[role] = {
            m: {
                k: rank_interval(v[:, j], ratings[:, t], writers, check)
                for t, k in enumerate(TARGETS)
            }
            for j, m in enumerate(MARKS)
        }
        candidates = [
            rank_interval(v[dev, j], ratings[dev, 0], writers[dev], check)["value"]
            for j in range(3)
        ]
        selected = max(
            (j for j, c in enumerate(candidates) if c is not None),
            key=lambda j: candidates[j],
            default=None,
        )
        test = (
            rank_interval(v[~dev, selected], ratings[~dev, 0], writers[~dev], check)
            if selected is not None
            else None
        )
        passed = bool(
            test
            and test["value"] is not None
            and test["value"] >= 0.26
            and test["interval"]
            and test["interval"][0] > 0
        )
        gates[role] = {
            "selection": candidates,
            "chosen": MARKS[selected] if selected is not None else None,
            "heldOut": test,
            "qualified": bool(not decision and role != "W" and passed),
        }
    agreement = {
        a + "-" + b: {
            m: rank_interval(scores[a][:, j], scores[b][:, j], writers, check)
            for j, m in enumerate(MARKS)
        }
        for a, b in [("B", "C"), ("B", "W"), ("C", "W")]
    }
    return {
        "card": "TP53",
        "q14Source": q14["sourceReceiptPin"],
        "q14Passed": decision,
        "descriptionOnly": decision,
        "attempt": None if decision else 4,
        "writerCriterion": 0.26,
        "humanSuddenness": 0.525,
        "roles": gates,
        "tables": tables,
        "agreement": agreement,
        "source": pin(file),
        "noProductionAdmission": True,
    }
