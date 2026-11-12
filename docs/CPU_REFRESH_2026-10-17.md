# Fresh battery and full-art preparation

Started 17 October 2026 at 14:34 Pacific. Updated October 18: all seven batteries
finished; the first job saved a partial art reading and exited at 19:39 Pacific
on October 17. The remaining analysis is awaiting shared memory headroom. Original
receipts remain in `.local/engine-cpu-20261017/`; continuation receipts are in
`.local/engine-cpu-20261018-art-continuation/`.

## Coordination and bounds

ToMpathy atomically claimed slot 0 through Sounding Line's existing counted CPU
slot protocol. Direct chat messages failed because the destination had an active
writer; the shared slot receipt is the actual resource coordination mechanism.
No research job, GPU allocation, study, code or running service was changed.

The job owns a pinned Qwen 3.5 9B / Ollama 0.40.3 service. It uses one numerical
CPU thread, below-normal priority, and runs Q8, Q9, Q5, Q1, Q3, Q4, Q7 serially
(200 constructed items each), then prepares the captured art essay. Exact calls
and question receipts are saved. Initial RAM and commit headroom must exceed
24 GiB; monitoring stops this owned job below 16 GiB RAM/commit or 20 GiB disk.
Session runtime is bounded at 48 hours, art preparation at 24 hours. A `STOP`
file in the run directory requests shutdown. `owner.json` records native PID and
creation identity; no cleanup may use broad process-name matching.

## Exact input and limits

Capture: 15,602 words, 328 passages, captured at 21:33 UTC. Revision:
`08d9b05c4935b67c9228a31e3f36a8442430d7b175e6d7c4018c5213b1b97a69`.
The immutable run copy is `capture.json`. Later website edits require a matching
new capture; mismatches must not silently reuse this reading.

Battery pin:
`d45889455cfc6623bd323cf87e08c03fadc5824a67a3a33892468932e3234bf3`.
Original thresholds and per-label/family controls are retained. Failed questions
remain disabled. Passing constructed tests do not establish natural-data accuracy.

Full-essay preparation feeds the whole capture to the existing bounded modules.
Reader scoring retains its windows. Goals have at most 21 calls and omit oversized
serialized groups. Techniques inspect at most 20 passages / 100 checks. Report
actual coverage and skipped, failed or unavailable modules on completion.

## Completion and review

1. Inspect `complete.json` or `failed.json`, question receipts, `art-refresh.json`,
   resource heartbeat and native ownership. A process being alive is not success.
2. The art stage installs all seven receipts in
   `.local/engine-question-admissions/` with hashes and a final completion marker.
   Practice validates that manifest. Gate changes alter preview-cache identity;
   exact raw calls can still be reused when model and input pins match.
3. `art-refresh.json` must confirm normal companion cache replay for this capture.
   Inspect module statuses before claiming a complete reading.
4. Close older ToMpathy review Chrome windows, use **Practice ToMpathy.cmd**, connect,
   open the matching art page, then choose **Load cached real preview**. This is
   the fixed-Qwen path. The Clef launcher has a different technique identity and
   does not automatically share this completed packet.
5. Report measured question results and actual module coverage; update this record
   and the practice guide. Verify the owned service exited and its slot was
   released. Never terminate foreign research processes.

At 14:54 Pacific, Q8 had attempted 66/200 items without a session error, with
approximately 38 GiB RAM / 33 GiB commit headroom. At that early rate, seven
batteries could take about seven hours; later questions and art preparation may
differ substantially. This is a forecast, not a completion guarantee. The next
useful check is before the first question finishes, then at estimated phase
boundaries rather than frequent model polling.

At 15:27 Pacific, Q8 completed all 200 constructed cases in 3,193 seconds with
validity and exact-answer accuracy both 1.0, meeting its unchanged lab thresholds.
Its receipt explicitly limits the scope to templated items; scientific admission
remains false. Q9 reached 23/200 at 15:33, with the serial job and resource
heartbeat healthy. The other questions and art refresh remain unfinished.

At 16:07 Pacific, Q9 completed 200 constructed cases in 2,366 seconds. All
responses were valid, but overall accuracy was 0.88, “no” accuracy 0.76 and
family-1 accuracy 0.52. Its unchanged gates failed; it remains disabled. This is
a measured limitation, not a runtime crash or a reason to weaken thresholds.
The serial queue continued to Q5, which reached 76/200 at 16:25. Resource
headroom remained above the configured floors. The art refresh is still pending.

## October 18 verification and continuation

The original supervisor, session and owned model service have exited. Its lease
was released; slot 0 is now owned by another research card and was left alone.
All seven installed receipt hashes match the completed run.

| Question | Cases | Valid | Accuracy | Constructed gate |
| --- | ---: | ---: | ---: | --- |
| Q1 | 200 | 100% | 100% | Pass |
| Q3 | 200 | 100% | 100% | Pass |
| Q4 | 200 | 100% | 100% | Pass |
| Q5 | 200 | 100% | 100% | Pass |
| Q7 | 200 | 100% | 100% | Pass |
| Q8 | 200 | 100% | 100% | Pass |
| Q9 | 200 | 100% | 88% | Disabled |

The October 17 19:39 cache replays through the normal companion path. It contains
complete habits and deviation (328/328 passages), but only 64/1,312 reader
comparison steps, 309/3,636 payoff calls, 15/100 technique checks and 1/21 goal
groups. Values remain unavailable. These are coverage counts, not accuracy.

The offline script incorrectly treated successful partial-cache responses as
finished preparation. The repaired script continues bounded companion passes,
reusing exact saved calls/windows, until every available module is complete.
Failed modules stop preparation for inspection; an owner stop and the 24-hour
preparation bound remain enforced. Cache replay is verified before a final
`availableModulesComplete` receipt is written. Five targeted software tests
passed, including partial continuation, failure, cancellation and normal-budget
cache compatibility; Ruff passed. No model, stage limit or research gate changed.

At 06:59 Pacific on October 18 the new supervisor claimed slot 1 and began the
continuation. It copies the exact capture and completed question receipts,
checks their pins and skips the finished batteries. It uses the existing shared
runtime for the slot protocol and the project engine environment for analysis.
Initial RAM/commit headroom was about 36/30 GiB. The old partial cache remains
available while preparation progresses. Completion of the bounded modules is
still not all-passage technique coverage or scientific admission.

At 07:00:48 Pacific the shared-resource guard stopped the continuation after its
memory floor was reached. The supervisor, child session and dedicated model
process all exited; slot 1 was released and has since been claimed by another
research card. No foreign process was stopped. Saved calls and the prior cache
remain. A later checkpoint will require additional headroom before resuming;
this is a preparation pause, not a finished full reading.

At 15:35 Pacific on October 18, available RAM was 30.8 GiB and commit headroom
17.6 GiB. Continuation was not restarted. The shared reservation requested in
Sounding Line's week packet is now at
`../SoundingLine/sounding-line/results/tompathy-demo-prep.lock`, alongside
`results/.cpu-slots-20261017`. Its reservation ID is
`tompathy-demo-prep-20261018`; it expires October 20 at 20:00 Pacific or on
confirmed completion. It reserves capacity without changing running jobs.

The stable completion receipt is `.local/engine-art-ready.json`. The preparation
script writes it only with `availableModulesComplete: true`,
`cacheReplayVerified: true`, the actual run directory and saved packet hash.
There is no such success receipt yet. The per-run `art-refresh.json` remains.
Check and remove only the matching reservation at completion/expiry; never
remove a counted lease belonging to another job.

Packet 1.10 may require packet-cache reconstruction, but existing exact model
calls/windows retain their frozen identities and remain reusable. All seven
batteries remain completed; Q9 remains disabled. A 16:15 Pacific checkpoint was
scheduled in the existing automation. Its execution has not yet been observed.

## October 26 isolated-runtime recovery

The 03:35 Pacific checkpoint found 70.8 GiB available RAM and 72.4 GiB commit
headroom, exceeding the required 32/32 GiB restart floor. No ToMpathy preparation
worker was running, and the old expired reservation marker was absent. No foreign
lease or process was changed. Startup now enforces that 32/32 GiB floor directly;
the existing running-job 16/16 GiB and 20 GiB disk floors remain unchanged.

The first fresh continuation, `.local/engine-cpu-20261026-art-continuation`, failed
before inference: desktop Ollama had advanced to **0.40.11**, while the existing
receipts require **0.40.3**. The exact supervisor/session identities exited and
slot 0 was released. That failed attempt is retained, with its logs and receipts.
No battery was rerun and no runtime/model gate was loosened.

The bounded repair uses the [official Ollama 0.40.3 portable release](https://github.com/ollama/ollama/releases/tag/v0.40.3), isolated in
`.local/runtimes/ollama-0.40.3/`. The complete Windows AMD64 archive matches the
published SHA-256 `e5ecff02dfc7cae8ddf6d6b7a7ac5f727ffeedf4491f44ae75ff5b0820dbbbd5`.
Its local receipt records source, digest and destination. The launcher now prefers
this isolated runtime when present, retaining the explicit environment override
and exact version/digest checks. Desktop Ollama and existing model weights were
left unchanged. The mismatch diagnostic now includes the observed version.

At **03:42 Pacific**, `.local/engine-cpu-20261026-art-resume-pinned` claimed slot 0
and started the dedicated CPU service successfully. Initial headroom was 68.7 GiB
RAM / 69.9 GiB commit. It reuses the exact 328-passage capture and all seven
byte-verified question receipts; Q9 remains disabled. It uses one CPU thread and
below-normal priority. The original raw-call and window caches remain in place.
The supervisor's native identity, session identity, service and lease are recorded
inside this run. No full-art success receipt exists yet.

The next checkpoint is **04:10 Pacific on October 26**, to inspect initial bounded
continuation outputs and derive the next estimate from actual module counts.
Scheduling was confirmed by the automation tool; delivery at that time is not yet
verified. Full completion remains uncertain and may take hours. No new scientific
admission or research study was performed.

## October 26 offline time-budget repair

The 04:10 Pacific checkpoint was delivered. The saved fifth pass showed habits
and deviation complete, agreement 394/1,312, payoff 371/3,636 and techniques
43/100. Resources were healthy. Inspection identified an engineering defect:
although offline passes allowed 600 seconds overall, they still inherited the
**90-second live goal-stage limit**. Long art-group calls previously measured
around 170 seconds could never complete. By the seventh saved pass, goals still
stood at 1/21 while the other modules advanced to 544/1,312, 394/3,636 and 51/100.

The internal offline preparation mode now lets a stage use the existing
600-second overall pass allowance and disables optional-module shedding in that
mode. Ordinary live stage limits, the overall deadline, transport timeout,
model/prompt pins, scientific gates and raw-call/window cache identities are
unchanged. There is no request-body switch for this mode. Rendered packet caches
may reconstruct against the changed implementation. Completion still requires
normal-practice replay and every available module complete.

The slow-call regression demonstrates a constructed 170-second call stopping in
live mode, completing offline, and still stopping at an earlier overall deadline.
The replay check verifies that normal practice loads the completed offline cache.
All **29 targeted preparation/scheduler tests passed**; Ruff and diff checks passed.
A restricted test process stalled; its exact PID, creation identity and unique
scratch path were checked before cleanup, and the mock-only checks passed outside
that restricted environment. No inference tests or gates were substituted.

The previous preparation was stopped through its verified supervisor at 04:18;
its supervisor, session, art worker and dedicated model service exited, and slot 0
was released. Exact saved calls and all receipts remain. The fresh continuation
`.local/engine-cpu-20261026-art-offline-budget` started at **04:19 Pacific** with
66.9 GiB RAM / 62.8 GiB commit headroom and a ready dedicated pinned service.
There remains only one preparation job, on one CPU thread at below-normal priority.

Next checkpoint: **04:55 Pacific on October 26**. Inspect the first few bounded
passes, especially whether goals progress beyond 1/21, before estimating completion.
The replacement checkpoint is scheduled; its future delivery is unverified. The
full cache is not ready, and no new scientific admission has been made.

At the delivered **04:55 Pacific** checkpoint, the third saved continuation pass
(04:49) had advanced goal progress to **9/21**, beyond the previous 1/21 stall.
That pass spent about 597 seconds in goals; its other counters were partway
through packet reconstruction. They do not measure how much raw work is already
cached. The heartbeat was fresh with 53.1 GiB RAM / 45.3 GiB commit headroom.
Neither a failure nor a full-art readiness receipt existed. The healthy run was
left running, with no restart or additional model job.

The next checkpoint is **05:30 Pacific**. The recent rate suggests another
30–50 minutes for goal processing, with uncertainty for long groups and the
governing call; the other modules still prevent a reliable full-cache ETA.
The replacement checkpoint was scheduled; its future delivery is not yet verified.

At the delivered **05:30 Pacific** checkpoint, attempt 7 (saved 05:29) showed
goal progress **20/21**, after 4,207 seconds in the repaired run. The remaining
goal step and other modules were still pending. The heartbeat was fresh with
52.6 GiB RAM / 44.8 GiB commit headroom; no failure or readiness receipt existed.
The job was left running unchanged. Next checkpoint: **06:05 Pacific**, to inspect
the goal-stage transition and measure the remaining modules before forecasting
full completion. That checkpoint is scheduled; future delivery remains unverified.

## October 26 governing-goal diagnostic

The **06:05 Pacific** checkpoint was delivered. The offline-budget run had
failed at **05:39:47**, after its eighth pass reached **20/21** goal steps.
The final governing-cover call was rejected before parsing or caching because
its completion was unfinished or unexpectedly included thinking. The old error
did not distinguish these cases. Output truncation is a hypothesis, not an
established diagnosis. All saved exact calls and partial packets remain.

The prior supervisor, session, art worker and dedicated model service were
verified absent, and their slot 0 lease had been released. No foreign process or
lease was touched. A bounded diagnostic improvement now reports only a safe
completion-reason category, output-token count and thinking-present flag. It
never logs generated prose or thinking, and still rejects the same responses.
Two mocked rejection tests passed; Ruff and diff checks passed. No prompts,
output budgets, reader/model pins, scientific gates or cache identities changed.

One unchanged-pin retry started at **06:14 Pacific** in
`.local/engine-cpu-20261026-art-goal-diagnostic`. The exact capture and all seven
receipt files were hash-verified before copying to the fresh run. Initial
headroom was **65.3 GiB RAM / 59.9 GiB commit**. The native supervisor and session
are recorded in its owner receipt; its dedicated service is ready. It claims
one counted slot and uses one CPU thread at below-normal priority.

The next checkpoint is **06:25 Pacific**, around the single long governing-call
and 600-second pass boundary. This is a diagnostic checkpoint, not a full-cache
completion forecast. Scheduling was confirmed; future delivery is unverified.
If the same rejection recurs, do not repeatedly retry it or silently increase
the pinned output budget. Preserve the evidence and ask the owner about a
separately pinned goal-generation repair. Available modules must still actually
complete and normal replay must pass before a readiness receipt can be written.

## October 26 confirmed output-limit blocker

The **06:25 Pacific** checkpoint was delivered. The one permitted diagnostic
retry failed at **06:24:43**, with the exact transport diagnostic
`done_reason=length, output_tokens=256, thinking=False`. This establishes that
the final governing response hit its output limit; it was not unexpected
thinking. The goal stage spent 482.8 seconds and retained **20/21** steps.
No full-art readiness receipt exists. The last heartbeat had 52.8 GiB RAM and
44.0 GiB commit headroom, so this was not a resource-floor stop.

The supervisor (51380), session (55496), service (55844), launcher (56688), and
any ToMpathy preparation worker were absent at the ownership check. The exact
slot-0 lease was absent. No foreign process or lease was changed. All previous
runs, the matching capture and exact cached work are retained. Current-pass
counts for other modules reflect packet reconstruction and do not measure all
previous raw work; those modules must still finish before full readiness.

No repeat was started. The checkpoint explicitly forbids changing prompts or
model settings, so the following repair is **proposed, not implemented**:

- Give only the final governing judgment a separately versioned call identity.
  Keep the 20 local-goal cache keys and fixed literal-reader identity intact.
- Replace verbose node/cue identifiers in that one model exchange with compact,
  deterministic aliases, validated and mapped back to the original evidence IDs.
  Do not drop evidence, accept unknown IDs or change the actual graph IDs.
- Give that response an explicit bounded allowance sized for its schema and
  retain the existing context guard, CPU resource floors, completion rejection,
  overall pass deadline and unvalidated goal status. A larger allowance alone
  may worsen runtime; the compact representation addresses avoidable output.
- Check alias round trips, unknown/duplicate reference rejection, separate cache
  keys, unchanged literal-reader pins/receipt hashes, strict truncation rejection
  and ordinary-practice replay compatibility before one CPU resumption. Do not
  rerun research batteries or transfer their badges to this new goal variant.

Owner authorization is required before this configuration/schema change and
resumption. The automated retry checkpoint was deleted after the tool confirmed removal,
rather than waking repeatedly on a known blocker. Saved work remains available, and Q9 stays disabled.
