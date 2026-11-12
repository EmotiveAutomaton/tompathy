# ToMpathy's three views: what to build and what to test, carried forward (18 October)

*Spec addendum to the 18 October packets for ToMpathy, Sounding Line and Ghost Scale Sim. It covers the Core values panel's three tabs as the curator described them at 14:14, drawn on his canvas "ToMpathy values panel: three views". Every decision is made here.*

*Timing:*
- *Nothing here enters a queue before Thursday 22 October, 07:00 PDT.*
- *Nothing touches Track A or the Tuesday freeze.*
- *No admission changes before Monday 26 October, per the ToMpathy packet's rule.*

## 0. The top ten, in order

**The finding that orders the list:** on a real page, the flame is gated by admission, not by engineering.
- The preview removes drive items by design.
- An admitted packet draws a drive tip only through a chain of seven links (section 1), and the checkout has none of the admissions that chain needs.

So the tabs get built now, as views over the right packet fields. The science items produce what admission needs.

| # | Item | Who | Why it ranks here |
|---|---|---|---|
| 1 | **B13. A Q10 that can say "nothing here"** | ToMpathy | Every drive tip needs Q10. The local Qwen answered "care" for 19 of 20 theme-free sentences, so as it stands it would paint fire on every page |
| 2 | **LT0. The corpus theme read** | Sounding Line | LT1, LT3 and the N19 calibration all need Q10 labels on the offered suggestions. No card produces them yet |
| 3 | **LT1. Do motivations recur within a writer?** | Sounding Line | The lattice means something only if a writer's tips recur across prompts more than across writers |
| 4 | **N19. Lattice recovery and the per-work budget** | Ghost | Sets how many decisions each work needs, which is the compute bill, and is a constructed-world witness the admission needs |
| 5 | **CL1. Can Clef carry bulk reads?** | Sounding Line | Decides whether Clef serves many-work reads, and how fast |
| 6 | **B14. The tabs' packet fields and honest states** | ToMpathy | The build: the canvas becomes the panel, and every non-admitted state says which link is missing |
| 7 | **B16. Scope by consent (amends B9)** | ToMpathy | Required before the creator tab reads anything beyond the owner and explicit links |
| 8 | **N21. When is fire real?** | Ghost | Separates multifinal works from reader artifacts, and checks whether dilution hides real fire |
| 9 | **B12. The admission chain, written down** | ToMpathy | One page naming each link, its owner and its state, so the empty states and the studies point at the same list |
| 10 | **LT3 and N20. How far "as of today" moves old works** | Sounding Line, Ghost | Puts a measured number on the label the curator asked for |

**Later:** B15 (reading many works), B17 (global), LT2, LT4 and N22. B6, Q9's failure analysis, stays where Track B has it; it gates the corrections route.

## 1. What the engine supplies today (`5f3ad0a`)

**Values in the preview.**
- The Core values module is "complete" only when the packet carries population items; otherwise "unavailable".
- Its detail line: choices, content corrections, stated goals and revision history would move these estimates; "text topics are never converted to drives".
- The preview strips every revealed-theme drive item, even from an admitted upstream packet (`preview/build.py`, lines 177 to 182). A preview packet never carries a drive tip.

**The chain for one drive tip** (in an admitted packet):
1. An admitted revealed-comparison preference fit with covariance for the domain: `backbone-preferences`, `literal-preferences`, `corrections` or `joint-preferences`. `apply_drives` runs only after one of them succeeds (`packet/modules.py`).
2. Q10 admitted on the transcriber pin.
3. `drive-recipes` admitted, with Ghost and Sounding Line witnesses and the real-data gate (`admission.py`).
4. Production records. Tier T0, final text, returns nothing.
5. A population with conditional covariances.
6. For the corrections route, Q8 and Q9 admitted. Q9 is disabled (B6).
7. SEEKING: no producer. "SEEKING awaits a separately tested pursuit-vigor interpretation" (`docs/ENGINE_INTERFACE.md`).

The checkout holds no admission records outside test fixtures.

**The drawing rule.** A drive counts as strong when the lower bound of its 95% interval is above zero (`packet/drives.py`). The tabs use that rule for "drawn" against "named, not drawn".

**Q10 as it stands.**
- Neither reader returns an empty theme set: Qwen answered "care" for 19 of 20 theme-free sentences (`THEORY_PASS_2026-10-17.md`, section 11).
- Haiku failed Q10's battery.
- The preview's seven receipts are Q1, Q3, Q4, Q5, Q7, Q8 and Q9.

**Readers and caches.**
- The Clef adapter answers Q1, Q3, Q4, Q5 and Q7 and "never claims fixed-reader eligibility".
- Reader answers are already cached by reader identity, prompt and input, not by the implementation hash: `transcribe/runner.py`, `preview/judgments.py`, `preview/clef.py`, `preview/readers.py`.
- The transcriber's pin digests the whole question catalogue, so editing one question's prompt voids every question's answers and receipts on that pin.

**Population.** `population/build.py` reports "unavailable: awaiting admitted population model". It already takes `until=`.

**Context.**
- Light context reads up to three explicit creator links. Agent search adds one hop, for six sources in all.
- `PRIVACY.md` says ToMpathy does not "create a model" of the creator.

**Compute.**
- A goal call takes about 170 seconds on the one-thread CPU pin.
- Clef takes about 50 seconds per decision on CPU. clef-flash is a Qwen3.5-9B fine-tune of 11 to 12 GB, the same class as the fixed pin; its gains come from several questions per request and from parallel slots on the GPU.
- Sounding Line's P1 scored 69,109 suggestions with five readers in one overnight GPU run. Bulk reading here is a GPU job.

**About the canvas.**
- Its passages feed its tips, for legibility. In the engine, tips come from choices and corrections.
- SEEKING appears on the canvas as part of the concept; the engine draws it only after a pursuit-vigor interpretation is tested.

## 2. ToMpathy: B11 revised, then B12 to B17 (Track B, from Thursday 07:00)

**B11 v2. The three views live in the Core values tabs.** This replaces B11's inset in Expertise and keeps B11's devaluation probe.

All three tabs draw the same teardrop facing right:
- evidence rows on the left;
- motivation tips at the right edge;
- time running down.

**States, in every tab:**
- **Illustration:** the safe example only, labelled "Illustration (authored)".
- **Admitted:** tips drawn by the rule in section 1.
- **Preview:** structure without tips, plus the first missing link from B12 (for example, "No admitted theme reader").
- **Final text only:** a hollow body or tape, with the reason.

**Current work only (the flame).**
- **Rows:** the work's evidence units in order: decisions, revisions, or passages that carry production records.
- **Bands:** one translucent band per row and tip above the rule, all overlaid.
  - Nothing else draws "fire". A work whose tips share rows looks like a flame because its bands overlap (B14's `coSupport`).
  - No flame score, no flame icon.
- **Lattice strip:** dotted vertical lines link the rows that feed the same tip.
- **Interaction:** hover or focus a tip to isolate it and light its rows; click holds it. Tip labels are 44 px targets.
- **Under the plot:** three different statements, never merged:
  - "named, not drawn" (below the rule);
  - "no evidence";
  - "no admitted reader".

**Creator (a life of works).**
- **Rows:** in-scope works (B16), dated and spaced by time. Each is a tape: a small teardrop with one tongue per drawn tip.
- **Lattice:** dotted vertical lines join the same tip across successive works.
- **Bands:** from each work to the creator-level tips. The current work's tape and bands are amber.
- **On the graph, in words:** "As of [date]. Every work is re-read with today's evidence." This is the curator's rule. LT3's measured shift is added when it lands.
- **Final text only:** a dashed tape with no tips.
- **While running:** "n of m works read". "Sources" opens the existing context timeline.

**Global.**
- Stays unavailable (B17).
- The canvas's Global board is the target:
  - periods as rows;
  - a spread column;
  - a dashed trend row;
  - trend words at the tips ("rising", "falling", "steady");
  - an "Illustration only" badge.
- The label never says "volition". A trend shows where values have been moving. Coherent extrapolated volition asks what people would want "if we knew more, thought faster" ([Yudkowsky 2004](https://intelligence.org/files/CEV.pdf)), and only a converging spread speaks to its "coherent" part (N22).

**Build order:**
1. The canvas as the illustration in the safe example.
2. The owner's own works, after `PRIVACY.md` is updated (B16).
3. Other creators, only under B16.

Badges stay "untested" until LT1 and N19 report.

**B12. The admission chain, written down.**
- Add `docs/DRIVE_ADMISSION_CHAIN.md`, listing section 1's seven links, each with its owner (ToMpathy, Sounding Line or Ghost), its state, and the item here that moves it.
- The panel's preview state names the first missing link from this file.
- No admission record changes before Monday 26 October.

**B13. A Q10 that can say "nothing here".**
- **Before any run, pre-register:**
  - the revised Q10 prompt, which allows and explains the empty set;
  - its battery: 200 items, at least 40 of them theme-free.
- **Scoring:** empty-set accuracy on the theme-free items, beside the 17 October gate (exact-set accuracy, and recall of at least 0.70 for every theme tag).
- **Pin.**
  - First split the transcriber pin per question: model, that question's template, settings. Editing Q10 then leaves the other receipts valid.
  - The split changes every pin, so it lands with B7's `live-gpu-2`, which needs fresh receipts anyway. Run all eight batteries there once. The fixed CPU pin and `live-gpu-1` stay as they are.
  - Q10 is asked in its own call, never joined with other questions, so its edits stay separable.
- **Clef.** Add Q10 to the Clef adapter behind the same battery only if CL1 passes.
- **If no pin passes,** drives stay off, and the panel says "no admitted theme reader".

**B14. The tabs' packet fields and states.** For each work, emit:
- `tips[]`: id, support with its interval, and status (drawn, named-not-drawn, no-evidence or no-admitted-reader);
- `rows[]`: evidence units, with order and date;
- `feeds[]`: row to tip, with weight;
- `coSupport`: for each pair of drawn tips, the share of supporting rows they share;
- `evidenceTier`: T0 or production;
- `asOf`;
- `firstMissingLink`: from B12.

Tips come only from admitted modules. The preview fills structure, never drive tips.

Acceptance, with a test for each:
- the example reproduces the canvas's structure, with illustration provenance;
- a Wikipedia page with history and no admitted modules shows rows, no tips, and names the first missing link;
- a plain page shows a hollow body, with the T0 reason.

**B15. Reading many works (later).**
- **Batched requests.** Several questions per request make a new pin, which needs its own receipts (B7's rule). Key cached answers per joint request.
- **Selection.** Directed reading inherits B1's gate and Ghost N16's random share, not a fixed 20%. Log selection probabilities.
- **Order of works:** DR1's route.
- **Join.** Creator tips come from per-work tips by the same aggregation, one tier up.
  - An edge needs the tip drawn in two successive works with production records.
  - Each edge lists its works.
- **Time.**
  - Show fits with all evidence to date, labelled "as of".
  - Store as-of-then fits (`until=` each work's date). Answers come from the cache; only the fits rerun.
- **Progressive.** The tab fills tape by tape. A run can be cancelled and resumed.
- **Expectation.** On CPU pins this is a background job; near-live needs the GPU. The owner's works are prepared ahead.

**B16. Scope by consent, not search. This amends B9.** A work may join the creator view only by one of these routes, each at most two hops from the page:
- **Owner:** the owner supplied it.
- **Explicit link (hop 1):** the page's named author links it.
- **Works list (hop 1 or 2):** a list of works the author publishes on the same origin as their explicitly linked page.
- **Two-way profile (hop 2):** a profile the author links that links back to the author's page with `rel="me"`. This is the check [Mastodon uses to verify links](https://docs.joinmastodon.org/user/profile).

Never use:
- search engines;
- same-name matching;
- style or timing matching;
- pseudonymous editors.

**Privacy.**
- `PRIVACY.md` promises ToMpathy doesn't "create a model" of the creator. The creator tab is that model, across works.
- Update `PRIVACY.md` and add an in-panel disclosure before build step 2, the owner's own view.
- Draw the motivation lattice only for:
  - the owner;
  - creators who publish a works list or two-way links.
- Everyone else gets today's context timeline and "current work only".

**Tests,** with B9's test updated:
- a one-way profile is excluded;
- a two-way profile is included;
- the same name on a different person is excluded;
- a third hop is excluded.

**B17. Global: decompose before displaying (later).**
- `population/build.py` stays "unavailable" until a population model is admitted.
- When LT4 lands:
  - per-period aggregates, with within-maker change separated from entry and exit;
  - a spread per period;
  - trend rows only with intervals.
- Never per-person output. Maker ids stay hashed.
- The dashed row needs both a mean trend and a spread trend, plus N22's rule for when a falling spread is convergence rather than attrition.

## 3. Sounding Line: new cards

**Authorization.**
- In the post-talk window, after SDT1 and before the backlog: each card's protocol, known-answer design and cost pilot.
- Production runs open the next campaign.
- These cards are descriptive. Any admission witness follows the admission path separately.
- Section 0's defaults of the week packet hold. None of these cards counts toward family null counters. Standing decisions S1 to S7 apply.
- A card blocked on a receipt is marked blocked (S6), naming B13 or CL1.
- Pin ToMpathy at `certified-fit-1` (`5f3ad0a`), as the EV cards do. The older default pin, `82789fd`, has no `preview/clef.py`.

**CL1. Can Clef carry bulk reads? (instrument)**
- **Reader:** Clef, pinned by revision and sha256 on loopback as its adapter requires, on Q1, Q3, Q4, Q5 and Q7.
- **Primary:** Clef's accuracy on the same 200-item constructed batteries the receipts used, per question. The receipted pins' accuracy is already recorded (the fixed pin passes these five at 100%), so the comparator doesn't rerun. Pass at 0.95 or better on every question.
- **Secondary:**
  - inter-reader κ against `live-gpu-1` on about 1,200 real decisions from P2's 16,855 (20 per writer, stratified by prompt and genre); if `live-gpu-1` has no receipts, skip this measure (S1);
  - units per hour on the GPU;
  - on CPU, a 50-decision Clef pilot.
- **Q10:** joins only after B13 has put a passing battery on a pin.
- **Cost:** at most 6 GPU-hours, with S4 applying; the CPU pilot at most 1 CPU-hour.
- **Route:**
  - **Pass:** Clef serves bulk reads on those questions, with its own receipts.
  - **Fail:** bulk reads use the receipted GPU pins.

**LT0. The corpus theme read (instrument).**
- **What:** Q10 on every offered suggestion in P2's sessions (69,109), by the pin that passes B13.
- **Cost:** GPU, capped at 16 GPU-hours, P1's overnight scale. If the pilot projects past the cap, read a stratified half of sessions (S4).
- **Privacy:** labels stay private; cards get aggregates.
- **Blocked** until B13 passes.

**LT1. Do motivations recur within a writer? (hypothesis test)**
- **Unit:** a session (one prompt) counts as one work.
- **Profile:** the session's revealed-theme contrast, Q10 themes of accepted against dismissed suggestions, from LT0.
- **Known-answer rung, in Q10 coordinates, before any real contrast.**
  - Plant writer-specific theme preferences into constructed accept decisions over the real offered suggestions and their LT0 labels, at δ in {0, 0.2, 0.4, 0.8}.
  - Pass: plants found at δ = 0.4, with a false-positive share of 0.1 or less at δ = 0.
  - Otherwise the card reports "blind in Q10 coordinates" and stops.
  - V4's taste lens plants in a different, lexical space and is already blind. Its label doesn't govern this card.
- **Similarity of profiles in three groups:**
  - same writer, different prompt;
  - different writer, same prompt;
  - different writer, different prompt.
- **Primary:** same writer, different prompt minus different writer, different prompt. Direction: positive.
- **Prompt control:** report the primary as a share of the prompt's own effect (different writer, same prompt, minus different writer, different prompt).
- **Route:**
  - **Positive:** the creator lattice may draw motivations once admitted, badged "tested on CoAuthor".
  - **Null or blind:** motivations stay "untested", and the creator tab leads with works and dates.
- **Cost:** under 2 CPU-hours after LT0.

**LT2. What can final text alone say? (instrument, later)**
- **Works:** those with both final text and production records: CoAuthor final documents with their logs, and Wikipedia articles with their histories.
- **Compare:** text-only theme profiles (preview, never admitted) against production-derived profiles for the same work.
- **Primary:** rank agreement per work, by genre.
- **Route:**
  - **Low:** final-text tapes stay hollow.
  - **High:** a labelled "themes in the text" overlay may be shown, never as drives.
- **Cost:** under 1 CPU-hour after LT0.

**LT3. How far does "as of today" move older works? (instrument)**
- **Writers:** at least 12 sessions (DR1's set).
- **Fits:** each session's profile as of that session, against as of the writer's last session.
- **Measures:** median absolute change, and the share of tips that cross the drawing rule.
- **Route:** the creator graph's "as of" line quotes the measured shift.
- **Cost:** under 1 CPU-hour after LT0.

**LT4. Drift: are writers changing, or is the population? (hypothesis test, later)**
- **Data:** Wikipedia histories, aggregate only, with hashed maker ids and no per-editor output.
- **Decomposition:** split period-to-period change into within-maker change and the change from people entering and leaving. Report the spread per period.
- **Primary:** the within-maker share of total change. Descriptive; no direction is registered.
- **Why:** aggregate change can differ in sign from individual change ([Robinson 1950](https://doi.org/10.2307/2087176)).
- **Opens after LT1 to LT3.** Its protocol sets sample and cost.

## 4. Ghost: V24 candidates N19 to N22

**Budget and rank,** within V24's authorized 40 pilot CPU-hours:
1. N16's promotion and FX1's redesign keep first claim.
2. N19 (4 CPU-hours) and N21 (3) rank next, ahead of the 17 October list's queued families, because they feed the engine directly.
3. N20 (2) runs as an arm of the queued "decaying set points" family, not separately.
4. N22 (3) waits behind the queued families.

Production batches follow V24's rules, after Monday 26 October, 08:00. The house sequence applies.

**The reader model, used in all four.**
- **Before B13 lands:** symmetric tag flips at 0.1, plus a bias arm that adds "care" to theme-free items at Qwen's measured rate (19 of 20).
- **After B13:** each pin's measured Q10 confusion from its battery, including its false-theme rate.

**N19. Lattice recovery and the per-work budget (pilot cap 4 CPU-hours).**
- **Worlds:**
  - makers with seven latent set points that drift slowly over 6 to 12 works, each work sampling decisions;
  - a genre arm, in which works share themes by topic with no maker signal.
- **Measures:** per-work tip recall and precision under the drawing rule; lattice-edge precision; creator-tip error; the false-lattice rate in the genre arm.
- **Primary:** decisions per work needed for 0.8 tip recall at 0.9 precision.
- **Route:** the budget table goes to B15, and the result is offered as a constructed-world witness for B12's chain.

**N20. Does "as of today" flatten drift? (pilot cap 2 CPU-hours, inside "decaying set points")**
- **Worlds:** careers with true drift of known size.
- **Compare:** as-of-then against as-of-today estimates under pooling across works.
- **Primary:** estimated drift as a share of true drift. Pooling toward a life's mean can flatten real change.
- **Route:** LT3 checks the number on real data; the creator graph's label quotes it.

**N21. When is fire real? (pilot cap 3 CPU-hours)**
- **Worlds:** works with k = 1 to 4 true motivations and set shares of co-supporting decisions.
- **Arms:**
  - **Reader correlation:** theme labels co-occur without any motivation behind them, which makes false tongues.
  - **Care bias:** the arm described under the reader model.
  - **Dilution:** each added goal lowers how instrumental the shared means looks for every goal ([Zhang, Fishbach & Kruglanski 2007](https://doi.org/10.1037/0022-3514.92.3.389)). A truly multifinal work ([Kruglanski et al. 2013](https://doi.org/10.1177/1088868312453087)) can then show several weak tips, each under the rule.
- **Measures:** recovery of k and of co-support; the false-tongue rate.
- **Primary:** recovery of k at N19's budget.
- **Route:** the renderer's rule. If dilution pushes real tips under the rule, B14 tests a work's pooled support before splitting it into tips.

**N22. Drift, composition and convergence (pilot cap 3 CPU-hours).**
- **Worlds:**
  - members drift;
  - membership changes;
  - dissenters leave.
- **Estimators:** aggregate means; within-maker fixed effects; entry and exit decomposition; the spread trend.
- **Primary:** how often attrition alone looks like convergence.
- **Route:** B17's rule for the dashed row.

## 5. Routes

| Result | What changes |
|---|---|
| B13 passes on a pin | LT0 can run. Drive tips still need the rest of the chain |
| B13 fails everywhere | The panel says "no admitted theme reader"; drives stay off |
| CL1 passes | Clef carries bulk reads on Q1, Q3, Q4, Q5 and Q7 |
| LT1 positive and N19 sets a budget | Motivations may enter the creator lattice once admitted, badged with both |
| LT1 null or blind | The creator tab shows works and dates; motivations stay "untested" |
| N21 finds dilution | Pooled support is tested before tips split |
| LT3 and N20 | The "as of" line quotes a measured shift |
| LT2 low | Final-text tapes stay hollow |
| LT4 and N22 | The global tab may leave "unavailable" |

## 6. Pre-mortem

- **Admission takes months.** The tabs then show the illustration and honest empty states for a long time.
  - *Guard:* that is acceptable and true. B12 makes the wait legible.
- **Q10 paints fire everywhere.** A reader that never returns an empty set gives every page tongues.
  - *Guard:* B13's theme-free items, and N21's care-bias arm.
- **Tips don't recur within writers (LT1 null).** Then the lattice draws the prompt or genre, not the person.
  - *Guard:* LT1's prompt control, N19's genre arm, and the "untested" badge.
- **Dilution hides real fire.** The most multifinal works would look the least motivated.
  - *Guard:* N21's dilution arm and the pooled-support test.
- **Scope creeps into profiling.** "Find more of their work" turns into search.
  - *Guard:* B16's routes and tests, and the privacy update before the owner view.
- **Creator runs take hours on CPU.**
  - *Guard:* existing answer caches, owner-first preparation, GPU batches with their own receipts.
- **The canvas is mistaken for engine output.**
  - *Guard:* every board carries "Illustration (authored)" or "Illustration only".

**Triggers (the only reasons to contact the curator):**
- a privacy defect;
- a result that reverses a delivered public claim.

## Sources

- [Yudkowsky 2004, Coherent Extrapolated Volition](https://intelligence.org/files/CEV.pdf)
- [Kruglanski et al. 2013, Features of multifinality](https://doi.org/10.1177/1088868312453087)
- [Zhang, Fishbach & Kruglanski 2007, The dilution model](https://doi.org/10.1037/0022-3514.92.3.389)
- [Robinson 1950, Ecological correlations and the behavior of individuals](https://doi.org/10.2307/2087176)
- [Mastodon documentation, profile link verification](https://docs.joinmastodon.org/user/profile)
- **Code**, under `engine/tompathy_engine/`:
  - `preview/build.py`
  - `packet/modules.py`
  - `packet/drives.py`
  - `admission.py`
  - `transcribe/runner.py`
  - `preview/clef.py`
  - `preview/judgments.py`
  - `preview/readers.py`
  - `population/build.py`
  - `preview/receipts/`
- **Docs:** `docs/ENGINE_INTERFACE.md`, `PRIVACY.md`, `THEORY_PASS_2026-10-17.md` (section 11)
