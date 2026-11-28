"""TP65 extension on complete forum reports inside the original B/W sentence overlap."""

import numpy as np
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, read
from rapid_sentence_contrasts import NAMES, PAIRS, fit
from rapid_sentence_data import CLASSES
from word_table_lane import write


def whole_prefix(parent, lengths, stop):
    if not 0 < stop <= len(parent):
        raise ValueError("Invalid saved sentence boundary")
    ends = np.cumsum(lengths)
    nreports = int(np.searchsorted(ends, stop, side="right"))
    nsentences = int(ends[nreports - 1]) if nreports else 0
    if np.any(parent[:nsentences] >= nreports) or np.any(
        parent[nsentences:] < nreports
    ):
        raise ValueError("Reports cross the selected sentence boundary")
    return nreports, nsentences


def prepare(out, check):
    directory = ROOT / "TP77-Q29-a"
    receipt = confirmed(directory)
    info = read(directory / "receipt.json")["result"]
    if info != read(directory / "table.json"):
        raise ValueError("Q29 agreement input differs from its verified receipt")
    with np.load(
        bound(directory / "aligned.npz", info["alignedPin"]), allow_pickle=False
    ) as data:
        parent, ordinal, lengths, authors, b, w, ten = (
            data[k]
            for k in ("parent", "ordinal", "lengths", "authors", "B", "W", "ten")
        )
    nfull = info["coverage"]["go"]["WSaved"]
    n, stop = whole_prefix(parent, lengths, nfull)
    if ten.shape != (len(parent), len(NAMES) - 1) or not np.isfinite(ten).all():
        raise ValueError("Q29 ten-channel table is incomplete")
    parent = parent[:stop]
    position = ordinal[:stop] / np.maximum(1, lengths[parent] - 1)
    readers, owners = np.unique(authors[:n], return_inverse=True)
    b, w = b[:stop], w[:stop]
    same = (b == w).all(1) & (b[:, 0] >= 0)
    gates = {k: c["CW"] for k, c in info["tables"].items()}
    # Reuse the registered whole-writer draws across arms and outputs.
    rng = np.random.default_rng(23)
    size = len(readers)
    weights = np.empty((2001, size), dtype=np.int32)
    weights[0] = 1
    for start in range(1, 2001, 50):
        check()
        weights[start : start + 50] = rng.multinomial(
            size, np.full(size, 1 / size), size=50
        )
    tables = {}
    for name, labels in (
        ("B", b[:, 0]),
        ("W", w[:, 0]),
        ("agreement", np.where(same, b[:, 0], -1)),
    ):
        scores = {}
        for key, (positive, negative) in PAIRS.items():
            fields = (
                ("change", "when", "whose")
                if name == "agreement"
                else ("change", "when")
            )
            if any(gates[k] == "not used" for k in fields):
                scores[key] = {
                    "status": "withheld under CW on the observed forum prefix",
                    "outputs": {},
                }
                continue
            scores[key] = fit(
                labels,
                positive,
                negative,
                ten[:stop],
                parent,
                owners,
                position,
                weights,
                check,
                names=NAMES[:-1],
            )
            scores[key]["status"] = (
                "weak descriptive"
                if any(gates[k] == "weak" for k in fields)
                else "usable on the observed prefix"
            )
        tables[name] = {
            "classCounts": {v: int((labels == i).sum()) for i, v in enumerate(CLASSES)},
            "outside": int((labels < 0).sum()),
            "contrasts": scores,
        }
    result = {
        "agreementReceipt": receipt,
        "coverage": info["coverage"],
        "forum": {
            "reports": n,
            "sentences": stop,
            "writers": size,
            "lastReportSentencesExcluded": nfull - stop,
            "gates": gates,
            "tables": tables,
        },
        "isear": {
            "status": "W has no saved readings; source-specific reliability and contrasts unavailable"
        },
        "outputs": list(NAMES[:-1]),
        "draws": 2000,
    }
    write(out / "table.json", result)
    return result
