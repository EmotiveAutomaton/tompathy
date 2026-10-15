# UX review — 0.2 development, October 14, 2026

## Current pass: contour currents and reliable reel handoff

Contour currents is the selected visual direction. Both category marks now share
rounded lobes, tapering ends and a continuous central curve: a rising current for
drives, accumulated currents for constructed values. The same marks appear in
card titles, using the graph/attention/preference palette. They are static SVGs,
with no continuous animation or new dependency. Their contour count and intensity
do not encode another score.

Definitions align on the left in both card types. Drive cards add a smaller
76 × 70 px brain on the right: anatomy at 36% opacity, brighter channel paths and
larger relative nodes. The visible schematic caption is removed; its accessible
qualification remains. The confidence legend grows from 8 to 12 px and nestles
under the arrow. Long headers wrap at narrow widths instead of clipping the legend.
Reload reading and its title offset are removed.

The wheel issue was a real handoff defect: entering the reader cleared the source
hover and deactivated its reels. That reset is removed. A resolved reel can now
advance and lock directly from an unlocked page hover; reverse wheel movement
returns to the previous choice. Wheel accumulation persists across lock/expansion
changes, while long unresolved lists retain ordinary scrolling. The first-use
invitation waits until the pointer leaves the reader before dismissing after an
in-panel selection, preventing the first wheel gesture from moving its own target.

A matching red banner was reproduced on protected Chrome tabs. Those access
states, ungranted pages and pages without readable text now show neutral guidance.
Unexpected capture failures retain their diagnostic error. Activation/action
messages from other Chrome windows are filtered, preserving the current selection.
The user's original transient message was not recorded, so this identifies a
confirmed matching case rather than every possible error they may have seen.

Remaining design review: compare the rising and layered marks at normal list size;
check that the pale brain remains a secondary cue and the highlighted channel is
legible. At 320 px a long title may put the confidence scale on the following line;
this preserves full words and the larger legend. The taxonomy and trajectories
remain illustrative. Sources and the selected design are in
[Core values design](CORE_VALUES_DESIGN.md).

## Previous pass: citation recovery, quieter attention and value perspectives

Citation hover was injecting temporary popup prose into the capture. A resulting
oversized heading invalidated the demo packet and left the reader disconnected.
Tooltips/popovers are now excluded and generated labels are bounded. A visible
Reload reading button reconnects the active page without closing the panel.
Chrome owns its pin toolbar; the button is at the top right inside the reader.

Current work only is the initial value perspective and has separate fictional
confidence, trajectories and observations. Creator and Global remain available.
PANIC/GRIEF displays as Belonging. Cards replace the pie with a straight confidence
arrow; concise definitions and approximate network sketches precede a full-width
lifetime curve. The initial guide now occupies its own temporary space rather
than covering tabs. Screenshot review also caught and fixed unresolved SVG colors
in portal tooltips and a reload/title overlap.

Broad attention selections retain their confidence-weighted recurrence ranking,
but show only the strongest phrases that fit. The creator control has a measured
cutout, and the portrait centers over the name. Stable page headings and footer
text are included on the commissioned website. References & Assets is a single
unit throughout highlights, hierarchy, attention and portable-reading validation.
The fully expanded essay now has 1,004 reading units, four with provisional cues;
these counts reflect the inspected public page, not a permanent corpus size.

[Three visual directions for Core values](CORE_VALUES_DESIGN.md) explore contour
currents, living strata and a neural atlas. Contour currents is my recommendation
for refining the small category icons while keeping the list quiet; the atlas
thumbnail already adds detail within the card.

Remaining review questions:

- **Scope:** can a reader distinguish evidence from this work, a creator-wide
  account and the broader Global catalogue? These are separate demo perspectives,
  not three measured inference pipelines.
- **Confidence versus strength:** the arrow deliberately matches the sentence
  cards. Check that high confidence does not look like a stronger drive.
- **Anatomical precision:** the network diagrams are approximate visual indices.
  They must not be read as scans, calibrated activity or definitive pathways.
- **Temporal interpretation:** the life axis is the intended conceptual scale.
  The present demo has no real lifetime observations; invented positions should
  not be used as a test of historical accuracy.
- **Selection after substantive page changes:** citation hovers are now harmless;
  opening a real new section still rebuilds the capture and clears selection.
  Preserving a uniquely matched selection remains a useful later refinement.

## Previous pass: actual website, adaptable tiers and populated value cards

The Review desk now opens the live essay and homepage. The extension captures their real DOM and applies sentence interactions in place. Expanding an essay aside or opening a homepage project refreshes the current packet; images, math, links and site controls remain live. The preview snapshot remains only an offline development fixture.

The previous generic sentence labels are replaced by authored possible intentions. The public-text corpus covers 997 essay sentences, 21 homepage sentences and 107 project-description sentences. The expanded live essay currently produces 999 prose spans because displayed prompts/controls and math segmentation differ from the offline fixture; every span still has exactly one node. All diagram purposes, attention weights, confidence and value trajectories are synthetic demo material. The Help method reports unmatched/provisional text when the website changes.

The graph gives a useful, populated intermediate tier more width by default. Draggable separators resize two adjacent columns without changing cell ownership; keyboard arrows do the same, and Home or a separator double-click resets widths. Lowest-tier dots use one analytic arc; deeper dots follow their own goal lobe. Six essay roots end at different levels. At whole-essay scale, tiny sentence dots are omitted rather than drawn as a noisy solid mass; zoom exposes them.

Core values restores full charts, tubes, vectors and three observations per entry. Creator has seven drives plus three constructed entries; Global has seven drives plus eighteen constructed entries. Category icons replace list confidence pies; the detail card retains its pie. The list keeps the established two-column scrolling height. The initial interaction hint now disappears once a selection is held, fixing an overlay that blocked the value tabs in the native narrow panel.

Remaining refinements worth testing with you:

1. **Orientation in a thousand-sentence graph.** The whole-essay silhouette communicates scope, but cannot make individual sentences easy targets. Page selection and zoom are the primary route. A small current-section cue or jump list may help more than additional marks.
2. **Divider discoverability.** Hover/cursor and keyboard focus expose the handles without adding permanent clutter. If reviewers miss resizing, show a one-time hint on the first graph focus rather than another button.
3. **Local focus after page changes.** Expanding content rebuilds exact anchors and currently clears the held selection. Preserving a uniquely matched sentence through that refresh would reduce interruption; it must not silently bind a changed sentence to its old analysis.
4. **Category comprehension.** Flame/layers distinguishes drive versus constructed value visually. Test whether the icons communicate that distinction without opening Help. Keep confidence separate from drive strength and from the category itself.
5. **Sparse-page wording.** The homepage is a useful opposite of the essay, but its interface headings are still text targets. Review whether every navigation-like heading needs attention analysis, or whether a future capture policy should prioritize substantive claims.
6. **Demo versus backend.** These invented accounts support usability testing, not conclusions about the creator. Before inviting external testers, explain that once in the review instructions. A backend connection and measured uncertainty remain outstanding.

See `evidence/website-validation.json` for the live native-Chrome receipt and `evidence/review-validation.json` for the separate deterministic native regression receipt. Images and receipts are ignored local QA evidence.

## Previous follow-up: snapshot text, graph entry and continuous type

The accepted keyboard, connector, font and small-icon recommendations are implemented. Tab enters one remembered graph cell, additional relationships have subtle endpoint dots, and a locally bundled continuous weight face removes regular/bold quantization. The creator portrait remains the supplied full artwork; 16/32 px icons use the new thin-outline variant.

The default reading now uses the public Art essay. Every sentence has exactly one graph location, including the appendix. Its 1,402 cells revealed two real defects: cell borders erased the overview at very small scale, and the capture adapter skipped five short headings/captions. Both are corrected. Offscreen detail is omitted only for large graphs; a regression check caught and corrected that optimization affecting small graphs.

The next review should distinguish **content fidelity** from **interpretation quality**. The page’s involvement disclosures are observed; the topical attention ranking and functional grouping are editorial demonstrations. Unspecified confidence stays unspecified, and nine possible values cite public text without scores. Git records can establish saved revisions, not a private mental sequence or AI authorship by themselves.

Remaining review priorities:

- Test whether the very dense whole-essay overview still helps orientation. A section jump control may be more useful than adding more marks, but is not added without a demonstrated need.
- Review section purposes and possible values with the creator before treating them as a reference analysis. Sentence labels currently quote the sentence, avoiding a fabricated fine-grained intention.
- Check whether readers understand “Not supplied” confidence and question-mark value indicators. These are intentional gaps in the evidence, not failed loading.
- The snapshot is text-focused. Figures, interactive citations and original site layout are outside this pass; the original essay is linked prominently.
- The small icon is now optically simplified. Compare its actual 16 px appearance with the retained creator image before selecting it for publication.

Build and native validation are recorded in [STATUS.md](../STATUS.md). This remains an engineering review, not participant research or a live backend validation.

## Previous review: typography, identity and compact values

The three-panel composition still works best as a restrained reading companion. Keep the graph shape and use the supplied head artwork for identity; adding a face behind the graph would compete with its already dense marks. This pass makes no new claims about inference accuracy.

The three titles now share Current attention's 11 px type. The supplied `ToMpathy.png` appears above the creator name and supplies the extension's 16/32/48/128 px icons and development favicon. The original artwork remains intact. Attention size and boldness both respond to supplied support; branch boldness uses weighted prominence, not an invented probability. Value-label boldness uses the same absolute confidence mapping. Missing confidence remains neutral. Cloud collision measurements include the heavier text.

Core values retains two columns. Four complete rows plus half of a fifth expose the beginning of the ninth entry. A ninth authored demo preference, Player agency, makes the affordance inspectable. This is a display fixture, not a new inferred conclusion. Row heights remain consistent, long labels use up to two lines, and keyboard focus scrolls the ninth entry fully into view.

Extra-parent connectors now choose the nearest valid corners by the actual vertical/horizontal route length. The three demo relationships use direct vertical drops, including the relationship that travels upward. No relationship or hierarchy ownership was changed.

### Defects found and addressed

- At 320 px, the Core values corner title covered the end of Curiosity. Clearance now responds to the actual first-row text and heading bounds; both columns remain aligned. No extra heading band is reserved when there is no collision.
- In a 600 px-high viewport, an automatic grid track squeezed the values panel below its contents. The values track now retains its content height and the reader scrolls as needed, keeping the footer reachable.
- At 320 × 450 px, the Core values explanation was about 526 px high and extended above the viewport. Hover previews are now bounded. Clicking a heading, or activating it with the keyboard, opens the existing scrollable Help dialog at that section; Escape returns focus. The surface remains three panels with no added persistent control.

Heading clicks wait half a second so the existing double-click-to-unlock gesture still works; keyboard activation is immediate. Escape and focus changes cancel that pending click. This is an interaction tradeoff worth observing in the next review, rather than hiding it behind an apparently unresponsive button.

### Recommended next improvements

| Priority | Observation | Recommendation |
| --- | --- | --- |
| High | Every graph cell is a Tab stop, despite working arrow-key navigation. A large graph makes it laborious to reach the controls below. | Use one Tab entry for the active graph cell, move among cells with arrows, and let the next Tab leave the graph. Keep separate access to zoom and order-uncertainty controls. |
| High | Several dotted relationships can share the same short vertical route. They are geometrically correct, but a line crossing intervening tiers can look like a relationship to those tiers. | Test a selected shared-parent example with a new reader. If they misread it, add subtle endpoint emphasis only during inspection; retain the requested dotted vertical route. Avoid adding permanent labels or line decorations before that observation. |
| High | Size and boldness reinforce the same score, while sentence ink, sentence grade and value wheels have distinct meanings. The visual distinction is clear to the builder but remains untested with outsiders. | Ask a participant to explain a large attention phrase, a faint sentence and a thin value label separately. Check that they understand confidence in an assessment is different from creator involvement or importance of a value. Keep the present treatment as an experiment until then. |
| Medium | The small creator confidence range produces intentionally subtle weight differences. Georgia also has discrete regular/bold faces rather than a continuous weight axis. | Judge this pass by readability first. If continuous changes are preferable, use a locally bundled variable weight face and remeasure word packing. Do not stretch each view's confidence range merely to exaggerate its differences. |
| Medium | Broader clouds retain all supplied focuses, so many labels become very small. They can be inspected, but are poor scanning targets at the widest branch. | Test a broad branch at native panel width before changing density again. Preserve all supplied focuses; investigate temporary magnification of the attention panel if users cannot reach a desired phrase. Do not silently drop low-ranked items. |
| Medium | Heading explanations are reachable now, but the Core values help is still a long theoretical paragraph. | Split the full explanation into “how to read this,” one concrete example, and the limitations. Keep the deeper theory in Help rather than adding instructional prose to the main panels. |
| Medium | The new icon reads as a left-facing profile at small sizes; the inner teardrop becomes much less distinct at 16 px. | Review the actual Chrome title/toolbar size before finalizing. A separate optically simplified 16 px drawing may preserve the inner opening better than scaling the master. The current pass deliberately retains the supplied drawing. |
| Medium | Small windows need both reader scrolling and values scrolling. This is preferable to clipped controls, but the nested scrolling can surprise people using a trackpad. | Include a laptop-height session and observe where wheel gestures land. If it causes confusion, review minimum graph height before reducing text or interaction targets further. |
| Medium | Global and Search remain demo previews, and linked-source context is not a trained search agent. | Keep the distinction explicit in the review introduction and Help before outside testing. Do not interpret a completed context progress bar as refreshed backend estimates. |
| Lower | Several visual controls and sentence cells are small, and the idle cue intentionally falls below normal contrast guidance. | Include keyboard and magnified-text tasks in the first participant trial. This pass is not a WCAG certification; preserving the requested faint cue does not establish broad accessibility. |

### Review coverage and limits

Code inspection and automated browser flows cover every sentence's unique graph cell, shared parents, click-to-center, arrow navigation, zoom/pan/fit, ambiguous reels, lock release/reminders, creator switching, missing/invalid input, revised accounts, export/import, context cancellation/cache, light/dark themes, reduced motion and 200% zoom. The added compact-layout checks exercise 320/360/400 px widths, the ninth-entry scroll affordance and short-window Help. Exact run outcomes and the ordinary Chrome build are recorded in [STATUS.md](../STATUS.md).

This is an engineering and visual review, not observed user research or a screen-reader certification. The most useful next validation is a person unfamiliar with the design completing five tasks: inspect a sentence, hold and release it, explain a shared-parent route, find its source again, and explain what a confidence cue means. No new context model or inference backend is implied by the UI changes.

## Earlier review and decision history

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
