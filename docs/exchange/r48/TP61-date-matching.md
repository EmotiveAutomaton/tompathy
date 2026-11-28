# TP61-date-matching · How well do linear tags repeat and match writers across dates?

**1. Question and prediction.** How well do linear tags repeat and match writers across dates? Read matching at five openings and compare it with both random-head families at each size.

**2. Source and size.** Class P. Blog Authorship Corpus, TP45 dated openings and original candidate folds. 1,425 authors at five openings per half and 970 at forty.

**3. Registered quantities.**

| Openings per half | Writers | Measure | Trained [95% writer interval] | Independent 95% band | Rotated 95% band | Rotated percentile |
|---:|---:|---|---:|---:|---:|---:|
| 5 | 1,425 | Mean head repeat | 0.3195 [0.3005, 0.3375] | [0.2477, 0.3014] | [0.2479, 0.3028] | 99.9 |
| 5 | 1,425 | Top-one accuracy | 0.1684 [0.1502, 0.1888] | [0.1551, 0.1740] | [0.1537, 0.1719] | 87.9 |
| 5 | 1,425 | Top-ten accuracy | 0.3930 [0.3684, 0.4189] | [0.3888, 0.4112] | [0.3853, 0.4098] | 24.3 |
| 5 | 1,425 | Top-one gain | 0.0288 [0.0140, 0.0428] | [0.0154, 0.0344] | [0.0140, 0.0323] | 88.2 |
| 5 | 1,425 | Top-ten gain | 0.0372 [0.0203, 0.0533] | [0.0330, 0.0554] | [0.0295, 0.0540] | 22.8 |
| 10 | 1,392 | Mean head repeat | 0.4629 [0.4440, 0.4813] | [0.3869, 0.4463] | [0.3844, 0.4481] | 99.7 |
| 10 | 1,392 | Top-one accuracy | 0.3261 [0.3017, 0.3499] | [0.3211, 0.3448] | [0.3182, 0.3434] | 23.6 |
| 10 | 1,392 | Top-ten accuracy | 0.6236 [0.5977, 0.6473] | [0.6193, 0.6451] | [0.6171, 0.6430] | 17.7 |
| 10 | 1,392 | Top-one gain | 0.0374 [0.0230, 0.0532] | [0.0323, 0.0560] | [0.0295, 0.0546] | 27.9 |
| 10 | 1,392 | Top-ten gain | 0.0474 [0.0295, 0.0654] | [0.0431, 0.0690] | [0.0409, 0.0668] | 17.8 |
| 20 | 1,323 | Mean head repeat | 0.6010 [0.5820, 0.6168] | [0.5334, 0.5913] | [0.5319, 0.5924] | 99.2 |
| 20 | 1,323 | Top-one accuracy | 0.6175 [0.5918, 0.6455] | [0.6009, 0.6266] | [0.5979, 0.6228] | 84.6 |
| 20 | 1,323 | Top-ten accuracy | 0.8602 [0.8420, 0.8791] | [0.8571, 0.8723] | [0.8556, 0.8723] | 21.5 |
| 20 | 1,323 | Top-one gain | 0.0597 [0.0423, 0.0763] | [0.0431, 0.0688] | [0.0400, 0.0650] | 84.1 |
| 20 | 1,323 | Top-ten gain | 0.0249 [0.0121, 0.0378] | [0.0219, 0.0370] | [0.0204, 0.0370] | 21.5 |
| 40 | 970 | Mean head repeat | 0.7151 [0.6973, 0.7315] | [0.6542, 0.7039] | [0.6526, 0.7045] | 99.5 |
| 40 | 970 | Top-one accuracy | 0.8072 [0.7835, 0.8320] | [0.8010, 0.8206] | [0.7990, 0.8196] | 33.8 |
| 40 | 970 | Top-ten accuracy | 0.9629 [0.9505, 0.9742] | [0.9608, 0.9691] | [0.9598, 0.9691] | 22.4 |
| 40 | 970 | Top-one gain | 0.0227 [0.0082, 0.0381] | [0.0165, 0.0361] | [0.0144, 0.0351] | 33.7 |
| 40 | 970 | Top-ten gain | 0.0082 [0.0000, 0.0175] | [0.0062, 0.0144] | [0.0052, 0.0144] | 22.4 |

The intervals use 2,000 whole-writer draws. Each control band uses 1,000 sets.

**4. Verdict.** **descriptive.** At five openings per half, the trained heads repeated at r = 0.319. Their top-ten matching gain was 3.7% [2.0%, 5.3%], inside the rotated control band [2.9%, 5.4%].

**5. Limit.** Matching identifies an author within the original candidate fold. Persistent style and topic can also distinguish writers.

**6. Withholding and release.** The public table includes each estimate, control median, band and percentile. Private writer-level outputs stay local.

**7. Tables and code.** [readers-tp61-date-matching-2026-11.json](../../../engine/validation/readers-tp61-date-matching-2026-11.json) · [rapid_date_matching.py](../../../scripts/rapid_date_matching.py) · [rapid_date_report.py](../../../scripts/rapid_date_report.py) · [Report builder](../../../scripts/r48_reports.py)
