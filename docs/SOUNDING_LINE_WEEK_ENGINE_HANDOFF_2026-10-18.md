# Engine evaluation handoff, October 18–25

Authority: the curator's [week packet](https://github.com/EmotiveAutomaton/sounding-line/blob/main/docs/design/stage-15/drive/WEEK_PACKET_20261018.md) and its
[reviewed implementation decisions](https://github.com/EmotiveAutomaton/sounding-line/blob/main/docs/design/stage-15/drive/WEEK_REVIEW_20261018.md). This is an input
contract and dependency handoff, not a completed EV comparison or an admission badge.

## Pinned dependency and timing

EV alone uses ToMpathy `certified-fit-1`, peeled commit
`5f3ad0a304727fff5e1a6beca592e786ee71b181`. Earlier cards retain their own pins.
The offline exporter is due Monday October 19 at 12:00 PDT. If still absent at
14:00, Sounding Line builds the packet's thin wrapper around those pinned functions.
The script was absent when reviewed Sunday; it is not overdue. A newly delivered
export script receives its own source hash, because adding a script cannot change
an already fixed commit. The imported engine and reader must still match the pin.

Required handoff: exact script/implementation path and hash, invocation, input/output
schema, engine/source hashes, reader weights/tokenizer/config hashes, and a small
constructed Unicode example. Existing output names can be adapted; this document
does not require changing the engine's feature calculations. Any newer engine
behavior needs a separately named comparison, never silent migration.

## Local input and export checks

- The input is all 1,399 authenticated final CoAuthor documents with session,
  writer, prompt and chronology keys retained privately. Preserve each exact
  UTF-8 text hash and its original character-provenance map. Raw text and writer
  identities stay in ignored Sounding Line paths; nothing is sent to a provider
  or copied into another repository.
- Export per-text habits, per-word preview departure scores and their exact
  character spans, recurring departure phrases and their paragraph/section
  support, plus complete pins. A per-text error is explicit, never a zero score.
- Declare each offset unit. Python codepoints, UTF-8 bytes and UTF-16 code units
  are different. Exact text slices and Unicode/newline fixtures must agree before
  joins; no fuzzy matching, silent trimming, case normalization or re-tokenization
  can replace the source span.
- Departure retains the pinned page median/interquartile-range normalization,
  content-word exclusions and zero-spread convention. The preview's allocated
  token losses are not silently promoted to normalized whole-word probabilities.
- EV1 needs the original production occurrence to survive into the final text,
  with exact provenance and span identity. Matching the same spelling or insertion
  ordinal alone is insufficient when words repeat or an insertion is edited.
  Source preparation must validate that mapping against the original D33 ledger.
- Habit vectors use the pinned eight connective and six punctuation counts,
  converted to rates per 1,000 unquoted words, sentence mean/spread and quoted-word
  share of quoted plus unquoted words. Empty denominators are unsupported, not
  invented zeros. Raw counts and denominators remain available for verification.
- The final-document EV3 comparison is primary. Its writer-typed-only secondary
  must document how retained spans and boundaries form its input; a fragmentary
  reconstruction cannot be described as the original complete prose. The two
  variants retain separate population/support audits.
- Habit repeated phrases and recurring *departure* signatures are different
  outputs. EV2 uses the latter's positive-departure/top-15/two-paragraph support,
  with the specified 100-document support pilot before full inference.

The exporter must run offline and CPU-only within a counted slot and the existing
thread/memory rules. A successful export does not admit a scientific claim. Each
consumer still needs known-answer checks, its fixed primary, full controls and
fresh-process verification. No paid route is needed for EV.

## Reservation and return

Please identify the exact shared `tompathy-demo-prep.lock` path and the durable
`availableModulesComplete: true` receipt. Sounding Line currently reserves one
counted CPU slot conservatively and requires at least 8 GiB RAM after the card's
measured peak, or a 4 GiB assumed peak. Missing lock metadata is not treated as
permission to consume the reservation. Existing workers retain their original plans.

At Tuesday October 20, 20:00 PDT, Sounding Line supplies aggregate
`ENGINE_FEATURE_TABLE.json` and `.md` for PMAP, V3, D17, D29 and EV1–3. Missing
identification/reliability/required-record measures will be explicitly unavailable
with reasons. The table will include actual definitions, control warnings,
record requirements only where measured, and the device/recording-context caveat.
Aggregate dictionary definitions will be checked against the dataset license.
No participant text, identity or person-level profile belongs in this return.

Badge semantics follow completed evidence: a null EV2 result means no demonstrated
cross-work recurrence, not proof of page locality. An EV1 pause association does
not identify attention or its cause. SDT1, if Ghost's prerequisite passes, is a
population-relative criterion/sensitivity diagnostic; competence remains open
without independent quality labels. These are interpretive boundaries, not
new gates added after seeing outcomes.

This note's existence proves preparation and delivery of a file only. The
exporter's receipt, actual execution and the recipient agent's uptake must be
verified separately. Wednesday's 06:00 start freeze and 12:00 drain still apply.
