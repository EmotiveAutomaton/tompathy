# ToMpathy status · 2026-10-11 · 0.4.0 alpha

The Options and connected-reels pass is implemented. This remains a private **0.4.0 alpha**. The intended later public release is **0.1 beta**, initially an empty frontend.

## Current interface

- Exactly three boxes, with top-right corner headings. Current attention remains independent of the hierarchy and keeps its quiet idle cue.
- Options contains Author selection, Context, two disabled future checkboxes (an author-like local model and word-level analysis), system/light/dark, Help, Import and Export. The status captions, manual capture command, source tools and list setting are absent from Options. Testing tools are available only in the explicit QA surface.
- Focus indicators use green instead of the earlier amber/red-looking outline. The values list moves into the top space with both columns aligned. The world tab is now **global**; global/search remain previews.
- Hierarchy geometry allocates each child inside its actual parent band. Shared DAG nodes get separate linked visual instances under each parent path. They highlight together; no brick crosses the two outcomes. The broad left edge remains rounded.
- Reels are always present. Idle reels are blurred and ignore hovering. With a locked selection, hovering/focusing any reel reveals ambiguous candidate rows and the supplied connections across intermediate levels. The chart and reels remain visible together. Escape first closes the expansion or dialog; it no longer also releases the source selection.
- A short first-use invitation offers a four-step hover/hold/inspect/unlock guide. It is dismissible, shown once per profile, and replayable from Help. No permanent fourth box was added.
- Export writes one portable HTML reading containing exact captured text, analysis, context and retained revisions. Import validates anchors and matching, reopens an extension-owned saved text page, and restores page/panel interaction. Original webpage styling, images and active features are not archived.
- Context is a bounded linked-author-source collector. Its wheel reports real completed retrievals, then checks/fades on success. It does not fabricate inference progress or alter estimates. Wider web search, brief synthesis and automatic Sounding Line submission are not connected. The fictional example has no real author profile.

## Research conclusion

Start with page metadata, explicit author links and an extractive brief. Use a maximum of two paid search calls only when the linked sources do not suffice. Make Chrome-local summarization optional, with a no-model fallback. Keep the future author-like model separate. [The implementation research](docs/CONTEXT_RESEARCH.md) covers extension viability, local/hosted alternatives, current provider prices, source identity, file choices and a staged evaluation plan.

## Verification

Local verification passed on build **`aea81e77c563`**:

- **17/17 core tests** and **16/16 browser tests**.
- Ordinary **Google Chrome 154.0.8037.98**: installed extension, actual native side panel, linked text/locks, portable export/import, updated imported revision retained after tab switching, toolbar capture, unchanged launcher continuity, and same extension ID/preferences after a full restart. No recorded browser errors.
- Bundled **Chromium 153.0.8010.12**: panel cleanup/reopen, stopped-worker recovery, 1,006-passage source, automatic recapture on return, and accepted revision retained across panel closure.
- Package verification confirms the ZIP contains the tested build, including the saved-page reader.
- Chrome's local Prompt and Summarizer availability probes both returned **downloadable**. No model was downloaded or run.

Receipts: `evidence/review-validation.json`, `evidence/native-validation.json`, `evidence/test-results.json` and `evidence/package-verification.json`. The physical folder picker is not claimed as automated. Screenshots were visually inspected at native width and in light/dark layouts; connected alternatives and the imported reading were inspected as well.

The geometry regression checks that each visual child meets its supplied parent and stays in its parent's band, all semantic nodes remain represented, and dots stay inside visible shapes. Browser checks cover Options, idle reels, connected expansion, Escape, source restoration, altered-file rejection, actual fixture retrieval progress, first-use guidance, narrow/dark/zoom layouts and legacy flows. New sources remain outside accepted scores until a matching analysis is supplied.

## Review and remaining boundaries

Run **ToMpathy Review** or **Review ToMpathy.cmd**, open the guided example, then Open Maker Reader. Review Options; lock **Show the iteration** and hover a reel; export/import a reading. Development tools and revision fixtures are linked separately from the Review desk.

No live inference, paid search account, model download, author training or scientific job was started. Automatic tab following respects Chrome's existing access grants; a new site still needs toolbar invocation. Dense graph payloads retain an automatic scrollable fallback, though the list setting is gone. Arbitrary-page capture remains heuristic; restricted pages, inaccessible frames, closed shadow roots and non-text media need future handling. Context is currently collected for the selected reading, not a persistent cross-site author profile.

The user's untracked `TOMPATHY_THEORY_AND_ENGINE_REVIEW_2026-10-10.md` remains untouched and excluded from the change. Work remains on `codex/author-first-testbed`; main and upstream scientific repositories are unchanged.
