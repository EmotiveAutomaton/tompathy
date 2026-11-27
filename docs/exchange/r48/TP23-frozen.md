# TP23-frozen · Do story tags improve separation of similar feelings?

**1. Question and prediction.** Do story tags improve separation of similar feelings? Mean transfer AUC gain must reach 0.06 and four pairs must gain at least 0.03. Encoders must also reach story AUC 0.76.

**2. Source and size.** Class P. Story Commonsense/ROCStories, public download with no dataset licence stated in the held release. The transfer source is Crowd-enVENT (CC BY 4.0). taught on 48,065 character-lines from 4,853 annotated stories (19 tags); tested on 6,600 Crowd-enVENT recalled-event reports. Story author identities are unavailable. The transfer cohort has 2,379 writers.

**3. Registered quantities.**

| Twin pair | Ratings AUC | Needs AUC | Both AUC | Gain |
| --- | --- | --- | --- | --- |
| pride-joy | 0.6192071 | 0.7682769 | 0.7782011 | 0.158994 |
| guilt-shame | 0.6169517 | 0.6575605 | 0.667805 | 0.05085336 |
| fear-sadness | 0.7245839 | 0.8197609 | 0.8434355 | 0.1188516 |
| anger-disgust | 0.7465746 | 0.7798611 | 0.8100344 | 0.06345978 |
| trust-joy | 0.8014725 | 0.8597183 | 0.8937778 | 0.0923053 |

| Story tag (acceptance is the current name for belonging) | Held-out AUC |
| --- | --- |
| contact | 0.8144085 |
| order | 0.7193439 |
| status | 0.7295086 |
| family | 0.8234785 |
| approval | 0.7225616 |
| curiosity | 0.789076 |
| tranquility | 0.8006093 |
| competition | 0.8528827 |
| savings | 0.8272678 |
| indep | 0.7557358 |
| food | 0.902604 |
| health | 0.8535307 |
| power | 0.7382779 |
| romance | 0.9072196 |
| honor | 0.6352375 |
| serenity | 0.7499082 |
| idealism | 0.652505 |
| rest | 0.88168 |
| belonging | 0.6016835 |

Thirteen-label macro-F1: ratings 0.3777752, needs 0.2702938, ratings+needs 0.4615164.

**4. Verdict.** **passed.** Mean twin gain 0.09689281, with 5 qualifying pairs. Story AUC 0.7767115. No sampling interval was computed.

**5. Limit.** The story folds are story-disjoint. Transfer tests reuse a common event cohort. Seed spread measures training variability.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [readers-need-frozen-2026-11.json](../../../engine/validation/readers-need-frozen-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
