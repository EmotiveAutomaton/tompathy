# ToMpathy status · 0.2 development

Updated 11 October 2026, Pacific time.

Work is on `codex/0.2-development`. npm version: `0.2.0-dev.1`; Chrome numeric version: `0.1.1`; display: **0.2 development 1**. The published `v0.1.0-beta.1` release and main baseline remain unchanged. This is the first iteration toward the complete frontend, not completion of 0.2. [Workflow and milestone criteria](docs/VERSIONING.md).

## This iteration

- Simplified three-column teardrop icon: list, two middle blocks, one soft tip.
- Direct node selection and its reels stay on the pointed visual branch. Page selection retains all supplied alternatives. Shorter branches fade the unused final reel.
- Accurate intersections at the rounded back remove clipped wedges. Two explicit sibling groups in the example show “Order uncertain” squiggles; absence of a squiggle does not assert known order.
- Expanded reels close outside their actual boxes, with a small allowance between neighboring boxes. Scrollbars stay hidden during expansion. Double-clicking either the page or reader releases selection.
- Light context captures the page byline and up to three explicit author sources. Agent search now enables one-hop discovery of linked pages/feeds on the same granted origins, at most six total sources. No model, paid provider or API key is required.
- Source-backed timeline, separate date kinds, undated facts, source excerpts, coverage, brief export and a 15-minute bounded memory cache. New context stays unselected until requested for a new analysis. Packet contract 1.5 adds optional order-uncertainty groups; 1.0–1.4 remain readable.

## Verification

Extension build **5792975216bb**:

- 22/22 core tests passed: contracts, source identity, calendar dates, branch geometry, cache expiry, cancellation and revision handling.
- 19/19 browser tests passed: bounded timeline discovery/coverage/export, inert feed/HTML parsing, precise hover boundaries, branch selection, both lock surfaces, narrow/dark layouts, import/export, keyboard and installed page-adapter behavior.
- Ordinary Google Chrome **154.0.8037.98** passed on this build: actual 360-pixel native panel, branch-local highlighting, faded endings, both double-click unlock surfaces, source/reader interaction, file round trip, toolbar capture and full restart with retained preferences. No recorded page errors. One earlier repeat exposed a stale `DevToolsActivePort` file pointing at the closed browser's port; removing that stale file before a fresh launch fixed the observed restart failure. Existing live review connections are preserved.
- Package verification passed: 18 entries, 351,340 bytes; every member matches the build. SHA-256: `47ad49dc72aa8889d31c926df50acc983027b4444474198b114953633a752e0d`. Source maps are excluded; MIT and dependency notices are included.

The icon, branch geometry, expanded reels, timeline and native panel were visually inspected. Generated evidence stays in ignored `evidence/` and CI artifacts. Public release assets were not replaced. Owner-supplied unpublished design files remain ignored and local.

## Review and boundaries

Use **Review ToMpathy.cmd** or `npm run review`. On the example, inspect each branch, hold a paragraph and hover a reel, then double-click to release. For context, use a page with explicit author links and choose **Options → Light context**, optionally **Agent search**, then **View context and timeline**. [QA guide](docs/DEVELOPMENT.md).

The example is still fictional and hand-authored. Sounding Line is not connected to a live endpoint. The timeline is an extractive report of source statements, not a verified biography or proof of improved inference. Broad web search, local summarization, author-like models, Global and value search remain future work. Redirects and JavaScript-only sources can be unavailable. [Context implementation and limits](docs/CONTEXT_RESEARCH.md).

No scientific jobs, model downloads, training runs, paid services or Store submission were started.
