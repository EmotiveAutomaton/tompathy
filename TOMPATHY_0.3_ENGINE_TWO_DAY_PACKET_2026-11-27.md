# ToMpathy engine 0.3: two days of rapid studies (Round 37)

*For the engine's agent. Saved at the repository's root as `TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-27.md`. It implements lane E of the Round 37 handoff (saved as `docs/exchange/THEORY_HANDOFF_R37.md`) and adds a queue for both GPUs at the curator's word. Made worlds for every new operator are in `PREFLIGHT_2026-11-27.zip`, beside the earlier bundles. This sheet carries no questions. Every choice in it is made here, and the curator's approvals are in the message that delivers it.*

## 0. Read first

- **What this is.** Ten studies on outputs already saved (cards TP61 to TP70, the handoff's E1 to E10), nine cards the analyst adds (TP71 to TP79), a queue of nine jobs for the Spark's GPU (Q26 to Q34) and four for the workstation's (G12 to G15). The handoff asked for no GPU. The curator then asked that both machines be kept busy, so the queue is the analyst's, built only from marks that feed a card.
- **The aim.** The curator, on 27 November: "your central main goal is to push the engine forward." Each card ends with the change it makes to the engine.
- **What changed from the handoff, and why.** Each is the analyst's, from the pre-flight or from the literature read for this sheet.
  - A random-heads row is a band from many null sets, not one set of nineteen, and the verdict is read against rotated copies of the trained heads. In made worlds with nothing planted, plain random heads called a lead in up to 24 of 40 runs and the rotated copies in none. Where style itself lay along the trained heads, both called a lead in every run, so a lead never shows a need by itself (amendment CU; `pf_heads.py`).
  - E4's test of the LUST output runs inside the forum comments. The chat situations have no desire label and no amused label, so the handoff's form would compare two sources and not two feelings.
  - E6's registered quantity is a difference from other texts, because any feeling output tends to rise toward the end of a short report. The chat situations average about twenty words; the pre-flight found that two or three sentences are enough for the operator when an order is there, so the short arm runs, and two long arms are added (blog posts by window; long recalled stories).
  - E8's bar is replaced. In a made world where the word is a pure blend, a head taught on the word alone beat the mix of the two outputs by 0.19 in every run, because it also learns what the word's situations are about. So the handoff's bar is filed as a description, and the card registers two forms that told the made worlds apart (`pf_blend.py`, `pf_blend2.py`). E8's first ask compares the first and the last sentence, because these texts are too short for thirds.
  - E10 scores each named grouping with one statistic against rotated copies of the trained heads, which keep how alike the heads are by construction. In made worlds, pairs of tags read one at a time drew false pairs in every world. Where the heads were alike by construction and the text held no groups, plain random heads called the true grouping in every run, and rotated copies in at most 1 of 20 (`pf_groups.py`, `pf_groups2.py`).
  - E3 is sized as an estimate. With about 2.8 reports a writer and two-item scales, only small correlations are plausible. It keeps card TP58's table shape where five traits exist.
  - E9 gains a third column, the acceptance tag.
  - The third reserve lane of 25 November, anger answered by rank, runs here as card TP79, on a talk-page corpus this program already holds. Anger is the top tenth of the RAGE output, because the corpus marks none; the addendum's own form would drop the lane.
- **Sizing, from what was measured.**
  - Cards. On 23 November this repository landed fourteen cards in a day once their inputs were saved. Thirteen of the nineteen cards here start on saved outputs now, some in part. Five wait on a queue job or on the filler's exit. One (TP78) is the table made at each push.
  - Spark GPU. Nine jobs. The six that are sized come to about 37.5 hours at the speeds this repository has recorded (section 3). Q26 and Q34 are under an hour each, and Q33 is timed on its first 1,000. Last week's filler was planned at about 36 hours and projects to 151 because its count was a quarter of the roster, not because the reader was slower. So each job here counts its texts and times its first 100 before it is sized, and these figures are a floor. The filler yields to every job here and resumes after them.
  - Workstation GPU. G12 (4 to 6 hours) and G14 (under 1), then G13, timed on its first 100, then a filler of up to about 21.6 hours at W's recorded 137 seconds a hundred blog openings (G15), so that GPU does not stand idle as it did last week.
  - The curator asked for one day of running and asked that it be sized as two.
- **The filler.** Q24 stops itself at 08:00 PT on 27 November. Card TP73 takes its export. After the export the filler restarts as job Q24b. It is a copy of `scripts/week_q24.py` with both uses of 1795795200 (the `check` cutoff and the `Guard` deadline) set to 1795968000 (29 November 08:00 PT), `OUT` set to `jobs/Q24b`, and `Q24b` as the job in its owner record and binding. It starts at the first roster ordinal without a verified Q24 `complete.json`, with its row offset at that author's start, and it reads again any author Q24 left part-read. Its script hash is filed. A copy of `scripts/week_q24_return.py`, with `SCRIPT`, the job name, the folder and the starting ordinal changed, exports it. Amendment CG applies to Q24b as it did to Q24, and it runs behind every job in section 3.
- **Files.** This packet at the root. The handoff as `docs/exchange/THEORY_HANDOFF_R37.md`. The bundle as `PREFLIGHT_2026-11-27.zip`. The return as `docs/exchange/THEORY_RETURN_2026-11-29.md`.

## 1. Terms added

| Term | Meaning |
|---|---|
| Linear score | A head's output before any squashing: the text's vector times the head's weights, plus its constant. Trained heads and null heads are compared in this form, each standardized on the same pool of texts |
| ISO set | A set of null heads with random weights, each scaled to unit length, as the nineteen of TP45 were made. Seeds `<card>:iso:<n>` by the same rule as `TP45:placebo:23`. A third kind of null, heads fitted on shuffled labels, is not made this round: the tag heads' fit script and teaching data are not in this repository |
| ROT set | The trained heads turned by one random rotation of the vector space. It keeps each head's length and the angles between heads, and loses only where they point. Seeds `<card>:rot:<n>` by the same rule. The rotation is the Q of a QR of a standard normal square matrix, with the signs of R's diagonal made positive, as `pf_heads.py` does it |
| Band | The 2.5th to 97.5th percentile of a statistic across null sets |
| Lead | The trained value lies above the ROT band. Inside the band is a tie. Below the band is filed as below |
| Random-heads row | Under amendment CU: the ROT band and the ISO band beside the trained value, with the trained value's percentile in each. The verdict is read against ROT |
| Standing mark | A reader's four answers about one text: whose doing it reports (her own, someone close to her, someone else, no one's); whether her standing rose, fell or neither; whether others saw it or will know; whether a rise was earned by her own doing or effort |
| B, C, W | The readers as this repository names them. B and C on the Spark, W on the workstation. W is never pooled with B (rule AP) |
| Held-out writers | Writers in no fold that fitted anything used to score them |
| SADNESS | The output this repository's code names PANIC/GRIEF and its rows show as SADNESS (rule BC). This sheet says SADNESS throughout |

## 2. Rulings and amendments

**The curator's rulings, 25 to 27 November.**

| Id | Subject | His words, or the record |
|---|---|---|
| R44 | Two days of rapid studies | "let's actually do a day-long set of rapid studies to create texture for our results real quick." and "go ahead and give us two days worth of studies." |
| R45 | The engine first | "your central main goal is to push the engine forward." |
| R46 | Both machines busy | "We want the Spark built out and running fully, testing all of the stuff and also all of our GPU and CPU resources humming away as well as we can." |
| R47 | The tag is called acceptance | Ruled on 25 November, as the Theory and Research thread's ledger records it (item 02). The tag this repository names belonging is shown and exported as acceptance |

**Amendments.** Each is the analyst's unless it says otherwise.

| Id | Subject | Text |
|---|---|---|
| CU | The random-heads row | Every number about a person (a repeat, a match, a slope inside a writer, a correlation with an outside score) is filed with its random-heads row: 1,000 ISO sets and 1,000 ROT sets where the vectors are at hand, 200 of each where a fit must be rerun for every set. Trained and null heads are compared as linear scores. The verdict word is read against the ROT band, because the pre-flight found that the ISO band calls a lead where nothing is planted (card TP61). The ISO band is filed beside it. Before the first use, check on the chat texts and on one blog shard of Q20 that the saved tag scores equal the squashed linear scores from the saved vectors, and the same for the placebo scores on the blog shard, where they are saved. File the largest gap. Columns saved as constants are left out. If a gap exceeds 0.00001, the trained heads' linear scores are taken as the logit of the saved scores, null sets are scored from vectors made by a frozen pass of the need encoder on the Spark, and the return says so |
| CV | The queue (the curator's approval is in the message that delivers this packet) | Section 3's jobs run on the two GPUs. One GPU job at a time on each machine, as now. Each job times its first 100 texts, writes its projected hours beside this sheet's figure, and runs. A job that projects to more than three times its figure still runs, and the return's first line says so. Rule AZ's launch at once applies to each job when its turn comes. Amendment BD's memory rule is extended to job Q32: up to 100 GB resident while reader C is loaded, no other job of this program on the Spark while it is, and if loading leaves less than 15 GB free, C is unloaded and Q32's C arm is skipped. This amends the limit amendment BS set |
| CW | A mark is a measurement | For every mark a reader makes here: the reader's pinned id, the prompt's text and hash, temperature 0 and a fixed seed are filed before the job. A second reader marks the same texts (W for B's jobs). Three wordings of the prompt are run on a sample (Q32). Agreement is filed as Cohen's kappa for each field. A mark with kappa at or above 0.60 between B and W is usable. From 0.40 to 0.60 it is weak, and any result that rests on it is a description. Under 0.40 it is not used. No prompt shows a reader the label a card will score against |
| CX | Many small studies | Every registered guess in section 4 (his, the thread's, print's) and in section 7 (the analyst's) enters card TP78's table, with a p value from a shuffle or from the writer resamples. The false discovery rate is held at 0.10 across the table. A result whose interval ends within one standard error of its bar is filed as unresolved. Where a card says so, the form is chosen on a random 70% of writers and scored once on the other 30% |
| CY | Long recalled stories (the curator's approval is in the message that delivers this packet) | The long recalled stories are the set Sounding Line's source list (`docs/TOOLS.md`) calls Hippocorpus and places at `open/hippocorpus/raw/` under that repository's data root (`SOUNDING_LINE_DATA_ROOT`), not in its tree. Only its recalled and retold stories are read. It has no stated licence. It is used as a test. If this repository cannot read it there, Q30 and TP76 are dropped and the return says so. Its figures stay in this repository's record and the theory thread, and sheets about it carry no number until the curator rules on one-word dispositions. |
| CZ | Display labels until card TP64 reports (the handoff's standing ask, with ruling R47) | The acceptance tag is shown beside the Respect tags. The LUST output is shown as wanting. The PLAY output is shown as amusement. The SHAME output is flagged as silent outside chat until TP64's third part lands. No Meaning row is shown. Card TP71 makes these changes |
| DA | Pushes, and the idle line | The return is pushed when a card lands and at least every six hours. Its first line says whether either GPU or the card queue is idle, and why. Last week nothing was pushed from 23 November 21:15 to 27 November 02:35 |
| DB | The bundle for the sealed jobs | Card TP72's bundle is handed to Sounding Line as TP58's was: a payload directory, a hash manifest, a rehearsal on invented data. Sounding Line's rows TMP2 and TMP3 run it. Until it is delivered Sounding Line rehearses with TP58's bundle |

Unchanged and in force: AO (local readers, temperature 0, fixed seed, structured output, pinned id), AP, AT (no host names), BC (channel rows say SADNESS), BD (memory; reader C alone when loaded, extended to Q32 by amendment CV), the stop at 90 °C or at any thermal slowdown, CE (ring and X; "Against, and clear" first), CG, CH, CJ, the bar on demographic columns, and no analysis by sex.

## 3. The queue

Speeds are this repository's own: B at 107 to 111 seconds a hundred short texts for eight ratings, 146 to 149 a hundred blog openings, about 42 a hundred sentences; C at about 163 a hundred sentences; W at 36 a hundred chat texts and 137 a hundred blog openings. A standing mark has four fields and is sized at 0.9 seconds a text for B, between a sentence mark and eight ratings, and at 3.5 seconds for C. One answer about a long opening is sized at 1.0 second and about a long story at 1.5. Those four figures are the analyst's guesses. The arithmetic is `queue37.py` in the bundle. Counts marked "about" are counted by the job.

| Job | Machine and reader | What it reads | Texts | Hours | Feeds |
|---|---|---|---|---|---|
| Q26 | Spark, B | A throughput trial: 200 chat texts one at a time, then two at once, then four at once, to the reader already loaded. No server setting is changed. If the outputs at two or four at once equal the serial outputs on all 200 and the texts a minute rise, later jobs use that many at once. If not, they stay serial. What would be needed to do better is written in the return for the owner | 600 | under 1 | every later job |
| Q34 | Spark, frozen readers | The worry encoder, as Q20 ran it (`scripts/week_spark.py`), on the 6,600 recalled events and the 51,557 roster sentences. If TP63's second header check holds, also the worry encoder, the tags and the ten outputs on the news-reaction essays, with base vectors saved. Inputs: the roster sentences from `Q21-inputs/Q11-sentences.jsonl.gz` and `Q12-sentences.jsonl.gz`, in file order so that they line up with Q21's outputs; and the event texts, packed on the workstation from the generation table (as `scripts/person_teacher_inputs.py` reads it) into a pinned input shard with a manifest and sent as Q21's inputs were | about 58,000, and the essays | under 1 | TP63, TP65 |
| Q33 | Spark, frozen readers | The tags, the ten outputs and the base vector of every message of the talk-page corpus, and of the court arguments if TP79's second table is made | 391,294 messages, and 1,700,789 utterances if the second table is made | timed on its first 1,000 | TP79 |
| Q27 | Spark, B | Standing marks | 24,850 chat texts; 6,600 recalled events; 11,571 held-out forum comments | 10.8 | TP67, TP74, TP77 |
| Q28 | Spark, B | The eight features on every recalled event. The record holds none by B | 6,600 | 2.0 | TP63, TP77 |
| Q32 | Spark, C then B | C's standing marks on 1,500 of Q27's texts (500 from each source, drawn by seed). B's on 1,000 of them under two further wordings of the prompt | 3,500 | 2.0 | TP77 |
| Q29 | Spark, B and the frozen readers | Sentence marks (change, whose, when) and the ten outputs for each sentence of the held-out forum comments and of the ISEAR reports | about 26,000 sentences | 3.0 | TP65, TP77 |
| Q31 | Spark, B | Blog posts. (a) Loss candidates: openings of posts with six or more saved windows whose mean SADNESS output is in the top twentieth, at most 6,000, each read once: is this post about a loss the writer has suffered, and of what kind. (b) A sentence sample: 500 authors drawn by seed from those with 80 or more posts, 20 openings each, every sentence marked, with the ten outputs for each sentence by the frozen readers | about 6,000 openings; about 70,000 sentences | 9.8 | TP65, TP66, TP75, TP77 |
| Q30 | Spark, B and the frozen readers | Long recalled stories, under amendment CY: one mark a story (is it about a loss the writer suffered), sentence marks, and the ten outputs, the tags and the base vector for each sentence. Retold stories share writers with recalled ones, so every interval resamples whole writers | about 4,100 stories; about 70,000 sentences | 9.9 | TP65, TP66, TP76, TP77 |
| G12 | Workstation, W | Standing marks on all of Q27's texts | 43,021 | 4 to 6 | TP77 |
| G13 | Workstation, W | Sentence marks on Q29's sentences, on Q31's sample, and on 20,000 of Q30's sentences. Then W's loss answer on Q31(a)'s openings and on Q30's stories | about 116,000 sentences; about 10,100 texts | timed on its first 100 | TP65, TP77 |
| G14 | Workstation, W | The eight features on all recalled events | 6,600 | under 1 | TP77 |
| G15 | Workstation, W | The workstation's filler. For each blog author B has read whole, in Q24's author order: ten openings from each date half, drawn by the seed rule TP45 used for k of 10, read for the eight features. Openings that job G11 already read with the same reader id and prompt are reused and not read again. It yields to G12, G13 and G14 and runs whenever that GPU would otherwise be idle | up to 56,700 openings | up to about 21.6 | TP73, TP77 |

**Order on the Spark:** Q26, Q34, Q27, Q28, Q32, Q29, Q31, Q30, then the filler Q24b. Q33 runs between jobs as soon as its corpus is readable. Q30 does not start without the curator's approval of amendment CY.

**The standing-mark prompt** is written once, hashed and filed before Q27. It shows the text and nothing else. It asks the four questions of section 1 in fixed order with fixed answer words, as structured output. The two further wordings for Q32 are written at the same time.

## 4. Cards

Each card is filed as the three-part sheet (who was measured and how; three to six plain sentences; the limit sentence), with its random-heads row where it reports on a person, a ring on each registered guess and an X where the result parts from it.

### TP61. Random heads beside every person check (the handoff's E1; claims P2, P3, P5)

- **Data.** Q20's saved scores for the 5,428 qualifying blog authors, and the blog vectors on the Spark.
- **Build.** On the Spark, from Q20's vectors: each author's mean vector over all her openings, and by date half at k of 5, 10, 20 and 40, drawn as TP45 drew them (`week_curve.nested_indices`); and the vectors of the openings TP47 used. These are exported in archives under the transfer cap, and null sets are then scored on the workstation. Means at k of 40 exist only for the 1,460 authors with 80 or more posts. Part (d) runs on the Spark, where every opening's vector is, and only its slopes are exported. For (d), only the id, author, date half and first-person count columns of the workstation's suffix joins are sent to the Spark, and no text goes.
- **Asks,** each with the random-heads row of amendment CU:
  - (a) Her highest need repeats (TP46: 34.1% against 15.1% dealt). Null groups are seven random groups of null heads, of the sizes of TP46's seven need groups, from each null set.
  - (b) Worry's repeat above the median tag (TP52), against the spread of repeats across null heads.
  - (c) Her own version of a word (TP47), with null heads in the tags' place.
  - (d) The slope of first-person words on opening worry (TP52), with each of the 3,800 heads of 200 ISO sets, and of 200 ROT sets, in worry's place.
  - (e) The analyst's, under CU: the same rows for TP45's repeat and match at k of 5, 10, 20 and 40, and for TP51's line inside a writer when TP73 lands.
- **Registered (the thread's).** On (a), (b) and (c) the trained value lies inside the ROT band. On (d) no null head reaches worry's slope: worry's slope lies above the 99.5th percentile of the 3,800 null slopes of each kind.
- **Read at the smallest k.** Match is filed at every k and read at the smallest, because it reaches its ceiling as posts are added.
- **Pre-flight (`pf_heads.py`).** Made worlds of 500 authors, forty runs each, at five and at twenty posts a half. Where authors differ only in style and no need is planted, the trained heads' match led the ISO band in 24 of 40 runs at five posts and the ROT band in none; where that style is strong along a few directions, in 10 of 40 and none. So a band of plain random heads calls a lead with nothing there, and the verdict is read against the ROT band (amendment CU). In those worlds the trained heads' repeat sat below both bands' medians (0.55 against 0.57), because heads that read content pick up what changes from post to post. Where style alone lay along the trained heads, with no need planted, the repeat led both bands in every run and the match led the ROT band in every run at five posts: a lead over ROT shows that the heads read what differs between writers, not that it is a need. With needs planted, the repeat led both bands in every run and the match led the ROT band in 39 of 40 at five posts. At twenty posts the match was at its ceiling (0.9995) and led nothing, so the match is read at the smallest k. The repeat of the highest need led in only 4 to 6 of 40 runs with needs planted, and in 13 to 19 when style alone lay along the heads: a tie on ask (a) is weak, and a lead on it would not show a need (the made world had six need groups; the card uses TP46's seven). For ask (d), a head tied to the outcome at 0.6 beat every one of 3,800 ISO null slopes in 39 of 40 runs, and a head with no tie sat near the 10th percentile of them.
- **Limit sentence.** A lead over null heads says that the trained directions hold more of what differs between writers. It does not say that what differs is a need. On (d) the null heads read base vectors and worry reads its own encoder, so a lead there also compares two encoders.
- **Changes in the engine.** Sorts the engine's checks into those that measure the reader and those that measure content. Only the second kind feeds a person display.
- **Prior art.** Control tasks for probes (Hewitt and Liang 2019), and the reviews that followed, say a probe's score needs a baseline of random features. No search found this exact comparison of fixed heads with rotated copies; it is not called new.

### TP62. Content against style (E2; claim P5)

- **Data.** The chat situations: 24,850 texts, 810 writers, 32 assigned words; the saved vectors; the 29 outputs (nineteen tags and ten channel outputs) as linear scores; writer ids rebuilt from the source as `ed_situations` does.
- **Asks.**
  - WORD. On held-out writers, in five folds by writer, name the assigned word from the 29 outputs with a multinomial logistic fit. The same from each of 200 ISO sets and 200 ROT sets of 29 heads.
  - WRITER. On held-out texts, crossed by word: for the 336 writers with eight or more texts, a writer's profile is her mean on texts of half the words, drawn by seed. Each of her other texts is given to the writer whose profile it lies nearest. The same from each null set.
  - Both again on texts that do not contain their assigned word or its stems.
- **Where.** On the workstation, from tp30's saved chat vectors and the saved heads.
- **Registered (the thread's).** The outputs beat the null heads on the word and lose to them on the writer: WORD above the ROT band, WRITER below the ROT median.
- **Pre-flight (`pf_content.py`).** Made worlds of 400 writers and 32 words, twelve runs a world with twenty null sets of each kind. Where the heads carry what the words differ in, and writers' style lies anywhere, the thread's pattern appeared in every run: the word was named from the trained outputs at 0.22 against 0.15 from rotated copies, and the writer at 0.20 against 0.23. Where the words differ only in directions the heads do not carry, the trained outputs named the word at chance (0.03) and the pattern never appeared. Where writers' style lies along the heads, the trained outputs beat the rotated copies on the writer in every run (0.54 against 0.41) and the pattern never appeared. So the two columns together tell the three worlds apart.
- **Limit sentence.** The words were assigned, and a writer's texts differ by word.
- **Changes in the engine.** One table that says what the tags are for, and makes matching a control and not a goal.
- **Prior art.** Work on telling authors apart holds the topic fixed or crosses it between fitting and testing (Stamatatos 2017; Altakrori and others 2021). This card follows that practice.

### TP63. Outside scores on the recalled-event writers (E3; claims P5, S3; the map's trait labels)

- **First step.** A header check of the recalled-event release for answers its writers gave about themselves. This repository reads two of them, `anxious` and `calm`, on the scale the header shows. They are worded like two items of a ten-item personality inventory (the analyst's memory of the release, not a fact on record). If the header holds the other eight, five two-item trait scores are formed with that inventory's own keys, fixed in the card before any outcome is opened. If it does not, the card runs on the two-item stability score alone and says so. Only the header's column names are read, and no demographic column's values are opened. Where five traits exist the table takes card TP58's shape.
- **A second header check (the results thread's note to the data collection thread, need 2).** Later releases of the news-reaction essays carry trait and empathy scores for each writer (the results thread's memory, not a fact on record). If the release this repository holds has them, the same table is made for the essays' writers, with the frozen readers run on the essays first (job Q34). If it does not, the card says so in one line and the data collection thread's check stands.
- **Data.** 6,600 reports by 2,379 writers; the saved tags and ten outputs; the worry reading after Q34; B's eight features after Q28.
- **In parts.** The table is made now from the saved tags and outputs. The worry row is added after Q34 and the reader's features after Q28.
- **Ask.** Each output is first cleared of the report's assigned feeling (the mean for that label is taken off). Per writer, the mean of each tag, each channel output and the worry reading, against each score, as a rank correlation with 2,000 whole-writer resamples. The same for 200 ISO and 200 ROT sets. Two bars from the null sets of each kind: a family bar (the 95th percentile, across sets, of the largest correlation anywhere in the table) and a cell bar for each trait. The verdict is read against the ROT bars.
- **Registered (his map's).** Curiosity with Openness; family, contact and acceptance with Agreeableness; status, approval, power, competition and honor with Extraversion; order, savings and serenity with Conscientiousness; worry and the unpleasant outputs with low stability; each leading its row and its column.
- **Registered (the thread's).** With a few short reports a writer, only worry and the unpleasant outputs against low stability clear the null heads.
- **Registered (print's, as the analyst reads Parks-Leduc and others 2015 and Dörendahl and others 2021).** Print agrees with the map on curiosity with Openness and on order with Conscientiousness. It parts from the map in three places: contact goes with Extraversion more than with Agreeableness; acceptance goes with low stability; power and competition go against Agreeableness.
- **Pre-flight (`pf_outside.py`).** Made worlds of 2,400 writers with a few short reports each and scores of reliability 0.5, forty runs a world. With nothing planted, the cell under test cleared the family bar in no run and its own interval left zero in 2 of 40. With a link of about 0.25 planted through one head, that cell cleared both bars and led its row and its column in every run. When a trait went with a part of style that no trained head carries, the cell read 0.00 and the null heads picked the trait up, which raised the family bar from 0.071 to 0.129. So the bars ask whether a head does better than a random direction, which is the question amendment CU puts, and a cell can clear zero without clearing them. The made world's bars came from plain random heads only. With nothing planted, some other cell of the table cleared the family bar in 3 of 40 runs.
- **Limit sentence.** Short scales and a handful of reports per writer.
- **Changes in the engine.** The first outside check of a person reading, on data already held.

### TP64. Head by head (E4; claim W1; the display's labels)

- **Data.** The ten outputs per text on the chat situations, on the recalled events less the 1,199 reports that taught the PRIDE head, and on the 11,571 held-out forum comments.
- **Asks.**
  1. For each output, how well it tells its own words from its two nearest other words, by TP48's operator (the area under the curve, with 2,000 whole-writer resamples), inside one source at a time. The two nearest words are chosen two ways and both are filed: the pairs the handoff names, and the two other words the output scores highest on a random half of writers, scored on the other half. Each again on texts that do not contain the word.
  2. The three loudest and three quietest labels per source, from TP59's table.
  3. The SHAME output on recalled events and forum comments. It is zero there because those sources are scored by the head fitted on forum comments alone, which has no shame label. Score them with the head that has a SHAME column (`go_plus_envent`), leaving out the reports in its fit, and file how well it tells shame and guilt events from the rest.
- **Registered (the thread's), restated inside one source.** In the forum comments the LUST output cannot tell desire from optimism and excitement (under 0.70). The PLAY output is at chance outside forum amusement. SEEKING, RAGE, FEAR, SADNESS, DISGUST and PRIDE each clear 0.70 against their nearest words.
- **Limit sentence.** The forum's desire label means wanting or wishing, not sexual desire, so an output taught on it reads wanting.
- **Changes in the engine.** Which outputs keep their names on the display. The third part ends the SHAME flag of amendment CZ where the output varies.
- **Fixture.** None beyond TP48's: the operator is the same.

### TP65. Coming or landed (E5; claims A1, T2, T3; catalog lines E3 and E16)

- **Data.** The saved roster of 51,557 sentences (every sentence of the 24,850 chat texts and of 6,050 recalled events) with B's and W's marks on all of it and C's on 5,014; the ten outputs per sentence; the worry reading of each sentence after Q34. Everything but the worry contrast runs now.
- **Classes.** Looking ahead: the when mark is ahead. Landed: a change is marked and the when mark is already. Neither: no change is marked. A change marked as ongoing is a fourth class, counted and left out of the contrasts.
- **Operator.** Inside one report: each output on one class less another, with the report's own mean taken off and the sentence's place in the report held. B's marks are the registered reading. W's marks are a second reading, and sentences where B and W agree a third. 2,000 whole-writer resamples.
- **Registered (his, kept from 22 November).** Every output is higher on change sentences than on neither.
- **Registered (the thread's).** FEAR, SEEKING and LUST are highest on look-ahead sentences. SADNESS, RAGE and PRIDE are highest on landed ones. Worry is higher on look-ahead sentences than on landed ones.
- **A check against people (the analyst's).** In the recalled events the writers rated their own events. The share of a report's sentences marked as looking ahead is set against the writer's ratings that come nearest to foresight, bound from the header before the outcome is opened. It is a description of the mark, not a registered test.
- **More sources as marks arrive:** forum comments and ISEAR (Q29), blog openings (Q31), long stories (Q30).
- **Pre-flight (`pf_marks.py`).** Made reports of two to fifteen sentences, marked by two readers who are each right four times in five; their kappa came to 0.46 to 0.47, which amendment CW calls weak. Forty runs a world. With nothing planted, an interval left zero in 2 to 3 of 40 runs. When the classes and the outputs both drift along a report and nothing else is planted, the contrast read as an effect in 15 to 24 of 40 runs without the sentence's place, and in 1 to 5 with the place held. A planted difference of 0.30 was found in every run, but it read 0.130 to 0.206, because wrong marks blur the classes. On sentences where both readers agree it read 0.265 to 0.293. So the place is held, a weak mark can still find an effect, and its size is read from the sentences both readers agree on.
- **Limit sentence.** "The changes are reader marks." The texts recall things past, so the mark reads which way the person in the story is facing, not the tense.
- **Changes in the engine.** A time direction on each channel row.
- **Prior art.** Appraisal theories split feelings about a prospect from feelings about an outcome (Ortony, Clore and Collins; Lazarus 1993). In the recalled events themselves, fear was rated high on suddenness and low on foreseeing consequences (Troiano and others 2023), which runs against the thread's guess for FEAR.

### TP66. FEAR before SADNESS inside one loss (E6; claims T2, T3; the gates beside E3)

- **Short arm, now.** Chat texts written to sad, devastated, lonely and disappointed, and recalled events labelled sadness, with two or more sentences. The card files the number of texts and of writers at two, three, and four or more sentences before anything else.
- **Operator.** For each text and output, the centre of where the output sits along the text. D is the mean, over loss texts, of SADNESS's centre less FEAR's. The registered quantity is D on loss texts less D on other texts with the same number of sentences, with 2,000 whole-writer resamples. The handoff's form (FEAR highest in the first third, SADNESS in the last) is filed beside it for texts of three or more sentences, as a share against the same share in other texts. A shuffle of sentences inside each text is filed as a description and is not the null. RAGE's centre is filed beside FEAR's.
- **Long arm one, blog posts (after Q31a).** Posts a reader marked as about a loss, by window: each post's saved windows in order, the same operator on window index, against candidate posts the reader marked as not about a loss, with the same number of windows.
- **Long arm two, long recalled stories (after Q30; amendment CY).**
- **Registered (his gates of 25 November).** In a text about a loss FEAR's output is highest in the first third and SADNESS's in the last.
- **Registered (the thread's).** It shows in recalled events and not in chat situations.
- **A rival from print (the analyst's reading of Maciejewski and others 2007, which followed bereaved adults over months and not sentences).** Disbelief and anger come before sadness, and fear is not in the order.
- **Pre-flight (`pf_order.py`).** Made texts at two lengths (two or three sentences; four to twelve), 1,500 loss texts and 1,500 others, forty runs a world. With nothing planted the registered quantity cleared zero in 1 of 40 runs at the short length and 0 at the long. With FEAR early and SADNESS late planted in loss texts it did so in every run at both lengths, so two or three sentences are enough for this operator when the order is there. When SADNESS rises along every text more steeply than FEAR does, loss or not, SADNESS's centre less FEAR's cleared zero by itself in every run, and the registered difference from other texts did so in 0 of 40 at the short length and 3 at the long. A shuffle of the sentences inside each text is not a fair null in that world: at the long length, the share of loss texts with FEAR highest in the first third and SADNESS highest in the last was 0.121, against 0.108 under the shuffle and 0.120 in other texts. So the comparison is with other texts, and the shuffle is filed as a description.
- **Limit sentence.** A short report runs from what happened to how it felt, so any feeling output peaks late. Only the difference from other texts is read.
- **Changes in the engine.** An order-of-channels line for longer texts.

### TP67. Whose rise (E7; claim T11)

- **Now.** Chat texts for proud (867), impressed (805), confident (785) and grateful (815). The PRIDE output by whose doing, from B's saved ratings of her own and another's responsibility: her own where the first is the higher, another's where the second is, ties left out. Inside each word where both sides have 50 texts or more.
- **After Q27.** The same with the standing mark's three levels: her own, someone close to her, someone else.
- **Registered (his trigger, a rise in her standing that she expects others to see).** Higher when the doing is her own.
- **Registered (the thread's).** No difference, because the output reads a rise in anyone's standing.
- **Registered (print's, as the analyst reads the work on reflected glory and on admiration).** Her own above someone close above someone else.
- **Limit sentence.** The split rests on a reader's mark, and "proud" in these texts is often said of someone else.
- **Changes in the engine.** If there is no difference, the PRIDE row needs a self or other split before it stands for his PRIDE, and admiration is shown apart.
- **Fixture.** None: a difference of means inside a word.

### TP68. Embarrassment: a blend, or an output of its own (E8; claims T4, T7)

- **Data.** Chat texts for embarrassed (740), ashamed (628) and guilty (760), and the other 29 words; tp30's saved chat vectors; the ten channel outputs and the nineteen tags as linear scores, each standardized over all chat texts; and the ten outputs per sentence of the roster, as Q21 saved them. Runs on the workstation.
- **Asks.**
  - (a) The PLAY output on the first and on the last sentence of texts with two or more sentences, for the three words. Read inside each word as last less first, with 2,000 whole-writer resamples.
  - (b1) His claim, as a blend. Nothing is fitted. For each of the 45 pairs of the ten outputs, the sum of the two standardized outputs is scored on how well it tells embarrassed from the other 31 words, as the area under the curve. Filed: the rank of the SHAME and PLAY pair among the 45, and that pair's area less the better of SHAME alone and PLAY alone, with 2,000 whole-writer resamples.
  - (b2) The engine's question, by a yardstick. For embarrassed and for each covered word: a logistic head on the frozen chat vectors taught to tell that word from the other 31, with the PRIDE head's penalty and optimizer (an L2 penalty of 1/(3n) on the weights; L-BFGS-B), fitted in five folds by writer and scored as the area under the curve on held-out writers; less the same for a logistic fit on the 29 linear outputs in the same folds. That difference is the word's gain, with 2,000 whole-writer resamples of the held-out predictions. The covered words are every chat word other than embarrassed that an output is mapped to in `tp28.py` (its MAP and SECONDARY), and proud; the list is filed in the card before any gain is computed. Filed: every word's gain, and where embarrassed's gain stands among the covered words.
  - (b3) The handoff's form: the dedicated head of (b2) against the best fitted mix of the SHAME and PLAY outputs, within 0.02. Filed as a description, with the pre-flight's finding beside it.
- **How it is read.**
  - His claim holds as a blend if the SHAME and PLAY pair ranks first of the 45. If it ranks first and its lead over the second pair has an interval that reaches zero, the reading is unresolved.
  - An eleventh output is supported if embarrassed's gain is above every covered word's gain. If its lead over the largest of them has an interval that reaches zero, the reading is unresolved.
  - Both can hold: a blend with something of its own.
  - If TP64's first part finds the PLAY output at chance on chat words, (a) and (b1) are filed as blind.
- **Registered (his).** "Embarrassment is just shame plus play." The SHAME and PLAY pair ranks first, embarrassed's gain is not above every covered word's, and PLAY's last less first is above zero in embarrassed texts and not in ashamed ones.
- **Registered (print's rival, a display of its own: Keltner and Buswell 1997; Tangney and others 1996).** Embarrassed's gain is above every covered word's.
- **Pre-flight (`pf_blend.py`, `pf_blend2.py`).** Made worlds of 500 writers and 32 words in which every word also has subject matter of its own (thirty runs for the handoff's form; twenty runs a cell for the others). Where embarrassed was a pure blend, the handoff's bar still went against his claim in every run: the dedicated head beat the mix of the two outputs by 0.19. Two forms held up. The unfitted sum of SHAME and PLAY ranked first of the 45 pairs in 18 to 20 of 20 runs where the word held the blend, and in no run where it did not. With heavier subject matter it ranked first in 5 to 9 of 20 blend runs, and still in none of the others: first place supports the blend, and a lower place does not rule it out. The dedicated head's gain over the 29 outputs was above every covered word's gain in every run where the word had a direction of its own, with the blend or without it, and in 3 to 5 of 20 runs where it had none. The made world had five covered words, which gives one run in six by chance; the card's list is about three times as long. The made world's yardstick used a default penalty and not the PRIDE head's. A plain difference in level between two words on one output cleared zero in 8 to 12 of 20 runs with nothing planted on that output, so no such difference is read. A change inside a text, as in ask (a), takes each word's own level out.
- **Limit sentence.** Assigned words. A head taught on one word also learns what that word's situations are about, and the yardstick takes off only what any word's head learns. The SHAME output varies only on chat until TP64's third part lands.
- **Changes in the engine.** Whether the display needs an eleventh output, and whether embarrassment can be shown as SHAME with PLAY.

### TP69. The Competence stand-in by word, and Respect against being liked (E9; claims N1, N2)

- **Data.** TP59's table; B's three features for the chat situations (goal support, own responsibility, own standards); the tags.
- **Ask.** TP59's table with three more columns per assigned word, each with its range from 2,000 whole-writer resamples: the Competence stand-in; the mean of the status, approval, competition and honor tags; and, as the analyst's addition, the acceptance tag. Then the words on which the first two part by half a standard deviation or more, with whether things went her way, and the words on which Respect parts from acceptance by as much. The Respect column gets a random-heads row.
- **Registered (the thread's).** The Respect tags rise without the stand-in on embarrassed, ashamed and jealous. The stand-in rises without them on prepared and content. Both rise on proud and confident.
- **Why the third column.** In print, standing and being liked come apart (Anderson, Hildreth and Howland 2015). The handoff's two columns cannot show that.
- **Limit sentence.** A writer's texts differ by assigned word, so nothing here is inside one situation.
- **Changes in the engine.** Whether Respect is its own row on the display or sits under Competence. It serves a question open with the curator and does not answer it for him.

### TP70. The needs from a blind sort (E10; claims N1, N4; the ledger's item 44)

- **Data.** The nineteen tags as linear scores, with ISO and ROT sets, on (a) the 24,850 chat texts and (b) the author means of the 5,428 blog authors, from TP61's export.
- **Method, fixed here.**
  1. Standardize each score and take out the text's length in words.
  2. Rank correlations between the nineteen, and the same for 1,000 ISO sets and 1,000 ROT sets.
  3. A floor on the count. The number of leading components of the correlation table whose size is above the 95th percentile of the ROT sets' component of the same rank. The pre-flight found that this reads low, so it is filed as a floor and not as a count of needs. The ISO figure is filed beside it.
  4. Named groupings, one statistic each. For a grouping of tags into groups: the mean correlation between tags in the same group, less the mean correlation between tags in different groups, with tags outside every group left out. It is read against its own band across ROT sets. Its excess is the statistic less the ROT median, in units of the ROT band's spread. Three groupings are scored: the map's (TAG_MAP_V2 in `engine/tompathy_engine/packs/trigger.py`: six groups, with romance and `indep` outside every group), the thread's three, and print's four. The thread's and print's groups use the code names `belonging` for acceptance and `indep` for independence. One grouping fits better than another if its excess is larger in both files.
  5. Which tags go together is then described from the components step 3 keeps, after a varimax turn: a tag goes with the component it loads on most, if that loading is 0.4 or more. If step 3 keeps fewer than two components, this step is skipped. A table of pairs is filed beside it as a description only.
  6. Steps 3 and 4 again with each score's projection on the first component removed, and again in 100 resamples of writers (chat) or authors (blogs).
- **How it is read.** A grouping above its ROT band holds some of the structure. Which grouping is right is read only from the comparison of excess between the groupings, in both files.
- **Registered (his).** The needs appear as groups: the map's grouping lies above its ROT band in both files.
- **Registered (the thread's, from a first look at 73 word profiles).** Three groups: standing (status, approval, competition, honor, acceptance, power), closeness (family, contact, romance) and exploring (curiosity, independence). This grouping lies above its ROT band in both files and fits better than the map's. No Meaning group: order, savings and serenity, scored as a grouping of one group against all other tags, do not lie above their own band. The body tags split.
- **Registered (print's, as the analyst reads the value circle).** A fourth group of order, savings and tranquility, which is the tag of that name: the four-group version fits better than the three.
- **Pre-flight (`pf_groups.py`, `pf_groups2.py`).** Made worlds of 800 authors with 25 texts each, twenty runs a world: heads alike by construction or not, and texts that hold three groups or none. Pairs of tags read one at a time drew at least one false pair in 55% of runs or more in every world and under either null, so pairs are a description. With heads alike by construction and no groups in the text, plain random heads read 2.60 to 2.70 components and called the true grouping in every run. Rotated copies read 0.05 to 0.15 components there, and called the true grouping in 0 to 1 of 20 runs; in the plain world with no groups, in 1. With three groups planted in the text, the grouping's statistic lay above its ROT band in 20 and 18 of 20 runs for texts and in 14 and 19 for author means, and a wrong grouping of the same sizes did so in 1 to 3 of 20 across all worlds. A partly wrong grouping, with two of the three planted groups merged, also lay above its band in 10 to 20 of 20 runs where groups were planted. So a grouping above its band holds some of the structure and is not thereby the right one, and which grouping is right is read from the comparison between them. The count against rotated copies read 1.35 to 1.55 where three groups were planted, so it is a floor. The reading of which tags go together from the kept components agreed with the planted groups at 0.58 to 0.70 on the adjusted Rand index when the heads were alike, and at 0.27 or less when they were not, so it is a description.
- **Limit sentence.** The tags were taught from short lists, and heads taught from like lists point alike. The rotated null takes that out; it cannot put back a need the lists never held. A partly wrong grouping can also lie above its band.
- **Changes in the engine.** The display's need rows come from this table.
- **Prior art.** Talevich and others (2017) sorted 161 motives by people's judgments into Meaning, Communion and Agency, with no stopping rule. Counting groups against a null is ordinary practice (parallel analysis). Not called new.

### TP71. Display labels, and the names in exports (amendment CZ; ruling R47)

- Apply amendment CZ to the display contract of TP60 and to every export: the tag named belonging becomes acceptance in outputs, exports and cards, with the old name kept as an alias for old files; the LUST and PLAY labels; the SHAME flag; no Meaning row. Tests updated. The change list is filed in the return.
- **Changes in the engine.** These are the changes.

### TP72. The bundle for the sealed jobs, second version (amendment DB; the handoff's S1 and S5)

- TP58's bundle with four changes:
  1. It takes its list of excluded communities and dropped comments from the receiver, which computes them inside the seal by Sounding Line's rule (its amendment DJ). It no longer asks for a list from the source's documentation.
  2. Every table gets its random-heads row: 200 ISO and 200 ROT sets, scored from each author's mean vectors inside the job.
  3. The map's cells and print's cells (as in TP63) are both marked, and each map gets its own pass column.
  4. A second adapter for conversations: rows of speaker key and turn text, giving each speaker's means over her turns.
- Qualified on invented histories and one invented conversation, then delivered with its manifest.
- **Changes in the engine.** The bundle is the engine running outside this repository.

### TP73. Whole authors, after the filler exits

- When Q24's worker exits at 08:00 PT: verify and export as `scripts/week_q24_return.py` does, then restart the filler as Q24b (section 0). Then, as registered on 22 November: TP51's blog arm, TP43's third table and TP52's extension, on the authors B has read whole (2,835 at the last count).
- **Added (the analyst's): B as a second reader of a person.** For each of B's eight features, the repeat of an author's mean across date halves at k of 10 and 20, beside the band of TP61's null heads on the same openings.
- **Added (the analyst's): do two readers agree about a person.** For each feature, the correlation across authors between B's mean and W's mean on the same openings, beside the two readers' agreement on single openings, and W's own repeat across date halves, each beside the band of TP61's null heads on the same openings. It starts on the authors that both Q24 and job G11 have read whole, and grows as G15 lands. B and W are compared and never pooled (rule AP).
- **Guess (the analyst's).** B's features repeat less than the null heads do, because a reader of content repeats less than a reader of style.
- **Limit sentence.** One reader, one build, and authors who wrote enough to be read whole.

### TP74. Standing that was not earned (the ledger's item 71; after Q27)

- **Data.** Texts whose standing mark says her standing rose, from all three sources, split by earned or not; and texts where it fell, split by her own doing or not, and by whether others saw.
- **Ask.** The PRIDE output, the mean of the Respect tags, and (on chat, where B's features are saved) the Competence stand-in, on earned against unearned rises, inside a source and inside a word where counts allow. The SHAME output (chat only until TP64's third part) on falls by her own doing against others', and seen against unseen.
- **What it can tell apart (the three worlds on the table with the curator).** If Respect is only Competence as others read it, PRIDE and the Respect tags rise on earned standing alone. If Respect is a need of its own, they rise on unearned standing as much. The third world, two needs on two gauges that mostly travel together, predicts a smaller rise on unearned standing with the stand-in flat.
- **Guess (the analyst's).** The third: PRIDE and the Respect tags are lower on unearned rises than on earned ones and above texts with no rise.
- **Limit sentence.** Whether a rise was earned is one reader's judgment of a short text, and unearned rises will be few.

### TP75. Worry and looking ahead in a writer's posts (after Q31b)

- **Data.** 500 authors, 20 openings each, every sentence marked; the saved worry reading and null-head scores for those openings.
- **Ask.** Inside an author, the slope of an opening's worry reading on its share of look-ahead sentences. Across authors, mean worry against mean share. Each with null heads in worry's place.
- **Guess (the analyst's).** The slope inside an author is above zero and above the band. That would tie the one reading that has repeated beyond the median tag to something the text says.
- **Limit sentence.** Reader marks, and one sample of long-running blogs.

### TP76. Long recalled stories (after Q30; amendment CY)

- TP65's and TP66's operators on the stories. And, in TP63's form: the curiosity tag and the SEEKING output against the writers' own openness score, which the release carries, with a random-heads row from the sentence vectors Q30 saves.
- **Guess (his map's and print's alike).** Curiosity goes with openness.
- **Limit sentence.** A set with no stated licence, used as a test.

### TP77. How good the marks are (amendment CW)

- **Now, from saved marks.** Agreement between B, W and C on the when and change marks over the roster: kappa for each pair and field, and the tables behind them.
- **As jobs land.** B against W on each field of the standing mark (Q27, G12); B against C and B against its own two rewordings (Q32); B's rating of own responsibility against the writers' own rating on the recalled events (Q28, G14); sentence marks and loss answers on the new sources (Q29 to Q31, G13).
- Each mark gets one line in the return: usable, weak, or not used, by amendment CW.
- **Limit sentence.** Two readers that agree can be wrong together. Only the last check sets a mark against people.

### TP78. The family table (amendment CX)

- Every registered guess of sections 4 and 7 in one table: whose it is, the estimate, its interval, its p value, its place under the false discovery rule, and its verdict word. "Against, and clear" first.
- **Limit sentence.** A false discovery rate across guesses of unequal weight treats each as one test.

### TP79. Anger answered by rank (the reserve lane of 25 November; claims A3, T1; after Q33)

- **Source.** The talk-page corpus that flags administrators, which this program already holds. Sounding Line took it in for its card CP1 (`corpora/store/external/convokit_wiki_corpus/` in that repository's tree): 38,462 speakers, 391,294 messages and 125,292 conversations, each message with the message it replies to, under CC BY-SA 4.0 as that repository's source list records it. If this repository cannot read it there, the return's first line asks the data collection thread for a readable copy, and the card waits.
- **Job Q33.** As in section 3. Speaker ids are salted before any table is written, and no message text or id enters a sheet.
- **Terms.** A message is angry if its RAGE score, as a linear score, is in the top tenth of all messages; the cut is set on a random half of the conversations, and every table is made on the other half. A reply pair is a message and a reply to it by another speaker. A speaker is an administrator in a pair if that message's own `is-admin` is set. No speaker field but `is-admin` and `edit-count` is read. From above: the first speaker is an administrator and the second is not. From below: the reverse. Level: both alike.
- **Asks.** The count in every cell before any rate.
  1. Returned anger. The share of replies that are angry after an angry message, less the share after a message that is not, for each of the three relations.
  2. No reply. For a message that itself replies to someone: the share that the someone answers, after an angry message less after one that is not, by relation.
- **Null.** For the null a speaker counts as an administrator if any of her messages is flagged. Those speaker flags are dealt at random among speakers, 200 times, and again dealt only among speakers in the same fifth of edit count. A difference between relations is read against those bands. The random-heads row is the same table with each of 200 ROT heads in RAGE's place.
- **A second table, if time allows.** The court arguments on the store (`open/supreme-corpus/raw/` under Sounding Line's data root, `SOUNDING_LINE_DATA_ROOT`), where a justice outranks an advocate: the same two asks from above and from below only.
- **Registered (his, 25 November).** Anger is returned most between near-equals. From below it more often draws no reply.
- **Not scored.** His third clause, that anger from above is answered with yielding. No mark for yielding exists here.
- **Limit sentence.** An administrator flag is a thin kind of rank, the RAGE output was taught on forum comments, and a heated thread raises everyone's anger whatever their rank.
- **Changes in the engine.** A first reading between people: whether the display should carry who is speaking to whom.
- **Prior art.** In this corpus people matched their wording more to administrators than to others (Danescu-Niculescu-Mizil and others 2012, as the analyst remembers it). In bargaining, anger from a weaker party drew less yielding (Lelieveld and others 2012, as the addendum of 25 November cites it). No search was made for anger by rank in this corpus. Not called new.

## 5. Opens when (counted as zero hours)

| Card or part | The one input it waits on | Owner |
|---|---|---|
| TP73 | Q24's worker exits (08:00 PT, 27 November) | this repository |
| TP61(e)'s line inside a writer | TP73 | this repository |
| TP63's worry row; TP65's worry contrast | Q34 | this repository |
| TP63's reader features | Q28 | this repository |
| TP63's essay table | Q34's essay part | this repository |
| TP70's blog file | TP61's export | this repository |
| TP67's second part, TP74 | Q27 | this repository |
| TP75, TP66's blog arm | Q31 | this repository |
| TP76, TP66's story arm | Q30, the curator's approval of CY, and the stories being readable from this repository | curator, then this repository |
| TP65's further sources | Q29, Q30, Q31 | this repository |
| TP73's part on two readers, beyond the authors G11 read | G15 | this repository |
| TP77's later parts | Each job it names | this repository |
| TP79 | Q33, and the talk-page corpus being readable from this repository | this repository; the data collection thread if it is not readable |
| The real trait job and the conversation job (TMP2, TMP3) | TP72's delivery, then Sounding Line | this repository, then Sounding Line |
| The person checks of TP61 on a second kind of writing | Word from the data collection thread on whether the dream reports on the store, which hold long series by one writer, may be read by local readers, and their path | data collection thread |
| A Meaning reader | A text set with purpose or meaning scores | data collection thread |
| A check of marks against people's own labels of time direction | A set of sentences that people labelled as about the past, the present or the future | data collection thread |

## 6. Order, the standing rule, and what to drop

1. Start Q26 at once, by writing `priority.pending` in the week folder, which Q24 and Q24b check. Then the Spark's queue in section 3's order. Start G12 on the workstation at once, then G14, then G13 as its inputs land. G15 fills every gap on that GPU.
2. Cards on saved outputs, in this order: TP71, TP61, TP62, TP70, TP64, TP65, TP77's first part, TP63's first table, TP68, TP69, TP66's short arm, TP67's first part, TP72.
3. TP73 when the filler exits, and the filler's restart as Q24b.
4. Cards and parts that wait, as their inputs land: TP63's worry row and reader features, TP65's worry contrast, TP79, TP67's second part, TP74, TP75, TP66's arms, TP76, TP61(e)'s last line, TP73's part on two readers, TP77's later parts.
5. TP78 at each push.

**Standing rule.** A card whose inputs are saved starts when the agent is free. A GPU that is idle beside a job whose inputs are ready is a fault, written in the return's first line. Nothing here waits on a question to the curator. Where the sheet leaves a choice open, take the reading that claims less and write the choice in the card.

**If time runs short, drop in this order:** Q30 and TP76; G13; TP75; TP66's blog arm; TP79's second table; TP69's third column.

## 7. Guesses before data

His, the thread's and print's guesses are in each card. The analyst's own, filed so they can be scored:

- TP61: (a), (b) and (c) tie against the ROT band. On (d) worry's slope is above the 99.5th percentile.
- TP62: the pattern holds, and holds on texts without their word.
- TP63: no cell clears the family bar. Worry against low stability clears its cell bar.
- TP64: the LUST output is under 0.70 inside the forum comments. The SHAME output, once scored with the right head, tells shame and guilt events from the rest above 0.70.
- TP65: SADNESS is higher on landed than on look-ahead sentences. FEAR is not higher on look-ahead than on landed sentences.
- TP66: in the short arm the difference from other texts is not clear of zero. In blog posts about a loss, SADNESS's centre lies later than FEAR's by more than in other posts.
- TP67: her own above another's, by less than a fifth of a standard deviation.
- TP68: the SHAME and PLAY pair is not first of the 45. Embarrassed's gain is not above every covered word's.
- TP70: the floor is one or two in both files. The thread's grouping lies above its band and fits better than the map's. Print's fourth group does not add.
- TP73, TP74, TP75: as written in those cards.
- TP77: the when mark is usable between B and W. The earned mark is weak.
- TP79: returned anger is above zero in all three relations and does not differ between them against the dealt flags. Anger from below draws no fewer replies.

## 8. The return

`docs/exchange/THEORY_RETURN_2026-11-29.md`, pushed at each landed card and at least every six hours.

1. The first line: whether either GPU or the card queue is idle, and why.
2. "Against, and clear."
3. TP78's table.
4. One line a card, with its sheet's path.
5. The queue: each job's first-100 timing, its projected and its real hours.
6. TP77's line for each mark.
7. TP71's change list, and each card's proposed change to the display, not switched on until the results and alignment thread has read the return.

## 9. Limits of this sheet

- The queue's hours are from recorded speeds and four guessed ones. Last week's large job ran four times its plan because its count was a quarter of the roster, not because the reader was slower. Every count here is counted by the job before it is sized.
- Marks by readers are the weakest link. TP53 found that the readers' change marks tracked the writers' own suddenness ratings well under the bar (0.13 for B against 0.26), so every card that rests on a mark carries TP77's line.
- A tie with null heads does not show that a need is absent. It shows that this check cannot see one.
- Nothing here reads a demographic column, and no analysis by sex is made.
