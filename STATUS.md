# ToMpathy status · 2026-10-11 · 0.4.0 alpha

The third verbal design pass is implemented. The packaged build is `1272115bb534`. This remains a private **0.4.0 alpha**; the owner's intended future public release is **0.1 beta**, initially an empty frontend. No public release was made.

## Current design

- Exactly three boxes. Titles occupy rounded top-right corners; the Reader menu sits at top left. Content uses the top area around these controls instead of a reserved header band.
- **Current attention:** about half the previous height (180px at a 900px viewport). At rest it displays only **Hover to see**. Its data is independent of the goal graph. The demo changes its leading phrase across sentences; new words grow from small to full size while shared words shift into space. Size reflects supplied support, with a wide range. Reduced motion and list fallback remain available.
- **Expertise, Habits, and Hierarchical Goals:** one continuous outline with a rounded broad left edge and two peaks ending at different depths. Shared subgoals reach both ends. Brick rows partition the actual widest visible edge so all 27 demo nodes remain usable, with no phantom slivers or discarded semantic nodes. Dots are centered within the visible area.
- Reels are 42px high, sufficient for two lines, and remain below the chart. No gray node caption remains. A hovered brick glows at the corresponding reel. Ambiguous descendants, ancestors and early endings can appear on either side of an exact selection.
- Clicking text or a brick locks the selection. Attention and reels remain fixed through incidental hovering; wheel/keyboard reel navigation deliberately selects a new node. The same green SVG lock appears on the source and overlaps the far-right reel corner. Either lock or Escape clears selection. Sentence bricks supply that sentence's attention; parent bricks leave it at the idle cue.
- **Core values:** a larger two-column area (252px at a 900px viewport), eight demo values in four rows, still capped at nine supplied hypotheses. Passive evidence tooltips and full details remain. Bottom **author** and **world** tabs work; world is an explicit placeholder. Search expands, accepts text and Enter, and closes with its button or Escape. It sends no query.
- Contract **1.4** accepts separate attention frames at sentence or sub-sentence ranges and explicit multiple hierarchy parents/roots. The installed adapter and preview supply character offsets. Versions 1.0–1.3 remain readable without inventing attention. Historical process edges remain separate from the goal graph. No backend jobs or inference endpoint were added.

## Verification

- TypeScript/build and **17 core tests** passed: legacy acceptance, separate attention ranges and invalid references, multiple parents, cycles, depth limits, reel ambiguity, and visible-edge/dot geometry at three heights.
- **12 browser/adapter flows** passed: shifting attention and retained phrase identities, locking and both release controls, within-sentence snapshots, wheel/keyboard navigation, compact geometry, cloud collision/font range, eight values and top-nine limit, tabs/search, deeper unnamed hierarchies, narrow/dark/reduced-motion/200% zoom, imports, revisions, text selection and page cleanup.
- Ordinary **Google Chrome 154.0.8037.98** exercised the real 360px native panel beside its source: independent attention, two peaks, linked highlights, both green lock controls, bidirectional ambiguity, compact reels, evidence, tabs/search, installation, normal HTTP activeTab capture and full-restart restoration. No page-script errors were recorded. `evidence/review-validation.json` records its exact build.
- Native **Chromium 153.0.8010.12** passed close/reopen cleanup, worker-stop recovery, tab-return recapture, revision retention and a 1,006-passage fixture. Twelve local hover-to-panel frame samples were 14–29.2ms while another browser check was running; this is a small local observation, not a performance guarantee. See `evidence/native-validation.json`.
- Screenshots were inspected for light/dark layout, the two peaks, attention, locks, search and passive tooltips. `tompathy-0.4.0.zip` matches the built files and retains no permanent webpage host permissions; see `evidence/package-verification.json`.
- A new preview test caught an inline-lock removal causing a synthetic hover to select the next sentence. Selection now responds to actual pointer movement, and the regression passes. Clicking inside a sentence also preserves the pointed attention frame instead of reverting to its first frame.

## Review loop

Double-click **ToMpathy Review** on the desktop, or `Review ToMpathy.cmd` here. Choose **Open the guided example**, then **Open Maker Reader**. Hover the article's second and fourth paragraphs to see different attention centers. Click a sentence, move away, scroll a reel, and release using either green lock. Hover the shared branch to see ambiguity on both sides; try the bottom tabs and search.

The launcher builds and restores/updates the extension in the persistent review Chrome profile. No server is needed for the bundled example. Bookmarks work during an open session; use the launcher after restarting Chrome/Windows to restore the development installation with the same ID. Save a reading session before replacing a build or closing the browser if its accepted account must be retained. The launcher does not pull, merge or publish automatically.

The private CI pipeline builds, tests core/browser/ordinary-Chrome flows, restores after restart and packages the tested ZIP. Work remains on `codex/author-first-testbed`; main is unchanged.

## Remaining boundaries

Sounding Line integration remains explicit file exchange. Ordinary pages await a matching supplied result. The complete demo, including its attention weights, is fictional and hand-authored. Sources support interpretations rather than establish an author's internal state.

World/search behavior, word-level goal analysis, richer multi-author selection and calibrated value confidence remain later work. Large hierarchies retain the list fallback. Arbitrary-page capture is heuristic; restricted Chrome pages, PDFs, closed shadow roots and inaccessible frames are outside ordinary DOM capture. Hover panels stay within Chrome's extension document.

The user's untracked `TOMPATHY_THEORY_AND_ENGINE_REVIEW_2026-10-10.md` is preserved and excluded from this change.
