# November 14 readers packet — implementation record

Work started 15 November 2026. The root readers packet and its supplied preflight
are the protocol. Backend work is primary; the owner's spoken panel description
supplies the frontend design. This record distinguishes implemented code,
executed benchmarks, and outstanding cards. Nothing here enables a maker reading
or changes a registered research result. New rows have **no ledger row**.

## Implemented foundation and panel

TS2 adds packet 1.11 and `bottom-box-1`, canonical need/channel IDs, empty legacy
upgrades, explicitly benchmarked passage readings and a closed maker tier.
Local packs verify encoder, head, table, license, policy and execution-code pins.
No pack loads by default. Counts are corrected through a held-out error table,
then conditioned on feeling-bearing sentences, with a fixed prior, minimum count
and sentence-bootstrap interval. Release packaging refuses research-only or
constructed packs. No trained pack is currently qualified.

Current Artifact now shows fluencies/channels on the left, reliability-weighted
teardrop echoes, and five need diagrams plus the body on the right. Connected
hover/focus traces arrows and highlights supplied hierarchy/passage links.
Author uses full action drops centered on the current artifact; dated source
facts provide other actions when present. Missing dates/history stay unknown.
Need buttons open detail diagrams. Bands, curves and built-in example connections
are explicitly illustrative; no invented life history or measured need trajectory
is presented. Authored essays and image assets remain unchanged.

Python contract/pack controls and the frontend build passed. Native Chrome
157.0.8103.51 verified the panel, hover, keyboard activation, need details and
Author centering; screenshots were inspected. Evidence is under ignored
`evidence/readers-*`. The final demonstration-link refinement also passed the
targeted native-browser check: hovering a need highlights connected attention
words and expertise nodes. The 53 frontend core checks passed.

The owner's November 15 refinement removes the visible explanatory captions from
Current Artifact and Author. Fluency tips now use Expertise's inward-curving
terminal contour, with a wider left column and smaller fluency labels; channel
lettering keeps its size. Each incoming connection has its own endpoint within
the need graph. Unselected connections are very faint, with stronger arrow ends
and linked-panel emphasis on hover or keyboard focus. The bands have fading left
fins and pointed exits. Body adds narrow Heat/Food/Sleep graphs, and a faint shared
return line leads into Stress and its fading curl. These are display elements,
not calculated stress or newly admitted measurements; details retain that context.

Build `8bee33c1c449` passed TypeScript/build and the targeted native Chrome
157.0.8103.51 check. Screenshots in `evidence/readers-v2-*` were inspected; distinct
vector endpoints, quiet/active opacity, cross-panel highlights, all four new
detail views, keyboard activation, Escape and Author placement passed with no
page errors. The first verification exposed an SVG-verbose accessible button
name and header crowding; explicit button names and header clearance repaired
both before the successful pass. Each disposable browser closed in `finally`.

## Reproduced preflight

The downloaded Crowd-enVENT archive matches SHA-256
`61c22527795669a0556df8d7441d3a7bf13ef8b2266b0433881645e92bf885e6`.
The supplied `pf_b.py` and `pf_c2.py` ran unchanged under the counted CPU protocol.
Both native exits and exact lease releases are verified. The rounded outputs
match the supplied outputs: one human accuracy/F1 **0.504/0.492**, five-reader
majority **0.581/0.565**, authors' five-model mean **0.605/0.594**, and the supplied
5,400-training-report bag-of-words row **0.414/0.393**.

The fixed 1,200-report test overlaps training writers on 628 reports in that
preflight. Similar observed scores for seen/unseen writers do not prove the
absence of leakage. The commissioned fixed split is retained and labelled
explicitly; writer-holdout cards use their separate grouped splits.

For peaked 60-report mixtures, human raw/corrected MAE is **0.0613/0.0395** and
largest-label accuracy **0.71/0.79**. Authors' raw/corrected MAE is **0.0520/0.0327**,
largest-label accuracy **0.77/0.83**. Correction worsens flat 60-report MAE:
**0.0448→0.0524** for people and **0.0395→0.0434** for the authors' model.
The supplied “with shrinkage” row uses a flat prior; new priors remain TP12 work.

## Current evaluation work

An isolated readers environment adds scikit-learn 1.7.2, sentence-transformers
5.1.2, model2vec 0.6.0, joblib 1.5.2, threadpoolctl 3.6.0 and Pillow 12.0.0.
Existing preview package versions and old frozen runs remain untouched.
Potion and MiniLM downloads retain exact revisions, licenses and file hashes.

TP10 L0–L2 implements fixed split/development selection, writer-bootstrap
intervals, confusion/calibration/selective accuracy, the 21-feature head and
eight-feature comparison, timing and neutral controls. The first attempt finished
constant/BOW/Potion, then failed before MiniLM loading because Pillow was absent.
The missing dependency was installed; the bounded continuation preserves those
completed rows and only runs MiniLM. No scientific gate is rerun.

The original TP9 before-sentence sample is joined to published IteraTeR document
domains. The document export omits domains on some rows; unknown domains are
excluded explicitly and leave full neutral-coverage qualification pending.
`wiki` is normalized to `wikipedia`; replacement sentences are never substituted.

The L0–L2 continuation completed, with native exit and exact releases verified.
The [aggregate receipt](../engine/validation/readers-envent-2026-11.json) binds to
source `f3972f768be441d26e06aa3e353756348de2bd82fd29b6d0c4bc288e20fb6248`.
Training/development/test counts are 4,898/502/1,200. After holding out development
writers, 567 test reports still share writers with training.

| Reader | Accuracy | Macro-F1 (writer-bootstrap 95% interval) | Development F1 | First 150 sentences |
|---|---|---|---|---|
| Constant | 0.0833 | 0.0118 [0.0097, 0.0138] | 0.0089 | not timed |
| BOW | 0.4117 | 0.3886 [0.3589, 0.4134] | 0.3724 | not timed |
| Potion frozen | 0.4175 | 0.3919 [0.3644, 0.4177] | 0.4095 | 0.019 s |
| MiniLM frozen | 0.4425 | 0.4252 [0.3948, 0.4518] | 0.4155 | 1.238 s |

No row meets B1 (0.49). MiniLM is selected for the preplanned L3 stage by its
development score, not its test result. Potion meets the one-second encoding
target; MiniLM misses. These timings exclude loading and head/aggregation/UI work.
The eight-feature RMSEs are BOW 1.3923, Potion 1.3787 and MiniLM 1.3273, below
the constant 1.5813 and one-reader 1.4519. Neutral theme silence is 2/40, 0/40
and 12/40 respectively; revision silence is 0.0419, 0.1047 and 0.2147 on 191
verified before sentences. These observed checks miss the bar independently of
the 22 unknown-domain exclusions. No pack is qualified. The full B3 coverage flag
remains pending in this stage receipt; no missing check counts as a pass.

TP12's expanded prior/count experiment completed. Its fixed design uses 20
halves, 60 bags per scenario, sizes 20/60/200, flat/peaked emotion mixtures and
neutral fractions 0/.5/.8. The 144 printed preflight cells match exactly.
Human and released-author rows use error-table EM because no head probabilities
were released; learned heads also report probability EM. Policy selection uses
only corpus-neutral scenarios; external neutral stress cannot tune the prior.
The L3 plan uses MiniLM, three fixed seeds, three epochs, 128-token cap, batch 16,
encoder/head learning rates 2e-5/1e-3 and joint label plus 0.1-rated-feature loss.
Development F1 selects epochs and then the export seed before test interpretation.

The [TP12 aggregate](../engine/validation/readers-counting-2026-11.json) is landed
after verified native exit and exact lease release, source pin
`c671e1c4e0480f35c2ddd6351adf458a96ca61ba94838669d9c78205ac397109`.
On peaked bags of 60 with no neutral, best-estimator MAE/top-label accuracy is
human 0.038945/0.791667, released author model 0.034501/0.829167, constant
0.128598/0.095000, BOW 0.043822/0.790000, Potion 0.045710/0.801667 and MiniLM
0.038309/0.848333. MiniLM's probability-EM row clears the primary bar, not the
stretch bar. This estimates the 12 emotion-label shares conditional on emotion,
after correcting all 13 labels; it is distinct from the original all-label
preflight table that was reproduced first.

The fixed prior/minimum rule selects prior 4 for the learned heads but qualifies
no minimum among 20/60/200 across all shapes and neutral fractions. On peaked
60-report bags with 80% neutral, MiniLM raw/prior-corrected MAE is
0.108595/0.111690 and top-label accuracy 0.271667/0.271667. BOW and Potion's
selected-prior checks also worsen both scores. The expected improvement did not
hold for those policies; no criterion is changed and no share pack is written.
The constant's relative-policy check passes at 60, but its absolute error and
label/neutral gates fail. It is a control, not a qualified reader. External B13
and IteraTeR stress rows retain the corpus error table and do not select policies.

TP10 L3 completed with native exit and exact releases verified. Its
[aggregate](../engine/validation/readers-envent-finetuned-2026-11.json) binds source
`ac5aa48a1e9a83d681969eadf9c7a8268831be97f8fbbc42b259ff72c226b759`.

| Seed | Development F1 | Test accuracy | Test macro-F1 (95% writer interval) |
|---|---|---|---|
| 23 | 0.4744 | 0.5000 | 0.4801 [0.4479, 0.5081] |
| 47, selected | 0.4796 | 0.4908 | 0.4738 [0.4428, 0.5017] |
| 71 | 0.4701 | 0.4967 | 0.4752 [0.4439, 0.5032] |

Mean F1 is 0.4764. Seed 47 was selected by development alone and stays selected.
All seeds miss B1. For the selected seed, neutral recall is 0.43, false-neutral
rate 0.0564, theme-free silence 14/40 and verified revision silence 0.2042.
Full external coverage remains unavailable. Selective accuracy is 0.7955 at 22%
and 0.6517 at 50%, missing B4's second requirement. Readable-feature RMSE 1.3093
beats both floors. The first 150 sentences took 2.974 s excluding loading,
missing the one-second target. No pack is written, and model-labeller expansion
requires the owner's ruling; other explicitly commissioned cards continue.

TP12-L3 completed separately and its native exit/releases and
[aggregate binding](../engine/validation/readers-counting-finetuned-2026-11.json)
are verified, source `218465767e1e80e9749589e117c914642cec6c98bb1480f875046146fe0404b2`.
Only the new head was measured; prior reference rows were reused unchanged.
For peaked 60-report bags without neutral, probability EM gives MAE 0.039173 and
top-label accuracy 0.820833, meeting the primary but not stretch bar. The fixed
policy chooses NNLS prior 2 and no minimum qualifies. With 80% neutral, raw
0.106170/0.271667 becomes 0.108231/0.266667 under that policy. Probability EM's
0.086000/0.417500 is better on this scenario but does not replace the fixed policy.
Dependent corrected-share studies must retain this missing qualification.

At 04:05 Pacific on November 15, the optional L4 admission check found commit
headroom 18.15 GiB versus 23.28 GiB required including the existing reservation.
No L4 process was launched. TP11 then began serially, with native identity and
exact leases verified. Cards will be recorded individually as they finish;
implemented infrastructure is not a completed benchmark. Old expired Q8, goal
and robustness pilots remain preserved and cannot receive a new clock.

## TP21: correction log

Ledger schema 1.1 adds `ProbeAnswer` with a maker, artifact, exact UTF-16 passage
span, content-addressed passage/answer/reading references, and answer time.
Probe answers require Satiate, Switch, Remove or Price; reading corrections have
no probe kind. This creates no reader-facing question or estimate. Existing 1.0
ledgers remain readable and accept their existing record types. Adding this new
type requires an explicit atomic schema upgrade that retains the original header.
No existing ledger was upgraded here. Six targeted checks passed in the sandbox;
two existing atomic-write checks hit Windows access restrictions and passed on
the authorized host-visible rerun. The atomic-write contract was retained.

## Additional intake and implementation

The downloaded EmpatheticDialogues archive contains 24,850 distinct conversation
IDs (19,533/2,770/2,547 train/validation/test). The source is line-delimited with
literal quotes and escaped commas; generic CSV quote parsing incorrectly joined
some lines. Intake recount uses no CSV quote interpretation, with the first
utterance identifying each situation and its writer. Original bytes and the
initial mistaken census remain preserved, with CC BY-NC 4.0 and `research_only: true`.
GoEmotions contains 211,225 individual judgments on 58,011 unique comment IDs;
the dataset card states Apache 2.0. These observed counts replace no source rows.
The three HarmonyLab motive models and SetFit retain MIT cards, exact revisions
and file hashes. SetFit's pickled head is converted to bounded numeric arrays
using inert estimator states; runtime does not load arbitrary pickle classes.
Its independent motive probabilities are not normalized to sum to one.

The remaining original-source intakes are also local and hashed: empathic
reactions (1,860 messages, 372 released response IDs with five messages each,
CC BY 4.0), Real World Worry (2,500 people, repository GPL 3.0, conservatively
research-only pending distribution compatibility), CaSiNo (1,030 dialogues,
CC BY 4.0), and EmoCause (3,775 validation plus 838 test situations). EmoCause's
archive matches its authors' published checksum and remains research-only with
its EmpatheticDialogues source material. The Blog Authorship original download
host failed DNS; the Bar-Ilan mirror matches the published original SHA-256 and
contains 19,320 writer files. No age or sex field is read. Intake is not evaluation.

GoEmotions' published split files use normal TSV quoting, unlike the literal
quotes in EmpatheticDialogues. The adapter checks every published text against
the raw comment with the same ID. All 54,263 published labelled rows now match;
58,011 raw comments and 1,063 comments with unavailable writer identity remain
explicit. The initial format mismatch was repaired before any study used them.
SetFit conversion's probability-equivalence and unsafe-payload rejection checks
passed. TP11 has completed; TP14 later resource-stopped as recorded below.

## TP11: what the event was about

This tests the analyst's proposed description, not a settled theory or need map.
TP11 completed with native exit, lease release and aggregate binding verified:
source `3032a9713d2b46fb98f80e0a7b34626a4163b2db4e6860bb10b793cca28484cf`.
The original frozen encoders keep the pair and left-out fits independent of TP10's
supervised test labels. Each pair uses five writer-held-out folds. The constant
is 0.5 AUC. People supplied 13-way judgments on the fixed validation subset;
outside-pair judgments are tied, and their different subset is explicit.

| Pair | Writer's 21 ratings | BOW | Potion | MiniLM | People, different subset |
|---|---|---|---|---|---|
| Pride / joy | 0.6192 | 0.7689 | 0.7573 | 0.8038 | 0.7203 |
| Guilt / shame | 0.6170 | 0.6884 | 0.6583 | 0.7021 | 0.6392 |
| Fear / sadness | 0.7246 | 0.8590 | 0.8763 | 0.8958 | 0.9045 |
| Anger / disgust | 0.7466 | 0.7797 | 0.8148 | 0.8535 | 0.7203 |
| Trust / joy | 0.8015 | 0.8957 | 0.9068 | 0.9208 | 0.7961 |

MiniLM clears the stated twins bar on all five pairs. Potion misses the allowed
BOW gap for guilt/shame. The receipt retains pooled out-of-fold writer intervals;
they are identified separately from the mean fold AUCs above.

For the left-out comparison, both each label and its writers are removed from
fitting. Joint column accuracy and profile correlation are different quantities;
their magnitudes cannot establish the packet's proposed "no worse" comparison.

| Held-out label | Potion joint / marginal chance | MiniLM joint / marginal chance | MiniLM 21-feature correlation / own-row rank |
|---|---|---|---|
| Pride | 0 / 0.000026 | 0.0036 / 0.000030 | 0.9906 / 1 |
| Shame | 0 / 0.000310 | 0.0073 / 0.002054 | 0.9026 / 1 |
| Sadness | 0.3236 / 0.2988 | 0.2945 / 0.2700 | 0.9261 / 1 |
| Anger | 0.0182 / 0.0266 | 0.0145 / 0.0273 | 0.9730 / 1 |
| Joy | 0.3782 / 0.3676 | 0.4600 / 0.4460 | 0.9875 / 1 |

The proposed columns fail the above-chance requirement for anger and transfer
very few complete pride/shame descriptions. MiniLM's feature shapes rank their
own label first for all five. There is no independent stake answer key and no
admitted need pack. [Aggregate](../engine/validation/readers-stakes-2026-11.json).

The remaining supplied corpus scripts were executed unchanged in a separate
counted preflight job. `pf_a`, `pf_d`, `pf_g` and `pf_h` match saved text exactly;
`pf_i` matches its numbers (the saved output also included one warning-source
line). `pf_e` retains 23/30 signs but its fitted AUCs differ; `pf_f` likewise
differs by up to 0.012 from the saved AUCs. The unchanged scripts reproduce our
current TP11 ratings/BOW rows at printed precision. The supplied environment's
pins are unavailable, so the discrepancy's cause is unresolved; no hyperparameter,
split or acceptance bar was adjusted to recover the old numbers. The independent
writer-held-out comparisons use the same current folds for all fitted rows.

The pack benchmark CLI now uses the same counted single-scorer protocol, checks
resources between batches and honors a bounded stop. Nine targeted reader tests
passed, including a constructed joint-head training/checkpoint round trip and
cooperative stop. No constructed test is scientific evidence.

## TP14: two motive instruments, resource-stopped

This tests the analyst's proposed motive-to-need route; the mapping remains
unsettled. TP14-b stopped at 06:19:57 Pacific on November 15 when commit headroom
fell to 7.14 GiB, below the unchanged 8 GiB floor. Host-visible native exit and
both exact lease releases were verified before the aggregate was landed.
The [partial receipt](../engine/validation/readers-motives-2026-11.json) binds to
source `730c8012116e093dcf28524cfe51756293c8ae13fa90f445b66079d15733b934`.

Achievement and affiliation each retain all 8,873 scores. Their first-150-text
times were 51.98 and 52.67 seconds at two threads, including tokenization and
excluding loading, above the five-second offline-only threshold. Power's progress
counter reached 5,446 texts, but only 128 scores are durable in its partial array.
The checkpoint defect below explains this difference; the unavailable scores
are not reconstructed or counted as saved. The second instrument never started.
Agreement, neutral controls and known-groups comparisons remain unevaluated.
IM1 was not created or copied. No efficacy failure, qualified pack or admission
is inferred from this resource stop.

The next ordered card is TP18. A host-visible admission check at 06:46 Pacific
found 14.27 GiB commit headroom against 15.30 GiB required including the existing
foreign reservation. No new scorer launched; no foreign process or lease changed.
The same counted admission gate applies to the remaining serial cards. TP19 can
use the completed channel/readable-feature head, but cannot use incomplete motive
instruments. The packet directs moving on after a memory stop, not rerunning TP14.

## TP18: additional pause features

This tests the packet's combined-feature proposal on the preserved CoAuthor
word scores. At 07:52 Pacific, host-visible counted admission recovered:
31.04 GiB commit headroom against 15.27 GiB required. TP18 started at 07:53:13
with a fresh immutable snapshot, two CPU threads, below-normal priority and a
three-hour bound. Native ownership and both exact leases were verified.
The original table pin is
`ad2b8cc0ec08538c1345780d5945bc64698a6b6cbf4370e3db275b678f8f7698`.
It fits the combined row and predeclared single additions with the original
eligible words and writer folds; the original attention receipt stays unchanged.
All seven rows completed at 07:55:10 Pacific. Native exit and exact release were
verified, and the [aggregate](../engine/validation/readers-attention-features-2026-11.json)
is bound to source
`e7aae87f2fbca899344e5c11235524d95a340f1994869cd3cab98897fcca44d3`.
The same 193,947 eligible words from the 1,399-session source were evaluated.
Intervals resample 60 supported writers; one single-class writer is excluded.
They condition on the fitted out-of-fold predictions.

| Row | AUC | Gain over baseline | Paired writer-bootstrap 95% gain interval |
|---|---|---|---|
| Original five-feature baseline | 0.551157 | — | — |
| Combined registered features | 0.572109 | 0.020952 | [0.010392, 0.031102] |
| Entropy alone (exploratory) | 0.564887 | 0.013731 | [0.008206, 0.018891] |
| Previous-word surprisal (exploratory) | 0.553568 | 0.002412 | [0.000541, 0.004532] |
| Next-word surprisal (exploratory) | 0.552709 | 0.001553 | [0.000266, 0.002744] |
| Two-words-ahead surprisal (exploratory) | 0.550913 | -0.000244 | [-0.000915, 0.000383] |
| Sentence-tail surprisal (exploratory) | 0.554653 | 0.003497 | [-0.001196, 0.007874] |
| Following punctuation (exploratory) | 0.553306 | 0.002149 | [-0.001027, 0.005117] |

The combined point estimate exceeds 0.02, but the required lower interval bound
does not. The primary therefore misses its gate. No exploratory row replaces
it, and neither a default nor the original registered attention result changes.
Forward-word and sentence-tail inputs describe an offline comparison, not a
causal live predictor.

The separately preplanned hidden-state probe started at 08:26:54 Pacific after
current admission recovered and its prerequisites were verified. It uses the
fixed lowest-hash third of sessions (466; 65,395 eligible words), pinned
SmolLM2-360M in float32, two CPU threads and an eight-hour bound. PCA's 64
components are fitted on each training fold only, alongside the five baseline
features. Native ownership and exact shared/local leases were verified. It
completed at 09:04:54 Pacific; native exit and exact release were verified at
09:18 before landing the [aggregate](../engine/validation/readers-attention-probe-2026-11.json).
Its source receipt pin is
`93e07b858ed6924656801a6b150861bbb42b10b10172f9ba45d913f9384b3f00`.
Within this fixed subset, baseline AUC is 0.558040 and probe AUC is 0.536290:
gain -0.021750, paired writer-bootstrap 95% interval [-0.037904, -0.008198].
The 2,000 draws resample 49 supported writers, excluding one single-class writer,
and condition on fitted out-of-fold predictions. The >0.02 lower-bound bar is
missed. This result applies to its fixed third, changes no default, and cannot
retrospectively recover TP18's primary gate. All 170 frozen files remain matched.

TP13 then passed its actual data/head prerequisites and counted admission:
26.50 GiB commit headroom versus 15.24 GiB required at 09:20 Pacific. It started
from the unchanged development-selected seed 47 and verified EmpatheticDialogues
and GoEmotions inputs, with an eight-hour bound. Its completed results follow;
the failed TP10 pack gates stay failed.

## TP13 completed; TP16 started

TP13 tests the analyst's proposed cross-corpus channel/feature transfer, which
remains unsettled. It completed at 09:33:43 Pacific on November 15; the owner's
early checkpoint verified native exit and exact releases at 09:40:59. The
[aggregate](../engine/validation/readers-transfer-2026-11.json) binds to source
`aecfcc8faca2d7eb9411a5de62b6210f5aa62ac3e5d3db93f1c0467dda4c8b59`.
All 170 frozen files matched. No TP10 inference gate or prior card was rerun.

| Test | Constant | BOW | Selected encoder | Writer-bootstrap 95% macro-F1 interval |
|---|---|---|---|---|
| ED accuracy / macro-F1 | 0.0499 / 0.0030 | 0.4594 / 0.4530 | 0.4912 / 0.4843 | [0.4535, 0.5128] |
| Go macro-F1 / micro-F1 | 0 / 0 | 0.3375 / 0.4745 | 0.2734 / 0.4069 | [0.2496, 0.2927] |

ED uses 19,533 training and 2,547 test situations, with 70 test writers. Go
uses 40,525 training and 5,427 test comments after purging 2,885 training comments
by known held-out writers; 5,322 test writer groups include separate unknown-author
texts. Neither test has a known training-writer overlap. Published model numbers
have different protocols and are references, not matched replications.

On exactly shared labels, Crowd-to-ED accuracy is 0.6412 versus the in-domain
0.7387; ED-to-Crowd is 0.5367 versus 0.5833. Crowd-to-Go is 0.2323 versus 0.7761;
Go-to-Crowd is 0.1632 versus 0.5116. Respective evaluated counts are
708/600/2,591/950, with 1,839/600/2,836/250 excluded. Go restriction requires
exactly one mapped label; these are restricted accuracies, not overall F1.

Part B misses on both corpora. ED median correlation is 0.8879, but only 3/9
shared rows have their own true row nearest. Go gives 0.7225 and 3/10. ED's
caring/lonely/jealous/grateful and Go's caring/curiosity/desire/amusement rows
are therefore withheld. No proposed channel map becomes an admitted measurement.

TP16 began at 09:42:06 Pacific after actual corpus/head/counting prerequisites
and counted admission passed (26.88 GiB commit, 15.24 GiB required). Its native
identity, exact leases and 170-file snapshot were verified. It runs Part A on
2,500 worry texts with five writer-held-out folds and an eight-hour bound.
Parts B/C retain the unqualified selected TP12 prior/minimum dependency.

### TP16: held-out worry

Part A completed at 11:56:58 Pacific on November 15, before the unchanged original
deadline. All 2,500 held-out forecasts are present across five writer-disjoint
folds; each fine-tuned fold uses 1,800 training writers and 200 development writers
for epoch selection, then predicts its 500 unseen writers. The original completed
fold's predictions were verified byte-for-byte against the final arrays after
recovery. All 170 frozen code files still match the launch manifest. Host-visible
native exit and both exact releases were verified at 12:25:08 Pacific.

| Row | R² (95% writer-bootstrap interval; 1,000 resamples) | Correlation | RMSE | Main / stretch |
|---|---|---|---|---|
| Constant | -0.000317 [-0.002384, 0.000003] | -0.023725 | 1.765049 | missed / missed |
| BOW Ridge | 0.206311 [0.188782, 0.222619] | 0.507612 | 1.572220 | passed / missed |
| Potion frozen | 0.216375 [0.190354, 0.241672] | 0.466663 | 1.562220 | passed / missed |
| MiniLM frozen | 0.222460 [0.195916, 0.248843] | 0.472598 | 1.556143 | passed / missed |
| MiniLM fine-tuned | 0.301335 [0.267053, 0.331896] | 0.554197 | 1.475104 | passed / passed |

The fine-tuned row clears the registered 0.16 R² main bar and 0.25 stretch bar.
Its correlation interval is [0.524709, 0.580033] and RMSE interval
[1.426439, 1.523776]; no resample was undefined. These are intervals for fixed
held-out forecasts, not fresh training across resamples. BOW uses whole texts;
embedding/fine-tuned rows use the first 128 tokens. The quoted paper error 1.26
is a reference with a different protocol, not a result reproduced here.

Part B's corrected label shares and Part C's plans partial correlation remain
dependency-blocked: the selected TP12 NNLS prior 2 has no qualified minimum.
No replacement minimum, uncorrected substitute or plans result is manufactured.
This supports prediction of self-reported worry in this one-country, one-month
COVID-era population; it does not establish general Stress, a personal value,
maker inference or production admission. No ledger row or default changes.

The aggregate is [readers-worry-2026-11.json](../engine/validation/readers-worry-2026-11.json),
source receipt pin `99da1d6376ce2cdd480afb2d9f62f7330f4399b4f614eddcda8dbe5aacf7d457`,
public pin `9940c8d168bc17905f990db326bd02eb0c279d7335ba105e15c5fde03e6698ea`.
Both failed/interrupted attempts and their exact continuation provenance remain
preserved; no completed fold or embedding inference was repeated.

## Engineering repairs and limits

TP16's first attempt failed at 09:43:31 Pacific on November 15, before completing
fold zero: sklearn Ridge returned a one-dimensional single-target prediction,
which could not fill the runner's two-dimensional target table. Host-visible
inspection verified native exit and both exact lease releases at 10:26. This is
an engineering failure with no evaluated worry score or scientific gate result.

The adapter now restores the single-target axis and rejects other shape mismatches.
Six targeted cases cover dense/sparse one- and two-target Ridge predictions,
verified cache reuse without encoding, changed-input/completed-source rejection,
and preservation of the original retry deadline. Ruff passed after import ordering
was corrected. The first bounded retry, `tp16-b`, started at 10:33:18 Pacific with
fresh output and a new frozen snapshot. Native ownership and both exact leases
were verified. It retains the original 17:42:06 Pacific deadline; only one further
engineering retry remains, if needed within that limit.

Both complete initial embedding tables were independently copied and SHA-256
verified: Potion 2,500 by 256 and MiniLM 2,500 by 384. The cache keys bind the
same ordered texts, model intake/files, package versions and byte-identical
encoding code. No completed forward inference is repeated. The original 170-file
snapshot, failure, receipt and caches remain unchanged. Retry provenance is
retained in its receipt. Current counted admission passed with 21.33 GiB commit
against 15.35 GiB required. TP16's missing TP12 policy remains a dependency;
neither the repair nor the retry permits an invented page-share minimum.

The delivered 11:05 Pacific checkpoint found that the host had restarted at
10:57:46, after TP16-b's last saved progress at 10:46:38. Host-visible native
inspection confirmed the scorer and its Python launcher were absent. There was
no application exception or release receipt; this is a host interruption, not a
measured memory-floor or scientific failure. Exactly this run's two matching
orphaned leases were backed up and released, with no foreign changes. The
post-restart recovery is explicitly distinguished from a runner-generated exit
receipt; independent exit/release verification passed at 11:08:36 Pacific.

Fold zero's 500 held-out forecasts, all three development epochs and 14 model
artifacts survived, along with both complete embedding tables. Fold one stopped
at 560/1,800 examples in its first epoch and had no durable weights. The final
bounded continuation reuses the complete fold without fitting or predicting it
again, and restarts only the unfinished fold. It retains the original 17:42:06
Pacific deadline. No full worry score has yet been evaluated, so the interrupted
attempt remains private with its preserved failure and restart provenance.

Recovery validates the host-restart audit, every preserved artifact, identical
training code, fold count, held-out positions, untouched future rows, target
scaling and copied model hashes. A preflight caught Windows path separators in
the audit; normalization was repaired before launch, preserving both preflight
attempts. Eight targeted cases passed, including both path formats and a mocked
full runner proving that the completed fold is skipped. Ruff passed. Admission
at 11:12:48 Pacific had 66.54 GiB commit against 14.00 GiB required. `tp16-c` is
the second and final bounded retry; no further retry is authorized under this
card's existing engineering allowance.

At the owner's follow-up, the preservation audit rechecked all nine public readers
receipts against their exact private source bytes, aggregate contents and snapshot/
launcher bindings. All passed. TP16-b's 195 preserved files still match its recovery
manifest; all three TP16 code snapshots retain their 170 recorded files. The
continued run retains the original 500 forecasts per control, all 14 completed-fold
artifacts and both exact embedding tables. Host-visible process and shared/local
lease ownership passed, with a fresh 11:17:22 Pacific heartbeat and fold one in
epoch two. The original deadline and one 11:45 Pacific checkpoint remain intact.
This verifies saved-result preservation, not recovery of previously unsaved work:
the interrupted first-epoch training segment restarted, and the earlier TP14 power
score loss remains explicitly recorded above. Private audit:
`.local/readers/preservation-audit-20261115-owner.json`.

The probe's source receipt already names its upstream primary. During landing
review, the reporter's dictionary merge would have overwritten the aggregate's
own source hash with that upstream hash. The live reporter now retains the latter
as `upstreamSourceReceiptPin` and always binds `sourceReceiptPin` to the actual
source receipt bytes. Two focused binding/idempotence/changed-source rejection
tests and Ruff passed before the first probe landing. Frozen snapshots and source
receipts were unchanged; no inference was repeated.

The first TP14 attempt stopped before any text scoring. The publisher saved
`label2id` but omitted `id2label`; the installed Transformers version replaced
the labels with generated names. The adapter now supplies the exact inverse of
the verified published No/Yes mapping and rejects contradictory maps. Source
model files remain unchanged. The original failure and exit/release audit are
preserved; the first bounded retry uses a fresh output. One targeted config test
and Ruff passed. The serial retry later stopped at the memory floor above.

The stop exposed a partial-save defect: the 150-text timing boundary shifted
later eight-text batches away from exact multiples of 64, so modulo-based saves
ceased until an instrument finished. The live runner now saves after at least
64 additional scores and at completion. Two mocked interruption/completion tests
crossing the timing boundary and Ruff passed. The failed snapshot, model bytes,
progress, 128 durable power scores and completed instruments remain untouched.
No inference was repeated and this repair does not authorize a new TP14 run.

Cross-corpus accuracy/F1 and regression variance/RMSE now retain whole-writer
intervals, including explicit undefined-resample counts. Three targeted grouping,
constant-target and label-restriction checks passed. No completed research row
was changed or rerun by this reporting extension.

The remaining card runners are implemented but their scientific rows are still
pending: attribution (TP17), the incomplete motive comparison (TP14), writer-held-out
concern (TP15), observed alternatives (TP19), negotiation priorities (TP20), smaller-reader
conversion (TP1c), and longitudinal page mixtures (TP22). These implementations
are not completed experiments. The fine-tuned head's separately identified
TP12-L3 counting run is complete; original reference rows were reused unchanged.

TP13 removes 2,885 GoEmotions training comments by known authors present in the
development/test split. The remaining 40,525 training rows retain the published
labels. EmpatheticDialogues' training writers are already disjoint from its
validation/test writers. All 4,613 EmoCause situations join exactly to held-out
EmpatheticDialogues situations and annotation indices agree. Unknown authors and
unreleased GoEmotions labels remain explicit; they are never assigned neutral.

TP19 extends the existing exact prequential handling scorer with optional pinned
features. Its default behavior is unchanged. The research runner keeps the
unwritten own option missing, uses only strictly earlier resolved personal picks,
and holds out writers for the five-option conditional-choice comparison. Its
new BOW control also learns vocabulary only from the training writers. A passed
comparison still requires the existing admission chain before maker display.

TP19 began at 12:27:24 Pacific on November 15 after TP16's verified exit and
release. The prerequisite audit matched the original 1,445-entry public CoAuthor
roster and all 1,445 source-file hashes, plus all 14 files of the development-selected
reader. Motive input is deliberately omitted because TP14 is incomplete. Counted
admission passed with 57.69 GiB commit against 15.31 GiB required. Native identity,
exact shared/local leases and the 170-file frozen snapshot are verified. At
13:00:50, intake had inspected 1,323 of 1,445 roster entries and compiled 1,315.
The 13:00:48 heartbeat was fresh with 56.39 GiB RAM and 54.07 GiB commit headroom;
no aggregate or terminal receipt existed yet. The observed intake rate suggests
roughly three more minutes for intake only; encoding, fitting and aggregation
follow. The eight-hour deadline remains 20:27:22 Pacific, with no whole-card
completion forecast. The delivered 13:35 checkpoint then found a numerical stop
at 13:11:19: the added-feature handling model's population calibration fit hit
the 500-iteration limit. Host-visible native exit and both exact releases were
verified at 13:35:49. This is an engineering failure, not a handling gate result.

The source retains all three completed five-option choice rows (5,719 taken
suggestions, 60 writers): accuracy 0.286238853/0.279594335/0.281342892 and log loss
1.573001190/1.572941569/1.575177790. Their paired accuracy gains are -0.006644518
[-0.014918648, 0.001877755] and 0.001748557 [-0.004468555, 0.008645116], from 2,000
whole-writer resamples. Both gates fail and are preserved without reevaluation.
Baseline handling completed all 8,988 decisions with mean log loss 0.899662598.
The fresh ledger compiled 1,436 of 1,445 sessions, excluding one original failed
reconstruction and eight nonmonotone/empty chronologies. Added-feature handling
and the BOW control remain incomplete; no maker admission follows.

A guarded diagnostic using the saved option features reproduced a 45-by-51
calibration problem hitting 500 steps. Continuing the same objective from its
last iterate converged in 22 steps at the unchanged tolerances (loss
0.388621412 to 0.388620860). The original objective, penalties and data remain
unchanged. TP19 alone opts into at most 2,000 further steps after an iteration-limit
failure; all fits must still report convergence. Ordinary harness defaults stay
unchanged. The diagnostic's native exit and exact releases are verified.

The first bounded continuation uses independently copied,
hash-verified ledger, reader features, completed choice arrays and baseline
handling forecasts. The selected reader's original files are reverified without
loading it. Completed choice fitting, bootstrap gates and baseline handling are
skipped; only unfinished handling and BOW execute within the original 20:27:22
deadline. Nine targeted cases and Ruff passed, including default failure,
unconverged rejection, exact artifact copying, changed/completed source rejection,
deadline preservation, and a mocked runner proving completed work is skipped.
The copy guard also checks resources/deadline and saves its phase every 64 files;
its two focused continuation tests and Ruff pass. The actual-data preflight
completed at 13:53:27, verifying 87,470 copied artifacts including the 87,464-file
ledger and saved result arrays without inference. Its private output is retained
separately from the fresh retry directory. The 14:05 checkpoint verified its
completion and receipt binding before admission.
The original partial source receipt pin is
`5ece2f99ed353b6c4061210aa3757e65a81bec83fed7511d2cc4fd7229ad258d`;
the final card aggregate will bind the continuation chain after terminal exit.

TP19-b began at 14:06:17 Pacific, using the first of two bounded retries and
retaining the original 20:27:22 deadline. Host-visible startup verification at
14:06:42 confirmed native identity and exact shared/local ownership; all 171
frozen files match the manifest. Admission found 49.27 GiB commit against
20.61 GiB required with two foreign leases, which were left unchanged. At
14:06:43, 2,368 of 87,470 artifacts had been copied into the fresh run, and the
heartbeat was fresh with 50.54 GiB RAM and 48.71 GiB commit. No aggregate or
terminal receipt existed yet. Remaining handling and BOW follow artifact reuse;
no whole-card ETA is established. The next checkpoint was 14:35 Pacific.

The delivered 14:35 checkpoint inspected the run at 14:35:22. The restored
baseline and all three choice rows are retained. Added-reader handling completed
8,988 decisions in 245.36 seconds, mean log loss 0.905256916 versus baseline
0.899662598. Its gain is -0.005594318, whole-writer interval
[-0.010540229, -0.001216209], missing the positive-gain bar. The personal-history
handling row had reached 8,750/8,988 decisions (652.95 seconds), with no saved
aggregate for that row yet. BOW and final aggregation follow. The 14:35:22
heartbeat was fresh with 43.26 GiB RAM and 31.44 GiB commit; no complete, failed
or released receipt existed. The next checkpoint is 14:50 Pacific, shortened
to inspect the approaching handling/control boundary. This is not a whole-card
completion estimate or scientific admission.

TP19-b completed at 14:35:35 Pacific. The 14:50 checkpoint verified native exit
and exact releases at 14:51:11, all 171 frozen files, byte-identical reuse of the
three original choice arrays and baseline handling file, and matching decision,
writer and outcome order across all three 8,988-decision handling files.
Personal-history handling log loss is 0.904724583, gain 0.000532333 over the
reader row with interval [-0.005933617, 0.006707773]; its gate also fails.
The writer-held-out BOW choice control gives accuracy 0.237454100 and log loss
1.606641936. All four nested gain bars fail. The reader and personal-history
handling rows used 106/107 bounded optimizer continuations, all converged within
151/167 additional steps at unchanged tolerances. These are engineering counts,
not extra scientific attempts. Motives remain omitted; no pack, maker estimate,
ledger admission or default change follows.

The aggregate [readers-choices-2026-11.json](../engine/validation/readers-choices-2026-11.json)
is landed and source-bound to
`5b155a76203f161d26c1d0457ffa465ed12273e83d743ac055703648f3166a67`;
public pin `b4943d0ffd6dc1dfd9a42278990409d5d71de679a9771b4ee3d223d8d2395ab7`.
The original failed attempt, diagnostic, independent copy preflight and exact
source chain remain preserved. No completed inference or failed gate was rerun.

TP15 started at 14:55:37 Pacific November 15 in the fresh private `tp15-a` job,
with its eight-hour deadline at 22:55:24 Pacific. Host-visible verification at
14:55:55 confirmed native identity and exact shared/local ownership; all 171
frozen files match. The source, two pretrained model inventories and descriptive
comparison inputs were verified before launch. Admission found 28.66 GiB commit
against 21.39 GiB required, with three foreign leases left unchanged.

Its 1,860 concern/distress reports come from 372 writers, five texts each. The
five writer-disjoint folds retain constant, BOW, Potion, frozen MiniLM and fresh
fine-tuned controls. The primary requires correlation at least 0.40 on both
targets, and the stretch requires 0.54 on both. Fine-tuned selection uses only
development writers within each training fold. The separately preplanned
full-data three-epoch head supports descriptive caring-versus-other comparisons
only; it cannot replace held-out forecasts or supply a new CARE admission.
At 14:58:57, the heartbeat was fresh with 46.46 GiB RAM and 29.81 GiB commit.
The receipt was running during initial embedding preparation, without evaluated
rows, a fold phase or terminal/release receipts. The next check is 15:30 Pacific;
five folds and subsequent descriptive scoring remain without a measured
whole-card completion estimate.

The delivered 15:30 checkpoint inspected TP15 at 15:30:31. Fold zero's three
development epochs were saved, and fold one was in epoch three at 1,184/1,340
fitting texts. The heartbeat was fresh with 39.32 GiB RAM and 26.79 GiB commit,
above the unchanged ongoing floors. The receipt remained running with no
evaluated aggregate rows or terminal/release receipts. Three further folds and
the descriptive full-data head remain; observed fold durations differ, so there
is no measured whole-card ETA. The next check is 16:00 Pacific, a conservative
30-minute interval. The healthy guarded scorer was left running.

The delivered 16:00 checkpoint inspected TP15 at 16:00:54. All five held-out
folds and their aggregate rows are saved. Fine-tuned concern correlation is
0.387506600, writer interval [0.344645061, 0.428997077]; distress correlation
is 0.379067750, interval [0.328527526, 0.427519846]. Both the 0.40 primary and
0.54 stretch bars miss. Concern/distress correlations for constant, BOW, Potion
and frozen MiniLM are -0.046841/-0.078587, 0.357176/0.373274,
0.352324/0.374727 and 0.327299/0.328546; all miss both bars. Intervals use
1,000 whole-writer resamples of fixed forecasts. Fine-tuned concern partial
correlation controlling reported distress is 0.312737398. These are reported
responses to articles, not proof of general CARE or maker-level inference.

All five forecast arrays and truth are finite 1,860-by-2 tables; the saved
forecast file pin is
`db8228cf2bd96962e460f636349991178dac043034f82dd64df4fa3741c53ee6`.
The scorer had advanced to the separately preplanned fixed full-data descriptive
head. Its inspected progress was epoch two, 832/1,860 texts, 381.30 cumulative
seconds. The 16:00:53 heartbeat was fresh with 35.08 GiB RAM and 24.71 GiB commit.
No complete, failed or released receipt existed. Descriptive head fitting and
ED/Go group scoring remain, with no measured whole-card completion estimate.
The next checkpoint is 16:30 Pacific. The completed held-out rows are recorded
now; final aggregate landing still awaits terminal state and verified release.

The 16:30 checkpoint found that TP15-a had stopped at 16:23:40 on Windows
`PermissionError` replacing `heartbeat.tmp` with `heartbeat.json`. The last
recorded commit headroom was 20.14 GiB, with no observed memory-floor stop.
The locking cause is unknown; native exit and exact shared/local releases were
verified at 16:31:34. The original source receipt, failure, 171-file snapshot,
all held-out forecasts and completed three-epoch descriptive head remain intact.
The preservation audit binds 269 saved files. Descriptive group forecasts had
only existed in memory; their completed count and corpus boundary are unknown.
They were not recovered, and no complete group result was claimed.

The bounded engineering repair retries only Windows replacement errors 5/32/33
up to five times after the first failure, with exponential waits totaling at
most 1.55 seconds. Each attempt rechecks the unchanged resource floor, STOP and
deadline. Persistent or other errors still stop the job. A TP15-specific
continuation validates the original exit, failure, snapshot, source, packages,
model bytes and saved forecasts, then independently copies the completed head
and forecasts. It preserves all held-out rows without refitting or recomputing
their scientific gates. The same Torch forward calculation is restored from
the saved state, including exact scaling. The original ED/Go intake pins remain
required. Each new 16-text descriptive batch is saved privately before the next
batch; completed group aggregates are also saved as they become available.

The copy-only preflight verified 15 copied artifacts, 103 encoder tensors and
both head tensors against the original saved state without forward inference.
All five forecast arrays retain pin
`db8228cf2bd96962e460f636349991178dac043034f82dd64df4fa3741c53ee6`.
Twelve targeted cases passed, covering bounded heartbeat retries, STOP/floor
checks, deadline preservation, batch interruption/reuse, altered-source rejection
and a mocked full continuation that forbids completed fitting/gate repetition.
Ruff passed after small test-style corrections. The failed attempt and preflight
remain preserved; this repair does not revisit the failed primary result.

TP15-b began at 16:38:46 Pacific, the first bounded retry, with the original
22:55:24 deadline. Admission found 26.66 GiB commit against 19.89 GiB required,
with two foreign leases left unchanged. Native identity and exact shared/local
ownership were verified at 16:39:18; all 172 new snapshot files match. At
16:39:20 the receipt retained all five held-out rows, no terminal/release receipt
existed, and the 16:38:53 heartbeat showed 36.35 GiB RAM and 26.23 GiB commit.
The source receipt pin is
`47378b7c9342722c42a7c662dfd42b3f72d9ec44a4daafb7779a66166a387d40`.
Only the unsaved descriptive scoring restarts; completed training and held-out
inference are not repeated. One engineering retry remains. The next checkpoint
is 17:10 Pacific, with no measured completion ETA for the remaining group scoring.


The delivered 17:10 checkpoint found TP15-b complete at 16:52:08 Pacific.
Host-visible native exit and both exact releases were verified at 17:15:16.
All 172 snapshot files, 15 copied artifacts and the unchanged held-out forecasts
match their pins. Both descriptive groups are durable: 1,554 ED batches contain
24,850 situations (final batch 2); 3,392 Go batches contain 54,263 comments
(final batch 7). Group completion is also recorded in the final receipt.
The aggregate source pin is
`3d41bb3ec3c5b0d19be22b389d81d716cc45a585347e8dfe2c2926bcea55d01d`;
public pin `9bc60823f42456371cc289f3dc55accb1b0fdfbc4a728318eec26e0a26cb4f7f`.

The descriptive ED caring-minus-other concern/distress differences are
0.712148/0.278397 (683 caring and 24,167 other situations); Go differences are
0.258678/0.200076 (1,375 caring and 52,888 other comments). These are predictions
from the separate full-data head, not an independent concern answer key or a
replacement for the failed held-out bars. ED remains research-only. No ledger
row, CARE/maker admission or live default change follows. The original failed
attempt and its unsaved, unrecovered group scoring remain explicitly documented.

Before TP17 launch, the actual prerequisite check caught the publisher's
`__label__` delimiters, which the original runner would not find in the head's
plain label list. The adapter now removes only that exact paired wrapper and
requires equality with the original ED situation label and membership in both
saved heads. All 4,613 items agree: 3,775 validation and 838 test situations,
with no duplicate IDs, training situations or token-alignment exclusions.
The 14 selected-reader files and both fixed TP13 heads match their original
pins. Eight targeted label cases and Ruff passed. No inference or scientific
gate was run during this prelaunch repair; source data and heads are unchanged.
Prerequisite audit: `.local/readers/tp17-prerequisites-20261115.json`.


TP17-a started at 17:19:15 Pacific November 15, with an eight-hour deadline
at 01:19:13 Pacific November 16. Host-visible startup verification at 17:20:10
confirmed the native identity and exact shared/local leases; all 172 snapshot
files match. Admission found 22.12 GiB commit against 19.05 GiB required, with
two foreign leases unchanged. At 17:20:27 it had saved 251/4,613 situations,
no alignment exclusions and no aggregate rows yet. Its heartbeat was fresh with
35.74 GiB RAM/22.51 GiB commit. No terminal/release receipt existed.
The fixed supplied-label deletion comparison has top-three hit-rate bars of
0.481 primary and 0.60 stretch. It concerns marked cause words, not motives.
Next check is 17:50 Pacific; one startup sample establishes no whole-card ETA.


The delivered 17:50 checkpoint found TP17-a complete at 17:39:36 Pacific.
Native exit and exact shared/local release were verified at 17:50:33. All 172
snapshot files match; all 4,613 private observations are finite and unique, with
149 writers and no alignment exclusions. Saved hit indicators reproduce each
aggregate row without forward inference or new bootstrap evaluation. Source pin
`72a731a62cfd86046d0e511a404368838fb77a737baab0b676e05ce5f5273fee`;
public pin `10078d3c730f877bf16960f9243fdcee721f3a465d75eace99d2decb9e1aa98d`.

Combined top-one/three/five hit rates are 0.348580/0.637329/0.746152; top-three
95% writer interval [0.614730, 0.661302], 1,000 whole-writer resamples of fixed
predictions. BOW top-three is 0.553219, deterministic original-order 0.270323,
and per-item chance 0.396084. Validation/test top-three rates are 0.602914/0.792363
with intervals [0.578779, 0.628772]/[0.759101, 0.831934]. Both splits and combined
clear the declared point-estimate 0.481 primary and 0.60 stretch bars. Chance
rates vary by split (0.370061/0.513309), so raw split performance is not a paired
comparison. The endpoint is at least one marked cause word among top k, not
recall of all marked words or the maker's motives. ED remains research-only;
no pack, maker admission, live default or ledger row follows.

TP1c preflight verified all eight Smol135 files at revision
`93efa2f097d58c2a74874c7e644dbc9b0cee75a2`, eight original Smol360 files, all 112
pinned converter files and llama-cpp-python 0.3.36. The three timing texts and
original 1,399-session cohort match their saved bindings. An initial audit
comparison confused file-byte SHA with canonical intake digest; the check was
corrected to the original canonical session and intake identities, without
changing any input or protocol. Audit: `.local/readers/tp1c-prerequisites-20261115.json`.
Its five gates use the smaller model's own float32 reference, with no padding
waiver; candidate accuracy/speed remain distinct from efficacy and serving.
The separately preplanned Smol360 Q4 row is timing only.


TP1c-a started at 17:52:53 Pacific November 15, with its eight-hour deadline
at 01:52:51 Pacific November 16. Admission found 25.05 GiB commit against
19.63 GiB required, with five foreign leases left unchanged. Native identity
and exact shared/local ownership were verified at 17:53:51; all 172 snapshot
files match. At 17:54:06 the Q8 conversion was saved and gate a passed: all
49,152 assigned token IDs and output rows agree, with no padding waiver.
Its GGUF pin is `7ef4905316f5ab3400a1b70929fd54b634b4d59c5e020d174cc80f8935ed29ab`.
The heartbeat was fresh with 37.51 GiB RAM/24.27 GiB commit; no terminal/release
receipt existed. Later numerical gates, own-reference cohort scoring if eligible,
and the separately preplanned Q4 timing remain. No whole-card ETA is measured.
Next checkpoint is 18:25 Pacific. This is a new commissioned small-reader study;
it does not rerun the closed two-day pilots or change their failed gates.


The delivered 18:25 checkpoint found TP1c-a complete at 18:04:10 Pacific.
Native exit and exact shared/local release were verified at 18:25:33. All 172
snapshot files and both converted-weight pins match. Gate a passes; gate b
fails the <=0.05 median absolute word-surprisal error criterion on manuscript
(0.057081) and art (0.053915); excerpt is 0.049763. Spearman correlations are
0.998276/0.998795/0.999460, above 0.98. Gates c-e, the 1,399-session comparison
and Smol135 timing never ran. This scientific failure will not be retried.
Source pin `5816ced9606b73ba0dddd73441858398d56ec7ab456c7e17a96826e7af00513b`;
public pin `32a3fff5cd5da8cef3f8fdfe20e8e56480e2aa120b9087b19fd98b29649a907a`.

The independently planned Smol360 Q4_K_M timing completed: manuscript 3,044 words
in 93.213779 seconds, art 6,038 in 222.398572, excerpt 598 in 10.294524. Long-text
rates are 91.866405/110.499456 seconds per 3,000 words, above 15; the excerpt's
51.644767 extrapolation is not an actual 3,000-word measurement. Loading is
excluded. Quantizer output reported 192/290 fallback tensors because 960 columns
are not divisible by 256. Read-only GGUF inspection confirms F32=65, Q8_0=17,
Q5_0=176, Q6_K=16 and Q4_K=16, so this is a mixed-type requested Q4_K_M output,
not a uniformly 4-bit model. Its exact GGUF pin is
`565282553127d18f962a6699b74b7c33bf01578fcc69c294b16efd989a36b477`.
No Q4 accuracy, serving admission or live default change follows.

TP22's actual prerequisites retain TP12-L3 status `no-policy-qualified`, prior2,
minimum null and the exact selected L3 head binding. The queued guarded job ran
at 18:26:55 and exited at 18:26:59 before reading blog posts or loading a reader.
Its constructed estimator recovered 0.984576/0.505221/0.007849 for planted
1/0.5/0; all constructed controls pass. The receipt remains dependency-blocked,
not completed human science. Native exit and exact releases verified at 18:27:20;
all 172 snapshot files match. Source pin
`a86cce05620d396f9c7944eec6dca64161fa45ef26b0226f1a5c1f93604d409b`;
public pin `8d242df486d7d75f5351d7c559c7ae625d64daa0623b18ec4702f734e3ad8120`.
No substitute page shares or minimum were used. Four foreign leases were left
unchanged; admission had 23.75 GiB commit against 14 required.

TP20 prerequisites verify the original 1,030 CaSiNo dialogues and exact selected
reader's 14 files. The declared first-five-message rule yields 2,052 perspectives
from 1,026 dialogues and excludes eight short perspectives; 10,260 messages are
encoded separately in chronological order. Five dialogue-disjoint folds keep
both perspectives together. Global participant identities are unavailable, so
this is not a writer-held-out result. Only assigned resource-order targets and
ordinary messages enter the analysis; private reasons, allocations, outcomes and
demographic/personality fields are not features. Input pin
`6b9c202e0b78d97551097ae19075fc9bb93e4a902215e21c7b9aba0749909775`.
Audit: `.local/readers/tp20-prerequisites-20261115.json`.


TP20-a began at 18:28:22 Pacific November 15, with a four-hour deadline at
22:28:21 Pacific. Admission at 18:28:07 found 24.46 GiB commit against 14 required,
with four foreign leases unchanged. Host-visible startup at 18:29:31 verified
native identity and exact shared/local ownership; all 172 frozen files match.
At 18:29:41 the heartbeat was fresh with 37.38 GiB RAM/23.88 GiB commit.
No phase, aggregate or terminal/release receipt existed yet, consistent with
initial message encoding before the aggregate is created. No whole-card ETA is
established. Next checkpoint is 19:00 Pacific. The exact-order bar is 0.45;
assigned negotiation priorities cannot establish stable values or endorsement.


The delivered 19:00 checkpoint found TP20-a complete at 18:31:24 Pacific.
Native exit and exact shared/local release were verified at 19:00:43. All 172
snapshot files match; all three forecast arrays and truth are finite 2,052-by-3,
and saved exact-order hits reproduce the aggregate without inference or new
bootstrap evaluation. Forecast pin
`77b538c7c8b36b11c7f6298c9e882f64fc944fa5f9e911eded79d31a7e89f9cb`.
Source pin `ce05ace3ffa14515e475fcee8bec9fa2b4ba88e82394a434483f0961f0c053bc`;
public pin `c53a9b853464e49d604ce70aa036de2880fa8d15569def14bf5fb8619a8e12cd`.

Constant/BOW/reader exact-order accuracies are 0.146199/0.356238/0.310429,
with 95% whole-dialogue intervals [0.130592, 0.164230]/[0.334795, 0.376706]/
[0.291423, 0.330446], using 1,000 resamples of fixed forecasts. Top-priority
accuracies are 0.316277/0.597466/0.604288, a distinct endpoint. All exact-order
rows miss 0.45; chance is 1/6. Global participant identity remains unavailable,
so no writer-disjoint, stable-value or maker admission claim follows.

Before the final lexical controls, the prerequisite check found a stale queued
path: `two-day-prepared/goals.json` does not match the saved baseline's canonical
data pin. The earlier two-day record explicitly places its corrected section
spans in `two-day-prepared-v2`; that file matches the baseline pin exactly,
`dd901f34b399253af97aaa236e15025003222dcb93d8da656c75c49a21a6a1e7`.
Only section spans differ between preparations. The queue now points to this
original corrected input, retaining 40 proposals/38 authors and the exact saved
TF-IDF rows. Neither prepared file was changed; no ranking was run. Audit:
`.local/readers/tp4-controls-prerequisites-20261115.json`.

At 19:03:43 a single host-visible admission check found RAM/commit 39.69/27.89
GiB, six counted foreign leases, capacity eight and 22.40 GiB reserved foreign
headroom. The required small-task headroom is 36.40 GiB, so the final control
was not launched. The local scoring lock and last owned native process were
absent; fresh output remains uncreated. No foreign process or lease changed.
Audit: `.local/readers/admission-20261115-post-tp20.json`. Next admission check
is 19:45 Pacific, a conservative 45-minute interval; recovery time is unknown.

At the delivered 20:30 checkpoint, admission recovered at 20:30:37 Pacific:
RAM/commit 38.97/24.07 GiB against 19.05 GiB required, with five foreign leases
left unchanged. The final TP4-controls job ran from 20:30:59 to 20:31:09 Pacific,
with the queued one-hour bound, two CPU threads and existing resource guards.
Host-visible native exit and exact shared/local release were verified at 20:31:28.
All 172 frozen files match; the saved TF-IDF rows reproduce the original baseline
exactly. All three private ranking tables contain 40 proposals / 38 authors, and
their saved ranks reproduce each aggregate point estimate without new inference.

TF-IDF / BM25 / rarity top-one accuracy is 0.6500 / 0.6750 / 0.7250, with 95%
whole-author intervals [0.4878, 0.8049] / [0.5128, 0.8250] / [0.5853, 0.8537].
Mean reciprocal rank is 0.729398 / 0.741073 / 0.800026, with intervals
[0.6014, 0.8496] / [0.6047, 0.8633] / [0.6922, 0.8967]. These use 2,000
whole-author resamples of fixed rankings. No paired gain test or new efficacy
bar was evaluated; point differences do not establish a reliable improvement.
BM25 retains k1=1.2 and b=0.75, candidate-only IDF and raw query frequency.
Rarity retains the TP7 B5 cosine definition with frequencies from unique pilot
candidate Motivation texts. Both use the original answer-withheld 12,000-character
body and candidate-ID tie breaking. No model or 9B service was loaded.

The aggregate `engine/validation/readers-goal-controls-2026-11.json` is bound to
source receipt `f984653714b401682e8151856a61ea56dda15473460bf523d1406ff42f4d29c2`,
public pin `88bc50c66d32602fe59ef4e8290577b91ca45fd6ceac49434319664064849070`.
Audit: `.local/readers/tp4-controls-completion-20261115.json`. No ledger row,
maker admission, live default change or further push follows.

The bounded readers queue is now closed and its checkpoint was deleted. All 17
reader aggregates retain verified source-receipt bindings and recorded native
exit/exact-release audits. Closeout: `.local/readers/readers-closeout-20261115.json`.
TP14 remains partial and IM1 unrun;
TP16 B/C and TP22 retain the missing qualified counting policy. Optional L4 did
not launch; model-labeller expansion and proposed mappings still require owner
rulings. Failed research gates remain failed, and previously unsaved TP14 power
scores and TP15 descriptive forecasts were not retroactively recovered. All
saved attempts, engineering repairs and source pins remain preserved. Closing
this queue does not claim every proposed study or pack type is complete.

TP22 uses a bounded writer-selection heap, never demographic filename fields.
Its TR1 adaptation reports true variance before unclipped corrected stability,
invalidates an interval containing undefined resamples, and has explicit planted
controls. It cannot run corrected page-share analyses without the exact selected
head's qualified TP12 policy. Subject centroids use Potion's documented 128-token
representation; sentence mixtures use the whole text subject to the fixed policy.
The topic adjustment uses other writers' earlier posts only. The later subject
composition is a retrospective conditioning variable, not a prospective forecast
of which subject a writer will choose.

The empathy source's 372 released response IDs represent the retained participants
after the original 403-participant sample excluded 31 participants and 155 messages.
This is documented in the [original paper](https://aclanthology.org/D18-1507.pdf).
CaSiNo's [priority-prediction paper](https://aclanthology.org/2022.findings-naacl.50.pdf)
reports the quoted five-utterance random/BOW/model figures in Table 1 and the expert
comparison in section 5.3. Its partial-dialogue and additional-training-data protocol
differs from this packet's opponent-only five-message input. Those are references,
not a replicated result.

The Smol135 source is downloaded with Apache 2.0, its revision and every file
hashed. TP1c reuses the pinned converter, requires the smaller model's own float32
references, and preserves the existing Qwen route's model requirement. Its Q4
360M row is timing only. The completed conversion, gate-b failure and timing
limits are recorded above; later gates and cohort accuracy remain unrun.

Six new targeted tests passed for strict historical cutoffs, missing own options,
constructed conditional choice, planted stability, dated post parsing and
unchanged zero-feature prequential forecasts. Five existing prequential and
weight-only checks also passed after the extensions. Ruff passed. One pytest
cache write was unavailable in the sandbox; test results were unaffected and
later targeted runs disabled that optional cache. No inference gate was repeated.

- A fixture read initially used the Windows default text encoding; explicit UTF-8
  restored hash parity. A frontend text read had the same encoding fault; it was
  repaired before the passing native panel check.
- The isolated environment's ensurepip setup failed; the existing pip installed
  into that environment without changing the original environment.
- MiniLM's missing Pillow import is the first TP10 execution repair. The failed
  attempt, snapshot, predictions and pins remain in private storage.
- A startup audit initially compared the lease to the owner file including its
  extra lease-path field. Native identity matched; the audit comparison was fixed
  to the actual protocol fields. The job then reached its dependency failure and
  its final native exit and releases were verified. No foreign lease was changed.
- SetFit conversion first rejected an unlisted loss-state class. Inspection
  showed `_loss.CyHalfBinomialLoss`; it was added only as inert state. Conversion
  then passed without importing or executing that pickled class.
