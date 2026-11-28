"""File the TP89 record repair using released tables only."""

import json
from pathlib import Path

from rapid_family import SHEET, render

EX = Path("docs/exchange")
VALID = Path("engine/validation")


def read(path):
    return json.loads(path.read_bytes())


def append_section(path, heading, content):
    text = path.read_text("utf8").split("\n" + heading + "\n")[0].rstrip()
    path.write_text(
        text + "\n\n" + heading + "\n\n" + content.strip() + "\n",
        encoding="utf8",
        newline="\n",
    )


def main():
    dest = EX / "result-sheets"
    ledger = [
        json.loads(row)
        for row in (VALID / "EVIDENCE_LEDGER.jsonl").read_text("utf8").splitlines()
    ]
    linked = next(r for r in ledger if r["id"] == "E-TP70-20261127")
    append_section(
        dest / "TP70.md", "## Scope of the grouping result", "Limit: " + linked["limit"]
    )
    contrast = read(VALID / "readers-tp65-original-2026-11.json")["sources"]["ed"]["B"][
        "contrasts"
    ]["changeMinusNeither"]
    lines = [
        f"Reader B. {contrast['eligibleSentences']:,} eligible sentences, with both conditions in {contrast['reportsWithBothClasses']:,} reports from {contrast['writersWithBothClasses']} writers.",
        "",
        "| Output | Difference | 95% writer interval |",
        "|---|---:|---:|",
    ]
    for name, row in contrast["outputs"].items():
        if name == "worry":
            continue
        lo, hi = row["interval"]
        lines.append(f"| {name} | {row['value']:.5f} | [{lo:.5f}, {hi:.5f}] |")
    lines += [
        "",
        "Six channel intervals lie below zero and RAGE lies above zero. The intervals for PRIDE, SADNESS and SHAME include zero.",
    ]
    append_section(
        dest / "TP65.md",
        "## Chat change sentences compared with neither",
        "\n".join(lines),
    )
    SHEET.write_text(
        render(read(Path(".local/rapid-20261127/TP78-measurements.json"))),
        encoding="utf8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
