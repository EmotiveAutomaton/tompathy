# TP23-bow · Do story tags improve separation of similar feelings?

**1. Question and prediction.** Do story tags improve separation of similar feelings? Mean transfer AUC gain must reach 0.06 and four pairs must gain at least 0.03. Encoders must also reach story AUC 0.76.

**2. Source and size.** Class P. Story Commonsense/ROCStories, public download with no dataset licence stated in the held release. The transfer source is Crowd-enVENT (CC BY 4.0). taught on 48,065 character-lines from 4,853 annotated stories; tested on 6,600 Crowd-enVENT reports. Story author identities are unavailable. The transfer cohort has 2,379 writers.

**3. Registered quantities.**

| Twin pair | Ratings AUC | Needs AUC | Both AUC | Gain |
| --- | --- | --- | --- | --- |
| pride-joy | 0.6192071 | 0.706883 | 0.7189129 | 0.09970581 |
| guilt-shame | 0.6169517 | 0.5881892 | 0.6340215 | 0.0170698 |
| fear-sadness | 0.7245839 | 0.7204027 | 0.7849666 | 0.06038272 |
| anger-disgust | 0.7465746 | 0.6897965 | 0.7794837 | 0.03290907 |
| trust-joy | 0.8014725 | 0.7535627 | 0.8396373 | 0.03816481 |

| Story tag (acceptance is the current name for belonging) | Held-out AUC |
| --- | --- |
| contact | 0.7632862 |
| order | 0.6523018 |
| status | 0.6495526 |
| family | 0.813406 |
| approval | 0.6403451 |
| curiosity | 0.7124346 |
| tranquility | 0.7414733 |
| competition | 0.8109887 |
| savings | 0.767688 |
| indep | 0.6887512 |
| food | 0.8576217 |
| health | 0.7742696 |
| power | 0.728144 |
| romance | 0.8586319 |
| honor | 0.6301867 |
| serenity | 0.652118 |
| idealism | 0.6214185 |
| rest | 0.8009862 |
| belonging | 0.6830497 |

Thirteen-label macro-F1: ratings 0.3777752, needs 0.2004152, ratings+needs 0.4215288.

**4. Verdict.** **failed.** Mean twin gain 0.04964644, with 4 qualifying pairs. Story AUC 0.7287712. No sampling interval was computed.

**5. Limit.** The story folds are story-disjoint. Transfer tests reuse a common event cohort. Seed spread measures training variability.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [readers-need-bow-2026-11.json](../../../engine/validation/readers-need-bow-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
