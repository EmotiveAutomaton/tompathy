# ToMpathy kickoff: live readings on any page, two readers, makers, and the order of work

16 October 2026, revision 2, after the curator's 14:17 answers. **For the ToMpathy agent, from the curator.** This is the whole plan. It merges and replaces the research-preview spec (`claude/TOMPATHY_RESEARCH_PREVIEW_SPEC_2026-10-16.md`) and the 13:47 driver. Handing it over is the curator's authorization. Nothing is left open: every former decision is settled in section 1.

If work on the preview spec has already started, continue it. Only the parts marked **(changed)** differ.

**Deadline.** The IHFES Lunch'n'Learn, **Thursday 22 October, 13:00 Irish time (05:00 PDT)**. It runs 30 minutes plus 15 for questions, presented remotely. The curator walks through the essays while demoing live readings.

**Starting point.** `codex/0.3-engine` at `82789fd`, built on the 0.2.0 frontend. Engine v1 already has:
- the ledger and the capture, Wikipedia and git adapters;
- the literal transcriber, with Ollama, llama.cpp and OpenAI-compatible loopback backends;
- the goal producer: local candidates plus a governing cover, bounded at 21 calls;
- the pooled backbone and the authenticated local companion;
- the explicit "Analyze Wikipedia history" action and packet schema 1.7.

No production module is admitted, so real readings currently show observed records and unknown estimates.

## 0. The curator's words

- **Run on anything (11:56):** "I kind of want it to be able to even run into a new unknown page and try to run the engine to see what it gets. I don't want pre-written stuff anymore… What matters is the actual test."
- **Two makers (12:57):** "The most fully realized version of ToMpathy should literally have, under the author dropdown, all of the various models that were used in the creation of this particular artifact. And you can jump between them." And: "What matters is the generative process."
- **Editing (14:17):**
  - "The creator tried to make the whole decision."
  - The model "tried to do all the decisions, fit it in where it went best they could."
  - "The follow-up person looked and tried to make sure that all the higher order hierarchical goals were properly satisfied. That's what editing is."
- **Readers (14:17):** "Different models should have different reading outputs just because that's how noise works. But practically speaking, the goal is to fully align with context and thus have removed the difference."
- **Vocabulary (14:17).** "Drive" is the name for Panksepp's lower-level emotional systems. The set point is the need itself. Deviations from the set point are called deviations.
- **Play (14:17):** play "solves the problem of having error bars that are too wide over unfamiliar situations", and "that reduction in error bars brings people closer."
- **Aesthetics (12:57).** He prefers compression progress as the definition of aesthetic pull.
- **The reader's habits (12:57):** "The AI reader would predict its own habits, and that'd be useful information."

## 1. Settled defaults (formerly open)

| Item | Setting |
|---|---|
| Research preview mode | **On by default** in every build, with the banner and badges |
| Statistical source signals | **In no build** until section 8's calibration gate passes. The preview spec's T0 "uniformity indicator" is dropped. The page's surprisal mean and spread stay, as plain page statistics, with no claim about where the text came from |
| Usernames in the talk | **Hidden** |
| The reader-side themes box | **Out for Thursday** |
| Demo backup | **Real runs, cached beforehand,** labeled as cached and when |
| Drives panel wording | **The curator's vocabulary, now** (section 7) |

## 2. Order of work

**P0, the research preview (section 3), must land for Thursday.** It's the base everything else uses. If time runs short, P0 wins.

**P1, Thursday additions, most interesting first** (each half a day or less):
1. **Two readers, and what context does to them** (section 4).
2. **The makers panel, version 0, with decision roles** (section 5).
3. **The payoff map** (section 6).
4. **The drives panel in the curator's vocabulary** (section 7). This is copy-level, an hour or two.
5. **Quick wins:**
   - a 20-dot quantile dotplot for each borrowed population value;
   - Wikipedia revision comments and tags as stated goals, plus a count of reverted revisions;
   - GitHub's commits call with the trailer parser, showing the AI co-author share and the remaining quota.
6. **Ghost's module gates** (section 11), only if P0 and P1 items 1 to 4 are done by Monday night. Otherwise this is the first job after Thursday.

**P2, after Thursday:** section 10, in order. **Demo risks:** section 9.

## 3. P0: research preview mode

### 3.1 What it is

**A second path, separate from the admitted path, that runs every available module on any page.** Every output says two things:
- what it's based on;
- whether it has passed any test.

The admitted path and its rules stay exactly as they are. Preview never writes an admission and never claims probability.

### 3.2 Labels (packet schema 1.8, backward compatible)

Add two optional fields to every hypothesis and attention item:

| Field | Values | Meaning |
|---|---|---|
| `evidenceStatus` | `admitted`, `constructed-tested`, `unvalidated` | `admitted`: passed both Ghost and Sounding Line admission. `constructed-tested`: passed a constructed battery or Ghost check, but nothing on natural data. `unvalidated`: no test passed |
| `basis` | `choices`, `corrections`, `history`, `text-surface`, `population`, `model-judgment` | What the estimate is computed from |

**Packet-level fields:**
- `provider.mode`: `admitted` or `preview`;
- `provider.previewNotice`: one sentence of plain text.

Support semantics stay `relative` everywhere in preview.

**Frontend:**
- **The banner.** A slim banner on every panel in preview: "Research preview: these are the engine's guesses. Each one says what it's based on and whether it has been tested."
- **The badges.** One small badge per item: **tested** (green), **lab-tested** (amber), **untested** (grey). Hovering shows the basis and a one-line reason.
- **The toggle.** Options gets a **Research preview** toggle, on by default **(changed)**.

### 3.3 T0: any page (final text only)

**A. Deviation map** (new; Current attention panel)

**What it computes.** It marks where the text departs from what a typical writer would have written next, using per-token surprisal under a small local language model. The model is a population forward model of text, so its large surprises are departures from the population's expected process.

**Why it fits the theory.** The curator's definition is that "current attention is inferred from deviations from the reader's personally generated process", adjusted toward the creator's. Readers' processing time tracks surprisal logarithmically across large corpora ([Smith & Levy 2013](https://www.mit.edu/~rplevy/papers/smith-levy-2013-cognition.pdf)). This map shows where a population reader would be surprised. It isn't measured attention.

**Method:**
1. **Model.** Load a small open causal language model in the companion, about 0.5B parameters (Qwen2.5-0.5B), pinned by file hash, CPU by default. Never download silently; installation is an explicit step.
2. **Scoring.** For each region (paragraph), score the tokens with the previous region as context, within a 2,048-token window. Record token surprisal, s = -ln p(token | preceding text).
3. **Aggregation.** Combine tokens into words and short phrases. Hold out tokens that are digits, URLs, code, or capitalized words not at the start of a sentence. Report those separately as "names and numbers": they're high-surprisal for trivial reasons.
4. **Departure score.** Each phrase's content-word surprisal, minus the page's median, divided by the page's interquartile range.
5. **Emitted attention frames.** The top 15 phrases, plus every sentence whose mean departure is in the page's top decile. Each frame carries `basis: text-surface`, `evidenceStatus: unvalidated`, the reader's name and hash, and relative support.

**Panel copy:** "Where this text went somewhere a typical writer wouldn't. A proxy for the author's choices; not measured attention."

**Also report** the page's surprisal mean and spread, as page statistics only **(changed: no uniformity indicator, no source claim)**.

**Budget.** The target is under 15 seconds for a 3,000-word page on CPU. It's a target, not a measurement: measure it on the demo machine first (section 6). Cache by content hash and model pin.

**B. Goal tree** (existing goal producer; Expertise, Habits, and Process panel)
- **Root cues:**
  - the page title;
  - h1 to h3 headings;
  - the meta description;
  - for T1 sources, the latest edit summary or commit message.
- **Calls.** Local candidates per region, plus one governing cover, within the existing 21-call bound. For longer pages, group adjacent paragraphs into at most 20 regions first.
- **Labels.** `basis: model-judgment`, `evidenceStatus: unvalidated`. The governing node's description names the root cues it used.
- **Theory note.** This is the top-down entry: a stated purpose as a root cue. In constructed worlds, a reliable root cue was worth up to 0.64 nats at the root when leaf evidence was sparse (Ghost V23, the stated-purpose family). Its real-data value is untested.

**C. Technique notes** (existing transcriber; process panel)
- **Questions:** Q1 topic continuity, Q3 register, Q4 tone change, Q5 dialogue and Q7 contradiction.
- **Run unit:** per region, not per sentence, to bound the number of calls.
- **Reader:** the original fixed-reader Qwen 3.5 9B prompt, which passed constructed admission on these questions. Label results `constructed-tested`.
- **Limits:** at most 100 calls per page, with results streamed as they land. Q6 (person) and Q10 (themes) stay off for technique notes.

**D. Habits** (deterministic; process panel)
- **Repeated phrasings:** 3- to 5-word sequences that recur more often than the page's own shuffled baseline predicts.
- **Rhythm and habit:** preferred connectives, sentence-length rhythm and punctuation habits.
- **Labels:** `basis: text-surface`, `evidenceStatus: unvalidated`.
- Separate the author's repeats from quoted text where quotation marks make that possible.

**E. Core values on T0**
1. **Borrowed population prior.** This is the existing path: drives at the population position, with zero personal records and zero personal evidence share.
2. **"What would move this estimate."** One line per drive or value, naming the evidence types that would move it:
   - choices among different options;
   - content corrections;
   - stated goals;
   - revision history.

   This is the anti-capture message in working form.
3. **No theme-to-drive mapping** **(changed: the themes box is out for Thursday)**.
   - The engine's guard rule 8.1 stands: text describes the artifact; only choices and corrections describe the maker.
   - The current danger-to-FEAR mapping also conflicts with the curator's account of play as fake danger, and with the finding that people enjoy fear most at moderate doses ([Andersen et al. 2020](https://www.psychologicalscience.org/observer/playing-with-fear)).

**F. Provenance** **(changed).** Evidence-first makers replace the source indicator (section 5).

### 3.4 T1: Wikipedia articles and GitHub-hosted essays (existing history action, extended)

**Existing:**
- fetch at most 20 revisions by default, with an option up to 500 for the curated demo pages;
- observed revisions, corrections, editors and edit summaries;
- edit focus;
- Q8 and Q9 correction classification. The fixed Qwen prompt passed constructed admission on both.

**Add for preview:**
- **Per-editor correction directions,** from content corrections only (Q8 not typo or grammar, and Q9 yes). Show each editor's strongest two directions with their counts, labeled `basis: corrections`, `unvalidated`. Process corrections feed the habits panel only.
- **Edit summaries as stated goals,** shown on the goal tree as the root cue for that revision.
- **The housekeeping-against-content split,** shown as counts per editor. Experienced writers revise for meaning and structure rather than words ([Sommers 1980](https://openlab.citytech.cuny.edu/fywpd/files/2019/01/sommors-revision-strategies.pdf)). The curator's 14:17 definition sharpens it: content corrections are where an editor protects higher-order goals.

### 3.5 T2: one internal CoAuthor session (existing; internal only)

No change. Use it in rehearsal only; don't present CoAuthor text publicly.

### 3.6 The global tab with real numbers (changed)

Add a supplied population comparison built from Sounding Line's public Phase 0 aggregates, `results/phase_2_4_stage_15/PHASE0_SUMMARY.json` (descriptive, historically exposed data).

**What the numbers say** (61 writers, 16,855 decisions):
- The Phase 0 backbone forecast writers' handling better than population base rates did: 0.021 half-Brier, interval 0.012 to 0.032. It's a pooled model with context features and shrunken per-writer offsets; the report says the two are bundled.
- It also beat each writer's raw past frequencies: 0.007, interval 0.00003 to 0.015.
- The edge over a writer's own frequencies is largest for decisions with no prior history (0.018). It's smallest for decisions with 300 or more (0.005, from the 14 most prolific writers; the report's crossed writer-and-prompt interval, -0.001 to 0.010, includes zero).

**Correction to the preview spec.** Different writers fill different history bins, and the Phase 0 report says this "prevents reading their shape as an individual learning curve". Don't present the bins as anyone's learning curve, and don't say a writer's own record "catches up".

**One sentence for the tab:** "A model that starts from everyone and adjusts a little for each writer, given the context, forecast these writers better than their own past choices alone did."

**A hover line, marked as a literature finding:** "In other studies, people predicted how much they'd enjoy something better from another person's report than from a description of the thing ([Gilbert et al. 2009](https://www.harvardmagazine.com/2010/03/pleasure-by-proxy))."

### 3.7 Live performance budget

Render progressively, fast modules first:

| Stage | Target on the curator's machine |
|---|---|
| Capture, deterministic habits | under 2 s |
| Deviation map | under 15 s |
| Second reader (section 4) | under 15 s more |
| Payoff layer 1 (section 6) | under 15 s more |
| Technique notes (streaming) | first results under 20 s; all within 2 min |
| Goal tree | within 2 min |
| T1 history fetch, 20 revisions | under 5 s (measured 2.83 s) |
| T1 correction labels, 20 revisions | under 2 min |

**Rules:**
- Pre-warm all models before the talk.
- Keep the existing cancellation and progress events.
- Cache every model call by exact input, model pin and template.
- A real cached run of a page is the fallback if the live run stalls. A hand-written reading never is. The packet records that the run was cached, and when.

### 3.8 Privacy and third parties

- Text stays on the machine (the companion on loopback, as now). Preview adds no network calls except the existing explicit history fetch.
- Exported readings carry `provider.mode: preview` and the per-item labels.
- No registry publication of per-person preview readings. The EU's top court treats data "liable indirectly to reveal" sensitive categories as sensitive ([CJEU C-184/20](https://www.insideprivacy.com/eu-data-protection/special-category-data-by-inference-cjeu-significantly-expands-the-scope-of-article-9-gdpr/)). Inferred values of named editors fall in that zone; keep them local.
- Update `PRIVACY.md` with the deviation-map models and preview mode before any release.

### 3.9 Acceptance tests for Thursday

1. **Five unseen pages** run end to end on the curator's machine, each within 3 minutes: a news article, a blog post, a Wikipedia article (T1), a GitHub-hosted essay (T1), and the curator's essay. Every panel shows content or an explicit, labeled empty state.
2. **Labels are complete.** Every hypothesis and attention item in a preview packet has `evidenceStatus` and `basis`. A validator test fails the build otherwise.
3. **No regressions.** Preview off returns exactly today's admitted-path packet for the same input. The 0.2 browser scenarios and the engine suite still pass.
4. **No theme-to-drive mapping** appears in preview output.
5. **Cancellation.** Cancel mid-run on each tier; the companion stays healthy.
6. **Two readers** (section 4) **(changed: a P1 test)**: on the curator's essay, the agreement view renders, and the convergence numbers are reported.
7. **Makers** (section 5) **(changed: a P1 test)**: the three makers tests pass.
8. **Payoff** (section 6) **(changed: a P1 test)**: the novel-span check passes, or the result is reported.

Tests 6 to 8 gate their own P1 items only. P0 ships without them.
9. **Rehearsal.** A full timed rehearsal on Wednesday 21 October, using the demo order in 3.10.

### 3.10 Suggested live demo order (the curator adjusts freely)

1. **The curator's essay (T0, preview):**
   - the deviation map against his own reading of where he made choices;
   - the two readers converging as context grows;
   - the goal tree with the title as root cue;
   - values borrowed from the population, then the global tab.
2. **Wikipedia's "Empathy" (T1):**
   - who edited (pseudonymized makers);
   - housekeeping against content corrections, as goal protection;
   - edit summaries as stated goals;
   - edit focus as attention.
3. **An unknown page from the audience (T0, preview),** with the badges doing the honesty work out loud.
4. **The test that would settle it:** a pre-registered prediction on public data. For example, predict Wikipedia editors' next edit purposes from their histories, against a population baseline.

## 4. Two readers, and what context does to them (P1.1)

**Why.** The essays define attention as departure from the reader's own expected process, so the reader is part of every reading. The curator's 14:17 answer adds the dynamics. Readers differ through noise and missing context, and context should close the gap. That's a theorem for Bayesian readers whose priors allow the same possibilities ([Blackwell & Dubins 1962](https://doi.org/10.1214/aoms/1177704456)). A gap that context doesn't close suggests one reader can't represent the move.

**Build:**
- **Provenance.** Every deviation and payoff item names its reader: model, version and file hash.
- **A second reader** from a different family: SmolLM2-360M beside Qwen2.5-0.5B.
- **The agreement view.** It shows three kinds of region:
  - regions both readers flag;
  - "departures this reader finds that another doesn't";
  - the agreement share for the page.
- **Context convergence.** Score the page twice per reader: once with short context (each sentence with only the previous sentence), and once with full context (the deviation map's default).
  - Report the agreement share at each, as Spearman correlation of token surprisal and overlap of top-decile departures.
  - Show it as one line: "With more context, these two readers agree more: X% to Y%."
  - If they don't converge, show that too. It's a finding.

**Copy for the global tab:** "What counts as expected depends on who's reading. More context brings readers together. Regions both readers flag are the safer bets. Regions only one flags are noise, or something one reader can't represent."

**Acceptance test.** On the curator's essay, the two-reader view renders with both agreement shares.

**Feeds from Sounding Line.** Card D21 runs the same convergence test across five readers on CoAuthor, with a size ladder. When it lands, cite its curve in the global tab.

## 5. The makers panel, version 0, with decision roles (P1.2)

**Goal.**
- List every generative process behind the artifact.
- Give each its own reading, and let the viewer switch between them.
- Attribute by decision, as the curator defined editing.

Version 0 lists makers only where there's evidence of them, and says so.

**Packet addition (schema 1.9, backward compatible):**
```
makers: [
  { id, kind: person | model | tool | bot | unknown,
    label,                        // e.g. "Editor 3", "Claude (co-author trailer)"
    evidence: [ { tier: signed | declared | flagged | trace | statistical,
                  source,         // e.g. "C2PA manifest", "git trailer", "Wikipedia bot flag",
                                  //      "{{AI-generated}} template", "oaicite markup"
                  detail, evidenceStatus } ],
    decisions?: { drafted, selected, edited, reverted },   // counts, where the source logs them
    role?,                        // a hypothesis label from the list below, never a verdict
    spans: [ [start, end] ]?,     // character ranges, only when attributable
    revisions: [ ids ]?,          // T1 sources
    reading: <packet sub-reading for this maker>? } ]
```

**Decision roles.** These come from the curator's answer.
- **Drafted:** the maker produced the words, for example a model's suggestion, or a commit by an AI-trailer author.
- **Selected:** the maker chose among options, for example a person accepting a suggestion.
- **Edited:** the maker changed text to protect a higher-order goal. Content corrections count; housekeeping is shown separately.

**What the roles mean for a reading.** A sentence that was drafted by a model and kept by a person is weak evidence about the person's wording, and moderate evidence about their goals, because it passed their check. Show the counts where the source records them:
- git: commits by AI-trailer authors against later human commits touching the same files;
- Wikipedia: bot edits against human content edits.

On sources without logs, show no counts.

**The evidence ladder.** Show the strongest tier present, with the rest listed beneath it. A statistical signal never creates a maker entry; only tiers 1 to 3 can.
1. **Signed:** C2PA manifests. Show validation and trust status separately, plus `digitalSourceType`. From spec 2.4 (April 2026), also show the `c2pa.ai-disclosure` fields: the model name, and human oversight (fully autonomous, prompt-guided or human-validated).
2. **Declared by a tool, unsigned:** git authors and trailers; Wikipedia usernames, edit summaries and tool tags. Defaults differ by tool:
   - Claude Code adds `Co-Authored-By:` with the model name (configurable);
   - GitHub's Copilot coding agent authors commits itself, with the assigning person as co-author and an `Agent-Logs-Url` trailer;
   - Cursor adds a "Made with Cursor" trailer;
   - Aider appends "(aider)" to the author name.

   Trailers are unsigned and editable. VS Code briefly stamped `Co-authored-by: Copilot` on commits with no AI involvement (April to May 2026, since reverted). So "declared" means declared, not proven.
3. **Flagged by editors or filters (not a finding):**
   - Wikipedia's {{AI-generated}} template;
   - edit tags such as "possible AI-generated citations";
   - "possible prose issues", a deliberately neutral tag name worth copying.
4. **Trace:** leftover markup from chat tools, for example `oaicite` artifacts in citations.
5. **Statistical resemblance:** in no build (section 8).

**Role labels, as hypotheses.** Use C2PA's human-oversight values and the six categories from the 2025 PAN shared task on human and AI collaboration:
- fully human;
- human-written, then machine-polished;
- machine-written, then machine-humanized;
- human-initiated, then machine-continued;
- deeply mixed;
- machine-written, then human-edited.

The best system in that task reached only 65 F1 on these six classes, so they're vocabulary for hypotheses, not outputs.

**What the viewer can do.** Choose a maker in the dropdown; "All makers" is the default view. The panels then show that maker's part:
- on T1 sources, that maker's revisions and corrections;
- on git, the commits by author, with AI-trailer commits as their own maker;
- on T0 pages with no provenance, a single "Author (unresolved)" maker, plus a line saying no provenance was found.

**Wikipedia and privacy.** Readings of named editors are readings of identifiable people.
- In the dropdown, editors appear as "Editor 1, Editor 2, …".
- Usernames can be revealed locally with one click, and are never exported.
- In the talk, they stay hidden.

**Acceptance tests:**
- A GitHub essay with AI trailers lists the person and the tool as separate makers, with commit shares and decision counts.
- A Wikipedia article lists pseudonymized editors by bytes changed, with bots flagged as bots and content edits counted as edits.
- A plain news page lists one unresolved maker and states that no provenance was found.

## 6. The payoff map (P1.3)

**Why.** The curator's definition of aesthetic pull is compression progress: a reader's model improves while reading, so the text gets cheaper to encode. Schmidhuber, who coined the term, separates two things ([Schmidhuber 2009](https://arxiv.org/pdf/0812.4360)):
- **beauty** is how compressible something already is;
- **interestingness** is "the first derivative of subjective beauty or compressibility": the improvement itself.

His example of fast fun is a joke. After the punch line, learning "helps to compress the whole history including the punch line a bit better than before". A page can do both, so the map has two layers. Both use the deviation map's pinned model.

**Layer 1: setups paying off.** This is how much the page's own history makes a sentence easy.
- For each sentence, take the mean surprisal with only a short summary of the page as context, minus the mean surprisal with all preceding page text as context. This is the "narrative flow" measure of [Sap et al. 2020](https://aclanthology.org/2020.acl-main.178.pdf).
- It's closer to Schmidhuber's beauty than to his progress: earlier text made this sentence easy.

**Layer 2: re-reading the past.** This is the closest to compression progress.
- For each paragraph k (at most 20), score a window of earlier text twice: once with paragraph k prepended, and once with the same paragraph's sentences shuffled.
- The gain is how much paragraph k makes what came before easier to encode. It's the punch-line effect, measured with the page as its own spoiler.

**Controls.** Without these, both layers mostly find repeated words and names.
- **Shuffled baseline.** Compare against the same page with its sentences shuffled. Payoff that survives shuffling is topical, not structural.
- **Novel spans only.** Recompute on tokens outside any run of four or more tokens that already appeared earlier. Language models copy repeated patterns mechanically ([Olsson et al. 2022](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html)).
- **Holdouts.** Exclude the tokens the deviation map holds out: names, numbers, URLs and code.
- **Position.** Compare at matched positions. Loss falls with position whatever the content.
- **Memorization.** Flag pages the model finds suspiciously easy with no context at all, such as well-known texts. Their payoff is memory, not structure.

**Emit.** Both layers carry `basis: text-surface` and `evidenceStatus: unvalidated`, with the reader named.
- **Layer 1:** the top-decile sentences, as "pays off" frames.
- **Layer 2:** the top three paragraphs, as "re-reads the past" frames, each naming the earlier passage it most improved.

**Panel copy:**
- "Pays off: places this page's own earlier text made easy."
- "Re-reads the past: passages after which the earlier text makes more sense to the reader model."
- "Proxies for what the author set up; not measured enjoyment."

**Budget:**
- **Layer 1:** one extra pass, under 15 seconds for 3,000 words.
- **Layer 2:** about 30 to 60 seconds. Skip it if the page has more than 20 paragraphs, or if the run is over its time budget.
- **Measure both on the demo machine first.** These budgets are targets.
  - The only measurement so far is SmolLM2-135M (int8, WebAssembly, two threads, on a 2-vCPU server): 26 seconds of forward pass plus 10 of log-softmax for 4,096 tokens. q4 was 4.4 times slower.
  - Qwen2.5-0.5B hasn't been measured anywhere.
  - If the CPU misses the budget, put the model on the GPU in the companion.

**Acceptance test.** On the curator's essay, the novel-span version of each layer keeps at least half of its top items. That shows the map isn't just finding repeats.

## 7. The drives panel in the curator's vocabulary (P1.4)

**Vocabulary (the curator, 14:17):**
- **Set point:** the need itself, what a person keeps.
- **Deviation:** distance from a set point.
- **Drive:** one of Panksepp's lower-level emotional systems: a pre-made solution that runs from a set point.
- **Constructed value:** a learned end. Today the curator adopted animal learning's test for one: it persists when the need it grew from is met another way.

**Changes for Thursday (copy and labels only; no new inference):**
- **The Core values header line:** "Drives are pre-made solutions, the seven systems Panksepp mapped. Each runs from a need, a set point the body or mind keeps. Constructed values are learned ends."
- **Each drive card's definition** names the need it serves. Keep the display name "Belonging" for PANIC/GRIEF (the curator's request), defined as: "Panksepp's PANIC/GRIEF system: the pre-made response to separation. The need it serves is belonging."
- **The PLAY card's definition:** "Panksepp's PLAY system. In this account, play narrows our uncertainty about how our own solutions work in unfamiliar situations. Done together, it brings people closer."
- **The constructed-value card** adds the test as its "what would move this estimate" line: "Would it persist if the need it grew from were met another way?"
- **Still no theme-to-drive mapping,** and still "what would move this estimate" on every card.

The curator may rewrite any of this copy; it's a starting point, not essay text.

**After Thursday:** a needs layer, with set points shown separately from drives, and deviations as their own display (section 10, item 9).

## 8. Statistical source signals: the rules

Detection of AI-written text is error-prone, and its errors fall unevenly:
- **Non-native writers.** Seven detectors flagged non-native English essays as AI-written 61% of the time on average, against 5% for native essays ([Liang et al. 2023](https://arxiv.org/html/2304.02819v3)). Later work disputes how general this is.
- **Boundaries.** Segment boundary detectors that are accurate within a word in-domain miss by about 15 words on unseen domains.
- **Wikipedia.** Editors are told to "avoid publishing content on Wikipedia obtained by asking LLMs to write original content" ([Wikipedia:Large language models](https://en.wikipedia.org/wiki/Wikipedia:Large_language_models)). The AI Cleanup project reports a stricter rule from March 2026, which the analyst couldn't re-check. Either way, any model reading of a Wikipedia edit reads as an accusation that an editor broke the rules.

So:
- **In no build** until this calibration gate passes:
  - a measured false-positive rate on known-human text ("X in 1,000 human texts score this high");
  - a non-native-writer slice reported separately;
  - a minimum length.

  Use pre-December 2022 Wikipedia revisions and commits, bots excluded, as the known-human set.
- **After the gate, off by default.** It never runs on Wikipedia per edit or per editor, and never on a page attributed to a named living person unless the viewer turns it on.
- **The whole page, never people.** Copy: "This text reads as unusually predictable to the reader model. That's common in model-written text, and also in formulaic, quoted or memorized human writing."
- **Abstain.** Copy PAN's output contract: a score of 0.5 means "can't tell", and abstaining is allowed.
- **No verdict words.** Never "AI-written", "detected", or a percentage of the author.
- **Evidence first.** If tiers 1 to 3 exist, show them and don't run statistics.
- **No sentence-exact boundaries.** Coarse regions only.

## 9. Risks for Thursday, and their guards

| Risk | Guard |
|---|---|
| Chrome 156 ships 20 October, two days before the talk | Retest the full demo on Chrome 156 on Tuesday |
| Chrome 142 added a permission prompt for public pages reaching local or loopback addresses; content-script requests run as the page's origin | Call the companion from the service worker, not from content scripts. On Tuesday, confirm calls to 127.0.0.1 go through with no prompt |
| Wikimedia's 2026 rate limits: 10 requests a minute for clients identified only by IP, 200 for browsers and clients with a proper user agent. A conference network may share one IP | Cache the demo pages' history responses beforehand. Send Wikimedia's `Api-User-Agent` header. Stay at 3 or fewer concurrent requests and obey `Retry-After` |
| GitHub allows 60 unauthenticated requests an hour per IP | One commits call returns up to 100 commits with their trailers. Show the remaining quota, and offer an optional token field |
| Model weights download on venue Wi-Fi | Pre-cache all weights before the talk |
| No `shader-f16` on the demo GPU, so a silent fallback to WebAssembly (slower) | Test the demo machine, and show the backend on the badge |
| Two readers plus payoff push the T0 run past 3 minutes | Render progressively. The second reader and layer 2 drop first when over budget |

## 10. After Thursday, most interesting first (changed)

This list is the preview spec's "after Thursday" items and the 13:47 driver's, merged and reordered by interest. Binoculars-class detection is dropped; section 8 replaces it.

1. **The how profile.** Once Sounding Line's D16 says which process features identify writers, show them for people with enough records. V3 says how many records each feature needs.
2. **Decision ledgers for logged sources.** Sounding Line's D22 defines drafted, selected and edited counts for suggestion logs. Adopt its definitions in the makers panel.
3. **What a page can claim.** Sounding Line's D27 measures what a finished page keeps of its making. Gate T0 readings to what it keeps.
4. **A browser-only path** for the deviation map, the two readers and the payoff layers, so ToMpathy runs on anything without the Python companion. It's about a day of work. If the companion misbehaves on the demo machine, pull this forward as Thursday's fallback.
   - **Library.** Transformers.js 4.3.1 (`@huggingface/transformers`) returns logits for the whole input on a plain forward call. Its scoring path sets `num_logits_to_keep = 0`, so per-token surprisal works in the browser. WebLLM can't do this: its log-probabilities cover generated tokens only.
   - **Model.**
     - SmolLM2-135M base: q4f16 (117.5 MB) on WebGPU when the adapter has `shader-f16`, int8 (135.7 MB) on WebAssembly otherwise.
     - SmolLM2-360M on WebGPU only.
     - For non-English pages, Qwen2.5-0.5B on WebGPU, or an "untested" badge. Language comes from Chrome's built-in Language Detector.
   - **Speed,** measured by the research pass on a 2-vCPU server with no GPU, one run each:
     - scoring 4,096 tokens with SmolLM2-135M int8 took 26 seconds of forward pass plus 10 of log-softmax, in WebAssembly with two threads;
     - q4 was about 4.4 times slower than int8 there;
     - putting the log-softmax and token gather into the ONNX graph cut 36.1 seconds to 24.7, with identical mean surprisal.

     WebGPU and real laptops weren't measured.
   - **Windows.** Use 512-token windows with stride 256, scoring the trailing 256 tokens. Exclude the first 32 tokens of the page. Non-overlapping windows create false departures at every window start.
   - **Comparability.** Surprisal shifts with quantization (5.48 against 5.03 bits per token, int8 against q4) and with window length (5.83, 5.48 and 5.05 bits at 256, 512 and 1,024 tokens). Compare within a page only, and show backend, data type and window on the badge.
   - **Manifest V3 constraints:**
     - the minimum content security policy includes `'wasm-unsafe-eval'`, and remote code is banned;
     - Transformers.js points its WebAssembly files at a CDN outside service workers, so set `env.backends.onnx.wasm.wasmPaths` to bundled copies via `chrome.runtime.getURL`;
     - multi-threaded WebAssembly needs the manifest's cross-origin isolation keys;
     - for now, run inference in the side panel. Later, move it to an offscreen document with a Worker. Service workers stop after 30 seconds idle, or after 5 minutes on one event.
5. **Corrections with intents:**
   - the released IteraTeR edit-intent classifier in the companion;
   - Wikipedia's structured edit types;
   - per-editor directions stated in words, the way recent work infers a user's preferences from their edits as a short description ([Gao et al. 2024](https://arxiv.org/pdf/2404.15269));
   - per-editor correction directions promoted out of preview once Sounding Line's corrections family has a result.
6. **"Test this reading":**
   - **a two-minute self-report of needs:** best-worst choices over seven items in seven blocks of three, as an external check on the third inference;
   - **the Wikipedia prediction:** predict an editor's next edit purpose, then reveal what they did.
7. **Makers panel, version 1:**
   - a C2PA reader using `@contentauth/c2pa-web` (WebAssembly; the extension's content security policy needs `'wasm-unsafe-eval'`);
   - Wikipedia tags and templates read through the MediaWiki API;
   - trailer conventions for each coding tool.
8. **"How this was made" for Wikipedia.** The WikiWho service gives token-level authorship for about 70 wikis, with every token's in and out history (data under CC BY-SA 4.0). Wikimedia's MIT-licensed "Who Wrote That?" extension colors article text by author with it. That fills the makers panel's `spans` for Wikipedia, behind the pseudonymized editor labels.
9. **The needs layer.** Show set points separately from drives, and deviations as their own display, still with no theme-to-drive mapping.
10. **Literal questions on Chrome's built-in model,** through the Prompt API. Extensions have had it since Chrome 138 ([Chrome docs](https://developer.chrome.com/docs/ai/prompt-api)).
    - It needs 22 GB of free disk, and either a GPU with more than 4 GB of VRAM or 16 GB of RAM with 4 CPU cores.
    - It supports English, Japanese, Spanish, German and French.
    - Each question needs its own battery on this backend.
11. **Uncertainty displays** for numeric estimates:
    - **Quantile dotplots.** In an incentivized bus-catching study, 50-dot plots got people to 97% of the optimal payoff, 5 points better than no uncertainty display (Fernandes et al., CHI 2018).
    - **Hypothetical outcome plots.** Animated draws beat error bars for comparing two or three quantities (Hullman, Resnick & Adar 2015).
    - **Implementation.** Vega 6.4.0 has official examples of both. The extension's security policy blocks Vega's default expression evaluator, so use `vega-interpreter`.
12. **Community signals per revision.**
    - Wikimedia's Lift Wing serves a revert-risk model (`revertrisk-language-agnostic`) and article-quality models. Show them as "Wikimedia's model", with Wikimedia's own badge, never as ToMpathy's reading.
    - Wikimedia's structured edit types (`mwedittypes` 3.1.0, now on Wikimedia's GitLab) run in the companion. Use the 3.x constructor, `SimpleEditTypes(content_type, prev, curr, lang)`; the README examples are out of date.
13. **Payoff map, version 2:** suspense and surprise from belief dynamics over sentence embeddings, which matched human suspense ratings better than probability-based measures ([Wilmot & Keller 2020](https://aclanthology.org/2020.acl-main.161.pdf)).
14. **The content-feature population model** from Sounding Line's D1, as the shared starting point for every T2 and panel reading.
15. **A reading of the curator's own essays from their commit history:** the maker model of himself, with consent built in.
16. **Statistical source signals,** only behind section 8's gate.

## 11. Cross-repository duties

**To Ghost Scale.** Ghost's twins wait on two things from ToMpathy (`docs/versions/v23-research-division/TWIN_INPUT_CONTRACT.md` at Ghost `d84e023a2`):
1. **A revision-purpose target.** The engine has no target for an unobserved revision purpose, so Ghost records `TARGET_UNAVAILABLE`.
   - Add a slot for why a revision was made, with intent classes from the IteraTeR and Wikipedia edit-intent taxonomies.
   - Give it `evidenceStatus` and `basis: corrections`.
2. **The list of product modules and their gates** for Ghost's real-data module smokes: which modules, which gate tests, and the commit to pin.

Ghost's V23 closes Wednesday 21 October at 22:04 PDT. Whatever lands after that serves V24.

**From Sounding Line** (its kickoff packet):
- D21, the reader-convergence curve (section 4);
- D22, decision ledgers (section 10, item 2);
- D27, what a page keeps (item 3);
- D16 and V3, the how profile and its reliability thresholds (item 1);
- D1, the content-feature population model (item 14).

## 12. Don'ts

- No theme-to-drive mapping in preview.
- No hand-written readings, cached or otherwise. A cached real run is allowed as backup, labeled as cached.
- No per-person readings exported or published.
- No AI-use verdicts about people.
- No CoAuthor text in public.

## Sources

**Repository.** ToMpathy `codex/0.3-engine` `82789fd`:
- `STATUS.md`, `docs/ENGINE_V1.md`, `docs/ENGINE_INTERFACE.md`, `docs/CORE_VALUES_DESIGN.md`, `engine/README.md`;
- `engine/tompathy_engine/models/goal_producer.py`;
- `engine/tompathy_engine/packet/drives.py`, `engine/tompathy_engine/admission.py`.

**Data and dependencies:**
- Sounding Line `c95dff4ad`: `results/phase_2_4_stage_15/PHASE0_REPORT.md` and `PHASE0_SUMMARY.json`; `docs/design/stage-15/F4_NATIVE_READINESS.md`.
- Ghost Scale `d84e023a2`: `docs/versions/v23-research-division/TWIN_INPUT_CONTRACT.md`.

**Theory:**
- [Smith & Levy 2013](https://www.mit.edu/~rplevy/papers/smith-levy-2013-cognition.pdf).
- [Schmidhuber 2009](https://arxiv.org/pdf/0812.4360).
- [Blackwell & Dubins 1962](https://doi.org/10.1214/aoms/1177704456).
- [Sommers 1980](https://openlab.citytech.cuny.edu/fywpd/files/2019/01/sommors-revision-strategies.pdf).

**Provenance and detection:**
- [C2PA 2.4 specification](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) and [c2pa-js](https://github.com/contentauth/c2pa-js).
- [PAN 2025 generative-content task](https://pan.webis.de/clef25/pan25-web/generated-content-analysis.html).
- [Liang et al. 2023](https://arxiv.org/html/2304.02819v3).
- [Wikipedia: WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup).
- Boundary-detection accuracy: [Kushnareva et al.](https://arxiv.org/html/2311.08349v3); [M4GT-Bench](https://arxiv.org/abs/2402.11175).

**Payoff map:**
- [Sap et al. 2020](https://aclanthology.org/2020.acl-main.178.pdf).
- [Olsson et al. 2022](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html).
- [Wilmot & Keller 2020](https://aclanthology.org/2020.acl-main.161.pdf).

**Corrections:**
- [Du et al. 2022 (IteraTeR)](https://arxiv.org/pdf/2203.03802).
- [Gao et al. 2024](https://arxiv.org/pdf/2404.15269).

**Technical facts.** Transformers.js, WebLLM, Chrome's built-in AI, Wikimedia's APIs, limits and models, `mwedittypes`, WikiWho, `c2pa-web` and Vega were checked by the research pass on 16 October, against official documentation, package registries and source. See section J of `claude/STEAL_LIST_2026-10-16.md`.
