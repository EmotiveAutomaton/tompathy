# Driver implementation — 16 October 2026

Source: `TOMPATHY_DRIVER_2026-10-16.md`, revision 2. Implementation follows P0,
then P1 in its stated order. P2 and scientific admission remain separate work.
The curator is editing the essays concurrently; their text and image arrangement
are outside this implementation pass.

## October 17 local Clef and refreshed essay

The real pinned Clef-flash release now runs in its own CPU-only environment;
**Practice ToMpathy with Clef.cmd** selects it for technique decisions. The
ordinary launcher still uses fixed Qwen, and goals/corrections retain that
backend in both modes. The [runtime record](CLEF_LOCAL.md) contains release hashes,
installation steps, memory limits, measurements and local receipts. Research
environments, GPU services and authored essays were not changed.

Four constructed five-question calls took 43–48 seconds each and matched 15/17
prespecified labels. The two scored misses concerned tone; an unscored response
also confused an event changing with a contradiction. These smoke checks do not
estimate natural-essay accuracy or establish a fast CPU preview. Real service
checks covered authentication, schema/body bounds, cancellation (1.64 seconds),
reuse after cancellation and owned-process cleanup. Peak resident memory in that
check was 13.93 GiB. All inference used one CPU thread.

The current full-art capture is 15,602 words / 328 passages. The refreshed Clef
packet contains complete habits, departures and comparison, 100 answers from
20 joint Clef calls, seven of 21 goal groups, and 58/909 payoff sentences. The
first 20 passages are Clef's explicit coverage bound; the goal and payoff stages
remain partial, with no governing goal cover or personal-value estimates.
Preparing those Clef calls took 1,013 seconds. A 20-minute offline goal pass
stopped cleanly at its bound. Explicit offline packet assembly permits 600
seconds; ordinary live pages retain 165 seconds and all module caps are unchanged.

The first assembly exposed a software replay cost: validating and rendering the
large packet after each tiny cached update exhausted comparison's 25-second
budget at 650/1,312 readings. Grouping cached comparison updates and throttling
intermediate departure rendering completed all 1,312 in 11.9 seconds; final
scores and source spans are unchanged in focused tests. This does not accelerate
fresh inference or alter scientific criteria. Native Chrome 155, frontend build
`24b7ba901126`, loaded the final refreshed Clef packet in 0.88 seconds, showed the
actual agreement disclosure and all 100 technique answers, and located a selected
passage on the live source. Layout
checks and inspected screenshots passed; owned services and browser were closed.
The ordinary-backend check then exposed an aliased attention-frame rollback bug
after a module timeout. A constructed regression reproduced the same packet
rejection; restoring the rendered attention tree as a snapshot fixed it without
weakening validation. The integration and replay changes passed 41 affected
engine/CLI checks across serial runs, focused Ruff and the extension build. The
full suite was not repeated.

Receipts: `evidence/clef-cpu-benchmark.json`,
`evidence/clef-runtime-validation.json`, `evidence/art-preparation-*.json`,
`evidence/preview-clef-cache-before-replay-fix.json` and
`evidence/preview-clef-cache-validation.json`.
[Current review steps](LIVE_PRACTICE.md#prepared-full-essay-review).

The ordinary fixed-Qwen launcher passed its final native rerun after the rollback
fix: packet assembly 276.6 seconds under the explicit offline allowance, cached
loading 0.85 seconds. All 328 departures and 1,312 comparison readings completed.
Its separate technique stage reached 26/100 checks, goals 7/21 groups, and payoff
52/909 sentences. Timeout recovery, source selection and layout passed; screenshots
were inspected and the owned companion/browser closed. Receipts:
`evidence/preview-cache-before-rollback-fix.json` (failure) and
`evidence/preview-cache-validation.json` (passing rerun).

## October 17 incremental reading and speed pass

Live preview now takes turns between modules on the same CPU worker. The first
attention result can arrive after a 512-token scoring window, and the selected
passage is visited first with its original preceding context. Goal grouping gives
that passage its own first judgment and covers every remaining passage in at most
19 additional contiguous groups. A slow call can still hold the worker until its
bounded timeout; the scheduler does not make the fixed 9B model itself faster.

The teardrop reserves an outline from these captured source groups before goal
judgments arrive. Later nodes occupy those fixed places, with stable IDs and a
stable camera. The reserved space is layout only, not an invented goal or parent
relation. Attention and payoff rankings remain provisional as coverage expands.

Small words and pie indicators beside the menu report actual completed work;
unknown totals use an indeterminate indicator. Completion becomes a check for
2.6 seconds and fades. Paused or failed work never gets a success check. A paused
reading offers **Continue reading**, retaining the previous display until cached
replay catches up. Coverage is not an accuracy percentage.

Scoring caches now retain exact completed 512-token windows, including work
inside an interrupted paragraph, plus a bounded in-memory tokenization cache.
Coalesced, validated progress uses compact top-level updates over the existing
stream. Checkpoints are saved during work, and replay cannot overwrite a more
complete reading. These changes retain the existing 2,048-token finite window,
source-word alignment, holdouts and CPU-only default. No speculative KV reuse,
cross-request batching or GPU concurrency has been enabled.

An optional loopback **Clef-flash** adapter sends five technique questions in one
SystemOne call per passage, caches the joint answer, and marks every result
unvalidated. It does not replace token scoring, generate goal labels, or inherit
the fixed-Qwen reader's constructed eligibility. The adapter contract is exercised
with software fixtures; at this earlier checkpoint no Clef weights had been
downloaded or run. The later local-runtime pass above supersedes that limitation.
Its [official model card](https://huggingface.co/Cloudflare/clef-flash)
describes a 9B Qwen3.5 backbone and a joint decision head, with a tested environment
different from this checkout. Hosted benchmarks are not local CPU measurements.
See [configuration](../engine/README.md#optional-clef-flash-and-reader-settings).

A bounded CPU precision check on a 200-word public excerpt found a material
tradeoff. Default dynamic-int8 scoring took 1.00 s versus 3.44 s for float32, but
their top-decile Jaccard overlap was 0.50 and rank correlation 0.764. Per-channel
int8 took 0.88 s versus 2.92 s in its paired float32 run, with overlap 0.364 and
correlation 0.733. Model load was separate. This is one excerpt, not a scientific
comparison or proof of accuracy. The default remains unchanged; float32 and the
experimental per-channel setting are explicit options. Receipts are local:
`evidence/reader-parity.json` and `evidence/reader-parity-channel.json`.

The October 16 full-essay packet below belongs to its earlier implementation.
At this earlier checkpoint, the new implementation hash required a fresh packet
run; the local-runtime pass above has now refreshed it using compatible exact
model-call caches. Complete goal/payoff coverage and the 15-second target remain
undemonstrated.

Verification for this pass: the 198-test engine suite passed, followed by four
additional mocked Clef wire-contract cases (valid joint result, missing question,
nonfinite score, invented option). Ruff and the production build passed. All 42
frontend core cases passed across the full run and the repaired fixture rerun.
`playwright.components.config.ts` verifies the production-bundled graph and
progress controls at 360 px, including stable outline/node positions, adjacent
menu placement, pause/continue, completion fading and no page errors. Initial
Vite fixture attempts stalled during CSS transformation; the focused test uses
the extension's esbuild path instead. The earlier full browser suite was not
rerun for this pass.

Native Chrome `155.0.8059.82`, final build `24b7ba901126`, passed automatic capture,
compact streaming and real CPU attention/agreement/payoff on a short constructed
page with an isolated score cache. Its goal/technique backend was disabled for
this bounded integration check; their scheduling is covered by software fixtures.
Screenshots were visually inspected, and owned companions and disposable browsers
were closed. Receipts: `evidence/incremental-native.json`,
`evidence/incremental-test-results.json`, `evidence/incremental-progress.png` and
`evidence/incremental-native-indicators.png`. The native receipt's elapsed field
starts after its progress screenshot, not at cold launch or capture.

## Evidence and boundaries

- Sounding Line's `F4_NATIVE_READINESS.md` identifies the original fixed Qwen
  reader's constructed eligibility for Q1/Q3/Q4/Q5/Q7/Q8/Q9. A different model,
  prompt or runtime cannot inherit those labels. Natural-data admission is absent.
- `PHASE0_SUMMARY.json` supplies public historical forecast comparisons. It does
  not supply seven numerical drive priors. Missing drive priors must stay missing.
- Small causal readers require an explicit local installation and file-hash pin.
  Analysis must never download weights or contact a hosted inference service.
- Reader comparisons must align words by source offsets across tokenizers;
  token indices from different vocabularies are not comparable observations.
- CPU timing targets are acceptance targets, not existing measurements.

## Implemented paths

- Separate preview orchestration, default-on frontend toggle, per-panel notice,
  evidence/status badges, strict labels/relative-support validation, progressive
  packets and cancellation. Preview off calls the unchanged admitted builder.
- Hash-pinned Qwen2.5-0.5B and SmolLM2-360M CPU readers, exact-call caches,
  word-aligned departures and two-context comparisons. Names/numbers, URLs,
  fenced/inline code and captured HTML code spans are held out.
- Deterministic page-shuffle phrasing controls, quoted-text separation, rhythm,
  connectives and punctuation. These are surface descriptions, not person traits.
- Dedicated fixed Qwen 3.5 9B / Ollama 0.40.3 service using the exact original
  constructed-tested literal reader. Q1/Q3/Q4/Q5/Q7 technique notes and Q8/Q9
  correction hooks are bounded and cached. Q6/Q10 remain disabled. Goal
  judgments use a separate unvalidated prompt with constrained root-cue IDs,
  title/headings/meta/revision summary, at most 20 local groups plus a cover.
- Pseudonymous source-scoped makers, local name reveal, bot flags, witnessed
  changed-byte counts, observed reverts, literal correction directions and
  unsigned Git tool declarations. Whole-page readings belong to an unresolved
  artifact maker, never the most active editor. Future revisions are excluded.
  Git boundary diffs fetch the actual parent file without inventing a parent
  revision. Completed Q8/Q9 pairs publish immediately; history corrections and
  technique notes each get a 45-second active-work budget on T1, interleaved with
  the other available modules.
- Two payoff layers with source holdouts, repeated-token controls and matched
  ordered/shuffled context lengths. The synopsis condition uses title/meta;
  its shorter context is disclosed. Layer 2 compares earlier paragraph windows
  and skips pages with more than 20 paragraphs. These are unvalidated probes.
- Real Phase 0 aggregate comparison, curator drive vocabulary, conditional
  supplied 20-quantile dots, no invented drive priors or theme-to-drive mapping.
- Explicit GitHub file history, optional memory-only token, quota/declaration
  share; Wikipedia tags, API user-agent and bounded Retry-After handling.
  History failures retain T0 preview. Public history caches expire in six hours.
- Integrity-checked real-run backups with timestamps. **Load cached real
  preview** can load an exact-input partial backup with its missing-module
  statuses intact. Per-person preview exports and all preview registry
  publication are refused.

## Measurements and acceptance status

All receipts below are local, ignored software-verification records under
`evidence/`; none is a scientific admission.
October 16 native review: Chrome `155.0.8059.82`, build `8df5c77cb5b4`; cached loading
1.05 seconds. The screenshot inspection and geometric checks confirm that the
attention cloud stays inside its panel and the process list starts below its
status controls. Owned test companions and disposable browsers were closed.

| Check | Observed result |
|---|---|
| 3,000-word Qwen float32 CPU scoring | 173.3 s, plus 12.7 s load |
| Same text, dynamic-int8 CPU scoring | 64.2 s, plus 14.4 s load; misses 15 s target |
| Exact fixed-Qwen Q1 smoke | Passed, 27.3 s first call; misses 20 s first-result target |
| Native Chrome 155 preview | Real CPU readers, service-worker relay, three notices, labels, maker default, progressive results, preview-off path passed |
| Native visual inspection | Disclosure selectors, heading overlap and history-list positioning repaired; single-node graph and badge bounds refined |
| Five real public pages | All returned within 165–167 s with explicit module states; one news goal failure, recorded in `preview-live-pages-audit.json` |
| Frontend regressions | 39 unit checks and all 58 browser scenarios passed across the reruns; build passed |
| Engine regressions | All 186 tests passed after final engine refinements; Ruff clean |
| Live cancellation | T0 news during technique inference and T1 Wikipedia/GitHub during correction inference cancelled, stayed healthy and accepted a subsequent request |
| Full-essay cached review | Real dated packet loads in about 1.2 s; agreement passages locate source text; Follow pages reads a blog and the essay without another toolbar action |

The live page budget is 165 seconds, with explicit module limits. Validated
partial results survive budget exhaustion. The small-reader CUDA option is
implemented but unmeasured; this pass uses CPU. The fixed 9B reader retains its
tested CPU/runtime identity. A faster or different literal backend cannot borrow
its constructed eligibility.

The first news-page run rejected an unavailable goal-cue reference. The preview
goal schema now constrains references to supplied cue IDs. Its focused real-model
recheck produced three validated local nodes before its 180-second limit, with
no governing cover. This verifies the repaired reference path, not complete goal
coverage or the full-page timing target. Receipt: `evidence/preview-goal-recheck.json`.
History fetch/reconstruction and software validity do not establish
correct inferred intentions or values.

## Remaining checkpoints

- Full-art reader preparation completed on CPU in 519.5 seconds after some exact
  calls were already cached. Transient equation-loading placeholders exposed
  changing capture hashes; the adapter now excludes them. A 24.3-second score
  refresh and a 166.1-second packet run completed the current 15,602-word,
  328-passage capture. Its comparison uses 9,961 common eligible words. Top-decile
  Jaccard overlap decreased from 45.3% to 43.5%, and rank correlation from 0.790
  to 0.752 with the longer context.
  This is a measured disagreement with the expected convergence, not a reason
  to change the thresholds. Receipts: `evidence/preview-preparation.json` and
  `evidence/preview-preparation-stable.json`; the final packet run is recorded in
  `evidence/preview-cache-preparation.json` (including that run's later UI-test
  selector failure). The exact final revision is
  `08d9b05c4935b67c9228a31e3f36a8442430d7b175e6d7c4018c5213b1b97a69`.
- The October 17 refresh above supersedes the earlier 12-judgment backup. Goal
  and payoff coverage remain partial. A full-essay novel-span payoff acceptance
  result is still absent; retention measured on a partial prefix is not full
  coverage. Current native review receipts are `evidence/preview-clef-cache-validation.json`
  and `evidence/preview-clef-*.png`. [Review steps](LIVE_PRACTICE.md#prepared-full-essay-review).
- Numerical drive priors remain unavailable. D21/D22/D27/D16/V3/D1 remain gated
  on their own Sounding Line results. Its October 16 review reiterates common
  source spans and explicit finite context windows. Reader pilot v3 failed its
  Pythia direct/cached numerical comparison; the following diagnostic lost its
  resource floor. Neither supplies a usable scientific result. ToMpathy uses
  direct CPU scoring and does not inherit admission from their separate runtime.
- Maker acceptance currently has constructed tool-trailer coverage and live
  Wikipedia/GitHub attribution coverage. A live essay with a verified retrieved
  tool trailer still needs its own acceptance run. C2PA signature/trust ingestion
  and broader editorial-flag ingestion are not implemented by this adapter pass.
  Slash-containing Git refs need URL encoding; automatic ref disambiguation is
  still available only in the separate lightweight context collector.
- Retest Chrome 156 on October 20 and rehearse on October 21. These future
  checkpoints have not run. P2 stays after Thursday. Ghost module-gate work is
  conditional on P0 and P1.1–4 readiness, not a completed handoff here.
