# ToMpathy status · 2026-10-11

Frontend 0.2.0 is built and packaged. The latest pass supplies the owner's repeatable QA loop: a one-click ordinary Chrome launcher, a bundled step-by-step review desk, automated installation/restoration, an action-permission fix, and private CI packaging. The preceding pass implemented the compact author-first header and the October theory/engine review. The three main sections remain the primary surface.

## Implemented

- Author-first header, approximately 69 CSS pixels tall in the measured preview, with tiny ToMpathy branding. Article title and editable requested author live in Source text. No header dropdown yet; existing multi-maker selection remains secondary.
- Explicit byline/metadata capture, with unknown identity when no attribution is supplied. A requested author never silently relabels an existing packet's subject.
- Contract 1.1 adds typed goals, historical events versus reader routes/repertoire, preferences versus values, coexisting goals, compatible whole accounts, typed process relationships and separate document/local contribution explanations. Legacy 1.0 remains readable. Temporal cycles and unresolved account/evidence references fail validation.
- The process tree displays supplied precedes/enables relationships; other relationships remain explicit cross-links, and shared nodes remain inspectable. No total chronology is manufactured from an unordered graph.
- Unknown contribution stays unpainted. Hover/source explanations name the contribution quantity and distinguish document-wide reasons, local evidence and uncertainty. Native page titles are restored on cleanup.
- Explicit revision acceptance retains up to five prior accounts and their evidence/context for inspection. Reopening the same matching built-in example preserves its accepted revision. Missing values no longer render as repeated per-passage placeholders.
- Improved article boundaries for conventional content containers and the two chosen public test pages. Page-wide fallback is labeled for review. Context is deduplicated by exact source/excerpt; new context IDs match Sounding Line's offline hash convention.
- Export either the plain capture or a request containing the requested author, exact snapshot and selected context only. No live inference endpoint is configured; no backend jobs or research environments were changed.
- `Review ToMpathy.cmd` / `npm run review` builds and opens a separate ordinary Chrome development profile, loads/verifies the extension and opens the bundled review guide. `npm run chrome` uses the current build. The guide and complete synthetic example need no local server. `npm run testbed` remains available for ordinary HTTP capture and result-file exchange.
- A content fingerprint avoids unnecessary extension reloads. When an unchanged build already has a panel open, the launcher leaves that reading in place. After a complete browser restart, the launcher restores the extension with the same ID. Local preferences persist; readings still use temporary session storage.
- The toolbar action now explicitly opens the side panel before asynchronous capture work. Chrome's automatic `openPanelOnActionClick` path bypassed the action event and did not grant `activeTab`, leaving ordinary-page capture unavailable. The corrected flow is tested with the delivered manifest and no added host permissions.
- The review desk includes a five-minute walkthrough, a real-author link, expected empty/backend states, update instructions, troubleshooting, and the build label to include in feedback. The CI workflow builds, tests, checks ordinary Chrome, and saves a verified private ZIP; it does not deploy or change the default branch.

## Fresh verification

- Build/typecheck passed. Twelve core tests passed, including new typed-contract, temporal-cycle, prior-account, selected-context and deduplication checks.
- Eight browser flows passed, including compact header, requested-author export, revision-history inspection, light/dark/narrow/zoom, malformed inputs, context cancellation, capture identity and legacy-layout extraction. The local testbed capture matches its downloadable packet exactly.
- Native Chromium 153.0.8010.12: actual side panel, source hover, pin/Escape, evidence-to-source, tree/cloud, fixed values, close/reopen cleanup, worker-stop recovery, tab-return capture and retention of an accepted revision after reopening passed. Latest long-page sample: 1,006 passages; local hover-to-panel frame samples under 20 ms. This is a small local sample, not a cross-hardware performance guarantee.
- The first native check read values before capture finished; its readiness assertion now waits for the known fixture values before measuring hover stability. The subsequent native check passed. No behavioral assertion was removed to hide a product failure.
- Connected Chrome 154.0.8037.98: current design preview opened and refreshed to the 1.1 fixture, zero console errors. Light, dark 320px and native panel screenshots were visually inspected.
- Public capture smoke: Datasette Lite article, 93 passages, Simon Willison supplied by page metadata; service-worker TIL, 14 passages, author unknown. Both retain main content and exclude the previously captured subscription/related-link boilerplate. Test-only host permissions are confined to the isolated test copy; no inference was requested. See `evidence/public-testbed-validation.json`.
- ZIP verified byte-for-byte against unpacked non-map assets. `tompathy-0.2.0.zip` has no permanent host permissions.

## Ordinary Chrome QA loop

The exact Windows `Review ToMpathy.cmd` entry point completed successfully and left the review guide open. A **ToMpathy Review** desktop shortcut was created and its target/working directory were read back. The first private [CI run](https://github.com/EmotiveAutomaton/tompathy/actions/runs/38142665302) passed every step and uploaded the verified ZIP and test receipts. The workflow pins Ubuntu 24.04, the tested runner OS, rather than following the imminent `ubuntu-latest` migration.

The connected automation Chrome process was observed running with `--disable-extensions` in a temporary Playwright profile. This is a concrete environment problem and a plausible explanation for an absent card; the owner's earlier folder-selection window cannot be identified retrospectively. The new launcher uses ordinary Google Chrome in this checkout's `.local/chrome-review`, without the disable flag, and verifies the loaded extension ID, version, path and enabled state through Chrome's development protocol. It never attaches to the personal Chrome profile.

The new regression check passed in Chrome 154.0.8037.98: fresh installation, guide-to-example-to-native-panel navigation, actual source-width reduction, hover, pin/Escape, stable values, tree/cloud, explicit revision acceptance, unchanged-launcher preservation, and a real extension-action invocation on an ordinary HTTP article. The last check caught the activeTab bug above; it now captures all six passages with the correct author. Screenshots are `evidence/review-desk.png` and `evidence/review-chrome-panel.png`; the receipt is `evidence/review-validation.json`.

The optional live pass (`node scripts/review-validation.mjs --public`) also passed against Simon Willison's linked Datasette Lite article using the actual extension action: 93 passages, correct metadata attribution, and **Awaiting analysis**, with no inference request. See `evidence/review-public-panel.png`. The restart check now waits for the owned Chrome process to exit fully before relaunching; a fixed one-second pause had proved unreliable.

The restart test also established that Chrome intentionally removes CDP-installed extensions at startup. The launcher restores the installation automatically and the test confirms the same extension ID and retained local preferences. No Chrome preference files or policies are altered to bypass that lifecycle. The owner should use the launcher after a full Chrome/Windows restart; bookmarks suffice within an open review session. A conventional manual Load unpacked installation is still an optional route for a regular personal profile.

The Windows UI helper ended because it could not confidently identify the current browser URL. No further native-helper input was attempted. Physical toolbar clicking, manual folder-picker confirmation, and OS shortcut invocation are not claimed by the CDP-driven receipt. The supported extension action and actual native side panel are verified in an isolated ordinary Chrome instance.

Earlier test failures were retained in the debugging record: panel width was initially sampled before its opening animation finished (fixed with a readiness wait); browser-level storage inspection lacked an extension context (fixed by reading through the tested panel); the initial restart expectation incorrectly assumed CDP loading persisted (corrected to explicit restoration after checking Chromium source). The ordinary-page capture assertion exposed a product bug, which was fixed without adding permissions or weakening that assertion.

Primary references: [Chrome extension loading and reloading](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world), [side-panel action behavior](https://developer.chrome.com/docs/extensions/reference/api/sidePanel), [CDP extension commands](https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/pdl/domains/Extensions.pdl), [Chrome cleanup of CDP-installed extensions](https://raw.githubusercontent.com/chromium/chromium/main/extensions/browser/extension_prefs.cc), and [isolating Chrome development profiles](https://developer.chrome.com/blog/remote-debugging-port).

## Remaining boundaries

- Live Sounding Line transport, authentication, job progress/cancellation/resumption and personal prediction models await a real service contract. Current integration is explicit file exchange. Stage 13 shape compatibility is tested locally; its scientific outputs are not re-evaluated here.
- The public collector still refuses redirects/private literal hosts and requests origin access explicitly. Permission-prompt acceptance in ordinary Chrome remains unverified. DNS aliases are not a browser-enforceable public-network boundary.
- Capturing arbitrary pages is heuristic. Some pages lack metadata, mix authors, or require selected/pasted text. Restricted Chrome pages, PDFs, closed shadow roots and inaccessible frames remain outside automatic DOM capture.
- Profiles and scientific claims are not inferred by this frontend. Synthetic estimates stay labeled; imported accounts are not automatically validated science. Old UUID context IDs require explicit mapping or recollection for Sounding Line's content-bound exporter.

## Resume

Owner review: double-click `Review ToMpathy.cmd`, or `npm run review`. Optional HTTP fixture: `npm run testbed`. Validation: `npm test`, `npm run test:browser`, `npm run test:review`. Package: `npm run package`, `node scripts/verify-package.mjs`. Source contract: `docs/INPUT_CONTRACT.md`. Browser receipts/screenshots: `evidence/`.
