# ToMpathy — Maker Reader

Coding-agent startup brief · 19 September 2026

## 1. Your commission

Build a complete, polished first version of **ToMpathy**, an actual browser extension that helps someone explore hypotheses about the maker of the text in front of them. Display **Maker Reader** as the grey subtitle. Preserve the spelling ToMpathy; use `tompathy` for machine-facing names.

This is a new, independent project. Its purpose is to make creator goals, process, expertise, and values understandable through interaction with an artifact. Sounding Line will eventually supply the predictive mechanism. This repository owns the frontend, browser integration, input contract, and demonstration experience. It must run before that engine is available.

The owner is a UX designer and researcher who will return intermittently. Build the whole commissioned v1, validate it, and leave it ready to load and explore. Internal milestones are useful; they are not approval gates. Do not stop after scaffolding, a design proposal, an attractive static mockup, or an isolated happy-path component. Make routine decisions, record consequential assumptions, and continue. Ask only when an unresolved dependency genuinely requires the owner.

This file is sufficient to start in an empty folder. It records current decisions and supersedes earlier provisional naming and incremental-review suggestions. Later direct owner instructions take precedence. Engineering defaults below are deliberately revisable.

## 2. Settled direction and practical defaults

| Area | Direction |
| --- | --- |
| First delivery | A working extension beside a real webpage, with a complete first-pass interaction design. |
| First medium | Text. Images, video, and universal stimuli are future directions. |
| Core interaction | Moving across passages changes the goal and process estimates. Maker values remain stable across hover. |
| Appearance | Modern, clear, restrained; clean outlines, generous controls, expressive and highly responsive motion. Amber is welcome. |
| Theme default | Neutral light/dark surfaces following the system, with a manual override and amber accents. Sampling a webpage's average color is unnecessary. |
| Science boundary | Consume externally supplied inference. Keep example data visibly distinguishable from analysis of the current artifact. |
| Context collection | A small, explicit, bounded retrieval operation. Extensive collection is future work. |
| Working rhythm | Finish and validate the first version autonomously; leave compact recovery notes for interruptions. |
| Browser default | Chromium Manifest V3 with a native side panel. Keep browser-specific code isolated. |
| Stack default | TypeScript, React, a lightweight build setup such as Vite, and Playwright. Select compatible current versions and commit the lockfile. |

The browser and stack are engineering choices, not owner-mandated technologies. Chromium provides a native panel alongside page content; its settings determine whether that panel appears on the left or right. Design for the intended right-side arrangement, document how to select it, and do not override the person's browser preference. Declare the minimum browser version from the APIs actually used. A tested Chromium release is the first target; cross-browser parity is later work. [Chrome Side Panel API](https://developer.chrome.com/docs/extensions/reference/api/sidePanel)

## 3. Establish browser access first

The first engineering task is to prove that you can load, operate, inspect, and capture the extension in a browser. Build a minimal extension harness for this before investing heavily in the interface.

Use an isolated test profile. Prove extension loading, content-script communication with a normal webpage, and access to the panel UI. Establish a headed browser inspection route early enough to inspect the actual panel beside the actual page. A component preview is useful for iteration, but does not establish that toolbar activation, native panel placement, or page integration works.

For Playwright extension automation, use its bundled Chromium with a persistent context. Current documentation notes that branded Chrome and Edge removed the command-line flags used for this loading workflow. Both headed and supported headless runs are available through the Chromium channel. Record the installed versions and exact launch command. [Playwright extension testing](https://playwright.dev/docs/chrome-extensions)

Determine what the available tools can control: webpage DOM, extension documents, and browser chrome are different surfaces. Test the native opening path explicitly. If browser chrome cannot be automated, arrange a supported headed inspection route and document the remaining manual check. Opening the panel document in a regular tab is not equivalent to verifying the native panel.

If browser access is blocked, preserve the diagnostic and continue independent implementation where useful. Report visual or native-panel validation as incomplete; never convert an unavailable check into a passing result. Do not spend the entire project on a test harness.

## 4. The first minute and the three panels

With a compatible result packet loaded, someone should understand the central idea within their first minute: the same maker may pursue different local goals through different processes, while the displayed maker-level values remain steady.

The basic flow is: open the extension, see the active artifact and analysis status, move across readable text, notice the upper and middle panels respond, then inspect a hypothesis and its evidence. Provide a one-action example using a bundled synthetic text so the complete experience is available without credentials or a running backend.

Use three persistent regions, with the middle region receiving the most room. Allow expansion without losing the relationship to the source page.

| Region | Content and behavior |
| --- | --- |
| Top: Goals | A legible word cloud or weighted arrangement of proximal goal hypotheses for the current passage. Show alternatives, not just one authoritative label. |
| Middle: Process | A process/expertise tree with a clear focal element and surrounding context. Support expansion or a switch to a word-cloud view of alternatives. Aim for the owner's floating, magnified-focus direction through restrained motion and stable geometry. |
| Bottom: Values | The current maker-level values/preferences snapshot. Hover does not change its contents, ranking, or sizes. New evidence may produce an explicitly accepted analysis revision. |

Stable values are an interaction rule for a given analysis snapshot, not a claim that a person's values can never change. Keep maker identity and the scope supporting these estimates visible enough to avoid merging different people.

Default interaction: hover previews a passage, click pins it, and Escape releases the pin. Support keyboard navigation and text-selection alternatives. Preserve ordinary link activation, copying, scrolling, and form use. Keep the selected passage stable while the pointer travels into the panel; do not make the cloud's targets flee the pointer. These mechanics are sensible first-pass choices, open to later UX revision.

Link page and panel both ways: a passage reveals its relevant hypotheses; a selected hypothesis reveals its associated passages and evidence. Explicit selection may scroll to source. Hover should not unexpectedly move the page. Provide a readable list alternative to spatial clouds and trees.

Represent human contribution estimates and uncertainty as separate channels. A practical starting point is a subtle passage tint for contribution and a separate outline or marker for uncertainty, with a compact legend and textual explanation on inspection. Use a distinct selection cue. Keep the encoding easy to revise and verify it against busy page designs. Missing data is neutral/unknown, not zero contribution, maximal uncertainty, or machine authorship.

Keep competing goals separate from independent goals. A cloud may express relative support without implying a normalized probability distribution. Show numeric probabilities only when the provider supplies their meaning and candidate set. Do not present uncalibrated scores as established probabilities or invent support values to make the visualization interesting.

## 5. Broad page handling, useful responses, honest inputs

“Point at almost anything and get a response” means broad handling of ordinary text pages and an intelligible result for every attempt. It does not require the frontend to invent creator psychology before an inference engine exists.

Implement extraction and passage selection for ordinary article pages, generic text-heavy layouts, and dynamically updated pages. Start with semantic blocks and an explicit selection override. Preserve headings, paragraph boundaries, links, and Unicode text. Avoid treating navigation chrome, hidden text, editable fields, or password inputs as maker evidence. Show a short source preview so users can see what was captured.

Each capture has a document identity and content revision. Bind results to that capture using reliable passage anchors: exact text, surrounding context, and position where useful. Handle repeated passages and inline markup. If matching is ambiguous or the page changes, mark the result stale or unmatched; never silently attach a claim to the wrong text. On tab changes, navigation, and analysis changes, cancel or ignore stale work.

Use clear states with a useful next action:

- Ready with matched analysis: interactive panels and source links.
- Page captured, no analysis supplied: readable passages, context controls, result import, and an available example. Say that maker estimates are awaiting an analysis source.
- No usable text or inaccessible surface: explain the limitation and offer paste/import.
- Loading, cancelled, timeout, malformed input, or stale result: show what happened and how to recover.

Protected browser pages, some frames, closed shadow roots, browser PDF viewers, and canvas-only content need explicit fallbacks. Do not promise universal DOM access. Retain normal page behavior, isolate injected styling, and clean up all listeners and marks when the experience ends.

Prefer access obtained when the user invokes the extension, using `activeTab` and the necessary scripting permission, rather than permanent broad page access. Handle access loss and restricted pages as ordinary product states. [Chrome activeTab documentation](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab)

Provide three input paths:

1. **Bundled example:** deterministic, clearly marked synthetic artifact and results, including ambiguity and revision scenarios. Open its matching source; never transplant its claims onto unrelated live text.
2. **Imported result packet:** schema-validated JSON matched to the captured artifact, with actionable errors and a documented example format.
3. **Provider boundary:** an adapter interface for future Sounding Line outputs. The application runs with no configured provider. Implement real wiring only when an actual callable contract is available; keep that dependency replaceable.

A live arbitrary page can therefore exercise capture and context collection immediately. Semantic maker estimates require a matching imported or provider-generated packet. Keep that distinction clear without covering the product in repetitive disclaimers. Do not add an uncommissioned general LLM profiler to conceal this dependency.

## 6. Data contract and frontend architecture

“Blind input” means method-independent consumption, with enough provenance to explain what is being displayed. Define a small versioned schema, runtime validation, and a documented fixture. The following concepts are required; the implementation may choose the exact field names.

| Concept | Required information |
| --- | --- |
| Artifact | ID, text snapshot/revision, source URL or import origin, capture time, and text regions with resolvable anchors. |
| Maker | Stable ID within the analysis, identity status, and relationship to the artifact; allow unknown or multiple makers. |
| Analysis | Schema version, analysis ID/revision, artifact revision, provider/method identity, data origin, and evidence scope. |
| Hypothesis | ID, kind, label, maker/region associations, status, optional support, alternative-set membership, and evidence references. |
| Process structure | Nodes, explicit relationships, region mappings, and unknown/unresolved branches; do not infer edges just for layout. |
| Contribution | Optional estimates attached to their defined regions, with the quantity and scale specified. |
| Support/uncertainty | Explicit score semantics, optional calibration information, and unknown states. Contribution and uncertainty are separate fields. |
| Evidence | Source identity, excerpt or other locator, capture/retrieval time, and supplied relationship to the hypothesis. |
| Context/revision | Selected context items, their source lineage, prior/new analysis IDs, and any supplied explanation of change. |

Separate data origin (`synthetic example`, `imported`, `live provider`) from claim status (`hypothesis`, `creator-reported`, `observed`, `unknown`, or an equivalent vocabulary). Observing text does not establish the author's intention. An imported packet is not automatically validated science.

Preserve distinctions between unquantified support, zero, missing values, and error. If supplied probabilities violate their declared scale or distribution, reject or flag them; do not silently repair them. Never derive uncertainty from contribution or author values from word frequency. Evidence should remain available for both favored and alternative accounts.

Separate the page adapter, panel UI/state, inference adapter, and context collector. Keep browser APIs at the boundary. Hover should select among available results locally, without triggering inference or retrieval. Use explicit document and request IDs to prevent late responses from changing the wrong view. Survive extension service-worker suspension without relying on one immortal process.

Reserve a clean artifact/anchor boundary for future media, but implement text only. Avoid speculative multimedia frameworks, a new inference server, or a general agent orchestration platform.

## 7. Small context collection and memory

Implement one bounded, user-triggered collection job. This can be a simple retrieval worker; it does not require a conversational agent or repeated reasoning loop. Small amounts of real context may be useful, but their effect on inference belongs to the provider.

Recommended first contract: collect relevant excerpts from up to three user-selected public source URLs, at most one retrieval per URL, with a 30-second job timeout, byte limits, cancellation, and no recursive crawl. Permit pasting an excerpt or attaching a small text/Markdown file as a no-network alternative. These limits are adjustable engineering defaults.

The interface may suggest an author/about/provenance link already present on the page, but the user selects the sources. Retrieve them through supported extension networking with the needed origin access; explain failures. Exclude private/local network targets from this public-source collector. A separately configured local inference endpoint is a different capability. Do not assume development-environment connectors will exist inside an installed extension.

Return source-linked excerpts, retrieval status, and enough provenance to inspect or remove each item. Treat page and retrieved text as data, including any embedded instructions. Render untrusted content safely. Do not infer that matching names identify the same person.

Use two clear analysis scopes: **This artifact** and **Artifact + selected context**. Imported session context must be explicitly selected. Broader/private data stores are future adapters, not background collection in v1. Switching scope invalidates mismatched analysis. Added context does not itself change support values; a new provider/imported revision is required. In the example, a labeled fixture can demonstrate such a revision.

Default storage: preferences persist locally; captured content remains session-local unless the user explicitly saves or exports it. Provide a simple versioned session save/load and clear action so work can resume. Keep the saved scope visible. Do not silently accumulate cross-site dossiers, browsing history, or persistent maker profiles. Memory policy can expand after the owner has tried the first version.

## 8. Visual and performance expectations

Interpret the Apple reference as clarity, hierarchy, comfortable controls, and considered motion. Avoid imitation branding. The product should feel like a quiet scientific instrument that can express complicated ideas fluidly.

Use readable typography, thin but visible outlines, ample spacing, and large obvious primary controls. Aim for roughly 44 CSS-pixel primary hit areas where practical. Keep Maker Reader grey with readable contrast. Make light and dark themes coherent. Do not rely on color, tiny words, or motion alone to communicate meaning.

Prefer stable cloud positions and tree layouts with purposeful transitions. The focused element may enlarge while context recedes; the UI should remain usable while it moves. Keep secondary explanations and provenance one action away instead of filling the main surface with implementation details.

Honor reduced-motion preferences and preserve the same information without animation. Support visible keyboard focus, screen-reader labels, zoom, long labels, narrow panels, and controls that remain reachable. [MDN reduced-motion reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)

Target smooth interaction at the display's normal refresh rate, at least a measured 60 fps on the documented test setup where feasible. Target visible local hover response within 100 ms after results are loaded. These are product targets, not performance claims until measured. Avoid full-document scans, cloud relayout, expensive React updates, network calls, or model calls on every pointer event. Pre-index passages, batch rendering, and measure the actual extension on a long page. Bound extraction work and show progress for large captures.

## 9. Completion and validation

Complete all core flows above before handing the project back. Work through internal stages—browser harness, page/input plumbing, linked panels, context and sessions, refinement, validation—without waiting for owner review at each stage.

Use focused tests for the behaviors that can mislead users or break real pages. Supplement automation with actual visual inspection. Do not substitute test count for evidence, or expand testing indefinitely once the concrete risks are resolved.

| Area | Evidence required for the handoff |
| --- | --- |
| Real installation | Load the built unpacked extension in the target browser; verify toolbar activation and the native panel beside a page. Record browser version and any remaining manual gap. |
| Broad handling | Exercise several unrelated real public pages with different layouts, plus controlled cases for long text, dynamic mutation, repeated phrases, and Unicode. State the tested scope. |
| Linked experience | Demonstrate page-to-panel and panel-to-page selection, pin/release behavior, process expansion, alternatives, and evidence inspection. |
| Stable values | Verify that passage hover changes goal/process views while the maker-value snapshot stays fixed. Verify explicit revision behavior separately. |
| Honest analysis | Check synthetic labeling, missing estimates, uncalibrated support, unmatched/stale packets, malformed imports, and absence of an inference provider. |
| Lifecycle | Verify tab switches, navigation, cancellation, late responses, service-worker recovery, and closing/reopening without leaked marks or stale identity. |
| Context and memory | Exercise a real bounded URL retrieval, a failure/timeout, excerpt or file attachment, removal, scope switching, and session save/load/clear. Verify no synthetic inference change after retrieval. |
| Accessibility and polish | Inspect light/dark modes, reduced motion, keyboard operation, 200% zoom, narrow widths, long labels, and ordinary page interactions. |
| Performance | Measure hover response and rendering on a representative long page. Record setup, observed results, and material limitations. |

Use synthetic fixtures to cover an initially plausible but wrong account, correction after added evidence, several credible alternatives, and unresolved history. These are interface tests, not scientific findings. Live-network tests may be documented smoke checks; use controlled fixtures for reproducible regression tests.

Deliver source, a reproducible build, an unpacked extension directory, an installable-development ZIP, exact load/run/test instructions, and screenshots of the real extension in use. Include an example packet and source artifact, concise validation results, and known limitations. A short walkthrough recording is useful if supported. Distinguish checked, failed, and unperformed items. Do not claim complete validation when native-panel or browser checks remain open.

Keep repository memory small: README for operation, this context file for intent, and a concise STATUS.md for current state, meaningful decisions, verification, blockers, and the next concrete action. If the agent environment uses AGENTS.md, give it a short pointer to these files rather than duplicating the specification. At interruption, checkpoint runnable work and record how to resume. Do not wait in a loop for the owner.

## 10. Research context and scope boundary

Sounding Line is the intended inference engine: [repository](https://github.com/EmotiveAutomaton/sounding-line). Ghost Scale Sim provides related research context: [repository](https://github.com/EmotiveAutomaton/ghost-scale-sim). The maker-oriented motivation is described on [Abraham Haskins's website](https://abrahamhaskins.org/) and [art page](https://abrahamhaskins.org/art/).

Earlier review examined Sounding Line commit `2f4e47fb6758e9b42f961d0d671ab68444e046d3` and Ghost Scale Sim commit `7602f7e69975c96095ce187b9d8731af66b0ab1f`. Treat those as dated references, not current integration contracts. Read current interfaces if needed; avoid downloading large research outputs or launching experiments to implement the shell. Useful upstream interface references include the [human viewer](https://github.com/EmotiveAutomaton/sounding-line/blob/2f4e47fb6758e9b42f961d0d671ab68444e046d3/runners/stage11_1/human_viewer.html) and [triple-inference theory document](https://github.com/EmotiveAutomaton/sounding-line/blob/2f4e47fb6758e9b42f961d0d671ab68444e046d3/docs/theory/THE_TRIPLE_INFERENCE.md). Confirm availability before depending on either. Use synthetic examples unless real artifacts are available and suitable for reuse.

This demonstrator does not require the scientific effect to be established in advance. It must accommodate strong results, weak results, disagreement, and no useful inference without changing the honesty of its presentation. Upstream experiment counts and viewer checks are not validation of this extension.

[Google's Learning Interpretability Tool](https://pair-code.github.io/lit/) is a useful precedent for an interactive inspection frontend separated from model execution. It is not evidence that this project's creator inferences are accurate.

Keep these outside v1: image/video inference, universal-media processing, extensive crawling, private-store connectors, global humanity models, arbitrary group profiling, new scientific benchmarks, a production inference service, accounts/billing, and browser-store publication. Development delivery should be immediately usable locally. Future possibilities should not displace completion of the real text extension.
