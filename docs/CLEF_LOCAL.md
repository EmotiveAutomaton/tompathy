# Local Clef-flash

Clef-flash is installed in an isolated, ignored environment under
`.local/clef-flash`. **Practice ToMpathy with Clef.cmd** selects it for the five
technique questions. Close an older ToMpathy review session before switching
launchers. The ordinary launcher retains fixed Qwen. Clef does not supply goal
labels, population surprisal or personal values.

The [official release](https://huggingface.co/Cloudflare/clef-flash) is a 9B
Qwen3.5 backbone plus a joint schema head. Its official example is tested on an
H200; that hardware's speed does not describe this workstation's CPU run.
The local adapter uses the release's joint decision code and weights directly,
with no quantization, generation fallback or hosted transmission.

## Installation and ownership

The pinned release is `8b2e5fd17c09fd49bc2880b805d5323ec7ff4ff3`.
All release files were verified against the pinned Hugging Face Git/LFS hashes.
The manifest SHA-256 is
`da20f62b359288afa2d7e15b493557d276a3ab29d6b1bf9acc0c3e56bed3551c`.
The custom model source was inspected before execution. Startup verifies the
complete local manifest and hashes; inference is offline. The runtime records
its own source hash, dependency versions, precision and thread count.

To reproduce the installation in a new checkout:

```powershell
engine/.venv/Scripts/python.exe -m venv .local/clef-flash/venv
.local/clef-flash/venv/Scripts/python.exe -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
.local/clef-flash/venv/Scripts/python.exe -m pip install -r scripts/requirements-clef-cpu.txt
engine/.venv/Scripts/python.exe scripts/clef-download.py
```

The download is approximately 19 GB. Do not install these dependencies into the
engine or a research environment. PyTorch is CPU-only and the runtime refuses a
CUDA build. Inference uses bfloat16 and one thread, with below-normal Windows
priority. Startup requires 28 GiB available RAM; the owned process exits if
available RAM falls below 16 GiB or its resident memory exceeds 28 GiB. These
are conservative operating bounds, not a guarantee of zero shared resource use.

The service binds a random loopback port, requires a fresh bearer token, refuses
browser origins and accepts one inference at a time. Requests are text-only,
at most eight choice questions and 4,096 encoded tokens. Oversized inputs are
rejected without truncating the state. A disconnected client cancels at the
next decoder layer; a call has a two-minute limit checked at those boundaries.
The practice host owns and closes only its own service processes.

## Initial CPU measurements, October 17

Four constructed snippets were fixed before inference. Each requested the same
five technique questions used by ToMpathy. Seventeen answers had prespecified
expected labels; the three document-wide negative-contradiction cases were left
unscored because the supplied window could not establish the whole document.
The fixture and all returned distributions remain inspectable.

| Measurement | Observed result |
|---|---|
| Model load, excluding release checksum verification | 6.38 seconds |
| First five-question decision, 591 input tokens | 48.13 seconds |
| Subsequent decisions, 597–601 input tokens | 43.42–48.02 seconds |
| Prespecified answers matched | 15 of 17 |
| Served decision after cancellation, same first fixture | 49.55 seconds |
| Cancellation until the worker accepted another request | 1.64 seconds |
| Peak resident memory during the served check | 13.93 GiB |

Both scored misses were tone judgments: closing a museum was treated as a more
negative tone, and the neutral butterfly-to-regulation transition was called
unclear. These expected tone labels are analyst judgments. The unscored output
also called a garden's destruction after a storm a contradiction of its earlier
beauty, illustrating a potential confusion between changing events and logically
inconsistent claims. No expected answer was revised after seeing model output.

This is a small apparatus and usability smoke check, not an accuracy estimate for
natural essays, calibrated confidence, or scientific admission. The option
probabilities are model scores. No fixed-Qwen eligibility transfers to Clef.
The measurements do not justify changing the ordinary default or calling Clef
a fast CPU preview. A head-to-head task-quality study and optimized CPU precision
comparison remain unperformed.

The CPU reports AVX-512 bfloat16 and VNNI support. The installed Transformers
Qwen3.5 implementation uses its general PyTorch attention fallback because the
optional fused kernels are absent. This identifies an optimization route to
investigate; it is not a measured attribution of the 43–50-second latency.
CPU quantization must preserve the joint head and receive its own output-quality
comparison. Receipt: `evidence/clef-cpu-capabilities.json`.

Local receipts: `evidence/clef-cpu-benchmark.json`, its log, and
`scripts/fixtures/clef-smoke.json`. The first benchmark preceded the HTTP
cancellation guard; its recorded runtime hash distinguishes that version from
the subsequently served runtime. The model, precision and question schema are
unchanged.

The served check additionally rejected missing authentication, browser origins,
invalid schemas and oversized bodies, cancelled an in-flight request, accepted
a subsequent real decision and confirmed owned-service shutdown. At least 40.49
GiB RAM remained available during that check. Receipt:
`evidence/clef-runtime-validation.json`. An initial run exposed the tool sandbox's
denial of Windows process-tree cleanup; the helper now reports shutdown failures.
The identified test trees were closed through the approved cleanup path, and the
complete lifecycle check passed with that permission. No other process was stopped.

## Refreshing the exact essay cache

`node scripts/capture-art.mjs` captures the live page through disposable Chrome.
The following steps warm real calls serially and close each owned model service:

```powershell
engine/.venv/Scripts/python.exe scripts/preview-prepare-stage.py readers
node scripts/preview-prepare-model.mjs clef
node scripts/preview-prepare-model.mjs goals
node scripts/preview-cache-validation.mjs --prepare --clef --quick
node scripts/preview-cache-validation.mjs --prepare --quick
```

Offline preparation permits a longer bounded CPU interval; it does not change
the live page budget or admission gates. Matching cache entries require the exact
captured revision, engine implementation and backend identities. Loading a cache
does not rerun inference. Missing modules stay visible as missing.
The goal preparation helper allows up to five minutes for a completed transport
response, within its overall 20-minute budget. Ordinary live calls retain the
110-second transport limit and the shorter page/module budgets. Model settings,
prompt, token limit and cache identity are identical.
`--prepare` in the native cache check explicitly gives final cache assembly up
to 600 seconds through `--preview-preparation-budget`; individual module caps
are unchanged. Normal practice remains at 165 seconds. An HTTP page request
cannot change this setting. Prepared caches load under the ordinary budget.

The October 17 capture is 15,602 words / 328 passages, revision
`08d9b05c4935b67c9228a31e3f36a8442430d7b175e6d7c4018c5213b1b97a69`.
The existing exact population-reader calls replayed in 41.3 seconds during
preparation, including model loading. Clef then made 20 real joint calls (100
answers) in 1,013.0 seconds. Its technique module intentionally covers only the
first 20 passages. Fixed-Qwen goal preparation reached seven of 21 groups within
its 20-minute bound. There is no governing cover yet.

An initial native assembly exposed excessive work validating and rendering each
tiny cached update. Batching cached comparison rows and throttling intermediate
departure rendering preserved final scores and made full comparison replay fit
its unchanged 25-second budget. Before/after receipts record 650/1,312 comparison
readings in 25.0 seconds versus all 1,312 in 11.9 seconds; departure replay fell
from 61.9 to 23.2 seconds. This is a replay optimization, not faster fresh model
inference. Every published packet still receives full validation.

The ordinary-backend native check also exposed a timeout rollback defect:
partitioned attention frames shared objects, and positional restoration could
attach an item to the wrong source region. A small constructed regression
reproduced the exact packet rejection. Rollback now replaces the rendered
attention tree from its validated snapshot while preserving the goal/module
objects held by suspended work. All 39 affected preview tests passed after the
fix, alongside the two earlier CLI checks. This repairs software references;
it does not change model outputs or relax packet validation.

The final Clef packet assembled in 182.1 seconds and loaded from cache in
0.88 seconds in native Chrome 155, build `24b7ba901126`. Its complete habits,
departures and comparison coexist with 20 Clef passage decisions, seven partial
goal groups and 58/909 payoff sentences; values remain unknown. Source selection,
cache timestamp, all 100 visible technique notes and layout checks passed;
screenshots were inspected. The ordinary fixed-Qwen launcher also passed at
0.85 seconds to load its separate cache (26 technique checks, seven goal groups,
52/909 payoff sentences). Both checks include successful timeout recovery. Test
services and the disposable browser were closed. Local receipts:
`evidence/art-preparation-{readers,clef,goals}.json`,
`evidence/preview-clef-cache-before-replay-fix.json`, and
`evidence/preview-clef-cache-validation.json`. The first passing replay receipt
(193.8 seconds to assemble, 1.0 to load) is preserved in
`evidence/preview-clef-cache-before-rollback-fix.json`; the ordinary final receipt
is `evidence/preview-cache-validation.json`.

Use the [prepared review steps](LIVE_PRACTICE.md#prepared-full-essay-review) to
inspect this real cached reading without rerunning inference.
