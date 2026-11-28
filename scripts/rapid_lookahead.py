"""TP75: align original B sentence shares and saved worry scores after verified Q31 agreement."""

from pathlib import Path

import numpy as np
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import Q20, bound, pin, read
from rapid_q31_agreement import REG
from rapid_sentence_data import CLASSES
from rapid_worry_repeat import WEEK
from word_table_lane import write


def opening_shares(parent, marks, n):
    if (
        parent.ndim != 1
        or marks.shape != parent.shape
        or parent.size == 0
        or parent.min() < 0
        or parent.max() >= n
        or not np.isin(marks, [-1, *range(len(CLASSES))]).all()
    ):
        raise ValueError("Sentence parent or timing label outside registered range")
    total = np.bincount(parent, minlength=n)
    if np.any(total == 0):
        raise ValueError("An opening has no sentence")
    missing = np.bincount(parent[marks == -1], minlength=n)
    ahead = np.bincount(parent[marks == CLASSES.index("ahead")], minlength=n)
    return np.where(missing == 0, ahead / total, np.nan)


def prepare(out, check):
    cfg = read(bound(ROOT / "Q31-registration.json", REG))
    sel = ROOT / "Q31-inputs-a"
    if confirmed(sel) != cfg["selectionReceiptPin"]:
        raise ValueError("Q31 selection source differs")
    rows = read(bound(sel / "selection.json", cfg["selectionPin"]))["sample"]
    selected, keys = zip(*rows, strict=True)
    agreement = ROOT / "TP77-Q31-a"
    source = confirmed(agreement)
    a = read(agreement / "table.json")
    prior = read(ROOT / "Q31-completion/complete.json")
    if (
        a != read(agreement / "receipt.json")["result"]
        or a["registration"] != REG
        or (prior["agreementReceipt"], prior["BReceipt"]) != (source, a["BReceipt"])
    ):
        raise ValueError("Unverified blog agreement or B source")
    gates = {k: a["tables"][k]["CW"] for k in ("change", "when")}
    result = {
        "agreementReceipt": source,
        "BReceipt": a["BReceipt"],
        "CW": gates,
        "jointlyValidTiming": a["tables"]["when"]["jointlyValid"],
        "registeredAuthors": 500,
        "registeredOpenings": 10000,
    }
    if "not used" in gates.values():
        result["status"] = "blocked by CW"
        write(out / "table.json", result)
        return result
    if any(v not in ("usable", "weak") for v in gates.values()):
        raise ValueError("Unrecognized CW ruling")
    with np.load(
        bound(agreement / "aligned.npz", a["alignedPin"]), allow_pickle=False
    ) as f:
        if (
            selected != tuple(f["opening"])
            or len(selected) != 10000
            or len(set(selected)) != len(selected)
        ):
            raise ValueError("Q31 opening order mismatch")
        share = opening_shares(f["parent"], f["B"][:, 0], len(selected))
        owners, index, sizes = np.unique(
            f["authors"], return_inverse=True, return_counts=True
        )
    if len(owners) != 500 or not (sizes == 20).all():
        raise ValueError("Unmatched 500 by 20 selection")
    eligible = np.bincount(index[~np.isfinite(share)], minlength=len(owners)) == 0
    keep = eligible[index]
    keys = np.asarray(keys)
    transfer = read(WEEK / "Q20-transfer.json")
    mirror = Path(transfer["mirror"])
    receipt = read(bound(mirror / "receipt.json", Q20))
    if not (
        transfer["nativeExited"]
        and transfer["priorFlockReleased"]
        and transfer["sourceReceiptPin"] == Q20
    ):
        raise ValueError("Q20 transfer proof missing")
    wanted = set(keys[keep])
    worries = {}
    for name, h in sorted(receipt["outputs"].items()):
        if not name.startswith("scores-"):
            continue
        check()
        if transfer["files"].get(name) != h:
            raise ValueError("Q20 score shard binding differs")
        with np.load(bound(mirror / name, h), allow_pickle=False) as f:
            ids = f["ids"].astype(str)
            take = [i for i, key in enumerate(ids) if key in wanted]
            if take:
                vals = f["worry"].reshape(len(ids))[take]
                if (
                    not np.isfinite(vals).all()
                    or any(key in worries for key in ids[take])
                    or len(set(ids[take])) != len(take)
                ):
                    raise ValueError("Invalid worry forecast")
                worries.update(zip(ids[take], vals, strict=True))
    if set(worries) != wanted:
        raise ValueError("Incomplete worry coverage")
    path = out / "paired.npz"
    with path.open("xb") as f:
        np.savez_compressed(
            f,
            owner=index[keep],
            opening=keys[keep],
            ahead=share[keep],
            worry=np.asarray([worries[k] for k in keys[keep]]),
        )
    result.update(
        status="paired inputs prepared",
        eligibleAuthors=int(eligible.sum()),
        eligibleOpenings=int(keep.sum()),
        incompleteOpenings=int(np.sum(~np.isfinite(share))),
        worryReceipt=Q20,
        pairedPin=pin(path),
    )
    write(out / "table.json", result)
    return result
