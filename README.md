# ToMpathy · Maker Reader

A Chrome side-panel extension for exploring possible goals, processes, and values behind a text. Sounding Line will supply the inference; this frontend already supports capture, imported results, evidence, context, and a complete synthetic example.

The reader has three quiet sections: a goal word cloud, a process tree that expands into a word cloud, and a stable values list. Select a word or node for evidence. The **⋯ Reader menu** holds source, context, imports, list view, maker selection, and settings. Context checkboxes and analysis scope live together in **Context**.

Private repository: [EmotiveAutomaton/tompathy](https://github.com/EmotiveAutomaton/tompathy).

![Reader preview](evidence/preview-light.png)

## Try it

From a fresh clone, run `npm ci` and `npm run build` first to create `dist/`.

1. Open `chrome://extensions` in Chrome 116 or later and enable Developer mode.
2. Choose **Load unpacked** and select this project's `dist` folder. Alternatively, unzip `tompathy-0.1.0.zip` into a folder and load that folder.
3. Pin **ToMpathy** from Chrome's extensions menu. Click its toolbar icon on an ordinary text page.
4. Choose **Explore an example** for the complete experience. It opens the matching fictional source. If needed, use its **Open Maker Reader** button.

Hover a passage to preview its hypotheses; click to pin; Escape releases. Use **Reader menu → Source text** for keyboard passage navigation, or select text on the page. Select a hypothesis to inspect its evidence and jump back to a passage. Values stay fixed for the analysis revision. In **Reader menu → Context**, preview and explicitly accept the example notebook revision to see a change of mind.

Chrome controls side-panel placement. For the intended right-hand layout, choose the right side in Chrome's **Settings → Appearance → Side panel**. The extension respects the existing setting.

The native panel was tested in Chrome for Testing 153.0.8010.12. The connected Chrome workspace (153.0.8010.49) was used for additional visual and interaction checks. Direct toolbar clicking remains a manual verification item; the native panel itself and its linked example were exercised through the example's button.

## Develop

Node 22.14.0 and npm 10.9.2 were used. Install the exact lockfile dependencies:

```sh
npm ci
npx playwright install chromium
npm run dev
```

Open `http://127.0.0.1:5173/` for the page-and-reader preview, or `http://127.0.0.1:5173/?panel` for the panel alone. The web preview is a design/testing surface; page capture and origin permissions belong to the installed extension.

```sh
npm run build
npm test
npm run test:browser
node scripts/native-validation.mjs
node scripts/live-validation.mjs
npm run package
node scripts/verify-package.mjs
```

`build` typechecks and bundles a self-contained `dist/`; no server is needed by the installed extension. `package` creates the development ZIP. Reload the extension in Chrome after rebuilding. Native validation uses an isolated headed profile and localhost CDP port 9334. Live validation contacts three public sources. Neither uses your personal Chrome profile. Ordinary-page tests add narrow fixture/source permissions to copies under `.local/`; the delivered manifest has no permanent page host permissions.

## Inputs, context, and storage

- **Bundled example:** fictional text, maker, scores, and evidence. It is always labeled synthetic and opens its own source.
- **Result import:** versioned JSON, validated and matched to the exact captured artifact, revision, anchors, and selected context. Export a capture from **The source text** for a provider. See [the input contract](docs/INPUT_CONTRACT.md) and [example packet](examples/bench-result.json).
- **Provider:** replaceable TypeScript interface in `src/core/provider.ts`; no live endpoint or credentials are configured.

Context collection is explicit: at most three HTTPS URLs, one retrieval each, 256 KB per response, a 30-second total deadline, cancellation, no redirects or crawl, and no credentials. Text/Markdown attachments and pasted excerpts work offline. Retrieved items start unselected. Added context never manufactures updated estimates: a matching analysis revision is required.

Preferences persist locally. Captures and context use `chrome.storage.session`, not browsing-history or maker-profile storage. **Save session** exports JSON only when requested; loading it creates a detached snapshot and deselects imported context. **Clear session** removes the reading and page marks. Browser-session data disappears when Chrome clears the extension session.

## Project map

| Location                                          | Responsibility                                                                    |
| ------------------------------------------------- | --------------------------------------------------------------------------------- |
| `src/App.tsx`, `src/reader.css`, `src/styles.css` | Reader, source preview, dialogs, themes, keyboard interaction                     |
| `src/content.ts`                                  | Bounded text extraction, anchors, local pointer selection, page marks and cleanup |
| `src/browser.ts`, `src/background.ts`             | Chrome boundary, side panel, session/preferences storage                          |
| `src/core/model.ts`                               | Versioned runtime schemas and artifact/scope matching                             |
| `src/core/provider.ts`                            | Future inference adapter interface                                                |
| `src/core/collector.ts`                           | Bounded public-context retrieval                                                  |
| `src/core/example.ts`, `examples/`                | Synthetic artifact, ambiguity, unknown history and explicit correction            |
| `tests/`, `scripts/*validation.mjs`, `evidence/`  | Repeatable checks and measured receipts                                           |

See [STATUS.md](STATUS.md) for verification and remaining limitations. The original [project context](TOMPATHY_PROJECT_CONTEXT.md) remains the intent source.
