# ToMpathy engine v1

The CPU-first Python companion for ToMpathy 0.3. This is the canonical engine
implementation that Sounding Line and Ghost Scale can pin and evaluate. The
extension and engine have separate builds. Python 3.12+ is required.

The decision ledger preserves what was observed, including offered alternatives,
revisions, timestamps, source identities and exclusions. Final text alone does
not establish choices, attention, endorsement or a maker's values. Estimates
remain relative hypotheses until the relevant module has scoped admission and
calibration evidence. Research admission is separate from software verification.

## Development

```sh
python -m venv engine/.venv
engine/.venv/Scripts/python -m pip install -e "engine[dev]"
engine/.venv/Scripts/python -m pytest engine/tests
```

On Unix use `engine/.venv/bin/python`. Keep datasets, ledgers, model weights,
tokens and generated readings outside tracked source. Fixtures contain only
constructed data. Do not publish CoAuthor source text or derive permission from
the software license.

## Implementation gates

1. Ledger, exact CoAuthor replay, deterministic features, pooled forecasting and
   time-safe evaluation. Preserve the original 16,959-decision source census
   separately from later chronology exclusions.
2. Capture/revision adapters, contract packets, local registry generation and
   opt-in frontend providers. New fields use packet **1.7** because the reviewed
   frontend already uses 1.5 and 1.6.
3. Literal transcriber, corrections, diagnosticity and calibration with explicit
   module admission records; constructed Ghost conformance checks.
4. Authenticated loopback companion, cancellation, population display and browser
   verification. Producing registry files does not publish or deploy them.

The October 14 engine specification is the implementation brief. Its older
frontend descriptions are reconciled against the reviewed 0.2 source. The full
Sounding Line theory folder, including both historical essays, was reviewed;
current definitions and corrections take precedence over historical claims.

## Source attribution

CoAuthor UTF-16 replay and the reference handling baseline are ported from
Sounding Line (copyright 2026 Abraham Haskins, MIT). Source provenance and the
license notice are retained beside the port. Numerical reproduction does not
claim new human validation or admission of other modules.

## Run the companion

Activate the virtual environment, then use the installed `tompathy-engine` command.
All examples below write local files. Each command has `--help`.

```sh
tompathy-engine serve --port 8765 --token-file .local/engine-token --extension-origin chrome-extension://YOUR_EXTENSION_ID
```

Use the actual 32-character ID from `chrome://extensions`. The service creates a
random token file and reuses it on restart. Copy its contents into **Options →
Analysis source → Local companion**, with URL `http://127.0.0.1:8765`. Save, then
select **Analyze capture**. Configuration alone sends no capture. Tokens stay in
extension-local settings, outside reading exports. Keep tokens and personal
captures out of Git.

The service binds to loopback, authenticates data endpoints, restricts browser
origins, limits requests to 2 MB and runs one analysis worker. Health distinguishes
loaded models from admitted modules. Send `Accept: text/event-stream` to
`POST /v1/analyze` for progress; cancel with `DELETE /v1/analyze/{requestId}`. The
extension uses JSON responses and forwards cancellation. Population files can be
served from `--population-dir`. Enable the separate **Analyze Wikipedia history**
action with `--history-dir .local/history`. Capturing a page never fetches history.
The action fetches at most 20 revisions by default, retains an immutable source
snapshot, and runs configured transcription and fitting before producing a packet.
Add `--transcriber-config FILE --question-records DIR --cache FILE --questions Q10`
to use an installed local reader. Q8 and Q9 classify corrections; Q10 is optional.
Every requested question needs a matching passed battery. Cancellation is checked
between bounded calls.

## Ledger, fit and reading

```sh
tompathy-engine ingest --adapter capture --source capture.json --ledger .local/ledger
tompathy-engine analyze --ledger .local/ledger --artifact https://example.org/article --capture capture.json --out .local/packets/article.json
tompathy-engine fit --ledger .local/choice-ledger --population writing-v0 --until 2026-10-15T00:00:00Z --out .local/writing-model.json
tompathy-engine analyze --ledger .local/choice-ledger --artifact https://example.org/article --capture capture.json --model .local/writing-model.json --admissions .local/admissions --out .local/packets/article.json
tompathy-engine population build --ledger .local/ledger --id writing-v0 --out .local/population/writing-v0.json
tompathy-engine registry publish --packets .local/public-packets --out .local/registry/v1
```

Use the exact browser capture from a saved reading. Its artifact block, including
UTF-16 anchors, is preserved. History import needs that same artifact ID, explicit
source attribution and a permitted license. Registry generation writes files;
hosting is separate. `--private` permits internal local datasets, not public
release. Immutable registry revisions cannot be overwritten: build a new registry
destination when changing an analysis of unchanged text.

`fit` uses observed choices resolved strictly before `--until`. It refuses T0/T1
ledgers without eligible choice labels. `--task handling` fits the four declared
handling actions; default `options` uses offered alternatives. The JSON bundle
records training identities, input fingerprint, coefficients, conditional
intervals, counts, pooling penalties and implementation/schema pins. Utility scale
is fixed at one. Loading a fit does not admit it. With `backbone-preferences`
admission, an options model may display conditional feature preferences and
population comparisons. Menu position remains a process control, never a value.
Changed inputs, wrong pins or a future cutoff refuse an admitted bundle.

Without an admitted fit, population output describes observed domain counts. It
does not invent drive means. With a fit, the pooled coefficient is the comparison
midpoint. Personal information shares and intervals are conditional Laplace
approximations with the population coefficient fixed. Curve endpoints show the
prior and observed widths at the same fitted penalty; intermediate widths are
not measurements. They are not calibrated human-value probabilities or authorship
shares. Serve an existing fit with `serve --model FILE --ledger DIR --admissions DIR`.

## Source formats

| Adapter | Input and boundaries |
| --- | --- |
| `capture` | Exact extension artifact JSON. No choices or maker estimates from final text. Identical reimport is idempotent. |
| `coauthor` | Manifest with `events_file`, `source_id`, `writer`, `source_sha256`, optional prompt text and `prompt_id`. Relative JSONL path stays inside the bundle and its bytes must match. A hashed prompt ID is not a stated goal. |
| `git` | Normalized history from `read_repository` or an explicit export: `artifact_id`, `source_uri`, allowlisted `license`, `license_evidence`, ordered `revisions` with `id`, `parents`, `maker`, `t`, `text`, optional `summary`. Reads public-file history from a local checkout, with exact reconstruction and bounded first-parent traversal. |
| `wiki` | Normalized history, or public Wikipedia article URL with `--artifact ID --limit 20`. Maximum 500 revisions, serial API requests. Boundary parents and missing summaries are explicit. IP identities are unstable; bot status can be unknown. Revert proxies use a censored 48-hour window. |
| `lichess` | PGN with clocks and UTC source time. Reconstructs legal alternatives; missing chronology excludes a game. Post-move evaluations remain outcomes. |
| `panel` | Normalized exchange with `dataset`, `source_uri`, `source_sha256`, `codebook`, `expected_rows`, `rows`. Rows supply source ID, maker, alternatives, taken option, open/resolve times and optional stated preferences. Ties, absent identities and missing times are exclusions. `native-panel` converts six supported released formats through pinned manifests; see the [integration guide](../docs/ENGINE_INTERFACE.md). |

Equal display names never join people. Ledgers are immutable bounded imports.
Identical reimports are safe; extending an existing artifact's revision list needs
a new ledger snapshot in this version. A writer lock prevents simultaneous
mutation. Inspect its owner before recovering from a crashed writer. Every row
has provenance, and text is stored in hash-addressed compressed blobs.

## Research components and admissions

The canonical pipeline binds literal labels and optional local entity/embedding
features to exact inputs, classifies corrections, and fits options, corrections
and a joint model. Process corrections do not train preferences. It supports
diagnosticity with cross-maker fitting and a shuffled control. `eval` scores
options/corrections with uniform, pooled, personal, correction, joint, prototype
and diagnosticity variants using only earlier resolutions. `eval-source` compares
source-use forecasts with fixed and recency baselines. Maker and prompt holdouts,
per-target scores and input fingerprints are exported for external admission.

Admitted packets can show correction/literal preferences, revealed-theme drive
projections, sparse recipes, repeated actions/phrases/edit types, source-use
trajectories, censored Wikipedia candidate expertise, exact edit focus and
explicitly located inspection events. A separately pinned goal producer emits
local candidates and a governing cover. T0 can borrow an explicitly admitted
population prior with zero personal records. It cannot update personal loadings.
SEEKING is reserved for separately validated pursuit vigor; it is never copied
from a topic tag. All current packet estimates remain relative.

An admission JSON supplies a module, status, exact implementation/schema pins,
domain, both research witness references and gate results. Explanatory admissions
cannot claim probability. Probability additionally needs scoped calibration. No
production admission is shipped. Packets identify the version, checkout commit
when available, implementation hash, available admissions and actual contributors.
Observed revisions, decisions and corrections are records, not inferred intent.
Actual contributor IDs, including question batteries, are in `provider.admissions`.

`transcribe/questions.yaml` contains Q1–Q10. Each question is a separate constrained
call cached by model, template, settings and exact input. Run:

```sh
tompathy-engine transcribe-test --config config.json --items battery.json --question Q5 --cache .local/transcriber.sqlite --out .local/q5-result.json
```

Each question needs 200 distinct known-answer examples, source records,
negation/paraphrase coverage, 95% valid outputs, 85% binary accuracy where
applicable and its deterministic cross-check. A question's admission does not
admit another question or a downstream module. `battery-build` prepares 200-item
constructed writing batteries; these template families do not establish transfer
to natural records. Q2 requires an installed spaCy model for its cross-check.
See the verification document for completed real-model runs.

Backends support Ollama, llama.cpp and OpenAI-compatible loopback servers. They
do not download models or authorize paid endpoints. Ollama verifies the installed
digest and defaults to CPU without keep-alive. GPU use is explicit and respects
the shared research lock; it never evicts another model or clears another owner's
lock. Compatible-server identity is operator-supplied because its protocol cannot
independently verify weights. Optional embeddings need an installed local model,
a declared pin and bounded cache.

## Validation and remaining gates

See [Engine v1 verification](../docs/ENGINE_V1.md) for results and pending scientific
acceptance. Default readings show available observed history. Inferred modules
require their own admissions and feature inputs. `fit-posterior` adds an optional
CPU NumPyro path with NUTS or SVI (`pip install -e "engine[bayes]"`). It exports
a research posterior with diagnostics; it does not silently replace the
companion's MAP fit. Predictability uses an explicit coefficient-norm convention
in a training-standardized basis. A freely scaled utility and independent
multiplier would be unidentifiable. Independent convergence, coverage and research
admission remain necessary. `calibrate` fits forecast calibration on separate
makers and tests it on a third, later maker set. Forecast calibration cannot
calibrate claims about drives or stated values.

```sh
python -m pytest engine/tests
python -m ruff check engine/tompathy_engine engine/tests
python engine/scripts/generate_fixture_packets.py
node engine/scripts/validate_with_packet_schema.mjs
npm run build
npx playwright test tests/engine.spec.ts
```

The generator uses only constructed inputs, including a fitted example with
fictional gates. Never move its gates into production. The authoritative validator
also accepts a file or directory argument for checking private local packets.
