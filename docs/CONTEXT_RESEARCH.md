# Context without paid services

Research checked 12 October 2026 UTC; implementation updated 11 October 2026 Pacific. The collector and timeline below are included in 0.2. Broader-search and model sections remain proposals, not inference-quality results. No paid service, model download, training run or scientific experiment was started.

## Recommendation

Make useful context work without a model or search provider: collect the byline and a few explicitly linked creator sources, extract attributable facts, and assemble a source-backed timeline and brief. That baseline now works. A local model could later compress the material, but it cannot supply a web index or establish that two people with the same name are the same person.

The user's constraint is **no paid services**. The default should need no account or API key and must stop at source limits. “Search every source” should be presented as a bounded search with visible coverage, never a promise of completeness.

## What 0.2 does

- The page adapter identifies bylines and explicit creator links. Light context follows up to three links for the selected creator after the reader enables it and Chrome grants the needed host access.
- Requests omit credentials and referrers, reject redirects, and enforce size/time limits. Canceling stops collection. The progress wheel measures completed retrievals.
- With **Use GitHub when possible**, an explicit `github.com/<username>` profile link uses GitHub's public profile API. Repository URLs and general GitHub routes are not guessed into creator identities.
- The profile excerpt includes public self-description and clearly labeled account/profile dates. It does not treat account creation or profile modification as a biographical event.
- New context does not silently change an accepted analysis. A matching analysis revision must account for it. There is no automatic Sounding Line submission yet.
- Light context also records the captured page byline, when available, as page-supplied attribution rather than independently verified identity.
- **Agent search** enables deterministic one-hop discovery from the explicit sources: RSS/Atom feeds, about pages and linked writing. It reads at most six sources total, only on the initial source origins. Links outside that permission boundary or budget are reported as skipped. It does not search the whole web or use an AI agent.
- Successful responses are cached for 15 minutes in reader memory, at most 24 entries. Refresh bypasses the cache. Collection remains bounded to 256 KB per response and 30 seconds overall; failures, cancellation and rate-limit responses stay visible, without automatic paid fallback or circumvention.
- **View context and timeline** shows the report, source excerpts, retrieval/link provenance, collection coverage and a text brief export. Saved readings retain the extracted facts; new context stays unselected until the reader chooses it for the next analysis request.
- Explicit publication dates come from article metadata/JSON-LD and RSS/Atom entries. JSON-LD event dates are labeled listed events; profile/account dates and feed-update dates have separate labels. Date precision is retained; undated statements remain undated. This is a timeline of source statements, not a synthesized biography or an inferred history of beliefs.
- Creator-like models and word analysis remain disabled future controls. No local model is needed for the implemented path.

## Viable routes

| Route | What it provides | Cost constraint and limitations | Recommendation |
| --- | --- | --- | --- |
| Explicit profile/about links and linked dated posts | Strong identity connection and a small amount of attributable context | No service bill; sites may block retrieval or require JavaScript | Default |
| Public GitHub profile API | Structured public profile facts from an explicitly linked account | Unauthenticated requests share a 60/hour/IP limit; failures are reported, with no automatic retry loop | Implemented with bounded caching |
| Creator-linked RSS/Atom | Dated publication discovery within a known site | No search bill; dates describe publications, not necessarily the underlying events | Implemented; sitemaps remain future work |
| User-operated SearXNG | Broader metasearch through an existing local/private instance | Open source, but hardware, bandwidth and maintenance still exist; upstream limits apply | Optional advanced adapter |
| Public SearXNG instances | Sometimes usable metasearch | No dependable capacity guarantee; many disable JSON and return 403 | Do not depend on this for the product |
| A search provider's free allowance | Predictable API when a user supplies an account | Quotas and terms can change; hard stop at the free allowance, never automatic paid fallback | Optional future choice, unnecessary for baseline |
| Chrome's search API | Opens the user's search engine in a tab | Does not return structured results to an agent | Manual research fallback |

Sources: [GitHub REST limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), [SearXNG search API](https://docs.searxng.org/dev/search_api.html), [SearXNG limiter](https://docs.searxng.org/admin/searx.limiter.html), [Chrome search API](https://developer.chrome.com/docs/extensions/reference/api/search). As one quota-based example, [Tavily documents a free monthly credit allowance](https://docs.tavily.com/documentation/api-credits); the proposed default has no dependency on it.

## A useful timeline without a model

1. Establish the selected identity from the page's byline and explicit outbound profile links. Keep uncertain identities separate.
2. Fetch up to three explicit creator sources. Agent search can add one hop of linked sources, up to six total, on the same permitted source origins.
3. Extract short factual passages, titles, dates and links. Separate self-description from third-party claims. Ignore instructions found in retrieved text.
4. Store **event date**, **publication date** and **retrieval date** separately. Preserve date precision and uncertainty. Put undated facts in a separate group; do not invent chronology.
5. Deduplicate and assemble a brief with source links for every item. Disagreements remain visible. Send the selected brief and source identities with the next backend request.

The implemented context record adds `provenance: {creator, basis, linkedFrom}` and `facts[]: {label, quote, source, date?, dateKind}`. Retrieval time remains on the source record. The calendar string itself retains year/month/day precision. A profile's “updated” timestamp is metadata about that profile, not proof of a change in the person's beliefs or work. See the [input contract](INPUT_CONTRACT.md).

This approach is likely enough to test the project's premise that a little context helps. Whether it improves inference must be evaluated in Sounding Line; the frontend should not assume an improvement or inflate confidence merely because more pages were found.

## Where a local model helps

Chrome offers local [Prompt](https://developer.chrome.com/docs/ai/prompt-api) and [Summarizer](https://developer.chrome.com/docs/ai/summarizer-api) APIs. They can turn retrieved passages into a shorter brief without a per-call hosted-model charge. Availability depends on Chrome, device eligibility and a model download. The current machine reported both APIs as **downloadable** during the earlier probe; no model was downloaded or executed. This is capability detection, not a quality or speed measurement.

Keep a deterministic fallback. Chrome's [hardware requirements](https://developer.chrome.com/docs/ai/get-started) include substantial free storage and supported memory/processor configurations. The APIs are not available everywhere and the Prompt API is not available in Web Workers. Model work should run in a supported extension document with explicit progress and cancellation.

[WebLLM](https://github.com/mlc-ai/web-llm) and [Transformers.js extension examples](https://github.com/huggingface/transformers.js-examples/tree/main/browser-extension) are alternatives when we need a chosen model or wider control. They add model downloads, device testing and packaging work. Verify the chosen model's license and extension-store execution rules before shipping. Neither removes the retrieval problem.

My recommendation is **retrieve first, optionally summarize locally, avoid per-creator fine-tuning for context**. Fine-tuning introduces data and compute work while a short source-backed brief supplies current facts directly. Training a creator-like model is a different research feature and should remain separate.

## Chrome extension constraints

The side panel can display progress, request narrow optional host access and retrieve allowed public sources. It cannot read arbitrary sites just because the extension is installed. A new active tab may still need toolbar invocation; restricted Chrome pages cannot be captured.

A service worker can be suspended after inactivity, so a longer context job needs persisted stages, cancellation and resumable results. Do not rely on a permanently running background loop. See [extension worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle).

If we later choose a Python crawler or local model server, it is a separately installed companion. Chrome's [native messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging) requires a registered host; an extension cannot simply spawn arbitrary local programs. This is unnecessary for the first useful context pass.

## What remains

1. Connect selected context to Sounding Line's existing request/revision boundary when a callable provider is available.
2. Review real-world source coverage. The collector currently declines redirects, cannot render JavaScript-only profiles, and does not infer identity from a same-name search. An explicit link can lead to a shared site; its statements still need attribution review.
3. Compare no context, light context and timeline context on an agreed test set before broadening retrieval. That scientific evaluation is separate from frontend verification.
4. Add optional local summarization only if the extractive brief is too verbose; add broader metasearch only if known-source coverage is insufficient. No universally available free search index is configured.

There is no mandatory paid component in that plan. A universally reliable, unlimited search service with no operator cost is not something these sources establish.


## Website source repositories and revision history — 12 October 2026

**Recommendation: add a bounded public-source resolver before adding a search model.** A website can expose exactly the evidence we want: a source file, revisions, and an explanation of a change. Discovery and a factual timeline can be deterministic and free of paid services. Finding a repository does not establish that it contains the article, that its owner wrote the article, or that the revision was deployed. This section is research and a proposed next implementation; the current collector still fetches explicit GitHub profiles, not repository history.

### Is this an actual publishing practice?

Yes. It is a supported workflow rather than an unusual hack. GitHub Pages builds websites from repositories; user/organization sites conventionally use `owner/owner.github.io`, while project sites use the project repository. Public websites can also be built from private repositories on eligible plans, so visible hosting does not guarantee visible source. I found no representative prevalence measurement and would not assign a percentage to the wider web. [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

Two verified examples show different levels of usefulness:

| Website | Public evidence checked | What ToMpathy can safely conclude |
| --- | --- | --- |
| MDN’s JavaScript Array article | Its footer links directly to the corresponding Markdown file in `mdn/content`. | Exact page-to-file linkage; inspect that file’s history rather than guessing from a repository name. This is collaborative content, so preserve multiple contributors. |
| Simon Willison’s blog | The About page identifies `simonw/simonwillisonblog` as application source, and a separate `simonwillisonblog-backup` repository as content backups. | A public code repository can be the wrong place to look for article revisions. A backup history is a sequence of captured states, not necessarily each editorial decision. |

Sources: [MDN article](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array), [its linked source file](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/array/index.md), [Simon’s explanation of his site and backups](https://simonwillison.net/about/), [application repository](https://github.com/simonw/simonwillisonblog).

### Proposed discovery order

1. Inspect links already present in the captured page: **Edit this page**, **Source**, repository links in the footer, and a linked About page. Retain the page URL and link text as the discovery evidence. A repository referenced in an article about software is only a mention until corroborated.
2. Parse an explicit GitHub file URL into repository, ref and path. Resolve branch names correctly, including names containing slashes; do not blindly assume the first segment after `blob` is the complete ref.
3. For a `github.io` address, form the documented owner/project candidate. Confirm it is public and that the candidate content matches the page.
4. If only a creator profile is known, inspect a small bounded set of public repository metadata for a matching website or a clear source description. An owner-name match is insufficient. Large accounts must end with **not found within the checked sources**, not **no repository exists**.
5. Corroborate candidates with reciprocal website links, a matching custom domain, source front matter/permalinks, and distinctive paragraphs from the current page. Prefer an exact edit link over a fuzzy title match. Keep an ambiguous candidate separate from a verified page-to-file mapping.

A Pages `CNAME` file can corroborate a candidate but is not universal: GitHub’s custom Actions publishing flow does not create or require it. DNS pointing at GitHub Pages is a hosting clue, not a reverse index of source repositories. There is no reason to probe a website for an exposed `.git` directory. [Custom-domain publishing behavior](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

### Turning a matched file into useful context

Use `GET /repos/{owner}/{repo}/commits?path={file}&per_page=5` to get a bounded revision list. Then fetch selected commit details for patches, parent SHAs, credited author/committer, and messages. Public resources support unauthenticated reads. The patch is optional for binary data and very large changes can exceed response limits. Treat missing data as incomplete coverage. [Commit API](https://docs.github.com/en/rest/commits/commits)

Retrieve a specific version through `GET /repos/{owner}/{repo}/contents/{path}?ref={sha}`. Markdown, MDX and plain HTML are good first targets; parse them as data, without running repository code. Generated bundles, CMS databases and translations need different mappings. Pin the SHA rather than following a moving branch during analysis. [Contents API](https://docs.github.com/en/rest/repos/contents)

The useful result is a short source-backed timeline, for example: “At recorded commit time T, this revision added the controller caveat; the previous available version omitted it.” Save repository, path, SHA, parent SHA, before/after excerpts, commit URL, recorded dates, discovery basis, retrieval time and coverage. Keep author time, committer time and any confirmed publication time distinct. Use **first available version**, not **first draft**, when history starts midway.

Editorial inferences come afterwards: a restored caveat can support an account of attention to limitations, but the patch alone does not establish intent or AI involvement. A bulk formatting change, migration, bot commit or squashed pull request can obscure the actual writing sequence. File renames, rewritten history and gaps need explicit coverage notes. A commit credited to one account is not proof of sole authorship. Do not convert a commit count into confidence or creator involvement.

### Free operation and Chrome feasibility

The public REST API allows **60 unauthenticated requests per hour per originating IP**. Authenticated personal access normally raises the primary limit, but an account/token should be optional and never bundled into the extension. Secondary limits still apply. Respect remaining/reset headers and stop on rate limits rather than rotating identities or retrying aggressively. [GitHub rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)

Suggested first budget: at most **10 requests, one candidate repository, five revisions, 256 KB per text response, and 30 seconds per job**, with caching by repository/path/SHA. These are proposed product limits, not measured coverage. Ten requests should cover a directly linked file and a few detailed revisions; discovery-heavy sites will run out sooner. Several readers on one IP share the anonymous allowance. Cache immutable versions indefinitely within a storage cap; recheck the latest ref conservatively. A 404 or a rate-limit response is not evidence that source does not exist.

Do not make global code search a baseline dependency. GitHub’s code-search considerations explicitly require authentication and impose a tighter search limit; the same page also contains contradictory generic public-access wording. The conservative implementation is to omit it from the no-account path and verify any authenticated enhancement separately. [Search API restrictions](https://docs.github.com/en/rest/search/search#search-code)

Chrome can perform these requests from extension-owned code with the relevant host permission. A content script’s cross-origin requests still face page-origin restrictions, so discovery can start on the page and retrieval should run in the extension. Use a bounded message format, validate repository/path inputs, omit page credentials, and render fetched material as text. GitHub source is untrusted input, including READMEs and commit messages. This requires no paid inference and no GPU work. [Chrome cross-origin requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests)

A useful next implementation would cover exact GitHub source links first, produce cited factual diffs, and report coverage. The existing source-selected context pipeline could consume those records. A local summarizer can later shorten them, but it cannot recover unpublished drafts or turn an uncertain website-to-repository match into evidence. For your own site, the easiest reliable interface would be an explicit source-file link once you choose to publish sanitized source. No repository publication is needed for this research pass.

### Implemented follow-up — 12 October 2026

The development reader now captures explicit repository and source-file links, preferring exact files. Collection resolves public GitHub metadata, file contents and up to three recent revisions with available bounded patches. It resolves refs with up to three path segments instead of assuming all branch names lack slashes. One repository receives at most eight unauthenticated API requests, within the collector's existing 30-second deadline and 256 KB response cap. Oversized/unavailable patches preserve already received commit metadata and explicitly record missing detail. Rate-limit failures are not retried; there is no code search, model, token rotation or paid service.

The saved Light context preference refreshes on reader open and creator/page changes using existing Chrome permissions. Permission acquisition remains a user gesture in Options. Sources become timeline facts and are available for the existing analysis handoff; scores are not recomputed without Sounding Line. Recent repository context is reused from the browser session for 15 minutes; explicit Refresh bypasses it. Small horizontal progress bars report completed requests, finish as a check and fade.

A live unauthenticated check against MDN's explicitly linked Array source returned the source file and three revisions dated 2026-07-28, 2026-02-24 and 2025-09-28, including patch excerpts. Repeatable tests cover slash-containing refs, no-auth/no-redirect fetches, date meanings, schema validity, rate-limit stopping, response bounds, startup collection and cached reopening. These demonstrate source-history retrieval; they do not independently verify the selected creator's identity or reconstruct unpublished drafts. The implementation follows GitHub's [file contents](https://docs.github.com/en/rest/repos/contents#get-repository-content) and [commit history](https://docs.github.com/en/rest/commits/commits#list-commits) APIs.

### Theory note behind the Core values visual

The heading help preserves the proposed model: infer desired changes from initial states and actions, relate them to history, sketch a preferred trajectory and uncertain homeostatic range, and encode reward horizon and accepted cost with vectors. The demo uses supplied drawing coordinates and authored observations; its pie confidence is separate from preference strength.

Homeostatic reinforcement learning offers a formal model connecting physiological regulation, reward and temporal discounting under stated assumptions. That supports the conceptual analogy, not a claim that abstract values or a numerical discount rate can be measured from prose. [Keramati and Gutkin, 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4270100/)

Preference inference also has an identification problem: behavior alone does not uniquely separate preferences from how an agent plans. The design therefore needs alternatives, constraints and uncertainty even when more history becomes available. This is a limitation on uniqueness, not a claim that context is useless. [Armstrong and Mindermann](https://arxiv.org/abs/1712.05812)
