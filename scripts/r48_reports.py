"""Build the R48 reports and digest using only released, versioned aggregate tables."""

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID = "engine/validation/"
EXCHANGE = "docs/exchange/"
FOLDER = EXCHANGE + "r48/"
SEED = VALID + "EVIDENCE_LEDGER_SEED_R29.jsonl"
COAUTHOR = "Stanford CoAuthor, public download. The original intake recorded internal research use and no express redistribution grant."
STORIES = "Story Commonsense/ROCStories, public download with no dataset licence stated in the held release. The transfer source is Crowd-enVENT (CC BY 4.0)."
ISEAR = "ISEAR, publicly obtainable under noncommercial research terms."
P_LIMIT = "Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC."
SCRIPT = "[Report builder](../../../scripts/r48_reports.py)"


class Store:
    def __init__(self, revision=None):
        self.revision = revision

    def read(self, path):
        if self.revision:
            return subprocess.check_output(
                ["git", "show", f"{self.revision}:{path}"], cwd=ROOT
            )
        return (ROOT / path).read_bytes()

    def tables(self, stem):
        return json.loads(self.read(aggregate(stem)))

    def files(self, prefix):
        if self.revision:
            return set(
                subprocess.check_output(
                    ["git", "ls-tree", "-r", "--name-only", self.revision, prefix],
                    cwd=ROOT,
                )
                .decode()
                .splitlines()
            )
        return {
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / prefix).rglob("*")
            if p.is_file()
        }


def aggregate(stem):
    return VALID + stem + "-2026-11.json"


def fmt(x):
    if isinstance(x, float):
        return f"{x:.7g}"
    if isinstance(x, list):
        return "[" + ", ".join(fmt(v) for v in x) + "]"
    return "unavailable" if x is None else str(x)


def table(headers, rows):
    def line(row):
        return (
            "| "
            + " | ".join(fmt(x).replace("|", r"\|").replace("\n", " ") for x in row)
            + " |"
        )

    return "\n".join(
        [line(headers), line(["---"] * len(headers)), *(line(r) for r in rows)]
    )


def measured(row):
    return f"{fmt(row['value'])} {fmt(row['interval'])}"


@dataclass
class Report:
    code: str
    day: str
    question: str
    prediction: str
    source: str
    size: str
    quantities: str
    verdict: str
    headline: str
    limit: str
    held: str
    files: list
    status: str = "in full"
    source_class: str = "P"

    def render(self):
        links = " · ".join(f"[{Path(p).name}](../../../{p})" for p in self.files)
        return f"""# {self.code} · {self.question}

**1. Question and prediction.** {self.question} {self.prediction}

**2. Source and size.** Class {self.source_class}. {self.source} {self.size}

**3. Registered quantities.**

{self.quantities}

**4. Verdict.** **{self.verdict}.** {self.headline}

**5. Limit.** {self.limit}

**6. Withholding and release.** {self.held}

**7. Tables and code.** {links} · {SCRIPT}
"""


LEGACY = [
    (
        "W1",
        "Do converted weights preserve pause scores at the required speed?",
        "speed-weightonly",
        ["E-W1-weightonly"],
    ),
    (
        "Attention",
        "Does word surprise predict pauses beyond the reference model?",
        "attention-stops",
        ["E-attention-row1", "E-attention-row2-history", "E-attention-row3-donor"],
    ),
    (
        "AI-involvement",
        "Can the reader distinguish accepted suggestions from writer-typed sentences?",
        "ai-involvement",
        ["E-ai-involvement-row1", "E-ai-involvement-row2-history"],
    ),
    (
        "History",
        "Do more earlier writing sessions improve pause prediction?",
        "history-ladder",
        ["E-history-ladder"],
    ),
    (
        "TP18",
        "Do added local word features improve pause prediction?",
        "readers-attention-features",
        ["E-TP18"],
    ),
    (
        "TP18-probe",
        "Does the fixed-third probe improve pause prediction?",
        "readers-attention-probe",
        ["E-TP18-probe"],
    ),
    (
        "TP19",
        "Do reader scores or earlier picks predict writers’ next decisions?",
        "readers-choices",
        ["E-TP19-reader", "E-TP19-history"],
    ),
    (
        "TP25",
        "Can a gate detect stakes and stay quiet on neutral texts?",
        "readers-stakes-gate",
        ["E-TP25"],
    ),
    (
        "TP27",
        "Does the pause residual recover a stop derived from the same interval?",
        "readers-pause-remainder-diagnostic",
        ["E-TP27"],
    ),
]


def legacy_reports(s, seed):
    for code, question, stem, ids in LEGACY:
        evidence = [seed[k] for k in ids]
        first = evidence[0]
        d = s.tables(stem)
        body = table(
            ["Registered row", "Estimate", "Interval", "Size", "Rule", "Verdict"],
            [
                [
                    r[k]
                    for k in ("label", "estimate", "interval", "data", "bar", "verdict")
                ]
                for r in evidence
            ],
        )
        headline = first["estimate"] + ". Interval " + first["interval"] + "."
        verdict = first["verdict"]
        if code in ("History", "TP18", "Attention", "AI-involvement"):
            body += "\n\n" + table(
                [
                    "Comparison",
                    "Baseline AUC",
                    "Reader AUC",
                    "Gain",
                    "Writer interval",
                    "Writers",
                ],
                [
                    [
                        r.get("name", r.get("k", r.get("id"))),
                        r.get("baseline"),
                        r.get("engine"),
                        r.get("gain"),
                        r.get("interval"),
                        r.get("clusters"),
                    ]
                    for r in d["rows"]
                ],
            )
        if code == "AI-involvement":
            verdict = "mixed"
        if code == "W1":
            e = d["gates"]["e"]
            headline = f"Paired AUC difference {fmt(e['gain'])} {fmt(e['interval'])} across {e['clusters']} writers. The two-thread speed target was missed."
            body += (
                "\n\n"
                + headline
                + "\n\n"
                + table(
                    ["Fixture", "Threads", "Seconds per 3,000 words"],
                    [
                        [r["frozenText"], r["threads"], r["secondsPer3000Words"]]
                        for r in d["measurements"]
                    ],
                )
            )
            verdict = "parity passed, speed missed"
        if code == "TP19":
            body += "\n\n" + table(
                ["Model", "Choice accuracy", "Choice log loss", "Handling log loss"],
                [
                    [
                        k,
                        r["choice_accuracy"],
                        r["choice_log_loss"],
                        r["handling"]["mean_log_loss"],
                    ]
                    for k, r in d["rows"].items()
                ],
            )
        if code == "TP25":
            body += "\n\n" + table(
                ["Source", "Units", "Tagged positive", "Sensitivity", "Silence"],
                [
                    [k, r["n"], r.get("positive"), r.get("sensitivity"), r["silence"]]
                    for k, r in (d["rows"] | d["neutral"]).items()
                ],
            )
        yield Report(
            code,
            first["date"],
            question,
            "Registered comparison: " + first["bar"] + ".",
            STORIES + " GoEmotions uses Apache 2.0." if code == "TP25" else COAUTHOR,
            first["data"] + ".",
            body,
            verdict,
            headline,
            first["limit"],
            P_LIMIT,
            [aggregate(stem), SEED],
        )


def tag_reports(s, seed):
    cohort = s.tables("readers-tp42")["estimate"]["crowd-enVENT"]
    for rung, evid in [
        ("bow", "bow"),
        ("frozen", "frozen"),
        ("fine-23", "fine"),
        ("fine-47", "fine"),
        ("fine-71", "fine"),
    ]:
        stem = "readers-need-" + rung
        d = s.tables(stem)
        a, t = d["story"], d["transfer"]
        qty = table(
            ["Twin pair", "Ratings AUC", "Needs AUC", "Both AUC", "Gain"],
            [
                [k, v["ratings"], v["needs"], v["ratings+needs"], v["gain_from_needs"]]
                for k, v in t["twins"].items()
            ],
        )
        qty += "\n\n" + table(
            [
                "Story tag (acceptance is the current name for belonging)",
                "Held-out AUC",
            ],
            a["auc"].items(),
        )
        qty += (
            "\n\nThirteen-label macro-F1: "
            + ", ".join(
                f"{k} {fmt(v)}" for k, v in t["thirteen_labels_macro_f1"].items()
            )
            + "."
        )
        head = f"Mean twin gain {fmt(t['mean_gain'])}, with {t['pairs_ge_03']} qualifying pairs. Story AUC {fmt(a['mean_auc'])}. No sampling interval was computed."
        row = seed["E-TP23-" + evid]
        yield Report(
            "TP23-" + rung,
            row["date"],
            "Do story tags improve separation of similar feelings?",
            "Mean transfer AUC gain must reach 0.06 and four pairs must gain at least 0.03. Encoders must also reach story AUC 0.76.",
            STORIES,
            row["data"]
            + f". Story author identities are unavailable. The transfer cohort has {cohort['writers']:,} writers.",
            qty,
            "passed" if d["qualifies"] else "failed",
            head,
            "The story folds are story-disjoint. Transfer tests reuse a common event cohort. Seed spread measures training variability.",
            P_LIMIT,
            [aggregate(stem), SEED],
        )
    profiles = s.tables("readers-need-frozen")["transfer"]["label_profiles_sd"]
    tags = list(next(iter(profiles.values())))
    head = f"The frozen reader's status tag for pride was {fmt(profiles['pride']['status'])} standard deviations above its cohort mean. No sampling interval was calculated."
    yield Report(
        "TP23-profiles",
        seed["E-TP23-profiles"]["date"],
        "Which story-trained tags distinguish the assigned event labels?",
        "Descriptive profiles with no per-tag pass threshold.",
        STORIES,
        f"{cohort['textsWithWriter']:,} event reports from {cohort['writers']:,} writers.",
        table(
            ["Tag", *profiles],
            [[tag, *[v[tag] for v in profiles.values()]] for tag in tags],
        ),
        "descriptive",
        head,
        "Each value is a standardized group contrast from the same trained reader.",
        P_LIMIT,
        [aggregate("readers-need-frozen"), aggregate("readers-tp42")],
    )


def feature_delivery(s):
    path = "docs/sounding-line-engine-features-2026-10-20/ENGINE_FEATURE_TABLE.json"
    d = json.loads(s.read(path))
    summary = []
    for row in d["rows"]:
        paired = (
            row.get("primary")
            or row.get("other_reliability")
            or row.get("paired_real_minus_fake", {})
        )
        ci = paired.get("ci95")
        if ci is None and "ci_low" in paired:
            ci = [paired["ci_low"], paired["ci_high"]]
        summary.append(
            [
                row["id"],
                paired.get("effect"),
                ci,
                paired.get("writers", row["real_identification"].get("writers")),
                row["real_identification"].get("accuracy"),
                row["fake_identification"].get("mean"),
                row["interpretation_status"],
            ]
        )
    info = d["dictionary"]["definitions"]
    counts = ", ".join(f"{v['count']} {k.replace('_', ' ')}" for k, v in info.items())
    head = f"{len(summary)} channel rows. The registered dictionary contains {counts}. Counts are exact."
    return Report(
        "EV4",
        "2026-10-23",
        "Which CoAuthor channel results and dictionary sizes reached the engine?",
        "Return measured identification and reliability alongside each source control.",
        COAUTHOR,
        "Each source contrast has its own support. Writer counts shown where available in the contrast or identification row.",
        table(
            [
                "Channel",
                "Effect",
                "Interval",
                "Writers",
                "Real identification",
                "Fake mean",
                "Original interpretation",
            ],
            summary,
        )
        + "\n\nThe linked table supplies reliability, projected record counts, shuffle controls and scope for each channel.",
        "descriptive",
        head,
        "A biased identity control invalidates the corresponding admission even when the measured contrast is positive.",
        "The receiver has the three dictionary sizes and ordered hashes. The literal dictionaries were never in its delivery. R48 releases statistical results. The archived feature definitions remain at source.",
        [path],
    )


def other_reports(s):
    legacy = s.tables("r48-legacy")
    c = legacy["coauthor"]
    size = f"{c['writers']} writer, {c['sessions']} session."
    head = f"{c['decisions']} decisions, {c['corrections']} correction and {c['fittedChoices']} fitted choices. No interval was estimated."
    yield Report(
        "CoAuthor-rehearsal",
        "2026-10-17",
        "Could the adapter reconstruct and fit choices from one writing session?",
        "Engineering rehearsal with no registered accuracy threshold.",
        COAUTHOR,
        size,
        head,
        "reconstructed",
        head,
        "One example verifies the adapter only.",
        P_LIMIT,
        [aggregate("r48-legacy")],
    )
    rows = legacy["baseFolds"]
    head = f"{len(rows)} completed folds cover {sum(r['heldOutLines'] for r in rows):,} held-out lines. No whole-study estimate or interval."
    yield Report(
        "TP23-base",
        "2026-11-19",
        "Does the optional base encoder meet the story and transfer thresholds?",
        "Use the same transfer and story bars as the other encoders.",
        STORIES,
        "Released counts are held-out character-lines. Story author identities are unavailable.",
        table(
            ["Fold", "Held-out lines", "Selected development AUC"],
            [[r["fold"], r["heldOutLines"], r["developmentAuc"]] for r in rows],
        ),
        "incomplete",
        head,
        "Development AUC selects the checkpoint and does not measure held-out transfer.",
        "The owner closed the run during the last fold. No final fit or combined estimate exists.",
        [aggregate("r48-legacy")],
        "in full for completed folds",
    )
    stem = "readers-refusals"
    d = s.tables(stem)
    m, a = d["matching"], d["stability"]
    head = f"Cross-prompt accuracy gain {fmt(m['gain'])} {fmt(m['interval'])}. Within-writer stability gain {fmt(a['gain'])} {fmt(a['interval'])}."
    yield Report(
        "TP32",
        "2026-11-20",
        "Are refusals stable within writers and useful for identifying them across prompts?",
        "Stability must clear zero and the matching gain must reach 0.030.",
        COAUTHOR,
        f"{m['writers']} writers and {m['sessions']:,} sessions in the matching comparison.",
        f"Baseline accuracy {fmt(m['baseline'])}, augmented accuracy {fmt(m['augmented'])}. "
        + head,
        "mixed",
        head,
        "Matching applies only to writers with enough eligible sessions.",
        P_LIMIT,
        [aggregate(stem)],
    )
    stem = "readers-tp42"
    d = s.tables(stem)
    c = d["estimate"]["CoAuthor"]
    rows = []
    for k, v in d["estimate"].items():
        if "writers" in v:
            rows.append(
                [
                    k,
                    v["writers"],
                    v["textsWithWriter"],
                    *[
                        (v[key] or {}).get("authors")
                        for key in ("atLeast20", "multipleDates", "both")
                    ],
                ]
            )
        else:
            rows.append([k, v["unavailable"], None, None, None, None])
    head = f"CoAuthor has {c['both']['authors']} writers meeting both requirements. Blogs have {d['estimate']['Blog Authorship Corpus']['both']['authors']:,}. Exact census counts have no sampling interval."
    yield Report(
        "TP42",
        "2026-11-21",
        "How many writers have enough texts on more than one date?",
        "Fewer than 200 qualifying writers in each source.",
        COAUTHOR + " " + STORIES,
        f"CoAuthor contributed {c['textsWithWriter']:,} sessions from {c['writers']} writers. The table lists the other released cohorts separately.",
        table(
            [
                "Source",
                "Writers or reason unavailable",
                "Texts",
                "At least 20 texts",
                "Multiple dates",
                "Both",
            ],
            rows,
        ),
        "failed",
        head,
        "Releases overlap and writer identifiers vary by source.",
        "Story Commonsense lacks writer identities. Computing its longitudinal count requires an actual writer key.",
        [aggregate(stem)],
    )
    stem = "readers-tp44"
    d = s.tables(stem)
    data = d["estimate"]["TP44"]
    allrows, repeat = data["table1"], data["table2"]
    p = allrows["all"]["pleasantness"]
    head = f"Pleasantness rho {measured(p)} in {p['reports']:,} reports. Style-cleared split-half rho {measured(repeat['styleCleared']['mean'])}."
    body = table(
        [
            "Feeling code",
            "Pleasantness rho [95% interval]",
            "People",
            "Reports",
            "Suddenness rho [95% interval]",
            "People",
            "Reports",
        ],
        [
            [
                k,
                measured(v["pleasantness"]),
                v["pleasantness"]["people"],
                v["pleasantness"]["reports"],
                measured(v["suddennessVsReversedExpectedness"]),
                v["suddennessVsReversedExpectedness"]["people"],
                v["suddennessVsReversedExpectedness"]["reports"],
            ]
            for k, v in allrows.items()
        ],
    )
    body += f"\n\nAcross feelings the uncleared mean was {measured(repeat['uncleared']['mean'])}. {repeat['fallbackCells']} country/city/feeling cells needed the country fallback. The source table includes responsibility means by answer, Pearson comparisons and tag intervals."
    body += "\n\n<details><summary>Responsibility means, secondary correlations and tag intervals</summary>\n\n"
    body += table(
        [
            "Feeling",
            "Cause category",
            "Reader feature",
            "Mean [95% interval]",
            "People",
            "Reports",
        ],
        [
            [k, cause, name, measured(val), val["people"], val["reports"]]
            for k, v in allrows.items()
            for cause, m in v["responsibilityMeans"].items()
            for name, val in m.items()
        ],
    )
    body += "\n\n" + table(
        [
            "Feeling",
            "Pearson pleasantness",
            "Pearson suddenness vs reversed expectedness",
        ],
        [
            [
                k,
                measured(v["pleasantness"]["pearson"]),
                measured(v["suddennessVsReversedExpectedness"]["pearson"]),
            ]
            for k, v in allrows.items()
        ],
    )
    body += (
        "\n\n"
        + table(
            ["Across-feeling tag", "Style cleared", "Uncleared"],
            [
                [k, measured(v), measured(repeat["uncleared"]["tags"][k])]
                for k, v in repeat["styleCleared"]["tags"].items()
            ],
        )
        + "\n\n</details>"
    )
    yield Report(
        "TP44",
        "2026-11-23",
        "Do reader features agree with own ratings and tag differences repeat across feelings?",
        "Reader ratings should agree with respondents and the style-cleared mean should repeat across feeling splits.",
        ISEAR,
        f"{p['people']:,} respondents. {repeat['completePeople']:,} complete and {repeat['incompletePeople']} incomplete respondents for the across-feeling analysis.",
        body,
        "passed" if all(d["verdict"].values()) else "mixed",
        head,
        "Ratings come from one questionnaire sitting. Within-feeling variation is limited.",
        P_LIMIT,
        [aggregate(stem)],
    )
    stem = "readers-tp54"
    d = s.tables(stem)
    head = f"Sadness slope {measured(d['responsibility']['sadness'])}. Fear slope {measured(d['responsibility']['fear'])}."
    yield Report(
        "TP54",
        "2026-11-23",
        "Does control distinguish sadness and fear from anger?",
        "Sadness should decline with control. The fear slope should stay within the registered equivalence margin.",
        "Crowd-enVENT (CC BY 4.0). " + ISEAR,
        f"{d['reports']:,} events from {d['writers']:,} writers in the measured arm.",
        table(
            ["Adjustment", "Outcome", "Slope [95% writer interval]"],
            [
                [k, tag, measured(v)]
                for k in ("responsibility", "highestNeed")
                for tag, v in d[k].items()
            ],
        ),
        "mixed",
        head,
        "The fear interval extends outside the equivalence margin.",
        "ISEAR: "
        + d["isear"]
        + ". This comparison requires an ordered event-control rating.",
        [aggregate(stem)],
    )
    access = legacy["heldAccess"]
    if access["sparkInPlace"] or access["sourceRowsRead"] or access["rawCopies"]:
        raise ValueError(
            "Held source access changed: reconcile Q30 and any registered aggregate before reporting"
        )
    for code, question, pred in [
        (
            "TP76",
            "Do curiosity and SEEKING track openness in long recalled stories?",
            "Curiosity should increase with self-rated openness. Report the timing operators and random-head comparison alongside it.",
        ),
        (
            "TP66-long",
            "Does FEAR precede SADNESS within long recalled losses?",
            "Loss should shift SADNESS later relative to FEAR against length-matched stories.",
        ),
    ]:
        yield Report(
            code,
            "2026-11-27",
            question,
            pred,
            "Hippocorpus V3. The held public release states no dataset licence.",
            "No analytical cohort or sample size yet.",
            f"The access check read {access['sourceRowsRead']} data rows and made {access['rawCopies']} copies. There is no effect estimate, interval or null band.",
            "pending",
            "No Q30 measurements. Analytical size and interval unavailable.",
            "Only recalled and retold accounts are eligible. Imagined accounts are excluded.",
            "Full figures are due after registered scoring in place. Spark needs a readable route to the held table. Stories stay at source, without copies or quotations.",
            [aggregate("r48-legacy")],
            "withheld: Q30 source access pending",
        )
    stem = "r48-tmp2-source"
    raw = s.read(aggregate(stem))
    # Fixed released status only. Adding an eligible sealed table requires its own reviewed
    # registration and installed-gate receipt. There is no generic prose or row passthrough.
    if (
        hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        != "cce9204fd40b913bf21e35d1c44b38ac19fc532fe5e98a72dc8a19a0a9c2e66e"
    ):
        raise ValueError("Unreviewed sealed release")
    d = json.loads(raw)
    if d["rows"] or d["gate"] != "skipped":
        raise ValueError("Unexpected sealed analytical rows")
    reason = f"Native exit {d['nativeExit']}, launcher exit {d['launcherExit']}, external gate {d['gate']}. Verify key uniqueness, timestamps and missing-value conventions inside the seal."
    yield Report(
        "TMP2-source",
        "2026-11-27",
        "Can the receiver bind the PANDORA source to its preregistered trait analysis?",
        "Source qualification only.",
        "PANDORA, Gjurković et al. (2021). Author terms permit aggregate public findings.",
        "The receiver released no analytical count.",
        "The released table is header-only. Counts for five trait fields, a reduced count and the pooled eligible share are unavailable.",
        "source unbound",
        "No estimate, interval or analytical size was released.",
        "The exit code does not isolate which source binding failed.",
        reason,
        [aggregate(stem)],
        "withheld: source binding failed",
        "S",
    )


def new_sentence_reports(s):
    stem = "readers-tp77-responsibility"
    r = s.tables(stem)
    rows = r["tables"]
    b = rows["B-writer"]
    yield Report(
        "TP77-responsibility",
        date.fromisoformat(r["ledger"][-8:]).isoformat(),
        "Do readers agree with writers about their own responsibility?",
        "The packet specified the comparison without a numerical pass threshold.",
        "Crowd-enVENT (CC BY 4.0).",
        f"{b['paired']:,} events from {b['writers']:,} writers in the full B comparison.",
        table(
            [
                "Comparison",
                "Paired events",
                "Writers",
                "Rank correlation (95% interval)",
                "Unweighted kappa (95% interval)",
                "Fraction in exact agreement",
            ],
            [
                [
                    k,
                    c["paired"],
                    c["writers"],
                    measured(c["rank"]),
                    measured(c["kappa"]),
                    c["exactAgreement"],
                ]
                for k, c in rows.items()
            ],
        )
        + "\n\nEach interval uses 2,000 whole-writer resamples. The aggregate includes every cell of each paired 1–5 table.",
        "descriptive",
        f"B and writer rank correlation {measured(b['rank'])}. Exact agreement {b['exactAgreement']:.1%}.",
        r["limit"],
        "W reached only the original source-order prefix before its memory stop. The full W estimate has no paired data beyond that prefix. Individual answers remain private.",
        [aggregate(stem), "scripts/rapid_responsibility.py"],
    )
    stem = "readers-tp77-q29"
    if aggregate(stem) not in s.files(VALID):
        return
    r = s.tables(stem)
    c = r["coverage"]
    rows = r["tables"]
    when = rows["when"]
    summary = table(
        [
            "Forum prefix",
            "Paired",
            "Author clusters",
            "Kappa (95% interval)",
            "CW on prefix",
        ],
        [
            [field, cell["jointlyValid"], cell["clusters"], measured(cell), cell["CW"]]
            for field, cell in rows.items()
        ],
    )
    counts = table(
        [
            "Source",
            "Reader",
            "Reports in roster",
            "Sentences in roster",
            "Saved",
            "Valid",
            "Neither",
            "Ahead",
            "Landed",
            "Ongoing",
        ],
        [
            [
                src,
                reader,
                srcrow["reports"],
                srcrow["sentences"],
                srcrow["WSaved"] if reader == "W" else srcrow["sentences"],
                *[
                    srcrow[reader][k]
                    for k in ("valid", "none", "ahead", "already", "ongoing")
                ],
            ]
            for src, srcrow in c.items()
            for reader in ("B", "W")
        ],
    )
    yield Report(
        "TP77-Q29",
        date.fromisoformat(r["ledger"][-8:]).isoformat(),
        "Do the two readers agree on the new sentence marks?",
        "Timing was predicted to be usable under CW (kappa at least 0.60).",
        "Held-out GoEmotions forum comments and ISEAR. " + ISEAR,
        f"{when['jointlyValid']:,} paired forum sentences from {when['clusters']:,} author clusters. ISEAR contributed {c['isear']['sentences']:,} B readings; authors were not joined for an unpaired comparison.",
        summary + "\n\n" + counts,
        "partial",
        f"Timing kappa {measured(when)} on the forum prefix ({when['CW']} on that subset).",
        r["limit"],
        "The workstation reached its memory floor before finishing the forum or reaching ISEAR. A full-panel estimate requires the missing independent readings. The original job is closed.",
        [aggregate(stem), "scripts/rapid_q29_agreement.py"],
    )

    stem = "readers-tp65-q29"
    if aggregate(stem) not in s.files(VALID):
        return
    r = s.tables(stem)
    f = r["forum"]
    contrasts = (
        "changeMinusNeither",
        "aheadMinusNeither",
        "landedMinusNeither",
        "aheadMinusLanded",
    )
    labels = [
        "Change minus neither",
        "Ahead minus neither",
        "Landed minus neither",
        "Ahead minus landed",
    ]
    rows = []
    counts = []
    for arm, panel in f["tables"].items():
        for channel in r["outputs"]:
            rows.append(
                [
                    arm,
                    channel,
                    *[
                        measured(panel["contrasts"][k]["outputs"][channel])
                        for k in contrasts
                    ],
                ]
            )
        for k, label in zip(contrasts, labels, strict=True):
            c = panel["contrasts"][k]
            counts.append(
                [
                    arm,
                    label,
                    c["eligibleSentences"],
                    c["eligibleReports"],
                    c["reportsWithBothClasses"],
                    c["writersWithBothClasses"],
                ]
            )
    primary = f["tables"]["B"]["contrasts"]["aheadMinusLanded"]
    both = f["tables"]["agreement"]["contrasts"]["aheadMinusLanded"]
    yield Report(
        "TP65-Q29",
        date.fromisoformat(r["ledger"][-8:]).isoformat(),
        "Do channel readings differ between look-ahead and landed forum sentences?",
        "SADNESS was predicted higher on landed sentences. The six channel-specific timing predictions and the change-versus-neither comparison were registered before Q29.",
        "Held-out GoEmotions forum comments. " + ISEAR,
        f"{f['sentences']:,} sentences in {f['reports']:,} complete comments and {f['writers']:,} author clusters. {f['lastReportSentencesExcluded']} sentences from incomplete comments excluded.",
        table(["Reading", "Channel", *labels], rows)
        + "\n\n"
        + table(
            [
                "Reading",
                "Contrast",
                "Eligible sentences",
                "Eligible comments",
                "Comments with both classes",
                "Author clusters with both",
            ],
            counts,
        )
        + "\n\nValues are position-adjusted within-comment differences with 95% intervals from 2,000 whole-writer resamples. Counts and intervals come from the released table.",
        "descriptive",
        f"SADNESS ahead minus landed {measured(primary['outputs']['SADNESS'])} using B and {measured(both['outputs']['SADNESS'])} on agreement.",
        r["limit"],
        f"ISEAR has {r['coverage']['isear']['B']['valid']:,} valid B marks and no W marks. Independent readings would be needed for a reliability-gated contrast. Q29 did not score worry.",
        [aggregate(stem), "scripts/rapid_q29_contrasts.py"],
    )


def paired_report(s):
    from rapid_paired_report import render

    stem = "readers-tp73-paired"
    if aggregate(stem) not in s.files(VALID):
        return
    r = s.tables(stem)
    brief, rows, limit = render(r)
    yield Report(
        "TP73-paired",
        date.fromisoformat(r["ledger"][-8:]).isoformat(),
        "How closely do two readers agree on the same blog authors?",
        "The paired comparison is descriptive. The registered B-only repeat prediction is recorded separately.",
        "Blog Authorship Corpus, dated openings with saved B and W readings.",
        f"{r['authors']:,} complete authors and {r['posts']:,} openings. Ten openings per date half.",
        "\n".join(rows)
        + "\n\nPearson correlations with 95% intervals from 2,000 whole-author resamples.",
        "descriptive",
        brief,
        limit,
        "Every aggregate estimate is available in the linked table. Per-opening scores and author identifiers remain private.",
        [
            aggregate(stem),
            "scripts/rapid_paired_controls.py",
            "scripts/rapid_paired_moments.py",
        ],
    )


def build(s):
    seed = {
        r["id"]: r
        for r in (json.loads(line) for line in s.read(SEED).splitlines())
        if r["program"] == "engine"
    }
    reports = sorted(
        [
            *legacy_reports(s, seed),
            *tag_reports(s, seed),
            *other_reports(s),
            *new_sentence_reports(s),
            *paired_report(s),
            feature_delivery(s),
        ],
        key=lambda r: (r.day, r.code),
        reverse=True,
    )
    if len({r.code for r in reports}) != len(reports):
        raise ValueError("Duplicate report ID")
    outputs = {FOLDER + r.code + ".md": r.render() for r in reports}
    rows = []
    for r in reports:
        if len(r.question.split()) > 15:
            raise ValueError(f"Digest question longer than 15 words: {r.code}")
        week = date.fromisoformat(r.day).isocalendar().week
        rows.append(
            [
                f"[{r.code}](r48/{r.code}.md)",
                f"{r.day[:4]}-W{week:02}",
                r.question,
                r.verdict,
                r.headline + " " + r.size,
                r.limit,
                r.status,
            ]
        )
    outputs[EXCHANGE + "HELD_RESULTS_DIGEST.md"] = (
        "# Held results digest\n\nMost recent study week first. Each study ID opens its seven-part report. "
        "A missing estimate or interval is shown explicitly. [Inventory and scope](HELD_RESULTS_INVENTORY.md) · [Ruling R48](RULING_R48.md)\n\n"
        + table(
            [
                "Report",
                "Week",
                "Question",
                "Verdict",
                "Headline, interval and size",
                "Limit",
                "Report status",
            ],
            rows,
        )
        + "\n"
    )
    inventory = []
    for r in reports:
        hold = (
            "The October release check kept the rehearsal local."
            if r.code == "CoAuthor-rehearsal"
            else "Public numerical tables already existed for this research source."
        )
        next_step = "Rebuilt from the linked aggregate. No inference is needed."
        if r.code == "EV4":
            hold = "The feature handoff used dictionary hashes pending the corpus terms check."
            next_step = "All received statistical quantities are releasable. Source-owned dictionary arrays were outside the delivery."
        elif r.code.startswith("TP77-"):
            hold = "New Round 37 reader comparison."
            next_step = (
                "Report generated from the released paired counts and estimates."
            )
        elif r.code in ("TP66-long", "TP76", "TMP2-source", "TP23-base", "TP54"):
            hold, next_step = r.status, r.held
        files = " · ".join(f"[{Path(p).name}](../../{p})" for p in r.files if p != SEED)
        inventory.append(
            [
                f"[{r.code}](r48/{r.code}.md)",
                r.day,
                r.source_class,
                hold,
                files,
                next_step,
            ]
        )
    outputs[EXCHANGE + "HELD_RESULTS_INVENTORY.md"] = (
        "# Inventory of held engine results\n\nReviewed the engine returns from the current two-day packet back to the "
        "October native-adapter return, both public evidence ledgers, dated scoreboard, source terms and the original "
        "feature-table delivery. Each row identifies the saved source of the numbers. The dates identify the filing week. "
        "Full precision stays in the linked tables. [Digest](HELD_RESULTS_DIGEST.md) · [Effective ruling](RULING_R48.md)\n\n"
        + table(
            [
                "Report",
                "Date",
                "Class",
                "Earlier disposition",
                "Aggregate source",
                "Action or outstanding requirement",
            ],
            inventory,
        )
        + "\n\n## Other entries checked\n\n"
        + "- TP58/TMP1 delivered an invented-data rehearsal. The later real PANDORA source check is TMP2-source above. "
        "TP72/TMP3 is a producer rehearsal and conditional receiver job. Neither rehearsal supplies a human estimate. "
        "[TP58](result-sheets/TP58.md) · [TP72](result-sheets/TP72.md)\n"
        + "- TP13 missed its transfer tests. Proposed label rows stayed unmeasured. TP1c stopped at numerical gate b before cohort accuracy. "
        "TP16 B/C and TP22 lacked a qualified population policy. TP14 retained partial scores only. Their published observations stand. "
        "[Readers return](THEORY_RETURN_READERS.md) · [Scoreboard](../ENGINE_SCOREBOARD.md)\n"
        + "- The en/de bilingual recall releases in R29, sacredness in R35 and the newly located Hansard temporal labels have no engine "
        "estimate in the surveyed returns. Original ISEAR in TP44 and TP54 is a separate release. DreamBank has no engine card here. "
        "Talk-page CP1 has a stated CC BY-SA licence and TP79 is awaiting in-place access.\n"
        + "- TP59's personally supplied reference workbook was used to match feeling names. The engine computed no pooled human "
        "estimate or rater accuracy. Individual scores remain private. Its public, source-specific model estimates and intervals "
        "are already in the [TP59 numerical table](result-sheets/TP59-by-source.csv). Theory owns any pooling.\n"
        + "- C0/IM2 exported existing scores. It added no independent scientific estimate. The trained reader used by later studies "
        "does not change the source on which those studies were evaluated.\n"
        + "- Sounding Line maintains its own MIDUS, CANDOR, PANDORA and other sealed returns. No additional sealed invocation "
        "was used by this engine pass. A source-binding failure has no coarser analytical table available. "
        "[Receiver inventory](https://github.com/EmotiveAutomaton/sounding-line/blob/18708a8f11e17e33bcd8717a21e330a8257bb2cd/docs/exchange/HELD_RESULTS_INVENTORY.md)\n\n"
        + "## Release procedure\n\nRebuild with `python scripts/r48_reports.py` at every return. "
        "Register a newly released aggregate here before landing its card. Run `python scripts/r48_reports.py --check` before pushing. "
        "The outgoing-commit check compares every generated page and the digest to the released inputs, refuses unregistered files "
        "in the report directory, and accepts only the exact reviewed receiver release.\n\n"
        + "Sealed jobs register fine, coarse and pooled forms before analysis. Inside the seal, count distinct people in every "
        "cell and check the finest eligible form once with the installed gate. Ten or fewer people, person-keyed tables, extrema, "
        "raw text and weights stay sealed. A new populated receiver release must bind its table and native gate receipt before import. "
        "The current import accepts a header-only table. The receiver owns the three predeclared forms for TMP2 and TMP3. "
        "[Forms](https://github.com/EmotiveAutomaton/sounding-line/blob/18708a8f11e17e33bcd8717a21e330a8257bb2cd/docs/design/stage-15/week8/R48_SEALED_FORMS.md)\n\n"
        + "The retained MIDUS project notice excludes cells below ten and requires MIDUS citation and funding acknowledgment. "
        "The engine floor is eleven distinct people. CANDOR permits nonidentifying aggregate findings and credits BetterUp Labs and "
        "Reece et al. (2023), plus Cooney and Reece (2025) for NaturalTurn. PANDORA permits aggregate public findings only. "
        "The source is Gjurković et al. (2021). [Retained clauses, editions and credits]"
        "(https://github.com/EmotiveAutomaton/sounding-line/blob/18708a8f11e17e33bcd8717a21e330a8257bb2cd/docs/design/stage-15/R48_SOURCE_TERMS.md)\n"
    )
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--revision",
        help="Verify the outgoing Git commit, independently of the worktree",
    )
    args = parser.parse_args()
    if args.revision and (
        not args.check or not re.fullmatch(r"[a-f0-9]{40}", args.revision)
    ):
        parser.error("revision checks require --check and a full commit ID")
    s = Store(args.revision)
    wanted = build(s)
    extra = s.files(FOLDER) - wanted.keys()
    if extra:
        raise SystemExit("Unregistered R48 output: " + ", ".join(sorted(extra)))
    for name, content in wanted.items():
        if args.check:
            if s.read(name).decode().replace("\r\n", "\n") != content:
                raise SystemExit(f"Output differs from released table: {name}")
        else:
            dest = ROOT / name
            dest.parent.mkdir(exist_ok=True)
            dest.write_text(content, encoding="utf8", newline="\n")
    print(
        f"{len(wanted) - 2} reports, inventory and digest {'verified' if args.check else 'written'}"
    )


if __name__ == "__main__":
    main()
