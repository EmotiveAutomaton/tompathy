# ToMpathy

![Development preview with a half-width reader: locked sentence, evidence tooltip, attention, hierarchy and core values](docs/assets/reader.png)

**What’s on the creator’s mind?** ToMpathy is a Chrome side-panel reader for exploring a creator’s current attention, expertise, habits, process and core values alongside a text.

**0.1 beta · MIT licensed · frontend preview.** The bundled example is fictional and hand-written. A live Sounding Line backend is not connected. Ordinary pages can be captured and paired with a matching imported analysis; the extension does not generate claims about their creators on its own.

This branch is **0.2 development** (`0.2.0-dev.2`; Chrome build `0.1.2`). The public 0.1 beta download below remains the earlier snapshot. See [our branch and version workflow](docs/VERSIONING.md).

## Try the beta

1. Download [tompathy-0.1.0.zip](https://github.com/EmotiveAutomaton/tompathy/releases/download/v0.1.0-beta.1/tompathy-0.1.0.zip) from the [beta release](https://github.com/EmotiveAutomaton/tompathy/releases).
2. Extract it into a folder you will keep. In Chrome, open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the extracted folder containing `manifest.json`.
3. Open an article and click **ToMpathy** in Chrome’s extension menu. For the demonstration, open **⋯ Options → How ToMpathy works → Open the example**, then **Open Maker Reader**.
4. Hover a sentence; click to hold it. Move across the hierarchy or hover the reels to inspect possibilities. Click the green lock to release.

No account, API key, paid service or model download is needed for the example, reading-file import/export, or linked-source context. This beta is distributed through GitHub; it is not yet listed in the Chrome Web Store. Unpacked installations update manually: replace the files and click **Reload** on the extension card.

## Three views, one reading

- **Current attention** is an independent, animated word cloud. It follows the pointed sentence or supplied sub-sentence frame; word size reflects the supplied support. It retains the last inspected frame between targets; broader graph nodes combine their constituent attention frames.
- **Expertise and habit (previous attention)** shows local choices flowing toward broader goals. Wheel to zoom, drag to pan, and use the corner-bracket button to fit the whole hierarchy. Cell-anchored goal labels fade in together as the graph grows. Hold a node and hover the odometer: ambiguous reels grow upward into selectable lists over the faded hierarchy. The arrow/magnifier below the lock centers highlighted text in the article, including groups with ambiguous reels.
- **Core values** shows a stable set of supplied latent-preference hypotheses. The demo contrasts low-confidence creator values with a higher-confidence Global set. Hover or select a value for a preferred-state curve, uncertainty band, and individually explained observation vectors.

The development reading, **The door we stopped explaining**, follows a fictional cooperative-game designer. Sentence ink shows supplied Ghost Scale involvement; font grade independently shows confidence in that classification. Original bold becomes underline. Pause over a sentence for its evidence and open **Options → View context and timeline** for the fictional draft record. These are authored demonstration judgments, not live inference. The Latin reading font is bundled locally (about 53 KB); it adds no font-service requests.

The reader supports keyboard focus, reduced motion, system/light/dark themes, multiple supplied creators, and retained analysis revisions. Estimates are hypotheses, not verified access to a person’s mind or calibrated probabilities unless the input explicitly says so.

## Context and saved readings

In this development branch, **Light context** records the byline and follows up to three explicit creator links. The setting persists: opening a reading refreshes context where Chrome already grants source access. **Use GitHub when possible** reads linked public profiles and an explicitly linked repository or source file, with up to three recent revisions and small change excerpts. **Agent search** adds one bounded hop of linked pages and feeds: at most six sources, including one repository lookup. It uses no account, model or paid search. Compact progress bars beside Options become a checkmark and fade. **View context and timeline** opens dated source entries, undated facts, retrieval coverage and an exportable brief. Sources remain available for selection into the next backend request; fetching context does not invent new scores. See [implementation and limits](docs/CONTEXT_RESEARCH.md).

Click a hierarchy cell to lock it and gently center its source text. Up/down arrows move between nearby cells; left/right moves between subordinate and broader goals. Scrolling away reveals Find. The Review desk also includes four generated head-and-teardrop logo studies, their prompts and small-icon previews; the production icon is unchanged.

**Export** saves one HTML reading containing captured text, analysis and context. **Import** restores its text beside the reader. The file also opens offline as plain text with reading styles; original site images, CSS and active features are not archived.

Read the [current UX review and next priorities](docs/UX_REVIEW_0.2_DEVELOPMENT.md).

See [Privacy](PRIVACY.md) for storage, network behavior and permissions.

## Develop and verify

Node 22.14+ and current Google Chrome:

```sh
npm ci
npm run review
```

The launcher builds the extension and opens a persistent, separate Chrome review profile. Its small dashboard links to the testing environment and twelve copyable image-generation prompts in contrasting visual styles. On Windows, **Review ToMpathy.cmd** provides the same entry point. It leaves normal Chrome profiles alone. For the design preview, run `npm run dev` and open `http://127.0.0.1:5173/`.

```sh
npm run build
npm test
npx playwright install chromium
npm run test:browser
npm run test:review
npm run package
node scripts/verify-package.mjs
```

[CI](https://github.com/EmotiveAutomaton/tompathy/actions) checks the reader, real extension integration, ordinary Chrome installation and restart recovery, then packages the tested build. Generated browser evidence stays in CI artifacts and local ignored folders.

[Development and QA](docs/DEVELOPMENT.md) · [Result contract](docs/INPUT_CONTRACT.md) · [Distribution plan](docs/DISTRIBUTION.md) · [Release notes](CHANGELOG.md)

## License

[MIT](LICENSE), copyright 2026 EmotiveAutomaton. Bundled dependencies retain their own [notices](THIRD_PARTY_NOTICES.txt).
