# ToMpathy vertical-slice review — 23 October 2026

## What changed

Core values now uses a plain list with fine leaders extending to broader levels
in the teardrop. The article geometry comes from Expertise, including tier
resizing. The larger sideways silhouette appears behind it as you zoom out.
The list scrolls independently, so a long list cannot push the entire graph off
screen. Only visible rows draw leaders. Labels retain mouse and keyboard access
to the existing diagrams and observation vectors. The nested fictional timeline
has been removed.

The safe example's connections and larger silhouette are authored illustrations.
Real connections require an explicit value-view feed and shared evidence. Missing
personal estimates remain missing; the new display does not create a biography,
measurement, population model or personal-value inference. Essay text and assets
are unchanged.

A real context defect was fixed: the combined “All makers” view could pass its
UI label to the context collector as if it were an author name. With exactly one
page-supplied author, it now retains that byline for context. It does not choose
among multiple named people. Attribution stays page-supplied and unselected for
analysis until the user selects it.

The [Sounding Line uptake note](SOUNDING_LINE_UPTAKE_2026-10-23.md) records all
11 verified file hashes, 21 channel-source mappings and the scoped EV1/EV2/EV3
summaries now shown in Global research. No scientific admission was added.

## Review paths

1. Close any older ToMpathy review Chrome before switching modes. Leave your
   regular browser and research processes alone.
2. Run `npm run practice:light` from this checkout. Connect the engine and enable
   Follow pages on the practice page. Open the native ToMpathy panel once.
3. Visit [Relax for the same result](https://sive.rs/relax). The article is 440
   captured words in 15 passages; the comments are excluded. A matching complete
   surface-reading cache is available locally. Ordinary navigation also reuses
   exact scoring calls. These observations are for this one page, not all blogs.
4. Enable Light context in the reader menu. Inspect the page-supplied Derek Sivers
   byline in the context timeline. This page has no supported explicit author
   profile link; identity search and invented cross-work history are not used.
5. Hover and click article sentences. The panel should follow and hold the same
   sentence. Release it, inspect attention, and open the module status. Use
   Continue reading if a new page reaches its scoring budget.
6. Open the bundled safe example to review the new values design. Compare the
   three tabs, use minus/reset/plus, scroll the value labels, and hover/focus CARE
   to inspect its sleeve and three observation vectors. The example supplies the
   illustrative values that the live blog cannot justify.
7. Visit Global on the live reading to inspect the new research summaries and
   source links. EV3 explicitly carries its failed-control warning.

`practice:light` uses the installed Qwen2.5-0.5B and SmolLM2-360M readers on one CPU
thread. It does not load fixed Qwen 9B or Clef. Goals and techniques remain
unavailable in this mode, and final text does not admit personal core values.
The ordinary `npm run practice` path is still available when sufficient memory
is available for its larger judgment model. Mode changes cannot silently reuse
the other mode's companion.

## Measured behavior and limits

The native test uses Chrome 155.0.8059.85, an isolated profile, an authenticated
local companion and a counted CPU slot with resource monitoring. The browser and
owned services close and the slot releases afterward. No GPU or research job is
borrowed. First-use native permission confirmation remains a manual user action;
the test granted permissions through Chrome's extension settings, then exercised
the actual Connect and Follow pages controls.

The final native run used build **3e728762a508** and a fresh isolated scoring
cache, with installed weights (no download). Startup took 28.7 seconds. Once the
companion was ready:

| Step | Observed time / coverage |
|---|---|
| Capture | 0.789 s; 440 words, 15 article passages, no reader comments |
| First visible reading | 1.0 s from navigation, including the context-setting action |
| First pass | 83.884 s; attention 15/15, reader comparison 60/60, payoff 131/324 |
| First Continue reading | 61.121 s; payoff advanced to 271/324 |
| Second Continue reading | 18.385 s; payoff finished 324/324 |
| Direct complete-packet cache replay | 0.030 s |

All available lightweight modules completed in about 163 seconds of analysis
across the three passes. Goals, techniques and values remained explicitly
unavailable. All 15 passages were marked; clicking the first sentence synchronized
the page and panel lock. Light context retained Derek Sivers's page-supplied
byline, unselected for analysis. The panel had no console or page errors.

A separate warm native run rebuilt the complete reading from exact scoring calls
in 5.22 seconds. Packet replay and exact-call reconstruction are different paths.
The earlier partial run is retained as diagnostic evidence, not a cold benchmark.
These timings measure software execution, not accuracy or research admission.

A first full-model attempt timed out during companion startup; its retry reached
live capture but the supervisor stopped the owned test tree at the shared resource
floor. The large goal/technique model therefore has no successful full-page result
in this pass. Both failed attempts were cleaned up; the ordinary review browser
and other projects were untouched.

The full art essay cache remains partial: `.local/engine-art-ready.json` is absent.
This smaller blog preparation does not imply completion of that separate job.

## Improvements, in order of impact

1. **Make full judgment-model startup fit the available memory.** The smaller
   readers are usable now, but goals and techniques need a successful reserved
   run of the larger model or a separately evaluated smaller replacement.
2. **Reduce payoff work before the first useful pass.** It dominates the scoring
   time even for 440 words. Exact caching and continuation work; a bounded initial
   subset or explicit on-demand payoff is the next product tradeoff to evaluate.
3. **Compact the live research explanations.** Repeated notices and vocabulary
   consume substantial space, especially when no goal hierarchy is available.
   Keep one clear preview notice and accessible detailed limits without crowding
   the graph. The overlapping provenance label was repaired in this pass.
4. **Make context coverage clearer.** A byline is useful evidence, but it does
   not itself provide a profile or history. The UI should make the difference
   between “no explicit link” and a retrieval failure easy to see.

## Verification

Build, 46 existing core checks plus the new sole-byline regression, 22 focused
engine checks (including receiving integrity and refusal to admit page claims),
and seven focused browser cases passed. Native evidence is in
`evidence/vertical-slice-blog.json`, with the earlier warm and partial runs kept
separately. The test scripts are `scripts/vertical-slice-validation.mjs` and its
counted supervisor `scripts/vertical-slice-job.py`. Source diagnostics, not raw
participant data, are retained. No commits, pushes or deployments were performed.
