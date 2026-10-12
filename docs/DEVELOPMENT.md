# Development and QA

ToMpathy owns the reader, Chrome integration, result validation and demo. Sounding Line will supply inference through `src/core/provider.ts`; no endpoint is currently configured.

## Everyday review

Run `npm run review` or double-click **Review ToMpathy.cmd**. The launcher builds `dist`, verifies installation in an isolated ordinary-Chrome profile, and opens the Review desk. Choose the guided example, then **Open Maker Reader**. Bookmark the desk if useful. After a full Chrome restart, run the launcher again so its development installation is restored. Preferences persist; readings are session-local unless exported.

After code changes, run the launcher again and refresh old article tabs. An unchanged build leaves the current reading in place. Chrome controls left/right side-panel placement through Settings → Appearance.

The separate development profile is `.local/chrome-review`. It enables Chrome’s extension-development interface for this workflow; do not use it for personal browsing. Manual **Load unpacked → dist** works without the launcher or that interface. An apparently empty folder-picker window is normal: select the folder, not a file.

## Review sequence

1. Hover different sentences. Attention should shift independently of the hierarchy; values should stay fixed.
2. Click a sentence, then move away. Both page and panel should retain a matching green lock.
3. Click **Show the iteration**, then hover its reel. The other reels expand upward over a faded hierarchy, without moving their bottom edge. Inspect or select a candidate.
4. Escape first dismisses the active expansion/dialog. Click a lock, or double-click anywhere in the active page/reader, to release the selection. Directly hover a lower-branch node: only that branch should light up, and its unused final reel should fade. Move above a short reel: expansion should close immediately, while a small gap between adjacent boxes remains traversable.
5. Open Options. Review author selection, Light context, Agent search, the GitHub preference and Color scheme. **View context and timeline** opens extracted dates, undated facts and source coverage. Author-like models and word analysis remain disabled. Light context does not invent results for a page without analysis.
6. Export a reading, import it, and check page/panel hover and locking. Updated imported revisions must survive switching away and returning.
7. Try the public-author link from the Review desk. Invoke the toolbar action to grant access. Capture should succeed; estimates await a matching result.

## Test-only controls

In the Review desk, expand **Development tools and example revisions** and open its special example. Its panel has a Development tools button; ordinary Options stays clean. The browser preview supports `/?qa` and `/?panel&qa`.

These tools retain raw packet import, source export, manual context, revision fixtures and session diagnostics. To demonstrate a revision, choose Context → Preview example revision → Accept this revision. The previous account remains inspectable.

`npm run testbed` prepares and serves a localhost article with matching downloadable packets. These fixtures are synthetic; use their exact source URL. The provider contract rejects a packet bound to a different capture or context selection.

## Checks and evidence

- `npm test`: schemas, hierarchy geometry, retrieval bounds, cancellation, explicit GitHub profiles and revision semantics.
- `npm run test:browser`: preview, responsive/keyboard flows and installed page-adapter behavior.
- `npm run test:review`: ordinary Google Chrome; real native side panel, toolbar permission grant, file round trip and full browser restart.
- `npm run test:native`: additional isolated Chromium lifecycle and long-page checks.
- `npm run package` then `node scripts/verify-package.mjs`: every ZIP member matches the build; source maps and development records are excluded.

Use project-local Playwright. `npx playwright install chromium` supplies its test browser; ordinary Google Chrome must be installed separately for `test:review`. Linux CI uses Xvfb for native-panel tests. UI screenshots alone do not establish extension integration.

Receipts and screenshots are generated under ignored `evidence/`; failure traces are under `test-results/`. The public README image lives in `docs/assets/`. CI retains generated verification artifacts for 14 days. Never add personal browsing traces, user readings, credentials or local profiles to Git.

## Code map

| Location | Responsibility |
| --- | --- |
| `src/App.tsx`, `src/components`, `src/mind.css` | Reader, Options, evidence and interactions |
| `src/core/hierarchy.ts`, `attention.ts` | Supplied graph layout and independent attention |
| `src/content.ts`, `browser.ts`, `background.ts` | Text anchors, Chrome messages and page lifecycle |
| `src/core/model.ts`, `reading-file.ts` | Runtime schemas and portable reading files |
| `src/core/collector.ts`, `page.ts`, `author-context.ts`, `context-source.ts` | Author-link discovery, bounded retrieval, cache and timeline extraction |
| `scripts`, `tests` | Build, fixtures, review launcher and repeatable checks |

The development display version is **0.2 development 1**; npm uses `0.2.0-dev.1`, and Chrome uses numeric `0.1.1`. The published 0.1 beta is unchanged. See [versioning and the 0.2 workflow](VERSIONING.md). Once uploaded to a Web Store listing, each later numeric version must increase.
