# Readers packet — theory return

November 16, 05:03 Pacific: TP23 frozen MiniLM completed and clears both bars.
Story mean AUC .776711539; transfer mean gain .096892812, all five pairs above
.03. Pride/joy, guilt/shame, fear/sadness, anger/disgust and trust/joy gains are
.158994021 / .050853357 / .118851596 / .063459785 / .092305304. In particular,
this rung improves guilt/shame under the registered comparison, unlike BOW's
sub-.03 result. Thirteen-label macro-F1: ratings .377775213, tags .270293849,
both .461516370. Final selection waits for the original fine-tuned seeds and
memory-eligible optional base rung; no IM2 handoff yet. TP25's failed gate still
blocks serving, and no maker inference follows. Seed-23 folds zero through three
subsequently completed, each with 619 saved artifacts verified; held-out counts
are 9,615 / 9,615 / 9,615 / 9,610 and the rows are disjoint.
The fifth original fold is running.
[Frozen need aggregate](../../engine/validation/readers-need-frozen-2026-11.json),
source `1d996fdce019a3cbf60bb55ad7cb77fdd0dc6d5481e0f95f8a8c9b4025334bf4`.

November 16 update: TP25 completed with no qualified gate. Held-out positive
detection is .396033058 / .573237237 / .265881823 for Crowd-enVENT / Go / Story.
At the fixed .5 diagnostic threshold it is silent on 1/40 theme-free items and
173/191 verified revision sentences. No saved grid threshold jointly meets all
requirements. No gate pack, new TP12 policy, gated TP22 or composite serving
follows; no threshold is selected from these external results. Saved predictions,
native exit and exact lease releases are verified.
[Gate aggregate](../../engine/validation/readers-stakes-gate-2026-11.json), source
`7803918cf1969c76aa6e4ee17603cf54c57dc0d91e3107214b6d6c5a9c9f69d1`.
TP27 has since completed as a circular diagnostic: AUC .954120488, baseline gain
.402963976, writer interval [.368969562, .427655734]. Its feature and outcome
share their timing source; no independent accuracy or display claim follows.
[Diagnostic aggregate](../../engine/validation/readers-pause-remainder-diagnostic-2026-11.json),
source `b50cb33c9f05b02ea958393664c132606996dcb7ef8f6859d365f88351c045d6`.
The owner ratified TP23's five-pair table scope; all 25 cells, including gains,
match within .012069799. The extra per-tag misses and BOW packing failure are
retained. A separate source-bound decision enables the unchanged encoder ladder;
frozen MiniLM subsequently completed as reported above. No completed BOW
inference was repeated.

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
controls miss the primary too. The separately preplanned descriptive comparison
is complete: caring-minus-other concern/distress differences are 0.7121/0.2784
on 24,850 ED situations and 0.2587/0.2001 on 54,263 GoEmotions comments.
The fixed full-data head supplies these contrasts, with no independent concern
answer key; they cannot replace the failed held-out result or qualify CARE/maker
inference. Native exit, release and the aggregate source binding are verified.
[Care aggregate](../../engine/validation/readers-care-2026-11.json).


The proposed cause-word reading clears its declared benchmark bars: on 4,613
held-out EmoCause situations, top-one/three/five hit rates are 0.3486/0.6373/0.7462.
Top-three writer interval is [0.6147, 0.6613], compared with BOW 0.5532,
per-item chance 0.3961 and original-order control 0.2703. Validation/test top-three
rates are 0.6029/0.7924; their differing difficulty remains explicit. The fixed
head was trained only on ED's training split; no cause-word annotation was used
to fit or select it. This supports the scoped marked-word task, not the maker's
motives or an admitted live reading. ED remains research-only, with no ledger row.
[Cause-word aggregate](../../engine/validation/readers-cause-words-2026-11.json).


The smaller-reader path does not qualify: Smol135 Q8 fails the fixed numerical
error limit on two long texts, so no cohort accuracy or first-paint candidate
result follows. The separate Smol360 Q4_K_M mixed-type conversion misses the
15-second speed target (91.87/110.50 seconds per 3,000 words on the long texts).
[Small-reader aggregate](../../engine/validation/readers-smol135-2026-11.json).

The proposed longitudinal reading is still untested on people: TP22's exact
counting policy has no qualified minimum, so its guard stopped before any blog
scoring. Successful planted-estimator controls do not supply a human stability
result or an alternative counting policy. [Blocked aggregate](../../engine/validation/readers-longitudinal-2026-11.json).


The assigned negotiation-priority reader misses its declared exact-order bar:
0.3104 accuracy (dialogue interval [0.2914, 0.3304]) versus BOW 0.3562 and
constant 0.1462; the required value is 0.45. Reader top-priority accuracy 0.6043
is a different endpoint and does not rescue that miss. Five dialogue-disjoint
folds cover 2,052 perspectives, but global participant identities are unavailable.
Assigned priorities do not establish values or endorsement, and no maker admission
follows. [Priority aggregate](../../engine/validation/readers-priorities-2026-11.json).

The complete two-instrument comparison remains unavailable. Proposed channel/stake
mappings have not been ruled on by the owner. Final-text readings remain passage
readings and cannot populate the maker tier.


The final carried lexical control completed on the fixed 40-proposal / 38-author
pilot, reproducing the original TF-IDF rows exactly. Top-one accuracy is 0.6500
for TF-IDF, 0.6750 for BM25 and 0.7250 for rarity weighting; mean reciprocal rank
is 0.7294 / 0.7411 / 0.8000. The 2,000-resample whole-author top-one intervals
are [0.4878, 0.8049] / [0.5128, 0.8250] / [0.5853, 0.8537]. No paired gain test
was evaluated; these pilot point differences do not establish reliable superiority
or maker inference. [Lexical-control aggregate](../../engine/validation/readers-goal-controls-2026-11.json).
Its source receipt pin is `f984653714b401682e8151856a61ea56dda15473460bf523d1406ff42f4d29c2`;
no ledger row exists. The bounded queue is closed with the incomplete motive
instrument/IM1 and counting-dependent readings still unresolved. No proposed
mapping, live default or maker-tier admission changes.


### November 15 trigger commission — TP26

Full-data worry refit completed; original TP16 held-out R² 0.301334951 is retained.
Known-group AUCs: Crowd-enVENT 0.700173370 (3300), ED 0.857812050 (5283),
GoEmotions 0.780889933 (18627, 37 overlapping-label comments excluded).
All three point-estimate bars of .70 clear. Forty theme-free texts average
5.946152687 of 9 (range 5.428977013–6.485096455); no plain-prose bar was set.
No independent Stress key, writer estimate, maker admission or live default.
Aggregate: `engine/validation/readers-worry-transfer-2026-11.json`, source pin
`99d507ec9350998b41af76ea95626cd789c78bdc59b607fe24c6ea99dcfb3789`.
Native exit, exact leases and all 175 frozen code files verified. No ledger row.


The trigger infrastructure now includes separately bounded TP23 fold jobs,
conditional gate/calibrated-counting exports and the owner's diagnostic-only
pause residual. That implementation checkpoint preceded the completed TP25 and
TP27 measurements recorded above; remaining unexecuted rows are not science.
The new full TP12 grid is authorized only behind a qualified gate; old failures
and minimum-policy dependencies remain. Current software checks and source
preservation evidence are in the trigger-reader working record.





TP7 EX5 is complete: E1 top-choice .3610 versus best rarity control .3810;
paired gain -.0200, interval [-.0370125, -.0050], fails the >.02 lower-bound bar.
All 2,000 observations are saved. The accepted-not-top-score subset (497) also
misses. Final-score baseline is descriptive because acceptance affects scores.
No values, endorsement, maker or E2 claim. [EX5 aggregate](../../engine/validation/readers-choice-ex5-2026-11.json)
(source `9338d0ffa9386236c2f20a9fc283ccb908d776b64b5ec2dcfc48adc5a23244e2`).


TP23 BOW completed: mean story AUC .728771248; five-pair transfer mean gain
.049646440 with four pairs at least .03. The .06 mean bar fails; no pack.
The supplied five-pair table reproduces within .011934465, while three extra
per-tag story checks differ by .02488 to .03905. Their original failed
reproduction flag is retained. The owner has since ruled that the packet's table
scope governs continuation; all 25 table cells match within .012069799.
No BOW fitting, transfer or failed scientific gate is repeated. TP25 subsequently
completed with failed gates, as recorded above. [BOW aggregate](../../engine/validation/readers-need-bow-2026-11.json),
source `46348623c7450c9cc903ef3f58a0e67109cc5a6db9e30d2a5d646c66b486fd26`.
