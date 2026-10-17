# ToMpathy return for Sounding Line Stage 15

Prepared 15 October 2026 in response to the
[filed dependency note](SOUNDING_LINE_STAGE15_DEPENDENCIES_2026-10-15.md).
The native-adapter corrections below are implemented and tested locally. This
is a reviewable, **uncommitted continuation**, not a new committed research pin,
proof of delivery to another agent, or scientific admission. Sounding Line's
running source capsule and studies were not changed.

## Pins and compatibility

| Item | Value |
| --- | --- |
| Existing committed baseline | `82789fdb50d9366ab9352129b01ee37622554dfa` |
| Existing pinned implementation | `f8207f2b65e12885f1493555bab2792b1050495ea7231324f9d0760e94626fca` |
| Local implementation at verification | `d148eac0a340fa583d5ba4692b0bd1e4f65e82d18ecdc296cd5639e1fda6eeee` |
| Ledger schema, unchanged | `ab5c4f63f66693da9b3be0cf33598e1a244b25f6b7ad0538ef2c92ee7a9c49c7` |
| Native export format | `tompathy-native-panel-2` |

The local hash covers the entire engine source, including the preexisting
companion logging change. It must not be attributed to the baseline commit.
The exact local interface and file inventory are in the ignored evidence bundle
`.local/sounding-line-stage15-return/`; `return-receipt.json` hashes its artifacts.
A committed return pin remains pending. Re-export the interface after any engine
source change and before explicitly selecting a new version for research.

The ledger record schema and normalized observation/maker ID construction are
unchanged. Export metadata and receipt audits are additive. Existing valid
chronology is preserved, but undocumented or ambiguous chronology is now more
strictly excluded or refused. CoAuthor compilation and UTF-16 replay source are
unchanged; the existing regression tests passed. This is not a new real-log
mapping audit or a rerun of the full prepared profile comparison.

## Corrections available for review

- Preserve original published IDs with their types, zero-based source record
  indexes, annotation groups/indexes/targets, and raw observations. Canonical
  parsed-record hashes accompany the separately pinned source-byte hash.
  MultiPref evaluator labels remain source labels; no participant count or
  cross-dataset identity is inferred from them.
- Retain license/codebook evidence, mapping choices, timezone/scale evidence,
  the manifest hash and supplied chronology witnesses. Receipts pin the exchange,
  implementation and ledger schema. Each normalized observation maps to a ledger
  decision, retained stated preferences, or an explicit exclusion, including
  undated rows and surveys.
- Reject unknown chronology keys, contradictory known endpoints, naive/reversed
  windows and blank witnesses. Missing durations stay unknown; invalid durations
  fail. A timezone name alone cannot resolve a daylight-saving fold or gap.
- Remove the unwitnessed MovieLens decision window previously made by assigning
  its single timestamp to both endpoints. Retain that timestamp as source
  evidence. A separate documented window is required for a decision record;
  ratings remain ratings, not binary choices. PRISM generation dates still do
  not supply decision chronology. The
  [release codebook](https://files.grouplens.org/datasets/movielens/ml_belief_2024_data_release_2_README.txt)
  documents the MovieLens timestamp and rating fields, not a decision window.
- Keep raw votes, reasons and confidence in post-choice outcomes and audits;
  they are not pre-choice features. Rating records cannot train the text-choice
  model. Existing separately stated preferences retain their own provenance.

The [interface guide](ENGINE_INTERFACE.md) describes the fields and exclusions.
Keep source exports and receipts under their source usage restrictions; original
labels are retained for local audit, not automatically made public.

## Verification and reproducible use

Serial targeted runs passed:

| Check | Result | Retained evidence |
| --- | --- | --- |
| Native/panel adapters, CoAuthor, replay and ledger regressions | 103 passed, 24.32 s | Execution output; no XML retained for this run |
| Updated native adapter cases, CLI, pipeline/model bundle, chronological evaluation, Ghost software conformance and packet schema | 43 passed, 13.12 s | `sounding-dependencies-tests.xml` in the local bundle |
| Added CLI source → manifest → exchange → ledger/audit → interface pin check | 1 passed, 1 deselected, 1.45 s | `sounding-dependencies-cli-tests.xml` in the local bundle |

These runs overlap; their counts are not a unique-test total. Ghost conformance
here uses constructed software fixtures and does not provide the external
known-world witness. No scientific admission record was created.

From the repository root, with the engine environment installed:

```powershell
& engine/.venv/Scripts/tompathy-engine.exe interface --out .local/interface-review.json
& engine/.venv/Scripts/tompathy-engine.exe native-panel --manifest YOUR_MANIFEST.json --out .local/panel-review.json --ledger .local/fresh-panel-review-ledger
```

The second command writes the exchange and `panel-review.json.receipt.json`.
Inspect `row_audit` under the receipt's `ledger` object alongside exclusion
counts. The local evidence bundle includes the exact constructed DICES-shaped
`source.jsonl`, `manifest.json`, exchange and receipt from the passing CLI check.
That fixture is software evidence only.

Use a **fresh ledger** when reviewing these exports. Added record provenance
changes immutable record contents; appending the same IDs to an older ledger
will correctly refuse conflicting records. Select any later committed pin
explicitly, retain both exports/receipts, and compare source coordinates and
exclusions. Do not replace a source capsule or migrate an in-flight study.

## Dependency disposition

Sounding Line continues to own the native CoAuthor mapping audit, dataset
manifests, exposed-holdout checks, empirical admissions and literal-model runs.
This return supplies adapter corrections and audit evidence for optional later
evaluation; it does not revise their current study pin or acceptance criteria.

[Future owner-capture evidence requirements](OWNER_CAPTURE_EVIDENCE.md) now spell
out permission, source-scoped pseudonyms, options/actions, witnessed times,
immutable revisions and separately stated goals. No collector or new arbitrary
owner-activity importer was enabled; no new collection is needed for the
currently prepared checks.

No independent natural-text, human-annotated literal benchmark is shipped in
this ToMpathy checkout. The retained [Q5 validation](../engine/validation/README.md)
is a constructed 200-item battery, scored 0.755 and remains disabled. It does not
supply a natural-text rubric, independent rater agreement or admission.

Per the incoming note, the prepared profile fit's remaining external dependency
is the relevant Ghost known-world witness after Sounding Line's native-data and
holdout checks pass. Product UI readiness is not its blocker. A new committed
ToMpathy pin is needed only if they elect to evaluate this continuation.
