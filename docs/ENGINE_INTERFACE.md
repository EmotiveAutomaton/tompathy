# Engine v1 integration

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
