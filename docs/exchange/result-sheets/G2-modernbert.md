# Did the largest encoder recover the assigned word groups more accurately?

We compared the larger encoder with the frozen reader using the same saved forecasts and writer-word scoring rule used for the earlier rungs.

The larger encoder missed the all-seeds rule.

| Seed | Mean AUC | Gain | CARE AUC |
|---|---:|---:|---:|
| 23 | 0.7551 | -0.0496 | 0.6355 |
| 47 | 0.7363 | -0.0684 | 0.6624 |
| 71 | 0.7620 | -0.0427 | 0.6767 |

Gain of at least .02 on mean AUC and CARE AUC of at least .70 on each of three registered seeds.

Held-out writers' words and reader votes are stand-ins. Co-rise describes predictions. ED is research-only.

[E-G2-MODERNBERT-20261121](../../../engine/validation/readers-profile-modernbert-2026-11.json)
