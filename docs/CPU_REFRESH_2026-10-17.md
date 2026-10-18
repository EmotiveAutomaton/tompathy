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
