# ToMpathy status · 2026-10-11

Frontend 0.2.0 is built and packaged. This pass implements the owner's compact author-first header, the October theory/engine review, and the later Sounding Line clarification that process concerns possible historical production events. The three main sections remain the primary surface. The companion product/inference spec named by the review was not present; no unprovided requirements were invented.

## Implemented

- Author-first header, approximately 69 CSS pixels tall in the measured preview, with tiny ToMpathy branding. Article title and editable requested author live in Source text. No header dropdown yet; existing multi-maker selection remains secondary.
- Explicit byline/metadata capture, with unknown identity when no attribution is supplied. A requested author never silently relabels an existing packet's subject.
- Contract 1.1 adds typed goals, historical events versus reader routes/repertoire, preferences versus values, coexisting goals, compatible whole accounts, typed process relationships and separate document/local contribution explanations. Legacy 1.0 remains readable. Temporal cycles and unresolved account/evidence references fail validation.
- The process tree displays supplied precedes/enables relationships; other relationships remain explicit cross-links, and shared nodes remain inspectable. No total chronology is manufactured from an unordered graph.
- Unknown contribution stays unpainted. Hover/source explanations name the contribution quantity and distinguish document-wide reasons, local evidence and uncertainty. Native page titles are restored on cleanup.
- Explicit revision acceptance retains up to five prior accounts and their evidence/context for inspection. Reopening the same matching built-in example preserves its accepted revision. Missing values no longer render as repeated per-passage placeholders.
- Improved article boundaries for conventional content containers and the two chosen public test pages. Page-wide fallback is labeled for review. Context is deduplicated by exact source/excerpt; new context IDs match Sounding Line's offline hash convention.
- Export either the plain capture or a request containing the requested author, exact snapshot and selected context only. No live inference endpoint is configured; no backend jobs or research environments were changed.
- Build validation and an explicit success message name the exact unpacked directory. `npm run testbed` prepares the local fictional page/results and starts or detects the preview server. `npm run chrome` opens a separate ordinary Chrome development profile (launcher supplied; not yet acceptance-tested).

## Fresh verification

- Build/typecheck passed. Twelve core tests passed, including new typed-contract, temporal-cycle, prior-account, selected-context and deduplication checks.
- Eight browser flows passed, including compact header, requested-author export, revision-history inspection, light/dark/narrow/zoom, malformed inputs, context cancellation, capture identity and legacy-layout extraction. The local testbed capture matches its downloadable packet exactly.
- Native Chromium 153.0.8010.12: actual side panel, source hover, pin/Escape, evidence-to-source, tree/cloud, fixed values, close/reopen cleanup, worker-stop recovery, tab-return capture and retention of an accepted revision after reopening passed. Latest long-page sample: 1,006 passages; local hover-to-panel frame samples under 20 ms. This is a small local sample, not a cross-hardware performance guarantee.
- The first native check read values before capture finished; its readiness assertion now waits for the known fixture values before measuring hover stability. The subsequent native check passed. No behavioral assertion was removed to hide a product failure.
- Connected Chrome 154.0.8037.98: current design preview opened and refreshed to the 1.1 fixture, zero console errors. Light, dark 320px and native panel screenshots were visually inspected.
- Public capture smoke: Datasette Lite article, 93 passages, Simon Willison supplied by page metadata; service-worker TIL, 14 passages, author unknown. Both retain main content and exclude the previously captured subscription/related-link boilerplate. Test-only host permissions are confined to the isolated test copy; no inference was requested. See `evidence/public-testbed-validation.json`.
- ZIP verified byte-for-byte against unpacked non-map assets. `tompathy-0.2.0.zip` has no permanent host permissions.

## Ordinary Chrome installation: one remaining owner action

The actual Chrome Extensions page had Developer mode enabled and no installed extension. The folder chooser is on `E:\EmotiveAutomaton\Projects\ToMpathy\dist`; its empty listing is expected because it shows subfolders rather than files. The Windows UI helper can inspect the native chooser but rejects its controls as stale or belonging to a different window. The owner has been asked to click **Select Folder**. No successful ordinary-Chrome installation or toolbar/OS-shortcut activation is claimed yet. The automated native panel above is a separate verified surface.

Once the card appears, pin ToMpathy, open `http://127.0.0.1:5173/testbed.html`, and click the toolbar icon. Import the first account downloaded from the test page. If reusing a loaded extension after another build, reload its card and refresh the source page.

## Remaining boundaries

- Live Sounding Line transport, authentication, job progress/cancellation/resumption and personal prediction models await a real service contract. Current integration is explicit file exchange. Stage 13 shape compatibility is tested locally; its scientific outputs are not re-evaluated here.
- The public collector still refuses redirects/private literal hosts and requests origin access explicitly. Permission-prompt acceptance in ordinary Chrome remains unverified. DNS aliases are not a browser-enforceable public-network boundary.
- Capturing arbitrary pages is heuristic. Some pages lack metadata, mix authors, or require selected/pasted text. Restricted Chrome pages, PDFs, closed shadow roots and inaccessible frames remain outside automatic DOM capture.
- Profiles and scientific claims are not inferred by this frontend. Synthetic estimates stay labeled; imported accounts are not automatically validated science. Old UUID context IDs require explicit mapping or recollection for Sounding Line's content-bound exporter.

## Resume

`npm run testbed`; optional `npm run chrome`. Validation: `npm test`, `npm run test:browser`, `npm run test:native`, `node scripts/public-testbed-validation.mjs`. Package: `npm run package`, `node scripts/verify-package.mjs`. Source contract: `docs/INPUT_CONTRACT.md`. Browser receipts/screenshots: `evidence/`.
