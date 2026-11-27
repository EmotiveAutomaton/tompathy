# TP23-fine-47 · Do story tags improve separation of similar feelings?

**1. Question and prediction.** Do story tags improve separation of similar feelings? Mean transfer AUC gain must reach 0.06 and four pairs must gain at least 0.03. Encoders must also reach story AUC 0.76.

**2. Source and size.** Class P. Story Commonsense/ROCStories, public download with no dataset licence stated in the held release. The transfer source is Crowd-enVENT (CC BY 4.0). same 48,065 story lines and 6,600 Crowd-enVENT reports; seeds landed 16, 17 and 18 November. Story author identities are unavailable. The transfer cohort has 2,379 writers.

**3. Registered quantities.**

| Twin pair | Ratings AUC | Needs AUC | Both AUC | Gain |
| --- | --- | --- | --- | --- |
| pride-joy | 0.6192071 | 0.7893306 | 0.793267 | 0.1740599 |
| guilt-shame | 0.6169517 | 0.6383439 | 0.6619268 | 0.04497508 |
| fear-sadness | 0.7245839 | 0.8169439 | 0.8442733 | 0.1196894 |
| anger-disgust | 0.7465746 | 0.7630228 | 0.8043477 | 0.05777305 |
| trust-joy | 0.8014725 | 0.8802931 | 0.908476 | 0.1070035 |

| Story tag (acceptance is the current name for belonging) | Held-out AUC |
| --- | --- |
| contact | 0.8228821 |
| order | 0.7375602 |
| status | 0.7541818 |
| family | 0.841025 |
| approval | 0.7283479 |
| curiosity | 0.7869317 |
| tranquility | 0.8148815 |
| competition | 0.8683152 |
| savings | 0.849052 |
| indep | 0.735187 |
| food | 0.9036265 |
| health | 0.8573715 |
| power | 0.7648037 |
| romance | 0.9122999 |
| honor | 0.6846566 |
| serenity | 0.7272539 |
| idealism | 0.6507134 |
| rest | 0.8472731 |
| belonging | 0.6862158 |

Thirteen-label macro-F1: ratings 0.3777752, needs 0.2818555, ratings+needs 0.4643207.

**4. Verdict.** **passed.** Mean twin gain 0.1007002, with 5 qualifying pairs. Story AUC 0.7880305. No sampling interval was computed.

**5. Limit.** The story folds are story-disjoint. Transfer tests reuse a common event cohort. Seed spread measures training variability.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [readers-need-fine-47-2026-11.json](../../../engine/validation/readers-need-fine-47-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
