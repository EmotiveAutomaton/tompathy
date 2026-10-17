# Local CPU performance

These are measurements from saved local receipts on the demo workstation, not
research admission or guarantees. Previous runs used the preceding October 17
implementation; the new context guard and goal-cover prompt invalidate old goal
and literal-call identities. No GPU was used for this pass.

| Stage | Measured result | Scope and caveat |
|---|---|---|
| Qwen2.5-0.5B departure map | 14.44 s model load + 64.23 s scoring | Earlier 3,000-word manuscript; dynamic int8, one CPU thread; not the current full art essay |
| Full art essay, two-reader preparation | 41.32 s total | Cached token-loss replay, 1,565 Qwen cache hits and 1,237 Smol cache hits; **zero forward calls** |
| Qwen load during that replay | 15.37 s | One thread; not cold scoring throughput |
| SmolLM2-360M load during that replay | 7.38 s | One thread; cold scoring time not separately recorded |
| Clef-flash full-art technique pass | 1,013.01 s for 20 completed decisions | 50.65 s/decision including transport; preceding configuration, unadmitted |
| Qwen 3.5 9B full-art local goals | 7 completed calls in 1,200.65 s, then budget stop | Partial only; prompt evaluation 956.49 s, generation 210.23 s, load 6.91 s |
| Earlier short-timeout goal attempt | 113.44 s; no completed call | ReadTimeout; not counted as successful preparation |
| Q1/Q3/Q4/Q5/Q7/Q8/Q9 with new gate | Pending | Fresh per-question measurements come from the serial battery runner; no fabricated estimate |
| Wikipedia history fetch, Haiku | 1.02 s, 20 revisions | Current live request, cached locally for practice; no suppressed rows |
| Wikipedia history fetch, Clerihew | 0.89 s, 20 revisions | Current live request, cached locally for practice; no suppressed rows |

Local source receipts: `evidence/preview-cpu-int8-benchmark.json`,
`evidence/art-preparation-readers.json`, `evidence/art-preparation-clef.json`,
`evidence/art-preparation-goals.json`, and
`evidence/art-preparation-goals-timeout.json`. Current history measurements are
in `evidence/history-performance-2026-10-17.json`. An initial Six-word story
candidate failed article resolution and was not cached; Clerihew replaced it.
These receipts are ignored local evidence,
not bundled data or a public benchmark dataset.

The measured bottleneck in the goal preparation is prompt evaluation, not model
loading. Keeping the model warm helps repeated calls but does not make the long
essay fit a two-minute live budget. Exact caching, smaller initial groups,
incremental publication, explicit pause/continue, and optional-stage shedding
remain necessary. Clef-flash's local measured rate is also too slow to describe
as instant feedback on this configuration.

Budget misses remove optional work in the packet's prescribed order: payoff
layer 2, second reader, technique regions beyond 30, then the governing goal
call. Completed local candidates and validated findings survive. Technique
notes currently consider at most 20 regions. The 135M reader fallback is
supported when explicitly installed; it is never silently downloaded or
presented as the 360M model.
