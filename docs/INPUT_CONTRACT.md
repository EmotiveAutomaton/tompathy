# ToMpathy result contract · 1.0

`src/core/model.ts` is the authoritative runtime validator. `examples/bench-result.json` is a complete valid packet; `bench-revision.json` demonstrates a context-conditioned revision. `bench-source.txt` is the corresponding synthetic text. Fixtures use `tompathy:example` as their portable origin. In the installed extension, use **Import result → Download example format** on the bundled source to obtain a packet bound to that installation's source URL.

## Producing a result

1. Export the current capture from **The source text**.
2. Preserve its `artifact` object, region IDs and anchors in the result. Infer only against this snapshot and explicitly selected context.
3. Supply makers, hypotheses, evidence and the declared scope. Use empty hypothesis/estimate arrays and unknown states when no useful inference is available.
4. Return a packet through result import, or implement `InferenceProvider.analyze(AnalysisRequest)` when Sounding Line has a callable service contract.

No transport endpoint has been invented. `configuredProvider` is null; ordinary text pages remain in the “awaiting an analysis source” state. Hover is entirely local and never invokes inference or retrieval.

## Fields

| Field                             | Meaning                                                                                                                                                   |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemaVersion`                   | Exactly `"1.0"`                                                                                                                                           |
| `id`, `revision`                  | Analysis identity and positive integer revision                                                                                                           |
| `artifact`                        | ID, source, title, capture timestamp, content revision, truncation flag and regions                                                                       |
| `provider`                        | Stable provider ID and method description                                                                                                                 |
| `origin`                          | `synthetic example`, `imported`, or `live provider`; separate from claim status                                                                           |
| `scope`                           | `artifact` or `context`, plus exactly the selected context IDs                                                                                            |
| `makers`                          | Analysis-local IDs, labels, identity status (`unknown`, `supplied`, `synthetic`) and relationship to the artifact                                         |
| `hypotheses`                      | ID, kind (`goal`, `process`, `value`), label, description, maker and region associations, claim status, optional support/alternative set and evidence IDs |
| `alternatives`                    | Explicit member IDs, `competing` or `independent`, and whether exhaustive                                                                                 |
| `process`                         | Process node IDs and explicit directed edges with supplied relationship labels                                                                            |
| `estimates`                       | Region ID, optional contribution value with quantity and 0–1 scale, independent uncertainty level and meaning                                             |
| `evidence`                        | ID, source identity/URL, excerpt, capture time and supplied relationship to the claim                                                                     |
| `revisionOf`, `changeExplanation` | Optional predecessor analysis ID and explanation to review before accepting                                                                               |

Claim status is one of `hypothesis`, `creator-reported`, `observed`, `unknown`. An observation of text is not an observation of intent. Makers are explicitly scoped; the UI lets readers select a maker and never merges identities by name.

Support is optional/null, or an object with `value`, a two-number `scale`, `semantics` (`relative` or `probability`), `meaning`, optional `calibration`, and optional `candidateSet`. A probability requires scale `[0,1]` and a valid candidate set. An exhaustive competing probability set must sum to one. Invalid values, nonfinite numbers, duplicate IDs and dangling references are rejected. Missing support and zero are distinct. Relative support is never labeled as probability. Contribution never determines uncertainty.

Maker-level values are rendered from the whole accepted snapshot. Their membership, order and sizes do not vary with the selected passage. A change in scope hides mismatched estimates; the UI does not reweight them. Replacing an existing packet opens an explicit revision review.

## Text identity and matching

The capture normalizes whitespace (`/\s+/gu` to one space and trim) within each readable semantic block. It joins blocks with two newlines, then computes SHA-256 over UTF-8 text for `revision`. `artifact.id` is the source URL without its fragment. Region IDs are capture-local `p1`, `p2`, and so on.

Each anchor contains exact normalized text, zero-based block `index`, UTF-16 character `start` in the joined snapshot, and up to 80 UTF-16 characters of `prefix` and `suffix`. Unicode is retained. Repeated phrases are distinguished by the full snapshot, index, offsets and neighboring text. Matching requires artifact ID, revision, region IDs, count and every anchor field to agree; it never fuzzy-attaches an unmatched claim.

The page adapter resolves anchors against its captured DOM index. Relevant text/structure, class or visibility-attribute changes invalidate that index. Explicit recapture is required. It captures at most 1,500 blocks / 300,000 normalized characters and declares truncation. Hidden material, navigation, editable regions and password fields are excluded. Inline links retain normal behavior.

## Session contract

`sessionVersion: "1.0"` wraps an artifact, nullable packet, context items and scope. Context items include ID, source, excerpt, retrieval timestamp, lineage (`pasted`, `file`, `public-url`, `synthetic`) and selection state. Imported session items are deselected until the reader chooses them again. Sessions load as detached snapshots; they do not attach claims to a current tab.

## Sounding Line inspection

Read-only inspection used the local `SoundingLine/sounding-line` checkout at commit `9d193b75cb117c999f197ca0319ff946656eba3f`. The reviewed `soundingline/reading_profile.py` separates proximal reconstruction, trajectories, historical claims, contribution hypotheses, observed process and explicit claim boundaries. The Stage 11.1 human viewer similarly keeps forecasts and witnessed facts separate.

These research structures are not a callable browser API and were not silently converted into maker values. The future adapter must preserve those distinctions, carry evidence lineage, map only fields whose semantics actually agree, and leave unavailable estimates unknown. No research outputs were copied, experiments launched, or upstream files edited.

Primary implementation references: [Chrome side panels](https://developer.chrome.com/docs/extensions/reference/api/sidePanel), [activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab), [Playwright extension testing](https://playwright.dev/docs/chrome-extensions).
