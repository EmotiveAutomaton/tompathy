"""Render published TP73 two-reader estimates and their registered control bands."""

FEATURES = {
    "pleasantness": "Pleasantness",
    "unpleasantness": "Unpleasantness",
    "self_responsblt": "Own responsibility",
    "goal_support": "Goal support",
    "social_norms": "Social norms",
    "other_responsblt": "Others’ responsibility",
    "standards": "Standards",
    "suddenness": "Suddenness",
}
LEVELS = {
    "openingAgreement": "B/W on openings",
    "authorAgreement": "B/W on author means",
    "WDateRepeat": "W across date halves",
}


def estimate(row):
    if row["value"] is None:
        return "unavailable"
    lo, hi = row["interval"]
    return f"{row['value']:.3f} [{lo:.3f}, {hi:.3f}]"


def render(r):
    t = r["tables"]
    if (
        set(t) != set(LEVELS)
        or any(set(v) != set(FEATURES) for v in t.values())
        or r["authors"] * 20 != r["posts"]
        or r["eligibleAuthors"] != r["authors"] + r["cohort"]["incomplete"]
    ):
        raise ValueError("Incomplete matched-reader table")
    rows = ["| Feature | " + " | ".join(LEVELS.values()) + " |", "|---|---:|---:|---:|"]
    for f, label in FEATURES.items():
        rows.append(
            "| " + label + " | " + " | ".join(estimate(t[e][f]) for e in LEVELS) + " |"
        )
    rows.extend(
        [
            "",
            "The following 95% bands describe individual random heads. Each family has 1,000 sets of 19 heads. The full aggregate also gives the bands for the median of each set and each observed result’s percentile.",
            "",
            "| Measure | Feature | Reference | Isotropic heads | Rotated heads |",
            "|---|---|---|---:|---:|",
        ]
    )
    names = {
        "BWithControl": "B with a control",
        "WWithControl": "W with a control",
        "repeat": "Control across halves",
    }
    for e, label in LEVELS.items():
        for f, feature in FEATURES.items():
            row = t[e][f]
            for ref, refname in names.items():
                if ref not in row["rot"]:
                    continue
                bands = []
                for family in ("iso", "rot"):
                    d = row[family][ref]
                    bands.append(
                        f"{d['individual']['low']:.3f} to {d['individual']['high']:.3f}"
                        if d
                        else "unavailable"
                    )
                rows.append("| " + " | ".join([label, feature, refname, *bands]) + " |")
    avg = t["authorAgreement"]
    brief = (
        f"Across {r['authors']:,} authors and {r['posts']:,} openings, B/W agreement on author means was "
        f"{estimate(avg['unpleasantness'])} for unpleasantness and {estimate(avg['social_norms'])} for social norms."
    )
    limit = (
        f"Only {r['authors']:,} of {r['eligibleAuthors']:,} eligible authors had both readers’ scores on all twenty openings. "
        f"G11 already covered {r['cohort']['historicalComplete']:,} of them. These estimates measure agreement and repeatability for two fixed reader builds on that subset."
    )
    return brief, rows, limit
