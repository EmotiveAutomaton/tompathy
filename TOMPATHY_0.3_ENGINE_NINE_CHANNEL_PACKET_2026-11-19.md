# ToMpathy 0.3 engine: the nine-channel reader and the Spark lane

*19 November 2026. From the analyst (the implementation thread), for the engine owner on branch `codex/0.3-engine`. Back end only, plus one opt-in row in the research view. It adds to the trigger-reader packet of 15 November and withdraws nothing in it except where section 2 says so. It carries no question for the curator: every choice is made here and can be overruled by him.*

**Where the files go.** This file: the repository root, as `TOMPATHY_0.3_ENGINE_NINE_CHANNEL_PACKET_2026-11-19.md`. The theory thread's Round 29 handoff, which this packet cites and does not replace: `docs/exchange/THEORY_HANDOFF_R29.md`. The thread's seed ledger, if the curator supplies it: `engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl`, unchanged. The pre-flight of this date concerns Sounding Line's cards and the sealed runner; nothing in it is an engine result.

## 0. Read first

- **Read at:** the engine `14e2ced` (18 November, 17:43 PST), Sounding Line `005f38fa7`, the theory thread through its Round 29 close, the Spark setup thread through 07:20 PST on 19 November.
- **Where the engine stands** (its own record of 18 November):
  - The wire works: gate, tags, channel, scalar and composite paths are implemented, opt-in, default off.
  - The need reader cleared on both bars in four fits (frozen MiniLM; three fine-tuned seeds, of which the filed rule selects seed 47). No pack and no export exist, because an optional larger rung is still running.
  - The gate failed. No tested threshold met both required bars together (0.70 detection, 0.80 silence). That blocks label serving, the gated counting grid and the composite trigger export.
  - The trigger reader's runner is built and has never run.
  - The worry reader passes its known-group checks and reads 5.95 of 9 on plain prose, so its level means nothing on a page.
- **What this packet does.** It closes the need reader and ships its export. It opens the Spark for the engine. It replaces the single label with a profile over the nine channels, which is the curator's ruling of 19 November. It rebuilds the gate on a definition taken from the theory. It runs the trigger reader. It tests the three things the theory thread asked of the engine (handoff legs A1, A2, A6).
- **The curator's direction, in his words:** "We want to get the triggers to where we can identify them damn near every time." "we're dealing with a PCA rather than a categorical distribution". "we're not going to get pure channels."

## 1. Terms this packet uses

| Term | Meaning here |
|---|---|
| Stand-in | a labelled feeling word used to read a channel. The map is in section 2, as the curator admitted it |
| Readers' labels, writers' labels | GoEmotions comments were labelled by readers. EmpatheticDialogues situations and Crowd-enVENT reports carry the writer's own label |
| Need tag | one of the nineteen tags the need reader scores (`TAGS` in `packs/trigger.py`) |
| Profile | nine numbers for one text, one per channel, each between 0 and 1. They need not sum to 1 |
| Reader A, reader B | the two local generative models frozen by card SP1. They read and label. They write nothing a user sees |
| Teacher label | a label a frozen local reader gives a text, used to train a small head |
| Head | a small classifier on an encoder's vectors |
| Lift | the mean score of a tag over texts with one label, minus its mean over the source's other labelled texts, in units of the tag's standard deviation in that source |
| Ledger row | one line of `engine/validation/EVIDENCE_LEDGER.jsonl` (card RC1) |
| Claim id | one of the ids of the handoff's section 2 (T1 to T9, N1 to N3, A1 to A3, S1 to S3, AT1, AT2, TB1, P1, P2, M1 to M4, LP1 to LP15). Always written after the word claim or claims |
| Need code | the engine's own codes for the six needs, N1 to N6 in `TAG_MAP`. Always written after the words need code. Need code N1 and claim N1 are different things |

## 2. Rulings and amendments

Rulings are the curator's, with his words and their dates. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R19 | Names | The first need is **Competence** (was Knowledge; 19 November). The second is **Meaning** (was Nest; 18 November). Need codes N1 to N6 keep their numbers. The stories' tranquility tag (safety) moves from need code N2 to the body, need code N6 (18 November: "I'll accept your calling of safety as a body trigger.") |
| R20 | The stand-in map is admitted | "I admit the map above with that notable exception." The exception is embarrassment: "Embarrassment is what you feel when someone mocks you instead of shaming you." The engine's hold on the map lifts |
| R21 | The map | SEEKING: curiosity and excitement (readers); excited, anticipating, hopeful (writers); need tag curiosity. PLAY: amusement (readers); need tag contact. LUST: desire (readers; it means wanting in general); need tag romance. CARE: caring and love (readers); caring and sentimental (writers); need tag family. PANIC/GRIEF: grief, sadness, lonely, devastated (the writers' source labels sadness as sad); need tag family. RAGE, FEAR, DISGUST: their own words; need tags power and order; safety and health, where the reader's tag for safety is tranquility; food. SHAME: ashamed (writers); need tags approval and status. Embarrassment and embarrassed are in no row |
| R22 | A profile, not a label | "there will be kind of a weighting of how much they are attracted to the given issue or problem or inference based upon their trigger." The target of a channel reader is the profile |
| R23 | Labels | Pride, guilt and embarrassment are labels. A test on a label is not reported as a channel test |
| R24 | The Spark is worked by agents | "I need to have agents be able to get up in there and do all their work in accordance with my standard spec sheet process." |
| R25 | The record | "I want there to be a grander structure that we're building." Card RC1 |
| AN | The optional rung closes (the thread's advice of 18 November, adopted) | Card C0 |
| AO | Readers on the Spark (analyst, under the facts sheet's first rule) | Local models read only: temperature 0, a fixed seed, structured output, pinned by model ID, nothing paid or remote. Training a small head or encoder on open data is new work with its own pins |
| AP | Two builds are never pooled (analyst; the sheet's warning made a rule) | The Spark's `qwen3.5:9b` is ID `56671c2ab938`. The workstation's is `6488c96fa5fa`. Forecasts from different IDs never enter one fit |
| AQ | A gate that passes TP31 is a qualified state gate (analyst's reading of the 16 November ruling) | The rows that ruling placed behind a qualified gate run behind it as new rows |
| AR | TP24 is evaluated without a gate (analyst) | The record lists a qualified gate as a dependency of TP24. Every input of its evaluation is an event report, so the evaluation needs none. Serving stays behind a gate |

## 3. The Spark lane: rules

As installed on 19 November. Where a later edition of `claude/SPARK_FACTS.md` differs, the sheet governs.

- **Reach.** From the workstation: `ssh spark` (host `spark-33de.local`, user `agent`, the agent's own key). No sudo for this lane, no Docker, no reading of `/srv/private`. The rules on the box are `/home/agent/AGENTS.md`. Never power it off.
- **First call of a session:** `ssh spark "id; nvidia-smi -L"`. If the call waits on an approval nobody gives, the lane's cards are held with that reason and the workstation cards go on. Nothing outside the lane waits on it.
- **Places.** Workspace `/home/agent`. Open data and the model cache `/srv/open` (`HF_HOME=/srv/open/hf`). Pins `/srv/open/pins`. The engine builds its own environment under `/home/agent/venvs/engine` to match the pins (PyTorch 2.14.1+cu130, transformers 5.14.1). The interpreter is `python3`.
- **One record.** A job is written and committed in this repository, copied to the Spark, run there, and its outputs are copied back and committed with a receipt that names the pins. The Spark keeps caches and nothing else.
- **GPU.** Every job that uses it holds `flock /home/agent/gpu.lock` for its whole run. One GPU job at a time across all programs.
- **Heat** (the limit is the analyst's). The sheet says the GPU with every processor core loaded throttled at 97 °C, and a two-hour test was started on 19 November. Until the sheet records its result: a GPU job uses at most 4 processor threads, loaders and tokenizers included, and no processor-heavy job runs beside it. The Sounding Line packet sets the same limit of 4 for sealed jobs.
- **Cost first.** Each new kind of job runs 500 texts and records seconds per 100 before its full run is sized.
- **No sealed data.** This lane touches open data only.

## 4. Cards

### C0. Close the need reader and ship its export (claims N1, M1, M3)

- **Why.** The frozen rung and the three fine-tuned seeds agree to within 0.008 on mean transfer gain (0.0969 to 0.1040). Sounding Line's IN13 Part D waits on the export. Each fold of the larger encoder takes about three hours on the workstation.
- **Do.**
  1. If the optional rung has finished all five folds when this is read, apply the registered comparison and select. If not, start no further fold; keep the finished folds and record the rung as closed unfinished. If it is wanted later it is a new card with its own pins.
  2. Select by the filed rule. Build the research pack and the IM2 export. Deliver IM2 to Sounding Line by the existing route.
  3. Register tag map version 2: tranquility under need code N6. The reader's nineteen tags do not change and nothing is retrained.
- **Done when** the pack's receipt and the export's delivery receipt are filed and each names a ledger row.

### SP1. Bring-up on the Spark, and two frozen readers (claim M1)

1. Reach, the environment, the lock, the thread limit.
2. **The encoder check.** The selected need reader scores 200 fixed texts on the Spark's processor and on its GPU. Largest difference from the workstation's saved forecasts: 0.0001 or less in probability.
3. **Reader A:** `qwen3.5:9b`, ID `56671c2ab938`, as pulled.
4. **Reader B:** the largest model of the same family that Ollama's library lists at 27 billion parameters or more and that runs in 64 GB, pulled once and pinned by ID. Catalogues list a 27b ([one listing](https://www.lmstudio.ai/qwen/qwen3.5-27b)); the tag in Ollama's own library is checked at pull time. If none exists there, reader A is the only reader and every teacher card says so.
5. **The panel,** each reader, no human involved:
   - 300 Crowd-enVENT reports from the engine's held-out fold. The reader rates the eight features of `FEATURES` from 1 to 5. Score: the mean rank correlation with the writers' own ratings. Bar: no lower than the saved readable-feature forecasts score on the same reports.
   - The same 300 a second time: identical output on 99% or more.
   - Valid structured output on 99.5% or more.
   - Seconds per 100 texts.
6. The reader with the higher panel score is the research reader. Wherever a teacher label is used, the two readers' agreement is reported beside it.

### TP28. The stand-in table (handoff A1; claims T6, T7, T8, T9, N1)

- **Question.** Do the admitted stand-in labels land on the need tag their row predicts, in text nobody tuned for it? Does joy split by tag?
- **Reader.** The pack of C0. It was trained on stories only. GoEmotions and EmpatheticDialogues have had no part in it. Crowd-enVENT was the transfer set behind the bars that qualified it, so its cells are not fresh in the way the other two sources' are.
- **Sources.** GoEmotions (readers' labels), EmpatheticDialogues situations (writers' labels), Crowd-enVENT (writers' labels).
- **Cells.** One per stand-in label and source, as in R21. With the intensity variants a source carries (furious, terrified) as second readings.
- **A cell is filled at tag level** when a predicted tag has the highest lift of the nineteen and its lift's interval excludes zero (2,000 draws; by comment, by conversation, by report). **Filled at need level** when the top tag belongs to the predicted tag's need under tag map version 2.
- **A channel's row is filled** when most of its cells are filled at need level.
- **Bar for the table** (analyst's): six of nine rows filled, with at least two of the four that have never had a test (SEEKING, PLAY, CARE, LUST).
- **The joy split.** Joy texts (joy; joyful) sorted by their top tag among curiosity, contact, romance and family. In GoEmotions, where a comment can carry several labels: the share of each split that also carries a SEEKING stand-in, the PLAY stand-in, the LUST stand-in, a CARE stand-in. Registered: in each split the matching share is the largest of the four. In Crowd-enVENT: the writers' 21 ratings compared across the splits, as a table.
- **Filed whole:** every stand-in label's profile over the nineteen tags.
- **Seen before.** On 15 November the analyst ran a bag-of-words need reader on Crowd-enVENT and saw fear on tranquility, disgust on food and sadness on family. Those three cells are replications and are marked so.
- **Limits to carry.** Readers' labels are a reader's guess at the writer. LUST is uncovered beyond the romance tag. A lift is about a word and a tag, not a channel and a need.
- **Prior art** (the thread's, from its 18 November addendum): pleasant feelings separated by appraisal ([Ellsworth and Smith 1988](https://doi.org/10.1080/02699938808412702)); motive and emotion modelled together on the story corpus ([COMMA 2022](https://aclanthology.org/2022.coling-1.15/)). Not found in a light search: a need reader used to split near-twin feelings.

### TP29. Embarrassment against shame (handoff A2; claim LP7)

- **Question.** The curator: embarrassment is SHAME under PLAY's shield. The published account: a feeling of its own, apart from shame and from amusement, with an appeasing job. Which does text show?
- **Sources.** EmpatheticDialogues situations labelled embarrassed and ashamed. GoEmotions comments labelled embarrassment, amusement and remorse.
- **Two heads, each trained away from the test source.** PLAY's stand-in head: amusement against the rest, on GoEmotions. SHAME's stand-in head: shame against the rest, on Crowd-enVENT.
- **Two marker lists, fixed before any count** and filed with the card: fun markers (laughing, joking, funny and their forms) and appeasement markers (apology, awkwardness, blushing and their forms).
- **Registered readings.**
  1. Fun markers are more frequent in embarrassed situations than in ashamed ones (rate ratio above 1, interval clear), with length held.
  2. PLAY's head scores embarrassed above ashamed by 0.2 standard deviations or more.
  3. For embarrassed against every other label, PLAY's head added to SHAME's head raises the area under the curve by 0.02 or more, with the interval above zero and both weights positive.
  4. In GoEmotions, embarrassment carries amusement as a second label more often than remorse does.
- **Verdict rule (owner amendment, 19 November).** A: PLAY is in embarrassment when readings 1, 2 and 3 all hold. B: embarrassment carries appeasement that shame does not when the length-adjusted appeasement-marker rate ratio is above 1 and its interval is clear. A and B are independent; reading 4 enters neither verdict. Report all four readings and the marker comparison. Use the four combined wordings in [the owner ruling](docs/TP29_OWNER_RULING_2026-11-19.md). This is a label test (R23), not a channel test.
- **Limit.** These are labels (R23). The result is a recipe for a word.

### TP30. The profile reader (analyst's card; claims A2, M1, M3, M4)

- **Why.** The ruling is a profile. A reader trained on one label per text is trained against the ruling. Two of the held sources record how several people labelled the same text.
- **Targets.**
  - GoEmotions, the release with one row per rater: for each comment and channel, the share of raters who chose a stand-in of that channel.
  - Crowd-enVENT's re-read reports: the same share over its readers.
  - Labels in no row of the map make an unassigned share. It is reported and not trained as a channel.
- **Reader.** Nine sigmoid outputs on the encoder's vectors, trained on the shares. Rung 1: frozen MiniLM vectors, on the workstation. Rung 2: the fine-tuned encoder, on the Spark.
- **Tests.**
  1. **Across sources.** Trained on readers' shares, scored on writers' labels (EmpatheticDialogues, Crowd-enVENT): area under the curve per channel. Seven channels have a writers' stand-in and can be scored this way. PLAY and LUST have readers' stand-ins only; they are scored on held-out GoEmotions comments against the raters' majority and reported apart as within-source figures. Bar: 0.70 or more on five of the seven, with SEEKING or CARE among them.
  2. **The mix is real** (analyst's). On held-out GoEmotions comments: the spread of the predicted profile goes with how much the raters disagreed (rank correlation 0.20 or more). And where two channels are both predicted at 0.25 or more, the raters' labels fall on those two more often than on any other pair.
  3. **The co-firing table.** Nine by nine: how the predicted channels rise together over held-out texts, beside how the raters' shares do. Filed whole. It is the first estimate in text of which channels travel together. The theory expects RAGE with FEAR to be allowed and PLAY to fall where FEAR is high.
  4. **Against the single label.** The same encoder trained on one label per text. The profile reader must not lose more than 0.01 of area on test 1.
- **Why it makes the engine better.** The panel can show a row of nine with its spread, and stop presenting a guess between two near channels as a fact.
- **Limits.** Shares are readers' guesses. A stand-in is a word. LUST's row is wanting in general.
- **Prior art.** Training on raters' distributions is established for subjective labels ([Collins, Bhatt and Weller 2022](https://doi.org/10.1609/hcomp.v10i1.21986); title checked, paper not opened). Not found in a light search: raters' shares mapped onto Panksepp's systems.

### TP31. The gate, rebuilt as a change detector (analyst's card; claim M2)

- **Why the first gate failed** (analyst's reading of the record). Its negatives were each source's own no-emotion rows. No-emotion means a different thing in stories, in forum comments and in event reports, so nothing carried to a held-out source.
- **The definition, from the theory.** Every channel fires on a change on a need. A sentence passes when it reports a change in some person's situation that has happened, is happening, or is expected. Description, instruction, argument and definition do not pass.
- **Teacher.** The research reader answers three things per sentence, as structured output: change or not; whose (the writer, someone else, nobody); when (already, ahead, ongoing, none).
- **Sources,** all already held: the three labelled sources and the stories for sentences likely to pass; the writer-typed sentences of the CoAuthor essays, the Stack Exchange answers of EX5 and each source's own neutral rows for sentences likely not to. A source not held is not fetched.
- **Teacher checks, before any head is trained.**
  - The two readers agree (Cohen's kappa 0.60 or more on 2,000 sentences).
  - Known groups: change on 0.85 or more of Crowd-enVENT's reports that carry a feeling label and of EmpatheticDialogues situations; change on 0.20 or less of the Stack Exchange answers.
  - The stories' own affected flag: agreement reported.
- **Student.** A head on frozen MiniLM vectors.
- **Bars, as registered for TP25:** detection 0.70 or more with silence 0.80 or more on every held-out source, where the key is the teacher's label. And two fixed acceptance sets the teacher never labels: silent on 32 or more of the 40 theme-free items, and silent on 0.80 or more of the 191 revision sentences.
- **If it passes:** a gate pack; amendment AQ applies. The when answer also gives the tense rule of TP24 a second key.
- **If it fails:** the failure table by source is filed, and serving stays blocked.
- **Limit, stated on the pack.** The key is a frozen local reader's reading of a definition. The gate agrees with that reader. No person labelled anything.

### TP24. The trigger reader, run (15 November card; claims A1, T1 to T5)

- **Unblocked.** Its need dependency is qualified by C0. Its gate dependency is lifted for the evaluation by amendment AR. Serving stays behind a gate.
- **Slots.** Need tags from the pack of C0. The eight features read by the research reader for all 6,600 reports on the Spark. Tense by the fixed rule, with TP31's when answer as a second key if it exists.
- **Amendment AP applies.** The 1,200 saved feature forecasts are a second view. Their agreement with the new ones is reported. The two are not pooled.
- **Bars unchanged:** slots within 0.10 of the direct reader; the fixed table at 0.33 or more; tense at 0.60 or more.
- **Added reading** (analyst's): the fixed table's output as a profile, scored against TP30's reader on the same reports. Where the table and the reader disagree, the disagreements are filed by channel pair. That list is the report of contradictions between the table and the fitted model that the engine's record promised the theory thread.

### TP32. A writer's refusals (handoff A6; claim P2)

- **Question.** Is what a writer keeps turning down stable across her sessions, and does it tell her apart beyond what she accepts?
- **Source.** The pinned CoAuthor census. Which suggestion was taken is decided by the inserted text and never by the logged index, which is known to be wrong for part of the accepted menus.
- **Measure.** Each offered suggestion is a vector from the frozen encoder, with its prompt's mean suggestion vector removed so that topic cannot identify anyone. A writer's refusal direction in a set of sessions: the mean vector of the suggestions she dismissed minus the mean of all she was offered. Her acceptance direction: the same for those she took.
- **Support.** Writers with four or more sessions and 20 or more dismissed suggestions in each half.
- **Registered.**
  1. Stability: her refusal directions in two halves of her sessions are closer to each other than to other writers' (mean cosine within minus between, above zero, draws by writer).
  2. Telling her apart: matching a held-out session to its writer from refusal direction, acceptance direction and acceptance rate together beats acceptance direction and rate alone by 0.03 or more in top-one accuracy. Pairs of sessions on different prompts only.
- **Limits.** About fifty writers. A suggestion she never opened was not refused. The thread's caution on these logs applies: this is a reader feature for the person side and not a channel test.
- **Prior art.** The corpus is [Lee, Liang and Yang 2022](https://doi.org/10.1145/3491102.3502030). Not found in a light search: profiles of what writers decline.

### TP33. Worry as a lift (analyst's card; claim S1)

- **Why.** The worry reader's level is about 6 of 9 on plain prose. Its ranking inside a source holds.
- **Do.** In the research view, show worry for a window as its score minus the median score of the page's own windows, and only where it is 1.0 or more above. No retraining.
- **Check.** On the 40 theme-free items the share of windows shown is 0.10 or less. On the three public essays the shown windows are a subset of those the level view marked. The three known-group figures are unchanged, since they are rankings. If the first check fails, the lift is not shown and the failure is filed; the threshold is not tuned on these sets.

### TS4. One row in the research view

- A profile row under a passage: nine short bars with the channels' names. Opt-in, default off, research view only, and only where a qualified gate passes the sentence.
- When the two largest are within 0.10, the row names both. It never prints one label alone in that case.
- It writes no share, count or badge. It appears only when TP30 clears test 1 and a gate pack exists.

### RC1. The record rule (claims: all)

1. A file `engine/validation/EVIDENCE_LEDGER.jsonl`, append only. At every scientific landing, one row with the handoff's eleven fields: `id` (the engine's result id), `date`, `question` (one plain sentence), `data` (the source and how many texts, writers or raters), `estimate`, `interval`, `bar`, `verdict`, `limit` (the record's own sentence on what the result does not establish), `claims`, `family` (the kind of data: readers' labels, writers' labels, stories, writing logs, forum answers).
2. Each receipt's ledger field names its row in place of reading no ledger row.
3. The seed, if supplied, is filed unchanged. A seed row known to be wrong is corrected by appending a row that names it.

## 5. Order

Sized for two to three days of building. The workstation's floors and its one-long-job rule are unchanged.

| When | Workstation | Spark |
|---|---|---|
| First | C0. TP28 and TP29 on cached vectors. RC1 | SP1 |
| Next | TP30 rung 1. TP32. TP33 | TP31's teacher pass. TP30 rung 2 |
| Then | TP31's head and bars. TS4 if earned | TP24's feature pass |
| Last | TP24's fits and the disagreement list. The return | |

**When building is the bottleneck,** keep in this order and drop from the bottom: C0; TP28; SP1; TP30; TP31; TP29; TP24; TP32; TP33; TS4.

## 6. Predictions before data

Written on 19 November, before any of these runs.

| Card | The registered prediction | The analyst's guess |
|---|---|---|
| TP28 | the map of R21, cell by cell | FEAR, DISGUST, PANIC/GRIEF and SHAME fill. SEEKING fills on curiosity and not on excited, anticipating or hopeful. CARE fills at need level. PLAY and LUST do not. Five or six rows of nine; the table's bar is close |
| TP28, joy | the matching share is the largest in each split | holds for curiosity and family, not for contact |
| TP29 | readings 1 to 4 | 1 and 4 hold; 2 holds weakly; 3 is a coin |
| TP30 | 0.70 on five of the seven channels that writers' labels can score | clears on RAGE, FEAR, DISGUST, PANIC/GRIEF and CARE; SEEKING is close; SHAME lacks examples. PLAY and LUST are within-source only |
| TP30, the mix | spread goes with disagreement at 0.20 or more | holds |
| TP31 | the TP25 bars | passes on stories, reports and essays; forum comments are the source most likely to fail |
| TP24 | the fixed table at 0.33 or more | 0.35 to 0.45 |
| TP32 | both readings | stability holds; telling apart does not |

## 7. The return

One file, `docs/exchange/THEORY_RETURN_NINE_CHANNEL.md`: TP28's table with every label's nineteen-tag profile; the joy split; TP29's four readings and both marker lists; TP30's per-channel figures and the co-firing table; TP31's teacher checks and bars by source; TP24's three bars and the disagreement list; TP32's two readings; SP1's panel. Each number carries its limit sentence. Verdicts in the record's own words. Nothing in the return asks the curator a question.

## 8. Limits of this packet

- Every source here is a word somebody chose. The stand-in table can show that words land where the map says. It cannot show a channel firing.
- A teacher label is a local model's reading. Two cards rest on it (TP31, and TP24's features). The panel, the two readers' agreement and the known-group checks are the guards, and none of them is a person.
- The cards have no pre-flight. Running a reader on these labelled sources beforehand would have turned each test into a replication of numbers the analyst had seen. Three cells were seen on 15 November and are marked.
- Reader B is named by rule and not by tag, because the library's listing could not be checked from here.
- The Spark's access path was tested once on 19 November: the coding agent logged in with its own key as the box's `agent` user, through an approved execution path. If that path asks for approval on each call, the lane waits and the workstation column of section 5 stands alone.
