# November back-half engine implementation

Working record started 11 November; the requested Sunday report filename is
retained. This is not a claim that the week or the natural-writing benchmarks
have finished. The source packet is
`TOMPATHY_0.3_ENGINE_BACK_HALF_PACKET_2026-11-11.md`.

## Assessment and scope

The plan is implementable as an engine experiment with explicit data and parity
gates. It does not establish a deployable AI detector or an admitted goal/value
reader. Its chief dependencies are the four source-pinned EX exports and the
shared machine's memory. Those files were absent at initial inspection.

The packet's assertion that none of October's work exists is stale: it exists
as local uncommitted changes. Those changes are preserved. The October 25 work
queue is superseded by this packet; existing implementation is not rolled back.
No frontend file is edited in this pass. The new field label is a default-off
engine function and is not wired into packet emission.

The packet requests both an at-most-two-thread host limit and a four-thread
measurement. This run honors the host limit; the four-thread row is deferred.
The small-reader measurements use one owned, below-normal CPU process. No model
is downloaded. The 9B memory gate is checked separately; no research process is
stopped or borrowed.

## What is built

- **TP0:** a frozen protocol, pending aggregate receipts, the four-capability
  [scoreboard](ENGINE_SCOREBOARD.md), and a receipt-scoped `field_status` function.
  It requires an exact protocol, reader/implementation and data match, natural
  writing evidence, and the registered primary interval clearing its bar. It
  returns `unvalidated` unless explicitly enabled. No production gate changes.
- **TP1:** an optional KV reader with bounded rebuilds and separate full-text and
  segment cache names. BOS stays until the first rebuild. Subsequent segments
  rebuild from the required preceding context, filling the existing window
  rather than discarding its unused tail. Old window scoring remains available
  and remains the default. Entropy is an optional benchmark output with separate
  cache identities. The serial speed runner measures load and scoring separately,
  processed tokens, source-word parity and the short/long-prefix quantization
  probe. It stops at a parity failure.
- **TP2/TP5:** source/README hash verification, exact replay checks, normalization,
  explicit Unicode offset conversion, bounded fallback alignment and the session
  loss stop. Text-only scoring supports the specified variants and strictly
  earlier own/donor histories. Baseline fitting and standardization stay inside
  writer folds. Paired whole-writer resampling reports both the gain and its
  uncertainty. Sentence involvement reuses the same word losses, excluding prompt
  and mixed-source sentences. Unsupported writer clusters and coverage limits
  stay explicit. A separate EX4 transfer function freezes the EX1 winner, fits
  only on EX1 and evaluates the two stop labels by session. The TP1 binding
  comparison refuses any change of labels, folds or word eligibility.
- **TP3:** exact existing hunk selection and length-band exclusions, frozen Q8
  label mapping, multinomial features, nested threshold selection, deterministic
  balanced sampling, direct Q8 calls and a paired cascade comparison. The first
  group of calls must produce a projection receipt before the remainder can run.
  Completed calls persist with exact hunk and reader pins. Cache-only answers
  without original inference timings cannot qualify a speed gain. Q9 stays off.
- **TP4:** a single-call goal function extracted without changing preview request
  serialization or cache keys. The pilot reads exact Git blobs, removes answer
  sections and description metadata, prepares body/departure/cues-only inputs,
  ranks the frozen Motivation candidates with candidate-only TF-IDF, and reports
  fully paired author-cluster comparisons. It preserves completed raw calls and
  stops at the specified wall-time budget. No pilot becomes a default.

Input contracts, identity joins and unresolved sender-format details are in
[ENGINE_BENCH_BUNDLES.md](ENGINE_BENCH_BUNDLES.md). In particular, hashed writer
IDs must be supplied in a verified mapping; they are never guessed from names.
Word-length alignment is only an approximate fallback. A missing matched donor
makes the third history row unavailable rather than changing its cohort.

## Measurements and checks

The source for speed figures is
[`speed-2026-11.json`](../engine/validation/speed-2026-11.json). Its running or
stopped state must be read before treating a row as a completed comparison.
The three texts are the frozen help manuscript excerpt, the first part of the
saved art capture, and a short excerpt from the saved Distill page. Input hashes
and exact word counts are in that receipt. The last is an excerpt, not a newly
fetched whole page. Timings are same-session comparisons on a shared host;
historical timings are not substituted for a current baseline.

The installed PyTorch version's
[2.9 quantization documentation](https://docs.pytorch.org/docs/2.9/quantization.html)
now directs development toward torchao. It does not establish equivalence between
different pass shapes. The benchmark tests that behavior directly while keeping
the installed runtime and weights pinned.

The software checks use a tiny seeded causal transformer, the existing replay
fixtures, known ranking/cluster examples, corrupted cache/manifest cases,
fold-leakage controls, exact goal cache identity and default-off status checks.
They provide engineering evidence only.

### Executed speed result, 11 November

Scoring seconds exclude model load. These are pinned Qwen2.5-0.5B readings;
word counts in the input manifest use whitespace, while parity uses the engine's
lexical word spans. Each row compares the same text and precision on this host.

| Text | Precision | Threads | Old window | KV reuse | Old input tokens | KV input tokens | Word-rank correlation |
|---|---|---:|---:|---:|---:|---:|---:|
| Manuscript, 3,000 words | float32 | 1 | 152.88 s | 67.35 s | 13,313 | 5,984 | 0.998775 |
| Art excerpt, 6,000 words | float32 | 1 | 329.18 s | 170.13 s | 27,649 | 13,540 | 0.997316 |
| Distill excerpt, 600 words | float32 | 1 | 14.36 s | 9.49 s | 1,240 | 728 | 0.999967 |
| Manuscript, 3,000 words | float32 | 2 | 100.70 s | 51.66 s | 13,313 | 5,984 | 0.998775 |
| Art excerpt, 6,000 words | float32 | 2 | 209.87 s | 105.34 s | 27,649 | 13,540 | 0.997316 |
| Distill excerpt, 600 words | float32 | 2 | 9.47 s | 6.68 s | 1,240 | 728 | 0.999967 |
| Manuscript, 3,000 words | int8 | 1 | 68.32 s | 28.38 s | 13,313 | 5,984 | **0.859051 — stop** |

Float32 model load was 7.04 seconds; the fresh int8 process loaded in 16.25
seconds. Every float32 comparison cleared the 0.98 rank gate. First-block token
loss differences were exactly zero, which also gives zero word-loss difference
for complete words under the identical allocation. The median absolute word
differences were 0.013860 nats for the manuscript, 0.013196 for art and zero for
the short excerpt, at both thread counts.

**The int8 path fails parity.** Its manuscript median absolute word difference
was 0.956229 nats. In the direct 512-versus-1,024-token prefix probe, float32 had
zero difference; int8 had median 0.925583 and maximum 8.837686 nats for the same
first 511 next-token losses. This demonstrates a pass-shape dependence in this
installed dynamic-quantized reader; it does not establish a general claim about
all quantization methods.

The 15-second target is not met. Per the packet's explicit rank stop, remaining
int8 comparisons and ONNX optimization were not attempted. No default changes.
The failed int8 combination is refused by the companion and downstream natural
benchmark commands; float32 KV remains an explicitly selected experiment. TP1
cannot close until the binding natural-writing comparison exists.
The speed runner also refuses to resume a receipt that already contains this
parity failure. A different numerical path needs its own reviewed configuration
and parity run before any dependent benchmark or promotion.

The first combined run stopped at 6.94 GiB commit headroom before its int8 probe.
The guard was retained. A fresh int8-only process reused the completed float32
measurements and reached the parity stop. Both scoring processes exited; no
9B model, GPU or research process was used. An initial detached sandbox launch
exited without running the measurement; the recorded int8 result comes from the
subsequent foreground execution.

### Verification repairs

The broad engine check exposed four stale test assumptions. Three exporter tests
were using the mutable engine despite the exporter's frozen Git baseline. They
now exercise its actual frozen loader in a fresh interpreter; the exporter pin
and production code are unchanged. The fourth expected five global findings;
it now checks exact equality with the active claim snapshot.

A targeted retry stalled in Windows asyncio's socket-pair creation under the
restricted runner, before application code. Its owned test session was stopped;
the serial suite was rerun with local loopback support. This was an environment
failure, not a relaxed assertion. Other refinements keep own-history work across
genres, restrict donor history to the target genre, bind private run directories
to exact identities, and preserve original per-call timings on pilot resumption.
The large-model memory callback rechecks the 20 GiB gate at actual model load,
including a reload after service eviction; cleanup does not invoke that gate.

Final executed checks are retained in
[`back-half-software-2026-11.json`](../engine/validation/back-half-software-2026-11.json):

- Broad suite: 287 passed, one expected outline-confound failure, and one new
  CLI-test setup error (missing required token-file argument).
- After that fixture correction: all 57 targeted tests passed, including frozen
  exporter loading, current claim propagation, KV continuation, natural-data
  harness controls and the failed-int8 serving refusal.
- Final memory-callback/fixed-reader checks: all three passed. A separate
  refusal check confirmed a failed speed receipt cannot load a reader on resume.
- Ruff passed for all engine sources/tests. The unchanged frontend PacketSchema
  accepted all 13 packet fixtures. `git diff --check` passed for engine/docs.

The known expected failure is rare-topic repetition dominating optional outline
density without frequency residualisation. An existing Starlette/httpx
deprecation warning remains. All owned benchmark/test processes were verified
exited. No frontend files, frozen essay content, published artifacts, model
installation or foreign process changed in this pass.

## Running the receiving harness

Use the project interpreter. Set numerical-library thread limits before Python
starts; keep one benchmark process at a time. PowerShell examples:

```powershell
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
$env:CUDA_VISIBLE_DEVICES='-1'
engine/.venv/Scripts/python.exe -X utf8 -B -m tompathy_engine.eval.back_half prepare
engine/.venv/Scripts/python.exe -X utf8 -B -m tompathy_engine.eval.back_half attention --bundle .local/bench/EX1/manifest.json --roster .local/bench/roster.json --source-root PATH_TO_AUTHORIZED_LOGS --private-out .local/bench/attention-window
engine/.venv/Scripts/python.exe -X utf8 -B -m tompathy_engine.eval.back_half edit-features --bundle .local/bench/EX2/manifest.json
```

The CLI starts no 9B service. `edit-q8 --url http://127.0.0.1:PORT --limit 50`
requires a dedicated empty service owned by the invoking session. Inspect its
projection before requesting `--limit 1000`. The goal pilot entry point is
`python -m tompathy_engine.eval.back_half.goal_pilot --bundle EX3_MANIFEST --peps
PINNED_PEPS_CHECKOUT --eips PINNED_EIPS_CHECKOUT --url OWNED_LOOPBACK_URL`.
Both check memory before loading the 9B model and unload their own model in
`finally`; whoever started the dedicated server must close that owned server.
Never point them at Sounding Line's or a normal desktop service.

After a permitted paired scoring run, `binding-parity --training-run OLD_RUN
--comparison-run KV_RUN` verifies identical labels, folds and eligibility and
writes a separate aggregate receipt. `secondary --bundle EX4_MANIFEST
--training-run EX1_RUN --private-out .local/bench/ex4` uses the exact saved EX1
reader identities and exploratory winner. Both refuse mismatched saved records.
The failed int8 configuration must not be used for a dependent benchmark.

An explicit float32 companion experiment can choose `serve --preview-scoring kv
--preview-precision float32` in addition to the usual serving arguments.
Absence of that argument keeps the old path. The binding TP2 comparison, history
admission, edit-cascade qualification and natural-data field labels remain
pending. There is no new always-on AI authorship attribution.

## What has not run

EX1–EX4 natural-data evaluations await verified exports/adapters. The initial
memory check did not qualify the 9B jobs, and their data was absent independently.
No public robustness benchmark, research battery rerun, new drive prior or
value inference was launched. The earlier full-art preparation remains stopped
at its documented governing-output limit; extracting its call has not changed
that limit or resumed the job. No recurring wake was created.

## Next bounded work

The subsequent [completion audit](ENGINE_COMPLETENESS_2026-11-11.md) repaired
resume deadlines, sample/projection identity, stopped-run reporting and source
binding, then passed the full engine suite and integrated frontend checks. That
audit is the current verification record; the earlier repair history above is
retained. All implemented October work is included in the integrated build.

Receive and verify EX1–EX4 with their format documentation and identity mappings,
then adapt their concrete wire formats to the receiving contract. The ordinary
window reader remains available for the registered baselines. Resolve the int8
pass-shape failure under a separately pinned plan before restarting TP1; its
current faster timing cannot justify promotion. EX2's first 50 Q8 calls and EX3's
paired pilot additionally require the 20 GiB load gate and a dedicated owned CPU
service. There are no natural-data scores to publish at this checkpoint.
