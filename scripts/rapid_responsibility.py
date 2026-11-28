"""TP77: compare frozen responsibility ratings with the event writers' own answers."""

import csv
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from rapid_cpu_dispatch import ROOT
from rapid_event_features import Q28
from rapid_head_check import bound, pin, read
from rapid_marks import core, digest
from rapid_outside import GENERATION
from rapid_standing_agreement import table
from rapid_standing_return import REG
from week_pride_inputs import FROZEN, SOURCE
from week_teacher_read import rank_interval
from word_table_lane import write

FAILURE = "56e6c128806ede0aa60b3595d760a5249d80e71df675717324289c458af613e9"
RELEASE = "4014a51add3281982cdd459e230c7d0e0488ae3f4b0489e74f827617cde7e923"
FIELD = "self_responsblt"


def ratings(folder, role, ids, count, registered, check, artifacts=None):
    protocol = read(folder / role / "protocol.json")
    if (
        protocol["schema"]["required"] != list(core.FEATURES)
        or [protocol["model"], protocol["modelPin"]] != registered["readers"][role]
        or protocol["inputPin"] != digest("\n".join(ids))
        or protocol["width"] != 1
        or any(protocol[k] != v for k, v in registered["prompts"]["features"].items())
    ):
        raise ValueError("Feature order, model, prompt or roster differs")
    values = np.full(count, np.nan)
    index = list(core.FEATURES).index(FIELD)
    hashes = hashlib.sha256()
    for i in range(count):
        if i % 100 == 0:
            check()
        name = f"{role}/from-{i:06d}.json"
        path = folder / name
        h = pin(path)
        if artifacts and h != artifacts[name]:
            raise ValueError("A returned feature file changed")
        hashes.update(bytes.fromhex(h))
        (row,) = read(path)
        if row["id"] != ids[i]:
            raise ValueError("Event rating order differs")
        v = row["values"]
        if v is not None:
            if (
                not isinstance(v, list)
                or len(v) != len(core.FEATURES)
                or not all(type(x) is int and 1 <= x <= 5 for x in v)
            ):
                raise ValueError("Invalid saved 1–5 response")
            values[i] = v[index]
    return values, hashes.hexdigest()


def comparison(left, right, writer, check):
    keep = np.isfinite(left) & np.isfinite(right)
    a, b, who = left[keep], right[keep], writer[keep]
    k = table(a.astype(int) - 1, b.astype(int) - 1, who, list(range(1, 6)), check)
    return {
        "submitted": len(left),
        "paired": len(who),
        "writers": len(set(who)),
        "counts": k["contingency"],
        "rank": rank_interval(a, b, who, check),
        "kappa": {key: k[key] for key in ("value", "interval", "validDraws")},
        "exactAgreement": float(np.mean(a == b)),
    }


def prepare(out, check):
    cfg = read(bound(ROOT / "registration.json", REG))
    intake = read(bound(FROZEN / "receipt.json", SOURCE))
    generation_pin = intake["sources"]["envent"]["files"]["generation"]
    frame = pd.read_csv(
        bound(GENERATION, generation_pin),
        sep="\t",
        quoting=csv.QUOTE_NONE,
        dtype=str,
        usecols=["text_id", "prolific_id", FIELD],
        keep_default_na=False,
    )
    ids = [digest("R37:23:envent:" + ident) for ident in frame.text_id]
    people = frame.prolific_id.to_numpy(str)
    if (
        len(ids) != 6600
        or len(set(ids)) != 6600
        or "" in people
        or len(set(people)) != 2379
    ):
        raise ValueError("The event-writer panel differs")
    human = pd.to_numeric(
        frame[FIELD].replace({"": np.nan, "NA": np.nan}), errors="raise"
    ).to_numpy(float)
    if not np.all(np.isnan(human) | np.isin(human, [1, 2, 3, 4, 5])):
        raise ValueError("Human rating outside released scale")
    transfer = read(ROOT / "Q28-transfer.json")
    if (
        not transfer["nativeExited"]
        or not transfer["ownedFlockReleased"]
        or transfer["sourceReceiptPin"] != Q28
    ):
        raise ValueError("Unverified Q28 release")
    folder = Path(transfer["mirror"])
    rec = read(bound(folder / "receipt.json", Q28))
    bound(folder / "B/protocol.json", rec["result"]["protocolPin"])
    b, bpin = ratings(folder, "B", ids, len(ids), cfg, check, rec["artifacts"])
    if rec["result"]["valid"] != int(np.isfinite(b).sum()):
        raise ValueError("B validity differs")
    partial = ROOT / "jobs/G14"
    fail = read(bound(partial / "failed.json", FAILURE))
    release = read(bound(partial / "released.json", RELEASE))
    if (
        fail["owner"] != release["owner"]
        or not release["nativeExited"]
        or not release["sharedLeaseReacquired"]
    ):
        raise ValueError("G14 native identity or release differs")
    n = len(list((partial / "W").glob("from-*.json")))
    if n != 928:
        raise ValueError("Saved G14 prefix differs from its recorded stop")
    w, wpin = ratings(partial, "W", ids, n, cfg, check)
    tables = {
        "B-writer": comparison(b, human, people, check),
        "W-writer-prefix": comparison(w, human[:n], people[:n], check),
        "B-writer-prefix": comparison(b[:n], human[:n], people[:n], check),
        "B-W-prefix": comparison(b[:n], w, people[:n], check),
    }
    result = {
        "target": FIELD,
        "generationPin": generation_pin,
        "BReceipt": Q28,
        "WRelease": RELEASE,
        "WFailure": FAILURE,
        "ratingPins": {"B": bpin, "W": wpin},
        "draws": 2000,
        "tables": tables,
    }
    write(out / "table.json", result)
    return result
