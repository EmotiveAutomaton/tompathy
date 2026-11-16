# Engine scoreboard

Only measured engine accuracy belongs here. Pending rows are not zero scores.
Field labels remain off. A passed software test is not a natural-writing result.

## Readers packet (no pack qualified)

Fixed Crowd-enVENT test, 1,200 writer-labelled reports; development writers are
held out of training but this commissioned test is not writer-disjoint. No ledger
row or admission. Fine-tuning is complete; later cards remain pending.

| Reader | Macro-F1 | Writer-bootstrap 95% interval | BOW floor | One / five people | B1 bar | Receipt |
|---|---|---|---|---|---|---|
| Potion frozen | 0.3919 | [0.3644, 0.4177] | 0.3886 | 0.492 / 0.565 | 0.49 and lower interval above BOW: missed | [L0–L2](../engine/validation/readers-envent-2026-11.json) |
| MiniLM frozen | 0.4252 | [0.3948, 0.4518] | 0.3886 | 0.492 / 0.565 | 0.49 and lower interval above BOW: missed | [L0–L2](../engine/validation/readers-envent-2026-11.json) |
| MiniLM tuned, development-selected seed 47 | 0.4738 | [0.4428, 0.5017] | 0.3886 | 0.492 / 0.565 | 0.49: missed | [L3](../engine/validation/readers-envent-finetuned-2026-11.json) |

Observed neutral checks also miss their bars. Readable-feature RMSEs improve on
constant and one-reader floors; that does not qualify the channel label head.
See [the readers record](ENGINE_READERS_2026-11-17.md) for timings and exclusions.

TP12's 60-report peaked mixtures, no neutral: best-estimator MAE/largest-label
accuracy is human **0.0389/0.7917**, released author model **0.0345/0.8292**,
BOW **0.0438/0.7900**, Potion **0.0457/0.8017**, MiniLM **0.0383/0.8483**.
The constant is **0.1286/0.0950**. MiniLM meets this primary counting bar using
probability EM, but no learned reader qualifies the predeclared NNLS prior/minimum
policy across mixture shapes and neutral fractions. The selected NNLS priors
also fail the 80%-neutral improvement check for the learned heads. Shares are
conditional on emotion after correcting all 13 labels; these are simulated bags
of real held-out reports, not measured page understanding. [Counting receipt](../engine/validation/readers-counting-2026-11.json).

The selected tuned reader's separate TP12-L3 row is **0.0392/0.8208** using
probability EM, clearing the primary bar only. Its selected NNLS prior is 2;
no tested minimum qualifies. At 80% neutral, raw versus selected-policy
MAE/top-label accuracy is **0.1062/0.2717** versus **0.1082/0.2667**. Probability
EM improves that scenario, but is not the qualified TS2 policy. Existing reference
rows were carried unchanged. [Tuned counting receipt](../engine/validation/readers-counting-finetuned-2026-11.json).

TP14 is resource-stopped with no validity score: achievement and affiliation
each saved 8,873 scores; power observed 5,446 but retained only 128 durable scores
because of a now-repaired checkpoint defect. The second instrument and IM1 are
unrun. First-150 timings were 51.98/52.67 seconds, exceeding the five-second
offline-only threshold. Agreement, human-key and known-groups comparisons remain
unavailable; missing results are not failures or zeros. [Partial motive receipt](../engine/validation/readers-motives-2026-11.json).

TP18's combined pause features score AUC **0.572109** against the same
five-feature baseline **0.551157**, a gain of **0.020952**, with paired
writer-bootstrap interval **[0.010392, 0.031102]**. The lower bound misses 0.02;
the registered gate fails. This covers 193,947 eligible words from the
1,399-session source, with 60 supported writers and one single-class exclusion.
Single additions remain exploratory. [TP18 aggregate](../engine/validation/readers-attention-features-2026-11.json).

TP16 worry completed five writer-held-out folds on 2,500 released long texts.
Intervals resample the fixed held-out forecasts by writer (1,000 draws).

| Worry reader | R² | 95% writer interval | Correlation | RMSE | 0.16 main / 0.25 stretch |
|---|---|---|---|---|---|
| Constant | -0.0003 | [-0.0024, 0.000003] | -0.0237 | 1.7650 | missed / missed |
| BOW Ridge | 0.2063 | [0.1888, 0.2226] | 0.5076 | 1.5722 | passed / missed |
| Potion frozen | 0.2164 | [0.1904, 0.2417] | 0.4667 | 1.5622 | passed / missed |
| MiniLM frozen | 0.2225 | [0.1959, 0.2488] | 0.4726 | 1.5561 | passed / missed |
| MiniLM fine-tuned | 0.3013 | [0.2671, 0.3319] | 0.5542 | 1.4751 | passed / passed |

Each model fold uses 1,800 fitting writers, 200 development writers and 500 held-out
writers. Encoder rows read the first 128 tokens; BOW uses the whole text. The
corrected-share and plans checks remain blocked by the unqualified TP12 policy.
This is self-reported worry in one UK population/event, with no maker admission
or live default change. [Worry aggregate](../engine/validation/readers-worry-2026-11.json).

The separately preplanned fixed-third hidden-state probe scores AUC **0.536290**
against its subset's five-feature baseline **0.558040**, gain **-0.021750** with
paired writer-bootstrap interval **[-0.037904, -0.008198]**. The >0.02 lower-bound
bar is missed. It covers 466 sessions and 65,395 eligible words, with 49 supported
writers and one single-class exclusion. Its subset differs from the primary;
the result changes no original gate or default. [Probe aggregate](../engine/validation/readers-attention-probe-2026-11.json).

TP19's completed five-option choice rows cover 5,719 taken suggestions and 60
writers: deterministic accuracy **0.286239**, plus reader **0.279594**, plus earlier
personal picks **0.281343** (chance 0.2). Nested gains are **-0.006645** with writer
interval **[-0.014919, 0.001878]**, then **0.001749** with **[-0.004469, 0.008645]**.
Both choice gates miss and remain fixed. Baseline handling log loss is 0.899663
over 8,988 decisions. The repaired added-reader row gives **0.905257**, with gain
**-0.005594** and writer interval **[-0.010540, -0.001216]**, missing its bar.
Personal-history handling gives **0.904725**, gain **0.000532** with interval
**[-0.005934, 0.006708]**, also missing its bar. The BOW choice control gives
accuracy **0.237454**, log loss **1.606642**. All four nested gain gates fail.
The card is complete; original completed rows survived the numerical continuation
unchanged. No maker admission follows. [Choice/handling aggregate](../engine/validation/readers-choices-2026-11.json).

TP15 has saved all five writer-held-out folds on 1,860 reports from 372 writers.
These held-out rows are complete; the separate descriptive group comparison is
still running and final aggregate landing awaits terminal exit and release.

| Concern/distress reader | Concern correlation | Distress correlation | 0.40 primary / 0.54 stretch on both |
|---|---|---|---|
| Constant | -0.0468 | -0.0786 | missed / missed |
| BOW Ridge | 0.3572 | 0.3733 | missed / missed |
| Potion frozen | 0.3523 | 0.3747 | missed / missed |
| MiniLM frozen | 0.3273 | 0.3285 | missed / missed |
| MiniLM fine-tuned | 0.3875 | 0.3791 | missed / missed |

Fine-tuned 95% writer intervals are [0.3446, 0.4290] for concern and
[0.3285, 0.4275] for distress, using 1,000 whole-writer resamples of fixed
forecasts. Concern partial correlation controlling reported distress is 0.3127.
Descriptive caring-label contrasts cannot replace this failed primary or qualify
CARE/maker inference. [Observed rows and coverage](ENGINE_READERS_2026-11-17.md).

## Registered attention and earlier pilots

TP13's writer-disjoint published test comparisons use the development-selected
encoder. EmpatheticDialogues accuracy/macro-F1 is **0.4912/0.4843** against BOW
**0.4594/0.4530** (constant **0.0499/0.0030**), on 2,547 situations. GoEmotions
macro/micro-F1 is **0.2734/0.4069** against BOW **0.3375/0.4745** (constant **0/0**),
on 5,427 comments. Known held-out writers are purged from training; unknown
writers remain explicit. Feature-row median correlation/own-nearest fraction is
**0.8879/3 of 9** for ED and **0.7225/3 of 10** for Go. Both Part B gates miss;
all proposed new rows remain withheld. These different label sets and protocols
do not establish equivalence to published model scores. [Transfer aggregate](../engine/validation/readers-transfer-2026-11.json).

TP11's frozen MiniLM clears its five writer-held-out twins comparisons: AUCs
0.8038/0.7021/0.8958/0.8535/0.9208 against BOW
0.7689/0.6884/0.8590/0.7797/0.8957 (constant 0.5).
Potion misses the guilt/shame tolerance. The proposed stake-column transfer does
not clear every left-out label and enables no need reading. Human subset, pooled
writer intervals, and the unresolved saved-preflight discrepancy are retained in
the [working record](ENGINE_READERS_2026-11-17.md#tp11-what-the-event-was-about) and
[aggregate](../engine/validation/readers-stakes-2026-11.json).

| Capability | Benchmark | Units | Metric | Baseline | Engine | 95% interval | Bar | Date | Receipt |
|---|---|---|---|---|---|---|---|---|---|
| attention · row 1 | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | 0.5512 | 0.5677 | [0.0081, 0.0241] (gain) | +0.02 | 2026-11-14 | [complete](../engine/validation/attention-stops-2026-11.json) |
| attention · row 2 | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | 0.5590 | 0.5600 | [-0.0002, 0.0020] (gain) | +0.01 | 2026-11-14 | [complete](../engine/validation/attention-stops-2026-11.json) |
| attention · row 3 | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | — | — | — | +0.00 | 2026-11-14 | [unavailable](../engine/validation/attention-stops-2026-11.json) |
| ai-involvement · row 1 | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | 0.6002 | 0.8055 | [0.1733, 0.2361] (gain) | +0.02 | 2026-11-14 | [complete](../engine/validation/ai-involvement-2026-11.json) |
| ai-involvement · row 2 | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | 0.8158 | 0.8186 | [-0.0013, 0.0068] (gain) | +0.01 | 2026-11-14 | [complete](../engine/validation/ai-involvement-2026-11.json) |
| ai-involvement · row 3 | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | — | — | — | +0.00 | 2026-11-14 | [unavailable](../engine/validation/ai-involvement-2026-11.json) |
| edit-reasons | Stack Exchange single-hunk body edits, comment-derived labels | edits | macro-F1 | 0.2583 | 0.3175 | — |  | 2026-11-14 | [stopped](../engine/validation/edit-reasons-2026-11.json) |
| edit-reasons | Stack Exchange single-hunk body edits, comment-derived labels | edits | two-way accuracy | 0.5000 | 0.5275 | — |  | 2026-11-14 | [stopped](../engine/validation/edit-reasons-2026-11.json) |
| goals (pilot) | PEP/EIP Motivation ranking pilot, abstract and summary removed | documents / authors | top-1; MRR | — | — | — |  | 2026-11-14 | [stopped](../engine/validation/goals-motivation-pilot-2026-11.json) |

History contrasts and exploratory variants remain separately identified in each receipt.
A CoAuthor involvement result applies to accepted suggestions from its 2021 model; it does not establish modern whole-document detection.

## Two-day pilots

These are separate pilot scopes. No row enables a detector, values reading or field label.

| Row | Status | Result | Scope / receipt |
|---|---|---|---|
| ai-robustness (pilot) | stopped | 2026/2500 documents; stratified rates and intervals in receipt | [RAID training pilot; fixed 5% calibration false-alarm threshold; no detector admission](../engine/validation/ai-robustness-pilot-2026-11.json) |
| choice (pilot) | waiting-for-EX5 | pending; no score | [Public accepted-answer choice; not values](../engine/validation/choice-pilot-2026-11.json) |
| human-edits  | unlaunched; bounded queue closed | no score; reserved memory gate never recovered | [IteraTeR balanced human intentions; fixed Q8; no fitting](../engine/validation/edit-reasons-human-2026-11.json) |
| human-features  | complete | macro-F1 0.0968; abstentions 0/300 | [IteraTeR; EX2-only deterministic-feature control](../engine/validation/edit-reasons-human-features-2026-11.json) |
| weightonly  | complete | a: pass; b: pass; c: pass; d: pass; e: pass | [W1 converted local base weights; five ordered gates](../engine/validation/speed-weightonly-2026-11.json) |
| first-paint  | complete | 6 first-600/whole-text timing pairs | [Three frozen texts; CPU; no default change](../engine/validation/first-paint-2026-11.json) |
| history-ladder  | complete | 6/6 exploratory rungs; coverage and writer intervals in receipt | [Exploratory earlier-session history; registered primaries unchanged](../engine/validation/history-ladder-2026-11.json) |

Edit-reasons human-labelled lines are separate from the comment-labelled EX2 result.
Goals also report candidate-only TF-IDF, reader-alone and top-five reranking in their receipt.
Live progress and dependencies: [two-day working record](ENGINE_TWO_DAY_2026-11-14.md).
