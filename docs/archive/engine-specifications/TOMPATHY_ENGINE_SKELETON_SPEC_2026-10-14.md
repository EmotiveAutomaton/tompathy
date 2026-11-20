# ToMpathy 0.3 spec: engine skeleton and frontend integration, 14 October 2026

**What this is.** The full build spec for ToMpathy 0.3, for the curator's ToMpathy thread. The engine is built in an `engine/` folder inside the ToMpathy repository, on a 0.3 feature branch, together with the frontend changes that connect it. It covers:
- where ToMpathy stands;
- the architecture;
- the data model, and each module with its math in plain words;
- the mapping onto the packet schema;
- the global tab;
- the first readings to publish;
- the service and the evaluation hooks;
- milestones with acceptance tests, and a pre-mortem.

This document specifies; it does not run anything.

**As of 14 October 2026, 20:15 PDT.**
- **ToMpathy app: 0.2 beta, frontend complete** (curator, 14 October). The engine lands in **0.3** on a feature branch.
  - The public `main` read on 14 October (`07dc29bb`) still calls itself 0.1 beta. Push 0.2 before branching, so the engine thread starts from it.
- **Two version numbers, not to be confused:**
  - the **app version**: 0.2 now, 0.3 with the engine;
  - the **packet schema version**: the `schemaVersion` field inside each analysis file. `docs/INPUT_CONTRACT.md` already numbers it 1.0 to 1.4. This spec adds **packet schema 1.5**, which ships with app 0.3.
- **Sounding Line** `main` is at `0a956219c`; **Ghost Scale** `main` is at `32ef58e`.
- The results this spec builds on are in `RESULTS_AND_ENGINE_PLAN_2026-10-14.md`.

**Decisions applied (curator, 14 October, 20:00 PDT):**
- the engine lives in `tompathy/engine/`;
- packet schema 1.5, with the population block, is in scope for 0.3;
- the analyst chooses the first readings (section 10.6).

Remaining choices are set as defaults (section 16).

**Companion specs.**
- `SOUNDING_LINE_NEXT_ROUND_SPEC_2026-10-14.md`: the research program that tests these modules.
- `GHOST_SCALE_NEXT_ROUND_SPEC_2026-10-14.md`: the constructed worlds that emit the same data model, so every module can be checked against known truth.

---

## 1. Where ToMpathy stands (read on 14 October)

**What exists.**
- **Form.**
  - A Chrome Manifest V3 side-panel extension: React 19, TypeScript, zod validation, d3 layout.
  - MIT licensed; distributed as a GitHub ZIP.
  - App 0.2 beta per the curator. The public `main` read here still shows the 0.1 beta of 12 October.
- **Three views:**
  - Current attention, an animated word cloud;
  - Expertise, Habits, and Process, a goal hierarchy with reels;
  - Core values, the top nine hypotheses by normalized support, each with a support wheel and evidence on hover.
- **The values panel has two tabs, "author" and "global".** Global and search are interface previews; no data sits behind them.
- **Packet schema** (the format of an analysis file, versioned separately from the app).
  - Versions 1.0 to 1.4 are validated at runtime by `src/core/model.ts` (`PacketSchema`), and `docs/INPUT_CONTRACT.md` documents them.
  - Packets carry:
    - an artifact snapshot with region anchors (UTF-16 offsets, SHA-256 revision);
    - makers;
    - hypotheses of kind `goal`, `process`, `value` or `attention`;
    - support objects with explicit `relative` or `probability` semantics;
    - alternatives, process graph, goal hierarchy, attention frames, accounts, evidence, revision lineage.
  - The validator rejects a probability without a candidate set, an exhaustive probability set that doesn't sum to one, dangling IDs and cycles.
- **Provider stub.**
  - `src/core/provider.ts` declares `InferenceProvider.analyze(AnalysisRequest): Promise<Packet>`.
  - `configuredProvider` is `null`. Ordinary pages wait for "an analysis source".
- **Sounding Line link.**
  - The only existing bridge is `runners/stage13/export_tompathy.py`, an offline 1.0 exporter.
  - It emits mostly unknown values and empty process graphs.
- **Privacy posture.**
  - No telemetry, no inference server, no account.
  - Page text stays in session storage.
  - Context retrieval is bounded and opt-in.
  - A future backend "will require updated behavior disclosures before release".
- **Curator intent (stated 13 October).**
  - ToMpathy is the public face of the research.
  - It is free.
  - Reading targets, in order:
    1. his own essay;
    2. essays in public git repositories with visible history;
    3. Wikipedia, late game.
  - The values display should convey anti-capture: credible value estimates need data from many people.

**What the backend must supply, from the frontend's point of view.**
1. A packet that validates against `PacketSchema`, bound to the exact captured artifact (same revision hash and anchors).
2. Makers that are never merged by name.
3. Values and goals as hypotheses with honest support semantics: relative unless calibrated.
4. Attention frames only when there is evidence about attention.
5. A goal hierarchy whose nodes cover real regions.
6. Evidence items that point at real sources.
7. Data for the global tab, which packet schema 1.4 does not define (section 9 adds it in 1.5).

**The structural fact that shapes everything below.**
- **Most web pages carry only final text.** The engine's validated strength is in production records: decisions, options, timing, corrections.
- **So the engine works in three evidence tiers, and must say which tier a reading came from:**

| Tier | What exists | Examples | What the engine can honestly say |
|---|---|---|---|
| **T0** | Final text only | Most articles, the curator's essay as published | Text-level hypotheses with weak support; population prior dominates the values box |
| **T1** | Revision history | Git-hosted essays, Wikipedia articles, Google Docs exports | Process (what changed, in what order), corrections, stated purposes (commit messages, edit summaries) |
| **T2** | Full process log | CoAuthor sessions, any instrumented editor | Decisions among offered options, timing, attention traces, corrections at keystroke level |

---

## 2. Architecture

### 2.1 The split, and where the engine lives

**The split (curator, walkthrough I).** Sounding Line stays the test environment and writes specs; ToMpathy implements them, in its own thread.

**One engine, not two (analyst amendment, kept).** If Sounding Line validated one implementation and ToMpathy shipped another, the shipped engine would be unvalidated within weeks.

**Where it lives: `tompathy/engine/` (curator, 14 October, 20:00).** It is a Python package inside the ToMpathy repository, on the 0.3 feature branch.
1. Sounding Line imports the engine from a pinned ToMpathy commit for every card that evaluates an engine module.
2. Ghost Scale emits the engine's data model, so the same module code runs on constructed worlds.
3. Every packet records the engine version (the ToMpathy commit) and the admission record of each module that contributed.

**Keeping one repository clean.**
- **Separate builds.** `engine/` has its own `pyproject.toml`; the extension build (`scripts/build.mjs`) never touches it.
- **Code only.** No datasets, model weights or ledgers are committed. `engine/` holds code, fixtures and schemas; raw data stays in a local data directory outside the repository.
- **Two CI jobs:**
  - the existing Node checks;
  - a Python job for `engine/`, which also validates every engine fixture packet with the extension's own `PacketSchema`.
- **License.** The repository stays MIT. Research-only dependencies sit behind an optional extra (`pip install -e "engine[research]"`).

### 2.2 Deployment ladder

| Stage | How a reading reaches the extension | Cost | Privacy | When |
|---|---|---|---|---|
| **D0, offline registry** | The engine analyzes chosen artifacts in batch and publishes packets as static JSON on GitHub Pages. The extension looks up the current page's artifact ID and revision | Free | The registry host sees which hashed artifact was requested; mitigate with prefix buckets (section 10.2) | First |
| **D1, local companion** | `tompathy-engine serve` runs on the reader's machine; the extension calls `http://127.0.0.1:<port>` with a session token | Free; uses the reader's CPU or GPU | Text never leaves the machine | Second |
| **D2, hosted** | A server the curator operates | Costs money | Text leaves the machine | Not planned; only if the curator chooses |

**D0 is the right first target.**
- It is free and needs no install for readers.
- It fits the curator's reading targets: his essay, chosen git-hosted essays, chosen Wikipedia articles.
- It lets the global tab ship with real population data from day one.

---

## 3. Data model: the decision ledger

Everything the engine reads becomes rows in one append-only ledger. Sounding Line's adapters already do a version of this for CoAuthor; the ledger generalizes it. **Ghost Scale emits exactly these record types** (its spec, Part B), with a truth sidecar that readers never see.

### 3.1 Record types

All IDs are strings. Content IDs are SHA-256 hex digests of canonical JSON (sorted keys, UTF-8). Times are ISO 8601 UTC; durations are seconds.

```text
Maker          maker_id, source_dataset, identity: unknown|pseudonymous|supplied|synthetic,
               display_label, identity_basis
Artifact       artifact_id, maker_ids[], kind: essay|article|code|game|session|other,
               source_uri, revisions[revision_id], tier: T0|T1|T2
Revision       revision_id, artifact_id, parent_revision_ids[], maker_id, t,
               content_ref, stated_goal_ids[]
Session        session_id, maker_id, artifact_id, t_start, t_end, stated_goal_ids[]
StatedGoal     goal_id, maker_id, scope: session|artifact|revision|decision,
               text, source: prompt|edit_summary|commit_message|assignment|title|request, t
StatedPreference  pref_id, maker_id, attribute, value, scale, source: survey|profile|self_description, t
Decision       decision_id, maker_id, session_id, t_open, t_resolve,
               options[ {option_id, origin: maker|ai|system|env, content_ref, position, features{}} ],
               taken: option_id | null, action: accept|edit|dismiss|ignore|write|delete|revise|move|submit|rate|choose,
               cost{ latency_s, keystrokes, chars_typed, time_left_s },
               context{ ... }, outcome{ ... }
Correction     correction_id, maker_id, decision_id | null, revision_id | null,
               span{region, start, end} | null, before_ref, after_ref, t, stated_reason | null
ContextEvent   event_id, session_id, t, kind: clock|opponent_move|environment|prime|other, payload{}
Evidence       evidence_id, source_uri, excerpt, captured_at, relationship
Provenance     record_id, adapter, adapter_version, source_file_sha256, created_at
```

**Notes on the types.**
- `StatedPreference` is the one addition beyond the Ghost brief. It carries survey answers (PRISM), stated predictions (MovieLens Beliefs) and personality scales (PARA, Persuasion for Good). Ghost should add it for its stated-versus-revealed family (N7).
- `content_ref` points into a content-addressed text store, so the same suggestion or paragraph is stored once.
- A `Decision` with one implicit option ("keep writing") is allowed. Revision histories without offered alternatives become `Correction` rows rather than invented options.

### 3.2 Storage

- Parquet files per record type, queried through DuckDB. Content store: a directory of zstd-compressed text blobs keyed by SHA-256.
- Append-only. A correction to a record is a new record with a `supersedes` field; nothing is rewritten. This follows Ghost V21's finding: a compressed predictor loses historical witnesses, and a ledger keeps them.
- Every row has a `Provenance` row. Raw human text from licensed datasets stays local; only derived aggregates and packets for public artifacts are published.

### 3.3 Identity rules (from the frontend contract, kept)

- Makers are never merged by name or display string.
- A maker ID is scoped to its source:
  - `coauthor:<worker>`;
  - `wikipedia:<user_id>`;
  - `git:<sha256(email)>`;
  - `lichess:<username>`.
- Cross-source identity needs explicit evidence: a profile link the maker published. That evidence is recorded in `identity_basis`.

---

## 4. Ingest adapters (record compilers)

Each adapter turns one source into ledger rows. It ships with fixtures that replay exactly, and it refuses malformed input rather than guessing.

| Adapter | Source | Produces | Port from | Acceptance |
|---|---|---|---|---|
| **A-coauthor** | CoAuthor JSONL event logs plus metadata | Sessions; StatedGoal (the assigned prompt); Decisions per suggestion opening (options are the offered suggestions plus a "write my own" option; action is accept, edit, dismiss or ignore); cost (`decide_seconds` from open to select or close; characters typed after); Corrections (user edits inside an accepted suggestion's span) | Sounding Line `runners/stage11/replay.py`, `runners/stage9/coauthor.py`, `runners/stage14/records.py` | Replays all 1,445 sessions; reproduces Sounding Line's census (16,959 usable opportunities, 39 excluded, 61 writers); 64 constructed fixtures exact |
| **A-git** | A public repository and file path | Revisions (commits touching the file); Corrections (diff hunks); StatedGoal (commit message, `source=commit_message`); maker (hashed author email) | Sounding Line `runners/stage14/public_git.py` | Byte-exact reconstruction of every revision from the diff chain; license allowlist enforced |
| **A-wiki** | Wikipedia revisions via dumps (bulk) or the API (single article; one connection, about 100 ms between requests) | Revisions; Corrections; StatedGoal (edit summary; about 54% of English edits have one); Outcome (reverted within 48 hours as a policy-error proxy); bot flag | New | Reconstruct each revision; summary coverage reported per editor; IP editors flagged as unstable identity |
| **A-capture** | A ToMpathy capture (artifact plus regions) | Artifact, tier T0; no decisions | ToMpathy `src/core/artifact.ts` rules | Recomputes the revision hash and anchors exactly as the extension does (UTF-16, `\s+` collapse, `\n\n` join) |
| **A-lichess** | PGN with `%clk` comments (clock data since April 2017) | Decisions per move (options are legal moves with engine evaluations where available); cost (`time_left_s`, latency from clock deltas); StatedGoal "win" (`source=assignment`); Outcome (result) | New; Maia-2 code for move encoding | Clock parsing verified on fixtures; engine-evaluation coverage reported |
| **A-panel** | Preference datasets: Community Alignment, PRISM, MultiPref, DICES, summarize_from_feedback, MovieLens Beliefs | Decisions (each comparison or rating; options are the responses); cost (time spent where present); StatedPreference (PRISM survey, MovieLens predicted rating and certainty); StatedGoal (prompts written by the annotator) | New | Row counts match dataset cards; per-person depth histogram reported |

**Why each adapter is in the skeleton.**
- **A-coauthor** is the only full T2 source.
- **A-git and A-wiki** cover T1 and the curator's reading targets.
- **A-capture** covers T0.
- **A-lichess and A-panel** give deep histories and ground truth for evaluation. They are not product inputs at first.

---

## 5. Features

Two feature sources feed every model. Deterministic features come first, because they cannot hallucinate.

### 5.1 Deterministic features (no model calls)

For each option or correction, computed against its context:
- **Length and position:** characters, tokens, position in the menu.
- **Overlap:** word overlap and character n-gram overlap with the preceding text. This is the feature the partial-pooling baseline already uses.
- **Embedding similarity:** cosine similarity to the last sentence and to the document, using MiniLM. Sounding Line already encoded 76,891 CoAuthor texts with a 128-token cap; reuse those encodings and record the cap.
- **Named entities:** counts, and new versus already-seen entities (spaCy small model).
- **Edit shape:** insertion, deletion or replacement; size; whether the change is confined to one sentence.
- **Timing, where present:**
  - latency;
  - latency relative to the maker's running median for that decision type;
  - pause before and after;
  - time left (chess).

### 5.2 The transcriber: literal LLM features, one question per call

**The rule that came out of Stage 14.**
- **What works:** asking one literal question per call and composing the answers in code. That passed 64 of 64 constructed records.
- **What fails:** asking for whole records or for probabilities about people. Small models' answers to a statement and its negation missed summing to one by 0.20 to 0.64. The 27B reader lost to base rates by 0.078.
- **So the transcriber answers questions about text, never about the maker.**

**Contract.**
- **Input:** `question_id`, the context window (up to 1,200 characters before), the option or edit text, and the answer set.
- **Output:** exactly one label from the answer set, plus `unclear`, as JSON enforced by constrained decoding (llama.cpp grammar, Ollama `format`, or vLLM guided JSON).
- **Settings:** temperature 0, fixed seed, token log-probabilities recorded where the backend exposes them.
- **Cache:** keyed by `sha256(model_id, template_version, question_id, inputs)`. A cache hit never calls the model.
- **Backends:**
  - a local Ollama or llama.cpp model (Llama 3.1 8B passed the factorized gate);
  - an OpenAI-compatible endpoint for Gear 3 runs;
  - later, Chrome's built-in Prompt API in the extension.

**Question catalogue v0.** Each question must pass its own admission battery before it is enabled.

| ID | Question (literal) | Answers | Applies to |
|---|---|---|---|
| Q1 | Does this text continue the topic of the last sentence? | yes / no / unclear | options |
| Q2 | Does this text introduce a person, place or object not mentioned before? | yes / no | options |
| Q3 | Register of this text | formal / neutral / casual | options, revisions |
| Q4 | Compared with the last sentence, is this text more positive, the same, or more negative in tone? | more positive / same / more negative | options |
| Q5 | Does this text contain dialogue? | yes / no | options |
| Q6 | Grammatical person | first / second / third / mixed | options |
| Q7 | Does this text contradict a statement earlier in the document? | yes / no / unclear | options |
| Q8 | Edit type | typo / grammar / wording / add content / remove content / reorder / tone / format | corrections |
| Q9 | Does the edit change what the sentence claims? | yes / no | corrections |
| Q10 | Theme tags present (multi-select from a fixed list: danger, care, play or humor, conflict, loss or separation, desire, discovery, status, food or body) | subset | options, revisions |

**Admission battery per question.**
- **The test.** 200 constructed items with known answers, drawn from the same text sources, including negation and paraphrase pairs.
- **The bar:**
  - at least 95% valid outputs;
  - accuracy at least 0.85 on yes/no questions;
  - agreement at least 0.8 with a deterministic cross-check where one exists (Q2 against spaCy entities, Q5 against quote marks, Q6 against pronoun counts).
- **Failure.** A question that fails is disabled, not tuned against its test items.
- **Record.** The battery result becomes an admission record, cited in every packet that used the question.

**Q10 is the riskiest question.** Theme tags describe the text, not the maker. Section 8 explains why they may only enter maker-level estimates through the maker's choices and corrections, never directly.

---

## 6. Models

**Plain-language variables used throughout.**
- *i* indexes a decision.
- *m* indexes a maker.
- *j* and *k* index the options in a decision.
- *x_ij* is the feature vector of option *j* in decision *i*.
- A "utility" is a score the model assigns to an option; higher means more likely to be taken.

### 6.1 Backbone: population model plus partial pooling

This is the one component that beat base rates on real records: +0.016 half-Brier, holding across writers. Every other module must beat it under the same harness, or stay off.

**Choice rule** (multinomial logit over the options actually offered):

$$P(\text{taken}_i = j \mid m) = \frac{\exp\big(\lambda_m\, x_{ij}^{\top}(\beta + u_m)\big)}{\sum_{k \in O_i} \exp\big(\lambda_m\, x_{ik}^{\top}(\beta + u_m)\big)}$$

- *β* (beta) holds the population weights: how much the average maker cares about each feature.
- *u_m* is maker *m*'s personal offset from the population.
- *λ_m* (lambda) is maker *m*'s consistency: how sharply their choices follow their utilities. High means predictable, low means close to random among options. This is the analogue of Regan and Haworth's consistency parameter for chess players (2011), and ToMpathy should display it as **predictability**.
- *O_i* is the set of options offered in decision *i*. For handling decisions (accept, edit, dismiss, ignore), the four actions are the options and the features are action indicators interacted with context features. This reproduces Sounding Line's baseline.

**Pooling.**
- *u_m* is drawn around zero with spread *τ* (tau): u_m ~ Normal(0, τ²), with one *τ* per feature group.
- A maker with few decisions stays near the population; a maker with many decisions moves toward their own data.
- The amount of movement is the **shrinkage weight**, roughly n_m τ² / (n_m τ² + σ²), where *n_m* is the maker's number of decisions and *σ²* is the noise in one decision's evidence.
- This is the same arithmetic that makes estimating many means together beat estimating each alone (James and Stein, 1961; Efron and Morris, 1977). The gain is in total error across makers; any single maker's estimate can get worse.

**Prototype variant (few-shot start).**
- **The model.** u_m is a weighted mix of *K* prototype vectors plus a small residual. A new maker's mix is estimated from their first few decisions.
- **Why.** This is the Maia4All recipe: it reached individual gains at 20 chess games where plain fine-tuning needed 5,000 (Tang et al., 2026).
- **Size of the gain.** It was small: 1.8 points of move accuracy at 20 games.

**Fitting.**
- **Fast path:** maximum a posteriori with L-BFGS (the existing Sounding Line code). *τ* is chosen on each maker's earlier calibration slice, as now.
- **Full path:** NumPyro, with NUTS for small sets and stochastic variational inference for large ones, giving posterior intervals on *u_m* and *λ_m*.
- **Time order.** Every fit takes an `until` time, so prequential scoring (forecast each decision from everything before it) is the default evaluation mode.

**Outputs.**
- Predictive distribution per decision.
- Per maker: posterior mean and interval of *u_m* and *λ_m*, the shrinkage weight, and *n_m*.

### 6.2 Diagnosticity weights (the agreed replacement for a noise bin)

The curator accepted a per-mark weight (walkthrough I, question 4: "how informative is just fine").

**Definition.** For a mark *m* and two preference hypotheses *A* and *B*:

$$d(m) = \left|\ln P(m \mid A) - \ln P(m \mid B)\right|$$

- *d* is near zero when the mark would look the same whatever the maker preferred: a mixed-strategy draw, a near-tie, an unhurried moment, or a choice driven by context the reader cannot see.

**Estimation in the backbone.** Each past decision gets a weight *w_i* between 0 and 1 in the log-likelihood:

$$w_i = \sigma(a + b\, z_i)$$

- *σ* (sigma) is the logistic function.
- *z_i* is decision *i*'s latency, standardized within the maker and decision type.
- *a* and *b* are fitted to maximize held-out log score, cross-fitted by maker.
- **The prediction:** *b* comes out negative, so fast decisions weigh more. Slow choices are the ones people later reverse (Konovalov & Krajbich, 2019), and response times let you recover preferences when choices are noisy (Alós-Ferrer, Fehr & Netzer, 2021).

**Guards.**
- **Don't double count.** Ghost V22 showed that weighting effort which is already in the likelihood double counts it and costs coverage. If latency enters the utilities as a feature, it must not also enter the weights.
- **Shuffled control.** Every run includes weights shuffled within maker. A weighting scheme ships only if it beats the shuffled version by the useful margin.
- **Not the old test.** Typing-effort weighting was tested in Stage 14 and added nothing (+0.0004). Decisiveness weighting is a different variable and is untested.

### 6.3 Corrections module ("improvements are corrections")

**What a correction says.** When a maker changes *before* into *after*, their preference points more toward *after* than *before*. With a linear preference over features *φ* (phi, the feature map from section 5), that is one constraint, a half-space:

$$w_m^{\top}\big(\varphi(\text{after}) - \varphi(\text{before})\big) > 0$$

- *w_m* is maker *m*'s preference direction over features.

**Made probabilistic** (Bayesian logistic regression on differences):

$$P(\text{after} \succ \text{before} \mid w_m) = \sigma\big(\kappa\, w_m^{\top}\Delta\varphi\big)$$

- *κ* (kappa) is how consistently corrections follow the preference.
- **Pooling:** w_m = w_pop + v_m, with v_m pooled like *u_m*.
- **Prior art:** this is coactive learning (Shivaswamy & Joachims, 2015). CIPHER applies the same idea to users' edits of model output (Gao et al., 2024).

**Separating process from preference.**
- Corrections the transcriber labels typo or grammar (Q8), or that don't change the claim (Q9 no), are **process corrections**. They feed the habits and expertise panel, not values.
- Only content, tone, add, remove and reorder corrections feed *w_m*.
- If CoAuthor's corrections turn out to be mostly process corrections, that is a finding about the dataset, not a failure of the module.

**Use in prediction.** *w_m* adds a term to option utilities: utility_ij += w_mᵀ φ(option_j). Sounding Line test T1b asks whether this lifts candidate choice, the task where nothing beats a uniform guess today.

### 6.4 Source trust (Ghost's source-inference module, first real-data port)

**What it models.** In CoAuthor, the AI is a source with a track record inside each session. Ghost V22 showed that inferring a source's reliability and intent beats any fixed trust (by 0.10 to 0.25 nats in constructed worlds), and spots a steering source with eight records.

**v0 model.**
- Each maker's acceptance propensity toward the AI follows a session-level random walk.
- Its steps depend on the observed quality of recent suggestions. Quality proxies:
  - whether an accepted suggestion survived to the end of the session;
  - how much of it was later edited.

**Comparison.** Fixed acceptance rates and a recency-only model.

**Output.** A "trust trajectory" hypothesis per session, shown in the process panel. It is not a value.

**Real steering data for testing.** Jakesch et al. (2023), 1,506 writers with an opinionated model (OSF), and Williams-Ceci et al. (2026), 2,582 participants with prior attitudes measured (Zenodo, CC BY 4.0), planted a steering AI. Sounding Line family F8 tests this module there.

### 6.5 Goal tree with a root cue (top-down entry)

**What Ghost found.** Ghost V22 found that joint top-down and bottom-up reading beats either direction at internal nodes. At the root it only tied bottom-up, because there was no root-level evidence. The curator's "this would cut, so it's a cutting tool" route needs exactly that evidence.

**v0 construction.**
1. **Leaves** are document regions: paragraphs, or sentences for short texts.
2. **Candidate local goals** per region come from the transcriber as labeled hypotheses with relative support. This is a judgment task, so it gets its own admission battery and stays labeled `hypothesis`.
3. **Root cue** is any StatedGoal at artifact scope: title, assigned prompt, commit message, edit summary. Its reliability is a parameter.
4. **Choosing the governing goal:** it must cover every leaf at the smallest depth. That is the curator's "first goal where the artifact's decisions all meet", scored jointly with the root cue.
5. **Hierarchy output** uses `goalHierarchy.nodes` with `parentIds`, as packet schema 1.4 allows.

**Honesty rule.** At tier T0 the tree is an explanatory hook, with status `hypothesis` and relative support. The curator called the attention and expertise boxes "mostly explanatory and a hook".

### 6.6 Calibration layer (for anything that claims a probability)

**Default.** All support is `relative`. A module may emit `probability` only after it passes calibration on held-out makers.

**Methods, in order of preference.**
1. **Temperature scaling** on held-out data.
2. **Prior-shift correction** by EM (Saerens et al., 2002). This removes label bias like the cloud reader's over-prediction of "edit".
3. **Contextual calibration** with content-free inputs (Zhao et al., 2021).
4. **Stacking** of the backbone, the LLM features and other modules on a proper score (Yao et al., 2018).

**Gate.** Expected calibration error below 0.05 and no loss against the backbone on held-out makers. Passing modules carry `calibration` text in the support object, naming the dataset and the error.

---

## 7. From models to ToMpathy's three views

### 7.1 Core values box: drives on top, values beneath

**The curator's spec (walkthrough H).**
- Drives come first, ranked by confidence; everyone has them.
- Values trail beneath, individual and constructed.
- Both carry icons.

**Drives.**
- **The list:** Panksepp's primary systems (SEEKING, RAGE, FEAR, LUST, CARE, PANIC/GRIEF, PLAY) plus Solms's bodily needs.
- **Representation:** a vector *g_m* of drive loadings, initialized at the population mean.

**How drive loadings may move: the affective-fallacy guard.**
- **Forbidden:** "this essay mentions danger, so its maker runs on FEAR". That reads content as motive, the move literary criticism named the affective fallacy (Wimsatt & Beardsley, 1949).
- **Allowed: revealed preference over themed content.**
  - When a maker repeatedly chooses or corrects toward options tagged with a theme (Q10), beyond what the population does, the loading on the matching drive rises.
  - Mapping v0:
    - danger → FEAR;
    - care → CARE;
    - play or humor → PLAY;
    - conflict → RAGE;
    - loss or separation → PANIC/GRIEF;
    - desire → LUST;
    - discovery → SEEKING;
    - food or body → bodily needs.
  - The mapping is many-to-many by design: the curator's "the mapping runs many to many".

**SEEKING.**
- **Default:** model it as **pursuit vigor**, an intercept that scales all pursuit, not as a value dimension. It loads on everything, so as a dimension it would top every profile.
- **Display:** shown with the drives, with a note.
- **Status:** this is the analyst's proposal from 14 October. The curator said SEEKING is not special in kind; the intercept treatment is about position, not kind.

**Values.**
- **What they are:** sparse recipes over drives plus the maker's preference directions *w_m* from corrections and choices.
- **v0:**
  1. Take the posterior of *w_m*.
  2. Keep directions whose interval excludes zero.
  3. Label each with a short phrase. The label comes from the transcriber, summarizing the features the direction loads on, for example "prefers concrete detail over abstraction".
  4. Attach recipe weights over drives where the themed choices support them.
- **Labels are judgments.** They stay `hypothesis`, with relative support.

**Mapping to packet schema 1.4.**
- **Kind.** Each drive and value is a hypothesis with `kind: "value"`.
- **Interpretation.** Values take `interpretation: "value"` (or `"preference"` for single-direction findings).
- **Drives need packet schema 1.5** (section 9) to get `interpretation: "drive"` and an icon key.
- **Until then:**
  - drives use `interpretation: "value"`, with a label prefix ("Drive: CARE");
  - the description states that this is an inherited system with a population prior.
- **Ranking in ToMpathy.** The extension shows the top nine by normalized support. Drives come first because their support includes the population term; values follow.

**Support semantics for values.**
- `value` is the posterior probability that the direction or loading is above the population mean, on scale [0, 1].
- `semantics` is `relative`, and `meaning` reads: "Probability-like ranking from a pooled model; not calibrated against stated values."
- `probability` semantics require the stated-versus-revealed calibration in Sounding Line family F5 (PRISM, MovieLens Beliefs).

### 7.2 Expertise, Habits, and Process

**Process.**
- **T1 and T2:** each revision or decision event becomes a process node with `interpretation: "historical-event"`. Edges are `precedes` from the ledger's time order, and `revises` for corrections. `process.interpretation` is `"historical-production"`.
- **T0:** no historical process. The panel shows the goal tree from 6.5 only.

**Habits** (the curator's "all repetition").
- Patterns that recur across a maker's decisions become hypotheses with `kind: "process"`, `interpretation: "repertoire"`:
  - repeated edit types;
  - repeated phrasings;
  - stable acceptance patterns;
  - time-of-day rhythms.

**Expertise** (the intended part of habit).
- **v0 marker:** a repertoire item whose use correlates with outcomes the maker kept, for example edits that survive versus edits reverted on Wikipedia.
- **Label:** "candidate expertise". Expertise is the curator's "intended repetition", and intention is not observed directly.

**Goal hierarchy.** From 6.5.

### 7.3 Current attention

**Only when there is evidence about attention.**
- **T2:**
  - dwell and pause before and around a region;
  - suggestions opened and closed unused;
  - cursor revisits.
  - Each frame's items are attention hypotheses with relative support.
- **T1:** which regions a revision touched and how often, as weak attention evidence. Label it "edit focus", not attention.
- **T0:** omit `currentAttention`. The extension shows "No attention supplied", which is the honest state.

### 7.4 Evidence

Every hypothesis cites evidence items:
- a quoted region from the page;
- a revision diff with its commit message or edit summary;
- a decision summary (for example, "chose suggestion 3 of 5 after 1.2 s; edited the second clause").

Packets never cite Ghost truth, only ledger evidence.

---

## 8. The guard rules, collected

1. **Text describes the artifact; only choices and corrections describe the maker.** No maker-level estimate moves on content alone.
2. **Unknown stays unknown.** Empty arrays and `status: "unknown"` are valid output.
3. **Relative unless calibrated.** Section 6.6.
4. **Never merge makers by name.** Section 3.3.
5. **Every module that contributes to a packet has an admission record** from Sounding Line (real data) or Ghost (constructed truth). The packet lists them in `provider.method`.
6. **Model everyone, gate uptake.**
   - The engine never withdraws modeling of a maker because they look neither warm nor competent (curator, walkthrough I: "We model everyone, obviously").
   - What the engine learns *from* a maker is a separate decision, and v0 learns nothing from any maker: it reads only.

---

## 9. The global tab ("the only way out is together")

**The curator's intent (walkthrough I).**
- **What it should show:** that extracting core values from one person is hard, so the individual estimates come out weak.
- **The resolution:** pooling across people, made discoverable: "the only way out is together."

**Make the claim precise, because the unconditional version is false.**
- **Where it fails.** With enough data, one person's choices can identify them. Chess stylometry picks a player out of 2,844 from 100 games with 85% accuracy without openings and 98% with them (McIlroy-Young et al., 2021). Ghost's spec builds such a world as its positive control.
- **What is true** is narrower and stronger:
  - **The decomposition theorem.** From behavior alone, a policy cannot be uniquely split into a planning algorithm and a reward function (Armstrong & Mindermann, arXiv 1712.05812). That is the triple inference's order in theorem form: process must be read before preferences.
  - **The other route.** Recovery becomes possible with variation: the same reward observed under different discount rates or sufficiently different environments can be identified up to a constant (Cao, Cohen & Szpruch, arXiv 2106.03498).
  - **So one person's values are only identifiable given assumptions about how they plan,** and those assumptions are estimated from the population, or from the same person across many contexts.
- **The global tab shows the population route.**

**Packet schema 1.5 additions (in scope for app 0.3).** All are optional and backward-compatible.

```text
hypotheses[].interpretation   adds "drive"
hypotheses[].icon             optional enum: seeking|rage|fear|lust|care|panic-grief|play|body|value
population                    optional object:
  populationId                string (e.g., "writing-v0")
  makersPooled                integer
  description                 string (which datasets, which domain)
  items[]                     per value/drive hypothesis:
    hypothesis                id
    populationSupport         Support (the population's mean, same scale)
    makerRecords              integer (n_m)
    shrinkage                 number in [0,1] (share of the estimate from the maker's own data)
    curve[]                   [{records, intervalWidth}] precomputed: how the interval narrows with records
maker predictability          makers[].predictability optional Support (lambda_m mapped to [0,1])
```

**What the tab displays, per value or drive.**
1. **Two positions:** the population's position and this maker's.
2. **A bar for the shrinkage weight:** how much of this estimate is the maker's own evidence, against borrowed population evidence.
3. **The interval-narrowing curve.**
4. **A line in plain words**, for example: "Your estimate moves from everyone toward you as your record grows. With 12 decisions, 80% of this estimate is borrowed from 4,212 other makers."

**Populations are domain-tagged.** Chess players are not a prior for essayists.
- **writing-v0:**
  - CoAuthor writers;
  - Wikipedia editors with at least 200 edits;
  - authors of the git-hosted essays.
- **preferences-v0:** Community Alignment, PRISM and MultiPref annotators, for any future chat-reading feature.

**Anti-capture, stated honestly.**
- The tab must never cap a maker's confidence artificially.
- It shows the true shrinkage. Most makers in T0 and T1 have little data, so most estimates are mostly borrowed, which is the curator's desired display and also true.

---

## 10. Service and frontend integration

### 10.1 Engine CLI (D0 first)

```text
tompathy-engine ingest   --adapter {coauthor|git|wiki|lichess|panel} --source <path|url> --ledger <dir>
tompathy-engine fit      --ledger <dir> --population writing-v0 --until <iso-time>
tompathy-engine analyze  --ledger <dir> --artifact <artifact_id> --capture <capture.json> --out <packet.json>
tompathy-engine population build --ledger <dir> --id writing-v0 --out population/writing-v0.json
tompathy-engine registry publish --packets <dir> --out <registry-dir>
tompathy-engine serve    --port 8765 --token-file <path>        (D1)
tompathy-engine eval     --dataset <name> --split prequential --modules <list> --out <scores.parquet>
```

`analyze` accepts the ToMpathy capture as input. The capture's artifact block is copied into the packet unchanged, so anchors and revision hashes match exactly.

### 10.2 Registry (D0)

**Layout:**

```text
registry/v1/index/<first 4 hex of sha256(artifact.id)>.json
    -> list of {artifact_id_hash, revisions[], packet_paths}
registry/v1/packets/<sha256(artifact.id)>/<artifact.revision>.json
registry/v1/population/writing-v0.json
```

**Privacy.** The extension fetches the bucket index by a 4-hex-character prefix. The host learns only that the reader's page falls in one of 65,536 buckets, then filters locally.

**Hosting.** GitHub Pages. The extension requests optional host permission for that one origin.

**Staleness.** If the page's revision hash differs from every stored revision, the extension shows "This page changed since it was analyzed" and does not attach claims. The existing matching rules already refuse fuzzy attachment.

### 10.3 Local companion (D1)

- **Transport:** FastAPI on `127.0.0.1`.
- **Session token:** a random 256-bit token written to a file that the user pastes once into ToMpathy Options.
- **CORS:** restricted to the extension's origin.
- **Endpoints:**
  - `POST /v1/analyze`: body is `AnalysisRequest` without `signal`; response is a contract packet; long jobs stream progress over server-sent events; cancellation is by `requestId`.
  - `GET /v1/health`: engine version, admitted modules, ledger size, models available.
  - `GET /v1/population/{id}`.
  - `POST /v1/ingest`: optional; fetch a git or Wikipedia history for the current page when the user asks.
- **Resources:**
  - CPU first; the transcriber is optional and uses the GPU if present.
  - It honors Sounding Line's GPU lock convention, so the companion never fights the research queue.

### 10.4 Frontend changes (same 0.3 branch)

1. Add `registryProvider` and `localProvider` implementing `InferenceProvider`. Selection lives in Options. The default is none, as now, until the curator enables a provider.
2. Accept packet schema 1.5 fields (section 9). Render the global tab from `population`.
3. Add the `drive` interpretation and icons in the values list.
4. Update `PRIVACY.md` for each provider before release.
5. Add a parity test in CI: every packet in `examples/` and every engine fixture packet validates under `PacketSchema`.

### 10.5 Schema parity

- **Source of truth.** The zod schema in ToMpathy stays authoritative. The engine mirrors it in pydantic (`engine/tompathy_engine/packet/contract.py`).
- **CI.** Engine CI runs ToMpathy's own validator through a small Node script on every produced packet. A mismatch fails the build.

### 10.6 First readings to publish

**Selection criteria.**
- The source is public, and its license permits analysis and quoting short excerpts.
- It has a revision history (T1) or a process log (T2) wherever possible.
- Authorship is public.
- The subject is close to the project's own, so the readings double as content.

**The picks (checked 14 October where noted).**

| # | Reading | Tier | Why | Status |
|---|---|---|---|---|
| 1 | The curator's essays: "Art: A Unifying Model" (abrahamhaskins.org/art) and "Art as an Algorithmic Virus" (in Sounding Line `docs/theory/essays/`) | T0 now; T1 if their drafting history is pushed | The first reading the curator asked for. It shows a mostly borrowed values box and a live global tab | Ready |
| 2 | **Distill articles** (`github.com/distillpub`, 55 repositories, one `post--...` repository per article) | T1 | Multi-author articles on interpretability and alignment, with finished histories (Distill paused in 2021). This is the best fertile ground found | `post--feature-visualization` checked: article content CC-BY-4.0, 87 commits. CC-BY-4.0 is also listed for `post--safety-needs-social-scientists`, `post--communicating-with-interactive-articles` and `post--understanding-rl-vision`. Check each other repository's license before use |
| 3 | **Wikipedia articles on the project's own subjects:** "Empathy", "Theory of mind", "Affective neuroscience", "Jaak Panksepp", "Aesthetics" | T1, with deep per-editor histories through the API | Long, summarized histories; many editors; CC BY-SA | Pull at M1. Report history length and summary coverage per article |
| 4 | One CoAuthor session | T2 | The full-process demo: attention, timing, corrections | Internal only. No public release unless the CoAuthor authors agree, because no license is stated |

**Ruled out:** gwern.net. The public repository holds site infrastructure, and its contributing notes say site content is not covered by it (checked 14 October).

---

## 11. Evaluation hooks (Sounding Line and Ghost)

- **Sounding Line.** Uses `tompathy-engine eval`.
  - **Output:** per-decision proper scores (half-Brier, log loss) with maker, prompt and time keys, as Parquet.
  - **Statistics stay in Sounding Line:** writer bootstrap, crossed resampling, the pooled futility rule, online false-discovery control.
  - **Pinning:** each Sounding Line card pins a ToMpathy commit.
- **Ghost Scale.** Emits ledgers plus truth sidecars.
  - `engine/tompathy_engine/ghost/bridge.py` loads them.
  - **Conformance suite:** eight tests, specified in the Ghost spec. It checks that every module runs unchanged on Ghost ledgers and that no truth field leaks into a reader view.
- **Admission records.** A module is enabled in packets only with:
  1. a Ghost record: recovers planted truth in its twin world, beats its ablation;
  2. a Sounding Line record: ties or beats the backbone on real held-out makers, or is labeled "explanatory" with relative support only.

---

## 12. Repository layout (inside `tompathy/`, 0.3 branch)

```text
tompathy/
  src/  public/  scripts/  tests/  docs/      (existing frontend, unchanged except section 10.4)
  engine/
    pyproject.toml          (Python 3.12; core: numpy, scipy, pandas, pyarrow, duckdb, pydantic,
                             fastapi, uvicorn; extra [research]: numpyro, jax[cpu], spacy,
                             sentence-transformers)
    tompathy_engine/
      ledger/        schema.py  store.py  ids.py  provenance.py
      adapters/      coauthor.py  git.py  wiki.py  capture.py  lichess.py  panel.py
      features/      deterministic.py  embeddings.py  timing.py
      transcribe/    questions.yaml  runner.py  admission.py  cache.py  backends/{ollama,llamacpp,openai_compat}.py
      models/        backbone.py  prototypes.py  diagnosticity.py  corrections.py  source_trust.py
                     goal_tree.py  calibration.py
      explain/       drives.py  values.py  attention.py  process.py  evidence.py
      population/    build.py  summary.py
      packet/        contract.py  build.py  validate.py
      registry/      publish.py
      serve/         app.py
      eval/          scoring.py  splits.py  controls.py  harness.py
      ghost/         bridge.py  conformance.py
    tests/
      fixtures/      coauthor/  git/  wiki/  capture/  ghost/
      test_ledger.py  test_adapters.py  test_backbone.py  test_corrections.py
      test_packet_schema.py  test_ghost_conformance.py  test_registry.py
    scripts/validate_with_packet_schema.mjs   (runs src/core/model.ts PacketSchema on engine packets)
  .github/workflows/verify.yml                (adds the Python engine job)
```

The canonical ledger schema is `engine/tompathy_engine/ledger/schema.py`. Ghost and Sounding Line pin it by ToMpathy commit.

---

## 13. Milestones and acceptance tests

Sequenced by gates, not dates; the curator works at agent speed.

**M0: ledger, CoAuthor, backbone.**
- **Build:**
  - ledger and store;
  - A-coauthor;
  - deterministic features;
  - the backbone (port of Sounding Line's partial-pooling baseline);
  - prequential scoring.
- **Accept:**
  - CoAuthor census matches Sounding Line (16,959 usable, 39 excluded, 61 writers); 64 fixtures exact.
  - On Sounding Line's 234 cloud-study targets, the port reproduces the baseline: half-Brier 0.2945 for partial pooling, 0.3102 for population, within 0.0005.
  - Prequential scoring over all decisions runs on CPU in under an hour.

**M1: packets and registry.**
- **Build:**
  - A-capture, A-git, A-wiki;
  - the packet builder;
  - values with population prior;
  - the global-tab population file (writing-v0);
  - the registry;
  - ToMpathy `registryProvider` (section 10.4).
- **Accept:**
  - Packets for the four readings in section 10.6 validate under ToMpathy's own `PacketSchema` and render in the extension:
    1. the curator's essay (T0: values mostly borrowed, goal tree as hypothesis, global tab live);
    2. one Distill article (T1);
    3. one Wikipedia article (T1);
    4. one CoAuthor session (T2: attention, process, weak values; internal only).
  - No `probability` semantics anywhere.

**M2: transcriber, corrections, diagnosticity, calibration.**
- **Build:**
  - the transcriber with admission batteries (Q1 to Q10);
  - the corrections module;
  - diagnosticity weights;
  - the calibration layer.
- **Accept:**
  - Each module's Sounding Line record exists: admitted, inconclusive, or killed.
  - Only admitted modules contribute to packets.
  - Ghost conformance suite passes.

**M3: local companion, source trust, goal tree with root cue.**
- **Build:** D1 service; ToMpathy `localProvider`; source trust; goal tree with root cue; predictability display.
- **Accept:**
  - A live analysis of a Wikipedia article (fetch history, ingest, fit, packet) finishes in under 60 seconds on the curator's machine with CPU only.
  - Cancellation works.
  - The privacy text is updated.

---

## 14. Non-goals for the skeleton

- **No hosted service** and no paid inference.
- **No per-author fine-tuned language models.** Stage 14's 86 adapter cells showed no useful gain.
- **No LLM judgments about makers.** The LLM transcribes; models decide.
- **No contribution percentages** (who wrote what share). That remains a Sounding Line detection question.
- **No learning from any maker's values.** The engine reads; it does not adopt.

---

## 15. Pre-mortem

| Failure | What it looks like | Guard |
|---|---|---|
| **T0 emptiness** | Most pages have only final text, so the values box is nearly all population prior and the product looks empty | Lead with T1 and T2 readings in the registry; make "borrowed" visible and meaningful in the global tab; show what evidence would move each estimate |
| **Two-implementation drift** | Sounding Line's numbers stop describing the shipped engine | One package in `tompathy/engine/`; Sounding Line pins ToMpathy commits; packets list engine version and admission records |
| **Affective fallacy** | Drive loadings track what the text is about | Rule 8.1: only choices and corrections move maker estimates; a Ghost control plants content-motive mismatches |
| **Judgment creep in the transcriber** | Questions drift from literal to interpretive, and errors look like findings | Admission batteries; deterministic cross-checks; labels and goal candidates stay `hypothesis` |
| **Projection** | The engine reads makers through its own defaults, as the cloud reader over-predicted "edit" (43% against 22%) and never predicted "dismiss" | Base rates and pooling first; prior-shift calibration; Ghost family N5 tests it |
| **Identity errors** | Two people merged, or one person split, across sources | Source-scoped IDs; explicit identity evidence only; IP editors flagged |
| **Privacy leak through the registry** | The registry host learns what readers read | Prefix buckets; local filtering; disclosure in PRIVACY.md |
| **Domain-mismatched priors** | Chess players' patterns used as a prior for essayists | Domain-tagged populations; the global tab names its population |
| **Resource contention** | The companion slows Sounding Line's GPU queue | CPU-first; the GPU lock convention honored |
| **Overclaiming "together"** | The tab implies nobody can be known alone | Show true shrinkage; no artificial caps; cite the decomposition theorem's actual scope |

---

## 16. Decisions: resolved, and defaults in force

**Resolved (curator, 14 October, 20:00 PDT).**
1. **Repository:** the engine lives in `tompathy/engine/`, on the 0.3 feature branch.
2. **Packet schema 1.5** (drives, icons, population block, predictability) ships with app 0.3.
3. **First readings:** chosen by the analyst (section 10.6).

**Defaults in force unless the curator overrides.**
4. **SEEKING** is modeled as pursuit vigor, an intercept, and shown among the drives with a one-line note.
5. **Deployment order:** D0, the static registry, first; D1, the local companion, at M3.
6. **Support semantics:** relative everywhere until a module passes calibration (section 6.6).

## Sources

- ToMpathy repository, `main` at `07dc29bb`: `README.md`, `STATUS.md`, `PRIVACY.md`, `docs/INPUT_CONTRACT.md`, `docs/CONTEXT_RESEARCH.md`, `src/core/model.ts`, `src/core/provider.ts`, `src/components/ValueTabs.tsx`.
- Sounding Line `0a956219c`: `runners/stage14_midweek/baselines.py`, `runners/stage14/records.py`, `runners/stage14/factorized.py`, `runners/stage13/export_tompathy.py`, and FINDINGS entries cited in the results doc.
- [Armstrong & Mindermann, "Occam's razor is insufficient to infer the preferences of irrational agents" (arXiv 1712.05812)](https://arxiv.org/abs/1712.05812)
- [Cao, Cohen & Szpruch, "Identifiability in inverse reinforcement learning" (arXiv 2106.03498)](https://arxiv.org/abs/2106.03498)
- [McIlroy-Young et al. (2021), behavioral stylometry in chess](https://www.cs.toronto.edu/~ashton/pubs/chessembed-neurips2021.pdf)
- [Tang et al. (2026), Maia4All](https://openreview.net/forum?id=iw4kjcw319)
- [Regan & Haworth (2011), intrinsic chess ratings](https://ojs.aaai.org/index.php/AAAI/article/view/7951)
- [Konovalov & Krajbich (2019), response times and preference strength](https://dlab.sauder.ubc.ca/sjdm/journal/18/181101/jdm181101.html)
- [Alós-Ferrer, Fehr & Netzer (2021), recovering preferences from noisy choices](https://doi.org/10.1086/713732)
- [Shivaswamy & Joachims (2015), coactive learning](https://mlanthology.org/jair/2015/shivaswamy2015jair-coactive)
- [Gao et al. (2024), learning latent preference from user edits](https://arxiv.org/abs/2404.15269)
- [Saerens, Latinne & Decaestecker (2002), prior adjustment](https://mlanthology.org/neco/2002/saerens2002neco-adjusting)
- [Zhao et al. (2021), calibrate before use](https://proceedings.mlr.press/v139/zhao21c.html)
- [Yao et al. (2018), stacking predictive distributions](https://arxiv.org/abs/1704.02030)
- [Koren, Bell & Volinsky (2009), matrix factorization for recommenders](https://datajobs.com/data-science-repo/Recommender-Systems-[Netflix].pdf)
- [Efron & Morris (1977), Stein's paradox in statistics](https://www.scientificamerican.com/article/steins-paradox-in-statistics/)
- [Jakesch et al. (2023), co-writing with opinionated language models](https://arxiv.org/abs/2302.00560); [OSF materials](https://osf.io/upgqw/)
- [Williams-Ceci et al. (2026), biased AI writing assistants; data on Zenodo](https://zenodo.org/records/18048642)
- [Wimsatt & Beardsley (1949), the affective fallacy, via](https://en.wikipedia.org/wiki/Affective_fallacy)
- [Lee, Liang & Yang (2022), CoAuthor](https://coauthor.stanford.edu/)
- [Wikipedia edit summaries research page](https://meta.wikimedia.org/wiki/Research:Wikipedia_Edit_Types/Edit_Summaries); [Wikimedia robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy)
- [Lichess dataset card (clock data since April 2017)](https://huggingface.co/datasets/Lichess/standard-chess-games/raw/main/README.md)
- [Chrome native messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging); [extension service worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle)
