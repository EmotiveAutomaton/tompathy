# Engine scoreboard

Only measured engine accuracy belongs here. Pending rows are not zero scores.
Field labels remain off. A passed software test is not a natural-writing result.

| Capability | Benchmark | Units | Metric | Baseline | Engine | 95% interval | Bar | Date | Receipt |
|---|---|---|---|---|---|---|---|---|---|
| attention | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | — | — | — | +0.02 | not run | [waiting-for-data](../engine/validation/attention-stops-2026-11.json) |
| ai-involvement | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | — | — | — | +0.02 | not run | [waiting-for-data](../engine/validation/ai-involvement-2026-11.json) |
| edit-reasons | Stack Exchange single-hunk body edits, comment-derived labels | edits | macro-F1; two-way accuracy | — | — | — |  | not run | [waiting-for-data](../engine/validation/edit-reasons-2026-11.json) |
| goals (pilot) | PEP/EIP Motivation ranking pilot, abstract and summary removed | documents / authors | top-1; MRR | — | — | — |  | not run | [waiting-for-data](../engine/validation/goals-motivation-pilot-2026-11.json) |

History contrasts and exploratory variants remain separately identified in each receipt.
A CoAuthor involvement result applies to accepted suggestions from its 2021 model; it does not establish modern whole-document detection.
