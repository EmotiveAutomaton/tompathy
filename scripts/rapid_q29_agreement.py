"""Analyze Q29 sentence agreement on the exact saved overlap and bind TP65 inputs."""

import hashlib
import json
from itertools import groupby
from pathlib import Path

import numpy as np
from rapid_cpu_dispatch import ROOT
from rapid_head_check import bound, pin, read
from rapid_inputs import key
from rapid_marks import digest
from rapid_sentence_data import CLASSES, WHO, classes
from rapid_standing_agreement import table
from tompathy_engine.eval.readers.tp31_teacher import valid_label
from tompathy_engine.eval.readers.tp39 import saved
from week_pride_inputs import FROZEN, SOURCE
from word_table_lane import write

REG = "86477edf7ee5b3f26ed8dc79d14469522375fc36677cfa57946a64539b13ece7"
Q29 = "87208aafd6bc6345d6a8a3babf98e648d323b93823289b617d01cceb7c66653e"
WFAIL = "d69e33f2a43a948795399ad397216a5939ec7bcb08b5848f23fc4bea9c1d3d8c"
WRELEASE = "06abcdf4181755b2456c1f007fa417fa24e514518541b98e16b767b71e5f67d4"
JOINS = "04298592cfd6f45b981f50f5c25c3d414eb5e7a727f2c7e8e6848356bcd03b83"


def decode(row):
    try:
        label = valid_label(json.loads(row["response"]))
    except (ValueError, TypeError):
        label = None
    if label != row["values"]:
        raise ValueError("Saved sentence label differs from the recorded response")
    return classes(label)


def roster(links, intake):
    ids, parents, ordinal, lengths, groups = [], [], [], [], []
    for source in ("go", "isear"):
        start = len(parents)
        for parent, batch in groupby(links[source], key=lambda row: row[1]):
            group = list(batch)
            idx = len(parents)
            for j, (ident, _, pos, n) in enumerate(group):
                if (
                    pos != j
                    or n != len(group)
                    or ident != digest(f"Q29:{source}:{parent}:{j}")
                ):
                    raise ValueError("Incomplete report or mismatched sentence order")
                ids.append(ident)
                ordinal.append(pos)
                groups.append(idx)
            lengths.append(len(group))
            parents.append(parent)
        counts = intake["counts"][source]
        if (
            len(links[source]) != counts["sentences"]
            or len(parents) - start != counts["reports"]
        ):
            raise ValueError("Incorrect source census")
    if (
        len(set(parents)) != len(parents)
        or len(set(ids)) != len(ids)
        or digest("\n".join(ids)) != intake["orderedIdPin"]
    ):
        raise ValueError("Changed sentence roster")
    return ids, parents, np.array(groups), np.array(ordinal), np.array(lengths)


def read_marks(folder, role, ids, count, cfg, check, artifacts=None):
    settings_file = folder / role / "protocol.json"
    if artifacts:
        bound(settings_file, artifacts[f"{role}/protocol.json"])
    settings = read(settings_file)
    expected_options = dict(cfg["options"])
    think = expected_options.pop("think")
    expected_options["num_thread"] = 3 if role == "B" else 2
    if (
        [settings["model"], settings["modelPin"]] != cfg["readers"][role]
        or settings["inputPin"] != cfg["sentences"]["orderedIdPin"]
        or settings["think"] is not think
        or settings["options"] != expected_options
        or settings["width"] != 1
        or any(settings[k] != v for k, v in cfg["prompt"].items())
    ):
        raise ValueError("Reader, schema or inference options differ")
    if sum(1 for _ in (folder / role).glob("from-*.json")) != count:
        raise ValueError("Saved response count differs")
    values = np.full((len(ids), 2), -1, dtype=np.int8)
    hashes = hashlib.sha256()
    for i in range(count):
        if i % 128 == 0:
            check()
        name = f"{role}/from-{i:06d}.json"
        raw = (folder / name).read_bytes()
        h = hashlib.sha256(raw)
        if artifacts and h.hexdigest() != artifacts[name]:
            raise ValueError("Returned response changed")
        hashes.update(h.digest())
        (row,) = json.loads(raw)
        if row["id"] != ids[i]:
            raise ValueError("Sentence and response IDs differ")
        values[i] = decode(row)
    return values, hashes.hexdigest()


def go_authors(parents):
    source = read(bound(FROZEN / "receipt.json", SOURCE))
    with np.load(saved(FROZEN, "go-targets.npz", source), allow_pickle=False) as d:
        native, people = d["ids"].astype(str), d["authors"].astype(str)
    refs = dict(zip(native, people, strict=True))
    with np.load(
        saved(FROZEN, "go-profile-forecasts.npz", source), allow_pickle=False
    ) as d:
        held = d["ids"].astype(str)
    if len(refs) != len(native) or [key("go", i) for i in held] != parents:
        raise ValueError("Held-out forum author order differs")
    people = np.array([refs[i] for i in held])
    if np.any(people == ""):
        raise ValueError("Missing source author key")
    return people


def prepare(out, check):
    cfg = read(bound(ROOT / "Q29-registration.json", REG))
    audit = read(ROOT / "Q29-transfer.json")
    if (
        audit["sourceReceiptPin"] != Q29
        or not audit["nativeExited"]
        or not audit["ownedFlockReleased"]
    ):
        raise ValueError("Q29 exit or shared lease unverified")
    bdir = Path(audit["mirror"])
    brec = read(bound(bdir / "receipt.json", Q29))
    artifacts = brec["artifacts"]
    wdir = ROOT / "jobs/G13-Q29"
    stop = read(bound(wdir / "failed.json", WFAIL))
    release = read(bound(wdir / "released.json", WRELEASE))
    if (
        brec["status"] != "complete"
        or brec["owner"]["registration"] != REG
        or stop["owner"] != release["owner"]
        or stop["owner"]["registration"] != REG
        or not release["childWaited"]
        or not release["sharedLeaseReacquired"]
        or release["exitCode"] != 1
    ):
        raise ValueError("Source jobs or release differ")
    intake = cfg["sentences"]
    if intake != brec["result"]["intake"] or intake != read(wdir / "intake.json"):
        raise ValueError("Sentence populations differ")
    ids, parents, parent, ordinal, lengths = roster(
        read(bound(ROOT / "Q29-inputs/local-parent-joins.json", JOINS)), intake
    )
    ng = intake["counts"]["go"]["reports"]
    n = intake["counts"]["go"]["sentences"]
    people = go_authors(parents[:ng])
    prefix = 17124
    b, bhash = read_marks(bdir, "B", ids, len(ids), cfg, check, artifacts)
    w, whash = read_marks(wdir, "W", ids, prefix, cfg, check)
    if int((b[:, 0] >= 0).sum()) != brec["result"]["reader"]["valid"]:
        raise ValueError("Valid count differs from B receipt")
    ten = np.empty((len(ids), 10), dtype=float)
    for start in range(0, len(ids), 100):
        check()
        file = f"ten/from-{start:06d}.npz"
        end = min(len(ids), start + 100)
        with np.load(bound(bdir / file, artifacts[file]), allow_pickle=False) as d:
            if (
                list(d["ids"].astype(str)) != ids[start:end]
                or d["ten"].shape != (end - start, 10)
                or not np.isfinite(d["ten"]).all()
            ):
                raise ValueError("Changed frozen score order, shape or values")
            ten[start:end] = d["ten"]
    x, y = b[:prefix], w[:prefix]
    who = people[parent[:prefix]]
    comparisons = {
        field: table(left, right, who, levels, check)
        for field, left, right, levels in (
            ("change", np.sign(x[:, 0]), np.sign(y[:, 0]), ["no change", "change"]),
            ("when", x[:, 0], y[:, 0], list(CLASSES)),
            ("whose", x[:, 1], y[:, 1], list(WHO)),
        )
    }
    coverage = {}
    for source, sel, available in (
        ("go", slice(0, n), prefix),
        ("isear", slice(n, None), 0),
    ):
        coverage[source] = {**intake["counts"][source], "WSaved": available}
        for role, m in (("B", b[sel]), ("W", w[sel])):
            coverage[source][role] = {
                k: int((m[:, 0] == i).sum()) for i, k in enumerate(CLASSES)
            }
            coverage[source][role]["valid"] = int((m[:, 0] >= 0).sum())
    aligned = out / "aligned.npz"
    np.savez_compressed(
        aligned,
        parent=parent[:n],
        ordinal=ordinal[:n],
        lengths=lengths[:ng],
        authors=people,
        B=b[:n],
        W=w[:n],
        ten=ten[:n],
    )
    result = {
        "BReceipt": Q29,
        "WFailure": WFAIL,
        "WRelease": WRELEASE,
        "BResponsesPin": bhash,
        "WResponsesPin": whash,
        "alignedPin": pin(aligned),
        "coverage": coverage,
        "tables": comparisons,
        "draws": 2000,
    }
    write(out / "table.json", result)
    return result
