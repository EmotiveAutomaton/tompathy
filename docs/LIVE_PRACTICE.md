# Live engine practice

Run **Practice ToMpathy.cmd**, or `npm run practice`. It builds the extension,
opens the existing separate Chrome review profile and starts the real Python
companion on an available loopback port. The launcher can close after startup;
a small background host keeps its companion available until review Chrome closes.
Normal Chrome profiles and research jobs are not touched.

The launcher requires this checkout's Node dependencies and installed Python
engine. If those are not present, install them once:

```powershell
npm ci
py -3.12 -m venv engine/.venv
engine/.venv/Scripts/python.exe -m pip install -e engine
```

An existing Python 3.12+ engine environment works; do not recreate it merely to
run practice. Capture and observed history work without a model. The research
preview additionally uses explicitly installed readers; see the
[engine installation instructions](../engine/README.md). This workstation has
both pinned population readers and the fixed Qwen runtime. The separate
**Practice ToMpathy with Clef.cmd** launcher selects the installed CPU Clef-flash
for technique questions; fixed Qwen still handles goals and corrections. Close
the older ToMpathy review Chrome before switching launchers. See the
[Clef measurements and limits](CLEF_LOCAL.md). No analysis silently downloads a model.

Research preview is on by default in Options. Each panel identifies the preview;
open its module-status disclosure for completed, skipped and unavailable modules.
Choose **Load cached real preview** for a previously completed exact-input run,
including a partially completed run. The saved timestamp and missing-module
statuses remain visible. The Global tab contains the supplied historical
population comparison; it does not supply numerical drive priors.

While reading, small words and pie indicators appear beside the bottom menu.
They count completed passages, judgments or scoring calls; they do not estimate
accuracy. Completed work briefly shows a check and fades. The teardrop reserves
space for source groups so new judgments can arrive without reshaping it. Empty
space remains unknown. Select a source passage before starting a reading to give
it priority while preserving its original context.

If the time budget expires or you cancel, use **Continue reading** beside the
menu. Completed exact calls and scoring windows are reused. The existing picture
stays visible while replay catches up. A failed module remains explicitly failed;
inspect its disclosure and retry from the menu after resolving its cause.

## Prepared full-essay review

A newer fixed-Qwen refresh is currently running after seven fresh constructed
batteries in an allocated CPU slot. It is **not complete yet**. See the
[run record](CPU_REFRESH_2026-10-17.md) for exact input, coverage limits and the
post-completion review path. The earlier Clef reading below predates this refresh
and subsequent engine changes; matching engine/capture identities are required.

The public [art essay](https://abrahamhaskins.org/art/) has a refreshed real Clef
backup, saved **17 October, 07:04 Pacific**, matching the current engine. It covers
the full captured prose (15,602 words across 328 passages). Equation-rendering
placeholders are excluded; mathematical notation is not scored by the prose reader.

1. Close an older ToMpathy review Chrome session, run **Practice ToMpathy with
   Clef.cmd**, then **Connect local engine** if needed. Startup loads the isolated
   CPU service; the cached action itself does not run inference.
2. Leave **Follow pages** off for this cached walkthrough. Open the art essay
   and click ToMpathy's toolbar icon once.
3. In the reader menu, keep **Research preview** on and choose **Load cached
   real preview**. Accept the revision if another reading is already displayed.
4. Open **Research preview** in Current attention to inspect the two-reader
   comparison. Expand **Both readers**, **Qwen only** or **Smol only** and click
   a passage to locate it on the page. The disclosure includes the cache time.
5. Enable **Follow pages** when ready to try new pages. Chrome needs the one-time
   site-access grant; subsequent navigation reads automatically while the panel
   is open. If an analysis is running, Cancel before choosing the cached action.

This backup contains complete habits, departures and reader comparison. Clef
completed its bounded first 20 passages, producing 100 technique answers in
16.9 minutes of CPU preparation. This is not technique coverage of all 328
passages. Seven of 21 goal groups are available, with no governing cover;
58 of 909 sentences have comparable payoff scores. Both stages are explicitly
partial. Values remain unknown. **Continue reading** requests more bounded CPU
work; it is unnecessary for the cached walkthrough.
The comparison reports decreased agreement with more context, not convergence.
Edited or expanded page text needs a new exact-revision reading. Cached loading
does not rerun models or refresh source history.

The native Chrome 155 check loaded this backup in **0.88 seconds**, selected a
comparison passage on the source, and verified the panel's layout and cache
timestamp. All 100 Clef answers were verified in the technique disclosure with
their unvalidated labels. Screenshots were inspected. The earlier Follow pages regression
covered a blog and the essay without a second toolbar click; it was not repeated
in this focused cache check. First-use permission bubbles remain a manual check. See
[driver measurements and remaining gates](DRIVER_IMPLEMENTATION.md).

The ordinary **Practice ToMpathy.cmd** launcher also has a matching refreshed
backup, saved **17 October, 07:00 Pacific** and verified at 0.85 seconds to load.
It uses fixed Qwen's separate 26/100 completed technique checks, seven goal
groups and 52/909 payoff sentences. Both launchers have complete habits,
departures and comparison; each loads the cache for its own backend identity.

Options offers explicit GitHub file history on public `github.com/.../blob/...`
pages, a history-record limit and an optional token held only in panel memory.
Editor names remain pseudonymous unless revealed locally. Personal preview
readings cannot be exported. Toggle preview off to use the admitted path.

## Use it

1. On the practice page, click **Connect local engine** and allow its local
   connection if Chrome asks. The launcher supplies an extension-private token;
   it never places the token in a URL, page text or exported reading.
2. Start with [Sneckdown](https://en.wikipedia.org/wiki/Sneckdown), then try
   [Desire path](https://en.wikipedia.org/wiki/Desire_path). These are live public
   articles, not copied fixtures. Their lengths and revision counts can change.
3. Click ToMpathy's toolbar icon, or press **Alt+Shift+Y**. The source page remains
   live beside Chrome's native reader.
4. Enable **Follow pages** on the practice page and allow Chrome's site-access
   prompt. While the panel is open, new active webpages are captured and analyzed
   automatically. Wikipedia readings fetch up to 20 public revisions; other
   pages receive a final-text capture reading. Progress and Cancel appear in the
   panel. Without this option, use **Analyze capture** or **Analyze Wikipedia
   history** manually. Turn automatic reading off in the reader menu.
5. Choose a contributor at the top, then open a recorded revision or correction
   in the middle panel. Inspect its timestamp, source and before/after evidence.
   Exact matching passages can connect to the current page. Wikitext and deleted
   text do not always have a surviving rendered-page anchor.
6. Use **Load cached real preview** to revisit an exact earlier engine run.
   Personal preview readings stay local and cannot be exported. A later analysis
   proposes a revision instead of silently replacing the current one.

The Review desk also links to the practice page. For a separately started
companion, **Options → Analysis source** still accepts its URL and token.
**Check saved connection** reports whether history analysis and admitted modules
are available, without sending a capture. Restarting practice may choose a new
port; the launcher restores a previously selected practice connection. First
connections and other configured providers still require Connect. If the engine
is offline, run Practice ToMpathy.cmd again, then Retry reading. The ordinary
Review launcher opens the UI but does not start an engine.

Unreadable pages offer a bundled safe example and Paste a text. The example has
authored fictional interpretations for interaction practice and needs no engine.
A genuinely blank page keeps the quiet “Start with a piece of writing” opener.
Chrome's internal/protected pages remain unreadable even with Follow pages on.

## What the result means

This exercises the actual capture → authenticated service → local models and
optional public history → packet → interactive reader path. Preview runs the
installed models and labels their hypotheses. It never creates scientific
admissions or reuses the fictional interpretations on the commissioned website
demo. Follow pages uses the engine on that website too.

Preview off retains the admitted path: inferred modules remain absent when their
validated inputs and model admissions are unavailable. Personal values stay
unknown in preview too; no numerical seven-drive prior has been supplied. An
empty value panel is therefore expected. Article subjects and editor names do
not establish a person's motives or identity across sources. The Global view can show supplied
domain summaries; it does not invent a population value profile.

The launcher stores its token, connection metadata and immutable history
snapshots under the ignored Chrome review profile's `tompathy-engine` directory.
Only the chosen public article is fetched. The service listens on `127.0.0.1`,
requires the token and allows the exact installed extension origin. Nothing is
hosted or uploaded. An existing companion from this same launcher is reused;
a different running build must be stopped by closing its review Chrome before restart.

`npm run test:practice` is the opt-in live check: it uses one disposable ordinary
Chrome profile, exercises the same launcher and real public pages, writes receipts
under ignored `evidence/`, and cleans up its own browser and companion. It is
separate from deterministic browser tests and scientific performance acceptance.
The test configures loopback access through Chrome's extension settings; the
first-use native permission confirmation remains a manual check.

`npm run test:follow` uses constructed cross-origin pages plus live Sneckdown to
check automatic navigation, new tabs, text updates, cancellation, disabled
following, protected pages, empty pages and offline recovery in the native panel.
It grants optional sites through Chrome's extension-settings API in its disposable
profile, then exercises the actual opt-in controls. `npm run test:practice-lifecycle`
checks startup-command exit, owned-browser shutdown and connection restoration.

## Verification on 15 October 2026

Ordinary Chrome 155 exercised both articles through the real companion and native
side panel, including contributor labels, correction evidence and saved-connection
checks, with zero page errors. Sneckdown supplied 14 captured passages / 235 words
and 119 recorded events from 16 source contributors. Desire path supplied 24
passages / 899 words and 60 events from 15 contributors. These counts describe the
bounded snapshots, not each article's entire history.

The affected checks passed: 35 core tests, four Python service tests, two built
extension integration tests, TypeScript/build and targeted stream-parser reruns.
Screenshots were visually inspected. The live check initially exposed a clipped
summary and a contributor label falling back to the page byline; both were fixed.
The complete inferred-reading scientific and timing gates remain separate.

The follow-up native-panel regression passed all ten navigation/recovery checks
with zero page errors. Its first runs exposed an asynchronous off-switch update
and a distinction between inaccessible browser tabs and accessible empty pages.
The final check also verifies that source changes cancel an older reading. The
separate companion lifecycle check passed all three startup/restart/shutdown
checks, with no dependency on keeping the initial terminal command alive.
