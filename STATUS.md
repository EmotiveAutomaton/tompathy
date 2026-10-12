# ToMpathy status · 0.2 development

Updated 11 October 2026, Pacific time.

Work is on `codex/0.2-development`. npm version: `0.2.0-dev.2`; Chrome numeric version: `0.1.2`; display: **0.2 development 2**. The published `v0.1.0-beta.1` release and main baseline remain unchanged. This is the second review iteration toward 0.2, not completion of that milestone. [Workflow](docs/VERSIONING.md).

## This iteration

- Creator terminology throughout the interface, context reports and example; **Previous attention (expertise and habit)** heading and quiet **`<- hover`** cue. Existing serialized fields and publisher metadata retain compatibility.
- Right-shifted, deeper dot arcs with full-circle clearance; uniform **Order uncertain** tooltips.
- The reel lock overlaps its top-left corner and follows expansion. Rapid blocked focus changes gently emphasize both locks with cooldown and reduced-motion support.
- Each expanded candidate highlights its own branch regardless of the previous hover. Arrow keys inspect candidates without prematurely changing the lock.
- System-dark palette correction, keyboard value tabs, viewport-contained document locks and context collection cancellation.
- Deselecting the last context restores artifact scope. Pending-context exports retain the previous account in history and round-trip without presenting stale estimates.
- [Detailed UX review, findings and next priorities](docs/UX_REVIEW_0.1.2.md).

## Verification

Final extension build **5123f80ba7cc**:

- **24/24 core tests passed**: contracts, sentence bindings, source identity, context deadlines/cancellation, revision handling, lock reminder thresholds/cooldown, and pending-context exports including rejection of changed anchors.
- **23/23 browser tests passed**: every sibling inspection order, keyboard navigation, both preview locks, motion preferences, dot clearance at three heights, cue contrast, explicit and system dark, context opt-in/cancellation, reading round trips, narrow panels, eight hierarchy levels, nine values and 200% zoom.
- **Ordinary Google Chrome 154.0.8037.98 passed**: actual 360-pixel native panel; reminders initiated from either document or panel; click/wheel/hover and branch behavior; file import/export; tab switching; toolbar capture with the shipped manifest; full restart with persistent preferences. No recorded page errors. The sandboxed launch could not connect initially; the authorized desktop run succeeded.
- The controlled 1,006-passage content-script fixture captured in **150 ms**; twelve hover-to-next-paint samples ranged **0.7–7.9 ms**. This is local content-script performance, not backend or complete panel latency.
- **Package verified**: 18 entries, 353,293 bytes. Every member matches `dist`; source maps excluded, license and dependency notices included. SHA-256: `881daaeeb461503e885805da93f6cb5c559d78aa097e53336d061fa64b505c08`.

Quiet and active panels, expanded reels, theme states, Options, timeline and refreshed README image were visually inspected. Generated evidence remains in ignored `evidence/` and CI artifacts. The owner’s separate Chrome review profile was updated to the same build and left open on the example with **Watching closely** selected. Unpublished owner design files remain ignored and local.

## Review and boundaries

Use **Review ToMpathy.cmd** or `npm run review`. Hold **Show the iteration**, hover its reel and move among the four sentence options; each should inspect just its own path. While locked, move rapidly among several different text sentences or hierarchy nodes to see the gentle reminder. Either lock, Escape or double-click releases selection. [QA guide](docs/DEVELOPMENT.md).

The example is fictional and hand-written. Sounding Line is not connected to a live endpoint. Context collection is free, bounded extraction from explicit links and their permitted follow-ups, with a source timeline; it is not a verified biography. Broad web search, local summarization, creator-like models, Global and value search remain future work. No model downloads, training, paid services or Store submission were started. [Context implementation and limits](docs/CONTEXT_RESEARCH.md).
