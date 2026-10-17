# Fresh battery and full-art preparation

Started 17 October 2026 at 14:34 Pacific. Current state: running, not a completed
measurement or refreshed reading. Receipts are in `.local/engine-cpu-20261017/`.

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
