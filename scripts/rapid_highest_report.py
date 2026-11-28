"""Render TP61(a) from its public writer-level estimates and fixed control bands."""


def render(r):
    delta = r["trained"]["difference"]
    lo, hi = delta["interval"]
    rot = r["controls"]["rot"]["difference"]
    paired, dealt = (r["trained"][name]["value"] for name in ("paired", "dealt"))
    brief = (
        f"The same group ranked highest for {paired:.1%} of {r['authors']:,} writers, "
        f"against {dealt:.1%} under random dealing. The excess was {delta['value']:.1%} "
        f"[{lo:.1%}, {hi:.1%}], {rot['position']} the rotated band "
        f"[{rot['low']:.1%}, {rot['high']:.1%}]."
    )
    lines = [
        "| Measure | Trained (95% writer interval) | Independent band · percentile | Rotated band · percentile |",
        "|---|---:|---:|---:|",
    ]
    for k, name in (
        ("paired", "Same writer"),
        ("dealt", "Random dealing"),
        ("difference", "Excess over dealing"),
    ):
        row = r["trained"][k]
        low, high = row["interval"]
        cells = [name, f"{row['value']:.2%} [{low:.2%}, {high:.2%}]"]
        for family in ("iso", "rot"):
            b = r["controls"][family][k]
            cells.append(
                f"[{b['low']:.2%}, {b['high']:.2%}] · {b['trainedPercentile']:.1f}"
            )
        lines.append("| " + " | ".join(cells) + " |")
    limit = (
        "The registered inside-band prediction missed on the point estimate. The lower writer interval "
        "is within one bootstrap standard error of the upper rotated threshold, leaving the comparison "
        "unresolved under CX. Repetition can reflect stable differences in writing style or subject matter."
    )
    return brief, lines, limit


def land(states):
    from rapid_cpu_dispatch import ROOT, confirmed
    from rapid_panel_return import PANELS, file
    from word_table_lane import read, write

    stage = "TP61-highest"
    folder = ROOT / (stage + "-a")
    confirmed(folder)
    r = read(folder / "receipt.json")["result"]
    note = read(ROOT / "TP78-measurements.json")
    diff = r["trained"]["difference"]
    rot = r["controls"]["rot"]["difference"]
    for key in ("TP61.1", "TP61.analyst"):
        if "Part (a) remains open." in note[key]["verdict"]:
            note[key]["verdict"] = note[key]["verdict"].replace(
                "Part (a) remains open.",
                "The (a) estimate exceeds ROT. Its interval is close to the bar under CX.",
            )
            note[key]["estimate"] += (
                f" (a) excess {diff['value']:.5f} {diff['interval'][0]:.5f}–{diff['interval'][1]:.5f}, ROT {rot['low']:.5f}–{rot['high']:.5f}."
            )
    write(ROOT / "TP78-measurements.json", note)
    PANELS[stage] = (
        render,
        "authors openings distinctOpenings vectorReceipt scaleReceipt TP46Receipt headPin groups draws setsPerFamily trained controls originalTP46",
        "Does a writer’s highest group repeat beyond random dealing?",
        "Trained excess inside the rotated control band.",
        ["P2", "P3", "P5"],
    )
    file(stage, states)
