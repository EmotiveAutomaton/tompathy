# Engine scoreboard

Only measured engine accuracy belongs here. Pending rows are not zero scores.
Field labels remain off. A passed software test is not a natural-writing result.

| Capability | Benchmark | Units | Metric | Baseline | Engine | 95% interval | Bar | Date | Receipt |
|---|---|---|---|---|---|---|---|---|---|
| attention · row 1 | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | 0.5512 | 0.5677 | [0.0081, 0.0241] (gain) | +0.02 | 2026-11-14 | [complete](../engine/validation/attention-stops-2026-11.json) |
| attention · row 2 | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | 0.5590 | 0.5600 | [-0.0002, 0.0020] (gain) | +0.01 | 2026-11-14 | [complete](../engine/validation/attention-stops-2026-11.json) |
| attention · row 3 | CoAuthor writer-typed content words after engine holdouts | writers | mean within-writer AUC | — | — | — | +0.00 | 2026-11-14 | [unavailable](../engine/validation/attention-stops-2026-11.json) |
| ai-involvement · row 1 | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | 0.6002 | 0.8055 | [0.1733, 0.2361] (gain) | +0.02 | 2026-11-14 | [complete](../engine/validation/ai-involvement-2026-11.json) |
| ai-involvement · row 2 | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | 0.8158 | 0.8186 | [-0.0013, 0.0068] (gain) | +0.01 | 2026-11-14 | [complete](../engine/validation/ai-involvement-2026-11.json) |
| ai-involvement · row 3 | AI involvement, CoAuthor suggestions, 2021 model | writers | mean within-writer AUC | — | — | — | +0.00 | 2026-11-14 | [unavailable](../engine/validation/ai-involvement-2026-11.json) |
| edit-reasons | Stack Exchange single-hunk body edits, comment-derived labels | edits | macro-F1 | 0.2583 | 0.3175 | — |  | 2026-11-14 | [stopped](../engine/validation/edit-reasons-2026-11.json) |
| edit-reasons | Stack Exchange single-hunk body edits, comment-derived labels | edits | two-way accuracy | 0.5000 | 0.5275 | — |  | 2026-11-14 | [stopped](../engine/validation/edit-reasons-2026-11.json) |
| goals (pilot) | PEP/EIP Motivation ranking pilot, abstract and summary removed | documents / authors | top-1; MRR | — | — | — |  | 2026-11-14 | [stopped](../engine/validation/goals-motivation-pilot-2026-11.json) |

History contrasts and exploratory variants remain separately identified in each receipt.
A CoAuthor involvement result applies to accepted suggestions from its 2021 model; it does not establish modern whole-document detection.

## Two-day pilots

These are separate pilot scopes. No row enables a detector, values reading or field label.

| Row | Status | Result | Scope / receipt |
|---|---|---|---|
| ai-robustness (pilot) | queued-after-attention | pending; no score | [RAID training pilot; fixed 5% calibration false-alarm threshold; no detector admission](../engine/validation/ai-robustness-pilot-2026-11.json) |
| choice (pilot) | waiting-for-EX5 | pending; no score | [Public accepted-answer choice; not values](../engine/validation/choice-pilot-2026-11.json) |
| human-edits  | queued-after-attention | pending; no score | [IteraTeR balanced human intentions; fixed Q8; no fitting](../engine/validation/edit-reasons-human-2026-11.json) |
| human-features  | queued-after-attention | pending; no score | [IteraTeR; EX2-only deterministic-feature control](../engine/validation/edit-reasons-human-features-2026-11.json) |
| weightonly  | complete | a: pass; b: pass; c: pass; d: pass; e: pass | [W1 converted local base weights; five ordered gates](../engine/validation/speed-weightonly-2026-11.json) |
| first-paint  | complete | 6 first-600/whole-text timing pairs | [Three frozen texts; CPU; no default change](../engine/validation/first-paint-2026-11.json) |

Edit-reasons human-labelled lines are separate from the comment-labelled EX2 result.
Goals also report candidate-only TF-IDF, reader-alone and top-five reranking in their receipt.
Live progress and dependencies: [two-day working record](ENGINE_TWO_DAY_2026-11-14.md).
