# ToMpathy status · 0.2 development

Updated 12 October 2026, Pacific time.


## Current icon and reading refinement

Build **80c8fc357d16** is verified on `codex/0.2-development`. Versions remain `0.2.0-dev.2` / Chrome `0.1.2`; the published beta is unchanged.

- Twelve new original SVG studies place the lateral teardrop graph inside a left-facing head. The second round varies overlapping lobes, downward-curving stems, open cranial frames, faceted outlines and solid cutouts. Each has actual 16/24/32/48 px samples, light/dark detail views and a brief tradeoff. These remain proposals; the production logo is unchanged.
- Sentence classifications and confidence percentages sit above two aligned, tapered arrows. Smaller gradient legends sit beneath, right aligned, with **Less · creator involvement · More** and **Less · confidence · More**. Ghost-text prompts remain below their evidence, inside the native private tooltip.
- Creator names have an immediately adjacent chevron; the active name determines the visible control width. Its hit area follows the visible control, while the native option list accommodates other names. The find-in-page button is at the odometer’s lower-left corner and matches the 23 px lock. The shared reminder again requires four rapid blocked focus changes, with jitter filtering and cooldown retained.
- All hierarchy labels finish fading in sooner once every label can fit. They retain their cell anchors and shared threshold. Attention uses longer, tightly packed phrases and holds through gaps; the thirty-sentence fictional reading includes draft, edit and unreviewed-generation branches.
- The README now shows a fresh half-width development preview with a held sentence, visible evidence card, active attention and the complete hierarchy. This is a browser preview capture; native-panel integration is verified separately.

Verification: build/type and whitespace checks passed; **26 core tests and all 34 browser tests passed**, followed by five affected browser checks after tightening the creator control. The final native QA loop passed in **ordinary Chrome 154.0.8037.98** with a real 360 px panel, page/panel locks, reminders, zoom/pan/fit, sentence finding, private evidence and prompt cards, import/export, HTTP capture and restart recovery. No page errors were recorded. The native receipt names build `57c9fdab89c7`; the final build differs only in license line endings and its fingerprint, with identical runtime files. Screenshots were visually inspected; owned test browsers and servers were confirmed closed. The verified package has **22 entries / 445,901 bytes** and matches the build exactly.

Open **Review ToMpathy.cmd**, choose **Open the testing environment → Open Maker Reader**, and refresh old example tabs. Choose **Icon studies** on the Review desk for the twelve new proposals. [Detailed review guide](docs/DEVELOPMENT.md).

Ignored evidence: `evidence/review-validation.json`, `attention-native-combined.png`, `ghost-tooltip-native.png`, `navigation-native-evidence.png`, `navigation-native-zoom.png`, `icons-native.png`, `icons-gallery.png`, and `package-verification.json`.

## Previous local navigation and evidence pass

Build **2ed4d3fc65b5** is ready for local review. Version identifiers remain `0.2.0-dev.2` / Chrome `0.1.2`. No staging, commits, pushes or deployment were performed.

- The thirty body sentences were present in the previous fixture but crowded into fixed-size targets. The hierarchy now includes **four ends and five levels**, distinguishing the design story, access, later playtest, copy editing and the unreviewed automated insertion. The latter is not shown as a reviewed creator intention. Sentence width is 1.5 shares per one share of each other tier.
- D3 zoom adds pointer-centred wheel zoom, drag-to-pan, click selection, blank-space/double-click release and a quiet corner-bracket fit control. Keyboard +/−, arrows and Home/0 are supported. Small dots yield to goal labels based on actual cell dimensions; labels stay inside the visible portion of their cell. Pathological DAG expansion retains a bounded fallback.
- A resolved locked sentence has an arrow/magnifier below its reel lock. Find scrolls to the sentence, briefly deepens its highlight, greys after arrival and rearms on document scroll. Graph selection itself no longer scrolls the article. Native scroll acknowledgement sends one message per find, rather than a continuous stream.
- Sentence cards begin with a large combined ink/grade sample, independently labelled involvement and confidence, and up to three distinct supplied evidence bullets. The fixture provides draft and contextual evidence. No decision-share percentage is inferred. Duplicate summary text is omitted. Native cards retain their closed shadow roots and use constructed stylesheets; a scroll-settled check fixes tooltips that otherwise stayed hidden after automatic scrolling.

Validation: build and whitespace checks pass. **25 core scenarios passed across the full run and affected reruns**; **29 browser scenarios passed across the full run and affected reruns**. The final native QA loop passed in **ordinary Chrome 154.0.8037.98**, with a real 360 px side panel, zoom/pan/fit, labels inside the viewport, sentence finding and scroll rearming, accessible private evidence, file round trips, normal HTTP toolbar capture and restart recovery. No page errors were recorded. Final native screenshots were visually inspected. Test browsers and owned servers were closed.

[Review instructions](docs/DEVELOPMENT.md#zoomable-hierarchy-review). Ignored evidence: `evidence/review-validation.json`, `navigation-native-fit.png`, `navigation-native-zoom.png`, `navigation-native-evidence.png`. Open **Review ToMpathy.cmd**, choose the example, then **Open Maker Reader**; reload an older example tab after rebuilding.

## Previous local reading pass

Build **0049bc4b9799** is ready for review on the existing 0.2 development branch; versions remain unchanged. The bundled reading is now **The door we stopped explaining**: nine body paragraphs, thirty sentence accounts, an expanded hierarchy, independent attention frames, and a five-entry fictional studio timeline.

- The cue is **← hover**, 11 px and 64% opacity, with contrast checked in light and dark themes. The middle heading is **Expertise and habit (previous attention)**.
- Ghost Scale involvement controls ink: original, 95% opacity for light edits, contrast-clamped curator grey, reversed unreviewed generation, and unchanged styling when information is absent. An independent GRAD font axis controls classification confidence without changing word widths. Original bold becomes underline. Supplied prompts appear beneath ghost text.
- Sentence tooltips explain classification, confidence and evidence. On native pages, detailed records remain in isolated memory; tooltip and prompt content uses closed shadow roots. The page can still observe the visual styling. Text-node wrappers preserve existing elements, links, keyboard access and live source edits, and are removed on cleanup.
- Contract **1.6** adds optional creator-bound sentence accounts and portable emphasis ranges. Versions 1.0–1.5 still load. Example fixtures are now `examples/lantern-*`; the local HTTP testbed matches the same story. The unreviewed sentence has no supplied creator attention.
- The 52,604-byte Latin grade font is bundled with its OFL notice. No remote font service, model or perpetual animation was added. Native font loading waits for supplied sentence accounts.

Validation: **25 core tests passed**. All **27 browser scenarios passed across the full run and affected reruns**; the final targeted run repeated the installed adapter, reading presentation, keyboard selection, private tooltip DOM boundary, accessibility tree, restoration and updated HTTP fixture checks. The maintained ordinary Chrome QA command passed installation, native interaction, toolbar capture, reading export/import, tab switching and restart recovery. The final build also passed the focused ordinary Chrome 154 native reading loop with a 360 px panel, zero page errors and disposable-browser cleanup. Final native screenshots were visually inspected. The verified local package has 19 entries, 418,532 bytes; nothing has been published.

Evidence stays in ignored `evidence/`: `reading-native.json`, `reading-native-source.png`, `reading-native-panel.png`, `reading-native-ghost.png`, `reading-native-timeline.png`, and `package-verification.json`. Run **Review ToMpathy.cmd**, open the example, then **Open Maker Reader**. Context is under **Options → View context and timeline**. [Review steps](docs/DEVELOPMENT.md#reading-treatment-review).

### Dot comparison resolved

The 12 October review explicitly requested smaller dots that yield to text as cells become readable. This supersedes the temporary hidden-dot comparison and its two-review reminder.

## Earlier local efficiency refinement


Unpublished working changes retain the same development version. Build
**7f0953dece74** lets attention settle after its arrival animation, skips hidden
cloud layout, bounds remembered word positions, and closes owned test browsers
on failure. Five targeted browser checks passed. Ordinary Chrome 154's native
panel confirmed four perpetual idle animations under the previous rule versus
zero with the new rule, with live hover updates preserved and no page errors.
The disposable review browser closed afterward. See the ignored local receipt
`evidence/efficiency-native.json`; the earlier full-suite results below describe
the preceding iteration, not a repeated full run for this refinement.

Work is on `codex/0.2-development`. npm version: `0.2.0-dev.2`; Chrome numeric version: `0.1.2`; display: **0.2 development 2**. The published `v0.1.0-beta.1` release and main baseline remain unchanged. This is the second review iteration toward 0.2, not completion of that milestone. [Workflow](docs/VERSIONING.md).

## Earlier 0.1.2 iteration

- Creator terminology throughout the interface, context reports and example; **Previous attention (expertise and habit)** heading and quiet **`<- hover`** cue. Existing serialized fields and publisher metadata retain compatibility.
- Right-shifted, deeper dot arcs with full-circle clearance; uniform **Order uncertain** tooltips. A measured heading guard protects top dots from overlap when platform fonts are wider. Accepted graph layout is cached across pointer updates.
- The reel lock overlaps its top-left corner and follows expansion. Rapid blocked focus changes gently emphasize both locks with cooldown and reduced-motion support.
- Each expanded candidate highlights its own branch regardless of the previous hover. Arrow keys inspect candidates without prematurely changing the lock.
- System-dark palette correction, keyboard value tabs, viewport-contained document locks and context collection cancellation.
- Deselecting the last context restores artifact scope. Pending-context exports retain the previous account in history and round-trip without presenting stale estimates.
- [Detailed UX review, findings and next priorities](docs/UX_REVIEW_0.1.2.md).

## Earlier 0.1.2 verification

Earlier extension build **28168cc21f65**:

- **24/24 core tests passed**: contracts, sentence bindings, source identity, context deadlines/cancellation, revision handling, lock reminder thresholds/cooldown, and pending-context exports including rejection of changed anchors.
- **24/24 browser tests passed**: every sibling inspection order, keyboard navigation, both preview locks, motion preferences, dot clearance at three heights, heading access with wider fonts and zoom, cue contrast, explicit and system dark, context opt-in/cancellation, reading round trips, narrow panels, eight hierarchy levels, nine values and 200% zoom.
- **Ordinary Google Chrome 154.0.8037.98 passed**: actual 360-pixel native panel; reminders initiated from either document or panel; click/wheel/hover and branch behavior; file import/export; tab switching; toolbar capture with the shipped manifest; full restart with persistent preferences. No recorded page errors. The sandboxed launch could not connect initially; the authorized desktop run succeeded. The first CI push then exposed heading overlap with Linux font metrics; a layout guard and regression checks corrected it.
- The controlled 1,006-passage content-script fixture captured in **161 ms**; twelve hover-to-next-paint samples ranged **1.2–6.5 ms**. This is local content-script performance, not backend or complete panel latency.
- **Package verified**: 18 entries, 353,609 bytes. Every member matches `dist`; source maps excluded, license and dependency notices included. SHA-256: `2737cfb78517e5f6240bacc00e994b42620030f644d7e0ce3d4fa86d731df4fe`.

Quiet and active panels, expanded reels, theme states, Options, timeline and refreshed README image were visually inspected. Generated evidence remains in ignored `evidence/` and CI artifacts. The owner’s separate Chrome review profile was updated to the same build and left open on the example with **Watching closely** selected. Unpublished owner design files remain ignored and local.

## Review and boundaries

Use **Review ToMpathy.cmd** or `npm run review`. Hold **Show the iteration**, hover its reel and move among the four sentence options; each should inspect just its own path. While locked, move rapidly among several different text sentences or hierarchy nodes to see the gentle reminder. Either lock, Escape or double-click releases selection. [QA guide](docs/DEVELOPMENT.md).

The example is fictional and hand-written. Sounding Line is not connected to a live endpoint. Context collection is free, bounded extraction from explicit links and their permitted follow-ups, with a source timeline; it is not a verified biography. Broad web search, local summarization, creator-like models, Global and value search remain future work. No model downloads, training, paid services or Store submission were started. [Context implementation and limits](docs/CONTEXT_RESEARCH.md).
