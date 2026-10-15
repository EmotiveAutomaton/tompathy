# ToMpathy result contract · 1.0–1.7

`src/core/model.ts` is the authoritative runtime validator. `examples/lantern-result.json` is a complete valid packet; `lantern-revision.json` demonstrates a context-conditioned revision. `lantern-source.txt` is the corresponding synthetic text. Fixtures use `tompathy:example` as their portable origin. In the installed extension, use **Development tools → Import result → Download example format** on the bundled source to obtain a packet bound to that installation's source URL.

## Producing a result

1. Export the current capture from **Development tools → Source text**.
2. Preserve its `artifact` object, region IDs and anchors in the result. Infer only against this snapshot and explicitly selected context.
3. Supply makers, hypotheses, evidence and the declared scope. Use empty hypothesis/estimate arrays and unknown states when no useful inference is available.
4. Return a packet through import, a configured static registry, or the local companion's `POST /v1/analyze` endpoint.

Provider selection defaults to None. Options accepts an HTTPS registry or a token-authenticated loopback companion. **Analyze capture** is an explicit action in Options. Hover and capture never invoke inference. Responses pass `PacketSchema` and exact artifact/scope matching; changes to evidence abort pending work. Replacing an existing packet uses the retained-revision review flow. The commissioned demo on `abrahamhaskins.org` remains an imported-origin, locally authored packet bound to the live capture. Changed visible text on that demo site automatically recaptures; other sites retain the stale-source gate. See [Privacy](../PRIVACY.md) for each provider's requests and storage.

## Additions in 1.7: engine population comparisons

Version 1.7 retains all earlier fields. The engine brief originally assigned these
additions to 1.5; that version and 1.6 already shipped other reader fields.

- Optional `provider.admissions` lists at most 100 actual contributing module and
  question-battery identifiers. The bounded `provider.method` explains the engine
  version, implementation pin and evidence semantics. Admission availability is
  reported by service health; an unused admission is not a packet contributor.

- A value hypothesis may use `interpretation: "drive"` and an `icon` key:
  `seeking`, `rage`, `fear`, `lust`, `care`, `panic-grief`, `play`, `body`, or `value`.
  Existing `valueCategory` remains available.
- A maker may supply `predictability`, a Support object with relative semantics
  and scale `[0,1]`. It describes consistency of observed choices under a model,
  never certainty about the maker's values.
- Optional `population` has `populationId`, `makersPooled`, a domain/dataset
  `description`, and `items`. Each item refers to a single-maker value hypothesis
  and includes `populationSupport`, `makerRecords`, `shrinkage` (the model's
  estimated share of personal evidence), and `curve: [{records, intervalWidth}]`.
  The comparison uses the same support scale. Curve record counts increase.
  Zero maker records require zero personal share. A model must describe any
  approximation in the support meaning; these numbers are not human authorship
  shares or guarantees about identifiability.

Population references, scales, duplicates and probability candidate sets are
validated. Probability semantics also require named calibration evidence;
exhaustive competing sets sum to one. The initial engine emits relative support.
No population object is required when no admitted population estimate exists.
An observed domain summary may supply an empty `items` array and explicitly state
that no admitted value estimates exist. Maker counts are source-scoped identities,
not a claim that identities across datasets were reconciled.
These fields require 1.7 and do not reinterpret earlier packets or demo values.

The local analysis request may additionally carry `history: "wikipedia"`, only
with artifact scope. This is an explicit network operation enabled separately by
the companion's `--history-dir`. The returned artifact still matches the exact
capture. Default analysis never fetches history. A one-point population curve
represents the supplied prior width at zero records; the reader does not invent
personal narrowing or a future trajectory.

## Fields

| Field                             | Meaning                                                                                                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemaVersion`                   | `"1.0"` (legacy, including Sounding Line Stage 13), `"1.1"`, `"1.2"`, `"1.3"`, `"1.4"`, `"1.5"`, `"1.6"`, or `"1.7"`                                                                   |
| `id`, `revision`                  | Analysis identity and positive integer revision                                                                                                                               |
| `artifact`                        | ID, source, title, capture timestamp, content revision, truncation flag and regions                                                                                           |
| `provider`                        | Stable provider ID and method description                                                                                                                                     |
| `origin`                          | `synthetic example`, `imported`, or `live provider`; separate from claim status                                                                                               |
| `scope`                           | `artifact` or `context`, plus exactly the selected context IDs                                                                                                                |
| `makers`                          | Analysis-local IDs, labels, identity status (`unknown`, `supplied`, `synthetic`) and relationship to the artifact                                                             |
| `hypotheses`                      | ID, kind (`attention` in 1.4, `goal`, `process`, `value`), label, description, maker and region associations, claim status, optional support/alternative set and evidence IDs |
| `alternatives`                    | Explicit member IDs, `competing` or `coexisting`, and whether exhaustive; legacy `independent` remains readable as coexistence without a new independence claim               |
| `process`                         | Process node IDs and explicit directed edges with supplied relationship labels                                                                                                |
| `estimates`                       | Region ID, optional contribution value with quantity and 0–1 scale, independent uncertainty level and meaning                                                                 |
| `evidence`                        | ID, source identity/URL, excerpt, capture time and supplied relationship to the claim                                                                                         |
| `revisionOf`, `changeExplanation` | Optional predecessor analysis ID and explanation to review before accepting                                                                                                   |

Claim status is one of `hypothesis`, `creator-reported`, `observed`, `unknown`. An observation of text is not an observation of intent. Makers are explicitly scoped; the UI lets readers select a maker and never merges identities by name.

Support is optional/null, or an object with `value`, a two-number `scale`, `semantics` (`relative` or `probability`), `meaning`, optional `calibration`, and optional `candidateSet`. A probability requires scale `[0,1]` and a valid candidate set. An exhaustive competing probability set must sum to one. Invalid values, nonfinite numbers, duplicate IDs and dangling references are rejected. Missing support and zero are distinct. Relative support is never labeled as probability. Contribution never determines uncertainty.

Maker-level values are rendered from the whole accepted snapshot. Their membership, order and sizes do not vary with the selected passage. A change in scope hides mismatched estimates; the UI does not reweight them. Replacing an existing packet opens an explicit revision review.

## Additions in 1.1

- `hypotheses[].interpretation`: `governing-purpose` / `local-goal` for goals; `historical-event` / `reader-route` / `repertoire` for processes; `preference` / `value` for the stable list. These are distinct meanings. Missing legacy meanings stay unspecified. Unknown value placeholders do not become a list of repeated asserted values.
- `process.interpretation`: `historical-production`, `functional`, or `unspecified`. Edges can carry `kind` (`precedes`, `enables`, `revises`, `alternative`, `related`, `order-unknown`), claim `status`, and evidence IDs. Only precedes/enables edges form displayed branches; other relations remain explicit cross-links. Shared events are referenced rather than silently dropped. A cycle of explicit `precedes` claims is rejected. Branches do not establish a total chronology. Reader-route and repertoire nodes are not mixed into the historical display.
- `accounts[]`: ID, label, member hypothesis IDs, and explanation. Accounts relate compatible goal/process/preference claims; the frontend does not infer a joint posterior from their individual scores.
- `documentContribution`: nullable value, named quantity, explanation, and evidence IDs. A local contribution can add `basis`, explanation, and evidence IDs. The frontend never adds global and local scores or treats edits as a quantity of thought. Unknown local contribution is unpainted. Page hover titles and source details explain both levels.
- Capture metadata may include explicitly sourced `authors[]` with `basis` and a `capture` method/note. Page metadata is not verified identity. The requested creator is separately editable in Source text and never relabels a loaded packet's maker.

All new evidence/account references are validated. Existing 1.0 packets remain accepted; adding fields does not supply missing historical or scientific warrant.

## Additions in 1.2

`goalHierarchy.nodes[]` is an optional, explicit hierarchy of possible goals. It is separate from `process` production-history edges. The renderer never derives parenthood from historical precedence. Each maker has one root; cycles, dangling IDs, cross-maker parents, paths deeper than 12 nodes and child regions outside the parent are rejected. Large hierarchies have a readable list fallback.

Each node supplies `id`, optional `parentId`, `maker`, `label`, `description`, `level` (`document`, `section`, `paragraph`, `sentence`), nonempty `regions`, and `evidence` IDs. Sentence nodes also require `span: {region, start, end}`: a half-open UTF-16 range inside that region's existing normalized `anchor.exact`. The range must be nonempty and within the region. Region identities, paragraph capture boundaries and capture revisions do not change.

Goal hypotheses can supply `spans[]` with the same range shape to limit visibility to individual sentences within their declared regions. Hypotheses may also supply `decisionNodes[]`, explicit same-maker references into the hierarchy. Core-value hover details use these references to identify particular decisions, alongside the actual page/context evidence. Sources are not treated as additive probability components. Missing support remains unknown; relative support stays explicitly relative.

The frontend segments captured prose into sentence ranges with `Intl.Segmenter`. It maps normalized offsets back to original DOM text nodes and paints CSS Highlights without inserting spans into third-party articles. Single left click locks the current sentence; links, form controls and nonempty native text selections are excluded. A hierarchy click or reel scroll locks that node and highlights its span or full region set. Escape releases it. Word-level analysis is a disabled development marker only.

The native title and three panels are intentionally spare. Analysis subject, synthetic/imported origin, methods, old process claims and full evidence remain available in Reader menu, Help, Source text and All supplied hypotheses.

Layout foundations: [D3 force simulation](https://d3js.org/d3-force/simulation) for gentle position relaxation, with phrase-shaped collision and bounded packing; [D3 hierarchy](https://d3js.org/d3-hierarchy/stratify) for explicit parent/ancestor/descendant relationships. [d3-cloud](https://github.com/jasondavies/d3-cloud) was considered; its fresh spiral placement and possible omission of non-fitting words were a poor fit for persistent goals.

## Additions in 1.3

`goalHierarchy.nodes[].level` becomes optional descriptive metadata (a nonempty string of up to 100 characters when present). Parent links determine hierarchy depth; the interface does not display fixed sentence/paragraph/section/document reel captions. Up to 64 levels are accepted with the existing 3,000-node bound, cycle checks, same-maker references and region-containment validation. A node explicitly labeled `sentence` still requires its exact span. Versions 1.0–1.2 keep their original level vocabulary and 12-level limit.

The compact reels scroll horizontally for deeper paths; each reel supports mouse-wheel and arrow-key selection. Top-nine values are selected by normalized supplied support, with stable input order breaking ties and unknown support last. The full hypothesis list remains available. Versions through 1.3 retain one parent per node and one root per maker. Contract 1.4 adds explicit branching ends below.

## Additions in 1.4

Current attention is an independent supplied stream. `hypotheses[].kind: "attention"` may carry `interpretation: "current-attention"`. It is never populated by filtering goal hypotheses or reading hierarchy nodes. Optional `currentAttention[]` frames have this shape:

```json
{
  "maker": "maker-1",
  "span": { "region": "p4", "start": 0, "end": 20 },
  "items": [
    {
      "hypothesis": "focus-2",
      "support": {
        "value": 0.94,
        "scale": [0, 1],
        "semantics": "relative",
        "meaning": "Supplied relative support, not calibrated probability"
      }
    }
  ]
}
```

Each item references a separate attention hypothesis associated with the same maker and compatible region. Frame ranges use normalized half-open UTF-16 offsets and may divide a sentence. Nonoverlapping frames for the same maker/region, valid references, support scales and probability candidate sets are enforced. An omitted item support inherits that hypothesis's support; explicit null means unknown. Exhaustive probability sets must be complete and sum to one within each frame that uses them. Limits: 3,000 frames, 40 items per frame. The content adapter supplies the pointed character offset; this does not enable the deferred word-level goal analysis.

The cloud is empty with **hover** until a source sentence or hierarchy node is selected. Parent nodes aggregate supplied attention across distinct descendant sentences, weighted by recurrence and confidence; they do not select an arbitrary sentence. A selected position without a supplied frame says **No attention supplied**. Older packets remain valid and do not acquire invented attention. The beta example supplies written sentence frames with shifting leaders, clearly labeled as synthetic in evidence and Help.

Hierarchy nodes may use `parentIds` (1–16 unique IDs) instead of `parentId`. A maker may have multiple roots. Both parent forms together, cycles, cross-maker parents, missing parents and child regions outside **any** parent are rejected. The 64-level/3,000-node bounds remain. No extra relationships are inferred.

The graph view places local leaves at the left; a node's rank follows its longest child path. Every semantic node has one cell. A spanning forest controls geometry, while additional supplied parents remain explicit connector lines during inspection and alternatives in the reels. Selection follows the complete semantic ancestor/descendant neighborhood. Parent choice for placement does not discard an analytical relationship. Dense graphs over 600 nodes use the detail fallback.

Reels remain visible at rest, blurred when unresolved. Locked ambiguous reels expand upward on inspection over the faded hierarchy. Green locks release selection; Escape dismisses the topmost overlay first. Find is available for a locked node with source regions, even with ambiguous reels, and centers the union of highlighted source text. The bundled example supplies separate creator and Global demo values; other packets do not receive invented Global estimates. Search remains a typing-only preview.

## Additions in 1.5 and context timeline records

Contract 1.5 optionally supplies `goalHierarchy.orderUncertainGroups[]`, each containing `id`, `nodes` (2–30 distinct sibling node IDs), `explanation`, and `evidence` IDs. Members must exist, share a maker and at least one explicit parent; evidence references must exist. At most 30 groups are accepted. The renderer places a subtle “Order uncertain” squiggle beside each supplied group. It does not derive chronological uncertainty from hierarchy geometry. Absence of a mark does not assert that order is known. Versions 1.0–1.4 remain accepted without these fields.

Context records optionally add `provenance: {author, basis, linkedFrom}`. Basis is `page-byline`, `explicit-author-link` or `linked-source`. Optional `facts[]` (at most 20 per source) carries `label`, `quote`, `source`, optional `date`, and `dateKind`: `publication`, `event`, `account-created`, `profile-updated`, `source-updated`, or `undated`. Calendar dates retain supplied precision (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`) and must be valid. Dated kinds require a date; undated facts forbid one. `retrievedAt` retains its separate meaning on the source record. These are additive context metadata; canonical context IDs still bind the source URL and excerpt.

The collector reads at most three explicit selected-creator sources, or six total with one-hop discovery enabled. Only the initial source origins are eligible for discovered requests. Successful sources have a 15-minute bounded memory cache. Collected context is initially unselected and never modifies the accepted packet. The timeline and text brief are extractive; neither provides inferred biography, score updates or automatic Sounding Line submission.

Double-clicking anywhere in the active page or reader releases the held selection. Native text selection is not prevented. Expanded reel pointer bounds follow each actual reel window with a small gap allowance, instead of the full expanded bounding rectangle.

## Portable reading files

Options → Export writes `tompathy-reading.html`: a static readable snapshot and one inert JSON payload with `{format:"tompathy-reading", version:1, session}`. The page contains only captured text, basic reading styles and source attribution; it is not a visual archive of the site's original CSS/images or interactive features. The payload includes the exact artifact, accepted packet, context and retained revisions. It loads offline as readable text.

Options → Import accepts this file or a matching provider packet. Reading imports validate the schema, recalculate the page hash and anchors, and validate packet/scope binding. Imported HTML is not executed or inserted into the extension. Chrome opens an extension-owned saved-page tab, whose adapter uses the original validated artifact identity rather than pretending that claims belong to the extension URL. The imported context scope is restored because the user explicitly imported the whole accepted reading. Legacy QA session JSON loading remains a separate detached path and deselects context as before.

The session schema has optional `contextSources` (at most three `{author,url}` links explicitly supplied by page metadata/bylines) and `repositoryLinks` (at most three explicit GitHub repository/file URLs, with exact file links preferred). Repository links belong to the captured page; they do not establish creator identity. Light context fetches matching links with bounded retrieval and narrow host permission. The saved option refreshes on opening a reading using already granted origins. GitHub profile and revision facts retain their date meanings. Revision entries use `source-updated` and quote both Git author and committer timestamps. Results remain unselected until chosen for the next analysis request; collection never mutates accepted scores. There is no web search provider or summarization model in this beta.

## Text identity and matching

The capture normalizes whitespace (`/\s+/gu` to one space and trim) within each readable semantic block. It joins blocks with two newlines, then computes SHA-256 over UTF-8 text for `revision`. `artifact.id` is the source URL without its fragment. Region IDs are capture-local `p1`, `p2`, and so on.

Each anchor contains exact normalized text, zero-based block `index`, UTF-16 character `start` in the joined snapshot, and up to 80 UTF-16 characters of `prefix` and `suffix`. Unicode is retained. Repeated phrases are distinguished by the full snapshot, index, offsets and neighboring text. Matching requires artifact ID, revision, region IDs, count and every anchor field to agree; it never fuzzy-attaches an unmatched claim.

The page adapter resolves anchors against its captured DOM index. Relevant text/structure, class or visibility-attribute changes invalidate that index. Explicit recapture is required. It captures at most 1,500 blocks / 300,000 normalized characters and declares truncation. Hidden material, navigation, editable regions and password fields are excluded. Inline links retain normal behavior.

## Session contract

`sessionVersion: "1.0"` wraps an artifact, nullable packet, context items and scope. Context items include ID, source, excerpt, retrieval timestamp, lineage (`pasted`, `file`, `public-url`, `synthetic`) and selection state. Imported session items are deselected until the reader chooses them again. Sessions load as detached snapshots; they do not attach claims to a current tab.

## Sounding Line inspection

October 11 integration update: the nearby repository now has `runners/stage13/export_tompathy.py`, an offline 1.0 exporter. It is not a live inference endpoint. The frontend preserves that shape, leaves its missing values unknown, and accepts empty process graphs. Newly added/retrieved context IDs use SHA-256 of UTF-8 `JSON.stringify([source, excerpt])`, matching its canonical source/excerpt identity. Legacy UUID context remains readable but needs recollection or an explicit ID mapping before use with that exporter. Synthetic example context uses its fixture ID.

**Export analysis request** writes `requestVersion: "1.0"`, request ID, exact artifact, requested creator (or null), scope with selected context IDs, selected context records only, and accepted packet versions. **Export capture** remains the plain artifact input expected by the offline exporter. No backend jobs are started by either action.

Sessions add optional `authorLabel` and `history` (up to five earlier packets, their context, and retention timestamp). Revision acceptance preserves the preceding account; history inspection does not repaint the page or replace the current account. Clearing the session also clears this history.

The original September inspection is retained below as historical context.

Read-only inspection used the local `SoundingLine/sounding-line` checkout at commit `9d193b75cb117c999f197ca0319ff946656eba3f`. The reviewed `soundingline/reading_profile.py` separates proximal reconstruction, trajectories, historical claims, contribution hypotheses, observed process and explicit claim boundaries. The Stage 11.1 human viewer similarly keeps forecasts and witnessed facts separate.

These research structures are not a callable browser API and were not silently converted into maker values. The future adapter must preserve those distinctions, carry evidence lineage, map only fields whose semantics actually agree, and leave unavailable estimates unknown. No research outputs were copied, experiments launched, or upstream files edited.

Primary implementation references: [Chrome side panels](https://developer.chrome.com/docs/extensions/reference/api/sidePanel), [activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab), [Playwright extension testing](https://playwright.dev/docs/chrome-extensions).

## Creator terminology and compatibility

The interface and context collector use **creator**. Existing packet/session/request fields `authors`, `authorLabel`, `author` and provenance basis `explicit-author-link` retain their serialized spelling so saved readings and backend producers remain compatible. Standard HTML `author` metadata, `rel=author` links and schema.org `author` fields are still read as specified by their publishers. No schema version changed for this vocabulary update. Source quotations are not rewritten.

Exporting after a context selection changes stores the previous, now mismatched account in reading history and leaves the active packet empty. The requested context stays selected. Reimport therefore preserves the page, prior account and pending selection without presenting outdated estimates as current.

## Additions in 1.6: sentence reading treatment

`ghostReadings[]` is optional and independent of contribution estimates, current attention and the goal hierarchy. Each record contains `maker`, a normalized half-open UTF-16 `span` (`region`, `start`, `end`), `kind` (`original`, `edited`, `curated`, `ghost`, or `unknown`), nullable `confidence` from 0 to 1, `explanation`, `confidenceExplanation`, evidence IDs, and an optional exact `prompt`. Supply complete sentence spans in this release; partial or word spans are reserved for later work. Records for a creator cannot overlap. Creator, complete sentence boundaries, region, bounds and evidence references are validated. Legacy packets remain readable without this field; contribution scores never become Ghost classifications by inference.

The first visual axis follows the [Ghost Scale essay](https://abrahamhaskins.org/art/): original ink, nominal 95% opacity for light edits, nominal 60% for curated text, reversed colours for unreviewed generation. Ink is composited against the actual solid page surface; curator and edited ink are raised to at least WCAG 4.5:1 where needed. A solid backplate prevents images and translucent site layers from undermining that calculation. The second axis uses Roboto Serif’s GRAD axis from -50 to 100 at fixed weight, width and optical size. Unknown confidence uses grade zero. This is confidence in the classification, not a percentage of human thought, factual reliability, or necessarily a calibrated probability. The supplied explanation must describe its meaning.

Original bold emphasis becomes underline within classified text. Captures may retain `regions[].emphasis[]` with normalized `start`/`end` ranges; saved readings preserve these without retaining executable page markup. The native adapter wraps text nodes, preserves existing elements and links, restores its changes when cleared, and invalidates annotations on content changes. Supplied prompts appear only in the sentence evidence tooltip, beneath its evidence; they are not appended to the article. Word-level painting is not enabled.

Native sentence evidence lives in an isolated-world WeakMap. Tooltip and prompt text renders inside closed shadow roots, and remains available to the accessibility tree. The website can observe the styling but does not receive the detailed record in data attributes.

Sentence evidence cards show a large sample combining involvement ink and confidence grade, with separately labelled involvement and classification confidence. They display at most the first three distinct resolved evidence excerpts, in provider order; producers should rank these by explanatory usefulness. Missing evidence remains explicit. No decision-share percentage is manufactured from ink opacity or confidence. The bundled example includes draft-record and contextual evidence for this demonstration.


### Additive display fields in the 1.6 development contract

`ghostReadings[].evidenceDirections` optionally supplies `{id, direction}` records for evidence IDs already listed on that reading. Direction is `more`, `less`, or `neutral`; duplicate or dangling IDs are rejected. Arrows refer to creator involvement, not classification confidence or factual accuracy. Omitted directions remain neutral; the renderer does not guess them from the Ghost category. Up to three distinct evidence excerpts remain visible, in supplied order.

`hypotheses[].preferenceTrace` optionally supplies a preference-domain label, start/end labels, 2–30 normalized curve points (`x`, `y`, `uncertainty`), and 1–6 observations. Each observation has `date`, `label`, `explanation`, normalized `from`/`to` coordinate pairs, `cost` from 0 to 1 and a textual `horizon`. Coordinates are drawing inputs, not calibrated utilities or discount rates. An observation row matches its numbered chart vector. The existing hypothesis support drives the confidence pie separately. Older packets retain the ordinary description/source card and remain valid. These optional fields survive export/import; no producer must supply them.

The legacy fictional fixture has creator scores from 10% to 22% and Global scores from 81% to 94%. Four labels overlap and four are additional. The commissioned website demo has its own categorized Creator/Global fixtures. Both providers use authored illustrations; unrelated imported/live analyses never receive fabricated Global values. Historical demo observations do not claim to be research findings.

Before styling known sentence readings, the native adapter resets existing CSS opacity on wholly annotated, text-only subtrees and applies opaque wrapper styling. It preserves and restores original inline values and priorities; subsequent site edits take precedence during cleanup. Ancestors shared with unannotated text, controls or media retain their opacity to avoid changing unrelated content. Whole-page compositing filters and overlays are not normalized; they can still affect the displayed result. Element opacity cannot be canceled by a child’s opacity. The color calculation itself still handles ordinary alpha-color input and produces contrast-aware ink against a solid surface.

## Optional website-demo metadata (1.6-compatible)

- A region may include `pageHint`: `heading` (1–6), `section` (string), and `involvement` (a Ghost Scale kind). These preserve source structure and creator-disclosed markings; they are not independent assessments. Existing producers may omit them.
- A hypothesis may include `valueCategory: "drive" | "constructed"`. The UI uses a category icon while confidence remains in support/label weight and the detail card. Older uncategorized value packets keep their confidence icon.
- `tompathy-art-demo` and `tompathy-website-demo` identify commissioned fixtures. The method records authored versus provisional sentence counts and explicitly identifies invented confidence and trajectories. They do not authorize inference or retrieval on unrelated domains.
- Every demo sentence binds to the current capture’s exact region/start/end span. Normalized corpus matching selects a handwritten interpretation; it never changes the current source anchor or relaxes imported-packet validation.
- Tier widths are view state, independent of hierarchy ownership and semantic depth. Dragging a separator changes adjacent widths without changing graph relationships.

The prototype’s seven drive labels follow [Panksepp’s primary-process systems](https://doi.org/10.1371/journal.pone.0021236). Generated higher-order entries are inspired by [Barrett’s theory of constructed emotion](https://pmc.ncbi.nlm.nih.gov/articles/PMC5390700/). These theories are distinct; placing them in this interface is a product hypothesis, not an established combined taxonomy or a measured personality assessment.


## Reading units and demo perspectives (development)

A captured region may supply `pageHint.unit: "group"` to declare its entire
normalized `anchor.exact` as one reading unit. This is used for the commissioned
website's References & Assets footer. Without this marker, prose still uses
`Intl.Segmenter` sentence boundaries. Graph spans, annotations, attention
aggregation, saved-reading previews and Ghost Scale validation share the same
unit boundaries; a grouped block must be covered in full. This optional capture
metadata does not relax ordinary sentence validation. Transient tooltip/popover
contents are excluded from capture.

The website's Current work only, Creator and Global perspectives are local demo
projections. Current work only uses its own authored data; other imported packets
only show values explicitly bound to regions in that work. There is no new
inference endpoint or invented global dataset for arbitrary imported packets.
PANIC/GRIEF uses the display name Belonging in the website fixture; imported
labels are preserved. Confidence remains distinct from preference strength.

Attention ranking retains confidence-weighted recurrence across the selected
units. The cloud presents the highest-ranked prefix that fits its measured space
(up to 18 phrases), without changing those scores or deleting packet hypotheses.
