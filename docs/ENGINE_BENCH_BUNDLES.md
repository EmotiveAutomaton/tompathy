# November private benchmark inputs

The November packet authorizes the named local benchmarks. Its EX1–EX4 exports
are not yet present. Do not infer their schema or silently read a replacement
corpus. The current receiving boundary below is tested on constructed replay
fixtures; compare each delivered README with it and add an explicit adapter if
the supplier's format differs. Preserve the original bytes and hashes.

Put all raw files, replays, per-word tables, model outputs, identifiers and
per-writer counts under ignored `.local/bench/`. Public validation receipts
contain aggregate outcomes, input/code/model fingerprints and exclusions only.
No benchmark content is sent to a model provider. The local readers verify their
existing model files and refuse remote code/downloads.

Each normalized bundle has `manifest.json`:

```json
{
  "schema": "tompathy.bench.bundle.v1",
  "kind": "EX1",
  "rows": 1,
  "records": {"path": "records.jsonl", "sha256": "SHA256_OF_EXACT_BYTES"},
  "readme": {"path": "README.md", "sha256": "SHA256_OF_EXACT_BYTES"}
}
```

Paths must stay inside that bundle. The manifest pins both data and its format
documentation. Placeholder hashes above are documentation, never accepted data.

## EX1: CoAuthor labels

One record per session: `session`, hashed `writer`, `fold` (0–4), `genre`,
`textSha256`, and `words`. Each word has Unicode code-point `start`/`end` and
`source` (`writer`, `suggestion`, `prompt`); writer words also have boolean `stop`
and finite `logPause`. No text/timing is included in model requests except the
replayed final text itself; timestamps are used only to order history.

The explicit local roster supplies `session`, the matching hashed `writer`,
relative `path` and `source_sha256`. If the original roster uses another identity,
require the supplied mapping; never join by display names or guess hashes.
Replay remains the existing engine implementation. Normalize NFC, CRLF/CR to LF,
then strip trailing whitespace from the end of the document. EX1 code-point
offsets stay code points; the engine's UTF-16 offset converter rejects split
surrogates. A matching hash still requires matching word segmentation.

On a mismatch the specified monotonic word-length alignment must cover at least
98% of both word sequences. This is an approximate fallback, not proof of text
identity. Log its coverage separately. More than 5% dropped sessions stops the
run. EX1's lexical segmentation must be checked on receipt; a disagreement needs
an adapter rather than silently moving word labels.

All five folds must be present for the primary comparison. Writer IDs cannot
cross folds. Frequencies/scaling are trained inside each training fold. History
uses strictly earlier session starts, retaining the latest 1,024 tokens of the
writer's earlier work across genres; donor context must match the target genre.
One seeded donor is chosen per writer from other writers
covering all of that writer's genres; no target/future session is used. A donor
lacking the matched amount of earlier context makes row 3 unavailable rather
than silently changing the row-2 cohort. Timing never becomes a predictor.

## EX2: edit reasons

One record per edit: unique `id`, hashed `writer`, `fold`, `postId`, `before`,
`after`, `category`, `features`. Categories are `typo or spelling`, `grammar`,
`clarity`, `added content`, `removed content`. The manifest additionally supplies
the reviewed frozen `featureNames` list and definitions in its README. Annotation
features must retain their original training-partition provenance. Classifier
outputs, edit comments, targets, identities and folds are not feature columns.

The existing `diff_hunks` selects exactly one hunk; its replacement/replaced
length bound stays 12,000. Report kept/excluded counts on either side of its
10,000-character line/character diff boundary. Post IDs and source licensing
remain in the private input for attribution. Nested cross-fitting chooses the
95% two-way-accuracy threshold inside each outer training fold. No qualifying
threshold means no cascade result. Q8 is called directly as a benchmark; Q9's
failed gate and production correction behavior are untouched.

Speed qualification also needs the actual cost of producing the supplied
features (`featureSeconds` per record, with its measurement provenance), in
addition to the engine's measured deterministic-feature and prediction time.
Missing feature costs permit accuracy reporting but do not qualify a runtime
speedup from precomputed feature columns.

## EX3: Motivation tasks

One record per document: `id`, `repository` (`peps`/`eips`), full 40-character
`commit`, repository-relative `path`, exact file `sha256`, hashed `author`,
`title`, 49 distinct `distractors`, `sections`, and `headings`.
Sections have `kind`, `start` (including heading), `contentStart` (after heading),
`end`, in code points of the exact decoded Git blob. Headings have `text`,
`level`, `start`. Resolve all candidate references inside the same pinned bundle.
If the delivered files lack file hashes/content offsets, explicitly construct
and retain a verified normalization receipt before using this contract.

Use local clones of `python/peps` and `ethereum/EIPs`, fetched only after the
commit list arrives. The reader uses `git show COMMIT:PATH`, never current HEAD.
Remove Motivation, Abstract, Simple Summary and description metadata before
making any of the three inputs. Candidate TF-IDF is fitted only on those exact
50 candidate Motivations. Ties use candidate ID order. The pilot persists raw
call caches and only includes documents with all three completed readers in its
paired summary. The fixed output limit still applies; an unfinished answer is a
failure, never a partial goal.

## EX4: independent essays

Each record has `session`, exact final `text`, and `words` with code-point spans,
boolean `stop80`, `stop2s`, `insertedLater`, and supplied pause evidence. Preserve
the sender's parse-failure exclusions privately and include their aggregate count
as manifest `parseFailuresExcluded`; only that count enters public receipts.
No writer identity is manufactured.
The secondary harness fits the baseline/score combinations on EX1 only, freezes
the exploratory winner, scores EX4 once, and clusters by session. History rows
are unavailable for this export. It reports later-inserted word coverage.

The protocol and all pending results are in `engine/validation/`; accuracy goes
only on [the scoreboard](ENGINE_SCOREBOARD.md). These receiving instructions do
not assert that an export has arrived or that any natural-data test has run.
