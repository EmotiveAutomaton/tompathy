# TP18-probe · Does the fixed-third probe improve pause prediction?

**1. Question and prediction.** Does the fixed-third probe improve pause prediction? Registered comparison: lower bound above 0.02.

**2. Source and size.** Class P. Stanford CoAuthor, public download. The original intake recorded internal research use and no express redistribution grant. CoAuthor fixed third: 466 sessions, 65,395 eligible words, 49 writers.

**3. Registered quantities.**

| Registered row | Estimate | Interval | Size | Rule | Verdict |
| --- | --- | --- | --- | --- | --- |
| TP18 hidden-state probe (fixed third) | AUC 0.536290 against 0.558040; improvement -0.021750 | [-0.037904, -0.008198] | CoAuthor fixed third: 466 sessions, 65,395 eligible words, 49 writers | lower bound above 0.02 | failed |

**4. Verdict.** **failed.** AUC 0.536290 against 0.558040; improvement -0.021750. Interval [-0.037904, -0.008198].

**5. Limit.** It offers no support for the proposed improvement on this subset and does not replace the failed primary or change a default.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [readers-attention-probe-2026-11.json](../../../engine/validation/readers-attention-probe-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
