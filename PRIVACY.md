# ToMpathy privacy

Updated 11 October 2026 (Pacific time) · 0.2 development branch

ToMpathy is a local browser reader for externally supplied analyses. This release has no developer-operated analytics, advertising, telemetry or inference server. No account is required.

## Page text and analyses

After you invoke ToMpathy on a page, the extension captures readable text and available creator attribution in browser-session storage. It uses the text to connect page highlights with supplied analysis. Captures exclude editable fields; extraction is heuristic and you should review a capture before sharing it. The beta does not send page text to an inference service.

Imported analyses, retrieved excerpts, extracted timeline facts, saved-page tabs and retained revisions remain in the current browser session. Theme, guide state, the GitHub preference and the Agent search preference persist locally. Readings do not sync to other devices. Export creates a file on your device containing the captured text, analysis and context; anyone you share that file with can read its contents. The context brief export also contains source excerpts and URLs. Exported files are not deleted by closing Chrome.

## Optional context requests

Light context fetches up to three explicit public creator links after Chrome grants access to their sites. When enabled, the GitHub option can replace an explicit GitHub profile link with a request to `api.github.com/users/<account>`. No token or GitHub sign-in is used. Requests omit credentials and referrers, decline redirects, and have size/time limits.

Agent search follows one additional hop of linked pages or feeds, only within those explicitly granted source sites, with at most six retrieved sources total, 256 KB per response and a 30-second job deadline. It is deterministic link following, without a model or search provider. Successful sources are cached in reader memory for 15 minutes, at most 24 entries. Refresh bypasses that cache; Clear context removes collected context and the memory cache. Requests stopped by source limits are reported rather than bypassed.

The destination receives ordinary network information, such as your IP address and the requested URL. Those sites apply their own privacy practices. ToMpathy stores source URLs, excerpts, explicitly supplied dates, retrieval times and link provenance locally. It does not run broad web search, create a model, or train on the creator. Model controls remain marked as planned.

## Permissions and control

- **activeTab** grants temporary access when you invoke the extension.
- **scripting** installs the text/highlight adapter on that page.
- **sidePanel** displays the reader beside the page.
- **storage** retains the current reading and local preferences.
- **Optional HTTPS site access** is requested for the specific context sources you choose to retrieve.

Close the panel to remove its page interaction layer. Uncheck Light context to cancel current retrieval. Close Chrome to end the temporary reading session; remove the extension to clear its extension-local data and permissions. Previously exported files remain under your control. You can review or revoke site access in Chrome’s extension settings.

For questions or defects, use the [project issue tracker](https://github.com/EmotiveAutomaton/tompathy/issues). Do not include private reading files or personal page content in a public issue.

This policy describes this development checkout. The published 0.1 beta retains its tagged policy. A future broad search, model or Sounding Line connection will require updated behavior disclosures before release.
