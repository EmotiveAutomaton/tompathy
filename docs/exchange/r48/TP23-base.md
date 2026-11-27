# TP23-base · Does the optional base encoder meet the story and transfer thresholds?

**1. Question and prediction.** Does the optional base encoder meet the story and transfer thresholds? Use the same transfer and story bars as the other encoders.

**2. Source and size.** Class P. Story Commonsense/ROCStories, public download with no dataset licence stated in the held release. The transfer source is Crowd-enVENT (CC BY 4.0). Released counts are held-out character-lines. Story author identities are unavailable.

**3. Registered quantities.**

| Fold | Held-out lines | Selected development AUC |
| --- | --- | --- |
| 0 | 9615 | 0.8222598 |
| 1 | 9615 | 0.5086667 |
| 2 | 9615 | 0.8037449 |
| 3 | 9610 | 0.8261514 |

**4. Verdict.** **incomplete.** 4 completed folds cover 38,455 held-out lines. No whole-study estimate or interval.

**5. Limit.** Development AUC selects the checkpoint and does not measure held-out transfer.

**6. Withholding and release.** The owner closed the run during the last fold. No final fit or combined estimate exists.

**7. Tables and code.** [r48-legacy-2026-11.json](../../../engine/validation/r48-legacy-2026-11.json) · [Report builder](../../../scripts/r48_reports.py)
