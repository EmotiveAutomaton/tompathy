# ToMpathy status

Updated 17 October 2026. **0.3.0-beta.1** development is on `codex/0.3-engine`,
based on the merged, owner-approved **0.2.0** frontend milestone.

The final owner walkthrough is implemented: dictated prose/caption edits,
natural aspect ratios for the opening diagram and Schadenfreude, fear order
1/4/3/2, black Pixar Cheaters border, and the replacement grey-bordered closing
image. The Review desk links to the safe example, which now shows current
drive/value artwork and seven explicitly unknown drive channels. “Mark likely
AI” draws a red checkbox X and outlines nodes with documented attribution or a
separately supplied calibrated probability above 50%. No general AI detector was
added; ordinary confidence is never converted into authorship probability.

The control sits on the right beneath Expertise, remains faint while off, and
becomes fully opaque when checked. Its centered red X extends beyond the box.
AI borders paint above all green cells; a union mask keeps joined areas' outer
borders intact and their internal seams thin. Opacity uses the same confidence
as the text, and thickness follows its involvement categories (edited, curated,
unreviewed). This display mapping does not admit AI attribution from Ghost Scale
confidence alone. The three fictional examples retain their explicit attribution.
Build **9e33a524fa18** passed 44 core checks, two focused browser cases (including
pixel verification of a partial shared edge), and native Chrome 155 placement,
centering, weighting and keyboard checks. Screenshots were inspected; evidence
is in `evidence/ai-mark-validation.json` and `evidence/ai-mark-native.png`.

The complete engine test suite and Ruff check also passed before the milestone
commit. The regenerated website handoff passed its browser test. The local
0.3.0 ZIP was rebuilt and verified byte-for-byte against `dist`. One disposable
static test server needed explicit ownership-checked cleanup after its test
passed; no research service was stopped.

The [website handoff](docs/WEBSITE_ESSAY_HANDOFF_GUIDE.md) contains exact text,
placement, 27 images, two diagrams, an offline preview, citation metadata and a
hash manifest. Run `node scripts/export-essay-handoff.mjs` to generate its
directory and ZIP from tracked inputs; generated duplicates stay out of Git.
All 27 curator files were
moved and hash-verified in `docs/archive/essay-curation/2026-10-17/`; active images
remain in `src/assets/essays/`. The [citation audit](docs/CITATION_AUDIT_2026-10-17.md)
records six unresolved access checks and four claim-scope cautions.

The preceding build **eaa4b54e4cbb** passed native Chrome 155 essay and safe-example
integration. Five focused browser cases passed across checks and affected reruns;
screenshots were inspected. All 44 core checks passed across the initial run and
targeted repairs. Nineteen affected engine gate/contract checks passed. A pytest
temporary-directory permission error was resolved using a repository-local
temporary directory. Owned disposable browser/server processes were closed.

Fresh batteries are **running**, followed by the full art-cache refresh, in one
counted Sounding Line CPU slot. The capture has 15,602 words / 328 passages. Work
is serial, CPU-only and below normal priority, with resource floors and native
ownership. Q8 finished all 200 constructed cases; the remaining batteries and
art-cache refresh are unfinished. No natural-data admission is claimed. See
the [run and review record](docs/CPU_REFRESH_2026-10-17.md).

## Earlier October 17 essay passes

The October 17 [tooltip walkthrough](docs/TOOLTIP_WALKTHROUGH_2026-10-17.md) is
implemented. Question marks follow their labels and show short invitations after
1.5 seconds. Essays expand with the viewport, retain an outside margin, and use
the owner's updated imagery and verbatim captions. Options → Bibliography lists
100 uniquely cited sources with shared numbering across all three essays.
Explanatory repository citations are removed; the closing repository invitations
remain. The original manuscript and picture directions are archived. See the
[editing guide](src/content/README.md) for future edits and citation scope notes.
The second walkthrough adds full-screen image viewing, display crops with preserved
originals, wider captions, smaller citations and cross-essay navigation. The
impact-ranked reader review is separate from the authored prose in the walkthrough.

Essay verification on October 17: build and three targeted browser checks passed
on packaged files, as did native Chrome 155 source-overlay and local-fallback
validation. Checks covered delayed hints, prose, all 27 raster images, two reused
diagrams, bibliography, narrow/wide layout and dismissal. The archive hash matches
the original; 19 captions match the owner's quoted or existing prose; image copies
match the curator/source hashes. The local Vite image check stalled on pending
image requests, so packaged-file and native verification were used. Local evidence
is in `evidence/essays-*`, `essay-validation.json`, and `essay-content-audit.json`.

## October 17 engine packet

The [implementation matrix](docs/ENGINE_PACKET_2026-10-17_IMPLEMENTATION.md)
records the all-question admission gate, certified fits with receipts, strict
preview parity, context guards, owned warm sessions, refusal diagnostics,
pseudonyms, goal lenses, evidence entries, aggregate findings and history
robustness. Software checks passed; no scientific admission is implied.

The earlier UI build was `4903a4f38479`. Targeted engine groups, 43 frontend checks,
three essay browser checks, the new goal-lens/global-findings browser check, and
native Chrome essay integration passed. Visual inspection found and resolved a
goal-lens control overlap. Native essay verification used `a1da4d385ed8`; the
subsequent build changes only the preview panel's layout and heading placement.

Fresh model batteries and the full art-cache refresh now use the allocated
shared CPU slot described above. Old receipts do not earn new badges.
Common-word score alignment is explicitly approximate until the reader exposes
the distributions needed for full boundary marginalization. Conditional research
features await reviewed handoffs. [Performance](docs/PERFORMANCE.md) separates
cached replay, live measurements and unfinished preparation. Haiku and Clerihew
each have 20 current public revisions cached locally. No release tag was published.

## October 17 incremental reading

Preview modules now take turns on one worker, publish passage/window results,
prioritize the selected passage with its original context, and save exact scoring
windows and checkpoints. **Continue reading** preserves the best visible result
while cached replay catches up. Compact progress updates avoid resending the
entire captured essay on each update. The bottom menu has simultaneous word/pie
indicators, completion checks that fade, and explicit paused/failed states.
The teardrop reserves source-group geometry before judgments arrive; the empty
space is not an inferred goal, and completed nodes retain stable positions.

The optional Clef-flash SystemOne adapter now runs the actual pinned 9B release
in an isolated CPU environment, batching five technique questions per passage.
Four constructed examples took 43–48 seconds each and matched 15 of 17
prespecified answers; these are smoke results, not natural-text accuracy.
**Practice ToMpathy with Clef.cmd** opts into this path. Normal practice still
uses fixed Qwen. The owned service verifies release files, authenticates requests,
reserves memory headroom and preserves exact caches across ephemeral ports.
[Runtime and measurement record](docs/CLEF_LOCAL.md). A small serial CPU comparison found quantization speeds
up scoring but materially changes rankings, so the existing default is unchanged
and precision alternatives are explicit. These improvements do not establish
scientific accuracy or the 15-second full-page performance target.

The Clef integration and cache replay pass 41 affected engine/CLI checks across
targeted serial runs, including runtime-identity rejection, cache reuse after a
service restart, unchanged final scores after batching cached updates, and
timeout rollback of overlapping attention spans. The
extension build and focused Ruff checks pass. The GPU and research environments
are unchanged.

The full engine suite passes 198 tests, plus four subsequently added mocked Clef
wire-contract cases. All 42 core checks passed across the full
run and the corrected stream-fixture rerun. The narrow browser component check
covers stable geometry, multiple pies, pause/continue and check fading. Native
Chrome 155 verifies automatic capture, real CPU attention/agreement/payoff and
completion fading, with no page errors. Goal/technique inference was deliberately
absent from this bounded native smoke. Details and local receipts are in
[the driver record](docs/DRIVER_IMPLEMENTATION.md#october-17-incremental-reading-and-speed-pass).

## October 16 driver implementation

The separate research preview is connected to pinned local population readers,
exact fixed-Qwen technique/correction calls, bounded goal judgments, deterministic
habits, two-reader comparisons and payoff probes. The frontend defaults preview
on after a companion is selected, displays evidence/test labels, and retains the
admitted path when preview is off. Source history has pseudonymous makers,
GitHub trailer declarations, quota reporting and bounded history caches. The
Global tab uses supplied Phase 0 historical aggregates; no numerical seven-drive
prior or new scientific admission has been supplied.

The implementation passed 186 engine tests, 39 frontend unit checks, and all 58
browser scenarios across reruns. Native preview, preview-off behavior, and live
T0/T1 cancellation passed. The scientific and performance gates remain separate.
CPU performance misses the 15-second, 3,000-word target: the measured optimized
score was 64.2 seconds, excluding model load. Live work has a 165-second page
budget and preserves validated partial output. See
[driver implementation and acceptance status](docs/DRIVER_IMPLEMENTATION.md)
for the exact working paths, measured limits and remaining checkpoints.

The October 17 full-art Clef backup matches the current engine and all 15,602
captured words / 328 passages. Native Chrome loaded it in 0.88 seconds and located
a comparison passage on the source. Habits, departures and the two-reader
comparison are complete; Clef supplied 100 answers for the first 20 passages.
Seven of 21 goal groups and 58 of 909 payoff sentences are available; those
stages remain partial, and personal values remain unknown. Cache replay now
groups tiny updates without changing final results: the complete reader
comparison fits its unchanged 25-second module budget.
The ordinary fixed-Qwen launcher has its own refreshed cache (0.85 seconds to
load, 26 technique checks and 52 payoff sentences). Both native paths passed
after the timeout rollback fix, with owned test services and browsers closed.
The [prepared review path](docs/LIVE_PRACTICE.md#prepared-full-essay-review)
explains how to load it and inspect source-linked passages. Preview no longer
falls back to the old authored website reading when Follow pages is off.

## Engine v1

The theory review is complete. The branch contains the CPU-first ledger, source
adapters, model/evaluation components, gated fitted-preference packets, registry
generation and authenticated local companion. The extension can opt into a
registry or companion and render exact-capture 1.7/1.8 packets, recorded production
history and supplied population comparisons. Default provider selection is None.

Live practice now has an optional Follow pages mode: automatic capture and
analysis across active-page navigation, with a persistent practice companion.
Unreadable pages, empty pages and an offline engine have distinct recovery
states. The safe example is bundled and fictional; ordinary live pages use the
engine, with explicitly labeled guesses in preview and evidence-gated estimates
on the admitted path. See [live practice](docs/LIVE_PRACTICE.md).

The pinned CoAuthor census and 234-target baseline reproduce exactly. All 16,855
chronologically eligible decisions score in 129.15 seconds on one CPU thread.
Four real-source reading packets validate and render; CoAuthor remains internal.
The real extension-to-companion flow and ordinary Chrome native-panel/restart
checks pass. See [Engine v1 verification](docs/ENGINE_V1.md) for measurements and
the remaining milestone gates, and [the engine guide](engine/README.md) to run it.

The continuation connects history ingestion, exact-input literal labels,
correction/choice fitting and packet generation. Native panel converters,
optional CPU posterior fitting, goal candidates, calibration and expanded
evaluation exports share the canonical engine. Gated display paths include
goals, revealed-theme drives/recipes, borrowed priors, repertoire, candidate
expertise, source-use and inspection evidence. The extension has an explicit
Wikipedia history action. [Integration details](docs/ENGINE_INTERFACE.md) explain
how Sounding Line and Ghost Scale can pin and test this implementation.

The [Stage 15 dependency return](docs/SOUNDING_LINE_STAGE15_RETURN_2026-10-15.md)
records locally tested native-adapter provenance and chronology corrections,
unchanged ledger schema, exact local hashes and migration guidance. This return
is uncommitted; Sounding Line's running pinned capsule remains unchanged.

The [October 16 review guide](docs/REVIEW_READINESS_2026-10-16.md) records the
current usability/stability pass: partial-access context collection, same-revision
retention, graph stress checks, interactive trajectory readouts and packet 1.8
current estimates with explicit uncertainty. Constructed fitted packets exercise
the full estimate display without enabling production admissions. Sounding Line's
dependency return now acknowledges the earlier handoff; its studies retain their
own pin. The overnight queue is limited to concrete integration/recovery work
and preparation for the 05:00 Pacific review.

No production scientific admissions are shipped. Admitted-path readings show
observed records and unknown estimates until the relevant evidence and admission
exist. Research preview is a separate, explicitly labeled path for unvalidated
surface readings and judgments; its constructed-tested badges bind only the
exact literal reader and applicable questions.
The full Wikipedia fetch → admitted fit → inferred packet acceptance check and
completion of the per-question real-model batteries remain separate gates.
The first real 200-item Q5 battery failed at 75.5% accuracy and stays disabled;
its exact constructed inputs and result are retained under `engine/validation`.
No registry hosting or release is included. CI is configured; a remote run has
not been claimed.

Live practice is available through **Practice ToMpathy.cmd**. The real companion
and ordinary Chrome native panel have exercised Sneckdown (14 captured passages,
119 recorded events) and Desire path (24 passages, 60 events), including source
evidence and connection checks. This is observed-history use; no inferred values
or model admissions are manufactured. See [the practice guide](docs/LIVE_PRACTICE.md).

## Verified baseline

Package and Chrome versions are aligned at **0.2.0**, with an installable
`v0.2.0` milestone. Main is the baseline for the next feature; the completed
milestone branch is retired after merge. Exact build identifiers live in the
verification receipts and packaged `build-info.json`.

- Live demo on the public essay/homepage; other pages accept matching supplied analysis.
- Linked attention, zoomable multi-peak hierarchy, wheel/keyboard reels and source navigation.
- Sentence reading scales, contour-current value categories and three demo perspectives.
- Bounded free linked context, GitHub revisions, timeline and portable reading files.
- No live inference backend or Chrome Web Store submission. Demo confidence and values
  remain explicitly invented. Future model/search/word-level controls remain unfinished.

The retained 0.2 baseline below describes the released frontend. Follow
[the branch workflow](docs/VERSIONING.md) for the active 0.3 feature branch.

Review locally with **Review ToMpathy.cmd → Open the live essay → ToMpathy toolbar icon**.
See [development and QA](docs/DEVELOPMENT.md), [release notes](CHANGELOG.md),
[the input contract](docs/INPUT_CONTRACT.md), and [the 0.2 UX review](docs/UX_REVIEW_0.2_DEVELOPMENT.md).
Detailed earlier checks remain in [the development archive](docs/archive/0.2-development.md).

## Retained 0.2 validation

- TypeScript/build and **29 core tests passed**.
- **All 51 browser scenarios passed** across the broad run and affected reruns.
  Release validation caught and fixed packing stopping at the first oversized
  attention phrase. Tests now reflect capped clouds, scrollable values, the
  Current work only default and live review links. One cold navigation timed out
  in the broad run and passed unchanged on the targeted rerun. Linux CI also
  exposed zoom-coordinate and late-font heading clearance issues; both were
  corrected. Font continuity is checked by rendered ink, since platforms can
  preserve advance widths across different weights.
- Ordinary **Chrome 154.0.8037.98**, actual **360 px native panel**: installation,
  source/panel locks, wheel and keyboard navigation, graph zoom, saved-reading
  import/export, revision retention, normal-page capture and full restart
  restoration passed with **zero panel errors**. No model download was requested.
- The ZIP is verified byte-for-byte against every built file. The release carries
  a checksum for its exact downloadable archive; ZIP timestamps can differ between
  otherwise equivalent local and CI packages.
- Pull requests and main updates run the full [CI checks](https://github.com/EmotiveAutomaton/tompathy/actions).
  Source maps, local inputs/profiles and generated evidence are excluded from Git
  and the installable package. Disposable browsers and servers close after checks.

Local receipts: ignored `evidence/review-validation.json` and
`evidence/package-verification.json`. The README screenshot shows the built 0.2
preview with half-width reader, a locked sentence and its evidence card.
