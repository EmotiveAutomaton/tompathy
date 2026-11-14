# November two-day engine implementation

Working record for `TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-12.md`.
Started November 13. The available implementation is built and checked; the long CPU
benchmarks are not complete. No production admission or default has changed.

## Received data

- **EX1:** all 1,399 sessions from 61 writers replayed to the exact exported NFC
  hashes; no session exclusions. 594,195 exact word-span matches, 22 unmatched
  exported spans and 11 unmatched engine spans. Unsupported timing stays null;
  labels never move to different words. 50,107 typed words lack supported timing;
  1,080 engine words have unknown source. These cannot supply a stop outcome or
  a source-pure involvement sentence, respectively.
- **EX2:** the unchanged engine hunk rule retains 1,692 of 5,000 edits. Missing
  feature vectors/editor identities were recovered read-only from the export's
  hash-bound producer checkpoints. All selected before/after text, labels, folds
  and source metadata matched. The 1,692 retained rows have their original 20
  features; 1,127 recovered editors remain fold-disjoint. No wider source study
  or refit was used for recovery. Original per-edit feature-generation timing is
  absent, so cascade speed cannot qualify even when accuracy can be measured.
- **EX3:** exact Git objects and byte hashes reconstruct the fixed 20-PEP/20-EIP
  pilot and its 715 distinct candidate documents. Abstract/Simple Summary
  subtrees are additionally excluded from the engine query. The original
  preparation is retained; corrected goals are in `two-day-prepared-v2`.
- **EX4/EX5:** absent at intake. CP1/EX6 remains dependency-gated. Receipt of data
  grants no scientific admission. New pilot rows have no ledger admission row.

## Paths and measurement state

| Item | Implemented path | Current measurement state |
|---|---|---|
| TP2 / TP5 | Exact-pin per-session resumption; registered float32 window; float32 KV binding; independent Smol primary; V1/V2/V3/V5; K=0/1/2/4/8/16 history ladder | Window/KV/Smol complete; history not started after resource stop |
| TP3 | Recovered feature bank; original nested folds; first-50 Q8 projection; remaining calls require less than six projected hours; paired cascade accuracy | Feature complete; Q8 resource-stopped at 472/1,000; partial aggregate preserved; cascade timing qualification unavailable |
| TP4 | Existing three goal readers; candidate-only TF-IDF; top-five reranking from the same body-goal call, with no candidates in its prompt; eight-hour limit | TF-IDF baseline complete; goal judgments memory-blocked before loading |
| TP1b | Local W1 conversion; ordered vocabulary, numerical, prefix, timing and TP2 gates; serving refuses any pending/failed gate | a-e complete; final accuracy difference +0.0000071 passed; speed target missed; separate first-paint timing complete |
| TP6 | Quotas; one-pass loss/entropy/log-probability variance; raw/normalized attacks; hash calibration split; Wilson rate intervals | All 2,500 inputs prepared; scoring running |
| TP7 | EX5 receiving contract; B0–B5/E1 controls; best-rarity comparison with site-stratified paired resampling; optional E2 | Waiting for actual EX5 format/data |
| TP9 | Fixed intention mapping; abstentions as errors; balanced 300; majority and EX2-only deterministic-feature control | Inputs prepared; calls queued |
| TS1 | Strict empty `bottom-box-0`; explicit `analyze --bottom-box`; no producer | Implemented; contract and existing frontend schema checks pass |

The history ladder retains the original 1,024-token cap and 512-token minimum.
Selecting sixteen sessions does not retain sixteen full documents. Counts and
cohorts are explicit; exploratory rows cannot replace a registered primary.
The human feature control excludes IteraTeR-trained intent sidecars to honor the
EX2-only training constraint. It is separately named, not a claim of identical
features to the fuller TP3 classifier.

TS1 is omitted by default. The ordinary frontend schema can ignore this optional
extension; live preview rejects it until its stricter contract is extended.
There are no frontend source changes or inferred bottom-box values.

## Data and runtime pins

[RAID](https://huggingface.co/datasets/liamdugan/raid), MIT training revision
`865cac74188466cb0c3b7574a10204007b57a459`: streamed in file order until all quotas
filled. Retained 800 human, 800 unattacked machine, and 300 each homoglyph,
zero-width-space and paraphrase documents. Scanned 5,139,241 rows and
10,451,746,816 streamed bytes; no full file or fallback download was retained.
Selected rows, IDs and hashes stay in ignored local storage.

[IteraTeR human sentences](https://huggingface.co/datasets/wanyu/IteraTeR_human_sent),
Apache-2.0 revision `e22e0371dac444239b944f9293f5b491d62b73f0`: downloaded the
published train/dev/test and card. Hash selection gives 60 pairs per intention:
243 train, 35 dev and 22 test. Excluded 58 `others` and nine duplicate pairs. Q8
is frozen with no task fitting. Human-trained features must not be tested on
their training rows.

[The authors' non-native essay dataset](https://huggingface.co/datasets/WxWx/ChatGPT-Detector-Bias/blob/main/README.md)
states MIT licensing. Revision `ca6b48c8ce435b4750efc895d3c40bfab8bd7d9a`
provides 91 original human TOEFL essays; polished/generated variants are excluded.
The auxiliary intake pin is
`f8cbfa70209ee168d5bda98bfed287ef6e27f72db00f55d6f0de2224e53bf0b8`.
Their false-alarm rates use the RAID thresholds without fitting on these essays.

Local packages: llama-cpp-python 0.3.36 CPU wheel, datasets 4.4.1, gguf 0.17.1,
sentencepiece 0.2.1, psutil 7.1.3. Converter and bundled GGUF Python definitions
are at llama.cpp `0c1e57098bba43ac29e6e3b677cdceebdd22334f`, the runtime's pinned
submodule. F16 and Q8_0 were converted from the existing model. No model download
or system installation occurred. Exact sources/output hashes remain in the local
conversion record. W2 is not attempted because W1 installed successfully.

**Owner clarification, November 13:** verified unused padding is equivalent in
gate a. All 151,665 assigned token strings/IDs agree. The 271 extra runtime slots
have exact `[PAD<id>]` names, UNUSED-only attributes and the original model's
151,936 output-row count. Both the literal failed preflight and clarified passed
preflight are preserved. Numerical gates and the 0.005 accuracy bound are unchanged.

## Repairs and checks

- Pytest's sandbox temporary directory was unavailable; a fresh project-local
  base directory resolved it. New test error-message/placement mistakes were
  corrected without changing criteria.
- The display sentence regex misses unpunctuated lines. The evaluation parser
  now includes those sentences; frontend/display behavior is unchanged. This
  correction precedes benchmark outcomes.
- Attempt A omitted the required entropy flag. Its own STOP sentinel halted it;
  exit and matching lease release were verified. Its work remains preserved.
  Attempt B uses a fresh frozen package/launcher snapshot and collects V5.
- The converter needed SentencePiece; the pinned local dependency repaired that
  import failure. The vocabulary probe needed explicit `close()` rather than an
  unsupported context manager. Both conversions then finished. These repairs
  were engineering checks, not numerical parity results.
- Final engine suite: **315 passed, one expected outline-confound failure**.
  The initial restricted-sandbox full-suite attempt failed/stalled in subprocess
  fixtures and was stopped; the permitted full rerun completed in 138.65 seconds.
  The 45 targeted two-day/back-half checks also passed. All **14** old/new packet
  fixtures pass the authoritative existing frontend schema. Ruff and the Node
  wrapper syntax check pass. No browser/UI changes require a new visual pass.
- Added known-answer controls for FD variance, partial calibration, rarity
  baselines, abstentions, Q8 projection stops, exact cache hashes, public receipt
  redaction and predecessor-logit alignment. These are software tests only.
- Final shutdown audit: owned-service unload failure now leaves a failed-cleanup
  receipt, even after successful scoring. All 16 pilot checks passed after this
  bounded repair; no real benchmark was repeated.
- At the November 13 23:30 checkpoint, the stopped Q8 receipt exposed a summary
  inconsistency: its top-level two-way score credited raw `unclear` as a
  non-mechanical answer, while the existing paired comparison counted it as an
  error. The live summary now follows that existing rule. Three targeted mocked
  checks and Ruff passed. The corrected partial aggregate was reconstructed from
  exact saved calls, with the original receipt retained and both source and
  aggregation-code pins exported. No model call, prompt or research gate changed;
  all frozen runtime snapshots remain untouched.

## Active run and continuation

Preserved attention run: `.local/bench/two-day-20261113-b`; immutable code/launcher:
`.local/bench/two-day-code-20261113-b`; exact intake:
`.local/bench/two-day-ex1-intake`. It used one counted shared CPU lease, two numerical
threads, below-normal priority, CPU only. Its exit/release are verified; the current
robustness scorer is described below.
Per-session work, resource heartbeats, terminal status and lease release are
saved. Cooperative STOP is checked between blocks.

At 03:58 Pacific on November 13, 75/1,399 initial window sessions were saved.
The observed projection was about 11.2 more hours for that phase, not the whole
packet. RAM/commit headroom was 40.3/15.6 GiB, above this small-reader run's floor
but below the 9B load gate. A later gate failure must retain the saved sessions.

After attention: TP3 features and first 50/projection; TP4; W1 numerical gates
and first paint; RAID; EX5 E1 if received; human edits; optional EX5 E2. A failed
scientific gate stays failed. Preserve stopped attempts. Freeze new code for
subsequent jobs and verify ownership/lease release before another scorer starts.
No publication is queued.

The **19:30 Pacific November 13** checkpoint found a resource stop at 19:28:13:
commit headroom had fallen to 0.704 GiB, below the existing 8 GiB floor. Window,
KV and Smol scoring and aggregates completed; the history ladder had not started.
The supervisor's native PID was absent, its release receipt matched its owner,
and both its exact shared slot and local scoring lock were absent. Prior attempts
and all saved observations remain intact.

At 19:30:58, RAM/commit headroom was 38.46/5.05 GiB, so no replacement job
could start. A sandboxed admission probe also reported a lease identity mismatch;
later native inspection showed sandbox visibility cannot establish identities of
elevated processes. That warning is not a confirmed fault in the foreign lease.
No foreign lease or process was changed. History remains explicitly deferred and
needs an exact-cache continuation plan; completed phases and failed research
gates must not be repeated.

The delivered **21:00 Pacific November 13** checkpoint found 48.63/23.86 GiB
RAM/commit headroom, no counted leases and valid shared admission. The final-v2
code and launcher hashes and all nine package versions matched the frozen
manifest. The edit-feature job completed at 21:01:27; native exit and both matching
lease releases were verified, and its aggregate receipt was landed.

The next serial job, `.local/bench/two-day-tp3-q8`, started at 21:02:55 under the
same frozen package and original queue deadline. It owns its dedicated exact
CPU service and one counted slot. Native scorer, wrapper, model and service
identities were verified through the Python venv launcher ancestry and saved in
`service-owner.json`. The pre-load RAM/commit probe was 48.75/24.08 GiB, passing
the 22 GiB shared reservation requirement as well as the 20 GiB load gate.

The delivered **21:20 Pacific** checkpoint found the first-50 projection at
19,576.841 seconds for 1,000 judgments, about **5 hours 26 minutes**, below the
six-hour continuation limit. All initial inference was timed. This permits the
remaining pilot calls; it establishes neither accuracy nor scientific admission.
The saved projection retains sample, reader, data and initial-call pins.

The delivered **23:30 Pacific November 13** checkpoint found Q8 stopped at
23:11:42, after 472/1,000 judgments, when commit headroom reached 7.978 GiB below
the existing 8 GiB floor. Host-visible inspection verified all seven recorded
owned processes exited, the release matched its owner and both exact lease paths
were absent. The partial receipt was landed after the bounded summary correction
described above. Its original six-hour deadline remains 03:02:55 Pacific November
14; saved work grants no fresh allowance or automatic retry.

At 23:31:28, headroom had recovered to 49.2/24.5 GiB RAM/commit with no counted
leases. The frozen final-v2 package, launcher and nine package versions matched
their manifest. The next serial goal-baseline job completed at 23:33:35; native
exit, matching lease release and aggregate source binding were verified.

The goal-reader pilot `.local/bench/two-day-tp4-goals` started at 23:34:29 using
the unchanged final-v2 snapshot. Its pre-launch headroom was 49.0/24.4 GiB, above
the 22 GiB shared reservation requirement and 20 GiB load gate. After the small
reader loaded and prepared the first input, commit headroom was 18.270 GiB.
The stricter pre-load guard stopped it at 23:36:48 before loading the 9B model;
zero documents completed. Host-visible inspection confirmed all five recorded
owned processes exited and both matching leases released. The stopped aggregate
is verified, retaining the completed TF-IDF baseline. This is a resource stop,
not an efficacy result. Its original eight-hour deadline is 07:34:30 Pacific
November 14; a later exact-cache continuation would retain that deadline.

The delivered **00:10 Pacific November 14** checkpoint found W1's a-d run
completed at 23:57:16 November 13. Native exit and both exact lease releases were
verified. The aggregate is landed and source-verified. Numerical and prefix
checks passed; timing gate d requires measurement, not hitting its target, and
the measured speed missed that target. Gate e remains required for serving.

The next serial job, `.local/bench/two-day-w1-binding`, started at 00:12:45 with
the verified final-v2 package and original queue deadline. It compares the exact
1,399-session cohort against the saved float32 window tables without rerunning
that reference. The completed a-d receipt stays intact; a byte-identical starting
copy at `two-day-w1-binding/gate-receipt.json` receives gate e's eventual result.
That combined gate receipt, rather than `pilot/receipt.json`, is the source to
land after binding completes and its owner exits/releases.

The delivered **02:10 Pacific November 14** checkpoint found all 1,399 binding
sessions and gate e complete at 01:59:58. Host-visible native exit, the matching
release receipt and both exact lease absences were verified. The combined root
gate receipt was landed and source-verified; the original a-d receipt is unchanged.
The final accuracy difference is within 0.005, as recorded below.

The next serial job, `.local/bench/two-day-first-paint`, started at **02:11:43**
with the verified final-v2 package, launcher and nine package versions. It times
float32 KV Qwen and Smol on the three frozen texts, using two threads and one
counted shared slot. Native identity and both lease ownerships were verified.
Startup headroom was 46.0/25.0 GiB RAM/commit. It completed at **02:17:10**.
The owner's follow-up found its terminal receipt; native exit, matching lease
release and the public aggregate's source binding were verified.

The next serial job, `.local/bench/two-day-robustness`, started at **02:18:39**
under the unchanged final-v2 package. At 02:27:06 it had saved 156/2,500 base
documents, with a fresh heartbeat and 43.7/19.6 GiB RAM/commit headroom. Native
identity and both lease ownerships are verified. No terminal receipt exists.
Early raw-document throughput suggests roughly two more hours for the base set;
normalized attacks and the auxiliary essays add work, so this is not a full-pilot
forecast. Its eight-hour deadline is **10:18:40 Pacific November 14**; the queue
deadline remains **03:20:11 Pacific November 15**. Next check: **03:30 Pacific
November 14**, registered and verified; future delivery is unobserved.

### Completed window measurements

These are mean within-writer AUC results from the registered window reader.
Intervals are paired writer-cluster bootstrap intervals for the gain, conditional
on the fitted out-of-fold models. After verified process exit and lease release,
the completed registered receipts were landed through the aggregate-only reporter
and the [scoreboard](ENGINE_SCOREBOARD.md) was regenerated. Public receipts match
the reporter's source-derived output, retain exact pins, and keep production
admission false. Reader comparisons never replace the registered window row.

| Registered contrast | Baseline | Engine | Gain (95% interval) | Bar | Outcome |
|---|---:|---:|---|---:|---|
| Attention, primary | 0.55116 | 0.56767 | +0.01651 [0.00807, 0.02414] | +0.02 | Missed |
| Attention, added history | 0.55900 | 0.56000 | +0.00100 [-0.00024, 0.00202] | +0.01 | Missed |
| AI involvement, primary | 0.60023 | 0.80551 | +0.20528 [0.17328, 0.23610] | +0.02 | Cleared |
| AI involvement, added history | 0.81584 | 0.81860 | +0.00276 [-0.00130, 0.00676] | +0.01 | Missed |

Both matched-donor contrasts are unavailable: required donor context is missing
in their fixed history cohorts. Cohorts were not silently changed. The primary
rows each have 60 supported writer clusters; the history rows have 49 and 50,
respectively. Involvement includes 30,621 eligible sentences from 104 writer/genre
cells and applies only to accepted suggestions from CoAuthor's 2021 model.
It does not establish modern whole-document detection. Failed registered gates
remain failed; the preplanned reader/history comparisons do not replace them.
No production admission or field label follows (**no ledger row**).

Source receipts: `.local/bench/two-day-20261113-b/attention/attention-window.json`
and `involvement.json` in the same directory. Both retain engine pin
`b51c5aea21d0a82c239ab994ae928f273f549b8f66d40f0c153a9e19f865d7d1`
and data pin `670812f8a6d19837c4772edaac075f6db7ae7d61352701c416214b07071e24f9`.


### Completed float32 KV comparison

The registered primary AUC is 0.567666111 with the window reader and 0.567691213
with float32 KV reuse. The difference is +0.000025102 (paired 95% interval
[-0.000038524, 0.000107330]), within the maximum absolute difference of 0.005.
The supplied binding receipt reports **passes: true**, with 60 supported writer
clusters. This passes the specified reader accuracy comparison. It does not
reverse the failed attention efficacy bar, pass W1's separate quantization gates,
enable production or change a default. Phase timings include different work and
are not an overall speedup measurement.

Sources: `.local/bench/two-day-20261113-b/attention/binding-parity.json` and
`attention-kv.json` in the same directory. The KV engine pin is
`f478242cbc81608a1b744af7465018958ad30dd0e3b2c4217fe8a0fd2bc9f6f4`;
its reference window and data pins are those above. Retain this comparison
separately from the registered window row. There is **no ledger row** or new
research admission.


### Completed smaller-reader comparison

SmolLM2-360M's primary AUC is 0.566761753 versus Qwen's 0.567666111, a difference
of -0.000904358. Its receipt marks `candidateFirstPaint: true`: the absolute
difference is within the specified 0.01 criterion. This is an accuracy candidate,
not a measured first-paint latency improvement or permission to change defaults.
The history ladder remains unrun. The separate V2 and V3 exploratory gains were
0.01561 and 0.01653; neither clears the 0.02 attention bar.

Source: `.local/bench/two-day-20261113-b/attention/reader-ladder.json`, engine pin
`96573b9e2ddd2955cf1b214dd91b4a59cdf82aeccf034c3bffc8fad8e997f0b9`, with the same
data pin above. `attention-exploratory.json` retains its separate combined pin
`38466c735f0466a7400b52e622ffcc3edec13ba654ca0327b809d5cf4e6a1cb4`.
No default, field label or production admission changed (**no ledger row**).


### Completed edit-feature benchmark

The recovered-feature classifier scored macro-F1 **0.484132** and two-way
accuracy **0.802009** on the 1,692 retained, comment-labelled EX2 edits, using the
original editor-disjoint folds. The original aggregate is retained in the receipt
history; the latest public status is stopped for the partial Q8 comparison below.
Original feature-generation timings are missing, so cascade speed cannot qualify.
No research admission follows (**no ledger row**).

Source: `.local/bench/two-day-tp3-features/pilot/receipt.json`, data pin
`9019f2dec0c55cd24ff535f1a24b0bd342106378c90fa0a4bd3dca1bfe0d36c6`, code pin
`43ecae394e1395cdbb9af02d764616d0c194eb9d1c9a8dc844859bceb9344c28`.
The reporter's public source-receipt pin is
`634a923a0b2ad70d58e03f74493dea50aa337fbc536e8397997ea68f0ba02f4b`;
its output was verified against the source-derived aggregate.

### Resource-stopped Q8 comparison

The 472 saved judgments are an incomplete prefix of the fixed 1,000-edit sample.
Q8 macro-F1 is **0.258336** and two-way accuracy **0.500000**; the feature
classifier on those same 472 edits scores **0.479442** and **0.783898**. These
partial results do not establish the final comparison. The top-level two-way
score now agrees with the unchanged paired comparison by counting `unclear`
answers as errors. Macro-F1 is unaffected. Cascade speed remains unqualified
because original feature-generation timings are absent. No admission follows
(**no ledger row**).

Corrected source: `.local/bench/two-day-tp3-q8/pilot/receipt-abstention-corrected.json`;
the original `receipt.json` and all calls remain intact. Public source-receipt pin:
`bb8cb2e1a3cd5f5c4a9d409c3bb5ffdc7aa9d3830adf83611cfe9f9d6787d4e2`.
Original receipt pin:
`50ac9b9243f963becda5ba32c05d0d0b06e8776793dac6af9e7f0ce7c4c4f620`.
Aggregation-code pin:
`3bbec6b1445c068a887b692a3087b9766ffe6d9f9e98bf4311759a02c4b2a9c8`.
The source retains the frozen inference code/data/reader pins independently.

### Completed goal word-matching baseline

Candidate-only TF-IDF ranks the correct reference first on **65%** of the fixed
40 proposals from 38 authors (author-bootstrap 95% interval **48.8%-80.5%**).
Mean reciprocal rank is **0.729398**. Goal-reader and reranking comparisons are
memory-blocked; this baseline alone establishes no model advantage or admission
(**no ledger row**).

Source: `.local/bench/two-day-tp4-tfidf/pilot/receipt.json`, data pin
`dd901f34b399253af97aaa236e15025003222dcb93d8da656c75c49a21a6a1e7`.
The source code pin is the unchanged final-v2 pin above; public source-receipt pin
`1feb2022320ffde75a0b4f6cf52d60f10ebf7f95fa3f8f07e7b1c1e49a0a2995`.
The subsequent zero-document goal stop has public source-receipt pin
`852613e02789e3a3695f0fe2ff18c4e5cb837ee3903becbf47888aba6c90c0dd`;
the earlier baseline receipt is preserved in history. Its inference engine pin
is `1b60a57a4b27f91551db08d043c88e4d4432a489b5e0e8ae3f38cca2a78c97c6`.

### Completed W1 gates and timings

Gate a passed with the owner's verified unused-padding equivalence. All three
frozen texts passed gate b's rank correlation of at least 0.98 and median absolute
loss difference of at most 0.05 nats against the float32 window reference:

| Text | Words | Rank correlation | Median absolute difference (nats) |
|---|---:|---:|---:|
| Manuscript | 3,044 | 0.998533 | 0.045859 |
| Art excerpt | 6,038 | 0.996999 | 0.043212 |
| Distill excerpt | 598 | 0.999584 | 0.031826 |

Gate c's maximum prefix token-loss difference was **0.0 nats**, under 0.001.
Gate d records timing; its 15-second target is not a waived numerical criterion.
The target was **not met**: the two long texts took 55.4 and 62.4 seconds per
3,000 words on two threads (101.8 and 116.1 seconds on one thread).

| Text | First up-to-600 words, 1 thread | First up-to-600 words, 2 threads | Whole text, 1 thread | Whole text, 2 threads |
|---|---:|---:|---:|---:|
| Manuscript | 17.39 s | 9.70 s | 103.30 s | 56.18 s |
| Art excerpt | 17.20 s | 9.59 s | 233.68 s | 125.62 s |
| Distill excerpt (all 598 words) | 11.76 s | 6.42 s | 11.76 s | 6.42 s |

Load times were 0.269 and 0.294 seconds respectively and are excluded above.
These measure scoring only, not a complete engine reading or UI latency. The
separate float32/Smol first-paint task is complete, as recorded below.

Gate e completed on the exact 1,399-session cohort. Mean within-writer AUC was
**0.567673237** versus **0.567666111** for the saved float32 reference: difference
**+0.000007126**, within the unchanged 0.005 maximum. The paired 95% interval was
[-0.000270119, 0.000232661], with 60 supported writer clusters and one excluded
single-class cluster. This completes a-e for the frozen package, including
recorded timing, while retaining the missed speed target. It does not reverse
the attention efficacy result or establish detector admission. Current live code
differs after the summary repair; exact serving pins remain required. No default
or research admission changed (**no ledger row**).

Combined source: `.local/bench/two-day-w1-binding/gate-receipt.json`; verified
public source-receipt pin
`9b11338e573659f596fd3398e95c4075ebd927c116af9d68d61f30d9e87203e0`.
The original `.local/bench/two-day-w1/pilot/receipt.json` is preserved, with its
earlier public version retained in the aggregate history.
Reader pin `996dc6c171a8ba4c89937cac9d80e42d5f5fed791791709d15f609a2c580b144`;
the receipt retains the converted-weight, frozen-text and final-v2 code pins.

### Completed first-paint timings

All six measurements completed on the three frozen texts, with two CPU threads
and float32 KV scoring. These are scoring times after loading, not full-engine
or interface latency; they do not enable a different default.

| Text | Qwen first up-to-600 | Smol first up-to-600 | Qwen whole text | Smol whole text |
|---|---:|---:|---:|---:|
| Manuscript, 3,044 words | 10.13 s | 7.65 s | 53.67 s | 41.92 s |
| Art excerpt, 6,038 words | 9.71 s | 6.21 s | 113.58 s | 80.76 s |
| Distill excerpt, all 598 words | 7.06 s | 4.04 s | 7.06 s | 4.04 s |

Recorded loading was 22.92 seconds for Qwen and 1.30 for Smol. The process loaded
Qwen first, so these are not a controlled cold-load comparison. Ordinary serving
already retains loaded readers across pages. Context reuse, exact text/window
caches, encoding reuse and incremental publication are already implemented.

Source: `.local/bench/two-day-first-paint/pilot/receipt.json`, source-receipt pin
`45b8ba1d4cf96006c89b6c23d82fcad8809fc54763110b0dc2fdd425a019ea39`.
The [public timing receipt](../engine/validation/first-paint-2026-11.json) retains
per-measurement reader hashes, text/code pins and the reader-ladder pin. There is
**no ledger row**, production admission or change to the failed attention bar.

### November 14 speed and completion review

- Removed repeated growing-prefix copies when selecting token context and
  classifying word boundaries. Precomputed UTF-16 offsets per passage and shared
  code holdouts across streamed chunks preserve source spans and exclusions.
- Released vocabulary-sized temporary tensors before yielding each scoring
  block. KV scoring retains only the needed final logit row and the bounded
  attention cache. Four tiny-model checks verify full logits are released before
  the next forward call and while yielding.
- Forty constructed Unicode/text cases and four tiny-model window/KV comparisons,
  with and without entropy, matched the previous code exactly. A 14,400-word
  constructed alignment/summary check took median 11.42 seconds before and 8.58
  seconds after over three paired runs during shared activity, about 25% less
  overhead. This is neither an inference-speed nor end-to-end measurement.
- The first-paint reporter had redacted reader identities without retaining their
  hashes. It now exports reader hashes and the ladder pin. Same-source formatting
  repairs update the report while archiving the earlier version; generated text
  and individual observations remain excluded. No inference was repeated.
- Targeted checks: **66 passed** across reader memory/cache, incremental preview,
  Unicode spans and pilot/reporting controls. A restricted test run stalled in a
  transport fixture; only its verified owned processes were stopped. The host
  rerun completed. One new test's expected phrase end was corrected to honor the
  existing held-word exclusion; the targeted rerun passed. Ruff and wrapper syntax
  checks pass. The active research snapshot and its gates are unchanged.

The reviewed hot paths have no further obvious change that can be enabled without
fresh measurement or changing the selected reader. Pending robustness, human-edit
work and the deferred history ladder remain measurements, not missing frontend
implementation. Missing exports and the separately blocked full-art cache retain
their documented gates and original deadlines.

## Ghost V29 receiving checkpoint, November 13

The 06:30 checkpoint found the newly delivered
[`ghost-v29-2026-11-13`](exchange/ghost-v29-2026-11-13/README.md) package. All 19
original and seven Q2-update manifest entries matched. Reports, protocols,
controls and verification receipts were read; all three families report passing
controls/reconstruction, and their aggregate hashes match their supplied claims.
These are descriptive constructed-method results, with no new engine admission.

The supplied claims are `G-V29-G1b-1`, `G-V29-Q2-1` and `G-V29-Q2-2`.
None is present in the app's claim snapshot (**no ledger row** there). The G1b
and SECONDARY claim report hashes differ from the delivered report bytes;
the updated Q2 claim/report binding agrees. Preserve the delivered bytes and
resolve those two source bindings before any public ledger uptake.

Gated items: validate context transfer before interpreting past writing as a
stable habit; keep control belief and deficit sensitivity as distinct possible
explanations; never count a deterministic summary of a complete history as extra
independent evidence. The current history ladder remains exploratory, and the
bottom box remains empty. These notes enable no additional commissioned scoring
or inferred values. The private intake record retains all pins and dispositions.

## Continuation commands

All paths below are relative to the repository root. The preserved B snapshot must
stay untouched. The final prepared snapshot is
`.local/bench/two-day-code-20261113-final-v2`; its `snapshot.json` records source,
launcher and installed package pins. Its private continuation file is
`.local/bench/two-day-continuation.json`. Verify native exit and both matching
lease releases before starting another scorer. Never remove a foreign lease.

Common arguments in PowerShell:

```powershell
$jobArgs = @('--sounding-line', 'E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line',
  '--snapshot', '.local/bench/two-day-code-20261113-final-v2',
  '--intake', '.local/bench/two-day-ex1-intake',
  '--readers', '.local/preview-readers', '--threads', '2',
  '--until', '2026-11-15T11:20:11+00:00')
```

Use a fresh output directory for each row, preserving failures. Small-reader or
feature jobs use `engine/.venv/Scripts/python.exe -B
.local/bench/two-day-code-20261113-final-v2/launcher.py @jobArgs --output <run-dir>
--task <task> --task-args <arguments>`. Judgment jobs use
`node scripts/engine-two-day-qwen.mjs @jobArgs --output <run-dir> --task <task>
--task-args <arguments>`; it owns and closes its dedicated service. No second
scorer starts while either shared or local ownership remains active.

| Order / task | Arguments after `--task-args` |
|---|---|
| `edit-features` | `--prepared .local/bench/two-day-prepared` |
| `edits` | `--prepared .local/bench/two-day-prepared --feature-output <feature-run>/pilot` |
| `goal-baseline`, then `goals` | `--prepared .local/bench/two-day-prepared-v2` |
| `weightonly` | `--gguf .local/bench/weightonly/qwen-0.5b-q8_0.gguf --texts .local/bench/speed-texts-20261111.json` |
| `weightonly-binding`, only after a–d pass | `--gguf .local/bench/weightonly/qwen-0.5b-q8_0.gguf --weightonly-receipt <w1-run>/pilot/receipt.json --attention-output .local/bench/two-day-20261113-b/attention` |
| `first-paint` | `--texts .local/bench/speed-texts-20261111.json --attention-output .local/bench/two-day-20261113-b/attention` |
| `robustness` | `--dataset .local/bench/raid-pilot-20261113 --auxiliary .local/bench/non-native-20261113` |
| `choice` | Actual verified EX5 required; never invent the export or its adapter |
| `human-features`, then `human-edits` | `--prepared .local/bench/two-day-prepared` |
| Optional `choice-goals` | Actual EX5 plus `--e1-output <completed-choice-run>/pilot` |

The queue is bounded to 48 hours from the active B start; do not reset that
allowance per job. Drop optional E2, then goal reranking, then human Q8, then RAID
paraphrase if time requires. Reranking reuses the existing body-goal response and
therefore costs no extra model call. Memory blocks on 9B can advance the next
small-reader item; they do not authorize remote or GPU inference. No parity gate
may be dropped. CP1/EX6 unsupported or absent means no standing-from-pair build.

Land finished or stopped aggregate receipts with:

```powershell
engine/.venv/Scripts/python.exe -B -m tompathy_engine.eval.two_day.reporting `
  --capability <capability> --source <private-receipt.json>
```

Use `attention-window.json` and `involvement.json` for the registered rows;
keep reader/history ladders and `attention-exploratory.json` distinct. The public
landing preserves old versions and omits individual records, generated prose
and raw error messages. Record the named stop gate in this working note. A
resource stop, failed parity, absent export or partial pilot is never completion.

## Five-line theory return, pending measurements

1. Own-history onset: registered history rows missed their bars; the exploratory ladder remains unrun after the resource stop.
2. Accepted-answer choice: EX5 absent; no preference/value claim.
3. Beyond word overlap: candidate-only TF-IDF top-1 is 65% on the 40-proposal pilot; reader and paired reranking results remain pending.
4. Robustness: scoring is running on the prepared quotas; no measured detection claim yet.
5. Speed: W1 numerical, prefix and final accuracy checks passed; recorded timing missed the speed target. Smol's first-600 scoring was 6.2-7.7 seconds on the longer texts, versus Qwen's 9.7-10.1; no default changed.
