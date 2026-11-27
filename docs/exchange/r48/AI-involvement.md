# AI-involvement · Can the reader distinguish accepted suggestions from writer-typed sentences?

**1. Question and prediction.** Can the reader distinguish accepted suggestions from writer-typed sentences? Registered comparison: lower bound above 0.02.

**2. Source and size.** Class P. Stanford CoAuthor, public download. The original intake recorded internal research use and no express redistribution grant. CoAuthor, 30,621 sentences, 104 writer/genre cells, 60 writers; one 2021 suggestion model.

**3. Registered quantities.**

| Registered row | Estimate | Interval | Size | Rule | Verdict |
| --- | --- | --- | --- | --- | --- |
| ai-involvement row 1 | AUC 0.8055 against 0.6002; improvement +0.2053 | [0.1733, 0.2361] | CoAuthor, 30,621 sentences, 104 writer/genre cells, 60 writers; one 2021 suggestion model | lower bound above 0.02 | cleared |
| ai-involvement row 2 (added own history) | AUC 0.8186 against 0.8158; improvement +0.0028 | [-0.0013, 0.0068] | CoAuthor history cohort, 50 writers | lower bound above 0.01 | failed |

| Comparison | Baseline AUC | Reader AUC | Gain | Writer interval | Writers |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.6002263 | 0.8055068 | 0.2052805 | [0.1732817, 0.236102] | 60 |
| 2 | 0.8158384 | 0.8186026 | 0.002764155 | [-0.001304013, 0.006761707] | 50 |
| 3 | unavailable | unavailable | unavailable | unavailable | unavailable |

**4. Verdict.** **mixed.** AUC 0.8055 against 0.6002; improvement +0.2053. Interval [0.1733, 0.2361].

**5. Limit.** A CoAuthor involvement result applies to accepted suggestions from its 2021 model; it does not establish modern whole-document detection.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [ai-involvement-2026-11.json](../../../engine/validation/ai-involvement-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
