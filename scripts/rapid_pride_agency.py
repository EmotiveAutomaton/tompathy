"""TP67's direct three-way agency comparison on the saved chat forecasts."""

import numpy as np
from rapid_agreement import classification
from rapid_blend import estimate
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import bound, pin, read
from rapid_inputs import key
from rapid_marks import CHOICES
from rapid_pride_scale import scaled
from rapid_word_contrasts import draws, grouped_mean
from tompathy_engine.eval.readers.tp39 import saved
from week_pride_inputs import FROZEN, SOURCE
from word_table_lane import write

WORDS = {"proud": 867, "impressed": 805, "confident": 785, "grateful": 815}
PAIRS = (("own", "close"), ("own", "other"), ("close", "other"))
STAGE = "TP67-agency"


def align(native_ids, submitted_ids, persons, writer_codes):
    expected = [key("ed", item) for item in native_ids]
    if len(set(expected)) != len(expected) or not np.array_equal(
        expected, submitted_ids
    ):
        raise ValueError("Chat forecast IDs and submitted agency IDs differ")
    if not all(str(person).startswith("ed:") for person in persons):
        raise ValueError("Writer from outside the registered chat source")
    if not np.array_equal(np.unique(persons, return_inverse=True)[1], writer_codes):
        raise ValueError("Original and standing-panel writer assignments differ")


def compare(pride, words, writers, agency, gate, check):
    levels = CHOICES["whose"]
    if (
        not (pride.shape == words.shape == writers.shape == agency.shape)
        or pride.ndim != 1
        or not np.isfinite(pride).all()
        or not np.isin(agency, [-1, *range(len(levels))]).all()
        or gate not in ("usable", "weak", "not used")
    ):
        raise ValueError("Invalid forecast, writer, group or CW classification")
    rows = {}
    for word in WORDS:
        check()
        use = words == word
        groups = {k: use & (agency == i) for i, k in enumerate(levels)}
        counts = {k: int(mask.sum()) for k, mask in groups.items()}
        counts["invalid"] = int((use & (agency == -1)).sum())
        contrasts = {}
        for first, second in PAIRS:
            name = f"{first}-{second}"
            if gate == "not used":
                contrasts[name] = {"reason": "Agency is unavailable under CW."}
                continue
            if min(counts[first], counts[second]) < 50:
                contrasts[name] = {
                    "reason": "Fewer than 50 reports on at least one side."
                }
                continue
            a, b = groups[first], groups[second]
            people = np.unique(writers[a | b])
            # A single cluster gives a point estimate and no sampling interval.
            weight = draws(len(people)) if len(people) > 1 else np.ones((1, 1))
            difference, _, standardized = scaled(pride, writers, a, b, weight)
            contrasts[name] = {
                "writers": len(people),
                "firstMean": estimate(grouped_mean(pride, writers, a, people, weight)),
                "secondMean": estimate(grouped_mean(pride, writers, b, people, weight)),
                "difference": estimate(difference),
                "differenceInSD": estimate(standardized),
                "belowOneFifthSD": estimate(0.2 - standardized),
            }
        rows[word] = {"reports": int(use.sum()), "counts": counts, "pairs": contrasts}
    return rows


def prepare(out, check, *, panel=None):
    panel = panel or ROOT / "TP77-standing-a"
    bridge = ROOT / "TP69-a"
    prior = ROOT / "TP67-original-a"
    releases = {p.name: confirmed(p) for p in (panel, bridge, prior)}
    gates = read(panel / "receipt.json")["result"]
    original = read(prior / "receipt.json")["result"]
    forecasts = read(bridge / "receipt.json")["result"]
    if (
        original["sourceReceiptPin"] != releases[bridge.name]
        or gates["card"] not in ("TP77-standing", "TP77-standing-chat-prefix")
        or gates["fields"] != list(CHOICES)
        or gates["counts"]["ed"] != 24850
    ):
        raise ValueError("Standing and original PRIDE sources are not bound")
    chat = gates["tables"]["ed"]["whose"]
    prefix = gates["card"] == "TP77-standing-chat-prefix"
    full = chat if prefix else gates["tables"]["all"]["whose"]
    for cell in (full, chat):
        if cell["levels"] != CHOICES["whose"] or cell["CW"] != classification(
            cell["value"]
        ):
            raise ValueError("Agency levels or reliability classification differ")
    check()
    with np.load(
        bound(bridge / "pride-responsibility.npz", forecasts["futureJoinPin"]),
        allow_pickle=False,
    ) as f:
        pride, words, writers = (f[k] for k in ("pride", "word", "writer"))
    source = read(bound(FROZEN / "receipt.json", SOURCE))
    ordered = saved(FROZEN, "ed-profile-forecasts.npz", source)
    with np.load(ordered, allow_pickle=False) as f:
        ids = f["ids"].astype(str)
    with np.load(
        bound(panel / "aligned.npz", gates["privateAlignmentPin"]), allow_pickle=False
    ) as f:
        ed = f["sources"] == "ed"
        align(ids, f["ids"][ed], f["persons"][ed], writers)
        agency = f["B"][ed, gates["fields"].index("whose")]
    if len(ids) != 24850 or chat["jointlyValid"] + chat["BOnly"] != int(
        (agency >= 0).sum()
    ):
        raise ValueError("Standing roster or valid B census differs from TP77")
    rows = compare(pride, words, writers, agency, full["CW"], check)
    if any(
        rows[w]["reports"] != n or original["reports"][w]["total"] != n
        for w, n in WORDS.items()
    ):
        raise ValueError("Word counts differ from the original TP67 roster")
    result = {
        "card": STAGE,
        "sourceReceipts": releases,
        "prideForecastPin": forecasts["futureJoinPin"],
        "orderedForecastPin": pin(ordered),
        "standingAlignmentPin": gates["privateAlignmentPin"],
        "agreement": {"roster": full["value"], "chat": chat["value"], "CW": full["CW"]},
        "reports": rows,
        "wholeWriterDraws": 2000,
    }
    if prefix:
        result.update(
            card="TP67-agency-chat-prefix",
            panelScope="Complete chat roster in G12's memory-stop prefix",
            originalPrefixSources=gates["originalPrefixSources"],
        )
    write(out / "table.json", result)
    return result
