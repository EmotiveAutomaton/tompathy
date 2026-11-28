"""TP78. Keep every filed hypothesis visible at every return, including unmeasured ones."""

import argparse
import json
import math
import re
from pathlib import Path

import day_predictions

PACKET = Path("TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-27.md")
SHEET = Path("docs/exchange/result-sheets/TP78.md")


def registration():
    rows = {}
    card = None
    section = 0
    for line in PACKET.read_text("utf8").splitlines():
        heading = re.match(r"## (\d+)\.", line)
        if heading:
            section = int(heading[1])
        match = re.match(r"### (TP\d+)\.", line)
        if match:
            card = match[1]
        registered = re.match(
            r"- \*\*(?:Registered|Guess) \((.*?)\)(.*?)\.\*\* (.*)", line
        )
        analyst = re.match(r"- (TP\d+): (.*)", line)
        if section == 4 and registered:
            who, question = registered[1], registered[3]
            key = f"{card}.{1 + sum(k.startswith(card + '.') for k in rows)}"
            rows[key] = (who, question)
        elif section == 7 and analyst:
            rows[analyst[1] + ".analyst"] = ("analyst", analyst[2])
    return rows


def adjustments(pvalues):
    """Benjamini–Hochberg over the full registered family, upper bounds while open."""
    ordered = sorted((p, k) for k, p in pvalues.items() if p is not None)
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p, _ in ordered):
        raise ValueError("Invalid registered p value")
    limit = 1.0
    adjusted = {}
    for rank in range(len(ordered), 0, -1):
        p, key = ordered[rank - 1]
        limit = min(limit, p * len(pvalues) / rank)
        adjusted[key] = (rank, limit)
    return adjusted


def render(measured):
    rows = registration()
    rows.update(day_predictions.rows())
    if set(measured) - set(rows):
        raise ValueError("An unregistered hypothesis entered the family")
    bh = adjustments(
        {
            k: measured[k]["p"] if k in measured else None
            for k in rows
            if k not in day_predictions.OUTSIDE
        }
    )
    lines = [
        "# TP78 · Round 37 and 38 family table",
        "",
        "Each row retains its claimant and registered prediction. The section 7 reference to TP73–TP75 points to their existing analyst rows. Each multi-part prediction requires all of its clauses; its joint test uses the largest component p value. Individual contrasts stay on their card sheets. A tie requires a registered equivalence criterion for a positive equivalence verdict.",
        "",
        "A ring (○) marks a registered prediction. A cross (×) marks a recorded departure on at least one clause. The false discovery rate is 0.10. Pending predictions count in the family size and have no measured p value. Adjusted p values remain conservative upper bounds while the family is open. An interval endpoint within one standard error of its bar leaves the verdict unresolved.",
        "",
        "| ID | Claimant | Prediction | Estimate and interval | p | BH rank / adjusted p | Verdict |",
        "|---|---|---|---|---:|---|---|",
    ]
    for key, (who, question) in rows.items():
        result = measured.get(key, {})
        rank = bh.get(key)
        place = f"{rank[0]} / {rank[1]:.5g}" if rank else "—"
        verdict = result.get("verdict", "Pending")
        against = result.get(
            "against",
            any(
                v in verdict.lower()
                for v in (
                    "registered direction missed",
                    "registered conjunction missed",
                    "tie prediction misses",
                )
            ),
        )
        if key in day_predictions.MISSED:
            against, verdict = True, day_predictions.MISSED[key]
        if key in day_predictions.OUTSIDE and key not in measured:
            verdict = (
                "Unscored"
                if key == "TP82.lust"
                else "Outside the false discovery family"
            )
        values = [
            key,
            who,
            "○ " + question,
            result.get("estimate", "—"),
            result["p"] if result.get("p") is not None else "—",
            place,
            ("× " if against else "") + verdict,
        ]
        lines.append(
            "| " + " | ".join(str(v).replace("|", "\\|") for v in values) + " |"
        )
    lines.extend(
        [
            "",
            "The family treats predictions of unequal scientific importance as one test each.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurements", type=Path)
    args = parser.parse_args()
    values = json.loads(args.measurements.read_bytes()) if args.measurements else {}
    if (
        not args.measurements
        and SHEET.exists()
        and SHEET.read_text("utf8") != render({})
    ):
        raise ValueError(
            "Supply the existing measurements before rewriting the family table"
        )
    SHEET.write_text(render(values), encoding="utf8", newline="\n")
