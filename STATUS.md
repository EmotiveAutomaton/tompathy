# ToMpathy status · 2026-10-11 · 0.4.0

The second verbal design pass is implemented. The final packaged build is `f5dc07e3b494`. Chrome uses **ToMpathy - What's on the author's mind?** and a new tiled, right-pointing pyramid icon. The reader still has exactly three panels.

## Current design

- **Current attention:** support controls a wider type-size range (about 9–28px in the example at a 360px panel width). A governing purpose stays centered. Stable IDs preserve shared phrases; smaller phrases have an irregular outward bias, gentle drift and soft entry/exit. Scores remain the supplied values, with no simulated live inference. Reduced motion and a readable list fallback remain supported.
- **Expertise, Habits, and Hierarchical Goals:** the bricks form one continuous tapered silhouette. Ancestor paths and descendant fans use the same green as the corresponding source. The triangle stays visible during page hover and locking.
- Compact 56px reels sit below the triangle in document flow. There are no fixed level captions or separate lock row. Single-click text or a brick to hold a selection; scroll over a reel or use its arrow keys to select a neighboring goal. Choosing a parent holds all its associated text, while blurred lower reels indicate unresolved descendants. Escape or the small lock releases it. Native text dragging and links remain usable.
- **Core values:** two columns, capped at the nine most supported supplied values, stable across passage changes. Wide passive tooltips summarize support and page/context/decision evidence, close when the pointer leaves, and never intercept pointer events or introduce their own scrollbars. Full evidence remains available by selecting a row or using All supplied hypotheses.
- The middle heading opens an illustrated explanation with the owner's line about expertise as a lossy, compressed record of earlier attentional focuses. It is presented as the project's conceptual model. Tooltips stay within Chrome's extension viewport; they cannot extend outside the native panel document.
- Contract **1.3** accepts optional descriptive level names and up to 64 hierarchy levels. The renderer follows parent links and scrolls deeper reel paths horizontally. Versions 1.0–1.2 remain readable. Cycles, invalid spans, cross-maker references and invalid region containment remain rejected. Multi-root/multiple-parent graphs are deferred, as requested; no extra peaks are simulated.

## Verification

- TypeScript/build and **15 core tests** passed, including 1.3 unnamed deep paths, the depth boundary, cycle rejection and legacy compatibility.
- **10 browser/adapter flows** passed: single-click locking, native text selection and links, wheel/keyboard navigation, persistent triangle and compact reel geometry, non-overlapping cloud phrases, wide font range, passive value tooltips, top-nine values, eight unnamed levels, narrow/dark/reduced-motion/200% zoom, evidence and accepted revisions.
- Ordinary **Google Chrome 154.0.8037.98** passed fresh installation, the actual 360px native side panel beside its source, the title and illustrated explanation, linked sentence/branch locking, wheel-driven source highlighting, value provenance, ordinary HTTP activeTab capture, accepted-reading preservation, and installation restoration after complete browser restart. Final-build receipt: `evidence/review-validation.json`. No page-script errors were recorded. Screenshots were visually inspected, including the tooltip after its entrance animation.
- Native **Chromium 153.0.8010.12** also passed close/reopen cleanup, worker-stop recovery, tab-return recapture, accepted revision retention and a 1,006-passage fixture. Twelve local hover-to-panel frame samples were 6.5–17.5ms; this is a small local observation, not a performance guarantee. See `evidence/native-validation.json`.
- `tompathy-0.4.0.zip` was verified against `dist/`, including manifest, icons and bundled guide. No permanent webpage host permission was added. See `evidence/package-verification.json`.
- One new test initially expected the wrong ninth-ranked value; inspection confirmed the supplied scores put Fixture preference 9 ahead of Care for others. The expectation was corrected and the full browser suite passed.

## Review loop

Double-click **ToMpathy Review** on the desktop, or `Review ToMpathy.cmd` in this project. The launcher rebuilds and restores/updates the extension in the persistent review profile. Choose **Open the guided example**, then **Open Maker Reader**. The revised Review desk and README describe the new controls. No development server is needed for this example.

Bookmarks work within an open review session. Use the launcher after restarting Chrome/Windows because Chrome removes development-API installations at startup. The launcher restores the same ID; local preferences persist. Save a reading session before replacing a build or closing the browser if you need its captured account later. The launcher does not pull, merge or publish automatically.

The private CI pipeline builds, tests core/browser/ordinary-Chrome flows, restores after restart, and packages the tested ZIP. Work remains on `codex/author-first-testbed`; main is unchanged.

## Remaining boundaries

Sounding Line integration remains explicit file exchange, with no live inference endpoint configured or backend jobs launched. Ordinary pages await a matching supplied result. The complete interactive example is fictional and hand-authored. Sources support interpretations rather than establish an author's internal state.

Multiple hierarchy peaks/parents, word-level analysis, richer multi-author selection and calibrated value confidence remain later work. Large hierarchies retain the list fallback. Arbitrary-page capture is heuristic; restricted Chrome pages, PDFs, closed shadow roots and inaccessible frames are outside ordinary DOM capture.

The user's untracked `TOMPATHY_THEORY_AND_ENGINE_REVIEW_2026-10-10.md` is preserved without edits or inclusion in the implementation commit.
