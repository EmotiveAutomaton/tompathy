# ToMpathy status

Updated 14 October 2026. Version **0.2.0** is the owner-approved frontend milestone.

## Verified baseline

Package and Chrome versions are aligned at **0.2.0**. The reviewed build is
**2ddebffebb65**, with a new installable `v0.2.0` milestone. Main is the baseline
for the next feature; the completed milestone branch is retired after merge.

- Live demo on the public essay/homepage; other pages accept matching supplied analysis.
- Linked attention, zoomable multi-peak hierarchy, wheel/keyboard reels and source navigation.
- Sentence reading scales, contour-current value categories and three demo perspectives.
- Bounded free linked context, GitHub revisions, timeline and portable reading files.
- No live inference backend or Chrome Web Store submission. Demo confidence and values
  remain explicitly invented. Future model/search/word-level controls remain unfinished.

The next feature awaits the owner's specification; no replacement development
branch has been opened. Follow [the branch workflow](docs/VERSIONING.md).

Review locally with **Review ToMpathy.cmd → Open the live essay → ToMpathy toolbar icon**.
See [development and QA](docs/DEVELOPMENT.md), [release notes](CHANGELOG.md),
[the input contract](docs/INPUT_CONTRACT.md), and [the 0.2 UX review](docs/UX_REVIEW_0.2_DEVELOPMENT.md).
Detailed earlier checks remain in [the development archive](docs/archive/0.2-development.md).

## Validation

- TypeScript/build and **29 core tests passed**.
- **All 51 browser scenarios passed** across the broad run and affected reruns.
  Release validation caught and fixed packing stopping at the first oversized
  attention phrase. Tests now reflect capped clouds, scrollable values, the
  Current work only default and live review links. One cold navigation timed out
  in the broad run and passed unchanged on the targeted rerun.
- Ordinary **Chrome 154.0.8037.98**, actual **360 px native panel**: installation,
  source/panel locks, wheel and keyboard navigation, graph zoom, saved-reading
  import/export, revision retention, normal-page capture and full restart
  restoration passed with **zero panel errors**. No model download was requested.
- The ZIP matches every built file: **2,069,869 bytes**, SHA-256
  `10c6863ead309f678edbb80d945d17562bf32ddc1de1cc0fa9186667582f0732`.
- Pull requests and main updates run the full [CI checks](https://github.com/EmotiveAutomaton/tompathy/actions).
  Source maps, local inputs/profiles and generated evidence are excluded from Git
  and the installable package. Disposable browsers and servers close after checks.

Local receipts: ignored `evidence/review-validation.json` and
`evidence/package-verification.json`. The README screenshot shows the built 0.2
preview with half-width reader, a locked sentence and its evidence card.
