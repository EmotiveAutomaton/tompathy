"""File TP67's direct marks beside the original responsibility comparison."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapid_card_record import RETURN, SCOREBOARD, STATUS, interval, live_line, number
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_family import SHEET, render
from rapid_head_check import bound, pin, read
from rapid_land import PUBLIC, put
from rapid_later_record import all_above, direction, prediction, standing, write_text
from rapid_pride_agency import PAIRS, STAGE, WORDS
from tompathy_engine.eval.evidence import append
from word_table_lane import write

CARD = Path("docs/exchange/result-sheets/TP67.md")
PUBLIC_FILE = PUBLIC / "readers-tp67-agency-2026-11.json"
FILES = (
    STATUS,
    SCOREBOARD,
    RETURN,
    CARD,
    SHEET,
    PUBLIC / "EVIDENCE_LEDGER.jsonl",
    PUBLIC_FILE,
)


def predictions(rows, gate, original, original_support):
    pairs = [r["pairs"] for r in rows.values()]
    eligible = [p for p in pairs if all("difference" in v for v in p.values())]
    own = [p[k]["difference"] for p in eligible for k in ("own-close", "own-other")]
    order = [p[k]["difference"] for p in eligible for k in ("own-close", "close-other")]
    size = [
        p["own-other"][field]
        for p in pairs
        if "difference" in p["own-other"]
        for field in ("differenceInSD", "belowOneFifthSD")
    ]
    usable = gate == "usable"
    updated = {}

    def estimates(pairs_to_show, field):
        parts = []
        for word, row in rows.items():
            pairs_for_word = row["pairs"]
            if all(field in pairs_for_word[k] for k in pairs_to_show):
                values = " / ".join(
                    interval(pairs_for_word[k][field]) for k in pairs_to_show
                )
                parts.append(f"{word} {values}")
        return ", ".join(parts) or "no eligible word"

    for key, cells, description in (
        (
            "TP67.1",
            own,
            "Own − close / own − other: "
            + estimates(("own-close", "own-other"), "difference"),
        ),
        (
            "TP67.3",
            order,
            "Own − close / close − other: "
            + estimates(("own-close", "close-other"), "difference"),
        ),
        (
            "TP67.analyst",
            size,
            "Own − other in within-word SD: "
            + estimates(("own-other",), "differenceInSD"),
        ),
    ):
        prior = original[key]
        p = all_above(cells) if usable else None
        if p is None:
            verdict = {
                "weak": "Direct estimates are descriptive under CW.",
                "not used": "Direct contrasts withheld under CW.",
            }.get(gate, "No fully estimable direct test.")
            updated[key] = prediction(
                description,
                verdict + " Earlier result retained.",
                prior["p"],
                prior["against"],
            )
            continue
        # The earlier two-level study had no measure of closeness. For the other
        # predictions both the original reading and the new reading must support it.
        earlier_applies = key != "TP67.3"
        joint_p = p
        if earlier_applies:
            joint_p = None if prior["p"] is None else max(prior["p"], p)
        against = prior["against"] or any(direction(c) < 0 for c in cells)
        supported = all(direction(c) > 0 for c in cells)
        if earlier_applies:
            supported = supported and original_support[key]
        verdict = (
            "Registered direction missed."
            if against
            else (
                "All eligible components clear."
                if supported and joint_p is not None
                else "Unresolved under CX."
            )
        )
        updated[key] = prediction(description, verdict, joint_p, against)
    previous = original["TP67.2"]
    departed = usable and any(
        direction(v["difference"]) != 0
        for p in pairs
        for v in p.values()
        if "difference" in v
    )
    updated["TP67.2"] = prediction(
        "Within-word differences are filed for each eligible pair.",
        "There is no registered equivalence margin. Equality remains unestablished.",
        against=bool(previous["against"] or departed),
    )
    return updated


def file_card(out, plan, states):
    receipt = read(out / "receipt.json")
    source = confirmed(out)
    r = receipt["result"]
    earlier = read(
        bound(
            PUBLIC / "readers-tp67-original-2026-11.json",
            read(plan)["originalPublicPin"],
        )
    )
    if (
        receipt["registrationPin"] != pin(plan)
        or receipt["status"] != "complete"
        or receipt["card"] != STAGE
        or r["card"] != STAGE
        or r != read(out / "table.json")
        or r["wholeWriterDraws"] != 2000
        or set(r["reports"]) != set(WORDS)
        or earlier["sourceReceiptPin"] != r["sourceReceipts"]["TP67-original-a"]
        or r["sourceReceipts"]["TP77-standing-a"] != confirmed(ROOT / "TP77-standing-a")
    ):
        raise ValueError("Unverified agency result or original forecast binding")
    gate = r["agreement"]["CW"]
    rows = r["reports"]
    for word, row in rows.items():
        if (
            sum(row["counts"].values()) != WORDS[word]
            or row["reports"] != WORDS[word]
            or set(row["pairs"]) != {f"{a}-{b}" for a, b in PAIRS}
        ):
            raise ValueError("Incomplete word or pair census")
        for a, b in PAIRS:
            eligible = (
                gate != "not used" and min(row["counts"][a], row["counts"][b]) >= 50
            )
            if eligible != ("difference" in row["pairs"][f"{a}-{b}"]):
                raise ValueError(
                    "Public contrast disagrees with the registered thresholds"
                )
    earlier_rows = standing(earlier)[2]
    original_cells = {
        "TP67.1": [
            x["difference"] for x in earlier["reports"].values() if "difference" in x
        ],
        "TP67.analyst": [
            row[k]
            for row in earlier["standardized"]["words"].values()
            if "ownMinusOtherInSD" in row
            for k in ("ownMinusOtherInSD", "distanceBelowOneFifth")
        ],
    }
    support = {
        k: bool(cells) and all(direction(c) > 0 for c in cells)
        for k, cells in original_cells.items()
    }
    updates = predictions(rows, gate, earlier_rows, support)
    family_path = ROOT / "TP78-measurements.json"
    family = read(family_path)
    if any(family.get(k) not in (earlier_rows[k], v) for k, v in updates.items()):
        raise ValueError("The earlier TP67 family record changed")
    zone = ZoneInfo("America/Los_Angeles")
    day = datetime.fromisoformat(receipt["at"]).astimezone(zone)
    ident = f"E-TP67-AGENCY-{day:%Y%m%d}"
    supported = sum(
        "difference" in x for row in rows.values() for x in row["pairs"].values()
    )
    brief = (
        f"B/W agreement on who acted had kappa {number(r['agreement']['roster'])} ({gate}). "
        f"{supported} of 12 within-word PRIDE comparisons yielded estimates."
    )
    public = {
        k: r[k]
        for k in ("card", "agreement", "reports", "wholeWriterDraws", "sourceReceipts")
    }
    public.update(
        sourceReceiptPin=source,
        ledger=ident,
        predictions=updates,
        originalLedger=earlier["ledger"],
        license=earlier["license"],
        productionAdmission=False,
    )
    put(PUBLIC_FILE, public)
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ident,
            "date": day.date().isoformat(),
            "family": "Round 37 agency and PRIDE",
            "claims": ["T11"],
            "question": "Does the chat PRIDE forecast vary by whose doing B marked?",
            "data": PUBLIC_FILE.as_posix(),
            "estimate": {"sourceReceiptPin": source, "predictions": updates},
            "interval": "2,000 whole-writer resamples for each eligible within-word contrast.",
            "bar": "At least 50 reports per side. Roster-wide B/W reliability governs use under CW.",
            "verdict": brief,
            "limit": "Fixed PRIDE forecasts and reader-attributed agency in chat reports with four assigned emotion words.",
        },
    )
    current = CARD.read_text("utf8")
    if ident not in current:
        lines = [
            "## Direct agency judgments",
            "",
            brief,
            "",
            "| Word | Own | Close | Other | No one | Invalid | Own − close | Own − other | Close − other |",
            "|---|---:|---:|---:|---:|---:|---|---|---|",
        ]
        for word, row in rows.items():
            counts = [
                str(row["counts"][k])
                for k in ("own", "close", "other", "no_one", "invalid")
            ]
            values = [
                interval(row["pairs"][f"{a}-{b}"].get("difference", {}))
                for a, b in PAIRS
            ]
            lines.append("| " + " | ".join([word, *counts, *values]) + " |")
        lines += [
            "",
            f"[Group means, standardized differences and source receipt · {ident}](../../../engine/validation/{PUBLIC_FILE.name})",
        ]
        write_text(CARD, current.rstrip() + "\n\n" + "\n".join(lines) + "\n")
    family.update(updates)
    write(family_path, family)
    write_text(SHEET, render(family))
    for path, link in (
        (STATUS, CARD.as_posix()),
        (SCOREBOARD, CARD.relative_to("docs").as_posix()),
    ):
        contents = path.read_text("utf8")
        if ident not in contents:
            title, rest = contents.split("\n", 1)
            write_text(
                path,
                f"{title}\n\n**{day:%B %d} · TP67.** {brief} [{ident}]({link})\n\n"
                + rest.lstrip("\n"),
            )
    lines = RETURN.read_text("utf8").splitlines()
    lines[0] = live_line(states)
    index = next(i for i, line in enumerate(lines) if line.startswith("| TP67 ·"))
    lines[index] = (
        f"| TP67 · Whose rise | {brief} The original responsibility contrasts and direct agency tables are filed together. | [TP67 · {ident}](result-sheets/TP67.md) |"
    )
    write_text(RETURN, "\n".join(lines) + "\n")
    proof = {
        "public": PUBLIC_FILE.as_posix(),
        "sha256": pin(PUBLIC_FILE),
        "sourceReceiptPin": source,
        "ledger": ident,
    }
    write(ROOT / f"{STAGE}-landing.json", proof)
    return proof
