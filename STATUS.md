# ToMpathy status · 0.2 development

Updated 12 October 2026, Pacific time.


## Current navigation, context and logo pass

Build **7c9b799e1241** is verified in ordinary Chrome on `codex/0.2-development`. Versions remain `0.2.0-dev.2` / Chrome `0.1.2` (0.2 development 2). The published beta is unchanged.

- Graph clicks lock and gently center the linked text. Up/down keys select nearby cells in the same tier; left/right move between subordinate and broader goals. Offscreen keyboard selections are brought into the graph viewport. Find stays hidden after centering and returns after scrolling away. Escape clears the source focus frame while ordinary keyboard focus remains visible.
- Extra parents use dotted child-bottom-right to parent-top-left corner routes. Sentence evidence arrows point up/down for more/less creator involvement. Wider, shaded value tubes contain shorter vectors with varied forward angles.
- Light context persists across reader opening and creator/page changes. Collection uses existing host permissions automatically; new permissions require an Options gesture. Explicit creator links and one explicitly linked GitHub repository/file feed the timeline, with up to three revisions, small patches, source attribution and both Git timestamp meanings. Six sources, one repository, at most eight repository requests, 256 KB responses and a 30-second deadline bound the job. No paid service or inference model runs. Context remains selectable for the backend handoff; accepted scores do not change automatically.
- Small horizontal progress bars beside Options show completed work, become a checkmark and fade. Recent source history is reused for 15 minutes; Refresh bypasses it. Creator switching preserves the enabled context option.
- The Review desk now shows four generated left-profile/right-teardrop logo studies, small-icon previews and complete prompts, alongside the twelve earlier prompt directions. One transparency defect was repaired. The production icon is unchanged.

Verification: **29 core tests passed**. All **41 browser scenarios passed across the full run and one corrected-assertion rerun**. The full run had 40 passes; its remaining legacy assertion expected centered tooltip values despite the later request for left alignment. That assertion was corrected to test left alignment and passed. Coverage includes navigation, Escape, context startup/cancellation, caching, creator switching, value cards, gallery loading and prompt copy/download. Final ordinary **Chrome 154.0.8037.98** verified build **7c9b799e1241**, with a real **360 px native side panel**, keyboard cell navigation, automatic group centering, Find rearming, export/import, normal-page capture and full restart recovery, with **zero page errors**. The local ZIP contains 26 matching build files, 1,892,967 bytes, SHA-256 `82d9ec16eaaf0ccd5e0545b06a536eac1a40a36205a39addcd1b3832454c3fad`. A live unauthenticated MDN source-file lookup returned three dated revisions and patch excerpts; startup/cache behavior was separately tested with controlled fixtures.

Review: **Review ToMpathy.cmd → Open the testing environment → Open Maker Reader**. Click a graph cell, use arrow keys, scroll the article away and return with Find. Open **Icon prompts** for the generated studies. Enable **Options → Light context** and **Use GitHub when possible** on a page with explicit links; the timeline is under **View context and timeline**. Local screenshots and receipts remain in `evidence/`.

## Previous values, evidence and navigation pass

Build **a58f698297f6** is verified locally on `codex/0.2-development`. Versions remain `0.2.0-dev.2` / Chrome `0.1.2` (0.2 development 2). The published beta is unchanged.

- Creator values use 10–22% demo confidence. Global shows four shared labels and four additional values at 81–94%, restricted to the bundled synthetic example. It is not a population estimate.
- Value hover cards pair confidence wheels with preferred-state curves, uncertainty tubes, numbered vectors and three individually explained observations. Miniature vectors match the chart directions. Clicking opens the same graphical account in a stable dialog. Core values heading help preserves the proposed theory and identifies its limits.
- Sentence evidence uses arrows for more/less involvement and a neutral indicator when no direction is supplied. Classification and “% confident” labels align left; the reversed gradient continues through spaces.
- Find centers all highlighted source text for a locked branch, even when reels remain ambiguous. Existing grey acknowledgement and scroll rearming remain.
- Three existing shared-parent links show alternative line treatments for review: dashed arrow, thin line with ring endpoint, and wider translucent arrow. They all represent the same relation. Options dots sit eight pixels lower.
- Existing CSS opacity is reset on wholly annotated, text-only subtrees and restored on cleanup. Unrelated text/media are protected; a site opacity/filter on a shared outer container can still affect the result.
- Branch attention, Agent search wording, cloud colors and the testbed remain unchanged. No new locate-in-graph control was added.
- [Public GitHub source/history research](docs/CONTEXT_RESEARCH.md#website-source-repositories-and-revision-history--12-october-2026) recommends a bounded, free resolver using explicit source links and file revisions. The repository-history collector is a proposal, not implemented in this pass.

Verification: build/type and whitespace checks passed; **28 core tests passed**. **Nine relevant browser scenarios passed across targeted runs**, including the final four-scenario value/navigation/keyboard/tab pass. Early new-test failures were corrected test interactions (wrong node ID and focusing a non-focusable preview span); group centering itself passed. The final built extension passed **ordinary Chrome 154.0.8037.98** with an actual **360 px native panel**, group Find, both value sets, charts, keyboard help, reading-file round trips, source capture and full restart recovery. Receipt build **a58f698297f6**, **zero page errors**. Native and narrow value cards and directional sentence evidence screenshots were visually inspected. Test profiles and temporary servers were closed.

Review: **Review ToMpathy.cmd → Open the testing environment → Open Maker Reader**. Hover an edited sentence, compare **Care for others** with **Global → Personal agency**, then lock **Show the iteration** and use Find. The complete proposed model is under the **Core values** heading. Local evidence includes `values-narrow.png`, `reading-directional-evidence.png`, `review-value-detail.png`, `review-global-values.png` and `review-validation.json`.

## Previous hierarchy, attention and UX review

Build **78f942d1b7ef** is verified locally on `codex/0.2-development`. Versions remain `0.2.0-dev.2` / Chrome `0.1.2` (0.2 development 2). The published beta is unchanged.

- Every supplied node has one visual cell. Shared parents remain explicit connecting lines during inspection and alternatives in the odometer. All thirty source sentences select exactly one matching cell; graph selection returns to that same sentence. Order-uncertainty markers also survive when their shared siblings occupy different geometric branches.
- The shared left boundary and lowest-tier dots follow continuous elliptical arcs. Individual curved brick edges have finer sampling near their endpoints.
- Branch attention combines recurrence and supplied confidence/support with equal sentence weights. Shared paths and split/overlapping frames cannot multiply a sentence's contribution. Hover details explain coverage; unscored entries do not receive invented confidence.
- Sentence-card values are larger, centered and nearer the arrows. Smaller legends have more spacing around their dots. Both scales read Less to More.
- The reminder needs twelve rapid blocked-focus points; page sentences count twice. Blank graph clicks clear without a black focus frame; keyboard focus remains visible.
- **Icon prompts** replaces the SVG studies: twelve contrasting directions, individual Copy buttons and a text download. No image model runs here, and the production icon is unchanged.
- A [comprehensive UX review](docs/UX_REVIEW_0.2_DEVELOPMENT.md) covers interpretation, orientation, visual density, keyboard use, context, performance and a practical participant trial. Highest priorities: finding exact sentences despite ambiguous ancestors, locating selected cells in a zoomed graph, explaining shared parents, and checking comprehension of involvement versus confidence.

Verification: build/type and whitespace checks passed. **27 core tests passed. All 36 browser scenarios passed across the full run, 12 affected reruns and a six-scenario final pass.** The final built extension passed the ordinary **Chrome 154.0.8037.98** QA loop with a real **360 px native panel**, page/panel locks and weighted reminders, complete sentence mapping, zoom/pan/fit, evidence cards, prompt copying, file round trips, normal HTTP capture and full restart recovery. The receipt names the same build, `78f942d1b7ef`, with **zero page errors**. Native, narrow, theme and expanded-reel screenshots were inspected. Disposable test browsers and servers were closed.

One earlier native run exceeded the five-second cloud-settling expectation; it did not recur in the following three runs. The animation diagnostic remains, and this is not claimed as a reproduced or fixed runtime defect. The tooltip accessibility check now waits for its restored exposed content after focus scrolls the page, rather than sampling during dismissal.

Open **Review ToMpathy.cmd → Open the testing environment → Open Maker Reader**. Refresh an older example tab after rebuilding. For icon exploration, choose **Icon prompts** from the Review desk; each prompt can be copied, and all twelve can be downloaded together. [Review guide](docs/DEVELOPMENT.md).

Current ignored evidence includes `evidence/review-validation.json`, `navigation-native-evidence.png`, `attention-native-combined.png`, `review-branch.png`, `refined-reels.png`, `icon-prompts-native.png`, and `icon-prompts-preview.png`. The local ZIP has 22 entries / 448,631 bytes and matches the built extension, including the prompt page. The README preview was refreshed and visually inspected. This pass remains local; no staging, commit, push or deployment was performed.

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
