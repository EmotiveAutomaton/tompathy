# Attention · Does word surprise predict pauses beyond the reference model?

**1. Question and prediction.** Does word surprise predict pauses beyond the reference model? Registered comparison: lower bound of improvement above 0.02.

**2. Source and size.** Class P. Stanford CoAuthor, public download. The original intake recorded internal research use and no express redistribution grant. CoAuthor writer-typed content words, 1,399 sessions, 60 writers (one excluded).

**3. Registered quantities.**

| Registered row | Estimate | Interval | Size | Rule | Verdict |
| --- | --- | --- | --- | --- | --- |
| attention row 1 (two-day packet) | AUC 0.5677 against baseline 0.5512; improvement +0.0165 | [0.0081, 0.0241] | CoAuthor writer-typed content words, 1,399 sessions, 60 writers (one excluded) | lower bound of improvement above 0.02 | failed |
| attention row 2 (added own history) | AUC 0.5600 against 0.5590; improvement +0.0010 | [-0.0002, 0.0020] | CoAuthor, 1,302 sessions, 49 writers with history | lower bound above 0.01 | failed |
| attention row 3 (matched stranger history) | unavailable | none | CoAuthor history cohort; required donor context missing | +0.00 | not run |

| Comparison | Baseline AUC | Reader AUC | Gain | Writer interval | Writers |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.5511565 | 0.5676661 | 0.0165096 | [0.008065869, 0.02414062] | 60 |
| 2 | 0.559 | 0.5599968 | 0.0009967689 | [-0.0002392526, 0.002016694] | 49 |
| 3 | unavailable | unavailable | unavailable | unavailable | unavailable |

**4. Verdict.** **failed.** AUC 0.5677 against baseline 0.5512; improvement +0.0165. Interval [0.0081, 0.0241].

**5. Limit.** Failed registered gates remain failed; the preplanned reader/history comparisons do not replace them.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [attention-stops-2026-11.json](../../../engine/validation/attention-stops-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
