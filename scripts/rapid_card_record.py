"""File the four prepared Round 37 aggregate returns and refresh their registered family entries."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapid_cpu_dispatch import ROOT
from rapid_family import SHEET, render
from rapid_head_check import pin, read
from rapid_land import registered_card, sentence_results
from word_table_lane import write

RETURN = Path("docs/exchange/THEORY_RETURN_2026-11-29.md")
SCOREBOARD = Path("docs/ENGINE_SCOREBOARD.md")
STATUS = Path("STATUS.md")
NAMES = {"TP70": "TP70", "TP64": "TP64", "TP65": "TP65", "TP77-original": "TP77"}


def number(x):
    return "unavailable" if x is None else f"{x:.3f}"


def interval(r):
    ci = r.get("interval")
    return number(r.get("value")) + (
        f" [{number(ci[0])}, {number(ci[1])}]" if ci else ""
    )


def group_text(r):
    data = r["sources"]
    rows = {s: data[s]["full"] for s in ("chat", "blog")}
    floors = {s: x["floors"]["rot"]["count"] for s, x in rows.items()}
    groups = {s: x["groups"] for s, x in rows.items()}
    tables = [
        "| Groups | Chat statistic | Chat ROT band | Blog statistic | Blog ROT band |",
        "|---|---:|---:|---:|---:|",
    ]
    for group in ("map", "thread", "print", "meaning"):
        line = [group]
        for s in ("chat", "blog"):
            v = groups[s][group]
            line.extend(
                [
                    interval(v["trained"]),
                    f"{v['rot']['lower']:.3f} to {v['rot']['upper']:.3f}",
                ]
            )
        tables.append("| " + " | ".join(line) + " |")
    measured = {}
    for row, kind in (("TP70.1", "map"), ("TP70.3", "printMinusThread")):
        if kind == "map":
            tests = [g["map"]["rot"] for g in groups.values()]
            margins = [t["marginAboveBand"] for t in tests]
        else:
            tests = [v["excessComparisons"][kind] for v in rows.values()]
            margins = tests
        verdict = (
            "Unresolved under CX"
            if any(t["nearBar"] for t in tests)
            else "Both margins are positive"
            if all(m["interval"][0] > 0 for m in margins)
            else "Registered direction missed"
            if any(m["interval"][1] < 0 for m in margins)
            else "Unresolved"
        )
        measured[row] = {
            "p": max(t["orientationP"] for t in tests),
            "estimate": "Chat and blog margins "
            + ", ".join(interval(m) for m in margins),
            "verdict": verdict,
        }
    compare = [v["excessComparisons"]["threadMinusMap"] for v in rows.values()]
    floor_text = f"Against rotated heads, the component floor was {floors['chat']} on chat texts and {floors['blog']} on blog author means."
    comparisons = ", ".join(interval(m) for m in compare)
    measured["TP70.2"] = {
        "p": None,
        "estimate": "Thread-minus-map excess in chat and blogs was "
        + comparisons
        + ".",
        "verdict": "Group and pair results filed. The body split has no specified decision threshold.",
    }
    measured["TP70.analyst"] = {
        "p": None,
        "estimate": floor_text,
        "verdict": "Floor and grouping predictions filed. The fourth group has no registered equivalence margin.",
    }
    map_margins = ", ".join(
        interval(g["map"]["rot"]["marginAboveBand"]) for g in groups.values()
    )
    summary = (
        floor_text
        + " The map’s margins above the rotated bands were "
        + map_margins
        + " in chat and blogs, respectively."
    )
    lines = [
        summary,
        "",
        *tables,
        "",
        "The comparison of standardized excess for the thread’s three groups versus the map was "
        + ", ".join(interval(m) for m in compare)
        + " in chat and blogs, respectively. The aggregate also gives the first-component sensitivity, resampled floors, descriptive pair table and any retained varimax assignments.",
    ]
    return summary, lines, measured


def channel_text(r):
    data = r["sources"]
    wanted = data["go"]["heads"]["wanting"]["fixed"]
    shame = data["envent"]["jointShame"]
    s = (
        "Forum desire versus optimism and excitement had AUC "
        + ", ".join(interval(wanted[k]["all"]) for k in ("optimism", "excitement"))
        + "."
    )
    joint = shame["writerHeldOut"]
    lines = [
        s,
        "",
        "The joint SHAME head scored all "
        + f"{shame['rows']:,} held-out events and {data['go']['jointShame']['rows']:,} held-out forum comments. "
        + "Event shame or guilt versus other labels had AUC "
        + interval(shame["reportHeldOut"])
        + " by held-out report and "
        + interval(joint)
        + " by held-out writer. The forum has no shame or guilt gold label.",
        "",
        "| Source | Matched reports with known writers | Writers | Loudest three | Quietest three |",
        "|---|---:|---:|---|---|",
    ]
    for src, v in data.items():
        n = v["census"]
        lines.append(
            f"| {src} | {n['assessedReports']:,} | {n['assessedWriters']:,} | "
            + ", ".join(x["word"] for x in v["tp59Loudest"])
            + " | "
            + ", ".join(x["word"] for x in v["tp59Quietest"])
            + " |"
        )
    want = r["readings"]["forumWanting"]["all"]
    pooled = {
        "p": None,
        "estimate": s,
        "verdict": "Individual label comparisons filed. PLAY has no outside gold or equivalence margin.",
    }
    tests = [wanted[k]["all"] for k in ("optimism", "excitement")]
    sh_test = [shame.get(k, {}) for k in ("reportHeldOut", "writerHeldOut")]
    complete = all(t.get("standardError") is not None for t in [*tests, *sh_test])
    verdict = "Unresolved"
    if complete and not any(t["nearPoint70"] for t in [*tests, *sh_test]):
        if all(t["intervalBelowPoint70"] for t in tests) and all(
            t["intervalClearsPoint70"] for t in sh_test
        ):
            verdict = "Both registered directions hold"
        elif any(t["intervalClearsPoint70"] for t in tests) or all(
            t["intervalBelowPoint70"] for t in sh_test
        ):
            verdict = "Registered conjunction missed"
    result = {
        "TP64.1": pooled,
        "TP64.analyst": {
            "p": max(want["jointP"], *(t["pAbovePoint70"] for t in sh_test))
            if complete
            else None,
            "estimate": s
            + " Event SHAME AUC "
            + interval(joint)
            + " on held-out writers.",
            "verdict": verdict,
        },
    }
    return s, lines, result


def timing_text(r):
    wording = (
        "The original sentence timing comparisons are "
        + r["interpretation"].lower()
        + "."
    )
    lines = [wording, ""]
    for key, val in r["CW"].items():
        lines.append(f"- B/W {key} kappa was {number(val['kappa'])} ({val['status']}).")
    lines.extend(
        [
            "",
            "| Source | B ahead | B landed | B ongoing | B neither | Worry, ahead minus landed |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for s, v in r["sources"].items():
        n = v["B"]["counts"]
        a = v["B"]["contrasts"]["aheadMinusLanded"]["outputs"]
        lines.append(
            f"| {s} | {n['ahead']:,} | {n['already']:,} | {n['ongoing']:,} | {n['none']:,} | {interval(a.get('worry', {}))} |"
        )
    measured = {}
    for key in ("TP65.1", "TP65.2", "TP65.analyst"):
        contrasts = []
        for v in r["sources"].values():
            t = v["B"]["contrasts"]
            if key == "TP65.1":
                contrasts.extend(
                    (m, 1)
                    for name, m in t["changeMinusNeither"]["outputs"].items()
                    if name != "worry"
                )
            elif key == "TP65.2":
                for ch in (
                    "FEAR",
                    "SEEKING",
                    "LUST",
                    "SADNESS",
                    "RAGE",
                    "PRIDE",
                    "worry",
                ):
                    sign = 1 if ch in ("FEAR", "SEEKING", "LUST", "worry") else -1
                    contrasts.append(
                        (t["aheadMinusLanded"]["outputs"].get(ch, {}), sign)
                    )
                    if ch != "worry":
                        other = (
                            "aheadMinusNeither" if sign == 1 else "landedMinusNeither"
                        )
                        contrasts.append((t[other]["outputs"].get(ch, {}), 1))
            else:
                contrasts.append(
                    (t["aheadMinusLanded"]["outputs"].get("SADNESS", {}), -1)
                )
        valid = bool(contrasts) and all(
            m.get("standardError") is not None for m, _ in contrasts
        )
        p = (
            max(m["pAboveZero" if sign > 0 else "pBelowZero"] for m, sign in contrasts)
            if valid
            else None
        )
        verdict = "Unresolved"
        if not r["interpretation"].startswith("Eligible"):
            verdict = r["interpretation"]
        elif key == "TP65.analyst":
            verdict = "FEAR has no registered equivalence margin"
            p = None
        elif valid and not any(m["nearZero"] for m, _ in contrasts):
            lower = [min(sign * v for v in m["interval"]) for m, sign in contrasts]
            upper = [max(sign * v for v in m["interval"]) for m, sign in contrasts]
            verdict = (
                "Both sources clear all directions"
                if min(lower) > 0
                else "Registered direction missed"
                if min(upper) < 0
                else "Unresolved"
            )
        measured[key] = {
            "p": p,
            "estimate": "Original chat and event comparisons, by writer. Additional sources still pending.",
            "verdict": verdict,
        }
    lines.extend(
        [
            "",
            "The aggregate contains both readers, the agreement sensitivity and the two comparisons with the writers’ foreseeability ratings.",
        ]
    )
    return wording, lines, measured


def agreement_text(r):
    bw = r["sources"]["all"]["B/W"]
    s = (
        "On the original sentences, B/W kappa was "
        + ", ".join(
            f"{number(bw[k]['value'])} for {k} ({bw[k]['CW']})"
            for k in ("change", "when", "whose")
        )
        + "."
    )
    lines = [
        s,
        "",
        "| Readers | Field | Valid pairs | Kappa and 95% writer interval |",
        "|---|---|---:|---:|",
    ]
    for pair, fields in r["sources"]["all"].items():
        for name, t in fields.items():
            lines.append(f"| {pair} | {name} | {t['jointlyValid']:,} | {interval(t)} |")
    lines.extend(
        [
            "",
            "The aggregate includes the counts behind every kappa and the results by source. Standing judgments, new sources and the comparison with writers’ own ratings have separate checks.",
        ]
    )
    measured = {
        "TP77.analyst": {
            "p": None,
            "estimate": "Original B/W timing kappa " + interval(bw["when"]) + ".",
            "verdict": "The original timing mark is "
            + bw["when"]["CW"]
            + ". The earned-standing clause awaits its own study.",
        }
    }
    return s, lines, measured


def live_line(states):
    parts = []
    for label, lane in (
        ("Spark", states["spark"]),
        ("the workstation GPU", states["workstation"]["gpu"]),
    ):
        if lane["state"] == "running":
            n = (
                f" ({lane['rows']:,}/{lane['total']:,})"
                if "rows" in lane and "total" in lane
                else ""
            )
            parts.append(f"{label} is running {lane['job']}{n}")
        else:
            parts.append(
                f"{label} has no verified active ToMpathy GPU worker ({lane['state']}, last {lane.get('last', 'unavailable')})"
            )
    cpu = states["workstation"]["card"]
    if cpu and cpu.startswith("TP70-block-"):
        current = "TP70 grouping block " + str(int(cpu.split("-")[2]) + 1) + " of 40"
    else:
        current = cpu.removesuffix("-a") if cpu else None
    parts.append(
        "the card queue is running " + current
        if current
        else "the card queue is "
        + (states["workstation"].get("cardIdleReason") or "between verified stages")
    )
    moment = (
        datetime.fromisoformat(states["checkedAt"])
        if "checkedAt" in states
        else datetime.now(UTC)
    )
    stamp = moment.astimezone(ZoneInfo("America/Los_Angeles")).strftime(
        "%b %d at %H:%M PT"
    )
    return (
        stamp
        + ", "
        + ", ".join(parts[:-1])
        + ", and "
        + parts[-1]
        + ". The workstation can read both held corpora. The last Spark check found no in-place route to the talk pages or recalled stories."
    )


def file_card(key, states):
    artifact = (
        sentence_results(key)
        if key in ("TP65", "TP77-original")
        else registered_card(key)
    )
    r = read(Path(artifact["public"]))
    if (
        pin(Path(artifact["public"])) != artifact["sha256"]
        or r["sourceReceiptPin"] != artifact["sourceReceiptPin"]
    ):
        raise ValueError("Public receipt binding differs")
    card = NAMES[key]
    methods = {
        "TP64": channel_text,
        "TP65": timing_text,
        "TP70": group_text,
        "TP77-original": agreement_text,
    }
    brief, lines, measured = methods[key](r)
    sheet = Path(f"docs/exchange/result-sheets/{card}.md")
    ref = Path(artifact["public"]).name
    ident = r["ledger"]

    def append_result(file, section):
        before = file.read_text("utf8")
        if ident not in before:
            file.write_text(
                before.rstrip() + "\n\n" + section.rstrip() + "\n",
                encoding="utf8",
                newline="\n",
            )

    append_result(
        sheet,
        "## Original-source results\n\n"
        + "\n".join(lines)
        + f"\n\n[Aggregate, source receipt and complete tables · {ident}](../../../engine/validation/{ref})",
    )
    for f, url in [
        (STATUS, f"docs/exchange/result-sheets/{card}.md"),
        (SCOREBOARD, f"exchange/result-sheets/{card}.md"),
    ]:
        content = f.read_text("utf8")
        if ident not in content:
            title, rest = content.split("\n", 1)
            if key == "TP70" and f == STATUS:
                rest = rest.replace(
                    " TP70 is running on the chat texts and blog author means.", "", 1
                )
            f.write_text(
                title
                + f"\n\n**November 27 · {card}.** {brief} [{ident}]({url})\n\n"
                + rest.lstrip("\n"),
                encoding="utf8",
                newline="\n",
            )
    record = RETURN.read_text("utf8").splitlines()
    record[0] = live_line(states)
    row = next(i for i, l in enumerate(record) if l.startswith(f"| {card} ·"))
    title = record[row].split("|")[1].strip()
    record[row] = f"| {title} | {brief} | [{card} · {ident}](result-sheets/{card}.md) |"
    decisions = [
        k
        for k, v in measured.items()
        if v["verdict"].startswith(
            (
                "Registered direction missed",
                "Registered conjunction missed",
                "Both margins are positive",
                "Both registered directions hold",
                "Both sources clear",
            )
        )
    ]
    if decisions and not any(l.startswith(f"**{card} · ") for l in record):
        at = record.index("## Registered predictions")
        record[at:at] = [
            f"**{card} · {', '.join(decisions)}.** "
            + brief
            + f" [{card} tables](result-sheets/{card}.md)",
            "",
        ]
    RETURN.write_text("\n".join(record) + "\n", encoding="utf8", newline="\n")
    private = ROOT / "TP78-measurements.json"
    family = read(private)
    for k, v in measured.items():
        if k in family and family[k] != v:
            raise ValueError(
                "Preserve the previously measured registered prediction " + k
            )
        family[k] = v
    write(private, family)
    SHEET.write_text(render(family), encoding="utf8", newline="\n")
    write(ROOT / (key + "-landing.json"), {**artifact, "ledger": ident})
    return artifact


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("card", choices=list(NAMES))
    args = p.parse_args()
    from rapid_lane_state import get

    print(json.dumps(file_card(args.card, get())))
