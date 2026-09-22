# ToMpathy status · 2026-09-21

Frontend v1 implemented and packaged for local exploration. The owner's September 21 refinement supersedes the earlier, denser presentation: three elegant sections and less visible machinery. The original commission remains `TOMPATHY_PROJECT_CONTEXT.md`.

## Decisions

- React/TypeScript, an esbuild extension bundle and Vite preview; Chrome MV3 native side panel, minimum Chrome 116.
- Goal word cloud; process tree with an expand-to-cloud toggle; refined, stable values list. Thin rules and typography define the regions. The process scrolls independently so goals and values remain available. Source, context, imports, maker selection, list-view checkbox and settings sit behind one menu. Evidence opens on selection. Context selection checkboxes and scope are together in their dialog.
- Restrained warm surfaces, green/amber accents, system/light/dark themes. Source text and reader are visually distinct. Missing support remains neutral. Relationship and alternative-account details are available with the evidence.
- Private GitHub repository: https://github.com/EmotiveAutomaton/tompathy. Build output, browser profiles, logs and dependency directories are excluded from Git.
- Exact capture/anchor matching; stale results are withheld. No arbitrary-page example claims or frontend-generated psychological estimates.
- Sounding Line is locally available and was inspected read-only. Its current research output is not a browser-service contract. A typed adapter boundary is ready; no live endpoint is configured.
- Session-local captured content, explicit exports, individually selected context, and explicit analysis revision acceptance.

## Verification so far

- Build/typecheck and 8 core contract/collector checks pass, including a real 30-second deadline with an unresponsive controlled fetch.
- 7 browser flows pass: linked interaction; stable values; evidence; scope/revision; malformed import; paste/empty state; theme/reduced motion/narrow panel; session/file-context save/load/clear; cancellation; 200% zoom; real content adapter, duplicate/Unicode/inline text, mutation, cleanup and long page.
- Actual native panel opened through the bundled example's **Open Maker Reader** action, in an isolated Chrome for Testing 153.0.8010.12 profile. Native page-to-panel hover, pin/Escape, evidence and panel-to-source links passed. `evidence/native-validation.json` records the source viewport narrowing and distinct native panel target.
- Programmatic native-panel closing removed injected marks; reopening restored the matching example. Stopping the isolated extension service worker preserved the reader's local interaction. Returning from a different tab allowed fresh recapture.
- Connected Chrome workspace 153.0.8010.49: revised tree/cloud switch, passage pin, evidence-to-source navigation, list-view checkbox and stable values exercised; light and narrow dark layouts visually inspected. No console errors in the final preview check.
- Public page captures: Example Domain (2 passages), W3C “Cool URIs don't change” (82), Wikipedia “Bench (furniture)” (54). Real bounded retrieval and HTTP 404 handling passed with no fabricated inference. See `evidence/live-validation.json`.
- Long-page receipts: `evidence/performance.json` and `evidence/native-validation.json` contain the latest measurements on 1,006 passages. These are small local samples, not a cross-hardware or compositor-present guarantee. No inference or retrieval occurs during hover.
- The page adapter bundle is approximately 10 KB, with runtime schema validation confined to the reader. `evidence/package-verification.json` records the packaged extension size and checksum.
- One first-run adapter test timed out while waiting for a browser animation frame during a click. The unchanged test passed on its isolated rerun and the subsequent complete seven-test run. No assertions were relaxed.

## Known limits / remaining verification

- Direct **toolbar click** and OS shortcut activation are not yet verified. The Windows helper twice rejected the returned Chrome for Testing handle with “window id … no longer belongs to Chrome; current owner is Chrome.” DOM-level shortcut injection did not grant activeTab. Native opening through the example's real button is verified; this is a distinct claim.
- Origin-permission prompt acceptance was not automated. Live smoke tests use isolated copies with explicitly scoped test host permissions; the delivered manifest retains activeTab and optional per-origin access only.
- Public-source validation rejects HTTP, credentials, custom ports, IP literals and local naming zones; redirects and credentialed requests are refused. A DNS alias or managed split-horizon DNS can still resolve an otherwise public-looking hostname privately. A browser-only frontend cannot pin the resolved connection IP through Fetch. Do not treat this collector as a general SSRF-resistant proxy; a future public-only relay would need an explicit service contract.
- Protected browser pages, closed shadow roots, non-top-level frames, canvas/PDF text and inaccessible surfaces use paste/import fallbacks. Scope is ordinary DOM text, not universal media.
- Semantic capture is conservative. For example, Wikipedia notices can appear in its source preview. The reader should inspect captures and use paste when a page mixes authors or non-artifact material.
- A 200% CSS-zoom visual check exposed an offscreen dialog header. Dialog sizing now accounts for viewport and zoom; the regression asserts the close control and full dialog bounds are on screen. Reduced-motion, 320px and long-page checks are included. No scientific validity is claimed for synthetic scores.

## Resume

`npm run build`, `npm test`, `npm run test:browser`, `node scripts/native-validation.mjs`, then `npm run package`. Development preview: `npm run dev` at `http://127.0.0.1:5173/`. The deliverables are the private repository, local `dist/`, `tompathy-0.1.0.zip`, README, the input contract, example packets and evidence screenshots.
