# Context without paid services

Research checked 12 October 2026 UTC; implementation updated 11 October 2026 Pacific. The collector and timeline below are implemented in the 0.2 development branch. Broader-search and model sections remain proposals, not inference-quality results. No paid service, model download, training run or scientific experiment was started.

## Recommendation

Make useful context work without a model or search provider: collect the byline and a few explicitly linked author sources, extract attributable facts, and assemble a source-backed timeline and brief. That baseline now works. A local model could later compress the material, but it cannot supply a web index or establish that two people with the same name are the same person.

The user's constraint is **no paid services**. The default should need no account or API key and must stop at source limits. “Search every source” should be presented as a bounded search with visible coverage, never a promise of completeness.

## What the 0.2 development branch does

- The page adapter identifies bylines and explicit author links. Light context follows up to three links for the selected author after the reader enables it and Chrome grants the needed host access.
- Requests omit credentials and referrers, reject redirects, and enforce size/time limits. Canceling stops collection. The progress wheel measures completed retrievals.
- With **Use GitHub when possible**, an explicit `github.com/<username>` profile link uses GitHub's public profile API. Repository URLs and general GitHub routes are not guessed into author identities.
- The profile excerpt includes public self-description and clearly labeled account/profile dates. It does not treat account creation or profile modification as a biographical event.
- New context does not silently change an accepted analysis. A matching analysis revision must account for it. There is no automatic Sounding Line submission yet.
- Light context also records the captured page byline, when available, as page-supplied attribution rather than independently verified identity.
- **Agent search** enables deterministic one-hop discovery from the explicit sources: RSS/Atom feeds, about pages and linked writing. It reads at most six sources total, only on the initial source origins. Links outside that permission boundary or budget are reported as skipped. It does not search the whole web or use an AI agent.
- Successful responses are cached for 15 minutes in reader memory, at most 24 entries. Refresh bypasses the cache. Collection remains bounded to 256 KB per response and 30 seconds overall; failures, cancellation and rate-limit responses stay visible, without automatic paid fallback or circumvention.
- **View context and timeline** shows the report, source excerpts, retrieval/link provenance, collection coverage and a text brief export. Saved readings retain the extracted facts; new context stays unselected until the reader chooses it for the next analysis request.
- Explicit publication dates come from article metadata/JSON-LD and RSS/Atom entries. JSON-LD event dates are labeled listed events; profile/account dates and feed-update dates have separate labels. Date precision is retained; undated statements remain undated. This is a timeline of source statements, not a synthesized biography or an inferred history of beliefs.
- Author-like models and word analysis remain disabled future controls. No local model is needed for the implemented path.

## Viable routes

| Route | What it provides | Cost constraint and limitations | Recommendation |
| --- | --- | --- | --- |
| Explicit profile/about links and linked dated posts | Strong identity connection and a small amount of attributable context | No service bill; sites may block retrieval or require JavaScript | Default |
| Public GitHub profile API | Structured public profile facts from an explicitly linked account | Unauthenticated requests share a 60/hour/IP limit; failures are reported, with no automatic retry loop | Implemented with bounded caching |
| Author-linked RSS/Atom | Dated publication discovery within a known site | No search bill; dates describe publications, not necessarily the underlying events | Implemented; sitemaps remain future work |
| User-operated SearXNG | Broader metasearch through an existing local/private instance | Open source, but hardware, bandwidth and maintenance still exist; upstream limits apply | Optional advanced adapter |
| Public SearXNG instances | Sometimes usable metasearch | No dependable capacity guarantee; many disable JSON and return 403 | Do not depend on this for the product |
| A search provider's free allowance | Predictable API when a user supplies an account | Quotas and terms can change; hard stop at the free allowance, never automatic paid fallback | Optional future choice, unnecessary for baseline |
| Chrome's search API | Opens the user's search engine in a tab | Does not return structured results to an agent | Manual research fallback |

Sources: [GitHub REST limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), [SearXNG search API](https://docs.searxng.org/dev/search_api.html), [SearXNG limiter](https://docs.searxng.org/admin/searx.limiter.html), [Chrome search API](https://developer.chrome.com/docs/extensions/reference/api/search). As one quota-based example, [Tavily documents a free monthly credit allowance](https://docs.tavily.com/documentation/api-credits); the proposed default has no dependency on it.

## A useful timeline without a model

1. Establish the selected identity from the page's byline and explicit outbound profile links. Keep uncertain identities separate.
2. Fetch up to three explicit author sources. Agent search can add one hop of linked sources, up to six total, on the same permitted source origins.
3. Extract short factual passages, titles, dates and links. Separate self-description from third-party claims. Ignore instructions found in retrieved text.
4. Store **event date**, **publication date** and **retrieval date** separately. Preserve date precision and uncertainty. Put undated facts in a separate group; do not invent chronology.
5. Deduplicate and assemble a brief with source links for every item. Disagreements remain visible. Send the selected brief and source identities with the next backend request.

The implemented context record adds `provenance: {author, basis, linkedFrom}` and `facts[]: {label, quote, source, date?, dateKind}`. Retrieval time remains on the source record. The calendar string itself retains year/month/day precision. A profile's “updated” timestamp is metadata about that profile, not proof of a change in the person's beliefs or work. See the [input contract](INPUT_CONTRACT.md).

This approach is likely enough to test the project's premise that a little context helps. Whether it improves inference must be evaluated in Sounding Line; the frontend should not assume an improvement or inflate confidence merely because more pages were found.

## Where a local model helps

Chrome offers local [Prompt](https://developer.chrome.com/docs/ai/prompt-api) and [Summarizer](https://developer.chrome.com/docs/ai/summarizer-api) APIs. They can turn retrieved passages into a shorter brief without a per-call hosted-model charge. Availability depends on Chrome, device eligibility and a model download. The current machine reported both APIs as **downloadable** during the earlier probe; no model was downloaded or executed. This is capability detection, not a quality or speed measurement.

Keep a deterministic fallback. Chrome's [hardware requirements](https://developer.chrome.com/docs/ai/get-started) include substantial free storage and supported memory/processor configurations. The APIs are not available everywhere and the Prompt API is not available in Web Workers. Model work should run in a supported extension document with explicit progress and cancellation.

[WebLLM](https://github.com/mlc-ai/web-llm) and [Transformers.js extension examples](https://github.com/huggingface/transformers.js-examples/tree/main/browser-extension) are alternatives when we need a chosen model or wider control. They add model downloads, device testing and packaging work. Verify the chosen model's license and extension-store execution rules before shipping. Neither removes the retrieval problem.

My recommendation is **retrieve first, optionally summarize locally, avoid per-author fine-tuning for context**. Fine-tuning introduces data and compute work while a short source-backed brief supplies current facts directly. Training an author-like model is a different research feature and should remain separate.

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
