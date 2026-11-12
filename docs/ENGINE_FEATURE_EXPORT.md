# Pinned offline feature export

Implementation: `scripts/export-engine-features.py`. The consumer runs it in a
fresh interpreter with ToMpathy's preview dependencies, under its existing counted
CPU supervisor. This is an interface delivery, not an EV study or admission.

Delivery SHA-256:
`a5dd4bc6447524968e75d1d4ae5f7d6c058529b41bbf2143ed44d4b7261273aa`.
Frozen engine source-manifest SHA-256:
`8aeee563b8f23202a042c7b4385df0669e1fd78c2d5f7f8455fd85ee6cb32bc7`.
The latter covers sorted engine archive paths and their file SHA-256s; it is
distinct from the engine's own implementation-version hash. Source extraction
and a constructed Unicode export were verified in a fresh process. The real
reader/corpus execution has not been performed for this handoff.

The script extracts `engine/tompathy_engine` from local Git objects at
`5f3ad0a304727fff5e1a6beca592e786ee71b181` into a disposable directory. It refuses
an interpreter that already imported the engine. It never imports the mutable
working checkout. Each export manifest supplies every engine file SHA-256, the
canonical source-manifest hash, the script's own SHA-256, and every installed
reader weights/tokenizer/config hash. Thus the new packet 1.10 implementation
does not migrate the EV comparison.

Baseline reader: Qwen/Qwen2.5-0.5B, revision
`060db6499f32faf8b98477b0a26969ef7d8b9987`, one CPU thread, dynamic int8 linear
layers and float32 embeddings. The exact canonical reader manifest SHA-256 is
`7612cbcd48959ed57557d659d6aa3961a8c9e210fd9e4c76f7a8923c1b6a2e8f`.
Installed files are verified by the frozen engine. No download, GPU, hosted
provider, or fixed-9B transcriber is used. Torch/Transformers versions are recorded
in the reader identity. Changing any of these requires a named comparison.

## Invocation

Paths below are placeholders owned by the consumer; participant data stays in
ignored Sounding Line storage. Do not copy it into this repository.

```powershell
engine/.venv/Scripts/python.exe -B scripts/export-engine-features.py `
  --input PRIVATE/final-documents.jsonl --check-input

# Launch only inside the existing counted, monitored CPU card:
engine/.venv/Scripts/python.exe -B scripts/export-engine-features.py `
  --input PRIVATE/final-documents.jsonl --output PRIVATE/features.jsonl `
  --reader .local/preview-readers/qwen --cache PRIVATE/surface-cache `
  --slot-lease SHARED/cpu-slots/slot-N.json --stop-file PRIVATE/STOP
```

Use absolute paths when invoking from another repository. The parent supervisor
owns native process identity, below-normal priority, wall-time bounds, the memory
monitor and lease release. The child checks the lease bytes and STOP file at each
scoring boundary, sets numerical libraries to one thread, and stops below 20 GiB
free output-disk space. It does not claim or reclaim slots. In accordance with
the dependency note, the parent's preflight must leave at least 8 GiB RAM after
the measured peak (or a 4 GiB assumed peak). Existing jobs keep their plans.

An output is created exclusively; existing exports are never overwritten. Files:
`features.jsonl`, `features.jsonl.manifest.json`, and, after exhaustion of input,
`features.jsonl.receipt.json`. Per-text errors are explicit records. Exit 2 means
at least one per-text error; an infrastructure failure interrupts the process
and leaves partial output without a completion receipt. Unsupported inputs are
counted separately from errors and successful scores. No receipt admits a claim.

## Input JSONL, one exact document per line

- `keys`: opaque private document/session/writer/prompt/chronology object,
  preserved verbatim; the consumer determines its dataset-specific fields.
- `text`: exact final UTF-8 text, including whitespace and newlines.
- `textSha256`: SHA-256 of that exact UTF-8 text, verified before scoring.
- `variant`: `final-document` (default) or `writer-typed-fragments`.
- `fragmentConstruction`: required for fragments; retain their boundary and
  source reconstruction description. Never label fragments as complete prose.
- `provenance`: original codepoint intervals `{start,end,occurrenceId,...}`.
  Additional original provenance fields are retained. The exporter checks bounds
  but cannot establish their truth. EV1 must validate them against the D33 ledger.
- `regions` (optional): ordered disjoint `{id,start,end,section?}` codepoint spans.
  They must cover all non-whitespace text. When omitted, split only on blank-line
  separators; retained paragraph slices are never trimmed or normalized.

All offsets are half-open. Each exported source span contains independent
document-global `codepoints`, `utf8`, and `utf16` pairs and its original `exact`
slice. Combining marks, emoji, CRLF and casefold expansion are covered by the
constructed Unicode fixture. Region-local reader spans are converted through
explicit boundary tables, never fuzzy matching or re-tokenization.

## Output definitions

Each line binds the input record hash, exact text hash, private keys, complete
original provenance and its hash, regions, variant, and manifest hash.

`habits.raw` is the pinned habit descriptor. Its eight connective and six
punctuation counts also appear as rates per 1,000 unquoted words. Zero unquoted
words gives null rates with `unsupported-empty-denominator`. Sentence mean/spread
are null when no sentence has words. Quoted share uses quoted plus unquoted words.
The pinned descriptor joins paragraph slices with one newline internally; the
original source and its offsets remain unchanged and separately identified.

`words` exports each exact lexical span and a distinct `allocatedSpan`, which
also includes following separators. `allocatedTokenLossNats` is byte-overlap
allocation of token loss, **not normalized whole-word probability**. Departure
uses the pinned page content-word median/IQR; held-out and function words have
null departures, and IQR <= 1e-12 uses zero. No remaining content words produces
an explicit unsupported result, not a zero measurement.

`departurePhrases` is the pinned top-15 non-overlapping phrase prefix, with a
runtime parity check against the frozen summarizer. A positive phrase recurs if
it has support in at least two sections (paragraph identities when section
metadata is absent). Every supporting occurrence has an exact source slice.
The pinned casefold substring rule is disclosed separately; it never substitutes
for production occurrence identity. `previewAttention` additionally preserves
the summarizer's sentence suffix, using its complete source span even where the
preview label was truncated. Habit repeats remain a different output.

`productionMappingValidated` is always false: exporting a provenance map does
not authenticate it. Intersections point back to original provenance entries;
repeated spelling never merges occurrences. The consumer owns known-answer
controls, the 100-document support pilot, independent population/support audits
for fragments, and fresh-process verification before any inference.

Constructed fixture: `engine/tests/fixtures/feature-export-unicode.jsonl`.
Validate it with `--check-input`. `engine/tests/test_feature_export.py` uses
explicit constructed losses for software checks, not model accuracy claims.
