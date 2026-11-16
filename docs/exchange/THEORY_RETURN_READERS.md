# Readers packet — theory return

15 November 2026. Local reproduction and initial reader measurements; no new scientific admission
and **no ledger row**. Implementation and subsequent measured cards are tracked in
[the working record](../ENGINE_READERS_2026-11-17.md).

The supplied Crowd-enVENT reader/model baselines reproduced at their reported
precision. Corrected counting reproduced the improvement on concentrated mixes
and the deterioration on flatter small bags. TP12 now finds that MiniLM's
probability-based estimate clears the concentrated 60-report bar (MAE 0.0383,
largest-label accuracy 0.8483). But no learned reader qualifies the fixed NNLS
prior/minimum rule across all tested scenarios. Selected priors fail the expected
improvement at 80% neutral; raw counts are not page shares, and no share pack is
qualified. This tests the analyst's counting proposal and does not settle it.

Fine-tuning improved the label score, but the development-selected model's
macro-F1 is 0.4738 [0.4428, 0.5017], missing the 0.49 bar. All three fixed seeds
miss; the highest test seed is not substituted for the development choice.
The eight-feature error improves on constant and one-reader floors. Neutral
and confidence requirements still fail. The next step of expanding the label
training through model labellers awaits the owner's ruling.

The selected tuned model also meets the narrow concentrated-mixture counting
bar (0.0392/0.8208), but again has no qualified prior/minimum policy. Its selected
NNLS prior worsens both scores at 80% neutral; probability EM improves them there.
This distinction remains explicit rather than changing the chosen policy after
seeing the results. No corrected page-share or maker reading is enabled.

The fixed 1,200-report test has writer overlap with the remaining reports.
Comparable scores on overlapping and new writers do not establish absence of
leakage. This split is retained for the commissioned reproduction, while the
twins and other writer-holdout cards must retain separate grouped splits.

## What a trigger is made of

The analyst's proposed stake description remains unsettled. MiniLM distinguishes
all five twins above the ratings baseline and within the required BOW tolerance.
The table is mean AUC across writer-held-out folds; the constant is 0.5.

| Pair | Ratings | BOW | Potion | MiniLM |
|---|---|---|---|---|
| Pride / joy | 0.6192 | 0.7689 | 0.7573 | 0.8038 |
| Guilt / shame | 0.6170 | 0.6884 | 0.6583 | 0.7021 |
| Fear / sadness | 0.7246 | 0.8590 | 0.8763 | 0.8958 |
| Anger / disgust | 0.7466 | 0.7797 | 0.8148 | 0.8535 |
| Trust / joy | 0.8015 | 0.8957 | 0.9068 | 0.9208 |

On a label and its writers held out from fitting:

| Label | Potion joint / marginal chance | MiniLM joint / marginal chance | MiniLM feature-shape correlation / own-row rank |
|---|---|---|---|
| Pride | 0 / 0.000026 | 0.0036 / 0.000030 | 0.9906 / 1 |
| Shame | 0 / 0.000310 | 0.0073 / 0.002054 | 0.9026 / 1 |
| Sadness | 0.3236 / 0.2988 | 0.2945 / 0.2700 | 0.9261 / 1 |
| Anger | 0.0182 / 0.0266 | 0.0145 / 0.0273 | 0.9730 / 1 |
| Joy | 0.3782 / 0.3676 | 0.4600 / 0.4460 | 0.9875 / 1 |

Anger's columns miss marginal chance. Pride and shame produce few complete
descriptions even where joint accuracy exceeds that low chance. Feature shapes
transfer well, but correlation and joint accuracy cannot be compared numerically
as the same score. These results do not establish a compositional need basis.
The unchanged supplied twins scripts produce our current baseline values;
saved preflight AUCs differ by up to 0.012, with the cause unresolved. No split
or gate was altered to recover them. Human comparisons and exact bindings are in
the [working record](../ENGINE_READERS_2026-11-17.md#tp11-what-the-event-was-about).

The analyst's motive-to-need proposal remains unsettled. TP14 hit its memory
floor before both instruments completed. Achievement and affiliation retain
8,873 scores each; power reached 5,446 texts but only 128 scores were durable
because a checkpoint defect interrupted saves. The defect is repaired for future
runs; the stopped inference is not repeated. Agreement and known-groups results
are unavailable, and no IM1 table was created or handed off. This is a resource
block, not evidence for or against the proposed mapping. The first two models
took about 52 seconds per 150 texts, excluding loading, so they miss the live-speed
threshold. [Partial aggregate](../../engine/validation/readers-motives-2026-11.json).

The packet's proposal to combine pause features remains unqualified. TP18's
combined row improved AUC from 0.551157 to 0.572109: gain 0.020952, paired writer
interval [0.010392, 0.031102]. The required lower bound above 0.02 is not met.
Forward context makes this an offline comparison; no live reading claim follows.
The separately preplanned fixed-third Smol hidden-state probe also misses:
baseline AUC 0.558040 versus probe 0.536290, gain -0.021750 with paired writer
interval [-0.037904, -0.008198]. This covers 466 sessions and 65,395 eligible
words, with 49 supported writers and one single-class exclusion. It offers no
support for the proposed improvement on this subset and does not replace the
failed primary or change a default. [TP18 aggregate](../../engine/validation/readers-attention-features-2026-11.json),
[probe aggregate](../../engine/validation/readers-attention-probe-2026-11.json).

The analyst's proposed cross-corpus feature-row transfer is not established.
TP13 completed with ED accuracy/macro-F1 0.4912/0.4843 versus BOW 0.4594/0.4530;
Go macro/micro-F1 is 0.2734/0.4069 versus BOW 0.3375/0.4745. The ED feature
shapes correlate at median 0.8879, but only 3/9 are nearest their own label;
Go gives 0.7225 and 3/10. Both predeclared gates miss. The new caring, lonely,
jealous, grateful, curiosity, desire and amusement rows remain withheld instead
of being filled in from an unqualified model. On restricted shared labels,
cross-corpus accuracy falls by 0.0975/0.0467 for Crowd-to-ED/the reverse, and
0.5438/0.3484 for Crowd-to-Go/the reverse. These losses are specific to the
declared label aliases, exclusions and protocols. [Transfer aggregate](../../engine/validation/readers-transfer-2026-11.json).

The analyst's proposed worry reading now has support on this target-task benchmark;
its interpretation as general Stress or a maker's state remains unsettled.
Five writer-held-out folds on 2,500 UK COVID-era reports give fine-tuned MiniLM
R² **0.3013** (writer interval **[0.2671, 0.3319]**), correlation **0.5542** and
RMSE **1.4751**, clearing the 0.16 main and 0.25 stretch bars. BOW/Potion/frozen
MiniLM give R² 0.2063/0.2164/0.2225. Encoder rows use only the first 128 tokens;
the result is about writers' reported worry in this population and event.
The original completed fold survived the host restart and is preserved unchanged
in the final forecasts. [Worry aggregate](../../engine/validation/readers-worry-2026-11.json).

The proposal that plans accompany lower worry is still untested here. TP16's
corrected-share and plans checks require TP12's qualified prior/minimum policy,
which remains unavailable; no substitute was used. This result creates no maker
admission or live default change.

The completed TP19 choice comparison does not support an improvement from the
reader or earlier personal picks: accuracies are 0.286239/0.279594/0.281343,
and both nested whole-writer gain intervals include zero. After the bounded
numerical repair, the added-reader handling row also misses: log loss worsens
from 0.899663 to 0.905257, gain -0.005594 with writer interval
[-0.010540, -0.001216]. Personal-history handling gives log loss 0.904725,
gain 0.000532 with interval [-0.005934, 0.006708], also missing its bar. BOW
choice accuracy is 0.237454. The card is complete with all four gain gates failed;
completed choice rows and gates were reused unchanged. Motives remain omitted.
This result does not support the proposed personal-choice reading and creates no
maker admission. [Completed aggregate](../../engine/validation/readers-choices-2026-11.json).

The concern/distress reader has completed its five writer-held-out folds on
1,860 reports from 372 writers. Fine-tuned correlations are 0.3875 for concern
and 0.3791 for distress, below the required 0.40 on both; the 0.54 stretch bar
also misses. Writer intervals are [0.3446, 0.4290] and [0.3285, 0.4275], with
concern partial correlation 0.3127 after controlling reported distress. All
controls miss the primary too. The separately preplanned descriptive caring
group comparisons remain running; they cannot replace the held-out result or
provide an independent concern answer key. This does not qualify CARE/maker
inference. Final aggregate landing awaits terminal state and release.

The complete two-instrument comparison remains unavailable. Proposed channel/stake
mappings have not been ruled on by the owner. Final-text readings remain passage
readings and cannot populate the maker tier.
