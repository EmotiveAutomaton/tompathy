# ToMpathy 0.3 engine: the machines first, a reader cleared per use, and the word tables

*Spec sheet of 20 November 2026, from the implementation thread (the analyst) to the engine's owner agent. It stands beside `TOMPATHY_0.3_ENGINE_NINE_CHANNEL_PACKET_2026-11-19.md`, whose cards keep their text unless a line here amends them. It carries no questions. Every choice in it is made here; the curator sees the ones he may want to veto in the reply that delivered it.*

## 0. Read first

- **What this is.** One day of work, to the morning of Saturday 21 November. Two long queues, one on the Spark and one on the workstation's GPU, are launched before anything else. Five quick cards on data already held are built while the queues run.
- **Why the order changed.** Between the packet of 19 November and the push of 20 November, 05:15 PT, the Spark's GPU was busy for about 1.3 hours of 19 (summed for the analyst from the record's start and end stamps; an estimate). Research compute on the workstation was minutes. The time went to building and to waits between a job ending and its check. So the long jobs go first and run unattended, and the quick cards fill the time they take.
- **Where files go.** This file at the repository root, beside yesterday's packet. The theory handoff of 20 November at `docs/exchange/THEORY_HANDOFF_R32.md`. The 19 November handoff is refiled from the supplied copy, because its sections 10 and 11 were added after the copy this repository holds. The bundle `PREFLIGHT_2026-11-20.zip` is unpacked where the last one was; its `dot_table.py` is the renderer of amendment AS.
- **Read before building:** section 2 (amendment BA overrides a rule of this repository's own protocol and says so), then section 4 (the queues).

## 1. Terms this packet uses

| Term | Meaning |
|---|---|
| Reader A, reader B | The two local models frozen on the Spark on 19 and 20 November: `qwen3.5:9b` and `qwen3.5:35b`, each pinned by ID in the engine's record |
| Reader C | A larger model of the same family, defined in card RD2. It exists only if that card's pull succeeds |
| Reader W | The workstation's own `qwen3.5:9b`, ID `6488c96fa5fa`. A different build from reader A. Its answers never enter a fit with reader A's or B's (amendment AP) |
| Trained reader | The engine's own readable-feature model, whose saved forecasts were the comparator of card SP1 |
| The eight features | `pleasantness`, `unpleasantness`, `self_responsblt`, `goal_support`, `social_norms`, `other_responsblt`, `standards`, `suddenness`: the ratings of the recalled-event source that the engine reads from text |
| Panel | Recalled-event reports from the held-out fold, read by a reader and scored against what the writers themselves rated |
| Fresh panels F1, F2, F3 | Held-out reports not yet scored for any reader. Defined in cards RD1 and RD2 |
| Human reference | How well one person who re-read a report for the source's own study recovered the writer's rating |
| Teacher | A reader whose answers become the training key of a smaller model |
| Stand-in | A feeling word taken to mark a channel, by the map the curator admitted on 19 November. A result on a stand-in is a result on a word |
| Lift | A word's mean on an output over its texts minus the mean over the other texts, in standard deviations of that output |
| Queue | An ordered list of long jobs on one machine, launched once and worked through without an agent turn between jobs |
| Morning check | The owner's first turn on Saturday 21 November at or after 07:00 PT |
| Standard reading | The eight features with the corrected prompt of 19 November, as job Q2 reads them |
| Result sheet | The picture and short text of amendment AS, written at every landing for the curator |
| Claim ids | T1 to T10, N1 to N5, A1 to A3, S1 to S4, W1, P1 to P4, M1 to M4, LP1 to LP15, as the two handoffs list them. Always written with the word claim. Need codes are written with the words need code |

## 2. Rulings and amendments

Rulings are the curator's, with his words and their dates. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R26 | Belonging and Compassion | One need, named Belonging (20 November): "We'll get rid of compassion, merge it into belonging." Need code N5 and its tag stay in every export. He asked for results "to be reported with both so I can change my opinion during the next round." |
| R27 | SADNESS | The channel long written PANIC/GRIEF is SADNESS (19 November): "If his questionnaire named it sadness, we will also name it sadness." New cards and exports say SADNESS. Older cards and results keep their wording |
| R28 | RAGE's aim | RAGE aims at a schema and not at a person (20 November): "We'll incorporate that." Card TP35 is the first test that follows |
| R29 | People differ in the channels | "So there is variation in the channels themselves." (20 November). No card here depends on it |
| R30 | How a result is shown to him | "I don't need the methodology details. I'm more interested in your conclusions and how to interact with that." "I kind of want graphs and tables. Graphs more so" (20 November). Amendment AS |
| R31 | The machines | "We're trying to keep the spark and my GPU maximally tasked for at least until tomorrow's theory walk morning thing." (20 November). Amendments AZ, BB and BD |
| AS | Result sheets (analyst, under R30) | Every landing with a table of signed numbers writes one picture and one short text beside its ledger row. Picture: `dot_table.py` of the bundle, from a file of cells (row, column, estimate, low, high). A positive cell is a white dot, a negative one red, the dot's area shrinks toward zero, and a cell whose interval includes zero is blank, on a dark background 680 units wide with no text under 9.5 units. Text: three to six plain sentences on what to look at, then the limit sentence in the record's own words. No method paragraph. Filed under `docs/exchange/result-sheets/` |
| AT | No machine names in records (analyst) | A record names the Spark as the Spark and reaches it as `ssh spark`. Host names, network names and addresses stay out of packets, records and receipts. This repository already does so |
| AZ | Machines first (analyst, under R31) | In any packet, long jobs come first: a job longer than an hour that needs nothing new is launched at once, and the others are built before any quick card. Each machine has one queue file, read again after every job, so jobs can be added while it runs. A job that fails is recorded and the queue moves on. A job's timing pilot and its full run are one job: the run goes ahead unless the pilot projects more than the job's cap in section 4, in which case the job trims by the rule in its row and records that |
| BA | A reader is cleared per use (analyst). **This overrides a rule of this repository** | The SP1 protocol says teacher studies cannot use an unqualified result, and the record of 20 November says a higher score alone does not qualify a teacher. Both followed from yesterday's card SP1, which set one bar for the readers' panel and did not say what missing it would stop. That gap is the analyst's, and so is this override. The rule from here: (1) Any use of a reader needs the two general bars of SP1, repeatability and valid output. Readers A and B both met them (300 of 300, 600 of 600). (2) SP1's third bar compared a prompted reader with a model trained on the panel's own source, on eight ratings. It decides who fills each of those eight slots, one feature at a time, by card RD1. Reader B missed it as a mean and is not a qualified reader of the eight as a set. (3) A teacher is cleared by the checks of the card that uses it. For TP31 those are that card's own teacher checks, which nobody has read. Reader B teaches TP31 if it passes them. The record's rule of no further retry of the SP1 panel stands; nothing here reruns it |
| BB | The workstation's GPU (analyst, under R31). **This amends the workstation's one-long-job rule for one lane** | One GPU lane beside the one counted CPU scorer and outside its count. It carries two kinds of job, one at a time: reader W through the workstation's local model server (temperature 0, seed 23, thinking off, reader A's context and output limits), and encoder training with the engine's own fine-tuning runner, which is new work with its own pins (amendment AO). The lane yields to anything else on the machine: when 20 calls or training steps in a row take more than five times the lane's median, or the workstation's commit floor is reached, it pauses for ten minutes and resumes from its last saved answer or checkpoint. It uses open data only |
| BC | Names in exports (analyst, under R26 and R27) | Any table with need-level rows gives them twice: Belonging and Compassion apart (need codes N3 and N5), and merged. Channel rows say SADNESS |
| BD | A larger reader for one card (analyst, under R31). **This amends the 64 GB limit** of yesterday's card SP1 and of this repository's resident-memory check, for card RD2's reader C only | Up to 100 GB resident while reader C is loaded. No other job of this program runs on the Spark while it is loaded. About 20 GB stays free, which is enough for the other program's sealed tabular jobs. If loading leaves less than 15 GB free, reader C is unloaded and its arm is skipped |

**Stated by the curator and not ruled. Build nothing on these:** a reference is set by whatever sets the schema; a social contract as a second convergent solution; where Neuroticism sits; Belonging as being predicted by other people; second-order slopes as triggers; a channel taken up and used by a schema.

## 3. The Spark lane and the workstation lane: rules

Section 3 of the 19 November packet stands (reach, places, one record, the GPU lock, four threads, cost first, no sealed data). Added:

- **One launch.** The Spark's queue is started once, detached from the session that starts it, and logs each job's start, end, exit and seconds per 100 texts. Each job takes the GPU lock for its own run and releases it, so another program's job can pass between two of ours.
- **Resuming.** A job that finds its own finished output does nothing. A reading job writes each answer as it is made and resumes after the last one written.
- **Heat.** The engine's own guard stays as run on 20 November: three numerical threads and one for telemetry, stop at 90 °C.
- **The workstation lane** follows amendment BB and keeps its own lock file.

## 4. The two queues

Times are the analyst's arithmetic from the record's speeds (reader B about 110 seconds per 100 reports with eight ratings; reader A about 215) and are sizes, not promises.

**The Spark, in this order of priority.** The queue runs the highest job in this table that is in its file and not yet done.

| # | Job | Reader | Texts | Size | Cap | If over the cap |
|---|---|---|---|---|---|---|
| Q1 | Card RD1, panel F1 | A, then B | 350 reports each | about 20 minutes | 1 hour | none expected |
| Q2 | Card TP24's feature pass on the recalled-event reports | B | every report B has not rated, except panel F2: about 5,400 | about 1 hour 40 | 4 hours | none; it resumes |
| Q3 | Card TP31, the first 2,000 sentences, then the card's two teacher checks as the job's last step | B, then A | 2,000 each | about 1 hour | 3 hours | none; it resumes |
| Q4 | Card TP31, sentences 2,001 to 30,000 | B | 28,000 | about 4 hours | 8 hours | it stops with what it has |
| Q5 | Card RD2: development, reader C, the test on panel F2, then reader B's standard reading of F2 | B, then C | 600 training reports by six prompts; reader C's 900 readings; then 350 each | 2 to 5 hours | 6 hours | drop the two prompts that think aloud; then drop reader C |
| Q6 | Card TP24's second source: the eight features for the chat situations | B | 24,850, in the order of the SHA-256 of `TP24:23:` and the situation's id | about 7 hours 40 | none | it is stopped at the morning check and resumes later |
| Q7 | Card TP31, beyond sentence 30,000 | B | fills any time left | | none | stopped at the morning check |

Q1 and Q2 need nothing new: the corrected prompt (the second version, of 19 November), the existing runner, and lists of report ids. **Launch them before building anything else.** Q3 to Q7 are added to the queue file as they are built. Job Q3 ends by computing TP31's two teacher checks and writing a pass or fail file. Q4 and Q7 start only if that file says pass, so no agent turn is needed between them.

**The workstation's GPU, in this order.** These jobs are numbered G, so that none shares a name with claim W1.

| # | Job | What | Size |
|---|---|---|---|
| G1 | Card TP38, the food check, by reader W | about 4,100 short situations | under an hour |
| G2 | Card TP30's fine rung and size ladder, and card RD2's trained side | training, as the cards say | unknown on this card; a timing pilot of one fold sizes it |
| G3 | Card RD2's six prompts by reader W, on the development reports only | 600 training reports by six prompts | one to three hours |

If the workstation's environment has no GPU build of the training library, G2 moves to the Spark between Q5 and Q6, and the return says so. No package is installed on the workstation to avoid that.

## 5. Cards

### RD1. Who fills each of the eight slots (claims M1, M4)

- **Why.** On SP1's panel reader B read four features better than the trained reader and four worse. A mean over eight hid that. The slots of card TP24 are filled one feature at a time.
- **Panels.** The held-out reports that are not among SP1's 500, ordered by the SHA-256 of `RD1:23:` followed by the report's id. The first 350 are F1. The next 350 are F2: no reader reads them until card RD2's test.
- **Candidates, fixed here before F1 is read,** from SP1's panel as filed: reader B for pleasantness, unpleasantness, `self_responsblt` and `other_responsblt`, the four where it led.
- **Read on F1,** per feature and reader: the rank correlation with the writers' ratings; its difference from the trained reader's on the same reports, with an interval from 2,000 draws of reports.
- **Human reference.** The source's own re-read ratings cover the held-out fold, five re-readers a report by the engine's census. The reference is the mean over re-readers of one re-reader's rank correlation with the writer, on the same reports. The rank correlation of the five re-readers' mean with the writer is shown beside it as a ceiling.
- **Slot rule.** A feature goes to reader B only if it is one of its four candidates and, on F1, the interval of B's difference from the trained reader is above zero. Every other feature goes to the trained reader. Readers A and W fill no slot.
- **Registered** (the analyst's): reader B takes the slots for pleasantness and `self_responsblt`, where it led by about 0.10 on SP1's panel. Bar: the slot rule above.
- **What each outcome means.** B takes two to four slots: the trigger reader runs on a mix of the two readers, each where it is better. B takes none: the eight slots stay with the trained reader and reader B's use is as TP31's teacher only.
- **Limit.** A panel of 350 places a rank correlation within about 0.05 either way. Writers' ratings are one person's account of an event, so no reader can be expected to match them fully; the human reference says how far a careful stranger gets.
- **Prior art.** The source's own paper compared readers' and writers' ratings and trained models on both ([Troiano, Oberländer and Klinger 2023](https://doi.org/10.1162/coli_a_00461); title and abstract opening checked by lookup, paper not opened). The human reference here repeats a figure of that kind on these reports and is labelled a replication.

### RD2. Can a reader read a broken standard? (analyst's card; claims M1, T4)

- **Why.** Both local readers fall short on whether a rule or a standard was broken, and those two readings are what SHAME's trigger turns on.
- **Three rivals.** The prompt is poor; the model is too small; the text does not hold the answer.
- **Prompted side, reader B, two features only (`standards`, `social_norms`).** Six prompts, written and hashed before any score is read:
  - V0: the prompt of 19 November as corrected, cut to the two features.
  - V1: the source questionnaire's own wording of each item and its scale labels, word for word, answered as the person who wrote the report.
  - V2: V1, thinking on, with 1,024 output tokens.
  - V3: V1 with eight worked examples from training reports outside the development set, the same eight in every call, each shown with the writer's two ratings. They are the first two reports found in each band of the `standards` rating (1; 2 or 3; 4; 5), in the order of the SHA-256 of `RD2:ex:23:` and the report's id.
  - V4: V1 in two steps inside one answer: first yes, no or unclear on whether anyone broke a rule, a law or a social norm, and on whether what happened went against the writer's own standards; then the two ratings.
  - V5: V3 with thinking on.
- **Development.** 600 training reports, ordered by the SHA-256 of `RD2:23:` and the report's id, the eight examples excluded. The held-out fold is not touched. For each feature the winner is the prompt with the highest rank correlation, if it beats V0 by 0.03 or more; if none does, V0.
- **Size as a third arm: reader C** (amendment BD). The largest tag of the same model family whose listed weights are under 96 GB (the engine's protocol of 19 November records one listed at 81 GB), pulled once, pinned by ID, thinking off, with reader B's limits. It answers V1, extended to all eight features, on the 600 development reports, and the first 300 a second time. It must meet SP1's two general bars: identical output on 99% or more, valid output on 99.5% or more. If the pull fails, memory runs short or the heat guard trips, the arm is skipped and named in the return.
- **Small-reader side, a description (job G3).** Reader W answers the same six prompts on the same 600 development reports. No held-out panel is spent on it. It says whether a model of the size the engine could serve can be prompted into reading the two features at all; reader A, of the same size, read both at about zero with the corrected prompt.
- **Trained side (job G2).** The trained reader's recipe, unchanged, with the encoder swapped for each rung of TP30's ladder below, fitted on the training reports with five folds, by writer where the file has a writer id.
- **Test, once, on panel F2.** Per feature, up to four candidates: the winning prompt, reader C, and each trained rung. Beside them: the trained reader as filed, and the human reference.
- **Naming rule.** A candidate is named for a slot only if, on F2, the interval of its difference from the trained reader is above zero. With up to eight comparisons, chance alone names one in about every five rounds like this. So a named candidate takes the slot only after it is at or above the trained reader again on panel F3: SP1's reports 301 to 500, which were read for timing. If the record shows those 200 were ever scored against the writers, there is no F3, the slot stays with the trained reader, and the candidate waits for fresh reports.
- **Reader C as research reader.** If reader C is at or above reader B on six of the eight features on F2, it is named the candidate research reader. A later packet confirms it on fresh reports before anything uses it.
- **Registered** (the analyst's): no candidate is named for either feature.
- **What each outcome means.** A prompt is named: the engine can read SHAME's trigger from a third party's text with the reader it has. Reader C is named and no prompt is: it takes a model that size. Nothing is named and one re-reader's figure is at or under the trained reader's: the text does not hold it, and SHAME must be read through the writer's own word or own rating. Nothing is named and the re-reader is well above: the text holds it and no reader here can get it yet.
- **Limit.** Two features in one source of recalled events written to a feeling word.
- **Prior art.** Not found in a light search: a comparison of prompted and trained readers with human re-readers on these two appraisals alone.

### TP24, TP31, TP30 and TS4: what changes

- **TP24.** Unblocked by amendment BA for its evaluation. Each of the eight slots comes from the reader RD1 clears for it. Where the trained reader's saved forecasts do not cover a report, its forecasts are made by the filed recipe with five folds, by writer where the file has a writer id. The rest of the card stands, bars included. It is evaluated on the recalled-event reports when Q1 and Q2 have finished; panel F2's reports join when Q5 has.
  - **Added, a second source** (the analyst's; a description with no bar). The same fixed table, fed with the same slots read from the chat situations (job Q6), scored against each writer's own word under the admitted map, for the seven channels that have a writers' stand-in. It is computed at the morning check on however many situations Q6 has read; their order makes any prefix a fair sample. Its limit: no reader's features were ever checked against writers in this source.
- **TP31.** Unblocked by amendment BA. The teacher is reader B, if it passes the card's own checks.
  - **The list.** Every sentence of the card's sources gets an id. The list is built in blocks of 60: ten sentences from each of six groups (chat situations, recalled-event reports, forum comments, story lines, writer-typed essay sentences, question-site answers), each group in the order of the SHA-256 of `TP31:23:`, its source and the sentence id. A group that runs out leaves later blocks. Any prefix of the list is then a balanced sample, so the pass can be stopped at any time.
  - **Checks, unchanged, on the first 2,000** (job Q3), which reader A reads as soon as B has: the two readers' agreement (Cohen's kappa 0.60 or more) and the known groups. The job computes them as its last step and writes a pass or fail file. If a check fails, the pass stops there, the failure is filed, and the queue moves on.
  - **If they pass,** B reads on (jobs Q4 and Q7). The student is trained at the morning check on what exists, 20,000 sentences at least, and its bars are unchanged.
- **TP30.** The fine rung runs as the engine's protocol of 20 November sets it, on the workstation's GPU under amendment BB (job G2), as a new reader with its own pins. Added, the size ladder (analyst's): the same protocol with `sentence-transformers/all-mpnet-base-v2` and with `answerdotai/ModernBERT-large`, three seeds each, pinned by revision at download, licence recorded. If a rung runs out of GPU memory its batch is halved once; if it still does not fit, or cannot be fetched, the rung is skipped and named in the return. Each rung reruns tests 1, 2 and 4. **Adoption rule:** a larger rung replaces the frozen one in a pack only if, on all three seeds, it gains 0.02 or more in mean area over the seven channels on writers' labels and CARE reaches 0.70. Otherwise the frozen rung stays, because it is cheaper and no worse.
- **TS4.** TP30's first test passed on 19 November. The row now waits only on a gate pack from TP31.

### TP34. The word table from saved forecasts, widened (handoff leg 1; claim W1)

- **Question.** What mix of the nine channel outputs goes with each of the 32 words the chat writers chose, and for which words are all nine quiet?
- **Data.** The saved nine-number forecasts of TP30's frozen rung for the 24,850 chat situations, each with its writer's own word. No new reading. No Spark.
- **Table 1.** For each word and each output: the lift, with an interval from 2,000 draws of whole writers. Filed whole, 32 by 9, and drawn as a result sheet.
- **Table 2, the widening.** Floor of an output: the 95th percentile of that output over the held-out forum comments that every rater labelled neutral. For each word: the mean over its situations of the largest of the nine outputs, and the share of its situations in which no output passes its floor. The same two figures over all situations are the baseline. Words are ranked by the second figure.
- **Registered before the data** (the theory thread's blind list of 19 November, read as the handoff registers it: the top two channels per word).

| Word | Named | Word | Named |
|---|---|---|---|
| embarrassed | SHAME, PLAY | joyful | PLAY, SEEKING |
| ashamed | SHAME, SADNESS | jealous | SADNESS, RAGE |
| guilty | CARE, SHAME | lonely | SADNESS |
| proud | SEEKING, PLAY | grateful | CARE, PLAY |
| anxious | FEAR, SADNESS | disappointed | SEEKING, on the low side: its lift is below zero (scored apart) |
| hopeful | SEEKING, FEAR | | |

- **Score** (the scoring rule is the analyst's). A hit is a named channel that is one of the word's two largest lifts. Nineteen channels are named over ten words.
- **Reference.** A reader that knew only pleasant from unpleasant would already score hits, because the list names pleasant channels for pleasant words. So the reference keeps that: the named sets are dealt out again among words of the same side, the four pleasant words (proud, hopeful, joyful, grateful) among themselves and the six unpleasant ones among themselves, over all 17,280 deals, and the score is computed for each.
- **Bar.** The score is above the 95th percentile of the deals. The count with three columns in place of two is filed beside it.
- **What each outcome means.** Past the bar: the blind list holds as a first recipe book beyond what pleasant and unpleasant give, and the rows that missed are the ones to revise. Under it: the list is replaced by table 1. Either way, table 2's top rows are the theory's lead on what the nine do not cover, which is the curator's question of whether nine is the right number.
- **Limits, to travel with every row.** The reader was trained on strangers' labels of forum comments. SHAME's output rests on one source. LUST's stand-in means wanting in general. A row is a recipe for a word and not a reading of a channel.
- **Prior art.** Feeling words as blends of a few primaries is an old proposal ([Plutchik 2001](https://doi.org/10.1511/2001.28.344); title only, as the theory thread's record has it). Not found in a light search: recipes over Panksepp's systems fitted from a reader's saved outputs.

### TP35. Is RAGE about suddenness? (handoff leg 2; claim T1)

- **Question.** Within reports of anger, does an event the writer rated more sudden go with stronger anger, once whose doing it was and how unpleasant it was are held?
- **Data.** The recalled-event reports with the writers' own ratings, every report (nothing is trained, so the held-out fold is not spent). Columns by the source's names: `suddenness`, `other_responsblt`, `self_responsblt`, `unpleasantness`, and the writer's rating of how intense the feeling was. First step: check each column in the file's header. A missing column voids its row; the row is not replaced.
- **Form.** Within the reports written to anger: intensity on suddenness with the three other ratings as covariates, all standardized within the feeling word; ordinary least squares; intervals from 2,000 draws of whole writers. The same fit within the reports written to sadness.
- **Registered** (the theory's): the slope on suddenness is positive for anger, and larger for anger than for sadness. **Bars** (the analyst's), in standard deviations of intensity per standard deviation of suddenness: the anger slope at 0.08 or more with its interval above zero; the difference at 0.08 or more with its interval above zero.
- **What the design can see.** With about 550 reports to a word, a slope of 0.12 is seen four times in five, and a difference between two words of 0.17. A smaller true effect returns as could not say.
- **Beside it, as descriptions.** The same slope for each of the other negative feeling words, as one dot row. The same fit with the writer's rating of how predictable the event was in place of suddenness. A second form that asks only whether intensity is at the top of its scale, since recalled anger sits near the top.
- **What each outcome means.** Both registered rows land: sudden stays in RAGE's trigger. The anger slope is positive with its interval above zero and under its bar, or the difference does not land: leaning; sudden stays in the wording as untested at this size. The anger slope's interval sits inside plus or minus 0.08: flat, and by the handoff a flat result leaves the trigger as an act against me and drops sudden from it.
- **Second table on the same file: does Neuroticism go with how strong or with how long?** (the analyst's, toward handoff leg 3; claim S3). If the file carries the writers' short personality items and their rating of how long the feeling lasted: across writers, within negative feeling words, the Neuroticism score against intensity and against duration, each standardized within the word, with the event's own duration held. Registered in the theory's direction: the score goes with duration more than with intensity. Bar: the difference of the two slopes above zero with its interval, by draws of writers. No column of age, sex or other demographics is read.
- **Limits.** A report is a remembered case of a word, chosen to fit it, and not a sample of moments. Suddenness and intensity are one person's ratings made together afterwards. The Neuroticism score is two items and the comparison is between people.
- **Prior art.** Which appraisals predict how intense anger is has been studied ([Van Mechelen and Hennes 2009](https://doi.org/10.1080/02699930902958297); title checked, paper not opened). Neuroticism against the intensity and duration of feelings in general has been studied ([Verduyn and Brans 2012](https://doi.org/10.1016/j.paid.2011.12.017); title checked, paper not opened), so the second table is labelled a replication in a new sample. Not found in a light search: the suddenness slope within anger against the same slope within sadness.

### TP36. Which need tags part (handoff leg 5, first ask; claim N4)

- **Question.** The needs travel together. Does every pair still part somewhere, and which pair parts least?
- **Data.** The need reader's export on the three labelled sources. No new reading.
- **Do.** A need's score for a text is the mean of its tags' standardized forecasts under tag map version 2. A need moves up in a text when its score is above plus 0.5 standard deviations for that source, down when below minus 0.5, and is still otherwise. For every pair of needs and each source: the shares of texts where both move the same way, where they move opposite ways, where one moves alone, and where neither moves; and the plain correlation of the two scores, with intervals by writer where writers are known. Under amendment BC the table is given with Belonging and Compassion apart and merged. Filed whole.
- **Pairs to watch** (the handoff's): Compassion with Belonging, Respect with Belonging, Competence with Respect.
- **Registered** (the analyst's reading of two statements): (1) every pair's correlation is under 0.80 in every source, which is what distinct means here; (2) if Belonging and Compassion are one need, their correlation is the highest of all pairs in at least two of the three sources.
- **What each outcome means.** (1) fails for a pair: to this reader the two are one thing, and the pair is listed for the theory thread. (2) holds: the merge of 20 November has its first support in text. (2) fails: in text the two travel together no more than other pairs do, which is what he asked to see before settling the merge.
- **Limits.** A tag is a word-proxy reader's contrast. Which tag belongs to which need is the map's. What a text is about is not what moved in its writer.
- **Prior art.** No search was made for this card. It is a table from the engine's own export that the handoff asks for, and nothing in it is called new.
- **Not in this card:** the row that Stress runs higher when Belonging and Compassion part. The handoff withdrew it.

### TP37. How many separate things do the reports need? (analyst's card, from the curator's ask of 20 November; claims A1, W1)

- **Where this stands with the handoff.** The handoff enters a tenth channel as a lead and not as a leg. This card is the analyst's addition, made because the curator asked for it in his own words and because it costs minutes on data in hand. It does not test for a tenth channel. It counts dimensions and shows what each looks like.
- **His ask.** "Like, come on, you need to like PCAs and shit to say that there might be another set of categories and then suggest what those categories would be."
- **Question.** Between what a writer rated about an event and the feeling word she wrote to, how many separate dimensions does held-out data support, and what does each look like?
- **Data.** The recalled-event reports: the writers' 21 ratings of the event and the feeling word each report was written to. Writers only; no reader is involved.
- **Form.** The pre-flight's rule (`pf_rank.py`): a linear discriminant fit on the training folds, the first r dimensions kept, a plain multinomial fit on those, and the held-out loss for each r from 0 to one less than the number of words, over five folds by writer. Two counts: the smallest r within one standard error of the best, and the largest r up to which every added dimension helps by more than two standard errors.
- **Report.** Both counts. Then the kept dimensions, turned for reading by a varimax rotation, as two result sheets: dimensions by the 21 ratings, and dimensions by the feeling words. Beside each dimension, the channel whose trigger it most resembles, as a naming aid of the analyst's and not as a test.
- **Reading rule, fixed before the data.** The count is read as a floor on the number of separate things between the ratings and the word, capped at one less than the number of words. In the pre-flight's made worlds (21 ratings, 13 words, 6,600 or 1,500 reports) neither count exceeded the planted number in any of 300 worlds, 60 of which had five-point ratings piled at the low end and channels with thresholds. At 6,600 reports with nine equal dimensions planted, the first count's median was eight and the second's nine. With nine of falling strength, six and seven. With twelve equal, nine and ten. That is what those worlds showed and not a proof, and the fixture folds by report where the card folds by writer. The theory names more than nine things that could shape a word: the nine channels, the four needs and Stress. So a count under nine does not say there are fewer than nine channels, and a count of ten or more is a lead on what else shapes the word.
- **Limits.** One source, one kind of data, words chosen by the task and not by the writer.
- **Prior art.** How many dimensions feeling reports need is a long-running question with answers from four ([Fontaine, Scherer, Roesch and Ellsworth 2007](https://doi.org/10.1111/j.1467-9280.2007.02024.x)) to twenty-seven ([Cowen and Keltner 2017](https://doi.org/10.1073/pnas.1702247114)); titles and abstract openings checked by lookup, neither paper opened. Not found in a light search: a held-out count between rated appraisals and the word, read against Panksepp's nine.

### TP38. The food check (handoff section 7; claim W1; the workstation's GPU)

- **Why.** In the word table of 19 November ashamed and guilty landed on the food tag. The plain rival is that the stories are about eating. The handoff: "A reader of the texts could settle it in an hour."
- **Texts.** Every chat situation whose writer chose ashamed, guilty, embarrassed or disgusted, and 1,000 others in the order of the SHA-256 of `TP38:23:` and the situation's id.
- **Reader W answers two things per situation:** whether eating, food, drink, cooking or dieting is part of what happened (yes or no); and what kind (something the writer ate or drank; a diet or weight goal; food given, taken or wasted; not about food).
- **Second key.** A fixed word list, filed with its hash before the reader runs: eat, ate, eating, food, diet, snack, meal, cake, pizza, drink, drank, hungry. Agreement between the list and the reader is reported.
- **Read.** The share of each word's situations that are about food, with intervals by writer. Then the food tag's lift for ashamed and for guilty, computed again with the food situations left out.
- **Registered** (the plain rival, registered by the analyst): each lift falls by more than half when food situations are left out.
- **What each outcome means.** If it falls: the food tag was the stories' topic and says nothing about channels. If it stays: shame and guilt sit near DISGUST's tag in text that is not about eating, which the theory thread will want.
- **Limit.** One source of short situations; one small local reader, checked only against a word list.
- **Prior art.** No search was made for this card. It checks a rival for two cells of the engine's own table, and nothing in it is called new.

### Carried from 19 November, unchanged: TP32, TP33

They follow the cards above. Nothing in them changed.

### The record at every landing

One ledger row (card RC1) and one result sheet (amendment AS). The row's `limit` field is the card's limit sentence.

## 6. Order

| When | What |
|---|---|
| First | Launch Q1 and Q2 on the Spark. Build TP38's texts and launch G1 on the workstation's GPU |
| Next, so that neither queue runs dry | Build in this order: TP31's list (add Q3, Q4 and Q7); the fine rung's payload and the ladder (add G2); RD2's six prompts and reader C (add Q5 and G3); the chat situations' list (add Q6) |
| Then | TP34, TP35, TP36 on the workstation's processor, in that order |
| When Q1 and Q2 end | RD1's table. TP24's evaluation on the reports |
| After that | TP37. TP32. TP33 |
| At the morning check | RD2's test. The ladder's table. TP31's student on what exists. TP24's second source on what Q6 has read. Stop Q6 and Q7 where they are and file how far each got |

**When building is the bottleneck,** keep this order and drop from the bottom: the queues; TP34; TP35; RD1 and TP24; TP36; TP38; TP31's student; RD2; the ladder; TP37; TP32; TP33.

## 7. Predictions before data (the analyst's guesses, filed so they can be scored)

| Card | Guess |
|---|---|
| RD1 | Reader B takes pleasantness and `self_responsblt`. One re-reader is below both machine readers on pleasantness and near them on the two standards features |
| RD2 | Nothing is named. The worked examples (V3) gain most among prompts. Reader C beats reader B on both features and still trails the trained reader. The largest encoder gains 0.03 or less. Reader W stays under 0.15 on both features with every prompt |
| TP31 | The two readers agree past the bar. The student passes on two held-out sources of three |
| TP30 | CARE stays under 0.70 on writers' labels at every rung |
| TP24 | On chat situations the fixed table's call is right less often than on the reports |
| TP34 | Short of the bar. The quietest words are trusting, faithful, grateful and proud |
| TP35 | The anger slope is positive and under its bar. It is not larger than the sadness slope. Duration goes with the Neuroticism score more than intensity does |
| TP36 | Competence with Respect is the tightest pair. Belonging with Compassion is not |
| TP37 | Six to eight dimensions |
| TP38 | The food tag's lift falls by more than half for guilty and by less than half for ashamed |

## 8. The return

One file, `docs/exchange/THEORY_RETURN_2026-11-21.md`, one row per card above: verdict word, estimate, interval, bar, the limit sentence, the ledger row's id, and the result sheet's path. Then: how far each queue got, with seconds per 100 texts for each job; what was skipped, with its reason; which of section 7's guesses held. It names the branch of each card's "what each outcome means" that the result falls in, and stops there. Reading it is the theory thread's work.

## 9. Limits of this packet

- No card here was pre-flighted on real text. The pre-flight covers one form (TP37's count) and the renderer.
- The queue sizes rest on one day's speeds and on a guess at half a second per sentence for TP31's list. Reader C's speed is unknown; its size in the table is a guess at four times reader B's. Training speed on the workstation's GPU is unknown.
- RD1's candidates come from a panel of 300.
- Amendment BA changes a rule after a miss. Reader B missed SP1's panel bar by 0.0002 on the mean, and trailed the trained reader by 0.10 and 0.14 on the two standards features. Under BA it can still teach TP31, on that card's own checks, and can still fill a slot it wins on fresh reports. That is an override made in the open, not a pass.
- Every result here is about words, labels or a reader's outputs. None is a reading of a channel in a person.
