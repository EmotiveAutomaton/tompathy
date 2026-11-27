"""Source-bound public tables and prediction entries for the next five Round 37 returns."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rapid_card_record import RETURN, SCOREBOARD, STATUS, interval, live_line, number
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_family import SHEET, render
from rapid_head_check import pin, read
from rapid_land import PUBLIC, put
from tompathy_engine.eval.evidence import append
from word_table_lane import write

# The keys below are the aggregate fields written by the five registered runners.
# Per-text joins and model arrays belong exclusively to their source directories.
PUBLIC_FIELDS = {
    "TP63-original": "sourceForecastPin tagsReceipt tenReceipt worryReceipt protocolPin reports writers targets linearProbabilityMaxGap constantColumnsOmitted bootstrapDraws nullSetsPerFamily nullHeadsPerSet bars outputs worryControl essayArm readerFeatures",
    "TP68": "designReceiptPin foldReceiptPins covered firstLastPlay unfittedBlend wordYardstick leadOverCovered dedicatedVsFittedPair reports writers draws playCheck scope",
    "TP69": "sourceDesignPin sourcePins sourceReports reports writers profiles linearRespect draws setsPerFamily",
    "TP66-short": "inputReceiptPin census sources wholeWriterDraws scope",
    "TP67-original": "reports draws scope",
}
STAGES = {
    "TP63-original": ("TP63-original", "tp63-outside", ["P5", "S3"]),
    "TP68": ("TP68-return", "tp68-blend", ["T4", "T7"]),
    "TP69": ("TP69", "tp69-respect", ["N1", "N2"]),
    "TP66-short": ("TP66-short", "tp66-short", ["T2", "T3"]),
    "TP67-original": ("TP67-original", "tp67-original", ["T11"]),
}


def prediction(text, verdict, p=None, against=False):
    return {"p": p, "estimate": text, "verdict": verdict, "against": against}


def direction(cell):
    if cell.get("interval") is None or cell.get("nearBar", False):
        return 0
    low, high = cell["interval"]
    return int(low > 0) - int(high < 0)


def all_above(cells):
    return (
        max(c["pAboveBar"] for c in cells)
        if cells and all("pAboveBar" in c for c in cells)
        else None
    )


def outside(r):
    table = r["outputs"]
    family = r["bars"]["rot"]["family"]
    measured = [
        (n, t, c)
        for n, row in table.items()
        for t, c in row.items()
        if c["value"] is not None
    ]
    exceed = [(n, t, c) for n, t, c in measured if c["pointAboveRotFamily"]]
    beyond = [
        (n, t, c)
        for n, t, c in exceed
        if c["intervalExcludesZero"]
        and min(abs(v) for v in c["interval"]) > family
        and not c["nearBar"]
    ]
    worry = table["worry"]["Emotional stability"]
    brief = (
        f"Across {r['writers']:,} writers, {len(exceed)} of {len(measured)} correlations exceeded the "
        f"rotated family bar of {family:.3f} in absolute value. Worry and emotional stability correlated {interval(worry)}."
    )
    limits = "Each writer supplied a few short reports. Worry uses a separate encoder. Its null reference uses the tag encoder."
    lines = [
        brief,
        "",
        "| Trait | Writers | Rotated cell bar | Strongest output by absolute correlation | Correlation and 95% interval |",
        "|---|---:|---:|---|---:|",
    ]
    for trait, count in r["targets"].items():
        best = max(
            ((name, c) for name, t, c in measured if t == trait),
            key=lambda pair: abs(pair[1]["value"]),
            default=None,
        )
        label, value = (best[0], interval(best[1])) if best else ("Unavailable", "—")
        lines.append(
            f"| {trait} | {count['available']:,} | {r['bars']['rot']['trait'][trait]:.3f} | {label} | {value} |"
        )
    lines.extend(
        [
            "",
            f"For {len(beyond)} cells the full interval lay beyond the family bar and passed the interval-distance check. Both sets of bars, every signed correlation, and the row and column leaders are in the aggregate.",
            "",
            limits
            + " The held essay data have no trait fields. Reader B’s eight features await Q28.",
        ]
    )
    expected = {
        "Openness": ("curiosity",),
        "Agreeableness": ("family", "contact", "acceptance"),
        "Extraversion": ("status", "approval", "power", "competition", "honor"),
        "Conscientiousness": ("order", "savings", "serenity"),
        "Emotional stability": ("worry", "FEAR", "SADNESS", "RAGE", "DISGUST", "SHAME"),
    }
    mapped = [
        (n, t, table[n][t])
        for t, names in expected.items()
        for n in names
        if n in table and table[n][t]["value"] is not None
    ]
    leads = [
        n
        for n, t, c in mapped
        if c["leadsRow"]
        and c["leadsColumn"]
        and (c["value"] < 0 if t == "Emotional stability" else c["value"] > 0)
    ]
    rivals = [
        ("curiosity", "Openness"),
        ("order", "Conscientiousness"),
        ("contact", "Extraversion"),
        ("contact", "Agreeableness"),
        ("acceptance", "Emotional stability"),
        ("power", "Agreeableness"),
        ("competition", "Agreeableness"),
    ]
    printed = ", ".join(f"{n}/{t} {interval(table[n][t])}" for n, t in rivals)
    clear_outside = [
        (n, t)
        for n, t, c in beyond
        if t != "Emotional stability"
        or n not in expected["Emotional stability"]
        or c["value"] >= 0
    ]
    wtext = f"Worry/stability {interval(worry)} against a rotated cell bar of {r['bars']['rot']['trait']['Emotional stability']:.3f}."
    rows = {
        "TP63.1": prediction(
            f"{len(leads)} of {len(mapped)} available mapped cells lead their row and column in the predicted direction.",
            "Individual rank and interval results filed. A simultaneous rank comparison is unavailable.",
        ),
        "TP63.2": prediction(
            f"{len(clear_outside)} cells outside the predicted negative stability links passed the family and interval checks.",
            "Registered restriction missed on the available cells."
            if clear_outside
            else "Available cells filed. Q28 features remain open.",
            against=bool(clear_outside),
        ),
        "TP63.3": prediction(
            printed,
            "Individual directions filed. The paired contact comparison has no saved interval.",
        ),
        "TP63.analyst": prediction(
            f"{len(exceed)} points above the family bar. " + wtext,
            "The no-cell clause missed on the available outputs."
            if beyond
            else "Family and cell checks filed. Q28 features remain open.",
            against=bool(beyond),
        ),
    }
    return (
        brief,
        lines,
        rows,
        "Rotated family and trait-specific bars, with whole-writer intervals.",
        limits,
    )


def blend(r):
    pair = r["unfittedBlend"]
    lead = r["leadOverCovered"]
    gain = pair["againstBestOtherPair"]
    brief = f"SHAME plus PLAY ranked {pair['rank']} of 45 pairs for embarrassed. The dedicated head’s gain over its strongest covered-word comparator was {interval(lead)} AUC."
    limits = "These are assigned chat words. The chat vocabulary supplies no positive PLAY label to check that output independently."
    times = r["firstLastPlay"]
    component = f"Last minus first PLAY was {interval(times['embarrassed'])} for embarrassed and {interval(times['ashamed'])} for ashamed."
    lines = [
        brief,
        "",
        "The pair’s AUC margin over its strongest competitor was "
        + interval(gain)
        + ", and its margin over the better single output was "
        + interval(pair["againstBetterSingle"])
        + ".",
        "",
        component,
        "",
        "The dedicated head minus the fitted SHAME and PLAY pair was "
        + interval(r["dedicatedVsFittedPair"]["dedicatedMinusPair"])
        + ". In the supplied simulation a dedicated head led a pure blend by 0.19 on this descriptive comparison.",
        "",
        limits,
    ]
    pair_loss = direction(gain) < 0
    own = direction(lead)
    rows = {
        "TP68.1": prediction(
            brief + " " + component,
            "Registered conjunction missed."
            if pair_loss or own > 0
            else "Timing and both discrimination tests filed. The full conjunction is unresolved.",
            against=pair_loss or own > 0,
        ),
        "TP68.2": prediction(
            "Embarrassed gain less the largest covered gain " + interval(lead) + ".",
            {
                1: "Gain clears the strongest comparator.",
                0: "Unresolved under CX.",
                -1: "Registered direction missed.",
            }[own],
            lead.get("pAboveBar"),
            own < 0,
        ),
        "TP68.analyst": prediction(
            brief,
            "Both directional contrasts lie below zero."
            if pair_loss and own < 0
            else "Registered conjunction missed."
            if direction(gain) > 0 or own > 0
            else "Unresolved under CX.",
            against=direction(gain) > 0 or own > 0,
        ),
    }
    return (
        brief,
        lines,
        rows,
        "Rank first among 45 pairs or exceed all 15 covered gains on paired writer draws, as specified for each account.",
        limits,
    )


def respect(r):
    data = r["profiles"]
    a = [
        w for w, c in data.items() if c["CompetenceMinusRespect"]["pointAtLeastHalfSD"]
    ]
    b = [
        w for w, c in data.items() if c["RespectMinusacceptance"]["pointAtLeastHalfSD"]
    ]
    brief = f"Across {r['reports']:,} chat situations, Competence and Respect lifts differed by at least half a standard deviation for {len(a)} of 32 words. Respect and acceptance differed by that much for {len(b)}."
    lines = [
        brief,
        "",
        "Competence versus Respect at that distance: " + (", ".join(a) or "none") + ".",
        "Respect versus acceptance at that distance: " + (", ".join(b) or "none") + ".",
        "",
        "| Predicted word | Competence lift | Respect lift | Acceptance lift |",
        "|---|---:|---:|---:|",
    ]
    only_respect = ("embarrassed", "ashamed", "jealous")
    only_competence = ("prepared", "content")
    both = ("proud", "confident")
    contradicted = []
    for word in (*only_respect, *only_competence, *both):
        c = data[word]
        lines.append(
            "| "
            + " | ".join(
                [
                    word,
                    *(
                        interval(c[k]["lift"])
                        for k in ("Competence", "Respect", "acceptance")
                    ),
                ]
            )
            + " |"
        )
        comp, resp = (direction(c[k]["lift"]) for k in ("Competence", "Respect"))
        if (
            (word in only_respect and (resp < 0 or comp > 0))
            or (word in only_competence and (comp < 0 or resp > 0))
            or (word in both and (resp < 0 or comp < 0))
        ):
            contradicted.append(word)
    limits = "The comparisons group different situations by assigned word. Equal or absent lifts have no registered equivalence margin."
    lines.extend(
        [
            "",
            "The complete table gives goal support, all word means, paired lift differences and the linear Respect orientation controls.",
            "",
            limits,
        ]
    )
    finding = (
        ("Directions conflict for " + ", ".join(contradicted) + ".")
        if contradicted
        else "Individual directions filed."
    )
    return (
        brief,
        lines,
        {
            "TP69.1": prediction(
                finding,
                "Registered conjunction missed."
                if contradicted
                else "The absent-rise clauses remain unresolved.",
                against=bool(contradicted),
            )
        },
        "Paired lifts differing by at least 0.5 source SD.",
        limits,
    )


def loss(r):
    sources = r["sources"]
    measured = {}
    lines = [
        "| Source | Loss texts matched on length | SADNESS minus FEAR, loss less other | SADNESS minus RAGE, loss less other | Draws retained |",
        "|---|---:|---:|---:|---:|",
    ]
    for s, cells in sources.items():
        c = cells["comparisons"]
        fear = c["sadnessMinusFear"]
        measured[s] = fear.get("difference", {})
        rage = c["sadnessMinusRage"].get("difference", {})
        lines.append(
            f"| {s} | {fear.get('matchedLossTexts', 0):,} | {interval(measured[s])} | {interval(rage)} | {number(fear.get('drawCoverage'))} |"
        )
    brief = (
        "After matching sentence counts, the SADNESS-minus-FEAR timing difference between loss and other texts was "
        + interval(measured["ed"])
        + " in chat and "
        + interval(measured["envent"])
        + " in recalled events."
    )
    limits = "Short reports use assigned feelings as a proxy for loss. The comparisons describe positions within written reports."
    lines = [
        brief,
        "",
        *lines,
        "",
        "The aggregate gives both sources’ census by length, peak-in-thirds shares, exact-length controls, draw coverage and within-text shuffles. Disbelief has no measured output for the published rival account.",
        "",
        limits,
    ]
    signs = [direction(measured[k]) for k in ("ed", "envent")]
    rows = {
        "TP66.1": prediction(
            brief,
            "Both short-source timing directions are positive."
            if signs == [1, 1]
            else "Short-source timing contrasts filed. Longer sources remain open.",
        ),
        "TP66.2": prediction(
            brief,
            "Recalled-event direction missed."
            if signs[1] < 0
            else "Short-source contrasts filed. A null chat effect has no equivalence margin.",
            against=signs[1] < 0,
        ),
        "TP66.analyst": prediction(
            brief,
            "Short-source no-clear-difference clause missed."
            if any(signs)
            else "Short-source intervals filed. The blog clause awaits Q31.",
            against=any(signs),
        ),
    }
    return (
        brief,
        lines,
        rows,
        "SADNESS-minus-FEAR centre difference relative to same-length controls, with paired whole-writer intervals.",
        limits,
    )


def standing(r):
    words = r["reports"]
    scale = r["standardized"]["words"]
    used = {w: c for w, c in words.items() if "difference" in c}
    raw = [c["difference"] for c in used.values()]
    concise = ", ".join(w + " " + interval(c["difference"]) for w, c in used.items())
    brief = (
        "Own minus other responsibility in mean PRIDE was "
        + (concise or "unavailable for all four words")
        + "."
    )
    lines = [
        brief,
        "",
        "| Word | Own | Other | Ties | Invalid | Difference in within-word SD |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    criteria = []
    for w, c in words.items():
        scaled = scale[w]
        effect = scaled.get("ownMinusOtherInSD", {})
        if effect:
            criteria.extend([effect, scaled["distanceBelowOneFifth"]])
        lines.append(
            f"| {w} | {c['own']} | {c['other']} | {c['ties']} | {c['invalid']} | {interval(effect)} |"
        )
    limits = "Reader B supplied the responsibility division. The two-group split cannot distinguish someone close from another person."
    lines.extend(["", r["standardized"]["scale"], "", limits])
    good = (
        bool(criteria)
        and len(criteria) == 2 * len(used)
        and all(direction(c) > 0 for c in criteria)
    )
    bad = any(direction(c) < 0 for c in criteria)
    scaled_text = ", ".join(
        w + " " + interval(c["ownMinusOtherInSD"])
        for w, c in scale.items()
        if "ownMinusOtherInSD" in c
    )
    rows = {
        "TP67.1": prediction(
            brief,
            "Original responsibility contrast filed. Direct standing marks await Q27 and G12.",
            all_above(raw),
            any(direction(c) < 0 for c in raw),
        ),
        "TP67.2": prediction(
            brief,
            "A zero difference has no preregistered equivalence margin. Direct standing marks remain open.",
            against=any(direction(c) != 0 for c in raw),
        ),
        "TP67.3": prediction(
            "Original ratings distinguish two groups.",
            "The three-level ordering awaits valid standing marks.",
        ),
        "TP67.analyst": prediction(
            scaled_text or "No eligible word.",
            "Both bounds clear for eligible words."
            if good
            else "Registered bound missed."
            if bad
            else "Unresolved under CX.",
            all_above(criteria) if len(criteria) == 2 * len(used) else None,
            bad,
        ),
    }
    return (
        brief,
        lines,
        rows,
        "At least 50 texts per side. For the analyst, the own-minus-other mean difference must lie between zero and 0.2 within-word SD.",
        limits,
    )


SUMMARIES = {
    "TP63-original": outside,
    "TP68": blend,
    "TP69": respect,
    "TP66-short": loss,
    "TP67-original": standing,
}


def current_lanes():
    from rapid_lane_state import get, live

    state = get()
    workstation = state["workstation"]
    if workstation["card"] is None:
        for name in (
            "sentence-card-queue",
            "outside-card-queue",
            "word-card-queue",
            "pride-scale-queue",
        ):
            folder = ROOT / name
            if not (folder / "registration.json").exists():
                continue
            if (folder / "stopped.json").exists() and not (
                folder / "complete.json"
            ).exists():
                workstation["cardIdleReason"] = (
                    "paused after " + name + " reported a stop"
                )
            for stage in read(folder / "registration.json")["stages"]:
                job = ROOT / (stage + "-a")
                if (
                    (job / "owner.json").is_file()
                    and not (job / "released.json").exists()
                    and live(read(job / "owner.json")["native"])
                ):
                    workstation.update(card=job.name, cardIdleReason=None)
                    return state
    return state


def source_result(key):
    stage, _, _ = STAGES[key]
    folder = ROOT / (stage + "-a")
    source = confirmed(folder)
    receipt = read(folder / "receipt.json")
    original = receipt["result"]
    table = folder / ("tables.json" if key == "TP68" else "table.json")
    if (
        receipt["card"] != stage
        or receipt["status"] != "complete"
        or original["card"] != key
        or original["productionAdmission"] is not False
        or original != read(table)
    ):
        raise ValueError("Terminal aggregate, job identity or source table differs")
    public = {k: original[k] for k in PUBLIC_FIELDS[key].split()}
    if key == "TP67-original":
        folder = ROOT / "TP67-scale-a"
        scale_pin = confirmed(folder)
        saved = read(folder / "receipt.json")
        extra = saved["result"]
        if (
            saved["card"] != "TP67-scale"
            or extra["card"] != "TP67-scale"
            or extra["inputReceiptPin"] != source
            or extra != read(folder / "table.json")
            or set(extra["words"]) != set(original["reports"])
        ):
            raise ValueError(
                "The verified scale supplement does not bind the original groups"
            )
        public.update(
            inputReceiptPin=original["sourceReceiptPin"],
            scaleReceiptPin=scale_pin,
            standardized={k: extra[k] for k in ("scale", "draws", "words")},
        )
    public.update(card=key, sourceReceiptPin=source, productionAdmission=False)
    if key != "TP63-original":
        public["license"] = "EmpatheticDialogues used for research under CC BY-NC 4.0."
    return public, receipt["at"]


def write_text(path, value):
    path.write_text(value, encoding="utf8", newline="\n")


def file_card(key, states):
    _, slug, claims = STAGES[key]
    card = key.split("-")[0]
    public, completed = source_result(key)
    day = datetime.fromisoformat(completed).astimezone(ZoneInfo("America/Los_Angeles"))
    ident = f"E-{key.upper()}-{day:%Y%m%d}"
    public["ledger"] = ident
    brief, lines, measured, bar, limit = SUMMARIES[key](public)
    private_family = ROOT / "TP78-measurements.json"
    family = read(private_family)
    for k, v in measured.items():
        if k in family and family[k] != v:
            raise ValueError("Preserve the earlier family entry for " + k)
    family.update(measured)
    family_text = render(family)
    file = PUBLIC / f"readers-{slug}-2026-11.json"
    sheet = Path(f"docs/exchange/result-sheets/{card}.md")
    put(file, public)
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": ident,
            "date": day.date().isoformat(),
            "family": "Round 37 " + card,
            "claims": claims,
            "question": sheet.read_text("utf8").splitlines()[0].removeprefix("# "),
            "data": file.as_posix(),
            "estimate": {
                "sourceReceiptPin": public["sourceReceiptPin"],
                "predictions": measured,
            },
            "interval": "95% whole-writer percentile intervals. Exact draw counts and coverage are in the aggregate.",
            "bar": bar,
            "verdict": brief,
            "limit": limit,
        },
    )
    text = sheet.read_text("utf8")
    if ident not in text:
        predictions = ["", "### Registered predictions", ""] + [
            f"- ○ {k}" + (" ×" if v["against"] else "") + ". " + v["verdict"]
            for k, v in measured.items()
        ]
        write_text(
            sheet,
            text.rstrip()
            + "\n\n## Measured results\n\n"
            + "\n".join([*lines, *predictions])
            + f"\n\n[Aggregate and source receipt · {ident}](../../../engine/validation/{file.name})\n",
        )
    for path, link in (
        (STATUS, sheet.as_posix()),
        (SCOREBOARD, sheet.relative_to("docs").as_posix()),
    ):
        text = path.read_text("utf8")
        if ident not in text:
            first, tail = text.split("\n", 1)
            write_text(
                path,
                first
                + f"\n\n**{day:%B %d} · {card}.** {brief} [{ident}]({link})\n\n"
                + tail.lstrip("\n"),
            )
    records = RETURN.read_text("utf8").splitlines()
    records[0] = live_line(states)
    i = next(i for i, l in enumerate(records) if l.startswith("| " + card + " ·"))
    title = records[i].split("|")[1].strip()
    records[i] = f"| {title} | {brief} | [{card} · {ident}](result-sheets/{card}.md) |"
    against = [k for k, v in measured.items() if v["against"]]
    if against and not any(l.startswith("**" + card + " · ") for l in records):
        i = records.index("## Registered predictions")
        records[i:i] = [
            f"**{card} · {', '.join(against)}.** {brief} [Tables](result-sheets/{card}.md)",
            "",
        ]
    write_text(RETURN, "\n".join(records) + "\n")
    write(private_family, family)
    write_text(SHEET, family_text)
    proof = {
        "public": file.as_posix(),
        "sha256": pin(file),
        "sourceReceiptPin": public["sourceReceiptPin"],
    }
    write(ROOT / (key + "-landing.json"), {**proof, "ledger": ident})
    return proof
