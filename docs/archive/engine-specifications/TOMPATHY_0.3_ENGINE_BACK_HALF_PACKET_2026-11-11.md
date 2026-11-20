# ToMpathy 0.3 engine, back half of the week (11 to 15 November): a faster reader, and the first scores against real writing

*Spec sheet for the ToMpathy engine agent, on branch `codex/0.3-engine` at `5f3ad0a`. It runs from handoff to Sunday 15 November, 22:00 PST. Engine only. Every decision is made here. It replaces the 25 October engine packet, none of which exists on the branch; the one piece kept is named in TP0. As of Wednesday 11 November 2026.*

**What this is for.** The curator, 11 November: "We want accuracy and speed. I'll hook up the front end once we have a better shape for what the front end looks like, but at the very least the engine should start to gain some of the powers if those powers are useful."

**Where the engine stands** (from the branch's own documents and code):
- **Accuracy.** Nothing in the branch measures attention, habit, goal or value accuracy against ground truth on natural writing. The question batteries are constructed templated items. Preview items are labelled `unvalidated`, or `constructed-tested` where a templated battery passed.
- **Speed.** A 3,000-word manuscript takes 64.2 seconds to score on one thread against a 15-second target. Goal calls ran about 171 seconds each on the art essay. Edit-type calls took about 16 seconds each on templated items in the 17 October run.
- **Design.** Attention is a word's surprisal under one small language model, a typical writer, scaled within the page. Goals are read by a separate call for each group of paragraphs. Nothing compares a writer with her own other work.

**What the last three weeks found that the engine can use.**
- Writers pause before words that are surprising given their own earlier writing, with the current prompt excluded: 0.051 per nat [0.036, 0.076], on 34 writers (Sounding Line, D33). The engine has no history baseline.
- A reason can be read from an edit's diff: macro-F1 0.275 against 0.200 from priors (Sounding Line, GO3, as the theory handoff reports it). The engine asks a 9B model about every hunk.
- In constructed worlds, reading goal and habit in separate passes recovered none of the joint reader's gain (Ghost, V27 K6). The theory thread's 11 November handoff makes that an engine note: "infer goal and habit jointly. Do not pick a channel and then re-read."
- The analyst's pre-flight for Ghost's V28 adds two things, to be confirmed there (the analyst's reading): a reader with only a typical habit was the worst one-pass reader in every cell where it was run, and departure marks from a single page were weaker than marks made with the maker's history (AUC 0.81 to 0.95 against 0.95 to 0.97 at sixteen earlier pages in one world, 0.58 to 0.68 against 0.87 to 0.90 in a smaller one).

**What the curator said in the theory thread on 11 November, and what that thread found.**
- On the engine's public test: "we have to take a stab at AI detection because that gives us PR", and "we need to make our accuracy good anyway like it needs to be numbers with the cutting edge if it's going to claim to be cutting edge." Also: "I think it's the theory that needs to tighten up."
- The theory thread then looked at the public tests (its Round 12 message to him):
  - **In-domain detection is close to solved by surface statistics.** On the 2026 shared task the top system averaged 0.975 and a word-frequency baseline scored 0.978 on validation. Beating that would show nothing about a theory. What's open is robustness under attack.
  - **The theory's own objection.** Detectors "frequently misclassify non-native English writing as AI generated", and formulaic human text looks like model text. In the thread's words: "A detector built on your theory inherits those false alarms unless it can tell one person's autopilot from everyone's average."
  - **Latent preferences.** Public tests exist, and none of the four it found reads values off prose or scores a reading of a writer against that writer's own later choices. It flagged that this was not a full survey.
- So this week's detection work is a first stab in the theory's own terms, on data the engine already holds: which words on a page are the writer's and which came from a model, and whether her own history tells her autopilot from everyone's average (TP5). It is not the amazing test. TP2's history rows ask the same question of attention.

So the week's order is: make the reader fast (TP1), score its marks against real stops and test the history reading (TP2), run the first test of AI involvement on the same scoring passes (TP5), score and speed up the edit reader (TP3), then pilot the smallest step toward joint reading on goals (TP4).

## 0. How to run this

- **Scope.** `engine/` and `docs/` only. No front-end file changes. Contract additions are optional fields or flags that default off, so the front end's validator keeps passing.
- **Order.** TP0, TP1, TP2, TP5, TP3, TP4. TP3's model calls and TP4 wait on memory; start them whenever the gate passes.
- **Threads.** Benchmark runs use at most two threads at below-normal priority. Sounding Line uses up to sixteen of this host's twenty-four logical processors and Ghost up to four (Sounding Line's 7 November packet).
- **Memory.** Before the 9B model is loaded, system commit headroom must be at least 20 GiB. Unload it when the run ends. If the gate fails, carry on with work that doesn't need it and try again next session. Sounding Line's readers are held today because commit headroom is 10.5 to 12 GiB; the engine must not take what is left.
- **Bench data.** `.local/bench/`, which is ignored by git. Never commit it and never send it to any provider. Sounding Line delivers four files there this week, each with a README and hash:
  - **EX1, stop labels for CoAuthor's final texts, with no text.** For every word in each session's final text: session id, hashed writer id, the writer's fold (five folds by writer), start and end as Unicode code points in the normalised final text, and its source (typed by the writer, inside an accepted suggestion, or part of the prompt). For writer-typed words only: the stop label and the log pause. Per session: the SHA-256 of the final text after NFC normalisation, line endings as `\n`, trailing whitespace stripped.
  - **EX2, edit-reason bundle.** 5,000 Stack Exchange body edits, 1,000 per reason category, each with before and after text, the reason category, the post id (for attribution under CC BY-SA), the user fold (five folds), and Sounding Line's classifier output, with the frozen feature definitions.
  - **EX3, goal task file.** For PEPs and EIPs: document ids, the pinned commits, section offsets, each document's 49 distractor ids, and a hashed first-author id.
  - **EX4, essays with stops (KLiCKe, CC BY 4.0).** For each replayed session: the final essay text, and for every word typed in order its start and end as Unicode code points in that text, the pause before its first keystroke, a stop label at 2 seconds and one at the essay's own 80th percentile, and a flag for words inserted later. It carries no writer id. Sessions with parse failures are excluded and counted. This one arrives last.
- **Until a file arrives,** build its harness against the constructed replay fixtures in `engine/tests/replay_fixtures.py`.
- **No remote model calls and no model downloads.** Every model named here is already pinned locally. Cloning the two public document repositories for TP4 is allowed.
- **Tests stay green** (`engine/.venv/bin/python -m pytest engine/tests`). Every new function gets a test. Every number in a document comes from a receipt JSON under `engine/validation/`.
- **Wakes.** None recurring. Work inline. Tokens are short this week, so prefer one long run to many short ones, and one session per item.

## 1. TP0: a scoreboard, and one new label behind a flag

- **`docs/ENGINE_SCOREBOARD.md`.** One table, one row per capability (attention marks, AI involvement, edit reasons, goals). Columns: benchmark, units, metric, baseline, engine, 95% interval, bar, date, receipt. This is the only place an accuracy figure for the engine lives.
- **`field-tested`.** Add a function that returns `field-tested` for a capability when its scoreboard receipt shows a registered row clearing its bar, and `unvalidated` otherwise. This week only attention marks and AI involvement have registered rows; the edit-reason and goal rows leave the bar blank. Put the function behind a flag that is off. Packets keep emitting today's statuses until the front-end pass turns the flag on and extends its validator. This is the one piece of the 25 October packet that is kept.
- Record in `docs/` that the 25 October packet is superseded.

## 2. TP1: speed of the departure reader

**What is slow.** `preview/readers.py`, `score_chunks`: a long target advances in 512-token blocks, and each block is scored in a fresh forward pass over a window of up to 2,048 tokens with `use_cache=False`. So a long page recomputes up to 1,536 tokens of context for every 512 it scores.

**What to expect.** A 3,000-word page is about eight blocks. Today's path processes 512 + 1,024 + 1,536 + 5 × 2,048 = 13,312 tokens to score about 4,096. Computing each token once can therefore save a little over three times at best, which is about 20 seconds from 64. A 600-word page gains much less. So step 1 alone is not expected to reach the target; steps 2 and 3 carry the rest. If the target is still missed after all three, the receipt says so.

**Work, in this order, each measured on the same three texts:** the 3,000-word manuscript, the first 6,000 words of the art essay, and a 600-word page.
1. **Compute each token once.** Carry the model's cached keys and values from block to block. When the window would pass its limit, rebuild from the most recent tokens. Choose the limit and the rebuild size that process the fewest tokens while every scored token keeps at least 1,024 tokens of context whenever the page has them.
2. **Threads.** Report one, two and four threads. The default stays one.
3. **If one thread still misses the target:** the same model exported with integer weights to ONNX Runtime. Measure load and score separately.

**Target.** 15 seconds for 3,000 words on one thread, load excluded.

**Parity.**
- When no context is passed, today's path conditions a page's first block on a beginning-of-text token and later blocks on the preceding text alone, cut at the window. A cached path keeps the beginning-of-text token at the head of its cache. So the two paths see identical inputs only on a page's first block. There, in float32, per-word nats must agree to within 0.001. State the new path's convention in the receipt.
- Everywhere else the paths differ by design. Report, for float32 and for int8, the rank correlation and the median absolute difference of per-word nats on the three texts. If a rank correlation falls under 0.98, stop and report before going further.
- In int8 the paths may differ even on the first block. [PyTorch's documentation](https://docs.pytorch.org/2.1/quantization.html) says only that with dynamic quantization "the activations are dynamically quantized during inference". That is the 2.1 page; check the installed version's. As the analyst understands it, the ranges come from the tokens in each pass, so a pass over different tokens quantizes differently; the documentation doesn't say so in those words. Test it directly: score a page's first 512 tokens alone, then again as the first half of a 1,024-token pass, keeping the logits for the first 512 positions. In float32 the two must match to rounding, because later tokens can't affect earlier ones. Any int8 difference is the quantization effect; record it.
- **The binding test is the benchmark.** TP2's row 1 computed with the new path must be within 0.005 AUC of the same row with today's path. That number arrives in TP2's receipt, and TP1 closes on it. Until then the new path is an option, not the default.
- Today's path stays available behind a setting.

**Cache.** Today's cache keys carry the scheme's name in two places: `surface-v1-window2048-chunk512` for a text and `surface-window-v1` for a window. Give the new path new names in both, so old scores are never mixed with new ones.

**Receipt.** `engine/validation/speed-2026-11.json`: times by text, thread count and path; tokens processed; parity numbers; the machine.

## 3. TP2: attention marks against real stops

This is the engine's first score against what a writer did.

**Data.**
- The engine's own CoAuthor logs, the ones `eval/census.py` reads through `--roster` and `--source-root`. `adapters/replay.py`'s `replay` returns each session's final document.
- Normalise that text as EX1 does (NFC, `\n`, trailing whitespace stripped), then compare its SHA-256 with EX1's. EX1's spans are code points in the normalised text; the replay counts UTF-16 units, so convert.
- On a hash mismatch, align by the sequence of word lengths and keep the session if at least 98% of words align; otherwise drop it and count it. If more than 5% of sessions are dropped, stop and report: the two replays disagree, and that has to be fixed first.
- Which words the writer typed herself comes from EX1's source field. The replay tracks ownership internally and doesn't return it.

**Label.** A word is a stop when the writer's preceding interval was hesitant, by Sounding Line's Week 4 definition. The engine never sees the timing.

**Words.** Two sets:
- **the engine's own:** content words that `surface.py` doesn't hold out (it holds out words with digits, capitalised words that don't start a sentence, and code spans, and it leaves stop words out of its statistics);
- **all** writer-typed words.

Report the share of stops that fall outside the engine's own set. Those stops are beyond its reach whatever its AUC.

**Scores.**
- V0, the engine as it is: the departure value the preview computes, word nats under Qwen2.5-0.5B scaled by the page's median and interquartile range, on the engine's own set.
- V4, her history: the same, with the most recent 1,024 tokens of the same writer's earlier sessions (their final texts as they stand) placed before the page as context. Order sessions by their first `eventTimestamp` in the logs; EX1 carries no times.
- V6, someone else's: the same amount of context from one other writer in the same genre, chosen once per target writer with seed 20261111.

**Baseline.** A logistic model on word length, log frequency counted on the training folds' own texts, position in the sentence, sentence start and paragraph start. Fit on four of EX1's writer folds and score the fifth, for all five.

**Metric.** AUC for stop against not, per writer, averaged, with a 2,000-draw writer-cluster interval. "Baseline plus a score" means the score is added to the logistic model as one more term, fitted on the same folds.

**Three registered rows.**
1. **The engine as it is.** AUC of baseline plus V0, minus AUC of baseline alone. The engine's own word set, all writers. Bar +0.02.
2. **Her history.** AUC of baseline plus V4, minus AUC of baseline plus V0, on the sessions that have at least 512 tokens of the same writer's earlier text, same words. Bar +0.01.
3. **Hers, or just more text.** AUC of baseline plus V4, minus AUC of baseline plus V6, on the same sessions. "Hers" when the whole interval lies above zero. "More text of the same kind" when the whole interval lies inside 0.01 of zero. Otherwise unresolved.

**Exploratory variants,** reported with their number so the selection is visible: raw nats with no page scaling (V1); SmolLM2-360M (V2); the mean of the two readers (V3); next-token entropy at the word's first token, which marks open choices (V5). Compute every variant's row-1 statistic on the engine's own word set; the best is the one with the largest. Report V1 on all words as well, separately. When EX4 arrives, score V0 and that best variant on it as the check on a second population: use the essay's own 80th-percentile stop label, report the 2-second label beside it, and cluster by session. Rows 2 and 3 can't be checked there, because EX4 carries no writer id.

**Rival.** Stops cluster at sentence and paragraph starts, which is planning by position. The baseline carries position, so the engine's row is what it adds beyond it.

**What follows.**
- Row 1 clears its bar: attention marks earn `field-tested` (flag off), and the scoreboard states the AUC.
- Row 1 doesn't: the scoreboard says so, and the preview's wording for attention stays "a proxy".
- Row 2 clears and row 3 reads "hers": history-in-context becomes an engine option for any maker with earlier pages, off by default until the front end can supply them.

**Cost.** The engine scores whole final texts, and EX1's README gives their word count. If that is about 400,000 words, then at today's 64 seconds per 3,000 V0 is about 2.4 CPU-hours. V4 and V6 carry up to 1,024 extra context tokens for each session and cost about three times that. Do TP1 first.

**Receipt.** `engine/validation/attention-stops-2026-11.json`, and the scoreboard's attention row.

## 4. TP5: whose words are these? A first test of AI involvement

**Why.** The curator wants a stab at AI detection. The theory thread found whole-document detection in a known domain close to solved by surface statistics, and found the theory's own weak point: formulaic human writing reads like model writing unless the reader can tell one person's autopilot from everyone's average. CoAuthor holds the case the Ghost Scale is for. Inside one page, some sentences were typed by the writer and some were suggested by a model and accepted, and every writer has earlier sessions.

**Data.** The same sessions, replays and scoring passes as TP2. EX1 gives each word's source. Units are sentences in which at least 90% of the words have one source, the writer or an accepted suggestion. Prompt sentences are left out. Report the counts by writer and genre.

**Scores per sentence,** all from passes TP2 already runs:
- **A0, predictability:** the mean of the words' raw nats under the typical reader. Model text should score lower.
- **A1, evenness:** the spread of the words' nats within the sentence. Model text should be more even.
- **A2, history gain:** the mean nats without her history minus the mean nats with it (TP2's V4 pass). Her own sentences should gain more from her history than a model's sentences do.
- **A2 from someone else:** the same, with the other writer's context (TP2's V6 pass).

**Baseline.** Sentence length, position in the document, and whether the sentence opens a paragraph, fitted on four writer folds and scored on the fifth.

**Metric.** AUC for suggestion against writer, per writer, averaged, with a 2,000-draw writer-cluster interval.

**Three registered rows.**
1. **Surface signal.** AUC of baseline plus A0 and A1, minus AUC of baseline alone. Bar +0.02.
2. **Her history.** AUC with A2 added to row 1's model, minus row 1's AUC, on sessions with at least 512 tokens of her earlier text. Bar +0.01.
3. **Hers, or just more text.** Row 2 with her history, minus row 2 with someone else's. "Hers" when the whole interval lies above zero.

**What it is and isn't.**
- The suggestions come from a 2021 model. They were written as continuations of her own text, and she chose which to accept. So this is a hard, small case: model words that already fit her page.
- It is span-level involvement inside a human page, which is the Ghost Scale's job. It says nothing about current models or about whole-document detection.
- Row 3 is the first measurement of the theory thread's condition: whether her history separates her autopilot from everyone's average.

**What follows.** Rows 1 to 3 go on the scoreboard as "AI involvement, CoAuthor suggestions, 2021 model". If row 1 clears its bar, the capability earns `field-tested` with that wording (flag off). A public robustness benchmark is the next step only after these rows exist.

**Cost.** Almost none beyond TP2: the same passes give nats for every word.

**Receipt.** `engine/validation/ai-involvement-2026-11.json`.

## 5. TP3: edit reasons on natural edits

**Data.** EX2. Use the edits whose diff is exactly one hunk under the engine's own `diff_hunks`, used as it is, because the stated reason belongs to the whole edit. Skip hunks over 12,000 characters, as the engine does. Count what is left out, and report the share of edits kept by length band, since `diff_hunks` changes from character to line hunks on long texts.

**Readers.**
- **(a) Today's question.** Ask Q8 directly, with the call `correction_steps` makes for a hunk (`reader.ask("Q8", ...)` with the replacement as text and the replaced span as `before`). Don't go through `correction_steps`: it refuses to run while Q9's receipt fails, and Q9 is disabled. Map Q8's nine labels by this table, frozen here: typo to typo or spelling; grammar to grammar; wording and tone to clarity; add content to added content; remove content to removed content; reorder, format and unclear to other.
- **(b) A feature classifier inside the engine.** `features/deterministic.py`'s edit features plus EX2's listed features, multinomial logistic.
- **(c) A cascade.** (b) answers when its top probability is at least a threshold; otherwise (a) answers.

**Folds.** EX2 carries five user folds. Every edit is scored by a (b) that was trained on the other four folds. Its threshold is chosen inside those four folds by cross-fitting: the lowest value at which (b)'s out-of-fold answers at or above it are at least 95% right on the two-way split below. If no value reaches 95%, the cascade is not run and the receipt says so.

**Sample.** (b) on every single-hunk edit. (a) and (c) on up to 1,000 of them, up to 200 per category, drawn by seed across the five folds; if a category has fewer, use all it has and say so. This part waits on the memory gate.

**Metrics.**
- Macro-F1 over the five categories. An "other" answer is never right.
- Two-way accuracy: housekeeping (typo or spelling, grammar) against content (clarity, added, removed). A reader's typo and grammar answers are housekeeping, "unclear" is wrong, and every other answer is content. This is the split the engine acts on.
- Seconds per edit.

**Rule.** If the cascade keeps today's two-way accuracy within 0.02 and at least halves the time per edit, it becomes an engine option, off by default. The evidence is Stack Exchange body edits; the engine's corrections run on other histories, which are untested, and the scoreboard row says so. The Q8 and Q9 receipt rules are unchanged.

**Cost.** The 16 seconds per call was measured on short templated items. Natural hunks are longer, so 1,000 edits will take more than the 4.4 hours that figure implies. Measure the first 50 and report the projection before running the rest.

**Caveat, stated in the receipt.** The reason is the editor's comment mapped by keywords, so the label carries how editors describe their edits. It is a first natural-data score, not a final one.

**Receipt.** `engine/validation/edit-reasons-2026-11.json`, and a scoreboard row.

## 6. TP4: goals read from departures (a pilot)

This is the smallest engine step toward reading goal and habit together: let the goal call see which sentences were departures. It is a pilot. It changes no default.

**Harness.** `judgments.py`'s `goals` makes one call per group of paragraphs, plus a governing call, inside a closure over a packet. Factor the single call out into a function that takes the cues and the text and returns the label and the description. The preview keeps calling it the same way, and its output on the cached fixtures must not change.

**Task** (EX3; the documents of Sounding Line's GO1). Clone `python/peps` and `ethereum/EIPs` at EX3's pinned commits. From each document remove the Motivation section, the Abstract section, an older EIP's Simple Summary section, their headings, and an EIP's `description` header, so the answer isn't sitting in the input. Rank the true Motivation among its 50 candidates.

**Three readers,** each one local-scope call with the title and the level 1 to 3 headings as cues:
- **(a) Body:** the first 12,000 characters of what remains;
- **(b) Departures:** the sentences at or above the page's 90th percentile of departure, as `summarize_deviation` returns them (each cut at 250 characters), in document order, until 6,000 characters are used;
- **(c) Cues only:** no text.

**Goal statement.** The label and the description the call returns, joined.

**Ranking.** Cosine between the goal statement and each candidate Motivation, under a TF-IDF fitted on the 50 candidates. No new model. Report top-1 and mean reciprocal rank.

**Sample.** 40 documents, 20 PEPs and 20 EIPs, drawn by seed from EX3. Run the three readers document by document, so that whatever completes stays paired.

**Report.**
- Each reader's top-1 and mean reciprocal rank, with author-cluster intervals.
- The paired differences (b) minus (a) and (b) minus (c).
- Seconds per call for each reader.
- From the paired standard error, the number of documents a full run would need to see a difference of 0.05.

**Reading.** With 40 documents the differences will have wide intervals. The pilot says what a full benchmark would cost and whether (b) is in the same range as (a) at a fraction of the input. Sounding Line's GO1 scores a TF-IDF reader and an encoder reader on these documents with the Abstract left in; expect all three goal readers to sit below those, since a short goal statement carries fewer of a document's words than the document does.

**Cost.** Not known until measured: the 171 seconds per call was one paragraph group of the art essay, and (a)'s input is longer. Budget 8 hours of one thread, stop at the budget, and report what completed. It waits on the memory gate. If the gate keeps failing to the end of the week, TP4 carries over and the report says so.

**Receipt.** `engine/validation/goals-motivation-pilot-2026-11.json`, and a scoreboard row marked "pilot".

## 7. Not in this packet

- Any front-end change.
- The 25 October packet's items, except TP0's label.
- **Habit marks.** The engine's habit phrases are repeats within one page, without character spans, and a 400-word session rarely repeats a phrase. Scoring habit against stops needs phrases that recur across a writer's sessions. That is a design for the next packet.
- **Public detection and preference benchmarks.** The theory thread's survey says where they stand; a run on a robustness benchmark waits until TP5's rows exist, and no public test yet scores a reading of a writer against her own later choices. The branch's own handling forecast is the nearest thing, and it is unchanged this week.
- **A joke marker.** The curator wants the laugh marker used. The theory thread found models read the familiar shape of a joke and fail the fresh one, and Sounding Line's laughter cards run this week. An engine marker waits on those.
- Drive priors, values, and any claim about a channel. Sounding Line's appraisal results are still being rebuilt this week.

## 8. Reporting

`docs/ENGINE_BACK_HALF_2026-11-15.md`, by Sunday 22:00 PST:
1. the scoreboard;
2. the speed table, before and after;
3. what is now default, what is an option, and what is behind a flag;
4. what didn't run, and the step it stopped at.

It carries no questions.

## 9. Pre-mortem

- **EX1 arrives late.** The harness is built on fixtures first, and most of TP1 needs no bench data.
- **The two replays of CoAuthor disagree.** The hash check, the word-length alignment, and the 5% stop.
- **Many variants, one winner.** Three rows are registered before scoring; the rest are labelled exploratory, the winner is chosen by a stated rule, and it is checked on a second corpus.
- **A faster path quietly changes the scores.** Exact agreement where the inputs are identical, the benchmark everywhere else, and new cache names.
- **The 9B model starves Sounding Line.** The 20 GiB gate, and unloading after each run.
- **A good number is read as more than it is.** The scoreboard states the benchmark, the units and the bar beside every figure, and TP4's row says "pilot".

## Sources

- **The theory thread:** the curator's turn of 11 November and the Round 12 messages sent to him (results, laughter, short takes, surprises, questions).
- **This branch, at `5f3ad0a`:** `engine/tompathy_engine/preview/readers.py`, `surface.py`, `judgments.py`, `makers.py`, `habits.py`; `engine/tompathy_engine/packet/contract.py`; `engine/tompathy_engine/eval/census.py`; `engine/tompathy_engine/adapters/replay.py`; `docs/PERFORMANCE.md`, `docs/DRIVER_IMPLEMENTATION.md`, `docs/CPU_REFRESH_2026-10-17.md`, `docs/ENGINE_V1.md`, `STATUS.md`.
- **Sounding Line:** the back-half packet of 11 November (exports EX1 to EX4); D33 (Week 4); GO3 (Week 5).
- **Ghost:** V27's K6; the V28 packet and pre-flight of 11 November.
- **The theory handoff:** `claude/THEORY_HANDOFF_2026-11-11.md` (Round 12).
- **The curator's message of 11 November 2026, 08:03 PST.**
- **Outside:** [PyTorch quantization documentation, version 2.1](https://docs.pytorch.org/2.1/quantization.html).
