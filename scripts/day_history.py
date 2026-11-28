"""TP89. Render released Round 37 tables and evidence-ledger limits under DY."""

import json
import re
from itertools import groupby

PACKET = "TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-27.md"
BASE = "docs/exchange/result-sheets/"
LEDGER = "engine/validation/EVIDENCE_LEDGER.jsonl"
ED = "EmpatheticDialogues, CC BY-NC 4.0."
EVENT = "Crowd-enVENT, CC BY 4.0."
BLOG = "Blog Authorship Corpus, public research release with no stated dataset licence."
GO = "GoEmotions, Apache 2.0."
DATA = {
    61: (
        "Do trained heads distinguish writers beyond random controls?",
        BLOG,
        "Original roster of 5,428 authors. The dated and matched cohorts vary by arm.",
    ),
    62: (
        "Do outputs distinguish words and writers beyond the controls?",
        ED,
        "24,850 texts from 810 writers with 32 assigned words.",
    ),
    63: (
        "Do writer-level readings track self-reported traits?",
        EVENT,
        "6,600 reports from 2,379 writers. Coverage varies by trait.",
    ),
    64: (
        "Which channels distinguish their closest assigned words?",
        f"{ED} {EVENT} {GO}",
        "24,850 chat texts, 6,600 events before training exclusions and 11,571 held-out forum comments.",
    ),
    65: (
        "How do readings differ across sentence-change timings?",
        f"{ED} {EVENT} {GO} ISEAR, noncommercial research.",
        "The original roster has 51,557 sentences. The paired forum extension covers 11,157 complete comments.",
    ),
    66: (
        "Does FEAR precede SADNESS within a loss?",
        f"{ED} {EVENT} Hippocorpus V3, no stated licence.",
        "The multisentence short arm includes 1,700 chat texts and 216 events.",
    ),
    67: (
        "Does PRIDE vary with who brought about the rise?",
        f"{ED} {EVENT}",
        "Five assigned chat words in the original responsibility arm. Counts by word appear below.",
    ),
    68: (
        "Is embarrassment better read by a pair or its own head?",
        ED,
        "24,850 chat situations, including 740 embarrassed, 628 ashamed and 760 guilty.",
    ),
    69: (
        "Can Competence and Respect be distinguished from their proposed stand-ins?",
        ED,
        "24,850 chat situations. Specific contrasts have separate eligible counts.",
    ),
    70: (
        "Which groups recur among the tags?",
        f"{ED} {BLOG}",
        "24,850 chat situations and the author means of 5,428 bloggers.",
    ),
    71: (
        "Did the approved names reach display and exports?",
        "Engine exports and TP60.",
        "304 existing tag-specific reliability entries.",
    ),
    72: (
        "Did the second sealed-job bundle reach the receiver?",
        "Constructed rehearsal for Sounding Line.",
        "27 verified payload files. Human cohort size is inapplicable.",
    ),
    73: (
        "How do reader features behave on matched whole authors?",
        BLOG,
        "The matched B/W comparison covers 432 authors and 8,640 openings. The other arms use separate cohorts.",
    ),
    74: (
        "How does PRIDE vary between earned and unearned standing?",
        f"{ED} {EVENT} {GO}",
        "Analyzed counts await the standing comparison.",
    ),
    75: (
        "Does worry increase with looking ahead within a writer?",
        BLOG,
        "The planned cohort is 500 authors with 20 openings each. The analyzed cohort awaits Q31 verification.",
    ),
    77: (
        "Which marks agree across readers and wordings?",
        f"{ED} {EVENT} {GO} ISEAR, noncommercial research.",
        "Original B/W panel of 51,557 sentences. The matched panels have separate valid counts.",
    ),
    78: (
        "Which registered predictions survive the family checks?",
        "The packet's hypotheses and released aggregate tables.",
        "One unit per registered prediction. This table adds no human observations.",
    ),
    79: (
        "Does returned anger differ by relative rank?",
        "Wikipedia talk-page corpus, CC BY-SA 4.0.",
        "38,462 speakers and 391,294 messages in the source inventory. Eligible directed replies await Q33.",
    ),
}
PENDING = {
    74: "The chat prefix is eligible under DU. Jointly valid groups and their intervals await computation.",
    75: "Q31 saved its marks and failed during final timing aggregation. The verified derived return and agreement check precede analysis.",
    79: "The archive supplied the talk-page file on Spark. Q33 intake, scoring and the directed-reply comparison remain pending.",
}


def tables(sheet):
    blocks, title = [], ""
    for is_table, lines in groupby(sheet.splitlines(), lambda s: s.startswith("|")):
        lines = list(lines)
        if is_table:
            blocks.append((title + "\n\n" if title else "") + "\n".join(lines))
        else:
            for line in lines:
                if line.startswith("## "):
                    title = "**" + line[3:] + "**"
    return "\n\n".join(blocks)


def reports(store):
    from r48_reports import Report

    ledger = [json.loads(line) for line in store.read(LEDGER).splitlines()]
    packet = store.read(PACKET).decode("utf8")
    sheets = store.files(BASE)
    for n, (question, source, size) in DATA.items():
        code = f"TP{n}"
        rows = [r for r in ledger if re.match(f"E-{code}(?:-|$)", r["id"])]
        sheet = BASE + code + ".md"
        text = store.read(sheet).decode("utf8") if sheet in sheets else ""
        card = re.search(
            r"(?ms)^### " + code + r"\..*?(?=^### |^## |\Z)", packet
        ).group()
        predictions = [
            line[2:]
            for line in card.splitlines()
            if line.startswith(("- **Registered", "- **Guess"))
        ]
        limits, verdicts, files, estimates = [], [], [], []
        for row in rows:
            file = row["data"]
            result = json.loads(store.read(file))
            if result["ledger"] != row["id"] or len(result["sourceReceiptPin"]) != 64:
                raise ValueError("Ledger or receipt binding differs: " + file)
            files.append(file)
            limits.append(row["limit"])
            verdicts.append(row["verdict"])
            estimates.append(
                f"- {row['id']}. {row['verdict']} [All estimates, intervals, sample sizes and controls](../../../{file})."
            )
        if text:
            files.append(sheet)
        if n in PENDING:
            verdict, headline = "pending", PENDING[n]
            held = headline
        elif n == 78:
            verdict, headline = (
                "family open",
                "The family table distinguishes measured predictions from unresolved comparisons.",
            )
            held = "An open prediction receives a p value when the registered measurements are available."
        else:
            verdict, headline = "filed", " ".join(dict.fromkeys(verdicts))
            held = "The linked aggregate tables give the released figures. Individual texts, keyed records and private outputs stay at source."
        tab = tables(text)
        quantities = "\n".join(estimates) + ("\n\n" + tab if tab else "")
        if n == 78:
            quantities = "The [complete family table](../result-sheets/TP78.md) gives each prediction, estimate, interval, p value, rank and adjusted p where available."
        yield Report(
            code,
            "2026-11-28",
            question,
            " ".join(predictions)
            or "This procedure has no directional research prediction.",
            source,
            size,
            quantities.strip() or "No measured estimate, interval or null band.",
            verdict,
            headline,
            " ".join(dict.fromkeys(limits))
            or PENDING.get(
                n,
                "Predictions of unequal scientific importance each receive one family entry.",
            ),
            held,
            [*files, PACKET, "scripts/day_history.py"],
            status="pending measurement" if n in PENDING else "in full",
            source_class="procedure" if n in (71, 72, 78) else "P",
        )
