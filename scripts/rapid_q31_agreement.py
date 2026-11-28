"""Verify the Q31 blog return and compare the jointly saved sentence marks by author."""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, pin, read
from rapid_marks import digest, template
from rapid_q29_agreement import decode
from rapid_sentence_data import CLASSES, WHO
from rapid_standing_agreement import table
from word_table_lane import write

REG = "6aa593aedf27e353db6751c652a166e0a76955e89185708866f45e0e51e31096"
WFAIL = "68cfb24226865fb88c782bc2baaf0f2d0745a6c0a8658b4a690232bf86523143"
WRELEASE = "596c4286d44f0546a8109ca08e5a10bafa311b903eac66bcce10011bc9c8665a"


def parents(ids, openings):
    pos = group = 0
    owners = []
    for key in ids:
        if key != digest(f"Q31:{openings[group]}:{pos}"):
            group += 1
            if (
                pos == 0
                or group >= len(openings)
                or key != digest(f"Q31:{openings[group]}:0")
            ):
                raise ValueError("Sentence outside its registered opening or position")
            pos = 0
        owners.append(group)
        pos += 1
    if not pos or group + 1 != len(openings):
        raise ValueError("Missing final registered openings")
    return np.array(owners)


def batches(directory, arm, count, config, role, width, check, artifacts=None):
    def original(file):
        name = arm + "/" + file
        return read(
            bound(directory / name, artifacts[name])
            if artifacts is not None
            else directory / name
        )

    protocol = original("protocol.json")
    options = dict(config["options"])
    think = options.pop("think")
    options["num_thread"] = 3 if role == "B" else 2
    intake = config["roster"]["sentences" if arm == "sentence" else "loss"]
    model, modelpin = config["readers"][role]
    if protocol != dict(
        config["prompts"][arm],
        options=options,
        think=think,
        inputPin=intake["orderedIdPin"],
        width=width,
        model=model,
        modelPin=modelpin,
    ):
        raise ValueError("Unexpected prompt, model, roster or options")
    if len(list((directory / arm).glob("from-*.json"))) != (count + width - 1) // width:
        raise ValueError("Incomplete batch inventory")
    for i in range(0, count, width):
        if i % 128 == 0:
            check()
        rows = original(f"from-{i:06d}.json")
        if len(rows) != min(count - i, width):
            raise ValueError("Wrong number of rows in saved batch")
        yield from rows


def prepare(out, check):
    cfg = read(bound(ROOT / "Q31-registration.json", REG))
    sel = ROOT / "Q31-inputs-a"
    if confirmed(sel) != cfg["selectionReceiptPin"]:
        raise ValueError("Q31 input identity differs")
    intake = read(sel / "receipt.json")["result"]
    joins = read(bound(sel / "local-joins.json", intake["joinPin"]))
    plan = read(bound(sel / "selection.json", cfg["selectionPin"]))
    transfer = read(ROOT / "Q31-transfer.json")
    src = transfer["sourceReceiptPin"]
    b = Path(transfer["mirror"])
    brec = read(bound(b / "receipt.json", src))
    w = ROOT / "jobs/G13-Q31"
    release = read(bound(w / "released.json", WRELEASE))
    stop = read(bound(w / "failed.json", WFAIL))
    proof = read(ROOT / "workstation-terminal-20261128.json")["jobs"]["G13-Q31"]
    if (
        not transfer["nativeExited"]
        or not transfer["ownedFlockReleased"]
        or brec["owner"]["registration"] != REG
        or brec["owner"] != transfer["owner"]
        or brec["status"] != "complete"
        or not proof["exitVerified"]
        or proof["releasePin"] != WRELEASE
        or proof["owner"] != release["owner"]
        or stop["owner"] != release["owner"]
        or stop["owner"]["registration"] != REG
        or not release["childWaited"]
        or not release["sharedLeaseReacquired"]
        or any(
            v != cfg["roster"]
            for v in (
                intake["roster"],
                brec["result"]["intake"],
                read(w / "intake.json"),
            )
        )
    ):
        raise ValueError("Cannot bind the completed B and stopped W jobs")
    artifacts = brec["artifacts"]
    width = read(
        bound(
            ROOT / "verified-Q26-3d8813a93303/receipt.json",
            "3d8813a933033506d9c9d2ff8f1bb2e550b42a2e658530363be177c7c49e3132",
        )
    )["result"]["selectedWidth"]
    n = cfg["roster"]["sentences"]["n"]
    prefix = proof["rowFiles"]
    ids = []
    labels = np.empty((n, 2), dtype=np.int8)
    for i, row in enumerate(
        batches(b, "sentence", n, cfg, "B", width, check, artifacts)
    ):
        ids.append(row["id"])
        labels[i] = decode(row)
    if (
        digest("\n".join(ids)) != cfg["roster"]["sentences"]["orderedIdPin"]
        or int((labels[:, 0] >= 0).sum()) != brec["result"]["sentence"]["valid"]
    ):
        raise ValueError("Blog sentence order or valid count differs")
    openings = [k for k, _ in plan["sample"]]
    if openings != [k for k, _, _ in joins["sample"]]:
        raise ValueError("Changed local opening joins")
    parent = parents(ids, openings)
    authors = np.array([a for _, _, a in joins["sample"]])
    other = np.full_like(labels, -1)
    for i, row in enumerate(batches(w, "sentence", prefix, cfg, "W", 1, check)):
        if row["id"] != ids[i]:
            raise ValueError("W order differs")
        other[i] = decode(row)
    if int((other[:, 0] >= 0).sum()) != proof["valid"] or (w / "loss").exists():
        raise ValueError("Stopped W coverage differs")
    loss = Counter()
    parse = template("loss")[2]
    for row, (key, _) in zip(
        batches(b, "loss", len(plan["loss"]), cfg, "B", width, check, artifacts),
        plan["loss"],
        strict=True,
    ):
        if row["id"] != key:
            raise ValueError("Loss roster differs")
        try:
            value = parse(json.loads(row["response"]))
        except (ValueError, TypeError):
            value = None
        if value != row["values"]:
            raise ValueError("Loss response and saved classification disagree")
        loss[value["kind"] if value else "missing"] += 1
    if sum(loss.values()) - loss["missing"] != brec["result"]["loss"]["valid"]:
        raise ValueError("Loss valid count differs")
    x, y = labels[:prefix], other[:prefix]
    tables = {
        name: table(left, right, authors[parent[:prefix]], levels, check)
        for name, left, right, levels in (
            ("change", np.sign(x[:, 0]), np.sign(y[:, 0]), ["no change", "change"]),
            ("when", x[:, 0], y[:, 0], list(CLASSES)),
            ("whose", x[:, 1], y[:, 1], list(WHO)),
        )
    }
    f = out / "aligned.npz"
    np.savez_compressed(
        f,
        ids=np.asarray(ids),
        parent=parent,
        authors=authors,
        opening=np.asarray([k for _, k in plan["sample"]]),
        B=labels,
        W=other,
    )
    result = {
        "BReceipt": src,
        "WRelease": WRELEASE,
        "registration": REG,
        "alignedPin": pin(f),
        "sentences": n,
        "openings": len(openings),
        "authors": len(set(authors)),
        "WSaved": prefix,
        "lossKindsB": dict(loss),
        "lossSavedW": 0,
        "validB": brec["result"]["sentence"]["valid"],
        "tables": tables,
        "draws": 2000,
    }
    write(out / "table.json", result)
    return result
