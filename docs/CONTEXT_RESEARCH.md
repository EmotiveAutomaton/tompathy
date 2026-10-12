# Context without paid services

Research checked 12 October 2026. This is an implementation proposal, not an inference-quality result. No paid service, model download, training run or scientific experiment was started.

## Recommendation

Make useful context work without a model or search provider: collect the byline and a few explicitly linked author sources, extract attributable facts, and attach a compact source-backed brief. Add an optional dated timeline later. A local model can compress that material, but it cannot supply a web index or establish that two people with the same name are the same person.

The user's constraint is **no paid services**. The default should need no account or API key and must stop at source limits. “Search every source” should be presented as a bounded search with visible coverage, never a promise of completeness.

## What 0.1 beta actually does

- The page adapter identifies bylines and explicit author links. Light context follows up to three links for the selected author after the reader enables it and Chrome grants the needed host access.
- Requests omit credentials and referrers, reject redirects, and enforce size/time limits. Canceling stops collection. The progress wheel measures completed retrievals.
- With **Use GitHub when possible**, an explicit `github.com/<username>` profile link uses GitHub's public profile API. Repository URLs and general GitHub routes are not guessed into author identities.
- The profile excerpt includes public self-description and clearly labeled account/profile dates. It does not treat account creation or profile modification as a biographical event.
- New context does not silently change an accepted analysis. A matching analysis revision must account for it. There is no automatic Sounding Line submission yet.
- Agent search, timeline synthesis and author-like local models remain disabled future controls.

## Viable routes

| Route | What it provides | Cost constraint and limitations | Recommendation |
| --- | --- | --- | --- |
| Explicit profile/about links and linked dated posts | Strong identity connection and a small amount of attributable context | No service bill; sites may block retrieval or require JavaScript | Default |
| Public GitHub profile API | Structured public profile facts from an explicitly linked account | Unauthenticated requests share a 60/hour/IP limit; honor errors and rate-limit headers | Implemented; add bounded caching later |
| Author-linked RSS/Atom and sitemaps | Dated publication discovery within a known site | No search bill; dates describe publications, not necessarily the underlying events | Next small extension |
| User-operated SearXNG | Broader metasearch through an existing local/private instance | Open source, but hardware, bandwidth and maintenance still exist; upstream limits apply | Optional advanced adapter |
| Public SearXNG instances | Sometimes usable metasearch | No dependable capacity guarantee; many disable JSON and return 403 | Do not depend on this for the product |
| A search provider's free allowance | Predictable API when a user supplies an account | Quotas and terms can change; hard stop at the free allowance, never automatic paid fallback | Optional future choice, unnecessary for baseline |
| Chrome's search API | Opens the user's search engine in a tab | Does not return structured results to an agent | Manual research fallback |

Sources: [GitHub REST limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), [SearXNG search API](https://docs.searxng.org/dev/search_api.html), [SearXNG limiter](https://docs.searxng.org/admin/searx.limiter.html), [Chrome search API](https://developer.chrome.com/docs/extensions/reference/api/search). As one quota-based example, [Tavily documents a free monthly credit allowance](https://docs.tavily.com/documentation/api-credits); the proposed default has no dependency on it.

## A useful timeline without a model

1. Establish the selected identity from the page's byline and explicit outbound profile links. Keep uncertain identities separate.
2. Fetch a bounded set of author-linked sources. An initial budget could be three pages, then up to three linked dated posts if the reader enables Agent search. These are proposed limits, not current extra requests.
3. Extract short factual passages, titles, dates and links. Separate self-description from third-party claims. Ignore instructions found in retrieved text.
4. Store **event date**, **publication date** and **retrieval date** separately. Preserve date precision and uncertainty. Put undated facts in a separate group; do not invent chronology.
5. Deduplicate and assemble a brief with source links for every item. Disagreements remain visible. Send the selected brief and source identities with the next backend request.

A future record might contain `subject`, `claim`, `eventDate`, `publishedAt`, `retrievedAt`, `datePrecision`, `sourceURL`, `supportingExcerpt`, and `identityBasis`. This is a proposal separate from the accepted result contract. A profile's “updated” timestamp is metadata about that profile, not proof of a change in the person's beliefs or work.

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

## Suggested next build

1. Cache explicitly linked profiles with a short expiry and visible provenance, respecting provider rate limits.
2. Add a small dated-post/RSS collector and deterministic timeline output. Keep undated statements separate.
3. Connect selected context to Sounding Line's existing request/revision boundary.
4. Compare no context, light context and timeline context on an agreed test set before broadening retrieval.
5. Add optional local summarization only if the extractive brief is too verbose; add broader metasearch only if known-source coverage is insufficient.

There is no mandatory paid component in that plan. A universally reliable, unlimited search service with no operator cost is not something these sources establish.
