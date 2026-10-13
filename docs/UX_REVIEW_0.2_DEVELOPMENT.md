# UX review — 0.2 development, October 12, 2026

The three-panel reader is ready for a small, observed usability trial with the fictional article. It is not yet ready for an unsupervised test of live analysis: no inference backend is connected, and this review cannot establish whether readers correctly interpret the scientific claims. The main remaining issues concern orientation and meaning rather than needing a different visual layout.

This review combines code inspection, browser interaction, visual inspection and native Chrome checks. It is not a participant study, a screen-reader certification or a claim of WCAG conformance. The faint idle cue and gradient legends remain deliberate visual experiments requested for this prototype.

## Follow-up decisions and implementation

The subsequent owner review supersedes the proposals below where noted. Find now works with ambiguous reels and centers the whole highlighted source group. No locate-in-graph button was added. Shared-parent links now use the selected dotted corner-to-corner vertical route. Branch-cloud behavior, Agent search wording, cloud colors and the current testbed remain as requested.

The next value-card pass adds low-confidence creator fixtures, higher-confidence Global fixtures, preferred-state/uncertainty charts and individually explained vectors. The same chart opens by clicking a value. Sentence evidence now has involvement-direction arrows; values are left-aligned with “% confident,” and the reversed gradient spans spaces continuously. The heading help captures the preferred-state proposal and distinguishes its research limits. See [the context research](CONTEXT_RESEARCH.md#website-source-repositories-and-revision-history--12-october-2026) for public-source history retrieval and primary theory references.

The latest pass adds source centering on graph click, arrow-key cell navigation, and a Find control revealed by scrolling away. Escape clears the source focus outline. Evidence directions are vertical; value tubes are wider and softly shaded, with shorter inward-pointing vectors. Context settings persist across opening the reader and changing creators, while explicit source history is collected through the free GitHub API. Four generated logo studies are now available alongside the twelve prompts. No backend estimates are fabricated when context arrives.

The observations and priority table below describe the earlier review snapshot, rather than an unchanged list of current defects.

## Changes in this pass

- **One cell per sentence.** The old layout unfolded shared parent paths, repeating paragraphs and their sentence cells. The layout now gives each supplied node one visual home. Additional supplied parents remain connected during inspection, and all alternatives remain in the odometer. Placement is not a claim that one parent is more likely than another. Every one of the thirty article sentences was exercised in both directions. The review also found and fixed an uncertainty marker that could disappear when shared siblings were placed under different geometric parents; membership now follows the supplied graph.
- **Smooth back and dots.** The common left outline uses an elliptical arc. Sentence dots use one analytic inset arc rather than snapped sample positions. Finer endpoint sampling also removes the stepped appearance of the individual curved brick boundaries. Higher-level dots continue to follow their own branch.
- **Weighted branch attention.** Each selected sentence gets equal weight. A focus occurring in two of four sentences with supplied confidence 80% contributes 0.40 to the overview; a focus occurring once with confidence 95% contributes 0.2375. Within a sentence, coverage fractions and the most specific supplied frame determine its contribution. Shared graph paths and splitting a frame do not multiply evidence. Missing scores add no weight. These are relative display weights, not calibrated aggregate probabilities. Hover details explain coverage and weighting without repeating the same paragraph twice.
- **Tooltip spacing.** The classification and percentage are larger, centered above the arrows and closer to them. Smaller legends sit just below, with more space around the dots. Both still read Less to More. Cards can be wider on a large page and remain constrained on a small one.
- **Lock reminder.** Twelve blocked-focus points within 1.2 seconds trigger the gentle reminder. A page-sentence transition contributes two; a graph target contributes one. Repeated movement on the same target and very short jitter do not accumulate. The six-second cooldown and reduced-motion treatment remain. This is a local interaction heuristic, not a measurement of frustration. Native page and panel counters currently accumulate separately; a triggered reminder synchronizes both visible locks.
- **Blank-space clearing.** Pointer clicks no longer outline the entire graph. Keyboard navigation retains a visible focus cue.
- **Icon directions.** Review desk now offers twelve complete prompts with Copy and Download actions. The directions deliberately vary the underlying idea and medium, not just the head outline. The old SVG study page is removed; the production icon is unchanged. No generation service or extra extension permission was added.

## What is working

The stable three-box composition is worth preserving. Attention changes locally, the hierarchy provides structural context, and values stay steady. Soft inspection surviving whitespace makes the reader much less flickery. Explicit locks are distinguishable and can be released from either surface, by Escape, by double-click or through blank graph space.

The smaller odometer and upward expansion make good use of the hierarchy area. Expanded alternatives now retain the real shared parents instead of hiding them because of geometric placement. The fixed cell labels and fast fit animation help maintain spatial orientation. The curved back looks coherent without needing an illustrated brain behind it.

Options has a readable order: context controls, future analysis controls, appearance, then help and file actions. Light and dark variants were inspected. The prompt collection works as a separate workspace without adding controls to the reader itself. Export/import and the persistent Chrome review launcher provide a useful repeatable review loop.

## Recommended next improvements

These are recommendations, not changes silently added to this pass. The first four would improve the next end-user trial most.

| Priority | Observation | Recommendation and reason |
| --- | --- | --- |
| High | Find in page is hidden if any higher reel is ambiguous, even when the locked sentence itself is exact. Shared-parent sentences now expose this more clearly. | Show Find whenever there is one exact sentence span. Uncertainty about its broader purpose does not make its physical location uncertain. This changes the earlier “all reels resolved” rule and should be an explicit design decision. |
| High | After zooming and panning, a newly inspected sentence can be outside the graph viewport. Fit restores the whole graph, but does not directly locate that sentence. | Add a quiet **Locate selection in graph** action when the selection is offscreen. Animate to its cell only on request; automatic camera following would fight deliberate exploration. |
| High | Shared-parent connectors preserve the data, but a newcomer could mistake them for writing order or a stronger causal connection. The same green also marks ancestry and descendants. | Give a connected branch an on-demand explanation naming its additional parent, and distinguish the selected cell from related cells with a consistent edge treatment. Do not solve this by duplicating sentences again or by adding a permanent legend. Test whether the distinction is understandable before adding more line styles. |
| High | Ink, stroke grade, involvement category and assessment confidence occupy a compact visual vocabulary. A plausible failure is reading “78%” as “78% written by the creator.” | In the first user trial, explicitly test that distinction with contrasting examples. Retain the visual card, but prepare a short click-open explanation if people misread it. The larger values help legibility; they do not by themselves solve meaning. |
| Medium | A branch cloud can contain many tiny items, and its strongest word is scaled relative to that selection. Two similarly large words in different selections need not have equal support. | Keep the complete cloud as requested, but expose the selected scope and recurrence in its heading/phrase details. If testing shows confusion, try a temporary “8 sentences” cue on branch selection, not another permanent box. Do not silently drop low-weight items. |
| Medium | The 23-pixel lock and find controls are subtle but demand precise pointing. Fit-level sentence bricks are necessarily thin. Keyboard users also encounter many individual graph tab stops. | Increase invisible hit areas where controls will not overlap. For the graph, use one entry point with arrow navigation among neighbors and an explicit way to leave it. Preserve zoom rather than inflating thin cells over their neighbors. A dedicated screen-reader pass remains necessary. |
| Medium | The sentence tooltip can occupy a substantial portion of the text column. Hover is useful for investigation but can interrupt ordinary reading. | Test its delay during uninterrupted reading. Consider an optional reading mode that opens sentence evidence on focus or an explicit gesture, while retaining the current exploratory default. Avoid permanently pinning a card over the article. |
| Medium | “Agent search” currently follows explicitly linked sources and extracts a timeline without an agent/model. Disabled future controls and Global/search previews are useful for this design review but distract an external tester. | Before a public usability build, rename the implemented action to **Follow linked sources**, or clearly reserve “Agent search” for the future model-assisted behavior. Hide inactive prototypes in that build. Do not imply that collecting context has already recalculated confidence. |
| Medium | The darkest cloud word communicates prominence; the other green, blue-grey and brown colors do not communicate an established category. The native reading card also stays light even beside a dark reader. | Use one restrained family of tints unless color gains an explicit meaning. Consider theme-aware evidence-card surfaces with separately verified Ghost Scale contrast. These are aesthetic refinements, not reasons to redesign the three panels. |
| Medium | The current article is rich enough for a reading rehearsal, but it remains one carefully prepared creator and one medium-size graph. | Add a small fixed review corpus: a very short item, a long edited item, missing confidence, long labels, multiple creators and many shared parents. Check the same tasks against each. The current nine-level and narrow-panel checks catch layout defects; they do not establish comfort with every real backend result. |
| Lower | The reader changes the article's typography, including turning original bold into underline. A reader may want to compare the treatment with the untouched text. | Consider a temporary **Show original text** gesture or control in Options for comparison. Preserve the current reading state when switching, and avoid implying that typography is ground truth. |
| Lower | The identity remains unresolved, but the graph already carries substantial visual information. | Keep a head/brain reference in the creator selector or toolbar icon. I would not add a person outline behind the teardrop: even a faint image would compete with edges, uncertainty marks and highlights. Judge candidate icons at 24–32 pixels and in one color before refining their detail. |

## Robustness and efficiency

The duplicate-path correction reduces actual rendered cells rather than merely hiding duplicate dots. Layout is still memoized across pointer movement. The force calculation stops after a finite layout pass; attention arrival and position transitions are finite, and hidden clouds skip layout. No worker, model or new runtime dependency was added.

The renderer intentionally falls back to a list beyond 600 graph nodes; attention also has an overflow layout for more than forty items. These limits prevent unlimited rendering, but the transitions into those layouts need a realistic large-result review before claiming a complete 0.2 frontend. The next optimization should be driven by such a fixture: cache sentence/frame coverage per accepted packet if profiling shows aggregation is significant, and use a spatial index for hit testing only if measured interaction latency warrants it.

The reminder's strict time window is now quite fast: twelve graph changes must occur in 1.2 seconds. That implements the requested higher threshold. Observe real use before expanding the time window or combining partial attempts across the native page and panel. Do not collect cursor histories or infer a user's emotional state to tune it.

## A useful first participant session

Ask someone unfamiliar with the interface to use the fictional article, with no walkthrough beyond “this explores possible creator attention.” Observe rather than teaching the gestures immediately.

1. Have them read two paragraphs normally. Notice whether the cards distract them and whether they understand why the right panel holds its last state.
2. Ask them to hold a sentence, inspect a broader branch, and return to free exploration. Record accidental locks and how they recover.
3. Ask which focus is most common across a branch, and why its biggest word is biggest. Check recurrence and confidence separately.
4. Show a confidently curated sentence and a less-confident creator-written one. Ask what each percentage means. This is the most important comprehension check.
5. Ask them to zoom to a cell, find its sentence in the page, then restore the whole graph. Include one shared-parent sentence to expose the current Find restriction.
6. Have them export, close and reopen a reading. Check whether they understand which source text and analysis were preserved.

Use the same tasks with a keyboard user and at a larger text scale. A small observed trial can reveal where the mental model breaks; it cannot validate the underlying inference. The project is ready to learn from that trial without another large aesthetic redesign.

## Verification record

The exact build, commands, counts and native Chrome outcome are recorded in [STATUS.md](../STATUS.md). Local screenshots and machine-readable receipts are in ignored `evidence/`, including `pass-tooltip.png`, `design-branch.png`, `refined-reels.png`, `options-dark.png`, `icon-prompts-preview.png`, `icon-prompts-narrow.png` and the native `review-validation.json`.

Thirty-six browser scenarios passed across the broad run, twelve affected reruns and a six-scenario final pass including the shared-sibling uncertainty regression. The first sentence round-trip assertion expected an obsolete class; the reminder test's locator waits stretched its intended burst beyond 1.2 seconds; programmatic focus alone did not put Chrome in keyboard modality for the prompt outline assertion. The corrected tests exercise the actual state and input behavior without reducing the functional criteria.

The native investigation also caught a transient cloud-settling timeout and a tooltip accessibility-tree sample taken during focus-driven scrolling. The latter check now waits for the restored exposed card. Any persistent unresolved behavior belongs in the current status rather than being counted as a pass.
