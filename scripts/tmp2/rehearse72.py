"""Exercise the real frozen producer on invented histories and invented speech only."""

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from conversation import TRAIT_FIELDS, conversation, turn_means
from curves import Frame
from history import history
from made import make
from panels import CONVERSATION, HISTORY, NSETS, Frozen, contracts, project


def made_histories(source):
    make(source)
    # The receiving archive expresses its invented profiles on the same 0..100 scale.
    table = source / "traits.csv"
    with table.open(newline="") as f:
        header, *data = csv.reader(f)
    with table.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows([[r[0], *[100 * float(x) for x in r[1:]]] for r in data])
    dropped = []
    with (source / "comments.csv").open("a", newline="") as f:
        writer = csv.writer(f)
        for i in range(48):
            key = f"drop-{i}"
            dropped.append(key)
            writer.writerow(
                [
                    f"person{i}",
                    key,
                    "2000-01-01",
                    "fiction",
                    "Receiver rejected this invented line.",
                ]
            )
    (source / "dropped_comments.json").write_text(json.dumps(dropped), encoding="utf8")


def invented_speech():
    objects = [
        "acorn",
        "bicycle",
        "compass",
        "daisy",
        "elm",
        "flute",
        "glass",
        "harp",
        "ink",
        "jigsaw",
        "kite",
        "lantern",
    ]
    speakers = []
    for i, noun in enumerate(objects):
        partner = objects[i ^ 1]
        outcomes = {"affect": 1 + i % 9, "how_enjoyable": 1 + (11 - i) % 9}
        for j, key in enumerate(TRAIT_FIELDS.values()):
            outcomes["self_" + key] = 1 + (i + j) % 5
            outcomes["partner_" + key] = 1 + (2 * i + j) % 5
        speakers.append(
            SimpleNamespace(
                conversation=f"pair{i // 2}",
                speaker=f"made{i}",
                turns=[
                    f"I gave the {noun} a name.",
                    f"Could it be next to the {partner}?",
                ],
                outcomes=outcomes,
            )
        )
    # The missing component should retain exactly eleven contributing people.
    speakers[-1].outcomes["partner_open"] = None
    return speakers


def exercise(work, check=lambda: None):
    import registered as reg

    frozen = Frozen()
    original_encode = frozen.encode

    def watched(texts):
        if any("Excluded fixture" in t or "Receiver rejected" in t for t in texts):
            raise ValueError("A receiver exclusion reached the encoder")
        return original_encode(texts)

    frozen.encode = watched
    work.mkdir(exist_ok=False)
    made_histories(work / "projection")
    cohorts = {}

    def observe(name, labels, people):
        if not name.startswith("conversation_"):
            expected = (
                48 if name in ("traits.csv", "contrast.csv", "channels.csv") else 32
            )
            if len(people) != expected:
                raise ValueError("Incorrect distinct writer cohort")
        cohorts[name, tuple(labels)] = len(people)

    h = history(work / "projection", work / "history", frozen, check, observe)
    if set(h) != HISTORY:
        raise ValueError(
            "Invented histories did not exercise all nine registered tables: "
            + str(sorted(set(HISTORY) - set(h)))
        )
    # Independent direct forward arithmetic for two distinct speakers and a repeated turn.
    turns = [
        ("first", "A made-up bell rang."),
        ("second", "An invented kite flew."),
        ("first", "The bell is quiet now."),
        ("first", "A made-up bell rang."),
    ]
    means = turn_means(turns, frozen, check)
    directions = frozen.directions("trained", 0)
    gap = 0.0
    for name in ("first", "second"):
        a, b = original_encode([t for k, t in turns if k == name])
        direct = project(a, b, directions).mean(0)
        xa, xb = means[name]
        actual = project(xa[None, :], xb[None, :], directions)[0]
        gap = max(gap, float(np.abs(actual - direct).max()))
    if gap > 2e-5 or np.allclose(means["first"][0], means["second"][0]):
        raise ValueError("Speaker means or frozen outputs differ")
    sample = invented_speech()
    small = conversation(sample[:2], work / "two-speakers", frozen, check, observe)
    if small or list((work / "two-speakers").iterdir()):
        raise ValueError("A two-person fixture escaped the cohort restriction")
    c = conversation(sample, work / "conversation", frozen, check, observe)
    if (
        set(c) != CONVERSATION
        or cohorts["conversation_traits.csv", ("curiosity", "partner", "Openness")]
        != 11
    ):
        raise ValueError("A missing receiver trait changed the wrong cohort")
    # Verify the optimized rank calculation against the registered TP45 reference.
    rng = np.random.default_rng(131)
    fold = np.arange(24) % 2
    x, y = rng.normal(size=(24, 2, 12)).transpose(1, 0, 2)
    cells = Frame(
        tuple(map(str, range(24))), fold, np.stack((x[:, :4], y[:, :4]), 1), None, None
    )
    left, right = cells.ranks(x[:, 4:], y[:, 4:])
    a, b = reg.rank_arms(x, y, [slice(0, 4), slice(4, 12)], fold, lambda: None)
    if not np.array_equal(left, a) or not np.array_equal(right, b):
        raise ValueError("Author matching ranks differ from the frozen reference")
    w = frozen.base_heads
    rot = frozen.directions("rot", 0)[0]
    if not np.allclose(w @ w.T, rot @ rot.T, rtol=1e-12, atol=1e-10):
        raise ValueError("Rotated geometry differs")
    totals = {}
    for mode, contract in (
        ("history", contracts(HISTORY)),
        ("conversation", contracts(CONVERSATION)),
    ):
        total = 0
        incomplete = 0
        for p in sorted((work / mode).glob("*.csv")):
            with p.open(encoding="utf8", newline="") as f:
                r = csv.DictReader(f)
                header, _, cats = contract[p.name]
                if r.fieldnames != header:
                    raise ValueError(
                        "Output header disagrees with the release contract"
                    )
                for row in r:
                    labels = tuple(row[k] for k in cats if k != "verdict")
                    if (
                        int(row["n"]) != cohorts[p.name, labels]
                        or not 11 <= int(row["n"]) <= 48
                        or not all(1 <= int(row[k]) <= NSETS for k in ("isoN", "rotN"))
                    ):
                        raise ValueError("Invalid matched row")
                    incomplete += int(row["verdict"] == "partial")
                    total += 1
        totals[mode] = {
            "rows": total,
            "rowsWithPartlyUndefinedNulls": incomplete,
            "bytes": sum(p.stat().st_size for p in (work / mode).glob("*.csv")),
        }
    return {
        "inventedOnly": True,
        "setsPerFamily": NSETS,
        "draws": 2000,
        "historyAuthors": 48,
        "deepAuthors": 32,
        "twoSpeakerRowsReleased": 0,
        "speechPeopleForDisclosureCheck": 12,
        "missingTraitN": 11,
        "largestSpeakerMeanDifference": gap,
        "matchingRanksExact": True,
        "receiverFiltersExercised": True,
        "rotatedGramMatched": True,
        "tables": {"history": h, "conversation": c},
        "size": totals,
    }


if __name__ == "__main__":
    import sys

    from run72 import offline

    sys.addaudithook(offline)
    print(json.dumps(exercise(Path(sys.argv[1])), sort_keys=True))
