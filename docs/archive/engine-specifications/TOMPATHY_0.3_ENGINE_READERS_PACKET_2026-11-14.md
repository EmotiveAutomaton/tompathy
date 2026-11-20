# ToMpathy 0.3 engine: the readers packet

14 November 2026, late evening. For the agent on `codex/0.3-engine`. It continues `TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-12.md`; nothing there is withdrawn unless section 1 or section 8 says so. Working record: `docs/ENGINE_READERS_2026-11-17.md`. Scoreboard rows go in `docs/ENGINE_SCOREBOARD.md` as before.

This is a spec sheet. It carries no questions for the owner. Choices are made here and listed in section 1. It is back end only: section 4 is reserved for the owner's own description of the bottom panel, and nothing in this packet builds a display.

## 0. Read first

**Sources.** The branch at `d49be5f` (unchanged at 23:17 on 14 November): `docs/ENGINE_SCOREBOARD.md`, `docs/ENGINE_TWO_DAY_2026-11-14.md`, `packet/bottom_box.py`, `packet/drives.py`, `packet/preferences.py`, `features/augment.py`, `features/deterministic.py`, `ledger/schema.py`, `adapters/coauthor.py`, `eval/harness.py`, `eval/back_half/attention.py`, `src/core/owner-probes.ts`, the B13 item file. The Round 16, 17 and 18 theory handoffs and the owner's three turns behind them; the first lines of Round 19 (14 November, 16:35). Sounding Line at `c03fc1620`, Ghost at `2962c7098`. Four capped lookups by a cheaper model and eight direct ones; a fact that rests on a lookup says who read it. One public corpus was downloaded and analysed by the analyst before writing (section 2).

**Where the engine stands** (scoreboard at `d49be5f`).

| Reading | State |
|---|---|
| Attention (TP2) | 0.5677 against a baseline of 0.5512: a gain of 0.0165 [0.0081, 0.0241] against a bar of 0.02. Missed. Her own history added 0.0010. SmolLM2-360M scored 0.5668 |
| AI involvement (TP5) | 0.8055 against 0.6002. Cleared, for one 2021 suggestion model |
| Edit reasons (TP3) | Feature classifier 0.484 macro-F1 on 1,692 edits. The 9B reader stopped at 472 of 1,000 at 0.258 against 0.479 for features on the same items |
| Goals (TP4) | Word matching names the goal for 65% of 40. The 9B goal reader never loaded (memory) |
| Speed (TP1b) | The weight-only route passes all five gates and takes 55 to 62 s per 3,000 words against a target of 15 |
| The bottom box (TS1) | `bottom-box-0` exists and is empty by design |
| Channels, needs, rules, Stress | Nothing reads them. `trigger` and `appraisal` do not occur in `engine/tompathy_engine` |

**What the owner asked for.** 14 November, to this thread: "testing out new ideas in the engine and trying to find ways of making real progress with results", "work out potential algorithms or engine refinements", and "leave some space for the bottom panel of Tompathy to be verbally described... You're just focusing on the back end." To the theory thread the same afternoon: "Somehow our engine is not growing as a result of our knowledge", "we're going to have to get much, much more clever very, very quickly. Try to find new ways to uncover things like triggers or even stress", "Maybe we just do blind inference and try to fill in a row", "So far, I haven't extracted the person from this anywhere."

**Standing rules.** One scoring process at a time, at most two numerical threads, below-normal priority. The 9B reader loads only past the 20 GiB gate. No GPU, no paid or remote model calls. Defaults do not change: every new path is a flag, and nothing here is displayed in the default build. Receipts carry exact reader, code and data pins. A failed gate is a result and stays disabled. The 14 October guard stands whole: only choices and corrections move maker estimates, and final text establishes neither.

**Names.** Needs: Knowledge, Nest, Belonging, visibly respectable, visibly compassionate, the body. Channels: SEEKING, RAGE, FEAR, LUST, CARE, PANIC/GRIEF, PLAY, DISGUST, SHAME. The marketplace of ideas holds tiles. On 14 November the owner sent the word "Freedom" back to the name pile; this packet writes "the stock" and gives it an id with no display name.

## 1. Choices made here

Each is made here. None is a question.

1. **Readers are trained, small and local.** No reading in this packet comes from prompting the 9B. A reader is a small encoder with linear heads, trained on a public corpus that carries an answer key, and run on CPU. One exception is a measurement and not a reading: TP10 prompts the 9B once on 300 reports to record how far prompting falls short, as Round 18 asked.
2. **Everything lands as `benchmarked`, behind a flag.** Round 18's first question (a page tier held to a human reader's score) is not ruled. This packet builds the readers and their scores and admits nothing. If he rules yes, admission is one flag. If no, the benchmarks stand as research.
3. **No model labels training text.** Round 18's second question (a strong model as an offline labeller) is not ruled, so no reader here is distilled from another model's labels. Two published motive coders are run as instruments on public text (TP14); training a student on their output waits.
4. **His own dictated messages are not touched** (Round 18's third question).
5. **No data request is sent.** Section 9 lists what sits behind a request form.
6. **This agent downloads public data and weights** into `.local/`, never committed, each with source, licence as read at download, row counts and SHA-256: Crowd-enVENT; GoEmotions; EmpatheticDialogues; the Real World Worry Dataset; the empathic-reactions essays; EmoCause; CaSiNo; the Blog Authorship Corpus; and weights for `all-MiniLM-L6-v2`, `potion-base-8M`, `SmolLM2-135M`, the three `theharmonylab/implicit-motives-*-roberta-large` models and `automatedMotiveCoder/setfit`.
7. **Licence decides what could ever ship.** Each pack records `research_only`. It is true when any training corpus or weight is non-commercial or carries no stated licence. Today that covers EmpatheticDialogues (CC BY-NC 4.0, read by the analyst in the repository's licence file) and the Blog Authorship Corpus (non-commercial research use, read on its dataset card). Crowd-enVENT is CC BY 4.0 (read by the analyst in the archive's `LICENSE.txt`).
8. **The engine repository is the fast lane for reader benchmarks.** Sounding Line recorded 89.74% of its slot-hours idle on 14 November with owner review as the named bottleneck. Reader benchmarks on public text run here. Sounding Line keeps the science on its own tables and receives one small table from this packet (IM1, in TP14).
9. **Packages.** A new optional extra `readers` with `scikit-learn`, `sentence-transformers` and `model2vec`, pinned by this agent at install and recorded. `torch` and `transformers` come from the existing `preview` extra.
10. **Stopped for good:** the 9B edit-reason reader (TP3's Q8 route) and the 9B goal re-rank (TP4). Both were behind plain features or never loaded. The feature classifier and the word-matching row stay.
11. **Bars are set against people and against the simplest model.** Three of Round 18's bars are replaced in section 2 because the corpus shows they sit on the wrong side of a floor.

## 2. What the corpus says before anything is built (the analyst's pre-flight)

The analyst downloaded Crowd-enVENT (the public archive, SHA-256 `61c22527795669a0556df8d7441d3a7bf13ef8b2266b0433881645e92bf885e6` as served on 14 November) and ran ten short scripts. Scripts and outputs are in `PREFLIGHT_2026-11-14.zip`. These are design numbers from one analyst pass, with no replay. The archive holds 6,600 reports by 2,379 writers, the five readers' judgements on 1,200 of them, and the corpus authors' own model predictions for those 1,200.

**2.1 The ladder a reader has to climb** (13 labels, the 1,200 reports with readers; the writer's own label is the key).

| Reader | Accuracy | Macro-F1 |
|---|---|---|
| Bag of words, logistic (the analyst's run, trained on the other 5,400) | 0.414 | 0.393 |
| One human reader | 0.504 | 0.492 |
| Majority of five readers | 0.581 | 0.565 |
| The authors' RoBERTa-large, mean of five released runs | 0.605 | 0.594 |

- Writers who also appear in training are read no better than new writers (bag of words 0.411 against 0.418; RoBERTa 0.586 against 0.605). The authors' split leaks nothing through the writer.
- Where four or five of the five readers agree (49.7% of reports) their choice matches the writer 74.2% of the time. Where all five agree (21.8%) it is 80.2%. An absolute bar of 0.85 cannot be met on this key by anyone.
- The bag-of-words reader is right 0.783 of the time on its most confident tenth and 0.577 on its most confident half. Confidence sorts well even in the weakest reader.

**2.2 Three bars in the Round 18 handoff sit on the wrong side of a floor.**

| Round 18's bar | What the corpus shows | Bar used here |
|---|---|---|
| Features: one reader's 1.57 on a 5-point scale | Guessing the training mean for every report scores 1.499. One reader scores 1.573, worse than the constant. Five readers averaged score 1.262. A bag-of-words ridge scores 1.374. Knowing the writer's label and using that label's mean row scores 1.336 | Beat 1.499; aim at 1.34 |
| Nothing-here: 0.70 on the corpus's no-emotion reports | One reader finds 0.208 of them, five readers 0.200, the authors' RoBERTa-large 0.490 | 0.40 on these reports; 0.90 on text that is plainly neutral (TP10) |
| The 21 rated features as the trigger instrument | See 2.3 | A reader of what the event was about (TP11) |

- Only some of the 21 features can be read off a report at all. Five readers' average against the writer: pleasantness 0.82, unpleasantness 0.78, own responsibility 0.71, goal support 0.64, external norms 0.64, others' responsibility 0.63, own standards 0.61, suddenness 0.58. At the bottom: acceptance of consequences 0.15, predictability of consequences 0.35, urgency 0.38, attention 0.41. The authors' model tracks the same order (0.25 to 0.76).

**2.3 The writer's 21 ratings barely tell near-twin feelings apart. Her words do.** In the space of the 21 ratings the labels fall into pairs with nearly the same row: pride and joy (0.99), guilt and shame (0.95), trust and joy (0.94), fear and sadness (0.92), anger and disgust (0.91). Telling the two apart inside each pair, with writers held out (area under the curve; 0.5 is chance):

| Pair | From her own 21 ratings | From the words of her report (bag of words) | Words that lean each way |
|---|---|---|---|
| pride, joy | 0.613 | 0.757 | award, competition, accomplished, managed / christmas, trip, puppy, loved |
| guilt, shame | 0.627 | 0.700 | dog, sick, accidentally, friends, care / afford, exam, fell, actions |
| fear, sadness | 0.728 | 0.863 | nearly, flight, emergency, waiting / died, left, grandpa, diagnosed |
| anger, disgust | 0.749 | 0.787 | telling, ignored, broke, mistake / smell, food, vomited, maggots |
| trust, joy | 0.798 | 0.891 | friend, boss, doctor, listened, supported / born, won, birthday, proposed |

The analyst wrote down which features the theory's channel distinctions should move before computing any pair (`twin_predictions_written_before_numbers.json`): 23 of 30 signs came out as written, and most gaps are under 0.4 of a standard deviation. The corpus paper reports the same thing from the other side: the label from the writer's own 21 ratings alone scores 0.32 to 0.35 macro-F1 against 0.59 from text ([Troiano, Oberländer and Klinger 2023](https://aclanthology.org/2023.cl-1.1), read by a helper).

**What this changes (the analyst's reading, unchecked by the theory thread).** Round 18's design claim is that one trigger reader reaches most of the theory, and its first instrument is the 21 rated features. The corpus says the channel a report belongs to is carried mostly by what the event was about: standing won against a pleasure enjoyed, harm done to someone against being exposed, a threat ahead against a loss already taken, a person's act against a contaminant. Emotion research calls these core relational themes (Lazarus; the comparison with rated components is Smith and Lazarus 1993, from memory and not opened; [summary](https://en.wikipedia.org/wiki/Core_relational_theme), title seen only). In the theory's own terms they are which set point moved, which way, by whose doing, and whether it has happened yet. So the engine's main instrument is a label head plus a reader of those four things, and the 21 features are a second layer with eight readable members.

**2.4 A page's mix should be counted through the reader's error table.** Bags of reports were drawn from one half of the 1,200 with the error table measured on the other half (20 splits). For peaked mixes, the case a page resembles, at 60 reports per bag:

| Estimate of the bag's mix | Error per label | Largest label named right |
|---|---|---|
| One human reader's raw count | 0.061 | 0.71 |
| The same count corrected through the reader's error table | 0.040 | 0.79 |
| RoBERTa-large raw count | 0.052 | 0.77 |
| RoBERTa-large corrected | 0.033 | 0.83 |

- Raw counts stop improving with length (0.059 for the human count at 1,000 reports). Corrected counts keep improving (0.027).
- For flat mixes the correction hurts below about 200 reports and helps above. TP12 settles the rule with a prior.
- When most sentences are nothing-here the raw count is useless. In the Ghost pre-flight with the model's table and 80% neutral sentences, the largest counted label is the maker's true largest 16 to 18% of the time at any number of pages, and the corrected count reaches 86% by 64 pages.
- The technique is standard under the name quantification, or adjusted counting (Forman; Saerens and colleagues; from memory, not looked up).

**2.5 A reader can place a label it never saw.** Leaving one label out of training and predicting the 21 features for its reports with a bag-of-words ridge, the predicted mean row correlates with the writers' true row at a median of 0.93 across the 13 labels, and the left-out label's own row is the nearest of the 13 for nine of them. The size of the predicted row is only 0.13 to 0.32 of the true size, and trust fails (0.10). The shape of a row transfers and its size does not. This is the check behind TP13.

## 3. The wiring (TS2): `bottom-box-1` and reader packs

Until a trained reader can be loaded, verified and aggregated by one code path, every benchmark below is a file. TS2 is that path. Build it first.

**3.1 Fixed ids.** Ids never change; display names live in one map (`packet/names.py`).

| Kind | Ids | Display names today |
|---|---|---|
| Needs | `N1` to `N6` | Knowledge, Nest, Belonging, visibly respectable, visibly compassionate, the body |
| Channels | `C1` to `C9` | SEEKING, RAGE, FEAR, LUST, CARE, PANIC/GRIEF, PLAY, DISGUST, SHAME |
| Stress | `S1` | Stress |
| The stock | `K1` | none (the old name was withdrawn on 14 November) |
| Tiles | a list under `marketplace` | each tile a record, replacing the bare `hub` string |

`tending`, `seen_as_competent`, `seen_as_kind` and `hub` leave the schema. The outlook is not carried.

**3.2 Two tiers.** `on_page` holds readings of the final text, each a claim about a passage. `about_maker` holds nothing unless a reading comes from choices, corrections or many pages, and it stays behind the existing admission chain. A reading never moves between tiers.

**3.3 A reading.**

```
{ "id": "C3", "tier": "on_page",
  "share": {"value": 0.18, "interval": [0.09, 0.29], "of": "sentences read as carrying a feeling", "method": "corrected"},
  "events": [ {"span": [1204, 1297], "label": "fear", "confidence": 0.71,
               "stake": {"need": "N6", "direction": "threatened", "by": "circumstance", "when": "ahead"},
               "who": "writer | other | unclear", "words": [[1231, 1240]]} ],
  "series": [ {"from": 0, "to": 2400, "value": 0.05}, ... ],
  "pack": "rp-envent-1@<sha256>",
  "key": {"corpus": "Crowd-enVENT", "labelled_by": "the writer", "n": 1200},
  "score": {"metric": "macro_f1", "value": null, "interval": null},
  "people": {"one_reader": 0.492, "five_readers": 0.565},
  "floor": {"bag_of_words": 0.393},
  "nothing_here": {"neutral_text_silent": null, "no_emotion_reports_found": null},
  "mapping": {"status": "proposed | ruled", "source": "..."},
  "status": "benchmarked" }
```

`status` gains the value `benchmarked`: an answer key exists and a score against it is recorded. It sits below `admitted` and displays nowhere by default. `events[].stake` and every `mapping` carry `proposed` until the owner rules on the label map.

**3.4 A reader pack** is a directory under `.local/packs/<name>/`:

- `pack.json`: name and version; task; label list; encoder id and SHA-256; head file and SHA-256; token cap; the abstention threshold and the share of text it leaves unread; the error table (rows the key's label, columns the reader's) measured on held-out data, with its counts; scores with intervals beside the floor and the human rows; nothing-here results; each training corpus with licence as read; `research_only`; the code pin.
- `head.npz`, and `table.json`.

`packs/registry.py` loads a pack only if every hash matches. `packs/run.py` takes sentences and returns events. With no pack present the box is empty, as now.

**3.5 The aggregation rule.** A share on a page is never a raw count. It is the count passed through the pack's error table (non-negative least squares), with a prior fixed by TP12, an interval from resampling sentences, and a minimum number of read sentences below which no share is given. Fixture, computed: with the table `[[0.8,0.1,0.1],[0.2,0.7,0.1],[0.3,0.2,0.5]]` and a true mix of 0.6, 0.3, 0.1 the raw shares are 0.57, 0.29, 0.14 and the corrected shares are 0.6, 0.3, 0.1.

**3.6 Tests.** The fixture above; a hash mismatch refuses to load; a pack with `research_only` true is refused by the build that packages a release; every existing fixture still validates after the version bump; `bottom-box-0` payloads are read and upgraded with empty tiers. The contract's own rule applies: tests and a version bump.

## 4. The bottom panel (reserved for the owner's spoken handover)

Nothing is specified here. The owner will describe the panel himself and the front end is built from that description. This packet builds no component, no layout and no copy.

What the back end will have on offer when he does, if the cards below land:

| For | Data | From |
|---|---|---|
| Each need | Events on the page that moved it, with direction, passage and the words that carried it; a series along the page; the instrument and its score beside people's | TP10, TP11, TP14, TP17 |
| Each channel | A corrected share with its interval; events with passages | TP10, TP12, TP13 |
| Stress | A reading keyed to writers' own worry ratings; sentences that state a plan | TP16 |
| The stock | Nothing | |
| Tiles | The repeats and the outline the engine already reads | existing |
| About the maker | What she takes when offered alternatives, if TP19 clears; otherwise empty, with the number of pages or choices still needed (Ghost V30, family P) | TP19 |
| Every reading | Whose answer it was scored against, how one person scores on the same items, and what it cannot say | TS2 |

## 5. Reader cards

Common rules. Splits hold out writers where the corpus identifies them. Intervals resample writers, or texts where writers are unknown. Every card reports the constant, the bag-of-words row and the human row beside its own. Every card writes a pack, or says why not. If TP10 writes no pack, the cards that name `rp-envent-1` run on TP10's best head and mark their rows unpacked.

### TP10. The channel reader, first pack (Round 18's R1)

- **Data.** Crowd-enVENT, [archive](https://www.romanklinger.de/data-sets/crowd-enVent2023.zip), CC BY 4.0. Texts, writers and the writer's label all come from `crowd-enVent_generation.tsv`: text column `hidden_emo_text` (the emotion word is hidden), label column `emotion`, writer `prolific_id`. `crowd-enVent_validation.tsv` holds no text; there `emotion` is a reader's label and `original_emotion` repeats the writer's. Join the two on `text_id`. Test: the 1,200 reports whose `text_id` appears in the validation file. Of the other 5,400, hold out for validation the reports of a tenth of their writers, chosen by SHA-256 of `prolific_id`.
- **Harness check, first.** Recompute from the archive's own files the four rows of 2.1 that need no training: one reader 0.504 and 0.492; majority of five 0.581 and 0.565; the authors' released predictions 0.605 and 0.594 (five files). The harness is right when it reproduces the reader and model numbers within 0.002 and the majority numbers within 0.01 (a tie among the five goes to the label met first in file order).
- **Ladder.** L0 the constant. L1 bag of words (expect about 0.41 and 0.39). L2 frozen embeddings with a linear head, twice: a static model ([potion-base-8M](https://huggingface.co/minishlab/potion-base-8M), MIT, 7.6M parameters; its card puts it level with MiniLM on classification) and [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Apache 2.0, 22.7M). L3 the better encoder fine-tuned, three seeds. L4 the 9B by prompt on 300 test reports, once, only if the memory gate holds; it is the measurement Round 18 asked for and it gates nothing.
- **Report.** Accuracy, macro-F1, recall per label, the error table, calibration, and accuracy on the most confident 22% and 50% (the shares at which five and four-of-five readers agree).
- **Bars.** B1: macro-F1 at or above 0.49 with the lower end of its interval above the bag-of-words row. B2, a stretch: 0.565. B3, nothing-here: at least 0.40 of the corpus's no-emotion reports found; at most 0.05 of emotion reports called no-emotion (one reader 0.023, the authors' model 0.029); at least 36 of the 40 theme-free B13 items silent; at least 0.90 silent among up to 2,000 before-revision sentences from IteraTeR's arXiv and Wikipedia documents (all of them if TP9's set holds fewer). B4, confidence: 0.70 on the most confident half, 0.78 on the most confident 22%.
- **Features.** A second head for all 21 rated features. Bar: on the eight readable features of 2.2, pooled error below the constant's and below one reader's. The other thirteen are kept for TP13 and are never displayed.
- **Speed.** Sentences per second on two threads for L2 and L3. The pack that would run live reads 150 sentences in under one second.
- **Outcome.** B1 and B3 clear: `rp-envent-1` is written and wired under the flag. B1 misses: the ladder is the result, and the next step waits on the owner's ruling about model labellers.

### TP11. What the event was about (the stake reader)

- **Why.** Section 2.3. A reader that cannot tell pride from joy cannot put an event on the right need.
- **The twins test.** For the five pairs of 2.3, with writers held out by `prolific_id`: the area under the curve from the writer's own 21 ratings (expect 0.613, 0.627, 0.728, 0.749, 0.798), from bag of words (0.757, 0.700, 0.863, 0.787, 0.891), and from TP10's encoders with a pair head. Bar: above the ratings row on all five pairs and within 0.02 of bag of words or better on all five.
- **Stake columns.** Four columns per report, derived from its label by the table below, trained as four more heads on the TP10 encoder: the need that moved, the direction, by whose doing, and whether it has happened. The table is a proposal: the first seven rows restate the theory thread's S1 mapping, which awaits the owner's ruling, and the rest are the analyst's. Every output carries `mapping.status: proposed`.

| Label | Channel | Need | Direction | By | When |
|---|---|---|---|---|---|
| pride | (none named) | N4 | up | self | already |
| shame | C9 | N4 | down | self | already |
| guilt | C5's alarm | N5 | down | self | already |
| trust | (none named) | N3 | up | other | already |
| surprise | C1 | N1 | (either) | any | already |
| relief | S1 resolving | any | restored | any | already |
| no-emotion | nothing-here | | | | |
| fear | C3 | any | threatened | any | ahead |
| sadness | C6 | any | down | any | already |
| anger | C2 | any | down | other | already |
| disgust | C8 | N6 | threatened | any | already |
| joy | (none named) | any | up | any | already |
| boredom | C1, low | N1 | unfed | circumstance | now |

- **Whether the columns are a basis.** For each label whose every column value also occurs in another label (under this table: pride, shame, sadness, anger and joy), train the four heads without it and read its reports. Score: the share of its reports whose predicted values match the table's row on every scored column, against the share expected from the heads' marginals. A cell that reads any or either is not scored, so pride and shame are scored on four columns and sadness, anger and joy on two or three. Report beside it the left-out result for the 21 features (2.5). If the four columns place unseen labels better than chance and no worse than the 21 features, the theory's parts work as a description language for feelings a reader has not met. If not, they are labels and no more.
- **Route.** The twins table and the left-out table go to the theory return under "what a trigger is made of".

### TP12. The page's mix by corrected counting

- **Protocol.** As 2.4: 20 random halvings of the 1,200; the error table from one half, bags from the other; bag sizes 20, 60 and 200; flat mixes (Dirichlet 1) and peaked mixes (Dirichlet 0.15); nothing-here shares of 0, 0.5 and 0.8, drawn from the corpus's own no-emotion reports so that the error table fits. One further row draws the neutral share from TP10's two neutral sets with the table unchanged: it measures what a mis-stated nothing-here row costs, the case Ghost's family P maps.
- **Estimators.** Raw count; corrected; corrected with a Dirichlet prior at 1, 2 and 4; the expectation-maximisation estimate on the head's probabilities.
- **Rows.** One reader's count and corrected count (from the archive), the authors' model (from the archive), each TP10 pack.
- **Check.** Reproduce the analyst's table (`pf_c2.txt`) for the human and RoBERTa rows within 0.005 before reading the pack's rows. In that file the rows named "with shrinkage" used a flat prior; the priors here are new.
- **Bar.** On peaked bags of 60 with no neutral sentences: the pack's best estimator errs at most 0.040 per label and names the largest label at least 0.79 of the time, which is what one human reader's corrected count reaches. Stretch: the authors' model's corrected row, 0.033 and 0.83. With 0.8 neutral the corrected estimate should beat the raw count on both scores; the pre-flight says it will, so that row is a check and not a finding.
- **Decides.** The prior and the minimum sentence count written into TS2's rule.

### TP13. All nine channels: the rows nobody rated

- **Why.** The owner: "we weren't even able to collect triggers for, or attempt to collect triggers for any but three of the channels", and "Maybe we just do blind inference and try to fill in a row." Crowd-enVENT has no label for SEEKING as interest, PLAY, LUST, CARE or loneliness.
- **Data.** [EmpatheticDialogues](https://arxiv.org/abs/1811.00207): 24,850 conversations, each opened by a one-to-three-sentence situation written by a person who was handed one of 32 labels, among them lonely, caring, jealous, grateful, anxious, anticipating, prepared, confident (read by a helper; research-only). [GoEmotions](https://arxiv.org/abs/2005.00547): 58,009 Reddit comments with readers' labels from 27 plus neutral, among them curiosity, desire, amusement, caring, grief; 26% neutral; BERT 0.46 macro-F1 (read by a helper; licence to be read at download).
- **Part A, coverage.** Train label heads on each corpus on the TP10 encoder. Report against the published rows (EmpatheticDialogues situation to label: 0.43 to 0.48 accuracy; GoEmotions 0.46). Then cross the corpora on the labels they share with Crowd-enVENT: train on readers' labels, test on the writer's, and the reverse. The drop is the price of using readers' labels where no writer's label exists.
- **Part B, the rows.** Apply TP10's 21-feature head to every EmpatheticDialogues situation and GoEmotions comment. Group by label. First the check: for labels shared with Crowd-enVENT, correlate each predicted mean row with the writers' true row, and count how often the true row of the same label is the nearest. Go on only if the median correlation is at least 0.80 and the true row of the same label is the nearest for at least half of the shared labels. Then report predicted rows for caring, lonely, jealous, grateful, curiosity, desire and amusement, each with the eight readable features marked and with the statement from 2.5 that shape transfers and size does not.
- **Channel map** (the analyst's proposal, `proposed` on every output): curiosity to C1; anger, annoyance, furious to C2; fear, nervousness, afraid, terrified, anxious to C3; desire to C4; caring to C5; grief, sadness, lonely, devastated to C6; amusement to C7; disgust to C8; embarrassment, ashamed to C9.
- **Route.** Part B's table is the first trigger row for five channels and goes to the theory return, marked as read by a model from other people's text.

### TP14. Needs on the page: two motive coders

- **Why.** Round 18: "The need has to come from the label (pride, trust, shame) or from what the passage is about. The second route has no answer key yet." Psychology has scored three motives from running text for decades, and two labs have now published machine coders trained on experts' codes.
- **Instruments.** `theharmonylab/implicit-motives-achievement-roberta-large`, `-affiliation-`, `-power-` ([Nilsson and colleagues 2025](https://doi.org/10.1037/pspp0000544): 85,028 expert-coded sentences from picture stories; agreement with coders at the level of a person 0.85, 0.89 and 0.87; read by a helper from the journal record; the three repositories confirmed by the analyst on the [organisation page](https://huggingface.co/theharmonylab); licence to be read at download). `automatedMotiveCoder/setfit` ([Brede and colleagues 2025](https://aclanthology.org/2025.nlpsi-1.3.pdf): German picture stories, 0.74, 0.79 and 0.74 per person, nearly the same on machine-translated English; read by a helper).
- **No public expert-coded set is in hand,** so validity here is by four checks.
  1. *Two instruments agree.* On 2,000 Crowd-enVENT reports and 2,000 EmpatheticDialogues situations: correlation between the two coders per motive, per text. Bar 0.50 on each motive.
  2. *Nothing-here.* Silent on at least 36 of the 40 theme-free B13 items and on 0.90 of the arXiv sentences.
  3. *Known groups, the twins.* Predictions written here before any run (the analyst's): achievement and power higher in pride than joy; affiliation higher in guilt than shame; affiliation higher in sadness than fear; power higher in anger than disgust; affiliation higher in trust than joy. Score: the gain in area under the curve when the three motive scores join the writer's 21 ratings, writers held out. Bar: a gain of 0.03 with the predicted sign on at least three of the five pairs.
  4. *The constructed themes.* On the 200 B13 items: power on `status`, affiliation on `care` and on `loss or separation`. Reported, no bar.
- **Mapping** (the analyst's, `proposed`): affiliation to N3; power to N4; achievement is shown under its own name and mapped to nothing.
- **What it reads.** What a page shows. Round 18's fifth surprise stands beside it: across studies the motives in a person's stories match the wants she states at about 0.13. The pack's description says so.
- **Speed.** Time one motive model on 150 sentences at two threads. Over 5 s: the pack is marked offline-only.
- **IM1, a table for Sounding Line.** `text_id`, three motive scores from each instrument, for all 6,600 reports, with pins. Copy to Sounding Line's `docs/exchange/` by the usual local procedure. It feeds IN13.

### TP15. CARE (Round 18's R2)

- **Data.** [Buechel and colleagues 2018](https://aclanthology.org/D18-1507): 1,860 short reactions to news stories by 403 people, each with the writer's own empathic concern and personal distress on a seven-point scale (read by a helper; repository `wwbp/empathic_reactions`; licence to be read).
- **Rows.** The constant; bag-of-words ridge; frozen embeddings with ridge; the fine-tuned encoder. Writers held out.
- **Bar.** Correlation of 0.40 on concern and on distress (the paper's own best model: 0.404 and 0.444). Stretch 0.54 (the best shared-task systems, [2022 overview](https://aclanthology.org/2022.wassa-1.20), read by a helper). No human reader's score exists for this set.
- **The reading that matters.** Concern with distress held fixed: the partial correlation of the concern head with the writer's concern given her distress. CARE is concern for the other; distress is the reader's own alarm.
- **Second check.** The head's mean on EmpatheticDialogues `caring` situations and GoEmotions `caring` comments against all other labels.

### TP16. Stress on the page

- **Why.** The owner: "is there any other thing we can measure as stress?" Round 18 looked for a text corpus carrying the writer's own stress rating and found none. The nearest thing found in this pass: the [Real World Worry Dataset](https://arxiv.org/abs/2004.04225). 2,500 people in the United Kingdom in April 2020 each wrote a long text (500 characters or more) and a short one about how they felt, and rated their own worry and eight feelings (anger, anxiety, desire, disgust, fear, happiness, relaxation, sadness) from 1 to 9 (read by a helper; data in the authors' repository `ben-aaron188/covid19worry`; licence to be read).
- **Part A, the worry reading.** Predict the writer's worry from her long text, people held out. Rows: constant; TF-IDF ridge (the paper: 0.16 of variance, error 1.26); frozen embeddings; fine-tuned. Bar: 0.16 of variance. Stretch 0.25.
- **Part B, the first test of TP10 on long free text.** Apply `rp-envent-1` to each long text sentence by sentence and aggregate by TS2's rule. Correlate the corrected share of fear with the writer's fear and anxiety ratings, anger with anger, sadness with sadness, disgust with disgust. Bar: each of the four above 0.15, and each label's share correlating more with its own rating than with the other three. This is a writer-keyed check that a reader trained on 13-word event reports says something about a paragraph.
- **Part C, plans** (exploratory; for the theory return). "A plan is resolved energy." Mark sentences that state the writer's own plan with a short fixed rule list (first person with will, going to, plan to, decided to, intend to, have arranged). Report the partial correlation between the share of plan sentences and her worry, holding fixed length and the corrected share of negative labels. A negative value is what the sentence predicts. It is a correlation in one population about one event: calm people may plan more. Masicampo and Baumeister (2011) found in experiments that making a plan removed the intrusions an unfinished goal causes (from memory, not opened).
- **Limits.** One topic, one month, one country; worry sits high (mean 6.55, spread 1.76).

### TP17. Which words carried it

- **Data.** [EmoCause](https://arxiv.org/abs/2109.08828): people marked the words that caused the feeling in about 4,600 EmpatheticDialogues situations. Naming a marked word in the top one, three or five: people 41.3, 81.1 and 95.0; chance 10.7, 30.6, 48.5; the paper's best method 17.3, 48.1, 68.4 (read by a helper).
- **Method.** For a static-embedding head with plain mean pooling the contribution of each word to the predicted label is exact: its vector through the head, divided by the sentence length. Where the encoder normalises the pooled vector, and for the transformer head: drop each word and take the fall in the label's probability. The head is TP13's, trained on EmpatheticDialogues' training split only; EmoCause's situations come from the validation and test splits.
- **Bar.** Top-three recall of 48.1. Stretch 60.
- **Use.** `events[].words`.

## 6. Attention and speed

### TP18. More from the same pass

- **Why.** TP2 missed by 0.0035 with one added number per word. In reading research, uncertainty before a word adds to the word's own surprisal and is sometimes the better predictor ([Pimentel and colleagues 2023](https://arxiv.org/abs/2211.14301), read by a helper), and larger models fit human timing worse than small ones ([Oh and Schuler 2023](https://aclanthology.org/2023.tacl-1.20/), read by a helper). One helper search and one by the analyst found no published study relating pauses in composition to a language model's surprisal, so there is no outside number to aim at.
- **What the receipt already holds.** `attention-stops-2026-11.json` has entropy before the word (`V5`) as an exploratory row: alone it gained 0.0137, against 0.0165 for surprisal alone. The two have never been in one model.
- **Features,** all from the scoring pass already made: entropy before the word (`V5`); the previous word's surprisal; the next word's and the one after; summed surprisal from the word to the end of its sentence; whether the word follows punctuation.
- **Registered row.** The baseline's five features plus all of the above in one model, same folds, same eligible words, whole-writer intervals, against the same bar of 0.02 over the baseline. Each single addition is reported as exploratory.
- **If it still misses.** One research row: a linear probe on the reader's last hidden layer reduced to 64 components, through the `torch` reader with SmolLM2-360M, on a fixed third of sessions. It changes no default.

### TP1c. A smaller reader for the live path

- **Why.** SmolLM2-360M matched Qwen2.5-0.5B on TP2 within 0.001. The literature above says smaller is not worse for timing. [SmolLM2-135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M) is Apache 2.0 (read by a helper).
- **Do.** Convert it by TP1b's route. Run TP1b's five gates with its own references, TP2's primary, and the 3,000-word timing on two threads. Also time the 360M model at Q4_K_M.
- **Bars.** TP2 primary within 0.005 of 0.5677; 15 s per 3,000 words. If both hold it becomes the first-paint candidate, behind the flag. From parameter counts alone the analyst expects 15 to 17 s; that is a guess.

## 7. Choices: the lawful road to the maker

### TP19. What she took when five were offered

- **Why.** The guard lets choices move maker estimates. CoAuthor is a record of choices in text: 1,445 sessions by 63 writers, five suggestions per request, one taken in 72.3% of requests (the [project page](https://coauthor.stanford.edu/), read by a helper). `adapters/coauthor.py` already compiles each request into a `Decision` whose options are the suggestions plus her own continuation; `Option.features` is a dictionary; `eval/harness.py` scores handling forecasts prequentially; `fit_pipeline` takes `extra_features`; and `packet/preferences.py` already has the words for the result ("conditional feature preferences from observed alternatives"; "Feature coefficients are not drive loadings"). A helper search found no published study predicting which suggestion a writer takes.
- **Do.** Through `features/augment.py`, add to every suggestion the outputs of the packs that exist: TP10's 13 label probabilities and eight readable features; TP14's three motives if it ran. Her own option is compiled without text (`Option(option_id=...:own, origin="maker", ...)`), so it gets a missing-value flag and no reader features.
- **Scores.** Two. Among requests where a suggestion was taken: which of the five, by a conditional logit over the suggestions (chance 0.2). And the harness's existing prequential score for handling, with the reader features summarised over the five (mean and largest).
- **Rows,** nested: (0) the deterministic features as they are; (1) plus the reader features; (2) plus her own earlier picks in reader space, the mean over strictly earlier decisions of taken minus not taken, shrunk toward zero by count.
- **Bars.** (1) over (0): a gain whose whole-writer interval excludes zero. (2) over (1): the same.
- **Outcome.** If (2) clears, "what she takes when offered" is the first reading that may enter `about_maker`, through the existing admission chain and its existing wording. If only (1) clears, the reader features describe suggestions people take in general and stay on the page tier. If neither, the row is filed.
- **Expectation** (the analyst's): small. Position and length likely carry most of it.

### TP20. Priorities from an exchange (Round 18's R4)

As Round 18 wrote it: CaSiNo, 1,030 negotiations with priorities assigned at random; the other side's first five messages in, the order of three priorities out; chance 16.5%, bag of words 28.5%, a published ranker 63.6%, an expert 75% on 100 dialogues. Those four numbers were read by the theory thread through a reader tool and a helper here could not confirm them in the corpus paper's abstract; record their source when the papers are fetched. A small ranker on TP10's encoder. Bar: 45%. These are prices by design and say nothing about refusals.

### TP21. The correction log, back end only (Round 18's R5)

- A record type for an owner's answer to a probe and for a correction of a stated reading, stored locally in the ledger beside `Correction`: probe kind, the passage, the answer, the reading it answers, the time. No interface.
- The new record has a probe-kind field with four values: the three in `src/core/owner-probes.ts` (`Satiate`, `Switch`, `Remove`) and `Price`, which no card asks today and nothing in the code names yet. Reason, from the Ghost V30 pre-flight (the analyst's, a constructed miniature): `Satiate` picks out a practice kept as a means and `Switch` one kept for an audience, and on both a rule and a habit answer nearly alike, since both survive losing their purpose and their audience. With honest answers the two questions together move a rule 0.61 of the 3 units of log-odds needed against a habit. `Remove` was not modelled. A question about price separates the two by what a rule is.

### TP22. The person across many pages (Round 18's R6, without waiting for a request)

- **Data.** The [Blog Authorship Corpus](https://huggingface.co/datasets/barilan/blog_authorship_corpus): 681,288 posts by 19,320 bloggers, non-commercial research use (read by the analyst on the card). Research-only. No age or sex column is read.
- **Sample.** 1,000 writers with at least 40 posts of 100 words or more, lowest SHA-256 of the writer id.
- **Do.** Per writer, TP10's corrected mix on the earlier half of her posts by date and on the later half.
- **Scores.** Sounding Line's TR1 recipe per label: true between-person variance first, then corrected split-half stability. And own history against the typical writer: the log score of her later mix under her earlier mix against under the population's.
- **Controls.** The same within subject: sort all posts into 20 subject clusters by their word vectors, and take each writer's mix as her average departure from her clusters' mean mixes, so that a steady subject is not mistaken for a steady person.
- **Bars.** Both after the control: stability of 0.5 (TR1's bar) on at least three labels; own history ahead with an interval excluding zero.
- **Standing.** A benchmark. The maker tier stays closed. Whether returning to a subject unprompted counts as a choice under the guard is unruled, and this card assumes it does not.

## 8. Carried and stopped

| Item | Now |
|---|---|
| TP6 (RAID) | Finish the scoring that was running; fill the row |
| TP7 (choice from attention) | Runs the day EX5 arrives; Sounding Line's packet puts EX5 first |
| TP9 (IteraTeR) | As queued. Its arXiv abstracts double as TP10's neutral set |
| TP3 | Feature classifier stays. The 9B route is stopped (choice 10) |
| TP4 | Word-matching row stays; add BM25 and TP7's rarity-weighted overlap. The 9B re-rank is stopped |
| TP2's history ladder | Not rerun. Her own history added 0.001 |

## 9. Order, limits, and what is not here

**Order.** Day one: TS2; TP10's harness check and L0 to L2; TP12. Day two: TP10's L3 and pack; TP11; TP14 with IM1; TP18. Day three: TP13; TP16; TP19. Then TP15, TP17, TP1c, TP22, TP20, TP21, with the carried rows in the gaps. A card that hits the memory floor stops and the next one starts; nothing waits on a rerun.

**Memory.** Encoders here are under 1 GiB. The motive models are about 1.4 GiB each: load one at a time.

**Behind a request form, not built** (recorded in the analyst's order of usefulness; no request is sent): ValueEval 2024 (about 3,000 long texts with every sentence labelled for 19 values and for whether the value is attained or constrained; a [request form and usage agreement](https://zenodo.org/records/10396293), read by the analyst; the closest thing found to a key for "which set point moved, which way" on essay-length text); the text of the [Vent](https://arxiv.org/abs/1901.04856) corpus (33.6 million posts tagged by their writers, including curious, stressed and anxious; research and non-commercial, by request; read by a helper); PANDORA; Stanford's narratives; NetHealth; CANDOR.

**Leads not built.** Questions a text raises and whether it later answers them, as a reading of what a page leaves open for its reader: [TED-Q](https://aclanthology.org/2020.lrec-1.141) has 2,412 such questions over six talks, each rated 1 to 5 for whether it was answered, about 46% at least partly (read by the analyst). It is small and it is the reader's open questions, not the maker's Stress. StoryCommonsense labels story characters' motives, and its labellers agree at only 0.30 ([paper](https://aclanthology.org/P18-1213), read by a helper): not a key.

**Dropped, as Round 18 said:** trigger questions to the 9B by prompt, apart from TP10's one measurement; the outlook; any reading of how firmly a view is held from one finished text (people score at chance: [Tan and colleagues 2016](https://arxiv.org/abs/1602.01103), 0.54, read by a helper).

## 10. The return

`docs/ENGINE_READERS_2026-11-17.md`: one paragraph per card with its rows, bars, what cleared and what stopped it. The scoreboard gains one row per pack with the floor and the human rows beside it. A short file `docs/exchange/THEORY_RETURN_READERS.md` carries, in plain words for the theory thread: the twins table and the left-out tables (TP11), the predicted rows (TP13), the known-groups result (TP14), concern against distress (TP15), plans against worry (TP16). Each says in its first line whose proposal it tested and that the proposal is not settled.

## 11. Limits

- Section 2 is one analyst's pass over one corpus with scripts written in an evening. Every number in it is to be reproduced by the harness before it is relied on.
- Crowd-enVENT's reports are short (13 words at the median), first person, and written to order for a named feeling. Essays are none of these. TP16's Part B is the only writer-keyed check on longer text in this packet.
- A label map from feelings to needs is theory. Everything that uses one is marked `proposed`.
- The motive coders were validated on picture stories. Their use on other text rests on checks of agreement and known groups, not on an expert key.
- A reader scored against a writer's own label reads what she said she felt. On an essay it must say "on this page", and it must not hand a described feeling to the writer.
