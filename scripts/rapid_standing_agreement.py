"""Whole-writer agreement between B and W on the original standing protocol."""

import csv
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rapid_agreement import classification, kappas
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, pin, read
from rapid_inputs import key
from rapid_marks import CHOICES, digest, protocol, standing
from rapid_standing_return import REG
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.person_halves import summary
from tompathy_engine.eval.readers.tp39 import saved
from week_pride_inputs import FROZEN, SOURCE
from word_table_lane import write

SOURCES = ("ed", "envent", "go")


def authors(manifest):
    original = read(bound(FROZEN / "receipt.json", SOURCE))
    data = Path(".local/readers/data")
    ed, intake = ed_situations(data / "empathetic-dialogues")
    if intake["intakePin"] != manifest["edIntakePin"]:
        raise ValueError("Original chat writer roster differs")
    source = bound(
        data / "crowd-enVent2023/corpus/crowd-enVent_generation.tsv",
        manifest["generationPin"],
    )
    events = pd.read_csv(
        source,
        sep="\t",
        quoting=csv.QUOTE_NONE,
        dtype=str,
        keep_default_na=False,
        usecols=["text_id", "prolific_id"],
    )
    with np.load(
        saved(FROZEN, "go-targets.npz", original), allow_pickle=False
    ) as table:
        lookup = dict(
            zip(table["ids"].astype(str), table["authors"].astype(str), strict=True)
        )
        if len(lookup) != len(table["ids"]):
            raise ValueError("Duplicate forum post in the saved author roster")
    with np.load(
        saved(FROZEN, "go-profile-forecasts.npz", original), allow_pickle=False
    ) as table:
        held = table["ids"].astype(str)
    native = {
        "ed": zip(ed.id, ed.writer, strict=True),
        "envent": zip(events.text_id, events.prolific_id, strict=True),
        "go": [(post, lookup[post]) for post in held],
    }
    ids, persons, corpora = [], [], []
    unknown = 0
    for name in SOURCES:
        file = ROOT / "inputs" / (name + ".jsonl.gz")
        with gzip.open(
            bound(file, manifest["files"][file.name]), "rt", encoding="utf8"
        ) as f:
            count = 0
            for line, (native_id, author) in zip(f, native[name], strict=True):
                ident = key(name, native_id)
                if ident != json.loads(line)["id"] or not author:
                    raise ValueError("Source and submitted writer roster do not align")
                missing = name == "go" and author == "unknown-comment-" + native_id
                unknown += int(missing)
                ids.append(ident)
                persons.append(name + ":" + str(author))
                corpora.append(name)
                count += 1
            if count != manifest["counts"][name]:
                raise ValueError("Source count differs")
    if len(ids) != 43021 or len(set(ids)) != len(ids):
        raise ValueError("Shared standing input census differs")
    return ids, np.array(persons), np.array(corpora), unknown


def decode(row):
    try:
        value = (
            standing(json.loads(row["response"]))
            if row["response"] is not None
            else None
        )
    except (ValueError, TypeError):
        value = None
    if value != row["values"]:
        raise ValueError("Parsed values do not match the saved response")
    return [
        CHOICES[field].index(value[field]) if value is not None else -1
        for field in CHOICES
    ]


def marks(binding, role, cfg, ids, check):
    directory = Path(binding["mirror"])
    receipt = read(bound(directory / "receipt.json", binding["sourceReceiptPin"]))
    folder = directory / role
    arm = read(
        bound(folder / "complete.json", receipt["artifacts"][f"{role}/complete.json"])
    )
    settings = read(bound(folder / "protocol.json", arm["protocolPin"]))
    expected = cfg["prompts"]["standing"]
    if (
        receipt["result"] != arm
        or arm["rows"] != len(ids)
        or not binding["nativeExited"]
        or arm["inputPin"] != digest("\n".join(ids))
        or settings["inputPin"] != arm["inputPin"]
        or expected != protocol("standing")
        or any(settings[k] != v for k, v in expected.items())
        or [settings["model"], settings["modelPin"]] != cfg["readers"][role]
        or settings["think"] is not False
    ):
        raise ValueError("Reader or standing protocol does not match registration")
    width = settings["width"]
    if not isinstance(width, int) or width not in (1, 2, 4):
        raise ValueError("Unsupported standing batch width")
    result = np.full((len(ids), len(CHOICES)), -1, np.int8)
    for start in range(0, len(ids), width):
        if start % 200 == 0:
            check()
        file = folder / f"from-{start:06d}.json"
        batch = read(bound(file, receipt["artifacts"][f"{role}/{file.name}"]))
        if [row["id"] for row in batch] != ids[start : start + width]:
            raise ValueError("Reader rows do not match the shared input order")
        result[start : start + len(batch)] = [decode(row) for row in batch]
    if np.sum(result[:, 0] >= 0) != arm["valid"]:
        raise ValueError("Valid standing count differs")
    return result, arm["protocolPin"]


def table(a, b, persons, levels, check):
    people, groups = np.unique(persons, return_inverse=True)
    n = len(people)
    size = len(levels)
    ok = (a >= 0) & (b >= 0)
    cells = np.zeros((n, size, size), dtype=np.int64)
    np.add.at(cells, (groups[ok], a[ok], b[ok]), 1)
    total = cells.sum(axis=0)
    estimate = kappas(total[None])[0]
    samples = []
    rng = np.random.default_rng(23)
    if n >= 2:
        p = np.full(n, 1 / n)
        flat = cells.reshape(n, -1).astype(float)
        for _ in range(40):
            check()
            draw = rng.multinomial(n, p, size=50).astype(float) @ flat
            samples.extend(kappas(draw.reshape(50, size, size)))
    samples = np.asarray(samples)
    result = summary(estimate, samples)
    result.update(
        CW=classification(result["value"]),
        levels=levels,
        contingency=total.tolist(),
        roster=len(a),
        clusters=n,
        jointlyValid=int(ok.sum()),
        BOnly=int(((a >= 0) & (b < 0)).sum()),
        WOnly=int(((b >= 0) & (a < 0)).sum()),
        bothMissing=int(((a < 0) & (b < 0)).sum()),
    )
    valid = samples[np.isfinite(samples)]
    if len(valid):
        result["bootstrapSE"] = float(valid.std(ddof=1)) if len(valid) > 1 else None
        result["atOrAboveUsable"] = float((1 + (valid >= 0.6).sum()) / (1 + len(valid)))
        result["atOrBelowUsable"] = float((1 + (valid <= 0.6).sum()) / (1 + len(valid)))
        result["atOrBelowWeakFloor"] = float(
            (1 + (valid <= 0.4).sum()) / (1 + len(valid))
        )
    return result


def original_when_tail(check):
    # The first TP77 receipt has the interval. Recover its tail from the fixed
    # predictions only, for the previously incomplete joint TP78 prediction.
    base = ROOT / "TP77-original-a"
    source = confirmed(base)
    original = read(base / "receipt.json")["result"]
    path = ROOT / "TP65-inputs-a"
    if confirmed(path) != original["alignedReceiptPin"]:
        raise ValueError("Original timing forecast binding differs")
    manifest = read(path / "receipt.json")["result"]
    with np.load(
        bound(path / "aligned.npz", manifest["files"]["aligned.npz"]),
        allow_pickle=False,
    ) as data:
        parent = data["parents"]
        marks = data["marks"]
        owners = np.char.add(
            np.char.add(data["source"][parent], ":"), data["writer"][parent]
        )
    earlier = original["sources"]["all"]["B/W"]["when"]
    value = table(marks[:, 0, 0], marks[:, 1, 0], owners, earlier["levels"], check)
    if (
        value["contingency"] != earlier["table"]
        or value["jointlyValid"] != earlier["jointlyValid"]
        or abs(value["value"] - earlier["value"]) > 1e-12
        or not np.allclose(value["interval"], earlier["interval"], atol=1e-12, rtol=0)
    ):
        raise ValueError("Original timing classes, cohorts or resamples differ")
    return {
        "sourceReceiptPin": source,
        "value": value["value"],
        "interval": value["interval"],
        "atOrBelowUsable": value["atOrBelowUsable"],
        "bootstrapSE": value["bootstrapSE"],
    }


def prepare(out, check):
    handoff = ROOT / "standing-return/complete.json"
    verified = read(handoff)
    cfg = read(bound(ROOT / "registration.json", REG))
    manifest = read(bound(ROOT / "inputs/inputs.json", cfg["inputManifest"]))
    ids, persons, corpora, unknown = authors(manifest)
    matrices, settings = {}, {}
    for role in ("B", "W"):
        matrices[role], settings[role] = marks(verified[role], role, cfg, ids, check)
    a, b = matrices["B"], matrices["W"]
    fields = list(CHOICES)
    rise = fields.index("standing")
    earned = fields.index("earned")
    both_rose = (a[:, rise] == CHOICES["standing"].index("rose")) & (
        b[:, rise] == CHOICES["standing"].index("rose")
    )
    results = {}
    for source in ("all", *SOURCES):
        subset = np.ones(len(ids), bool) if source == "all" else corpora == source
        values = {
            field: table(a[subset, j], b[subset, j], persons[subset], levels, check)
            for j, (field, levels) in enumerate(CHOICES.items())
        }
        joint = subset & both_rose
        values["earnedAmongJointRises"] = table(
            a[joint, earned],
            b[joint, earned],
            persons[joint],
            CHOICES["earned"][:2],
            check,
        )
        results[source] = values
    path = out / "aligned.npz"
    with path.open("xb") as f:
        np.savez_compressed(
            f, ids=np.array(ids), sources=corpora, persons=persons, B=a, W=b
        )
    result = {
        "card": "TP77-standing",
        "counts": manifest["counts"],
        "unknownForumAuthorsAsSingleComments": unknown,
        "draws": 2000,
        "fields": fields,
        "tables": results,
        "readerReceipts": {
            role: verified[role]["sourceReceiptPin"] for role in ("B", "W")
        },
        "protocols": settings,
        "inputManifest": cfg["inputManifest"],
        "nativeReturnPin": pin(handoff),
        "privateAlignmentPin": pin(path),
        "originalTimingTail": original_when_tail(check),
    }
    write(out / "table.json", result)
    return result
