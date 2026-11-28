# TP77-responsibility · Do readers agree with writers about their own responsibility?

**1. Question and prediction.** Do readers agree with writers about their own responsibility? The packet specified the comparison without a numerical pass threshold.

**2. Source and size.** Class P. Crowd-enVENT (CC BY 4.0). 6,600 events from 2,379 writers in the full B comparison.

**3. Registered quantities.**

| Comparison | Paired events | Writers | Rank correlation (95% interval) | Unweighted kappa (95% interval) | Fraction in exact agreement |
| --- | --- | --- | --- | --- | --- |
| B-W-prefix | 928 | 655 | 0.6881465 [0.6414923, 0.7316652] | 0.4411774 [0.3984139, 0.4826432] | 0.6228448 |
| B-writer | 6600 | 2379 | 0.6142661 [0.5975712, 0.6318888] | 0.2603073 [0.245492, 0.275213] | 0.4315152 |
| B-writer-prefix | 928 | 655 | 0.4469924 [0.3828005, 0.5080943] | 0.1986252 [0.1574549, 0.240243] | 0.4579741 |
| W-writer-prefix | 928 | 655 | 0.3998214 [0.3351843, 0.4595707] | 0.1650055 [0.1261727, 0.2044227] | 0.4396552 |

Each interval uses 2,000 whole-writer resamples. The aggregate includes every cell of each paired 1–5 table.

**4. Verdict.** **descriptive.** B and writer rank correlation 0.6142661 [0.5975712, 0.6318888]. Exact agreement 43.2%.

**5. Limit.** The comparison measures agreement with self-reports of who caused an event. W’s saved source-order prefix covers 928 events. Its results are descriptive for that subset.

**6. Withholding and release.** W reached only the original source-order prefix before its memory stop. The full W estimate has no paired data beyond that prefix. Individual answers remain private.

**7. Tables and code.** [readers-tp77-responsibility-2026-11.json](../../../engine/validation/readers-tp77-responsibility-2026-11.json) · [rapid_responsibility.py](../../../scripts/rapid_responsibility.py) · [Report builder](../../../scripts/r48_reports.py)
