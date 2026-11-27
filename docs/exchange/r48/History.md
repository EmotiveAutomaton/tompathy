# History · Do more earlier writing sessions improve pause prediction?

**1. Question and prediction.** Do more earlier writing sessions improve pause prediction? Registered comparison: none (exploratory).

**2. Source and size.** Class P. Stanford CoAuthor, public download. The original intake recorded internal research use and no express redistribution grant. CoAuthor, six rungs from 0 to 16 earlier sessions, 39 to 60 writers per rung.

**3. Registered quantities.**

| Registered row | Estimate | Interval | Size | Rule | Verdict |
| --- | --- | --- | --- | --- | --- |
| history-ladder (exploratory) | one, two, four and eight sessions: improvements 0.0001 to 0.0009, intervals span zero; sixteen sessions +0.001030 with interval barely above zero on a different cohort | per rung; all within about [-0.0014, 0.0019] | CoAuthor, six rungs from 0 to 16 earlier sessions, 39 to 60 writers per rung | none (exploratory) | no verdict |

| Comparison | Baseline AUC | Reader AUC | Gain | Writer interval | Writers |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.5676661 | 0.5676661 | 0 | [0, 0] | 60 |
| 1 | 0.5724058 | 0.5725243 | 0.0001184447 | [-0.001407184, 0.001491917] | 39 |
| 2 | 0.558594 | 0.5594998 | 0.0009058558 | [-0.0001707927, 0.001911454] | 48 |
| 4 | 0.5606614 | 0.5612915 | 0.0006300931 | [-0.0008825255, 0.001937592] | 41 |
| 8 | 0.5520326 | 0.5526045 | 0.0005718655 | [-0.0002786222, 0.001565486] | 34 |
| 16 | 0.5578085 | 0.5588389 | 0.001030399 | [1.269474e-06, 0.002578642] | 23 |

**4. Verdict.** **no verdict.** one, two, four and eight sessions: improvements 0.0001 to 0.0009, intervals span zero; sixteen sessions +0.001030 with interval barely above zero on a different cohort. Interval per rung; all within about [-0.0014, 0.0019].

**5. Limit.** This establishes neither history onset nor admission and does not change the failed registered bars.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [history-ladder-2026-11.json](../../../engine/validation/history-ladder-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
