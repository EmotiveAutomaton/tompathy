"""Land the matched TP73 B repeat aggregate and its single registered prediction."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapid_card_record import RETURN, SCOREBOARD, STATUS, interval, live_line
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_family import SHEET, render
from rapid_land import PUBLIC, put
from rapid_later_record import prediction, write_text
from tompathy_engine.eval.evidence import append
from word_table_lane import core, pin, read, write

CARD = Path("docs/exchange/result-sheets/TP73.md")
PUBLIC_FILE = PUBLIC / "readers-tp73-b-repeat-2026-11.json"
FILES = (
    STATUS,
    SCOREBOARD,
    RETURN,
    CARD,
    SHEET,
    PUBLIC / "EVIDENCE_LEDGER.jsonl",
    PUBLIC_FILE,
)


def describe(result):
    lines, contrasts, below, clear, opposite = [], [], 0, 0, 0
    for k in ("10", "20"):
        entry = result["k"][k]
        features = entry["features"]
        excluded = entry["excluded"]
        lines.extend(
            [
                f"### {k} posts per date half",
                "",
                (
                    f"{entry['authors']:,} whole authors contributed. {excluded['tooShort']:,} had too few posts in at least one date half and "
                    f"{excluded['missingBAnswer']:,} had a missing selected B answer."
                ),
                "",
                "| Feature | B repeat [95% writer interval] | Individual ROT band | B minus individual ROT head [paired interval] |",
                "|---|---:|---:|---:|",
            ]
        )
        for feature in core.FEATURES:
            cell = features[feature]
            delta = cell["BMinusRandomRotatedHead"]
            name = {
                "self_responsblt": "self responsibility",
                "other_responsblt": "other responsibility",
            }.get(feature, feature.replace("_", " "))
            control = cell["rot"]["individual"] if cell["rot"] else None
            band = (
                f"{control['low']:.3f} to {control['high']:.3f}"
                if control
                else "unavailable"
            )
            lines.append(
                f"| {name} | {interval(cell['B'])} | {band} | {interval(delta)} |"
            )
            if (
                control is None
                or delta["validDraws"] != result["draws"]
                or delta["spread"] is None
            ):
                continue
            contrasts.append(delta["upperTail"])
            low, high = delta["interval"]
            far = min(abs(low), abs(high)) > delta["spread"]
            below += int(control["position"] == "below")
            clear += int(control["position"] == "below" and high < 0 and far)
            opposite += int(control["position"] == "above" and low > 0 and far)
        lines.append("")
    brief = f"B fell below the rotated individual-head band in {below} of 16 feature-by-size comparisons."
    if len(contrasts) != 16:
        brief = f"B fell below the rotated individual-head band in {below} of {len(contrasts)} supported feature-by-size comparisons out of 16."
    verdict = (
        "All 16 components clear the rotated band and paired intervals."
        if clear == 16
        else "Registered conjunction missed."
        if opposite
        else "Unresolved under CX."
    )
    measurement = prediction(
        brief, verdict, max(contrasts) if len(contrasts) == 16 else None, bool(opposite)
    )
    return brief, lines, measurement


def file_card(out, plan, states):
    source = confirmed(out)
    receipt = read(out / "receipt.json")
    r = receipt["result"]
    if (
        receipt["registrationPin"] != pin(plan)
        or receipt["status"] != "complete"
        or receipt["card"] != r["card"]
        or r["card"] != "TP73-B-repeat"
    ):
        raise ValueError("Source or registration differs")
    if set(r["k"]) != {"10", "20"} or (
        r["wholeAuthors"],
        r["setsPerFamily"],
        r["headsPerSet"],
        r["draws"],
    ) != (2993, 1000, 19, 2000):
        raise ValueError(
            "Registered author return, control families, or bootstrap incomplete"
        )
    expected = {
        f"{family}-{n:04d}.npz" for family in ("iso", "rot") for n in range(0, 1000, 25)
    }
    if set(r["privateControlShards"]) != expected or any(
        pin(out / n) != h for n, h in r["privateControlShards"].items()
    ):
        raise ValueError("Private control shard inventory differs")
    public = {
        key: r[key]
        for key in (
            "card",
            "wholeAuthors",
            "draws",
            "setsPerFamily",
            "headsPerSet",
            "sourceB",
            "q20Inputs",
            "vectorReturn",
            "roster",
            "tagHeads",
        )
    }
    public["k"] = {}
    for size, entry in r["k"].items():
        if (
            pin(out / f"paired-authors-k{size}.npz") != entry["privatePairedMeansPin"]
            or entry["authors"] + sum(entry["excluded"].values()) != r["wholeAuthors"]
            or set(entry["features"]) != set(core.FEATURES)
        ):
            raise ValueError("Paired author means or feature census differs")
        public["k"][size] = {
            name: entry[name]
            for name in (
                "authors",
                "excluded",
                "features",
                "trainedMedianLinearTagRepeat",
            )
        }
    day = datetime.fromisoformat(receipt["at"]).astimezone(
        ZoneInfo("America/Los_Angeles")
    )
    ident = f"E-TP73-B-REPEAT-{day:%Y%m%d}"
    brief, lines, measurement = describe(public)
    limit = "One fixed B reader, whole blog authors with enough dated posts, and the same selected openings for every control."
    bar = "All eight features at both sizes below the individual rotated band, with clear paired intervals under CX."
    public.update(
        sourceReceiptPin=source,
        ledger=ident,
        registeredPrediction=measurement,
        scope=limit,
    )
    put(PUBLIC_FILE, public)
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ident,
            "date": day.date().isoformat(),
            "family": "Round 37 blog repeat",
            "claims": ["P2", "P3"],
            "question": "Do B's feature means repeat less across dates than the matched null heads?",
            "data": PUBLIC_FILE.as_posix(),
            "estimate": {"sourceReceiptPin": source, "TP73.1": measurement},
            "interval": "2,000 whole-author draws. Paired control gaps include variation among rotated heads.",
            "bar": bar,
            "verdict": brief,
            "limit": limit,
        },
    )
    note = CARD.read_text("utf8")
    if ident not in note:
        extra = (
            "\n\n## Measured B repeat\n\n"
            + brief
            + " "
            + measurement["verdict"]
            + "\n\n"
            + "\n".join(lines)
        )
        write_text(
            CARD,
            note.rstrip()
            + extra
            + f"\nThe aggregate also reports the isotropic bands and the medians of each control set. {limit} "
            + f"[Aggregate and source receipt · {ident}](../../../engine/validation/{PUBLIC_FILE.name})\n",
        )
    family_file = ROOT / "TP78-measurements.json"
    family = read(family_file)
    if "TP73.1" in family and family["TP73.1"] != measurement:
        raise ValueError("Preserve the earlier TP73 family record")
    family["TP73.1"] = measurement
    write(family_file, family)
    write_text(SHEET, render(family))
    for path, link in (
        (STATUS, CARD.as_posix()),
        (SCOREBOARD, CARD.relative_to("docs").as_posix()),
    ):
        old = path.read_text("utf8")
        if ident not in old:
            first, tail = old.split("\n", 1)
            write_text(
                path,
                first
                + f"\n\n**{day:%B %d} · TP73.** {brief} [{ident}]({link})\n\n"
                + tail.lstrip("\n"),
            )
    lines = RETURN.read_text("utf8").splitlines()
    lines[0] = live_line(states)
    i = next(i for i, l in enumerate(lines) if l.startswith("| TP73 ·"))
    lines[i] = (
        f"| TP73 · Whole authors | Q24 returned 2,993 whole authors. Both curiosity predictions missed. {brief} "
        f"| [TP73 · {ident}](result-sheets/TP73.md) |"
    )
    write_text(RETURN, "\n".join(lines) + "\n")
    proof = {
        "public": PUBLIC_FILE.as_posix(),
        "sha256": pin(PUBLIC_FILE),
        "sourceReceiptPin": source,
        "ledger": ident,
    }
    write(ROOT / "TP73-B-repeat-landing.json", proof)
    return proof
