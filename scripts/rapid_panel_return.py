"""Write the TP63 reader extension and TP77 wording tables from verified aggregate receipts."""

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapid_card_record import RETURN, SCOREBOARD, STATUS, interval, live_line
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_family import SHEET, render
from rapid_land import PUBLIC, put
from rapid_later_record import write_text
from tompathy_engine.eval.evidence import append
from word_table_lane import core, pin, read, write


def features(r):
    if set(r["outputs"]) != set(core.FEATURES) or any(
        set(row) != set(r["targets"]) for row in r["outputs"].values()
    ):
        raise ValueError("Incomplete feature-by-trait table")
    cells = [(feat, t, c) for feat, row in r["outputs"].items() for t, c in row.items()]
    n = sum(c["pointAboveRotFamily"] for _, _, c in cells)
    feat, trait, top = max(cells, key=lambda x: abs(x[2]["value"]))
    brief = f"Across {r['writers']:,} writers and {r['reports']:,} reports, {n} of {len(cells)} feature–trait correlations exceeded the rotated family threshold of {r['bars']['rot']['family']:.3f}. The largest absolute correlation was {feat} with {trait.lower()}, {interval(top)}."
    traits = list(r["targets"])
    lines = [
        "| Reader B feature | " + " | ".join(traits) + " |",
        "|---|" + "---:|" * len(traits),
    ]
    for name, row in r["outputs"].items():
        lines.append(
            "| "
            + name.replace("_", " ")
            + " | "
            + " | ".join(interval(row[t]) for t in traits)
            + " |"
        )
    limit = "Each writer provided a few short events. The rotated reference uses the tag encoder. Each rating was cleared of assigned feeling before averaging within writer."
    return brief, lines, limit


def wordings(r):
    comparisons = ["B/C", "B/standing2", "B/standing3", "standing2/standing3"]
    fields = ["whose", "standing", "known", "earned"]
    if set(r["tables"]) != set(comparisons):
        raise ValueError("Incomplete reader or wording comparison")
    lines = [
        "| Readers or wordings | Paired valid / submitted | "
        + " | ".join(fields)
        + " |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in comparisons:
        row = r["tables"][name]
        if set(row) != set(fields) or any(
            sum(map(sum, c["contingency"])) != c["jointlyValid"] for c in row.values()
        ):
            raise ValueError("Invalid standing contingency")
        cell = row["standing"]
        lines.append(
            f"| {name} | {cell['jointlyValid']:,} / {cell['roster']:,} | "
            + " | ".join(interval(row[f]) for f in fields)
            + " |"
        )
    bc = r["tables"]["B/C"]["standing"]
    brief = f"B and C agreed on the direction of standing with kappa {interval(bc)} on {bc['jointlyValid']:,} jointly valid texts out of {bc['roster']:,}."
    return (
        brief,
        lines,
        "The two rewordings use the same fixed reader and reports. CW usability requires B/W agreement. G12 stopped before the full W panel was available.",
    )


def responsibility(r):
    rows = r["tables"]
    primary = rows["B-writer"]
    if set(rows) != {"B-writer", "B-writer-prefix", "W-writer-prefix", "B-W-prefix"}:
        raise ValueError("Missing registered comparison")
    labels = {
        "B-writer": "B and writer, all events",
        "B-writer-prefix": "B and writer, W prefix",
        "W-writer-prefix": "W and writer, W prefix",
        "B-W-prefix": "B and W, W prefix",
    }
    lines = [
        "| Comparison | Paired events | Writers | Spearman correlation (95% interval) | Cohen kappa (95% interval) | Exact 1–5 agreement |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, label in labels.items():
        c = rows[name]
        if (
            sum(map(sum, c["counts"])) != c["paired"]
            or c["rank"]["reports"] != c["paired"]
        ):
            raise ValueError("Paired counts and response table disagree")
        lines.append(
            f"| {label} | {c['paired']:,} | {c['writers']:,} | {interval(c['rank'])} | {interval(c['kappa'])} | {c['exactAgreement']:.1%} |"
        )
    brief = (
        f"Across {primary['paired']:,} recalled events from {primary['writers']:,} writers, "
        f"B’s own-responsibility rating correlated {interval(primary['rank'])} with the writer’s rating. "
        f"The two gave the same 1–5 answer on {primary['exactAgreement']:.1%} of events."
    )
    return (
        brief,
        lines,
        "The comparison measures agreement with self-reports of who caused an event. W’s saved source-order prefix covers 928 events. Its results are descriptive for that subset.",
    )


def sentences(r):
    tables = r["tables"]
    coverage = r["coverage"]
    if set(tables) != {"change", "when", "whose"} or set(coverage) != {"go", "isear"}:
        raise ValueError("Missing source or agreement table")
    if (
        any(
            c["roster"] != coverage["go"]["WSaved"]
            or sum(map(sum, c["contingency"])) != c["jointlyValid"]
            for c in tables.values()
        )
        or coverage["isear"]["WSaved"] != 0
    ):
        raise ValueError("Agreement census differs from the saved overlap")
    when = tables["when"]
    brief = f"On the saved forum prefix, B/W kappa for sentence timing was {interval(when)} on {when['jointlyValid']:,} paired sentences. ISEAR has {coverage['isear']['B']['valid']:,} valid B readings and zero W readings."
    lines = [
        "| Forum prefix | Paired | Writer clusters | Kappa (95% interval) | CW on prefix |",
        "|---|---:|---:|---:|---|",
    ]
    for field in ("change", "when", "whose"):
        c = tables[field]
        lines.append(
            f"| {field} | {c['jointlyValid']:,} | {c['clusters']:,} | {interval(c)} | {c['CW']} |"
        )
    lines.extend(
        [
            "",
            "| Source | Reader | Saved | Valid | No change | Ahead | Already | Ongoing |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, c in coverage.items():
        for role in ("B", "W"):
            row = c[role]
            n = c["sentences"] if role == "B" else c["WSaved"]
            vals = [
                n,
                row["valid"],
                *(row[k] for k in ("none", "ahead", "already", "ongoing")),
            ]
            lines.append(
                f"| {name} | {role} | " + " | ".join(f"{v:,}" for v in vals) + " |"
            )
    return (
        brief,
        lines,
        "The overlap follows the original forum order up to the workstation memory stop. Full-panel agreement and ISEAR reliability are unavailable.",
    )


def forum_contrasts(r):
    f = r["forum"]
    arms = f["tables"]
    if set(arms) != {"B", "W", "agreement"} or r["draws"] != 2000:
        raise ValueError("Unexpected forum contrast design")
    if (
        f["sentences"] + f["lastReportSentencesExcluded"]
        != r["coverage"]["go"]["WSaved"]
        or sum(arms["B"]["classCounts"].values()) + arms["B"]["outside"]
        != f["sentences"]
    ):
        raise ValueError("Incomplete forum analysis census")
    lines = [
        "| Reading | Reports with both timings | SADNESS, ahead minus landed | FEAR, ahead minus landed |",
        "|---|---:|---:|---:|",
    ]
    for name in ("B", "W", "agreement"):
        row = arms[name]["contrasts"]["aheadMinusLanded"]
        if set(row["outputs"]) != set(r["outputs"]):
            raise ValueError("Incomplete channel contrast")
        lines.append(
            f"| {name} | {row['reportsWithBothClasses']:,} | {interval(row['outputs']['SADNESS'])} | {interval(row['outputs']['FEAR'])} |"
        )
    primary = arms["B"]["contrasts"]["aheadMinusLanded"]
    both = arms["agreement"]["contrasts"]["aheadMinusLanded"]
    brief = (
        f"Among {f['reports']:,} complete forum comments, B marked both timings in {primary['reportsWithBothClasses']}. "
        f"SADNESS was lower ahead than after a change, difference {interval(primary['outputs']['SADNESS'])}. "
        f"On sentences where the readers agreed, the difference was {interval(both['outputs']['SADNESS'])}."
    )
    return (
        brief,
        lines,
        "All three B/W reliability checks were weak on this source-order prefix. These within-comment estimates are descriptive. ISEAR has no paired timing contrast, and Q29 has no sentence worry scores.",
    )


# stage: renderer, aggregate fields, question, registered comparison, claim IDs.
PANELS = {
    "TP63-features": (
        features,
        "originalReceipt readerReceipt readerProtocol reports writers targets bootstrapDraws bars outputs",
        "Do B’s eight event ratings track writers’ self-rated traits?",
        "Rotated family and trait-specific bars.",
        ["P5", "S3"],
    ),
    "TP77-responsibility": (
        responsibility,
        "target generationPin BReceipt WRelease WFailure ratingPins draws tables",
        "How closely do the readers’ own-responsibility ratings agree with writers’ answers?",
        "Descriptive human check on a common 1–5 scale.",
        ["T11"],
    ),
    "TP77-Q29": (
        sentences,
        "BReceipt WFailure WRelease BResponsesPin WResponsesPin alignedPin coverage tables draws",
        "How closely do B and W agree on the new sentence marks?",
        "CW thresholds on the observed overlap only.",
        ["T2", "T11"],
    ),
    "TP77-wordings": (
        wordings,
        "readerReceipts protocols draws tables inputManifest",
        "How sensitive are standing judgments to reader and prompt wording?",
        "Descriptive reader and wording checks.",
        ["T2", "T11"],
    ),
    "TP65-Q29": (
        forum_contrasts,
        "agreementReceipt coverage forum isear outputs draws",
        "How do channel scores differ on look-ahead and landed forum sentences?",
        "Weak CW marks allow descriptive comparisons on the observed prefix.",
        ["A1", "T2", "T3"],
    ),
}


def file(stage, states):
    renderer, fields, question, bar, claims = PANELS[stage]
    card = stage.split("-")[0]
    sheet = Path(f"docs/exchange/result-sheets/{card}.md")
    out = ROOT / (stage + "-a")
    source = confirmed(out)
    rec = read(out / "receipt.json")
    r = rec["result"]
    if (
        rec["card"] != stage
        or rec["status"] != "complete"
        or r != read(out / "table.json")
    ):
        raise ValueError("Analysis identity or aggregate differs")
    day = datetime.fromisoformat(rec["at"]).astimezone(ZoneInfo("America/Los_Angeles"))
    ident = f"E-{stage.upper()}-{day:%Y%m%d}"
    if set(r) != set(fields.split()):
        raise ValueError("Unexpected public aggregate fields")
    brief, lines, limit = renderer(r)
    file = PUBLIC / f"readers-{stage.lower()}-2026-11.json"
    put(file, {**r, "sourceReceiptPin": source, "ledger": ident, "limit": limit})
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ident,
            "date": day.date().isoformat(),
            "claims": claims,
            "question": question,
            "data": file.as_posix(),
            "estimate": {"result": brief, "sourceReceiptPin": source},
            "interval": "95% intervals from 2,000 whole-writer draws.",
            "bar": bar,
            "verdict": brief,
            "limit": limit,
            "family": "Round 37 reader measurements",
        },
    )
    note = sheet.read_text("utf8")
    if ident not in note:
        note = note.replace(
            "Reader B’s eight features await Q28.",
            "Reader B’s eight features appear below.",
        )
        write_text(
            sheet,
            note.rstrip()
            + "\n\n## "
            + question
            + "\n\n"
            + brief
            + "\n\n"
            + "\n".join(lines)
            + "\n\nIntervals use 2,000 whole-writer resamples. "
            + limit
            + f" [Full aggregate and source receipt · {ident}](../../../engine/validation/{file.name})\n",
        )
    for path, link in (
        (STATUS, sheet.as_posix()),
        (SCOREBOARD, sheet.relative_to("docs").as_posix()),
    ):
        note = path.read_text("utf8")
        if ident not in note:
            head, tail = note.split("\n", 1)
            write_text(
                path,
                head
                + f"\n\n**{day:%B %d} · {card}.** {brief} [{ident}]({link})\n\n"
                + tail.lstrip("\n"),
            )
    if stage == "TP63-features":
        family_file = ROOT / "TP78-measurements.json"
        family = read(family_file)
        for key in ("TP63.analyst", "TP63.2"):
            row = family[key]
            if "Q28 features remain open." in row["verdict"]:
                row["verdict"] = (
                    row["verdict"].split(" Q28")[0]
                    + " The full feature table is recorded. The worry interval crosses the trait-specific bar."
                )
                row["estimate"] += " " + brief.split(" The largest")[0]
        write(family_file, family)
    if stage == "TP65-Q29":
        family_file = ROOT / "TP78-measurements.json"
        family = read(family_file)
        for key in ("TP65.1", "TP65.2", "TP65.analyst"):
            row = family[key]
            marker = " Forum prefix contrasts are descriptive under CW."
            if marker not in row["estimate"]:
                row["estimate"] += marker
        write(family_file, family)
    write_text(SHEET, render(read(ROOT / "TP78-measurements.json")))
    note = RETURN.read_text("utf8").splitlines()
    note[0] = live_line(states)
    i = next(i for i, l in enumerate(note) if l.startswith("| " + card + " ·"))
    if ident not in note[i]:
        row = note[i].rsplit(" | ", 1)[0]
        note[i] = (
            row + " " + brief + f" | [{card} · {ident}](result-sheets/{card}.md) |"
        )
    write_text(RETURN, "\n".join(note) + "\n")
    write(
        ROOT / (stage + "-landing.json"),
        {
            "sourceReceiptPin": source,
            "public": file.as_posix(),
            "sha256": pin(file),
            "ledger": ident,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=sorted(PANELS),
    )
    parser.add_argument("observations", type=Path)
    args = parser.parse_args()
    file(args.stage, read(args.observations))
