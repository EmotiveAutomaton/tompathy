# ToMpathy result contract · 1.0, 1.1 and 1.2

`src/core/model.ts` is the authoritative runtime validator. `examples/bench-result.json` is a complete valid packet; `bench-revision.json` demonstrates a context-conditioned revision. `bench-source.txt` is the corresponding synthetic text. Fixtures use `tompathy:example` as their portable origin. In the installed extension, use **Import result → Download example format** on the bundled source to obtain a packet bound to that installation's source URL.

## Producing a result

1. Export the current capture from **The source text**.
2. Preserve its `artifact` object, region IDs and anchors in the result. Infer only against this snapshot and explicitly selected context.
3. Supply makers, hypotheses, evidence and the declared scope. Use empty hypothesis/estimate arrays and unknown states when no useful inference is available.
4. Return a packet through result import, or implement `InferenceProvider.analyze(AnalysisRequest)` when Sounding Line has a callable service contract.

No transport endpoint has been invented. `configuredProvider` is null; ordinary text pages remain in the “awaiting an analysis source” state. Hover is entirely local and never invokes inference or retrieval.

## Fields

| Field                             | Meaning                                                                                                                                                         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemaVersion`                   | `"1.0"` (legacy, including Sounding Line Stage 13) `"1.1"`, or `"1.2"`                                                                                                   |
| `id`, `revision`                  | Analysis identity and positive integer revision                                                                                                                 |
| `artifact`                        | ID, source, title, capture timestamp, content revision, truncation flag and regions                                                                             |
| `provider`                        | Stable provider ID and method description                                                                                                                       |
| `origin`                          | `synthetic example`, `imported`, or `live provider`; separate from claim status                                                                                 |
| `scope`                           | `artifact` or `context`, plus exactly the selected context IDs                                                                                                  |
| `makers`                          | Analysis-local IDs, labels, identity status (`unknown`, `supplied`, `synthetic`) and relationship to the artifact                                               |
| `hypotheses`                      | ID, kind (`goal`, `process`, `value`), label, description, maker and region associations, claim status, optional support/alternative set and evidence IDs       |
| `alternatives`                    | Explicit member IDs, `competing` or `coexisting`, and whether exhaustive; legacy `independent` remains readable as coexistence without a new independence claim |
| `process`                         | Process node IDs and explicit directed edges with supplied relationship labels                                                                                  |
| `estimates`                       | Region ID, optional contribution value with quantity and 0–1 scale, independent uncertainty level and meaning                                                   |
| `evidence`                        | ID, source identity/URL, excerpt, capture time and supplied relationship to the claim                                                                           |
| `revisionOf`, `changeExplanation` | Optional predecessor analysis ID and explanation to review before accepting                                                                                     |

Claim status is one of `hypothesis`, `creator-reported`, `observed`, `unknown`. An observation of text is not an observation of intent. Makers are explicitly scoped; the UI lets readers select a maker and never merges identities by name.

Support is optional/null, or an object with `value`, a two-number `scale`, `semantics` (`relative` or `probability`), `meaning`, optional `calibration`, and optional `candidateSet`. A probability requires scale `[0,1]` and a valid candidate set. An exhaustive competing probability set must sum to one. Invalid values, nonfinite numbers, duplicate IDs and dangling references are rejected. Missing support and zero are distinct. Relative support is never labeled as probability. Contribution never determines uncertainty.

Maker-level values are rendered from the whole accepted snapshot. Their membership, order and sizes do not vary with the selected passage. A change in scope hides mismatched estimates; the UI does not reweight them. Replacing an existing packet opens an explicit revision review.

## Additions in 1.1

- `hypotheses[].interpretation`: `governing-purpose` / `local-goal` for goals; `historical-event` / `reader-route` / `repertoire` for processes; `preference` / `value` for the stable list. These are distinct meanings. Missing legacy meanings stay unspecified. Unknown value placeholders do not become a list of repeated asserted values.
- `process.interpretation`: `historical-production`, `functional`, or `unspecified`. Edges can carry `kind` (`precedes`, `enables`, `revises`, `alternative`, `related`, `order-unknown`), claim `status`, and evidence IDs. Only precedes/enables edges form displayed branches; other relations remain explicit cross-links. Shared events are referenced rather than silently dropped. A cycle of explicit `precedes` claims is rejected. Branches do not establish a total chronology. Reader-route and repertoire nodes are not mixed into the historical display.
- `accounts[]`: ID, label, member hypothesis IDs, and explanation. Accounts relate compatible goal/process/preference claims; the frontend does not infer a joint posterior from their individual scores.
- `documentContribution`: nullable value, named quantity, explanation, and evidence IDs. A local contribution can add `basis`, explanation, and evidence IDs. The frontend never adds global and local scores or treats edits as a quantity of thought. Unknown local contribution is unpainted. Page hover titles and source details explain both levels.
- Capture metadata may include explicitly sourced `authors[]` with `basis` and a `capture` method/note. Page metadata is not verified identity. The requested author is separately editable in Source text and never relabels a loaded packet's maker.

All new evidence/account references are validated. Existing 1.0 packets remain accepted; adding fields does not supply missing historical or scientific warrant.

## Additions in 1.2

`goalHierarchy.nodes[]` is an optional, explicit hierarchy of possible goals. It is separate from `process` production-history edges. The renderer never derives parenthood from historical precedence. Each maker has one root; cycles, dangling IDs, cross-maker parents, paths deeper than 12 nodes and child regions outside the parent are rejected. Large/deep hierarchies have a readable list fallback.

Each node supplies `id`, optional `parentId`, `maker`, `label`, `description`, `level` (`document`, `section`, `paragraph`, `sentence`), nonempty `regions`, and `evidence` IDs. Sentence nodes also require `span: {region, start, end}`: a half-open UTF-16 range inside that region's existing normalized `anchor.exact`. The range must be nonempty and within the region. Region identities, paragraph capture boundaries and capture revisions do not change.

Goal hypotheses can supply `spans[]` with the same range shape to limit visibility to individual sentences within their declared regions. Hypotheses may also supply `decisionNodes[]`, explicit same-maker references into the hierarchy. Core-value hover details use these references to identify particular decisions, alongside the actual page/context evidence. Sources are not treated as additive probability components. Missing support remains unknown; relative support stays explicitly relative.

The frontend segments captured prose into sentence ranges with `Intl.Segmenter`. It maps normalized offsets back to original DOM text nodes and paints CSS Highlights without inserting spans into third-party articles. Double-click locks the current sentence; it does not suppress native text selection. Word-level analysis is a disabled development marker only.

The native title and three panels are intentionally spare. Analysis subject, synthetic/imported origin, methods, old process claims and full evidence remain available in Reader menu, Help, Source text and All supplied hypotheses.

Layout foundations: [D3 force simulation](https://d3js.org/d3-force/simulation) for gentle position relaxation, with phrase-shaped collision and bounded packing; [D3 hierarchy](https://d3js.org/d3-hierarchy/stratify) for explicit parent/ancestor/descendant relationships. [d3-cloud](https://github.com/jasondavies/d3-cloud) was considered; its fresh spiral placement and possible omission of non-fitting words were a poor fit for persistent goals.

## Text identity and matching

The capture normalizes whitespace (`/\s+/gu` to one space and trim) within each readable semantic block. It joins blocks with two newlines, then computes SHA-256 over UTF-8 text for `revision`. `artifact.id` is the source URL without its fragment. Region IDs are capture-local `p1`, `p2`, and so on.

Each anchor contains exact normalized text, zero-based block `index`, UTF-16 character `start` in the joined snapshot, and up to 80 UTF-16 characters of `prefix` and `suffix`. Unicode is retained. Repeated phrases are distinguished by the full snapshot, index, offsets and neighboring text. Matching requires artifact ID, revision, region IDs, count and every anchor field to agree; it never fuzzy-attaches an unmatched claim.

The page adapter resolves anchors against its captured DOM index. Relevant text/structure, class or visibility-attribute changes invalidate that index. Explicit recapture is required. It captures at most 1,500 blocks / 300,000 normalized characters and declares truncation. Hidden material, navigation, editable regions and password fields are excluded. Inline links retain normal behavior.

## Session contract

`sessionVersion: "1.0"` wraps an artifact, nullable packet, context items and scope. Context items include ID, source, excerpt, retrieval timestamp, lineage (`pasted`, `file`, `public-url`, `synthetic`) and selection state. Imported session items are deselected until the reader chooses them again. Sessions load as detached snapshots; they do not attach claims to a current tab.

## Sounding Line inspection

October 11 integration update: the nearby repository now has `runners/stage13/export_tompathy.py`, an offline 1.0 exporter. It is not a live inference endpoint. The frontend preserves that shape, leaves its missing values unknown, and accepts empty process graphs. Newly added/retrieved context IDs use SHA-256 of UTF-8 `JSON.stringify([source, excerpt])`, matching its canonical source/excerpt identity. Legacy UUID context remains readable but needs recollection or an explicit ID mapping before use with that exporter. Synthetic example context uses its fixture ID.

**Export analysis request** writes `requestVersion: "1.0"`, request ID, exact artifact, requested author (or null), scope with selected context IDs, selected context records only, and accepted packet versions. **Export capture** remains the plain artifact input expected by the offline exporter. No backend jobs are started by either action.

Sessions add optional `authorLabel` and `history` (up to five earlier packets, their context, and retention timestamp). Revision acceptance preserves the preceding account; history inspection does not repaint the page or replace the current account. Clearing the session also clears this history.

The original September inspection is retained below as historical context.

Read-only inspection used the local `SoundingLine/sounding-line` checkout at commit `9d193b75cb117c999f197ca0319ff946656eba3f`. The reviewed `soundingline/reading_profile.py` separates proximal reconstruction, trajectories, historical claims, contribution hypotheses, observed process and explicit claim boundaries. The Stage 11.1 human viewer similarly keeps forecasts and witnessed facts separate.

These research structures are not a callable browser API and were not silently converted into maker values. The future adapter must preserve those distinctions, carry evidence lineage, map only fields whose semantics actually agree, and leave unavailable estimates unknown. No research outputs were copied, experiments launched, or upstream files edited.

Primary implementation references: [Chrome side panels](https://developer.chrome.com/docs/extensions/reference/api/sidePanel), [activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab), [Playwright extension testing](https://playwright.dev/docs/chrome-extensions).
