# ToMpathy 0.3 engine: one more day of studies (packet of 28 November 2026)

*From the implementation thread, for the engine's agent. It turns the results and alignment thread's handoff of 28 November (Round 38, saved as `docs/exchange/THEORY_HANDOFF_R38.md`) into cards. Syntheses marked "the analyst's" are the implementation thread's and are not the curator's rulings. Nothing here asks the curator a question: his approvals are in the message that delivers this packet. Read at the engine's head `fbd597d`.*

## 0. Read first

- **What this is.** Eight studies on outputs already saved (cards TP80 to TP87, the handoff's E1 to E8), four cards the analyst adds (TP88 to TP91), the closing of yesterday's cards that stopped on the workstation's memory floor, two jobs for the Spark's GPU (Q35, Q36) and a restart of the workstation's queue with one new job (G16).
- **The aim.** The curator, on 28 November: "we're crafting another day's worth of studies". And on 27 November: "your central main goal is to push the engine forward." Each card ends with the change it makes to the engine.
- **What changed from the handoff, and why.** Each is the analyst's, from the made worlds in `PREFLIGHT_2026-11-28.zip`.
  - E1 holds topic by clusters fitted on other authors. In a made world with thirty topics, 10 clusters left a topic's lead standing in most runs, 30 in some and 100 in few, so K = 100 carries the verdict and 30 and 300 are filed beside it. A topic that two or three authors share cannot be held this way (`pf_topic.py`).
  - E2's ceiling is not the plain analysis-of-variance figure, which overstated it when many writers have one report. The card adds, for each cell, the largest true correlation its null still allows (`pf_ceiling.py`).
  - E3's verdicts come from a reader's mark of which need a text is about (job Q35), with the tag directions taken out of each channel's reading. Tag cells are descriptions: with no key at all they named a highest group in most made runs, because heads taught on one vector overlap (`pf_keys.py`).
  - E4 takes standing from the reader's standing mark for the same reason, and leaves out the reports the PRIDE head was fitted on (`pf_doing.py`).
  - E5's verdict is on chat, with the tag directions taken out of the SADNESS reading. Her own rating of intensity, if the event file holds one, is filed beside it on events, where 550 texts are too few to decide (`pf_lossneed.py`).
  - E6 starts from what is saved. Card TP66's sheet already has RAGE beside FEAR on the same texts, so two of the three guesses are answered there, and only SEEKING is new. Its saved centres add that on events SADNESS comes late in a loss, while neither FEAR nor RAGE comes early. These texts are short: 1,361 of the 1,700 chat loss texts have two sentences. In the made world an order as large as the one TP66 landed showed in texts that short, and small orders did not. A pair says which of two centres is earlier and not that the first is early, so each link is scored with the channels' own centres (`pf_order4.py`).
  - E7's first question cannot be answered as asked. With a good reader the suddenness rating beat the outputs in every made world, with or without an output for surprise; with a poor one it lost in a world with no such output. So a win does not show that surprise has no channel, and a loss does not show that it has one. The card scores print's claim and SEEKING's place, and files the rest as description. An arm on recalled events, with the writer's own suddenness rating, is added (`pf_surprise.py`).
  - E8 adds a check across two halves of the authors before a group is named, and runs again with topic held.
- **What yesterday left open, and how it closes.**
  - Every workstation job stopped when free commit reached the 8 GiB floor (`scripts/word_table_lane.py`), and the reader arm cannot resume. Two amendments: a stopped job's finished rows are admitted as a prefix panel (DU), and the arm resumes and treats the floor as a wait (DV). G12's finished rows cover every chat text, so TP67's three-way split, TP74 and TP77's standing check run today on chat.
  - The line "39 valid new ratings out of 28,846 new calls" (job G15) reads as a failure of the reader. It was the memory floor: 28,846 calls were planned and fewer than 100 ran. Card TP89 rewords it.
  - Q30 and Q33 still wait on a copy of two sets that the Spark can read (section 5).
  - When Q31 exits, an armed handoff (`scripts/rapid_q31_release.py`) gives the Spark's GPU to the filler. Section 6 holds it so that Q35 goes first.
- **Landed this morning, after the handoff was written.** Card TP61's sheet gained two results. Its part (a): the same map group ranked highest in both date halves for 45.4% of 5,409 writers, an excess over random dealing of 29.7% [28.3%, 30.9%] against a rotated band of 21.0% to 27.8%, which that sheet leaves unresolved under amendment CX. Its dated profiles: the tags' mean repeat at 5, 10, 20 and 40 openings a half is 0.32, 0.46, 0.60 and 0.72, each just above its rotated band, while at five openings the gain in matching a writer over a style and topic baseline lies inside its band. So the first part of card TP90 is already answered and is dropped, and card TP80 also files the highest-group statistic with topic held.
- **Sizing, from what was measured.**
  - Cards. On 27 November this repository landed thirteen cards in 2.8 hours once their inputs were saved, then eight parts in 17.7 hours while it waited on GPU jobs. Ten of the twelve cards here start on saved outputs, two of them (TP82, TP84) in part. TP88 and the mark arms wait on Q35, and TP91 comes last. With the second build of each table that amendment DZ asks for, expect six to ten hours of card work.
  - Spark GPU. Q35 is 5.8 hours at B's recorded speeds (53.74 seconds a hundred chat texts, 111.65 a hundred recalled events) and Q36 is 1.0: 6.8 hours, then the filler Q24b until the cutoff.
  - Workstation GPU. The rest of G12 (2.9 hours), G16 (6.8), the rest of G14 (1.9) and of G13 (12.9): 24.5 hours at W's recorded speeds, if the commit floor lets them run. Yesterday it did not, so this is a ceiling and not a forecast.
  - In sum: about a third of a day of card work, a full day on the workstation's GPU if memory allows, and a quarter of a day of new work on the Spark's. The limit is saved readings and questions, not machines.
- **The window.** Yesterday's: it ends on Sunday 29 November at 08:00 PT (1795968000). The return goes on in `docs/exchange/THEORY_RETURN_2026-11-29.md`.
- **Files.** This packet at the root as `TOMPATHY_0.3_ENGINE_ONE_DAY_PACKET_2026-11-28.md`. The handoff as `docs/exchange/THEORY_HANDOFF_R38.md`. The bundle as `docs/exchange/PREFLIGHT_2026-11-28.zip`. Yesterday's bundle is not in the tree; the return says where it was put.

## 1. Terms added

- **Rotated band.** As amendment CU has it: the spread of a statistic when the trained heads are replaced by rotated copies of themselves (`scripts/rapid_nulls.py`, seed rule unchanged, with this card's id in the seed text). 1,000 sets unless a card says otherwise. Where a card rotates channel heads, the ten are rotated together.
- **Topic held.** A reading from which the mean of its topic has been taken away. A topic is a cluster of post openings in the vectors' own space, fitted on other authors (card TP80).
- **Planted survivor.** A made constant that belongs to an author and to no topic, added to the real vectors to see how much of it the topic step takes away (card TP80).
- **Ceiling.** The largest correlation two noisy scores could show if what they measure agreed perfectly: the square root of the product of their reliabilities (card TP81).
- **A reading with the tag directions taken out.** A channel's head, less its part inside the span of the nineteen tag heads, applied to the same vector. In the made worlds this is what stopped a head's overlap with the tags from passing as a key (cards TP82, TP83 and TP84).
- **Need mark.** A reader's answer to one question about a text: which of the writer's needs is most at stake (section 3).
- **Prefix panel.** The rows a stopped reader job finished, in roster order, verified by hash (amendment DU).
- **Second build.** The same table made again by a script that shares no code with the first (amendment DZ).
- **The map's groups** are the six of `TAG_MAP_V2` in `engine/tompathy_engine/packs/trigger.py`: Competence (curiosity); Meaning (order, savings, serenity); Belonging (acceptance, family, contact); Respect (status, approval, power, competition, honor); Compassion (idealism); Body (food, rest, health, tranquility). Romance and independence are in no group. A group's score for a text is the mean of its tags' standardized linear scores.

## 2. Rulings and amendments

**The curator's words this sheet rests on.**

| Id | Ruling | His words |
|---|---|---|
| R51 | One more day of studies | "we're crafting another day's worth of studies" |

Ruling numbers: R48 is the ruling on reports and nothing else. R49 is not used. R50 is in Sounding Line's addendum of today.

**Amendments (the analyst's, unless marked).** The letters run on from Sounding Line's addendum of today, which ends at DT.

| Id | What | Text |
|---|---|---|
| DU | Prefix panels (the curator's approval is in the message that delivers this packet) | A reader job that stopped at the memory floor is admitted as a prefix panel: its finished rows, in roster order, verified by hash up to a stated ordinal. `scripts/rapid_standing_return.py` and every reader of a W panel accept such a job. Agreement between readers is computed on the prefix. A card that uses a prefix says which sources it covers and how many of its rows are valid replies (G12's prefix covers every chat text in roster order, and about nine tenths of its rows are valid). This replaces the practice that a stopped job is closed |
| DV | A pause is a wait | The workstation's reader arm gains resume code: a job restarts at its first unfinished row and keeps its finished rows by hash. Restarted jobs are registered as G12r, G14r and G13r. At the floor the arm waits: it checks free commit once a minute and goes on when free commit exceeds 8 GiB plus the reader's resident size. Each pause and resume is a line in the queue's record with two numbers: the commit held by this program's own processes and by Sounding Line's slots, and the commit held by everything else. No other process is named. A job that has waited two hours is the return's first line, which gives the share of commit held outside this program and Sounding Line as the blocker. The floor itself does not change |
| DW | Today's queue (the curator's approval is in the message that delivers this packet) | Section 3's jobs run. One GPU job at a time on each machine, as now. Each job times its first 100 texts and writes its projected hours beside this sheet's figure. Amendment CV's memory rule for reader C applies to Q36's C arm, and card TP80's CPU job does not run on the Spark while C is loaded. The handoff that gives the GPU to the filler when Q31 exits is held by writing the filler's `YIELD` file, which that handoff checks. The cutoff is yesterday's |
| DX | The need mark | Section 3's prompt is written once, hashed and filed before Q35. Amendment CW applies to it. Until W has marked the same texts (G16), agreement between B and C on Q36's sample stands in for agreement between B and W: at kappa 0.60 or more the mark is usable, from 0.40 to 0.60 a result that rests on it is a description, under 0.40 it is not used |
| DY | Every card has a report | A card lands with a report in ruling R48's seven parts, with a line that begins "Limit:". Card TP89 writes the missing reports for TP61 to TP79 |
| DZ | A second build | Each card that carries a verdict is built twice. The second script is written from this card's text alone and shares no code with the first beyond reading the saved inputs. The card lands when every number agrees to 0.001 and every verdict word agrees. A disagreement is the return's first line, and the card waits until it is explained |

## 3. The queue

| Job | Where, reader | What | Texts | Hours | Feeds |
|---|---|---|---|---|---|
| Q35 | Spark, B | The need mark | 24,850 chat texts; 6,600 recalled events | 5.8 | TP82, TP84, TP88 |
| Q36 | Spark, C then B | C's need mark on 1,500 of Q35's texts (1,000 chat and 500 events, drawn by seed). B's on 1,000 of them under two further wordings | 3,500 | 1.0 | TP88, amendment DX |
| Q24b | Spark, as registered | The filler, behind Q35 and Q36 | | to the cutoff | TP73 |
| G12r | Workstation, W | The rest of the standing marks | 15,821 | 2.9 | TP74, TP77 |
| G16 | Workstation, W | The need mark on all of Q35's texts | 31,450 | 6.8 | TP88, amendment DX |
| G14r | Workstation, W | The rest of the features on recalled events | 5,672 | 1.9 | TP77 |
| G13r | Workstation, W | The rest of the sentence marks (forum comments, then blog sentences) | 93,247 | 12.9 | TP65, TP77 |
| G15 | Workstation, W | The filler, as registered, behind the others | | to the cutoff | TP73 |

**Order.** Spark: Q31 finishes, then Q35, Q36, Q24b. If Q31 is still running when this packet arrives, the filler's `YIELD` file is written before it exits. If the filler has already started, it is parked again as it was parked behind yesterday's queue (the `priority.pending` file), its finished rows are kept, and Q35 starts. Workstation: G12r, G16, G14r, G13r, G15. Q30 and Q33 start when the Spark can read their sets, ahead of the filler.

**The need-mark prompt.** It shows the text and nothing else, and asks two questions with fixed answer words, as structured output.
1. Which of the writer's needs is most at stake in this text? One of: `competence` (skill, learning, getting something done), `respect` (standing, approval, rank, how others judge her), `belonging` (family, friends, love, being included or left out), `meaning` (purpose, order, beliefs, what her life adds up to), `body` (health, safety, food, rest, physical comfort), `romance` (wanting or having a partner), `money` (money or things she owns), `none` (no need is clearly at stake).
2. For that need, what does the text report? One of: `loss` (it fell, or was threatened), `gain` (it rose, or she hopes it will), `neither`.

A reply is invalid if the first answer is `none` and the second is not `neither`. No prompt shows the assigned feeling word. The two further wordings for Q36 are written at the same time.

## 4. Cards

Every card: a report in R48's seven parts with a "Limit:" line (amendment DY), a second build (DZ), and its guesses entered in card TP78's table (CX). "Clears zero" means the 95% interval from 2,000 whole-writer draws excludes zero. A reading of a person goes against the rotated band (CU).

### TP80. What stays with a writer once topic is held (the handoff's E1)

- **Data.** TP61's 2,527 blog authors and TP52's date halves. The Q20 opening vectors, which are on the Spark.
- **The statistic.** TP61's: for each tag, the correlation across authors between her mean linear score in the two date halves; then the median over the nineteen tags. The record has 0.498 for the trained tags against a rotated band of 0.416 to 0.487.
- **Topic.** Lloyd's k-means on the opening vectors of the whole roster (372,842 openings), at most 12 passes, as the made world ran it, from K openings drawn by the seed rule (text `TP80:kmeans:<K>:<fold>`), for K = 30, 100 and 300. Authors are split into two folds by the parity of the first byte of SHA-256 of `TP80:fold:` and the author's id. Centres are fitted on one fold's openings and used to place the other fold's. From each opening's vector, take away the mean vector of the other fold's openings in its cluster. So an author's own posts never enter what is taken from her.
- **Job on the Spark's CPU, one numerical thread, as TP61's vector return ran.** For each K it returns the topic-held mean vectors for every roster author (both date halves for the 5,409 who have both, and all posts for the 5,426), the cluster sizes, and the planted survivor's author means. The statistic is then computed on TP61's 2,527. It also returns, for each tag, the mean and the standard deviation of its topic-held linear score over openings, which TP61's part (a) needs for its scale. It returns no opening and no text.
- **The planted survivor.** A unit direction inside the span of the nineteen tag heads (seed text `TP80:plant:0`). Each author gets one constant along it, with a spread equal to the noise of a half mean along that direction. It is added to every one of her openings and the clusters are fitted again with it in; the study's own clusters are fitted without it. The survivor's slope is the slope, across authors, of her topic-held mean along the direction on her constant. A slope of 1 means the constant came through whole.
- **Registered.** K = 100 carries the verdict, and K = 30 and K = 300 are filed beside it. The verdict is read only if the survivor's slope at K = 100 is 0.90 or more. Under that, the step is taking the author with the topic, and the card says so and gives no verdict.
- **Guesses.** The results thread's: with topic held, the trained tags' median repeat falls into the rotated band (computed on the same topic-held vectors). Rival: it stays above the band.
- **How it is read.** Inside or below the band at K = 100: what stayed with her in TP61 was what she keeps writing about, as far as clusters shared with other authors can hold it. Above the band: something beyond shared topics stays with her. Either way the card files how much of the raw lead is left: the trained median minus the band's middle, with topic held, over the same difference without.
- **Also filed, as a description.** TP61's part (a), by its own script and rules, on the topic-held means at K = 100: how often a writer's highest map group is the same in both date halves, over random dealing, against its rotated band. No made world tried this statistic under the topic step.
- **Pre-flight.** In made authors where the trained tags led only because thirty shared topics lie along them, holding topic with 10 clusters left the lead in 9 of 10 runs, with 30 clusters in 3, with 100 in 1 and with 300 in 1. Where the lead was the author's own it stayed in 10 of 10 runs at every K, and where only style was planted a lead was called in 0 to 1. At K = 100 the planted survivor's slope ran from 0.89 to 0.97 across the 8 made worlds, and in 2 of them, both with 600 topics, it fell just under the card's line of 0.90, where the card would have given no verdict. Where each topic belonged to two or three authors the step could not hold it, and the lead stayed in 10 of 10 runs. Where the lead was the author's own and topics were near-private as well, the raw lead itself showed in only 2 of 10 runs and the held one in 2 to 5, so the card cannot see an own lead in such a corpus. Ten runs a world, which is few (`pf_topic.py`).
- **Limit sentence.** A topic here is a cluster of the same vectors the tags read, shared with other authors. A topic that only she writes about cannot be told from her, and the planted check bounds the step only for a constant. The made world had thirty shared topics; with another number a different K may be right, which is why two more are filed. These are blog posts, and no outside score is in the study.
- **Prior art.** Topic masking improves authorship attribution most across topics (Stamatatos 2017). No published share of an author's stability put down to topic was found, so the card is not called new and has no published figure to match.
- **What changes in the engine.** The person row's label: hers, or what she keeps writing about (card TP91's table).

### TP81. How much of the trait null is noise (E2)

- **Data.** TP63's: 6,600 recalled events by 2,379 writers, its 29 outputs with the assigned feeling's mean taken away, and the ten trait items.
- **Quantities.** For each output: the reliability of a writer's mean, with a whole-writer interval. It is built from the reliability of one report (the intraclass correlation from a one-way analysis of variance by writer over all reports, floored at zero) and each writer's own number of reports: ICC over ICC plus (1 minus ICC) times the mean of one over her number of reports; beside it a split-half figure for writers with two or more reports (50 random splits, stepped up by Spearman-Brown). For each trait: the correlation of its two items after reflection, stepped up for two items; beside it the inventory's published six-week retest figures (0.62 to 0.77, mean 0.72; Gosling and others 2003). For each of the 145 cells: the ceiling under each trait figure; the bound, which is the upper end of TP63's interval (in absolute value) divided by the ceiling and capped at 1; and the number of reports a writer that would lift the ceiling to 0.30.
- **Against rotated heads.** The reliability of a writer's mean for 200 rotated sets of TP63's 28 heads. It says whether writers differ more along the trained directions than along arbitrary ones.
- **Guesses.** The results thread's: for most cells (73 or more of 145) the ceiling is under 0.2, under the item-agreement figure. Rival: fewer than 73.
- **How it is read.** A cell's null stands if its bound is under 0.30, and says little otherwise. The count of each is filed under both trait figures. The plain analysis-of-variance figure (1 minus the within-writer mean square over the between-writer mean square) is filed beside the registered one and not read, because it overstated the ceiling in the made world.
- **Pre-flight.** In made writers with the record's count, where a writer's share of the variance of one report was 0.10 and a trait's two items correlated 0.25, the true ceiling was 0.268 with about 2.8 reports a writer and 0.235 when over half the writers had one report. The plain analysis-of-variance figure gave 0.302 and 0.292, and across the grid its bound covered the planted correlation in as few as 52 of 200 runs. The registered form gave 0.265 and 0.234, and its bound covered the planted correlation in 180 to 199 of 200 runs wherever writers differed at all. Near the line the call is a coin toss: at a true ceiling of 0.19 a cell was called under 0.2 in 103 to 117 of 200 runs. With a planted correlation of 0.3 the observed one passed the bar of 0.088 in 18 of 200 runs at a share of 0.05 and in 56 at 0.10 (4 and 40 when over half the writers had one report), so a null there says little. The reports a writer needed for a ceiling of 0.30 came out at 15, 6, 3 and 2 for shares of 0.02, 0.05, 0.10 and 0.20 (`pf_ceiling.py`).
- **Limit sentence.** Reliability here is agreement across a writer's few reports, each written to an assigned feeling, and a writer with one report adds nothing to it. The inventory has two items a trait.
- **Prior art.** The attenuation formula is Spearman's. In a meta-analysis of 85,724 people the strongest links between word counts and self-reported traits were 0.08 to 0.14 (Koutsoumpis and others 2022), so a small ceiling would be no surprise.
- **What changes in the engine.** Whether the person row needs more events a person, or a different outside score, before a trait can check it. The figure is also the yardstick for Sounding Line's sealed trait job, which has hundreds of comments an author.

### TP82. Each channel's key, by need (E3)

- **Data.** Chat (24,850 texts, 810 writers), recalled events (6,600; the head set there leaves SHAME constant, so SHAME is read on chat and blogs), blog openings (the roster's 372,842, by the saved Q20 scores, for kind (c) alone). Ten channel outputs, the map's groups, and, when Q35 lands, the reader's need mark.
- **Cells.** Three kinds, each inside an assigned word (chat, events) or inside an author (blogs, kind (c)), with intervals from 2,000 whole-writer draws. (a) Mark cells, which carry the verdicts: the channel's reading with the tag directions taken out, in texts the reader marked with a need, minus the same in the rest, in standard deviations. On chat they are also computed inside a writer. (b) Tag cells with the tag directions taken out of the channel, against the rotated band, with the span found again for each rotation. (c) Plain tag cells: the correlation of the channel's output with a group's score. Kinds (b) and (c) are descriptions. The savings row uses tags alone: the savings tag's correlation with the Respect group's score, minus its correlation with the mean of order and serenity, with its own interval and the same contrast's rotated band beside it.
- **Registered contrasts**, each a direction with zero beside it.
  - His: SEEKING's highest need is Competence ("It is exclusively focused on competence."). The word "exclusively" is not scored: a mark cell is a contrast with the rest, so one raised need lowers the others.
  - His against the thread's, one contrast: PRIDE's cell with Competence minus its cell with Respect. His is positive ("Lust cares about status, and pride cares about competence."). The thread's is negative.
  - His against the thread's: SADNESS's cell with Belonging minus the mean of its other cells. The thread's is positive. His is zero ("But sadness cares about drops in anything."), which has no margin here: he loses if the contrast clears zero, and otherwise his line stands unshown.
  - His: the savings tag travels with the Respect tags more than with order and serenity ("I think savings is part of status."). Savings is left out of Meaning for this row. Tags carry no verdict, so this is a description.
  - The thread's: for FEAR, DISGUST and SHAME the highest need is Body. For RAGE the thread named two tags, power and order. Tags carry no verdict here, so that line is filed as a description from kind (b).
  - The LUST output is filed as a description. It reads wanting, so it cannot answer his line on status, which enters TP78's table as not scored.
- **How it is read.** Verdicts come from the mark cells alone, and only if the need mark passes amendment DX's kappa rule; from 0.40 to 0.60 they are descriptions. A channel keys on a need when its mark cell for that need is positive and clears zero under amendment CX's false discovery rule over the card's seventy cells (ten channels by seven needs). That cell is the form the pre-flight tried, three cells a world and not seventy, and one unkeyed cell was still called in up to 6 of 40 made runs, which is more than the rule assumes. So a lone keyed cell is weak evidence, and the card says so wherever one stands alone. Its highest need is the largest such cell. A contrast between two needs is the difference of the two cells with its own interval; the made world tried cells and not contrasts. SADNESS's contrast is taken on texts marked as a loss. Until Q35 lands the card files kinds (b) and (c) and the savings row, and waits.
- **Pre-flight.** In made texts with no key at all, where every head shares a general direction, the plain tag cells named a highest group with a clear gap in 26 to 35 of 40 runs and put a named cell above its rotated band in 28 to 37. A reader's mark did not escape while the channel's plain output was used: at 0.6 and 0.8 accuracy it called a key in an unkeyed cell in 9 to 28 of 40 runs, and where one head merely leaned toward a tag group with no shared content it called that cell in 40. With the tag directions taken out of the channel's reading, the mark cells called an unkeyed cell in 0 to 6 of 40 runs and the leaning cell in 1 to 5, and still found a planted key in 40. The same step on tag cells was safe (0 to 3 of 40) and weak: it found a planted key in 8 to 39 (`pf_keys.py`).
- **Limit sentence.** Both sides of every cell are readings of one text. A tag cell shows how two trained readings travel together, and trained heads can travel together with no shared content. A mark cell rests on one reader's judgment. Neither is a measurement of a need.
- **Prior art.** Appraisal theories key feelings to how a goal stands and who caused it, not to which goal it is (Roseman and others 1990). In 141 couples, autonomy frustration went with anger and relatedness frustration with sadness and hurt (Pirrone and others 2023). No tested map from feelings to need content was found; the card is not called new.
- **What changes in the engine.** A keys-on column for each channel row (TP91's table).

### TP83. PRIDE by her own doing, crossed with standing (E4)

- **Data.** The 6,600 recalled events. The PRIDE output with the assigned feeling's mean taken away. Her own rating of "The event was caused by my own behavior." (`self_responsblt`, 1 to 5). Standing two ways: the mean of the standing tags (status, approval, competition, honor, acceptance, power), and reader B's standing mark from Q27 (rose, against fell or neither). A second arm on chat, with B's `self_responsblt` from Q6 in place of her own rating.
- **Quantities.** The PRIDE reading with the tag directions taken out, with the assigned feeling's mean taken away, fitted on her own doing (standardized), standing and their product, with a term for each assigned feeling. Intervals from 2,000 whole-writer draws. Filed four ways: with B's standing mark; the same without the 1,199 reports the PRIDE head was fitted on; inside the four good-event feelings (pride, joy, relief, trust); and as four cell means (own doing 4 or 5 against 1 or 2, by standing rose or not). The plain PRIDE output with the standing tags is filed as a description.
- **Guesses.** His: her own doing raises PRIDE and standing alone does not ("Like you pride yourself on your decisions. You don't pride yourself on anything else."). The results thread's: standing raises it and her own doing adds nothing, as TP67 found. Print's: both.
- **How it is read.** By the own-doing term on the events arm without the 1,199 fitted reports. Clear and positive: his first clause holds. Wholly inside plus or minus 0.05: the thread's holds, since the made world found an effect of that size. Otherwise undecided. The standing term rests on a mark whose agreement between two readers was 0.57 yesterday, so by amendment CW it is a description until the rest of the standing marks say otherwise. If both terms are clear, print's reading is filed with that caution.
- **Pre-flight.** In made events where the assigned feelings differ in own doing, in standing and in PRIDE and nothing else links the three, a fit without a term for each feeling called own doing in 120 of 120 runs. With those terms it did so in 1 to 10. A noise shared between the PRIDE output and the standing tags (0.3), which two heads on one vector can have, was enough for the fit to call standing in 120 of 120 runs where standing did nothing. A band of made standing scores with the same shared noise stopped that, kept a standing effect of 0.15 in 120 of 120 runs and lost one of 0.05 (0). Rotated heads do not keep a head's angle to PRIDE, so that band has no counterpart on the real heads: the tag form of standing is a description, and the card takes the tag directions out of the PRIDE reading, the step the made worlds for cards TP82 and TP84 tried and this one did not. Own doing at 0.15 was found in 120 of 120 runs. At 0.05 it was found in 118 with all reports, 114 to 115 without the fitted ones, 66 to 75 inside the four good-event feelings and 62 to 65 from cell means (`pf_doing.py`).
- **Limit sentence.** Her rating is of the whole event, the output reads her text, and she was given the feeling to write about. Whether standing rose is one reader's judgment of a short text.
- **Prior art.** Pride is tied to an internal cause (Weiner 1985, not opened for this sheet), yet pride in what others did was as strong as pride in one's own doing where responsibility was low (De Hooge and Van Osch 2021). No study that crossed own responsibility with a rise in standing was found.
- **What changes in the engine.** PRIDE's row label: her doing, or a rise in standing whoever's.

### TP84. SADNESS by which need the loss touched (E5)

- **Data.** Loss texts by assigned word, with the words TP66 used: recalled events given sadness (550), and chat texts given sad, devastated, lonely or disappointed (3,153). TP66 itself used the 216 and 1,700 of them that have two or more sentences. The handoff asked for texts with a landed loss by the reader's marks; that roster joins when Q35 lands: texts where reader B's sentence marks hold a change that has already happened and the need mark's second answer is `loss`. Outcomes: the SADNESS reading with the tag directions taken out, inside a word; and, on events, her own rating of how intense the feeling was, if the event file holds one. If none binds, that arm is void and the card says so.
- **Leading group.** Two ways. By the reader's need mark (Q35), using texts marked as a loss. By the tags: the map group with the highest score, with a text set aside as mixed when its top two groups differ by less than 0.25.
- **Quantities.** For each group: the mean outcome in texts it leads minus the mean in the rest, in standard deviations, inside a word.
- **Guesses.** His: no difference between groups. The results thread's: highest where Belonging leads.
- **How it is read.** On chat, with the reader's mark if it passes amendment DX's rule and with the tags otherwise. A lead for Belonging is called if its difference from the rest clears zero and is the largest; a lead takes precedence. If no group's difference clears zero and every interval lies inside plus or minus 0.20, the card says so as a description and not as a verdict for his line, because the made world also showed that pattern where a lead was planted. Anything else is undecided. On events both outcomes are filed with their intervals and no verdict, because 550 texts are too few. The plain SADNESS output is filed as a description.
- **Pre-flight.** In made loss texts where sadness did not depend on the need and the SADNESS head leaned toward the Belonging tags (a cosine of 0.2), the plain output called a Belonging lead in 165 of 200 runs at chat's size and 151 at the events' size, and the rotated band cut that only to 33 and 17. With the tag directions taken out of the SADNESS reading it was 6 to 7 and 5 to 7 of 200, and her own rating gave 4 to 9. A true lead of 0.30 standard deviations was then found in 166 to 168 of 200 runs at chat's size, in 48 to 52 at the events' size from the reading and in 51 to 55 from her rating; a lead of 0.15 was found in 72 to 83 at chat's size. Every group within 0.20 was seen in 160 to 163 of 200 runs at chat's size where there was no lead, but also in 39 to 40 where a lead of 0.30 was planted and in 111 to 115 where one of 0.15 was, so that pattern is a description. At the events' size it was seen in 0 runs of any world. The made texts each had a writer of their own; chat's loss texts come from far fewer writers than texts, so real intervals will be wider than these (`pf_lossneed.py`).
- **Limit sentence.** Texts about losing someone are the pattern the SADNESS output was taught on, so a higher output there can be closeness to that pattern. Her own rating is free of that, and it is one number an event.
- **Prior art.** Loss and failure did not differ in rated sadness in a small study, though they differed in tears and anger (Shirai and Suzuki 2017). In 4,856 twins, deaths and breakups gave more sadness and failures more fatigue (a 2007 paper in the American Journal of Psychiatry, doi 10.1176/appi.ajp.2007.06091564; abstract only).
- **What changes in the engine.** SADNESS's key on the display: any need, or Belonging first.

### TP85. The order inside a loss, with RAGE and SEEKING (E6)

- **Data.** TP66's loss texts and its other texts, with two or more sentences: 216 events and 1,700 chat texts. They are short: of the chat loss texts 1,361 have two sentences, 286 three and 53 four or more; of the events', 130, 35 and 51. The saved outputs by sentence. TP66's long arms join as they land: blog windows when Q31 exits, and the long recalled stories if Q30 runs.
- **Already saved.** TP66's sheet has both pairs that end in SADNESS. FEAR before SADNESS: 0.268 [0.184, 0.352] on events and minus 0.014 [minus 0.058, 0.032] on chat. RAGE before SADNESS: 0.247 [0.159, 0.336] on events and minus 0.034 [minus 0.081, 0.013] on chat. Its saved table (`engine/validation/readers-tp66-short-2026-11.json`) also has each of the three channels' own centre, in loss texts minus other texts. On events: FEAR minus 0.033 [minus 0.079, 0.016], RAGE minus 0.012 [minus 0.072, 0.045], SADNESS 0.235 [0.171, 0.298]. On chat: FEAR 0.028 [minus 0.001, 0.060], RAGE 0.048 [0.016, 0.084], SADNESS 0.014 [minus 0.035, 0.062].
- **What the saved figures already say.** On events both pairs are "SADNESS is late": SADNESS comes later in a loss, and neither FEAR nor RAGE comes earlier. By this card's rule that meets the Theory and Research thread's guess and the results thread's in the weak reading only. On chat neither pair is clear, and RAGE's own centre is later, not earlier. These are not scored again as new tests. What is new here is SEEKING: its pairs, its own centre, and the chain.
- **Quantities.** TP66's form for each pair of SEEKING, RAGE, FEAR and SADNESS: the second output's centre minus the first's, in loss texts, minus the same in other texts with the same number of sentences. Positive means the first comes earlier. Beside the pairs, each channel's own centre in loss texts minus its centre in other texts of the same length.
- **Guesses.** His, from Klinger: "Faster seeking followed by aggression, followed by depression, followed by recovery." So SEEKING before RAGE, and RAGE before SADNESS. The Theory and Research thread's: RAGE before SADNESS. The results thread's: FEAR and RAGE before SADNESS, SEEKING not placed.
- **How it is read.** On all loss texts of two or more sentences, as TP66 was. A link "A before B" is met in full when its pair clears zero and A's own centre is earlier in loss texts than in other texts. If the pair clears zero and only B's own centre has moved, the link is filed as "B is late", which meets a guess in its weak reading only. His chain needs both of its links in full. A pair that clears zero the other way is against.
- **Pre-flight.** The made texts ran from two to eight sentences, so only the rows for two or three sentences speak for chat and events as they are. With nothing planted, no verdict was called in more than 8 of 100 runs. On texts of two or three sentences, with 216 loss texts, a pair statistic of 0.43 was called in 100 of 100 runs, and a chain with links of 0.21 and 0.21 in 89. TP66's figure for FEAR before SADNESS on events, 0.27, lies between those sizes. Small orders were not seen in such texts: with a pair statistic of 0.03 on longer texts, or of 0.01, each of the three verdicts was called in only 0 to 17 of 100 runs, and a wrong direction in up to 12. Where only RAGE was planted early and SADNESS late, and FEAR had no place of its own, the results thread's pair was still called in 85 to 100 of 100 runs when the planted order was large, and in 1 to 70 when it was small. That is why a link is scored in full only when the first channel's own centre has moved, a guard the made world did not itself run (`pf_order4.py`).
- **Limit sentence.** Position in a short written report follows how stories are told, and the report opens with the feeling she was given. Klinger's order is over weeks and months.
- **Prior art.** In 233 bereaved people, yearning peaked at four months, anger at five and depressed mood at six (Maciejewski and others 2007). Across about 40,000 narratives, words that set the scene fall and words of mental effort peak late (Boyd and others 2020). So an order inside a text can come from telling.
- **What changes in the engine.** A time order across four channel rows.

### TP86. Surprise as a jump with no channel (E7)

- **Data.** Chat: 1,279 texts given the word surprised among 24,850, the ten outputs, and reader B's suddenness rating (Q6, every text). Recalled events (the analyst's arm): 550 given surprise among 6,600, the outputs, her own suddenness rating, and B's (Q28).
- **Quantities.** (a) The ten standardized differences between surprised texts and the rest, as a profile. (b) The SEEKING output in surprised texts minus the same in the texts of the word whose mean profile on the other nine outputs is nearest, in standard deviations; the same against the three nearest words, and against the rest. (c) TP66's form for SEEKING's place: its centre in surprised texts minus its centre in other texts with the same number of sentences. (d) Two areas under the curve for telling surprised texts from the rest: from the suddenness rating alone, and from the ten outputs by a logistic fit scored on held-out fifths. (e) On events, (a) to (d) with her own suddenness rating, and the correlation between B's suddenness rating and hers.
- **Guesses.** His: none ("we're going to probably need neurological data for that one"). The results thread's: suddenness alone tells surprised texts apart better than the ten outputs do, and SEEKING comes late in them. Print's: surprise travels with curiosity, so the SEEKING output is raised in surprised texts.
- **How it is read.** Print's claim holds if (b) is clear and positive against the nearest word. Against the rest alone it is a description, since most texts given this word are pleasant and the SEEKING head was taught on excitement. The made world tried the difference against the rest; the form against the nearest word is a plain difference between two words' texts, as card TP69 used, and was not tried there. The thread's second guess holds if (c) is clear and positive. Its first guess, (d), is filed as a description: in the made world the rating beat the outputs whenever the reader read suddenness well, with or without an output for surprise, and lost with a poor reader where there was none. So this card cannot show that surprise has no channel. It can show whether SEEKING comes with it, and where.
- **Pre-flight.** In made chat where surprised texts have no output of their own (flat on every output, half joy and half fear, or mostly joy), the ten outputs still told them from the rest at an area under the curve of 0.62 to 0.69, by what such texts are not. Where a SEEKING lift of 0.8 was planted the area was 0.70 to 0.71, too close to tell the two apart. When the rating tracked true suddenness at 0.8 it beat the outputs in 30 of 30 runs in every world, with or without an output for surprise. When it tracked it at 0.5 it won in 30, 11, 2 and 0 of 30 in the four worlds (flat on every output; half joy and half fear; mostly joy; a SEEKING lift). So a win shows a good reader, and a loss does not show a channel, since the mostly-joy world has none. The standardized difference of the SEEKING output against the rest was the one quantity that told the worlds apart: clear in 0 of 30 runs with no lift and in 30 with it. The call that surprised texts are flat on all ten outputs was made in only 9 to 11 of 30 runs where they were flat by construction (`pf_surprise.py`).
- **Limit sentence.** The reader rates suddenness from the same words the outputs read. Chat texts given this word are mostly pleasant, and no output was taught on a surprise label.
- **Prior art.** In the chat corpus's own paper the example for surprised is a lottery win (Rashkin and others 2019). Surprise is at first mildly unpleasant (Noordewier and Breugelmans 2013) and predicts exploring (Vogl and others 2020, abstract only).
- **What changes in the engine.** Surprise shown as a feature of the event, not as an output.

### TP87. Name the author-level groups (E8)

- **Data.** The blog author means TP70 used (5,426 authors), and the topic-held author means from TP80 at its registered K.
- **Asks.**
  1. Components. The number above the rotated floor, as TP70 counted it. Varimax on that many, and on one more and one fewer. For each component, its tags with loadings of 0.40 or more. Authors are split in two by the parity of a hash; a component is kept for naming only if its match across the halves (Tucker's congruence) is 0.85 or more.
  2. Named groupings, each with TP70's statistic against the rotated band: the map's, print's four, the thread's three, and the tag source's own five if its documentation is at hand. Only the comparison between groupings is read, since a partly wrong grouping also lies above its band.
  3. The ten channel outputs. Each output's author mean against each kept component and each map group; the group it falls with is the largest, with the share of 2,000 whole-author draws that agree.
  4. All of it again on the topic-held means.
- **Guesses.** His is a method: "whether we can allow the groupings to arise organically and then label them after". The results thread registers no grouping. The analyst's: the map's margin over the rotated band stays above zero with topic held. Rival: it falls to the band.
- **How it is read.** Asks 1 and 3 are descriptions. Ask 2 is read as TP70 was. Ask 4 decides the analyst's guess.
- **Pre-flight.** The statistic and the varimax reading were tried yesterday (`pf_groups2.py` in `PREFLIGHT_2026-11-27.zip`); nothing new is registered here except the topic step, which is TP80's.
- **Limit sentence.** Groups of tags across authors can be groups of topics, and rotation and the number of components shape them. The names are labels put on after.
- **Prior art.** People's sorts of 161 motives gave three groups at the top: meaning, communion and agency (Talevich and others 2017). Those come from likeness of meaning, not from travelling together inside people.
- **What changes in the engine.** The need rows on the person display.

### TP88. The tags against a reader's need mark (the analyst's; after Q35 and Q36)

- **Data.** Chat and recalled events with a valid need mark.
- **Asks.** For each need the reader named in 200 texts or more: how well each map group's score tells those texts from the rest inside a word (the area under the curve), against the rotated band; and which group tells them best. The savings tag and the romance tag are scored against `money` and `romance`.
- **Guess (the analyst's).** For Belonging, Respect and Body, the map's own group tells the reader's texts best and lies above its band. No guess for Competence, which has one tag, or for Meaning.
- **How it is read.** By amendment DX's kappa rule. A group that does not tell its own need's texts above the band is flagged on the display until a need score from people can check it. The map's Compassion group has no answer word in the mark, so it is not scored here.
- **Limit sentence.** The yardstick is one reader's judgment of a short text. It is not a score from the writer.
- **Prior art.** No search was made; the card is not called new.
- **What changes in the engine.** Which need rows the display can show without a flag.

### TP89. The record (the analyst's; amendment DY)

- A report in R48's seven parts, with its "Limit:" line from the evidence ledger's `limit` field, for each of TP61 to TP79. TP70's sheet gains its limit.
- TP65's sheet gains the table already saved: on chat, six outputs read lower on change sentences than on neither (CARE, DISGUST, FEAR, LUST, PLAY, SEEKING) and RAGE higher.
- TP78's table: TP64's first row and its analyst row, TP65's first, TP70's second and its analyst row are crossed as missed. TP61's first stays crossed: part (b) fell below its band, seven of 7,600 null heads reached worry's slope where the guess said none would, and part (a) now lies above its band where the guess said a tie.
- The return's line on G15 is reworded: 28,846 calls were planned, fewer than 100 ran, and the job stopped at the memory floor.

### TP90. Whether the channels are hers (the analyst's)

- **Already saved.** How much text a person row needs was this card's first part. TP61's dated profiles, landed this morning, answer it: the tags' mean repeat is 0.32 at 5 openings a half, 0.46 at 10, 0.60 at 20 and 0.72 at 40, each above its rotated band by 0.01 to 0.02. They are cited and not rebuilt.
- **Data.** On the workstation: the roster's author mean vectors for the whole date halves.
- **Ask.** The ten channel outputs' repeat across the date halves, each and their median, against 1,000 joint rotations of the ten channel heads.
- **Guess (the analyst's).** The channels' median repeat lies above its rotated band. Rival: inside it.
- **Limit sentence.** A repeat across two halves of one blog shows that something stays with the author. It does not say what.
- **Prior art.** No search was made; the card is not called new.
- **What changes in the engine.** Whether the person row carries channel rows. The tags already repeat above their band at five openings a half, by a small margin.

### TP91. What each verdict would change on the display (the analyst's)

A table, filed with the return when TP80 to TP88 have landed: for each verdict, the label or row it would change. Nothing is switched on. The results and alignment thread reads it first, as section 8 of yesterday's packet has it.

### Yesterday's cards that close today

- **TP67's three-way split, TP74, and TP77's standing check** run on G12's prefix panel (amendment DU), which covers chat. Each says so. They run again on events and forum comments when G12r finishes.
- **TP75, and the blog arms of TP65 and TP66,** when Q31 exits.
- **TP73's open parts,** as registered.
- **TP76 and TP79** wait on section 5.

## 5. Opens when (counted as zero hours)

| What | Waits on | Owner |
|---|---|---|
| Q30 and TP76 (the long recalled stories); Q33 and TP79 (the talk pages) | a copy of each set that the Spark's agent account can read | the data collection thread |
| The first check of a need reading against a need score from people | a set with need scores beside text. The data collection thread has one in progress (osf.io/uxneu) and added another on 28 November (osf.io/bwr2a) | the data collection thread |
| A Meaning reader | the Theory and Research thread's open item on whether Meaning needs one, and a meaning score beside text | that thread; the data collection thread |
| Display labels for the body tags | the Theory and Research thread's open item on where the body goes | that thread |
| Any change on the display | the results and alignment thread's reading of TP91's table | that thread |

## 6. Order, the standing rule, and what to drop

1. At once: hold the Spark's GPU for Q35. If Q31 is still running, write the filler's `YIELD` file so the armed handoff does not give the GPU to Q24b when Q31 exits; if the filler has already started, park it as section 3 says. Then amendments DU and DV, and G12r on the workstation. Q35's prompt is written, hashed and filed, and Q35 starts as soon as the GPU is free.
2. Cards on saved outputs, in this order: TP89, TP81, TP83, TP85, TP86, TP80 (its Spark job first), TP87, TP90, TP82 (kinds (b) and (c)), TP84 (tag form).
3. Yesterday's cards on the prefix panel: TP67's three-way split, TP74, TP77's standing check.
4. When Q35 and Q36 land: TP88, then the mark arms of TP82 and TP84.
5. TP91 last. TP78 at each push.

**Standing rule.** A card whose inputs are saved starts when the agent is free. A GPU that is idle beside a job whose inputs are ready is a fault, written in the return's first line; a GPU waiting at the memory floor is not a fault, and the line says how long it has waited. Nothing here waits on a question to the curator. Where the sheet leaves a choice open, take the reading that claims less and write the choice in the card.

**If time runs short, drop in this order:** G13r; TP87's ask 4; TP86's events arm; Q36's two further wordings.

## 7. Guesses before data

The analyst's, entered in TP78's table with the others. Each is a direction with its rival. TP88's and TP90's have no made world behind them, so they sit outside the table's false discovery family.

| Card | Guess | Rival |
|---|---|---|
| TP80 | The trained tags stay above the rotated band with topic held, and the lead shrinks by more than half | They fall into the band |
| TP81 | More than 100 of 145 ceilings are under 0.2 | 100 or fewer |
| TP82 | On the mark arm, PRIDE's cell with Respect is above its cell with Competence | The reverse, or no difference |
| TP83 | On the events arm without the fitted reports, own doing clears zero and is positive | Inside plus or minus 0.05, or undecided |
| TP84 | On chat, no group's lead clears zero | Belonging leads |
| TP85 | SEEKING's own centre is not earlier in loss texts than in other texts, so the chain's first link is not met in full | It is earlier |
| TP86 | Against its nearest word, SEEKING is not raised in surprised texts | It is raised |
| TP87 | The map's margin stays above zero with topic held | It falls to the band |
| TP88 | The map's own group tells the reader's texts best for Belonging, Respect and Body | It fails for one of them |
| TP90 | The channels' median repeat lies above its band | Inside it |

## 8. The return

`docs/exchange/THEORY_RETURN_2026-11-29.md`, pushed at each landed card and at least every six hours.

1. The first line: whether either GPU or the card queue is idle or waiting, and why.
2. "Against, and clear."
3. TP78's table.
4. One line a card, with its report's path. Each report has R48's seven parts.
5. The queue: each job's first-100 timing, its projected and its real hours, and each pause at the memory floor with its two commit figures.
6. For each mark: kappa between B and C, and between B and W when G16 lands.
7. TP91's table.

## 9. Limits of this sheet

- Every card but TP81, TP83's events arm, TP84's rating arm (if the event file holds her rating) and TP86's events arm compares one reading of a text with another reading of the same text. Those four have something the writer herself said beside the reading.
- A reader's mark is the weakest link. Yesterday's standing mark reached kappa 0.57 between B and C, which makes it a description by amendment CW. The need mark may do no better.
- The workstation's hours assume the memory floor lets its jobs run.
- A tie with rotated heads does not show that a need is absent. It shows that this check cannot see one.
- Nothing here reads a demographic column, and no analysis by sex is made.
