# Author context implementation research

11 October 2026 · design recommendation for ToMpathy and its Sounding Line boundary

The first useful version does not need a search agent or a new model. Read the author information already attached to the article, follow a few explicit author links, and give Sounding Line a compact packet of source-linked excerpts. Add paid search only when those links are insufficient. Make model summarization an optional replacement for the final compression step.

This separates three jobs: finding the right person, finding useful material, and shortening that material. A model can help with the last two, but it cannot make an uncertain identity certain. The proposed collector supplies evidence; Sounding Line remains responsible for interpreting it.

## What exists in this build

The Context checkbox now finds up to three explicit author links from `rel=author` or Article JSON-LD author records, filters them against the selected author label, requests Chrome access to those origins, and uses the existing bounded collector. The collector accepts HTML/plain text/Markdown, omits credentials, declines redirects, caps each response at 256 KB and the job at 30 seconds, and cancels when the reading changes. It retains source URLs, timestamps and excerpt hashes. A small progress wheel counts completed sources; success becomes a check and fades, while failure never gets a success check.

This is a linked-source foundation. It does not yet issue web searches, synthesize a report, train a model, or submit a new Sounding Line analysis. Collected items remain separate from the accepted analysis. The fictional example has no real author profile to retrieve. The disabled author-model checkbox and word-level checkbox are deliberate placeholders.

## A small default workflow

1. **Identify the author from the page.** Prefer the selected byline and its direct profile link. Read Article/Person metadata as publisher claims. An organization, multiple authors, pseudonym or missing byline should remain such; do not silently pick a same-named person from search.
2. **Take the free information first.** Preserve the byline, description, publication/date, author profile URL, explicit role or affiliation, and linked project. These are data fields and excerpts, not inferred personality traits.
3. **Retrieve two or three relevant sources.** Prefer the author's own profile/about page, the project or article they explicitly link, and a relevant first-person note. Stop when the brief has enough useful material. A general biography dump is unnecessary.
4. **Search only to fill a specific gap.** Use at most two templated queries, such as `"Name" site:publisher.example author` and `"Name" "Project"`. An exact handle/linked domain is a stronger seed than a name. A small model may suggest a better query later; a deterministic template is a useful initial baseline.
5. **Write a short evidence brief.** Target 300–600 words or roughly 600–1,000 tokens as an initial budget, with source references for every factual entry. Preserve relevant quotes separately from generated summaries. Return fewer facts when little is known.
6. **Request a new analysis.** Bind the brief and raw excerpts to the article revision, selected author and context IDs. Ignore a late result if the user has moved to a different page or author. Keep the accepted reading stable until a valid replacement is ready.

These sizes and stopping rules are proposed engineering defaults. They have not been demonstrated to improve the scientific engine. The user's observation that small amounts of context help is the motivation for testing this economical baseline.

For a page with an explicit GitHub profile, a small dedicated adapter can use the public user endpoint for a bio, linked site and stable account identity. A project link alone does not establish the page author's identity. Unauthenticated public REST access is limited to 60 requests per hour per originating IP; common authenticated requests have a 5,000/hour primary limit, with additional restrictions on some endpoints. Cache a confirmed profile within the reading session and handle rate-limit failures. [GitHub user endpoint](https://docs.github.com/en/rest/users/users#get-a-user), [GitHub rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

## Ways to build it

| Approach | What happens | Benefits | Main cost or limitation |
| --- | --- | --- | --- |
| Rules and excerpts inside Chrome | Follow explicit links; rank paragraphs; return a structured extractive brief | No model download or per-query model bill; inspectable and deterministic | Sparse metadata and difficult pages; limited semantic compression |
| Rules plus Chrome's local AI | Same retrieval, then locally summarize or produce structured fields | No per-call inference service charge; no separate desktop installation | Device eligibility, initial download, model changes and output validation |
| Search API plus a small service | Backend holds the search key, retrieves sources and prepares the brief | Consistent keys, budgets and network handling; easy Sounding Line handoff | A service to operate and small usage charges |
| Bundled browser model | Transformers.js or WebLLM runs a chosen model in the extension | Greater control over model/version; useful for specialized ranking | Download size, RAM/GPU load, packaging and model lifecycle work |
| Local companion process | Chrome sends a bounded job to a local Sounding Line helper | Reuses local compute; suitable for future specialized models | Installer, process lifecycle and an authenticated local connection |
| Fully hosted research agent | Delegate search, reading and synthesis | Quick to prototype a sophisticated report | More variable cost, latency and source selection; excessive for a tiny first brief |

My recommendation is the first approach, with a search provider behind the existing backend boundary when needed. Then compare the same evidence with and without local summarization. A local model should earn its place by producing a better, shorter brief, not be a prerequisite to retrieving an author page.

## Chrome can host this, with specific constraints

**The panel is a viable home for short work.** Extension pages can fetch other origins with host permission; page content scripts retain the page's cross-origin restrictions. Put retrieval in the extension document or a service, and communicate with the page adapter using small messages. [Chrome network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests).

**The background worker is not a permanently running agent.** Chrome normally ends it after 30 seconds of inactivity, a five-minute request, or a fetch response that takes over 30 seconds to arrive. Store job IDs and completed stages instead of relying on globals. The current short collector cancels when the panel closes; a future service can finish independently and return a result when the panel resumes. [Worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle).

**Built-in AI is worth a feature probe.** The Prompt API is stable for extensions from Chrome 138 and can constrain output to JSON Schema. It is not available in Web Workers. Use an extension document for an initial prototype. [Prompt API](https://developer.chrome.com/docs/ai/prompt-api). The Summarizer API is also stable from Chrome 138. Its availability must be checked at runtime; a first model download requires user activation. [Summarizer API](https://developer.chrome.com/docs/ai/summarizer-api).

A read-only probe in this machine’s ordinary Chrome 154 extension panel returned **downloadable** for both `LanguageModel` and `Summarizer`. No model was created or downloaded. This establishes API availability here; it does not measure quality, download time or inference speed. The receipt is `evidence/review-validation.json`.

The current hardware requirements include a supported desktop OS, 22 GB free on the profile volume, and either more than 4 GB VRAM or at least 16 GB RAM with four CPU cores. The storage requirement is not the model's download size. After download, inference is local. Use the extractive brief whenever the device is unavailable, and never download a model simply because someone hovers a sentence. [Built-in AI requirements](https://developer.chrome.com/docs/ai/get-started).

An offscreen document supplies DOM access and runtime messaging, but only one is generally available per extension and creation needs a supported reason. It is a possible later home for DOM processing; it is not proof that all built-in AI/download activation flows work invisibly there. Test that separately before relying on it. [Offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen).

**Search and local inference are separate.** Chrome's `search.query()` opens results in a tab or window and returns no result list. It does not supply a free structured search backend. A local LLM also has no current web index by itself. [Chrome search API](https://developer.chrome.com/docs/extensions/reference/api/search).

**Keep shared service keys outside the shipped extension.** For a private prototype, an explicitly provided user key is possible. For a public release, use an authenticated service with per-user budgets. Packaged source is inspectable. Chrome recommends user-provided keys or a proxy and treats model weights separately from remotely hosted executable code. [Extensions and AI](https://developer.chrome.com/docs/extensions/ai). Bundle JavaScript/WASM runtime code appropriately; do not copy a CDN-loading web demo unchanged into Manifest V3. [Remote code rules](https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code).

**Following pages automatically still has an access boundary.** ToMpathy already reacts to active-tab changes and navigation. `activeTab` is granted by invoking the extension and is revoked on navigation to another origin. Seamless reading on every new site would need broader site access; the current build keeps the toolbar-grant approach. Removing the redundant capture command does not remove Chrome's permission requirement. [activeTab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab).

## Search costs

Public list prices checked 11 October 2026, excluding taxes, extra services and the main Sounding Line inference. The per-author column assumes exactly two searches, with no retry or extra extraction. It is arithmetic, not a measured production bill.

| Service and mode | Published rate | Two searches per author | 1,000 authors at that workload |
| --- | --- | --- | --- |
| Direct links with our collector | No search-provider calls | $0 search API spend | $0 search API spend |
| Brave Search | $5 / 1,000 requests | $0.010 | $10 |
| Tavily basic, pay as you go | 1 credit/search at $0.008/credit | $0.016 | $16 |
| Exa Instant | $4 / 1,000 requests, up to ten results | $0.008 | $8 |
| Exa Fast / Auto | $7 / 1,000 requests, up to ten results | $0.014 | $14 |

Brave lists $5 monthly free credits; its signup still requires a card check. The current pricing page is preferable to older Brave comparison posts that describe a different free plan. [Brave pricing](https://brave.com/search/api/), [credit requirements](https://api-dashboard.search.brave.com/documentation/resources/help-feedback).

Tavily provides 1,000 free monthly credits without a card. Advanced search costs two credits; extraction is separately metered. This is attractive for a quick evaluation with little setup. [Tavily pricing](https://docs.tavily.com/documentation/api-credits).

Exa lists $10 monthly credits plus a $10 onboarding bonus without a payment method. Its current table distinguishes Instant from Fast/Auto; older pages showing only $7/search-thousand miss that distinction. Extra results and generated page summaries add costs. [Exa pricing](https://exa.ai/pricing).

For a scale example, if only 25% of 1,000 authors need fallback search and each uses two Brave searches, the gross search bill is $2.50 before credits. That 25% is an assumption to measure. Cache hits and early stopping could matter more than shaving a fraction of a cent from summarization. Do not enable unconstrained “research until done” calls for this job.

## Reusable implementations

- Google's [on-device extension sample](https://github.com/GoogleChrome/chrome-extensions-samples/tree/main/functional-samples/ai.gemini-on-device) is a starting point for availability, model sessions and extension integration.
- Hugging Face supplies a [Transformers.js extension example](https://github.com/huggingface/transformers.js-examples/tree/main/browser-extension). This route is worth considering for a compact classifier, embedding ranker or sentence selector before choosing a generative model.
- [WebLLM](https://github.com/mlc-ai/web-llm) supports in-browser generation, structured output and extension examples. It gives more model control, but the first download and cache lifecycle are meaningful engineering work. It does not provide a search index.
- [Native messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging) can connect Chrome to a separately installed executable through a registered host. That is a reasonable future bridge to local Sounding Line. A private development HTTP bridge is another option, but it needs an explicit origin/token boundary and a maintained local process.

No runtime or model was installed from these examples during this pass. They are candidates to reuse after the retrieval baseline is measured.

## What the brief should contain

Use a versioned object with `jobId`, article revision, selected maker, source URLs, retrieval time, exact excerpts, and a compact list of statements with supporting source IDs. Include how each source is connected to the author: direct byline link, publisher author record, author-linked project, or unresolved search candidate. Keep unresolved candidates out of the accepted brief.

A useful short report might say: “The publisher identifies this writer as a garden designer [S1]. The linked notebook describes testing a seat with visitors [S2]. The project brief names material and access constraints [S3].” Those are proposed example contents, not findings about a real person. Do not let compression turn “the bio says” into verified biography, or a present-day profile into something the author necessarily knew when writing an old article.

The raw source excerpts should remain available even if the local model produces the compact report. Sounding Line can then compare a compressed brief against the original excerpts. Keep current attention, hierarchy and latent preferences out of the collector's output unless the inference engine itself supplies them.

## Files and the progress indicator

The current Export includes a readable page snapshot and the accepted reading in one HTML file. It preserves text and anchors for reinspection, not the website's original visuals. Future context briefs can travel in the same versioned bundle beside their raw sources.

If full visual archiving becomes necessary, Chrome's `pageCapture.saveAsMHTML()` captures the page and resources, but requires an additional permission. MHTML can only be opened from the filesystem in a main frame, so it is awkward as an imported extension-owned reading surface. A ZIP containing MHTML plus analysis is a separate design, not an invisible upgrade to the current one-file reader. [Page capture API](https://developer.chrome.com/docs/extensions/reference/api/pageCapture).

For a fuller context job, progress can have two little wheels: sources gathered and brief prepared. Use actual completed source counts, measured model-download progress, and an indeterminate state during work with no honest percentage. Show a check only after the brief validates; do not tie progress to a claimed confidence gain. On failure, retain a compact hover explanation and a retry path. Never let an older author's completed job replace the current author's result.

## A focused next implementation pass

First, collect a small corpus of public pages with explicit author links, ambiguous names, organizations, missing bylines and outdated profiles. Use fixtures for failures and rate limits so QA stays deterministic. Test direct links and an extractive brief before paying for search.

Then add a provider-neutral search interface behind Sounding Line or a tiny companion service. Evaluate two providers on the same missing-context cases, with fixed budgets. Record wrong-person matches, useful source yield, source-grounded statements, report size, latency and actual cost. Compare no added context, raw excerpts, extractive brief and model-compressed brief in the existing engine's evaluation process; this frontend pass does not launch or redefine those experiments.

The remaining product choices are small: whether broader public search should be automatic when Context is checked, whether a model download is acceptable as an optional feature, and whether the public extension should rely on a hosted service or an installed local companion. My defaults are bounded automatic fallback search after strong identity evidence, an optional model download with an extractive fallback, and the existing Sounding Line service boundary. The author-like model remains a separate later project.
