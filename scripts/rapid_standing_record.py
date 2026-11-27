"""Record the four standing-mark comparisons and complete the registered TP77 row."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapid_card_record import RETURN, SCOREBOARD, STATUS, interval, live_line
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_family import SHEET, render
from rapid_land import PUBLIC, put
from rapid_later_record import prediction, write_text
from rapid_marks import CHOICES
from tompathy_engine.eval.evidence import append
from word_table_lane import pin, read, write

CARD = Path("docs/exchange/result-sheets/TP77.md")
PUBLIC_FILE = PUBLIC / "readers-tp77-standing-2026-11.json"
FILES = (
    STATUS,
    SCOREBOARD,
    RETURN,
    CARD,
    SHEET,
    PUBLIC / "EVIDENCE_LEDGER.jsonl",
    PUBLIC_FILE,
)


def expected_range(cell, lower, upper=None):
    if cell["interval"] is None or cell.get("bootstrapSE") is None:
        return "unresolved"
    lo, hi = cell["interval"]
    se = cell["bootstrapSE"]
    bounds = (lower,) if upper is None else (lower, upper)
    if min(abs(v - cut) for v in (lo, hi) for cut in bounds) <= se:
        return "unresolved"
    if hi < lower or (upper is not None and lo >= upper):
        return "against"
    if lo >= lower and (upper is None or hi < upper):
        return "clear"
    return "unresolved"


def describe(r):
    cells = r["tables"]["all"]
    timing = r["originalTimingTail"]
    earned = cells["earned"]
    k = ", ".join(
        f"{field} {interval(cells[field])} ({cells[field]['CW']})" for field in CHOICES
    )
    brief = "Standing-mark agreement across the three sources was " + k + "."
    verdicts = (expected_range(timing, 0.60), expected_range(earned, 0.40, 0.60))
    probs = [
        timing["atOrBelowUsable"],
        earned.get("atOrAboveUsable"),
        earned.get("atOrBelowWeakFloor"),
    ]
    verdict = (
        "Both registered clauses clear."
        if all(v == "clear" for v in verdicts)
        else "Registered conjunction missed."
        if "against" in verdicts
        else "Unresolved under CX."
    )
    measurement = prediction(
        f"Original timing kappa {interval(timing)}. Earned-standing kappa {interval(earned)}.",
        verdict,
        max(probs) if all(x is not None for x in probs) else None,
        "against" in verdicts,
    )
    return brief, measurement


def file_card(out, plan, states):
    receipt = read(out / "receipt.json")
    source = confirmed(out)
    r = receipt["result"]
    if (
        receipt["registrationPin"] != pin(plan)
        or receipt["status"] != "complete"
        or receipt["card"] != "TP77-standing"
        or r != read(out / "table.json")
        or r["privateAlignmentPin"] != pin(out / "aligned.npz")
        or r["nativeReturnPin"] != pin(ROOT / "standing-return/complete.json")
        or set(r["tables"]) != {"all", "ed", "envent", "go"}
    ):
        raise ValueError("Registered terminal standing analysis differs")
    for name, table in r["tables"].items():
        n = 43021 if name == "all" else r["counts"][name]
        if set(table) != set(CHOICES) | {"earnedAmongJointRises"}:
            raise ValueError("Incomplete standing field set")
        for field, cell in table.items():
            if (
                (field in CHOICES and cell["roster"] != n)
                or sum(map(sum, cell["contingency"])) != cell["jointlyValid"]
                or sum(
                    cell[key]
                    for key in ("jointlyValid", "BOnly", "WOnly", "bothMissing")
                )
                != cell["roster"]
            ):
                raise ValueError("Standing contingency or missingness count differs")
    day = datetime.fromisoformat(receipt["at"]).astimezone(
        ZoneInfo("America/Los_Angeles")
    )
    ident = f"E-TP77-STANDING-{day:%Y%m%d}"
    brief, measurement = describe(r)
    public = {
        k: r[k]
        for k in (
            "card",
            "counts",
            "unknownForumAuthorsAsSingleComments",
            "draws",
            "fields",
            "tables",
            "readerReceipts",
            "protocols",
            "inputManifest",
            "originalTimingTail",
        )
    }
    public.update(
        sourceReceiptPin=source, ledger=ident, registeredPrediction=measurement
    )
    fam = ROOT / "TP78-measurements.json"
    family = read(fam)
    old = family.get("TP77.analyst")
    if old != measurement and (
        not old
        or old["p"] is not None
        or "earned-standing clause awaits" not in old["verdict"]
    ):
        raise ValueError("Unexpected prior TP77 family measurement")
    put(PUBLIC_FILE, public)
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ident,
            "date": day.date().isoformat(),
            "family": "Round 37 standing-mark agreement",
            "claims": ["A1", "T2", "T3"],
            "question": "How consistently do B and W mark agency, standing change, visibility and earning a rise?",
            "data": PUBLIC_FILE.as_posix(),
            "estimate": {
                "sourceReceiptPin": source,
                "agreement": {f: r["tables"]["all"][f]["value"] for f in CHOICES},
            },
            "interval": "2,000 whole-writer resamples. Unidentified forum posters are single-comment clusters.",
            "bar": "Unweighted Cohen kappa of 0.60 or greater is usable. From 0.40 to below 0.60 is weak.",
            "verdict": brief,
            "limit": "Two fixed readers can agree on an incorrect account. Writer validation is separate.",
        },
    )
    previous = CARD.read_text("utf8")
    if ident not in previous:
        lines = [
            "",
            "## Agreement on standing",
            "",
            "| Field | Jointly valid | B/W kappa [95% writer interval] | CW |",
            "|---|---:|---:|---|",
        ]
        for field, cell in r["tables"]["all"].items():
            display = (
                "Earned among joint rises"
                if field == "earnedAmongJointRises"
                else field
            )
            lines.append(
                f"| {display} | {cell['jointlyValid']:,} | {interval(cell)} | {cell['CW']} |"
            )
        lines += [
            "",
            (
                f"The source-specific tables include every contingency and missing response. {r['unknownForumAuthorsAsSingleComments']:,} "
                "held-out forum comments lacked an identified author and contributed single-comment clusters. "
                "The full earned-standing field includes the no-rise category. The joint-rise row shows agreement within rises. "
                f"[Aggregate and source receipt · {ident}](../../../engine/validation/{PUBLIC_FILE.name})"
            ),
            "",
        ]
        write_text(CARD, previous.rstrip() + "\n" + "\n".join(lines))
    family["TP77.analyst"] = measurement
    write(fam, family)
    write_text(SHEET, render(family))
    for path, link in (
        (STATUS, CARD.as_posix()),
        (SCOREBOARD, CARD.relative_to("docs").as_posix()),
    ):
        text = path.read_text("utf8")
        if ident not in text:
            head, tail = text.split("\n", 1)
            write_text(
                path,
                head
                + f"\n\n**{day:%B %d} · TP77.** "
                + brief
                + f" [{ident}]({link})\n\n"
                + tail.lstrip("\n"),
            )
    lines = RETURN.read_text("utf8").splitlines()
    lines[0] = live_line(states)
    i = next(i for i, l in enumerate(lines) if l.startswith("| TP77 ·"))
    lines[i] = (
        f"| TP77 · Reader agreement | Original sentence B/W kappa was 0.609 for change, 0.614 for timing and 0.444 for whose situation changed. {brief} | [TP77 · {ident}](result-sheets/TP77.md) |"
    )
    write_text(RETURN, "\n".join(lines) + "\n")
    proof = {
        "public": PUBLIC_FILE.as_posix(),
        "sha256": pin(PUBLIC_FILE),
        "sourceReceiptPin": source,
        "ledger": ident,
    }
    write(ROOT / "TP77-standing-landing.json", proof)
    return proof
