# TP61-highest · Does a writer’s highest group repeat beyond random dealing?

**1. Question and prediction.** Does a writer’s highest group repeat beyond random dealing? The trained excess was predicted to fall inside the rotated control band.

**2. Source and size.** Class P. Blog Authorship Corpus. Each author has openings in both original date halves. 5,409 writers, 372,273 opening occurrences, 336,008 distinct openings.

**3. Registered quantities.**

| Measure | Trained (95% writer interval) | Independent band · percentile | Rotated band · percentile |
|---|---:|---:|---:|
| Same writer | 45.39% [44.07%, 46.66%] | [37.71%, 45.98%] · 96.2 | [37.53%, 45.79%] · 95.9 |
| Random dealing | 15.72% [15.55%, 15.91%] | [15.50%, 19.06%] · 5.3 | [15.60%, 19.03%] · 3.6 |
| Excess over dealing | 29.67% [28.35%, 30.92%] | [21.23%, 27.98%] · 99.9 | [20.97%, 27.77%] · 99.7 |

Intervals use 2,000 whole-writer resamples. Each band uses 1,000 complete sets.

**4. Verdict.** **outside predicted band on point estimate, unresolved under CX.** The same group ranked highest for 45.4% of 5,409 writers, against 15.7% under random dealing. The excess was 29.7% [28.3%, 30.9%], above the rotated band [21.0%, 27.8%].

**5. Limit.** The registered inside-band prediction missed on the point estimate. The lower writer interval is within one bootstrap standard error of the upper rotated threshold, leaving the comparison unresolved under CX. Repetition can reflect stable differences in writing style or subject matter.

**6. Withholding and release.** All group estimates are released. Individual openings, author scores and weights stay private.

**7. Tables and code.** [readers-tp61-highest-2026-11.json](../../../engine/validation/readers-tp61-highest-2026-11.json) · [rapid_highest_need.py](../../../scripts/rapid_highest_need.py) · [rapid_opening_scale.py](../../../scripts/rapid_opening_scale.py) · [Report builder](../../../scripts/r48_reports.py)
