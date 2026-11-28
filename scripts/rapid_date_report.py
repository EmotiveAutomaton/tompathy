"""Aggregate reporting for TP61's four dated TP45 comparisons."""

METRICS = {
    "meanRepeat": "Mean head repeat",
    "firstOne": "Top-one accuracy",
    "firstTen": "Top-ten accuracy",
    "firstOneGain": "Top-one gain",
    "firstTenGain": "Top-ten gain",
}


def render(r):
    at_five = r["sizes"]["5"]
    gain = at_five["trained"]["firstTenGain"]
    rot = at_five["controls"]["rot"]["firstTenGain"]
    repeat = at_five["trained"]["meanRepeat"]
    brief = (
        f"At five openings per half, the trained heads repeated at r = {repeat['value']:.3f}. "
        f"Their top-ten matching gain was {gain['value']:.1%} "
        f"[{gain['interval'][0]:.1%}, {gain['interval'][1]:.1%}], {rot['position']} the rotated control band "
        f"[{rot['low']:.1%}, {rot['high']:.1%}]."
    )
    lines = [
        "| Openings per half | Writers | Measure | Trained [95% writer interval] | Independent 95% band | Rotated 95% band | Rotated percentile |",
        "|---:|---:|---|---:|---:|---:|---:|",
    ]
    for k in ("5", "10", "20", "40"):
        cell = r["sizes"][k]
        for metric, name in METRICS.items():
            v = cell["trained"][metric]
            a, b = (cell["controls"][f][metric] for f in ("iso", "rot"))
            lines.append(
                f"| {k} | {cell['authors']:,} | {name} | {v['value']:.4f} [{v['interval'][0]:.4f}, {v['interval'][1]:.4f}] | [{a['low']:.4f}, {a['high']:.4f}] | [{b['low']:.4f}, {b['high']:.4f}] | {b['trainedPercentile']:.1f} |"
            )
    return (
        brief,
        lines,
        "Matching identifies an author within the original candidate fold. Persistent style and topic can also distinguish writers.",
    )


def land(states):
    from rapid_panel_return import PANELS, file

    PANELS["TP61-date-matching"] = (
        render,
        "vectorReceipt headPin TP45profiles TP45receipt draws setsPerFamily sizes",
        "How well do linear tags repeat and match writers across dates?",
        "Read matching at five openings. Report both control families at all four sizes.",
        ["P2", "P3"],
    )
    file("TP61-date-matching", states)
