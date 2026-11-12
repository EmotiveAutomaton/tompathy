# B13: empty-theme protocol preparation

Prepared 25 October 2026, before any real reader run. This document freezes the
new prompt and constructed inputs; it is not a receipt or scientific admission.
No real Q10 results are reported here.

## Instrument and inputs

Only the explicitly configured `live-gpu-2` profile may use `QuestionProfile`.
The fixed CPU profile and `live-gpu-1` retain their existing catalogue-wide pins,
prompts, cache keys and receipts. Q10 remains a separate call. The new per-question
pin hashes the model, settings, question, answer schema and common prompt version.
Changing Q10 does not invalidate other questions on that new profile.

The revised Q10 question is exactly:

> Theme tags explicitly present in the text, not the maker's motives. Return an empty array [] when none of the listed themes is present. Ordinary objects, locations, mechanical descriptions and negated themes do not by themselves imply care, discovery or any other theme. Use unclear only when a theme is genuinely ambiguous; never use it as a substitute for no theme.

The answer vocabulary and strict array schema are unchanged. The exact 200 inputs
are `engine/validation/q10-empty-v2.items.json`: 160 constructed positive examples
from the existing battery and 40 explicitly theme-free examples, half ordinary
mechanical descriptions and half explicit negations. They include nine positive
themes, negation, paraphrase and declared template families. They are deliberately
small constructed controls, not a natural-writing generalization claim.

File SHA-256: `ef2c6a534d079262b0f2d0e79f00fc057a76395aed98f83315239373213e5676`.
The receipt also retains the canonical battery hash and every answer.

## Frozen scoring and execution boundary

- At least 0.95 valid outputs and 0.85 exact-set accuracy overall.
- At least 0.70 exact-set accuracy for every expected label and template family.
- At least 0.70 recall for **each of the nine** positive theme tags; missing tags fail.
- At least 0.70 empty-set accuracy on at least 40 theme-free items, reported separately.
- At least 0.10 accuracy above the best constant answer.
- Protocol is `q10-empty-v2`; normal use requires its passing, pin-matched receipt.

The empty-set floor follows the existing per-label floor; it does not relax the
overall 0.85 gate. Report the false-theme rate and measured confusion alongside
these gates for the downstream care-bias experiment.

The new GPU profile is not provisioned or run by this pass. Once its exact model,
revision, runtime, precision, settings and resource slot are assigned, freeze that
manifest and run all eight requested batteries once under the new pins. Keep the
inputs and outcomes for failures as well as passes. Do not change admission records
before 26 October under the carry-forward instruction. A failed gate stays disabled;
any prompt or item revision is a separately preregistered run. Passing this literal
battery alone cannot admit personal drive estimates.

The Oracle in `test_week_packet.py` verifies the scoring software only. It does not
save an admission receipt and supplies no model accuracy evidence.
