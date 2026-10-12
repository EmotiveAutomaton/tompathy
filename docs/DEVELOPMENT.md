# Development and QA

ToMpathy owns the reader, Chrome integration, result validation and demo. Sounding Line will supply inference through `src/core/provider.ts`; no endpoint is currently configured.

## Everyday review

Run `npm run review` or double-click **Review ToMpathy.cmd**. The launcher builds `dist`, verifies installation in an isolated ordinary-Chrome profile, and opens the Review desk. Choose **Open the testing environment**, then **Open Maker Reader**. The third card opens the temporary **Icon studies**; the live-creator card is disabled until live analysis is available. Bookmark the desk if useful. After a full Chrome restart, run the launcher again so its development installation is restored. Preferences persist; readings are session-local unless exported.

After code changes, run the launcher again and refresh old article tabs. An unchanged build leaves the current reading in place. Chrome controls left/right side-panel placement through Settings → Appearance.

The separate development profile is `.local/chrome-review`. It enables Chrome’s extension-development interface for this workflow; do not use it for personal browsing. Manual **Load unpacked → dist** works without the launcher or that interface. An apparently empty folder-picker window is normal: select the folder, not a file.

## Review sequence

1. Hover different sentences. Attention should shift independently of the hierarchy; values should stay fixed. Moving through whitespace retains the last inspected item without locking it. The next sentence or graph cell replaces that soft hold.
2. Click a sentence, then move away. Both page and panel should retain a matching green lock. Rapidly hover four different blocked targets: both locks should gently emphasize, while the held selection stays fixed. Ordinary movement over one target should do nothing.
3. Click **Show the iteration**, then hover its reel. The other reels expand upward over a faded hierarchy, without moving their bottom edge. Inspect or select a candidate. Each candidate should highlight only its own path. The lock follows the upper-left corner of the first reel.
4. Escape first dismisses the active expansion/dialog. Click a lock, or double-click anywhere in the active page/reader, to release the selection. Directly hover a lower-branch node: only that branch should light up, and its unused final reel should close into a thin horizontal aperture. Move above a short reel: expansion should close immediately, while a small gap between adjacent boxes remains traversable.
5. Use the brain/name control at the upper left to choose a creator. Open Options from the three dots at the bottom right of Core values. Review Light context, Agent search, the GitHub preference and Color scheme. **View context and timeline** opens extracted dates, undated facts and source coverage. Creator-like models and word analysis remain disabled. Light context does not invent results for a page without analysis.
6. Export a reading, import it, and check page/panel hover and locking. Updated imported revisions must survive switching away and returning.
7. Open **Icon studies** from the Review desk. Compare the twelve brain-and-profile logo concepts at 16, 24, 32 and 48 pixels, then open a study and use the arrow keys to compare concepts. These are proposals; choosing a study does not change the reader.

## Test-only controls

Developer-only controls remain available through the browser preview at `/?qa` and `/?panel&qa`, or by adding `?qa` to the extension example URL. The Review desk has only the test environment, disabled live-creator entry, and icon studies; ordinary Options stays clean.

These tools retain raw packet import, source export, manual context, revision fixtures and session diagnostics. To demonstrate a revision, choose Context → Preview example revision → Accept this revision. The previous account remains inspectable.

`npm run testbed` prepares and serves a localhost article with matching downloadable packets. These fixtures are synthetic; use their exact source URL. The provider contract rejects a packet bound to a different capture or context selection.

## Checks and evidence

- `npm test`: schemas, hierarchy geometry, retrieval bounds, cancellation, explicit GitHub profiles and revision semantics.
- `npm run test:browser`: preview, responsive/keyboard flows and installed page-adapter behavior.
- `npm run test:review`: ordinary Google Chrome; real native side panel, toolbar permission grant, file round trip and full browser restart.
- `npm run test:native`: additional isolated Chromium lifecycle and long-page checks.
- `npm run package` then `node scripts/verify-package.mjs`: every ZIP member matches the build; source maps and development records are excluded.

Use project-local Playwright. `npx playwright install chromium` supplies its test browser; ordinary Google Chrome must be installed separately for `test:review`. Linux CI uses Xvfb for native-panel tests. UI screenshots alone do not establish extension integration.

For a small UI change, run `npm run build` and the affected spec, for example
`npm run test:browser -- tests/efficiency.spec.ts`. Run browser checks serially;
the configuration already uses one worker. Use `test:review` when Chrome
integration changes, and reserve the full sequence for broader regressions and
release validation. The built extension needs no Vite server: close the review
window when finished and reopen it with `npm run chrome`. Test browsers close
on failure as well as success. Attention bubbles into place, then settles; a
held reading no longer keeps the cloud animating indefinitely.

Receipts and screenshots are generated under ignored `evidence/`; failure traces are under `test-results/`. The public README image lives in `docs/assets/`. CI retains generated verification artifacts for 14 days. Never add personal browsing traces, user readings, credentials or local profiles to Git.

## Code map

| Location | Responsibility |
| --- | --- |
| `src/App.tsx`, `src/components`, `src/mind.css` | Reader, Options, evidence and interactions |
| `src/core/hierarchy.ts`, `attention.ts` | Supplied graph layout and independent attention |
| `src/content.ts`, `browser.ts`, `background.ts` | Text anchors, Chrome messages and page lifecycle |
| `src/core/model.ts`, `reading-file.ts` | Runtime schemas and portable reading files |
| `src/core/collector.ts`, `page.ts`, `creator-context.ts`, `context-source.ts` | Creator-link discovery, bounded retrieval, cache and timeline extraction |
| `scripts`, `tests` | Build, fixtures, review launcher and repeatable checks |

The development display version is **0.2 development 2**; npm uses `0.2.0-dev.2`, and Chrome uses numeric `0.1.2`. The published 0.1 beta is unchanged. See [versioning and the 0.2 workflow](VERSIONING.md). Once uploaded to a Web Store listing, each later numeric version must increase.


## Reading treatment review

The current development example is **The door we stopped explaining**. Run `npm run review` (or **Review ToMpathy.cmd**), open the example from the review guide, then use **Open Maker Reader**. If an old example tab remains after an update, reload that tab too.

1. Read the opening normally. Hover or Tab through sentences; click or Enter to hold a sentence. Escape, either lock, or double-click releases it.
2. Continue through the access discussion and the account of writing with an assistant. Compare full ink, nearly full ink, grey, and reversed text. The stroke grade varies independently. Existing bold emphasis is underlined.
3. Pause for a sentence's evidence tooltip. It shows involvement and confidence as two visual scales beside a large letter sample, followed by at most three evidence bullets. The fixture evidence remains fictional; the tooltip omits repeated explanatory prose. A ghost-text card also shows its supplied estimated generation prompt beneath the evidence.
4. Open **Options → View context and timeline** to inspect the five dated fictional records. Context remains unselected until an analysis explicitly uses it.
5. Export and import a reading to preserve the exact text, emphasis, sentence judgments and context. Plain offline HTML retains original bold; reopening in ToMpathy applies the current reading treatment.

The dot comparison is resolved: small dots now indicate cells with room for a marker; goal labels replace them as the cells become readable on screen. There are no new perpetual animations or running models. The font is loaded by the native adapter only when a sentence account arrives.


## Zoomable hierarchy review

1. Open the example in **Review ToMpathy.cmd → Open the testing environment → Open Maker Reader**. Reload an older example tab after the launcher rebuilds.
2. Read through the final paragraph. Each of the thirty sentences has a cell, including the late reflection, copy-edit pass and unreviewed generated insertion. The latter belongs to an automated assembly branch, not a reviewed creator choice.
3. Wheel over the hierarchy to zoom at the pointer; drag to pan. Pinch is supported by D3. Click a cell to hold it. Click blank graph space, double-click, Escape or either lock to release. The small four-corner button at bottom right fits the entire graph again.
4. Zoom toward a highlighted cell. All labels fade in together once the hardest-to-fit label has enough room. Their positions remain attached to their cells while you pan. Dots stretch into a subtle waveform before giving way to text. The sentence column has 1.5 shares versus one share per other tier. Selection persists while navigating.
5. Hold a sentence with a resolved path, scroll the article away, and click the arrow/magnifier below the reel lock. The page returns to the sentence and briefly deepens its highlight. The button greys after arrival and becomes active on the next document scroll. Selecting a graph cell alone no longer scrolls the page.
6. Tab to the graph background: **+ / −** zoom, **arrow keys** pan, and **Home / 0** fit. Node focus and Enter/Space still select. Reel wheel gestures continue to choose goals; they do not zoom the graph.
7. Pause over a sentence. Compare the large letter sample to the text: ink identifies involvement, stroke grade identifies classification confidence. Up to three supplied evidence excerpts explain the judgment. The demo's draft and context records are fictional; no inference runs on real pages.

[D3 zoom](https://d3js.org/d3-zoom) was selected because it handles SVG mouse/touch gestures, click-distance discrimination and programmatic fit without replacing the existing hierarchy renderer. The field allows generous pan margins and at least 32× zoom; the maximum grows when thin cells require more magnification. Minimum zoom is the centered whole graph, and the fit control returns there in a short eased transition. Text appearance depends on cell dimensions in screen pixels, not the zoom multiplier alone. Layout remains cached across pointer updates, and zoom has no idle animation loop. A pathological DAG that would unfold into more than 600 visual instances retains the scrollable list fallback to avoid exponential expansion; this is a deliberate bound, not literal unlimited graph capacity.

Targeted checks: `npx playwright test tests/navigation.spec.ts tests/reading.spec.ts`. `npm run test:review` also exercises navigation and sentence finding in an actual native Chrome panel and saves `evidence/navigation-native-*.png`.


## Soft inspection and branch attention

Article hover uses the most specific supplied attention frame. Graph inspection combines the frames covered by that node’s descendant sentence spans, retaining every distinct attention hypothesis. Shared DAG paths do not duplicate a frame. For multiple frames, size uses mean normalized support with absent items counted as zero; this is a relative overview, never a combined probability. A single frame retains its supplied support unchanged. Missing attention stays missing.

The last hovered target persists across whitespace. A new target replaces it; click still creates an explicit lock. Release, source changes and stale-source cleanup clear either state. Hovering an order-uncertainty mark inspects its common parent and softly highlights the possible subordinate choices. Absent hierarchy levels close their reel aperture without moving neighboring reels.

The idle “hover” cue is deliberately faint decorative text, at the requested 10 px / 32% opacity. Sentence ink and interactive controls retain their separate accessibility treatments.

## Icon studies

`icons.html` is a local, offline gallery of twelve original SVG logo proposals, each placing one or two lateral teardrop graphs inside a left-facing profile. This second round varies the head silhouette, overlapping lobes, open contours, cutouts and a tail turned down into a stem. Every card shows actual toolbar sizes and a larger view; opening it compares light and dark backgrounds. Arrow keys move between studies. These are visual proposals only: the production logo and the hierarchy remain unchanged. The superseded hierarchy-shape gallery and its build outputs have been removed.

The top-left creator selector uses its own small left-facing brain, with the stem at right. Options is in the Core values footer. Attention demo labels average 2.5 words and use up to two lines. Sentence evidence puts the classification and confidence above aligned tapered arrows. Smaller, right-aligned letter-by-letter legends below both arrows run from Less to More; an estimated generation prompt, when supplied for ghost text, appears beneath the evidence rather than in the article. The prompt remains in the native tooltip’s private shadow tree. Selection bloom is finite (230 ms), has no idle animation, and is suppressed for reduced motion.

Targeted checks for this pass: `npx playwright test tests/review-pass.spec.ts`. The maintained native Chrome check also visits the dashboard and icon studies before exercising the real side panel.
