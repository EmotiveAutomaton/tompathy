# TP23-fine-71 · Do story tags improve separation of similar feelings?

**1. Question and prediction.** Do story tags improve separation of similar feelings? Mean transfer AUC gain must reach 0.06 and four pairs must gain at least 0.03. Encoders must also reach story AUC 0.76.

**2. Source and size.** Class P. Story Commonsense/ROCStories, public download with no dataset licence stated in the held release. The transfer source is Crowd-enVENT (CC BY 4.0). same 48,065 story lines and 6,600 Crowd-enVENT reports; seeds landed 16, 17 and 18 November. Story author identities are unavailable. The transfer cohort has 2,379 writers.

**3. Registered quantities.**

| Twin pair | Ratings AUC | Needs AUC | Both AUC | Gain |
| --- | --- | --- | --- | --- |
| pride-joy | 0.6192071 | 0.781048 | 0.7876309 | 0.1684238 |
| guilt-shame | 0.6169517 | 0.6585628 | 0.678159 | 0.06120731 |
| fear-sadness | 0.7245839 | 0.8137556 | 0.8393997 | 0.1148158 |
| anger-disgust | 0.7465746 | 0.7851224 | 0.8187032 | 0.07212854 |
| trust-joy | 0.8014725 | 0.8799507 | 0.9050882 | 0.1036157 |

| Story tag (acceptance is the current name for belonging) | Held-out AUC |
| --- | --- |
| contact | 0.8131466 |
| order | 0.7343885 |
| status | 0.7511742 |
| family | 0.836713 |
| approval | 0.7238859 |
| curiosity | 0.7841614 |
| tranquility | 0.811807 |
| competition | 0.8613032 |
| savings | 0.8432047 |
| indep | 0.7257144 |
| food | 0.9033692 |
| health | 0.8538323 |
| power | 0.768788 |
| romance | 0.9010135 |
| honor | 0.6897391 |
| serenity | 0.7085774 |
| idealism | 0.6415773 |
| rest | 0.8559804 |
| belonging | 0.7385469 |

Thirteen-label macro-F1: ratings 0.3777752, needs 0.2877239, ratings+needs 0.472303.

**4. Verdict.** **passed.** Mean twin gain 0.1040382, with 5 qualifying pairs. Story AUC 0.7866802. No sampling interval was computed.

**5. Limit.** The story folds are story-disjoint. Transfer tests reuse a common event cohort. Seed spread measures training variability.

**6. Withholding and release.** Individual records, texts, identities and fitted personal weights stay with the source. All available group statistics are reportable under DC.

**7. Tables and code.** [readers-need-fine-71-2026-11.json](../../../engine/validation/readers-need-fine-71-2026-11.json) · [EVIDENCE_LEDGER_SEED_R29.jsonl](../../../engine/validation/EVIDENCE_LEDGER_SEED_R29.jsonl) · [Report builder](../../../scripts/r48_reports.py)
