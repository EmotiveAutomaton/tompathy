# ToMpathy privacy

Updated 14 October 2026 (Pacific time) · 0.3 beta development

ToMpathy is a browser reader with optional analysis sources. It has no developer-operated analytics, advertising, telemetry or hosted inference server. No account is required. Analysis defaults to **None**; configuring a source does not send a captured page until you choose **Analyze capture**.

## Page text and analyses

After you invoke ToMpathy on a page, the extension captures readable text and available creator attribution in browser-session storage. It uses the text to connect page highlights with supplied analysis. Captures exclude editable fields; extraction is heuristic and you should review a capture before sharing it. Page text reaches an analysis service only through the explicit local-companion request described below. On `https://abrahamhaskins.org` and its `www` hostname, this version matches captured public text to a creator-commissioned, hand-authored demo. It assigns invented analysis and provisional cues locally for UX testing. This site-specific behavior does not classify other websites. Newly visible sections and project descriptions refresh the local capture. On this commissioned site, stable navigation, headings and footer text are also captured; References & Assets is grouped as one reading unit. Temporary citation tooltips and popovers are excluded. No private website history is bundled.

Imported analyses, retrieved excerpts, extracted timeline facts, saved-page tabs and retained revisions remain in the current browser session. Theme, guide state, Light context, the GitHub preference and the Agent search preference persist locally. Readings do not sync to other devices. Export creates a file on your device containing the captured text, analysis and context; anyone you share that file with can read its contents. The context brief export also contains source excerpts and URLs. Exported files are not deleted by closing Chrome.

## Optional analysis sources

**Public registry.** You supply an HTTPS registry address and grant access to that origin. Analyze capture first requests a bucket named by four hexadecimal characters of the artifact identifier's SHA-256 hash. The extension filters that index locally. When a matching revision exists, its packet request reveals the **full identifier hash and revision hash** to the registry host. Hashes and buckets do not make this anonymous: a host can compare known public pages. Requests send no captured text, selected context, cookies or credentials. Context-conditioned readings cannot use this provider. A changed page is refused rather than attached approximately.

**Local companion.** You run the separate engine on `http://127.0.0.1`, enter its port and 256-bit token, and grant loopback access. Analyze capture sends the complete captured artifact, requested evidence scope and only selected context for context scope. The engine verifies the token and exact extension origin. Its normal analysis path uses local records and CPU code; it does not call a model or fetch history automatically. Cancellation requests identify the running job. Changing the source, scope or selected context invalidates the pending response.

The provider address and companion token persist in extension-local storage. They do not sync and are excluded from reading exports and analysis packets. Choosing None clears the saved token from the provider setting. The token file, ledgers, model files, feature caches and generated packets belong to the separately installed engine and remain on disk until you remove them. Removing the extension does not delete those files. The development web preview uses its own origin's local storage for provider settings.

The engine's explicit ingest command can retrieve public Wikipedia history or read an explicitly supplied Git checkout, PGN, panel bundle or CoAuthor log. These commands retain source text, identities scoped to the dataset, timestamps, provenance and exclusions locally. Public source requests reveal the requested source to its host. The optional literal transcriber accepts explicitly configured loopback model endpoints; it makes no paid calls and downloads no models. Model inputs and labels can remain in its local cache. Research-only tools are separately installed and are not enabled by extension capture. Registry generation writes local files; publishing those files is a separate action. Private CoAuthor readings require a private local registry.

**Wikipedia history analysis.** On Wikipedia articles, the separate **Analyze Wikipedia history** action asks an explicitly enabled companion to fetch up to 20 public revisions from Wikipedia. Wikipedia receives the article request and ordinary network information. The companion retains an immutable local history snapshot and may run its explicitly configured, admitted literal transcriber and comparison models. A capture alone never starts this workflow. Cancellation stops at the next fetch, transcription, or fitting boundary; a local model call already in progress may finish before cancellation takes effect.

## Optional context requests

Light context fetches up to three explicit public creator links after Chrome grants access to their sites. When the saved option is enabled, reopening the reader or changing the creator/page starts collection using existing permissions. Missing permissions require a user-initiated refresh from Options. The GitHub option reads explicit profile links and one explicitly linked repository or source file through `api.github.com`. It retrieves public metadata and up to three revisions, including available bounded text patches. Git-recorded contributor names and dates are retained; ownership is not treated as proof of authorship. No token or GitHub sign-in is used. Requests omit credentials and referrers, decline redirects, and have size/time limits.

Agent search follows one additional hop of linked pages or feeds, only within explicitly granted sites, with at most six retrieved sources total, 256 KB per response and a 30-second job deadline. One repository lookup may use up to eight requests within that deadline. It is deterministic link following, without a model or search provider. Successful sources are cached in reader memory for 15 minutes, at most 24 entries; fresh repository context can also be reused from the current saved session. Refresh bypasses caches; Clear context removes collected context and the memory cache. Requests stopped by source limits are reported rather than bypassed.

The destination receives ordinary network information, such as your IP address and the requested URL. Those sites apply their own privacy practices. ToMpathy stores source URLs, excerpts, explicitly supplied dates, retrieval times and link provenance locally. It does not run broad web search, create a model, or train on the creator. Model controls remain marked as planned.

## Permissions and control

- **activeTab** grants temporary access when you invoke the extension.
- **scripting** installs the text/highlight adapter on that page.
- **sidePanel** displays the reader beside the page.
- **storage** retains the current reading and local preferences.
- **Optional HTTPS site access** is requested for the specific context sources you choose to retrieve.
- **Optional loopback access** is requested when you save a local-companion configuration. Registry configuration also requests access to its chosen HTTPS origin.

Close the panel to remove its page interaction layer. Uncheck Light context to cancel current retrieval. Close Chrome to end the temporary reading session; remove the extension to clear its extension-local data and permissions. Previously exported files remain under your control. You can review or revoke site access in Chrome’s extension settings.

For questions or defects, use the [project issue tracker](https://github.com/EmotiveAutomaton/tompathy/issues). Do not include private reading files or personal page content in a public issue.

This policy describes the 0.3 beta working branch. Published older versions retain their tagged policies. Hosted inference and broad model search are not included.


Sentence reading treatment uses only the accepted packet's supplied Ghost Scale records. The ordinary-page adapter does not classify text or send it to a font service; the commissioned website demo supplies locally authored classifications as described above. A bundled font resource is accessible to the page while annotations are applied; it contains no reading data. The adapter temporarily wraps text nodes and restores them on cleanup. Exported readings may include captured bold-emphasis ranges, exact supplied generation prompts, and sentence-level production explanations, alongside the existing text and analysis.

On ordinary pages, detailed sentence explanations and evidence are held in the content script’s isolated memory. Tooltips and supplied prompts use closed shadow content rather than embedding those details in page-readable attributes. The visual text styling itself remains visible to the page.
