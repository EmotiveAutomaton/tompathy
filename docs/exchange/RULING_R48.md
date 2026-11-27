# Ruling R48: every study returns a report (27 November 2026)

*Drafted by the implementation thread from the curator's message of 27 November 2026. In force in a repository when the curator's message delivers it. In the engine's record it is amendment DC. In Sounding Line's record it is amendment DN. It replaces every earlier line that keeps a result's figures in an internal, restricted or local-only record, and it withdraws the proposed practice of one-word verdicts.*

## 1. The rule

A study is not landed until its report is in the pushed record. This holds for every source: sealed, restricted, "tests only", or with no stated licence. A receipt that says a study ran is not a report.

Both repositories are public. "Reported" below means published.

## 2. Two classes of source

**Class P, anyone can download it.** Every set that a member of the public can fetch, whatever its licence line says, including "none stated" and "tests only". All statistics are reported: estimates, intervals, counts, small groups, and figures under the source's own public codes. What stays in: rows and texts are not copied into the record, a scale's item wording is not reproduced where the source does not grant reuse, and nobody is named. From now on "tests only" means that the data are not copied out, shipped or built into a product. It no longer limits what is said about them.

**Class S, obtained under an agreement or by personal delivery.** MIDUS, CANDOR, PANDORA, and any set the data thread marks sealed. Statistics over groups are reported: estimates, intervals, correlations, model coefficients, test statistics, null bands, sample sizes, and counts or means for cells of 11 people or more. What never leaves: a row, a value, a text, a per-person figure, a list keyed by person, a minimum or maximum, a cell of 10 or fewer, a voice print or face print, and weights or vectors fitted on the rows. The gate and its checks stay as installed.

## 3. How terms are read

A figure is kept in only by a sentence in the source's own retained terms that bars reporting results. The report quotes that sentence and gives everything else. Silence, "none stated", "research only", "non-commercial" and "do not redistribute the data" do not keep a statistic in. Where the wording is unclear, the reading that reports is taken, and the report says which reading it took.

## 4. Sealed jobs that would be withheld

Each sealed job registers three forms before it runs: the fine table, a coarse table with cells merged until each holds 11 or more, and a summary line (the pooled estimate, its interval and its size). Inside the seal the job counts its cells by the gate's own rule and writes out only the finest form that meets it. The gate then checks that one form as installed. A withheld form is not asked again. If the gate still withholds, the report says so, with the gate's code and what would release it. A withheld cell no longer voids a row without a report.

## 5. The report

One page a study, in this order. Every number is built into the text by a script from the released table.

1. The question in one sentence, and the prediction registered before data.
2. The source, its class, its terms line, and how many people and units were counted.
3. Each registered quantity: estimate, interval, size, the null band where one exists, and its direction against the prediction.
4. The verdict word and the sentence it rests on.
5. The limit sentence.
6. What is withheld, by which rule or quoted sentence, and what would release it.
7. The table file and the script.

A report is written from released figures only. No reader, local or remote, is used to put a withheld figure into words.

Before a push, a script checks each class S report: no cell of 10 or fewer, no table keyed by person, no minimum or maximum.

## 6. The digest

One file in each repository, `HELD_RESULTS_DIGEST.md` beside the returns, rebuilt by script at every return. One line a study: id, week, the question in fifteen words or fewer, verdict, headline estimate with interval and size, limit, status (in full, coarse, or withheld with the reason), and the path of the report. Contrasts whose whole interval ran against the prediction are listed like any other. This file is what the theory thread and the results thread read.

## 7. The pass over earlier studies

1. **Inventory.** Every return since the record began that holds a figure in an internal return, a restricted companion, a local copy, a corpus release check or a gate withholding. One line each: id, how it is held, where the figures are, and what a report needs.
2. **Class P returns.** Reports are written from the numerical sheets already held locally. Nothing is rerun.
3. **Corpus release checks on open corpora.** Read again under class P.
4. **Class S withholdings.** Listed with the gate's code. Where one invocation under section 4 would give a report, it is run. Up to ten sealed invocations are allowed for this pass, counted apart from any week's allowance.
5. **Order.** The studies the latest final return lists first, then backward by week. The pass runs in free slots and does not hold a running row. The digest's first push comes within six hours.

## 8. Limits

The analyst is not a lawyer. Section 3 rests on the common terms of public research data, which bar copying the data and naming people and do not bar publishing findings. The data thread is asked to quote the retained terms of the three class S sources, and a quoted sentence that bars reporting results amends the reports for that source. A figure once pushed to a public record cannot be taken back, which is why class S keeps its floor of 11 and its check before a push.

## 9. For the corrections log

| Document | Topic | Corrected to | Class | How found |
|---|---|---|---|---|
| Both sheets of 27 November (engine amendment CY and the return; Sounding Line's return line, row LGH6 and row ATL2) | Carried forward the practice of keeping figures from "tests only" and restricted sources in an internal record, so that a landed study gave the theory thread no number | Ruling R48: every study returns a report, and the figures of class P sources are reported in full | scope | The curator, on a note from the theory thread |
