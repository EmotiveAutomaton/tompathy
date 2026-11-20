# ToMpathy 0.3 engine: two-day packet

12 November 2026. For the agent on `codex/0.3-engine`. Sized for 13 and 14 November at the host's limit of two numerical threads. It continues `TOMPATHY_0.3_ENGINE_BACK_HALF_PACKET_2026-11-11.md`; nothing there is withdrawn unless section 1 says so. Working record: `docs/ENGINE_TWO_DAY_2026-11-14.md`.

This is a spec sheet. It carries no questions for the owner. Choices are made here and listed in section 1.

## 0. Read first

**Sources.** The branch at `2e36d89`: `docs/ENGINE_BACK_HALF_2026-11-15.md`, `docs/ENGINE_SCOREBOARD.md`, `STATUS.md`, the two GO1 handoff notes. The Round 13, 14 and 15 theory handoffs and the theory thread for 11 and 12 November. Sounding Line at `8c81299a5` and Ghost V28's return. Three capped lookups by a cheaper model; facts that rest on them say how they were read.

**Where the engine stands.**

| Item | State on 12 November |
|---|---|
| Benchmark harnesses TP2, TP5, TP3, TP4 | Built and tested. All four scoreboard rows read "not run": the exports had not arrived when the harness was finished |
| Exports | Sounding Line records EX1, EX2 and EX3 as copied to this machine with matching hashes on the evening of the 11th. EX4 is still to come |
| Speed, 3,000 words | Float32 with cache reuse: 67.35 s on one thread and 51.66 s on two, against 152.88 s and 100.70 s for the old window. Word ranks agree at 0.9988 |
| Int8 with cache reuse | 28.38 s on one thread, and it failed parity: rank agreement 0.859, and the same 511 tokens scored differently after a 512-token and a 1,024-token pass |
| Goal reading, from Sounding Line | On 1,431 proposals, word matching picked the stated motivation 0.906 of the time and an embedding reader 0.551; with other-category decoys, 0.929 and 0.588 |
| History, from Ghost V28 | With 16 earlier documents a one-pass reader that knows the maker's own history came within 0.05 nats of the joint reader in 8 of 12 constructed settings; extra passes over one page lost 0.36 to 1.80 nats |

**What the owner asked for.** On 11 November: "We want accuracy and speed... at the very least the engine should start to gain some of the powers if those powers are useful." In the theory thread: "I bet we could actually do pretty well in robustness as well", "we would need to have to be a public one for latent preferences", and, on the surface-word baseline, "It'd be hard to beat surface statistics". On 12 November: look for "any opportunity to improve upon the engine", "making it faster, smarter or better in some way."

**Standing rules.** One scoring process at a time, at most two numerical threads, below-normal priority. The 9B reader loads only past the 20 GiB memory gate, on a service this session owns. No GPU, no paid or remote model calls. Defaults do not change in this packet: every new path is a flag, and the `field-tested` label stays off. Receipts carry exact reader, code and data pins. A failed research gate is a result and stays disabled.

## 1. Choices made here

- **Run before build.** The first day goes to the four benchmarks that are built and unrun. A scoreboard with numbers is worth more than a fifth harness.
- **No model is downloaded.** The faster reader in TP1b is made on this machine from the weights already pinned. The vendor's ready-made files exist ([Qwen's GGUF repository](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF); read by a helper) and are not used.
- **Two public benchmark sets are downloaded by this agent** into `.local/bench/`, never committed: a bounded subset of RAID (MIT licence) and the human-labelled IteraTeR sentences (Apache 2.0). Record source, licence, row ids and hashes.
- **Packages.** `llama-cpp-python` with llama.cpp's conversion script and the `gguf` package, or `onnxruntime` with `optimum`; and `datasets`. All pinned and recorded. If neither runtime installs without a system change, TP1b records that and stops.
- **Every purpose or goal row shows a word-matching baseline beside it.** Sounding Line's two results make word overlap the bar on stated purpose.
- **One pass, more history.** No second pass over a single page is built. Ghost's result is constructed-tested only, and TP2's ladder is its test on people.
- **The standing-from-a-pair benchmark waits** for Sounding Line's CP1 and its export EX6. If CP1 does not support, it is not built.

## 2. Day one: the four benchmarks that are built

Run in this order. Each ends with its scoreboard row filled or with the gate that stopped it.

### TP2. Attention marks against real stops (EX1; then EX4 when it arrives)

As specified on 11 November: the registered primary, her-history row and hers-against-someone-else's row, with baselines fitted inside writer folds and paired whole-writer resampling. Use the registered window reader in float32 first. Then one rerun with float32 cache reuse and the `binding-parity` command: same labels, folds and word eligibility, primary within 0.005.

**Added: the history ladder.** The her-history row is rerun with K = 0, 1, 2, 4, 8 and 16 strictly earlier sessions by the same writer, in order of time. Report the curve with whole-writer intervals and the number of writers at each rung. It is exploratory and changes no primary. Ghost's constructed worlds put the useful history at about 16 documents; this says where it falls for people.

**Added: the reader ladder.** The primary once more with SmolLM2-360M as the only reader. If its result is within 0.01 of Qwen2.5-0.5B's, record it as a candidate first-paint reader (TP1b). No default changes.

### TP5. AI involvement at sentence level (EX1)

As specified. Its row keeps the scoreboard's caveat: accepted suggestions from a 2021 model, and nothing about modern whole-document detection.

### TP3. Edit reasons (EX2)

As specified: the feature classifier first; then the first 50 Q8 calls and their timing projection; then the remaining calls only if the projection is under six hours and the memory gate holds.

### TP4. Goals from departures, 40-document pilot (EX3)

As specified, with one added row.

**Added: word matching first, the reader second.** Rank candidates by the candidate-only TF-IDF row. Then let the 9B goal reading re-rank only the top five. Report top-1 for TF-IDF alone, for the reader alone, and for the re-rank. The question is whether the reader adds anything once word overlap has done its part. The pilot's eight-hour ceiling stands; this row is dropped first if time runs short.

## 3. Day two: faster

### TP1b. A reader that is fast and gives the same answer whatever the pass

**Why int8 failed.** Dynamic quantization sets the scale of each layer's activations from the range it sees in that forward pass ([ONNX Runtime's description](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html); read by a helper through a summary. PyTorch's own page was not verified). A longer pass sees a different range, so the same token gets a different loss. The fix is a path that quantizes weights only, with nothing calibrated per pass.

**Two routes. Build W1; build W2 only if W1 cannot be installed.**

- **W1, llama.cpp.** Convert the pinned Qwen2.5-0.5B weights on this machine to GGUF at 16-bit float and at Q8_0, with llama.cpp's own conversion script at a pinned tag (a Python script that needs the `gguf` package; as the analyst recalls, it writes both types directly, which the build should verify). If the script or the runtime cannot be had without a system change, W1 stops there. Score through `llama-cpp-python` with `logits_all=True` ([API reference](https://llama-cpp-python.readthedocs.io/en/latest/api-reference/); read by a helper), feeding the engine's own token ids and reusing the cache across blocks as the float32 path does.
- **W2, ONNX Runtime.** Export the same weights with `optimum`, then apply weight-only block quantization (the `MatMulNBits` route in the page above) at 8 bits.

**Gates, in this order. A failed gate stops the route and is recorded in a new receipt, `engine/validation/speed-weightonly-2026-11.json`. The old speed receipt is not resumed.**

| Gate | Test | Pass |
|---|---|---|
| a. Same tokens | The runtime's vocabulary table against the engine tokenizer's, id by id; the ids fed are the engine's | identical |
| b. Same answers | Word surprisal on the three frozen texts against the float32 window reference | rank agreement at least 0.98 and median absolute difference at most 0.05 nats (float32 cache reuse scored 0.014) |
| c. Same answer whatever the pass | The first 511 next-token losses after a 512-token pass and after a 1,024-token pass | every difference under 0.001 nats |
| d. Speed | Scoring seconds per 3,000 words at one and two threads, load time apart | recorded; the target is 15 s on two threads |
| e. Same science | TP2's primary with this reader, through `binding-parity` | within 0.005 of the float32 result |

llama.cpp's own perplexity tool can compare a quantized file with saved full-precision logits, token by token ([its README](https://github.com/ggml-org/llama.cpp/blob/master/tools/perplexity/README.md); read by a helper). Use it as a second check on gate b if it is at hand.

**If all five pass:** the route becomes selectable as `--preview-precision w8` beside the existing flag. The default stays where it is.

**First paint.** Whatever the route, record two more numbers for each of the three texts: seconds until the first 600 words are scored, and seconds for the whole text. The float32 cache-reuse path already scores 600 words in 6.68 s on two threads. If TP2's reader ladder found the 360M reader within 0.01, record the same two numbers for it. A panel that fills from the top in a few seconds and finishes in the background may meet the owner's "faster" sooner than any quantization does; this packet measures it and builds nothing in the interface.

## 4. Day two: smarter

### TP6. Robustness of the AI-involvement signals on a public benchmark

**Why.** The owner: "I bet we could actually do pretty well in robustness as well." Round 14 carried a "detection stab" with false alarms on formulaic and non-native writing as the worry.

**Data.** RAID: over 10 million documents from 11 generators in 11 genres with a set of adversarial attacks; the metric is accuracy at a fixed false-alarm rate, 5% by default; MIT licence; the training split is labelled and public and the test split is leaderboard-only ([repository](https://github.com/liamdugan/raid); read by a helper through a summary). Use the training split, streamed, and stop when these quotas fill in file order:

- 800 human documents, 100 from each of the eight main genres;
- 800 machine documents without attack, 100 per genre, at most 12 per generator per genre;
- 300 attacked documents for each of three attacks: homoglyph, zero-width space, paraphrase.

If streaming fails, the download is capped at 6 GB. Record every row id.

**Signals,** all from one forward pass of the small reader, which already yields entropy as a benchmark output:

- A0, mean surprisal, and A1, evenness, as TP5 defines them;
- FD, the analytic form of the curvature test: the sum of token log-probabilities plus the sum of per-position entropies, divided by the square root of the summed per-position variance of log-probability. It is the test of [Bao et al. 2024](https://arxiv.org/abs/2310.05130) with one model as both sampler and scorer.

**Normalization.** Each signal is scored twice on the attacked sets: on the text as given, and after Unicode compatibility folding, removal of zero-width characters, a confusable-character map and whitespace collapse.

**Protocol.** Split the human documents in half by hash. Set each signal's threshold at 5% false alarms on one half. Report on the other half and on all machine documents: detection rate at that threshold, by genre, by generator and by attack, with and without normalization; and the false-alarm rate by genre, where recipes and abstracts stand in for formulaic writing. Give every rate its interval. The held-out half has 50 human documents per genre, so a false-alarm rate by genre is good to about six points either way; the headline pools genres.

**Non-native writing.** A published set of essays by non-native writers showed detectors "[consistently misclassify non-native English writing samples as AI-generated](https://arxiv.org/abs/2304.02819)" (abstract). If that set can be fetched with a stated licence, report the false-alarm rate on it at the RAID threshold. If not, record that and move on.

**Scoreboard.** One new row, "ai-robustness (pilot)", with no bar and the caveat that it reads signals and admits no detector. For context only: small readers can be the better zero-shot detectors (a 125-million-parameter model reached an area of 0.81 where a 6-billion one reached 0.45, [Mireshghallah et al.](https://arxiv.org/abs/2305.09859), abstract), and the strongest published two-model score reports over 90% detection at a 0.01% false-alarm rate on its own test ([Hans et al. 2024](https://arxiv.org/abs/2401.12070), abstract) with far larger models.

**Time.** About five hours of scoring. Ceiling eight.

### TP7. Choice from attention (EX5, a public test of what the maker cares about)

**Why.** The owner asked for a public test for latent preferences. Stated purpose turned out to be a word-matching task. A choice is harder to fake with shared vocabulary: an asker reads several answers and accepts one. If the engine's attention marks on the question find what the asker cared about, weighting by them should pick the accepted answer more often than plain overlap does.

**Data.** Sounding Line's EX5: 2,000 questions from five public sites, each with 3 to 8 answers and an accepted one that is not the asker's own.

**Rows,** each ranking a question's answers:

| Row | Rule |
|---|---|
| B0 | Final score. Shown for scale only: acceptance itself raises an answer's later score |
| B1 | Posted first |
| B2 | Longest |
| B3 | TF-IDF cosine between question and answer |
| B4 | B3 with the rarity weight squared |
| B5 | B3 with each question word's weight multiplied by its surprisal under plain word frequency, with no context |
| E1 | B3 with each question word's weight multiplied by the small reader's surprisal for that word in the question (content words only) |
| E2 | On a hash-chosen 150 questions: one 9B goal reading of the question through the single-call function, then TF-IDF between that reading and each answer |

**One primary.** E1 minus the best of B3, B4 and B5 in top-1 accuracy, paired by question, resampled within site. Bar +0.02. B4 and B5 are there because a reader's surprisal partly tracks plain rarity, which TF-IDF already rewards; E1 has to beat rarity to count. Also report mean reciprocal rank, and everything again on the questions whose accepted answer is not the top-scored one.

**By construction.** Every answer is about the question, so all candidates overlap with it. A result here is about a choice among answers and is not a reading of values.

**Scoreboard.** A new row, "choice (pilot)".

**Time.** About two hours for E1; about seven for E2 if the memory gate holds. E2 is dropped first.

### TP9. Edit reasons against human labels

**Why.** The back-half return parked the edit-reason habit test because "comment-derived labels cannot establish personal habit". A human-labelled set gives Q8 its first check that does not lean on editors' own summaries.

**Data.** IteraTeR's human-annotated sentence pairs, with five intentions: clarity, fluency, coherence, style and meaning-changed; Apache 2.0 ([repository](https://github.com/vipulraheja/IteraTeR); read by a helper).

**Frozen mapping from Q8's nine labels.** typo and grammar to fluency; wording to clarity; reorder to coherence; tone to style; add content and remove content to meaning-changed; format and unclear count as abstentions.

**Rows.** The majority label. TP3's feature classifier, trained on EX2 only, through the mapping. Q8 direct on a hash-chosen balanced 300 pairs, 60 per intention, with the first 50 calls projected as in TP3.

**Metric.** Macro-F1 over the five intentions, with abstentions counted as errors and also reported apart. No bar. The row joins "edit-reasons" on the scoreboard as its human-labelled line.

**Time.** About an hour and a half of 9B calls.

## 5. Day two: a shape for the bottom box

### TS1. A default-off schema, and nothing that fills it

**Why.** The owner: "I kind of want to imagine to use echoes of that shape and picture to design the bottom box of tompathy", and on the 11th, "I'll hook up the front end once we have a better shape for what the front end looks like". The engine can offer the shape without claiming a reading.

**What.** An optional `bottom_box` object in the packet contract, version `bottom-box-0`, absent unless a flag asks for it:

- `set_points`: knowledge, tending, belonging, seen_as_competent, seen_as_kind;
- `body`: warmth, food, sleep;
- `readings`: stress, freedom;
- `hub`: a label or null;
- `channels`: SEEKING, FEAR, RAGE, PANIC_GRIEF, CARE, PLAY, LUST, DISGUST, SHAME.

Every entry is `{value: null, evidence: [], status: "unvalidated", ledgerRows: []}`. There is no producer. The names are the ones Round 15 lists as safe to build on. The three reads, level, slope and jump, and the Big Five mapping are not in it, because they await the owner's ruling.

**Checks.** Contract tests; the frontend's schema still accepts every existing packet fixture; one new fixture with an empty bottom box. No frontend file changes.

## 6. Order, time and what to drop

| Slot | Work | Scoring hours (estimate) |
|---|---|---|
| Day 1 | TP2 with both ladders, TP5 | 8 to 12 |
| Day 1 | TP3: features, 50 calls, projection | 1 |
| Day 1 into night | TP3's remaining calls or TP4's pilot, whichever the memory gate allows | 5 to 8 |
| Day 2 | TP1b gates a to d, first paint | 3 |
| Day 2 | TP6 | 5 |
| Day 2 | TP7 E1, then TP9, then TP7 E2 | 2, 1.5, 7 |
| Beside scoring | TS1; the TP1b build; the TP6, TP7 and TP9 runners | none |

Code work proceeds beside a scoring run. If time runs short, drop in this order: TP7's E2, TP4's re-rank row, TP9's Q8 calls, TP6's paraphrase set. Never drop a parity gate.

**When blocked** on a memory gate or a missing export: TP2's ladders at more rungs; TP6 with the 360M reader; the working record.

## 7. The return

- `docs/ENGINE_SCOREBOARD.md`: four rows filled or stopped with a named gate, plus "ai-robustness (pilot)" and "choice (pilot)" and the human-labelled line under edit-reasons.
- `docs/ENGINE_TWO_DAY_2026-11-14.md`: what ran, what stopped and why, in the back-half note's form.
- For the theory thread, five lines: where her own history starts to pay (TP2's ladder); whether attention marks find what an asker cares about (TP7); whether the reader adds to word overlap on purpose (TP4's re-rank); how the signals hold under attack (TP6); how fast a parity-safe reader is (TP1b).

## 8. Limits

- TP5 and TP6 read signals. Neither admits a detector, and no field label turns on.
- TP7's ground truth is one person's click. It tests whether marks find what that person weighed, and says nothing about set points.
- TP9's intentions are annotators' judgments of other people's edits.
- TS1 is a container. Shipping it claims nothing.
