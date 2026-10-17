# Engine v1 integration

The October 16 driver adds a separate local preview path. `POST /v1/analyze`
accepts `mode: "preview" | "admitted"` (service default: admitted; frontend
default: preview), `history: "wikipedia" | "github"`, `historyLimit` (20 default;
500 Wikipedia / 100 GitHub maximum), an optional memory-only `githubToken`, and
`preferCache` for an exact-input real-run backup. SSE streams `progress`,
validated `partial` packets, then the final `packet`; cancellation still uses
the request ID. The admitted builder and its scientific gates are unchanged.

Packet 1.8 adds optional `evidenceStatus` / `basis`, provider mode/notice, and
preview module status, reader pins, comparison and timing metadata. Packet 1.9
adds evidence-first maker kinds, revision references, decision counts and a
local-only username field. Preview validation requires labels and relative
support. No statistical source inference is enabled. Numerical population
quantiles must be supplied, sorted and in scale; the frontend never invents
them. [Implementation status](DRIVER_IMPLEMENTATION.md) separates working paths,
software tests and still-unmet performance/acceptance targets.

Captured regions may carry `codeSpans` as bounded UTF-16 offsets. Surface readers
convert them to source-character spans and hold inline/preformatted code out of
word statistics. Git history may carry `parent_text_witness` with an actual parent
revision ID and its file text; it supports boundary diffs without inventing a
parent ledger revision or timestamp.

Cross-project research handoff: [Sounding Line Stage 15 dependencies](SOUNDING_LINE_STAGE15_DEPENDENCIES_2026-10-15.md). Interface use, source mapping and remaining research admissions are distinguished.

ToMpathy owns the implementation. Sounding Line owns real-data tests and
admitted/inconclusive/killed decisions. Ghost Scale owns constructed-world truth
and recovery/coverage tests. Consumers pin an engine archive or checkout and the
export below; they do not need to copy model code into their repositories.

```sh
tompathy-engine interface --out .local/engine-interface.json
tompathy-engine ghost-ingest --source reader-bundle.json --ledger .local/ghost-ledger
```

The export includes the engine implementation hash, ledger schema hash, record
schemas, literal catalogue, label/feature/model/candidate schemas and module gates.
The ledger schema remains unchanged by this continuation. A new implementation
hash requires explicit refitting and matching research admissions. Existing
research pinned to the earlier foundation can finish on that exact version.
Ghost truth sidecars never enter the reader ledger or product packet.

Packet **1.8** adds `preferenceEstimate` to admitted value hypotheses: quantity,
finite estimate, optional reference, explicit interval or `null`, method and basis.
The existing conditional preference/drive intervals now travel as structured data.
Packets without current estimates remain 1.7. See [the result contract](INPUT_CONTRACT.md).
This display change requires a new implementation pin but changes neither ledger
schema nor scientific gates; do not migrate an active study merely for the UI.

## Labels, fits and packets

```sh
tompathy-engine transcribe --ledger .local/ledger --domain writing --until 2026-10-15T00:00:00Z --config reader.json --question-records .local/question-records --questions Q8,Q9,Q10 --maximum-calls 500 --cache .local/reader.sqlite --out .local/labels.json
tompathy-engine fit --pipeline --ledger .local/ledger --population writing-v0 --until 2026-10-15T00:00:00Z --labels .local/labels.json --questions Q10 --out .local/pipeline.json
tompathy-engine analyze --ledger .local/ledger --artifact EXACT_CAPTURE_ID --capture capture.json --model .local/pipeline.json --admissions .local/admissions --out .local/packet.json
```

Labels bind to exact question inputs, the literal reader pin, cutoff and schema.
Missing labels exclude the comparison; they never become zeros. Q8 typo/grammar
or Q9 no classifies a process correction. Only eligible content corrections
train preference comparisons. The pipeline retains separate options, corrections
and joint fits, classifications, exclusions, covariance and training fingerprints.
`joint` shares one coefficient across both evidence types. The separate
`correction-augmented` forecast adds the fitted correction direction to the choice
utility, as proposed in the brief; both variants are separately scored. Correction
evaluation conditions on the witnessed before/after pair, rather than forecasting
the text of an unseen future edit.
Loading it does not admit it. Final text cannot train personal preferences.

`analyze-history` combines these steps with a normalized source export or an
explicit Wikipedia fetch. Source snapshots and implementation-specific runs are
content-addressed. An identical repeat reuses the same data; a refresh preserves
the prior snapshot. Files at a pinned path cannot be replaced with different data.

```sh
tompathy-engine analyze-history --capture capture.json --directory .local/history --source history.json --adapter wikipedia --admissions .local/admissions --config reader.json --question-records .local/question-records --cache .local/reader.sqlite --questions Q10 --out .local/history-packet.json
tompathy-engine serve --token-file .local/token --extension-origin chrome-extension://YOUR_EXTENSION_ID --history-dir .local/history --transcriber-config reader.json --question-records .local/question-records --cache .local/reader.sqlite --questions Q10
```

Omit the reader options for observed history only. A configured reader must have
passed Q8/Q9 batteries; selected text feature questions need their own batteries.
The default call bound is 500, checked before model work. CLI limits are explicit;
there is no silent truncation of a feature input or hidden model download.

## Native intake

```sh
tompathy-engine native-panel --manifest bundle/manifest.json --out .local/exchange.json --ledger .local/panel-ledger
```

The manifest supplies `dataset`, a bundle-relative `file`, full `source_sha256`,
`expected_source_rows`, `source_uri`, `codebook`, and `license_evidence`.
The source path must remain within the bundle. Original source rows and derived
observation units are counted separately. Conversion is not scientific admission
or permission to redistribute a dataset.

| Dataset | Native mapping and limits |
| --- | --- |
| MultiPref | Comparison records with normal/expert annotation arrays. `target` selects overall/helpful/truthful/harmless. Original ties are retained as exclusions. Naive submission times require documented `timezone` and `timezone_evidence`. Duration supplies the start only when the end is known. |
| PRISM | Conversations group offered model responses by turn; prompts can become attributed requests. Conversation generation dates are not decision times. For `record_kind: "survey"`, `preference_scales` and `scale_evidence` are mandatory; stated preferences remain separate from revealed choices and are undated when no observation time is available. |
| Community Alignment | Four native turn fields and response_a–response_d choices. An alternative release can declare `choice_map`. Missing decision chronology remains excluded. |
| DICES 350 | A declared individual Q2–Q6 `target`, epoch timestamp and response duration produce a rating record. Gold labels, aggregate votes and demographics are not maker features. |
| Summarize from Feedback | `info`, summaries, worker and choice become a comparison. Batch names are not timestamps. |
| MovieLens Beliefs release 2 | Seen status separates experienced ratings from expected ratings and certainty. System predictions do not become self-reports. Undated or unresolved observations remain explicit. |

A manifest may supply `chronology` keyed by normalized observation ID, with
`t_open`, `t_resolve` and an independent `evidence` witness. It must not invent
times to make a dataset eligible. Ratings are retained in the ledger but excluded
from the offered-text preference likelihood; their substantive target requires
a separately justified rating model.

### Native export audit contract (local continuation, 15 October)

The additive `tompathy-native-panel-2` exchange keeps the original dataset labels
and IDs in each row's `native_source.ids`, with its zero-based original record
index, canonical record hash, annotation group/turn/target, and raw observations.
The original file's byte hash remains `source_sha256`; the canonical row hash is
not a claim of byte-identical source serialization. Existing normalized observation
IDs and maker namespaces remain unchanged. Released evaluator labels are not a
count of independently identified people and never join across datasets.

Exports retain the codebook, license evidence, manifest hash and explicit mapping
settings, including timezone/scale evidence. An external chronology window must
have a nonempty witness, ordered timezone-aware endpoints, a known observation ID,
and agree with any already known native endpoint. Its original witness is retained.
Missing durations, ambiguous daylight-saving times and nonexistent local times
remain unknown. Negative or nonfinite durations and contradictory windows refuse.
MovieLens's single `tstamp` is preserved as source metadata; it does not supply an
opening or resolution window. A separately witnessed rating remains `rate`, never
a text preference choice. See the [release codebook](https://files.grouplens.org/datasets/movielens/ml_belief_2024_data_release_2_README.txt).

The conversion receipt pins the source bytes, manifest, exchange, implementation
and ledger schema. With `--ledger`, `ledger.row_audit` maps **every** normalized
observation to its decision/stated-preference IDs or primary exclusion reason.
Raw annotation votes, reasons and confidence are post-choice observations in
`Decision.outcome.native_observation`, not pre-choice feature inputs. Excluded
records remain inspectable in the exchange and audit; retained survey preferences
are mapped even when decision chronology is absent. These files can contain
private source material; keep them with the private dataset, not public results.

The ledger schema is unchanged, but enriched records are different immutable
content. Re-ingest into a **new ledger directory**, and explicitly repin/refit any
new study. Do not append this export over an older ledger or migrate an in-flight
capsule. The [dependency return](SOUNDING_LINE_STAGE15_RETURN_2026-10-15.md) records
the tested implementation and the remaining commit/admission boundary.

Primary format references: [MultiPref](https://huggingface.co/datasets/allenai/multipref),
[PRISM](https://huggingface.co/datasets/HannahRoseKirk/prism-alignment),
[Community Alignment](https://huggingface.co/datasets/facebook/community-alignment-dataset),
[DICES 350](https://github.com/google-research-datasets/dices-dataset/blob/main/350/README.md),
[Summarize from Feedback](https://github.com/openai/summarize-from-feedback), and
[MovieLens Beliefs release 2](https://files.grouplens.org/datasets/movielens/ml_belief_2024_data_release_2_README.txt).

## Optional features, judgments and posteriors

`features` extracts entities and last-sentence/document embedding similarities
from installed local models. Directory contents are hashed, embeddings retain
the 128-token cap, and the cache is model/input-bound. Pass the resulting JSON
with `fit --pipeline --features FILE` or `eval --features FILE`. The
`local-features` admission must pin `digest(feature.model_pins)` before a fitted
packet can use them. These libraries/models are optional; the default engine
does not install or download them.

`goals-build --capture FILE --maker ID --config FILE --cache FILE --out FILE`
asks a separately pinned local judgment producer for region and governing
candidates. `--ledger` supplies attributed root cues; `--root-reliability`
controls their weight. The producer has its own pin and `goal-candidates`
admission, independent of Q1–Q10. Pass candidates through `analyze --goals FILE`
or `serve --goals FILE`; `goal-tree` admission is also required. Descriptions
remain hypotheses, including at T0. Root evidence and candidate coverage are
checked against the exact capture.

`fit-posterior` uses the canonical option/correction features with CPU NUTS or
SVI. It records posterior intervals, feature scales, cutoff, diagnostics and
package versions. Predictability is the effective coefficient norm in an
explicit training-standardized basis; inactive features cannot inflate it.
This resolves the free utility-scale/multiplier ambiguity by convention, not
by discovering an independently measured personality trait. NUTS runs one chain;
its export explicitly requires independent multi-chain/convergence assessment.
SVI intervals require a coverage check. Both paths are research exports and
cannot silently replace the product's MAP bundle. Implementation follows the
[NumPyro inference APIs](https://num.pyro.ai/en/stable/svi.html).

## Evaluation and calibration

```sh
tompathy-engine eval --dataset .local/ledger --task options --domain writing --until 2026-10-15T00:00:00Z --labels .local/labels.json --questions Q10 --modules uniform,population,backbone,corrections,joint,prototypes --maximum-targets 1000 --out .local/scores.parquet
tompathy-engine eval-source --ledger .local/ledger --until 2026-10-15T00:00:00Z --out .local/source-scores.parquet
tompathy-engine calibrate --source calibration-input.json --method temperature --out .local/calibration.json
```

`--heldout-makers` and `--heldout-prompts` accept JSON lists. Earlier means
strictly resolved before the target opens: overlapping and simultaneous outcomes
are excluded. Prototype discovery uses other makers' earlier offsets, with the
target maker's earlier records estimating its mix. Diagnosticity is an additional
opt-in evaluator and can be expensive: every prefix runs cross-fitting and its
shuffled control. There is no automatic promotion after a favorable result.

Source-use evaluation compares fixed, recency and random-walk forecasts.
Quality adjustments require both `Decision.outcome.source_quality` in [-1,1]
and `source_quality_available`, after resolution and before the next forecast.
Absent timely quality witnesses, the result describes acceptance propensity.
It does not establish reliability, endorsement or steering detection.

The CoAuthor adapter supplies a declared original-text retention proxy at episode
end, retaining its actual availability time. It also exports session-end retention
separately. The latter cannot influence earlier within-session forecasts. Both
measure surviving inserted UTF-16 units, not factual quality or endorsement.

Calibration input has `dataset`, `source_hash`, `training_makers`, `calibration`
and `test`. Each row has `id`, `maker`, `p`, `baseline`, `y`, `training_latest`,
`opened` and `resolved`. All three maker sets are disjoint, each forecast uses
earlier training, and calibration outcomes precede the final test. Temperature
scaling, prior-shift EM, content-free contextual correction and stacking have
separate methods; the latter methods additionally require their priors or
component forecasts. The final gate records ECE and proper-score comparison.
Passing it does not calibrate values or drives against self-reports.

## Product admissions

| Contribution | Additional requirements |
| --- | --- |
| Conditional preference | `backbone-preferences`, `literal-preferences`, `corrections` or `joint-preferences`, matching the fitted task; literal question receipts as used. |
| Drive mapping / sparse recipe | `drive-recipes`, Q10 and an admitted revealed-comparison fit with covariance. Final text cannot update a loading. SEEKING awaits a separately tested pursuit-vigor interpretation. |
| Borrowed T0 prior | `population-prior` plus `drive-recipes`, an eligible population fit, zero own-maker records and zero personal share. |
| Repertoire / candidate expertise | `habits`; `expertise` additionally needs repeated edit types and a complete, censored 48-hour Wikipedia outcome window. Survival is a proxy, not correctness or intended expertise. |
| Source-use | `source-trust`; explicit availability times for quality outcomes. |
| Attention | `attention`; unique surviving edit locations or T2 `ContextEvent.payload` with exact `capture_revision`, `region`, `inspection_kind` (dwell/cursor-revisit/opened-unused), and optional bounded `duration_ms`. |
| Goals | `goal-candidates` with its producer `model_pin`, plus `goal-tree`; exact capture/root-cue fingerprints. |

Each module admission must match the implementation, ledger schema and domain,
and retain both research witness references. Question batteries are necessary
feature checks, not downstream module admissions. `provider.admissions` lists
actual contributors. Software fixtures use explicitly constructed gates only.
