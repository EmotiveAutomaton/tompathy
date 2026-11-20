# TP24 amended recalled-event inputs

Use the eight feature assignments in the landed RD1 receipt. Only the four
preregistered RD1 candidates can be assigned to B. A missing answer from the
assigned reader leaves the corresponding feature missing. Record the attempted,
valid and common counts before any comparison. Evaluate all controls on the
same complete reports in each view.

| Source | Reports | Forecast to reuse |
|---|---:|---|
| Corrected SP1 pilot | 500 | Reader B’s original first pass, including its 200 timing reports |
| Q1 | 350 | B’s F1 answers |
| Q2 | 5,400 | B’s answers on the original training reports |
| Q5 after development selection | 350 | B’s standard eight-answer F2 pass, linked locally by opaque ID |

The first three sources make the initial 6,250-report roster. The fourth
extends it to 6,600. Preserve both stages and their denominators. Keep B’s
model, corrected questions, options and feature order fixed across the four
sources. A and W are outside this comparison.

The filed selected TP10-L3 seed already supplies the trained comparator for
1,200 reports. For the other 5,400, the MiniLM regression component of G2
uses five writer-disjoint outer folds of 1,080 reports each. Its original
pretrained weights, two-head objective, development selection and test
assignment are recorded. These predictions can be joined by report ID as
their folds become available. Larger encoders are RD2 candidates only.
Count the 1,200 previously held-out rows separately because the original
TP10 split allowed some training-writer overlap. A full-cohort result
requires verified feature coverage. Read the original and prompted forecasts
side by side on their available overlap.

Retain the original C0 need-tag scores, direct frozen MiniLM vectors, fixed
tense rule, writer-held-out downstream fits, five-way loss-word table and
its three bars. Compare the table profile with the filed TP30 predictions
on the same reports. The chat prefix at the morning boundary is a separate
description. Its table must use the same feature assignments and report the
eligible writer-word count and each missing input. The packet assigns seven
writer stand-ins in this source. The fixed trigger table defines scores for
five loss channels. Keep the emitted rows and the full eligible denominator
visible in that comparison.
