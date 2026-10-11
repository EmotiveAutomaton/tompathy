# ToMpathy status · 2026-10-11 · 0.3.0

The verbal design pass is implemented. The reader has exactly three panels: Goals, Process, and Core values. Chrome supplies the title “What's on the author's mind?” The author/header band and passage/pin footer are removed. Author identity, analysis origin and methods remain in the Reader menu, Source text and Help.

## Current design

- Goals use a persistent, animated phrase cloud. Declared support controls size; a governing goal remains centered. Shared IDs preserve positions as sentence-specific goals enter/leave. D3 force relaxation plus rectangle packing keeps phrases legible in a 360px Chrome panel. Movement settles and respects reduced motion. A list fallback handles dense results.
- Process rests as a rounded, right-pointing hierarchy: sentence goals at left, broader purposes at right. Hovering page text rolls the corresponding spools; unchanged ancestor spools remain still. Hovering/focusing a node highlights its ancestor path and descendant fan, plus matching source text. Blurred lower spools represent multiple possible descendants.
- Double-click locks a sentence without suppressing native word selection. A lock appears next to the source and inside Process. Escape or the Process lock releases it. Entering Process exposes the hierarchy even while locked.
- Core values is the smallest panel: a stable list with support wheels. Hover/focus reveals the larger wheel, the supplied scale and actual page/context/decision evidence. Relative support is never called calibrated probability. The heading explains why “latent preferences” is the creator's preferred term.
- Explanations are on hover/focus and in Help. The settings menu includes a disabled word-level reminder. All supplied hypotheses retains older historical process evidence outside the main hierarchy view.
- Contract 1.2 adds explicit maker-scoped goal hierarchy, exact UTF-16 sentence spans and decision references. Legacy 1.0/1.1 remain readable. Historical process edges never silently become parent/child goals. Invalid cycles, anchors and evidence references are rejected.
- Page integration uses CSS Highlights over original DOM ranges; it does not wrap or rewrite third-party prose. Recapture cancels pending invalidation timers, preventing an earlier mutation from invalidating a fresh capture.

## Verification

- TypeScript/build and 14 core tests passed, including hierarchy cycles, exact Unicode spans, same-maker decision references and legacy contracts.
- The frontend/adapter suite covers three panels, a stable cloud center, non-overlapping phrases, sentence spools, descendant/ancestor highlighting, double-click lock, keyboard help, disabled word-level settings, source export, accepted revisions, context cancellation, malformed inputs, narrow/dark/200% zoom, and exact capture identity.
- Ordinary Google Chrome 154.0.8037.98: the actual 360px native side panel, fresh verified installation, linked sentence selection, lock marker, branch highlights, value provenance, accepted revision preservation, normal HTTP activeTab capture, and installation restoration after complete browser restart passed. No page script errors were recorded. See `evidence/review-validation.json` and the `review-*.png` screenshots.
- Native Chromium 153.0.8010.12: panel close/reopen cleanup, worker-stop recovery, tab-return recapture, retained accepted revisions, and a 1,006-passage fixture passed. Twelve local hover-to-panel animation-frame samples were 8.7–21.8ms; this is a small local observation, not a performance guarantee. See `evidence/native-validation.json`.
- Visual inspection caught overlapping cloud phrases at native width; bounded packing and a browser assertion now cover that defect. Long-page checks now require a real selection/highlight, rather than merely timing an obsolete pointer event. Some Chrome startup/restart attempts hit the launcher's connection timeout; subsequent complete fresh-profile runs passed. The timeout is reported rather than counted as a passing attempt.
- A compatible source-map-js patch resolved the dependency advisory reported during installation; npm audit then reported zero vulnerabilities.

## Review loop

Double-click **ToMpathy Review** on the desktop, or `Review ToMpathy.cmd` in this project. The existing launcher rebuilds, updates/restores the unpacked extension in `.local/chrome-review`, and opens its bundled Review desk. Choose **Open the guided example**, then **Open Maker Reader**. The revised five-minute guide and README walk through the new controls. No development server is needed for this example.

Bookmarks work within an open review session. Use the launcher after restarting Chrome/Windows: Chrome removes CDP-installed extensions on startup, and the launcher restores the same extension ID. Local preferences persist; save a reading session before replacing a build or closing the browser if you need its captured account later. No browser preference files or policies are patched.

Private CI builds, tests core/browser/ordinary-Chrome flows, and packages the verified ZIP. The design branch is `codex/author-first-testbed`; main is unchanged. Publishing to the Chrome Web Store is outside this pass.

## Remaining boundaries

Sounding Line integration is still explicit file exchange, with no live endpoint configured and no backend jobs launched. Ordinary pages await a matching supplied result. The full interactive hierarchy is demonstrated by the fictional, hand-authored example. Sources support an interpretation; they do not establish an author's internal state.

Word-level analysis, richer multi-author selection and calibrated value confidence await later work. Capture remains heuristic for arbitrary pages; restricted Chrome pages, PDFs, closed shadow roots and inaccessible frames are outside ordinary DOM capture. Double-click locking is a deliberate first-pass interaction to review with the owner.

The user's untracked `TOMPATHY_THEORY_AND_ENGINE_REVIEW_2026-10-10.md` is preserved without edits or inclusion in the implementation commit.
