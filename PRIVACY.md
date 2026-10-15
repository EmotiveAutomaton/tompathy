# ToMpathy privacy

Updated 14 October 2026 (Pacific time) · 0.2.0

ToMpathy is a local browser reader for externally supplied analyses. This release has no developer-operated analytics, advertising, telemetry or inference server. No account is required.

## Page text and analyses

After you invoke ToMpathy on a page, the extension captures readable text and available creator attribution in browser-session storage. It uses the text to connect page highlights with supplied analysis. Captures exclude editable fields; extraction is heuristic and you should review a capture before sharing it. The extension does not send page text to an inference service. On `https://abrahamhaskins.org` and its `www` hostname, this release matches captured public text to a creator-commissioned, hand-authored demo. It assigns invented analysis and provisional cues locally for UX testing. This site-specific behavior does not classify other websites. Newly visible sections and project descriptions refresh the local capture. On this commissioned site, stable navigation, headings and footer text are also captured; References & Assets is grouped as one reading unit. Temporary citation tooltips and popovers are excluded. No private website history is bundled.

Imported analyses, retrieved excerpts, extracted timeline facts, saved-page tabs and retained revisions remain in the current browser session. Theme, guide state, Light context, the GitHub preference and the Agent search preference persist locally. Readings do not sync to other devices. Export creates a file on your device containing the captured text, analysis and context; anyone you share that file with can read its contents. The context brief export also contains source excerpts and URLs. Exported files are not deleted by closing Chrome.

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

Close the panel to remove its page interaction layer. Uncheck Light context to cancel current retrieval. Close Chrome to end the temporary reading session; remove the extension to clear its extension-local data and permissions. Previously exported files remain under your control. You can review or revoke site access in Chrome’s extension settings.

For questions or defects, use the [project issue tracker](https://github.com/EmotiveAutomaton/tompathy/issues). Do not include private reading files or personal page content in a public issue.

This policy describes release 0.2.0. The published 0.1 beta retains its tagged policy. A future broad search, model or Sounding Line connection will require updated behavior disclosures before release.


Sentence reading treatment uses only the accepted packet's supplied Ghost Scale records. The ordinary-page adapter does not classify text or send it to a font service; the commissioned website demo supplies locally authored classifications as described above. A bundled font resource is accessible to the page while annotations are applied; it contains no reading data. The adapter temporarily wraps text nodes and restores them on cleanup. Exported readings may include captured bold-emphasis ranges, exact supplied generation prompts, and sentence-level production explanations, alongside the existing text and analysis.

On ordinary pages, detailed sentence explanations and evidence are held in the content script’s isolated memory. Tooltips and supplied prompts use closed shadow content rather than embedding those details in page-readable attributes. The visual text styling itself remains visible to the page.
