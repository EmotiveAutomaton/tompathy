# Pre-flight summary, 20 November 2026

What the analyst computed or checked before writing the two packets of 20 November, and what each result changed. Scripts and outputs: `PREFLIGHT_2026-11-20.zip`. No dataset was opened. Every number in sections 1 and 2 comes from a constructed world and says nothing about people. Section 4 lists what was read from public records. Both simulation scripts were written by a helper from the analyst's written specification and read line by line by the analyst afterwards. The independent checker then added four worlds to the first, and the analyst added one to the second. Each default run was replayed from the bundle and reproduced its saved output byte for byte on the analyst's machine. The receiving repositories reproduce every number before relying on it.

## 1. Does a trait go with first size, or with what is left? (`pf_n1.py`)

The theory handoff's leg 3 asks where Neuroticism sits: after a criticised moment, does the score go with how big the bad feeling is at that prompt (first size), or with how much of it is still there at the next prompt (what is left)? The packet's form asks whether an answer is above the scale's lowest point, on the logit scale, with the trait multiplied into both effects.

The worry before any world was run: a logit effect is the true effect divided by the noise in a person's answers. If high scorers simply answer more noisily, both of their effects shrink by the same proportion. First size is the larger effect, so it loses more in absolute terms, and the plain difference between the two products leans toward the registered direction with nothing planted.

The contrast meant to be free of that fault, with $B_1$ and $B_2$ the two effects and $C_1$ and $C_2$ their products with the trait:

$$\text{RATIO} = \frac{C_2}{B_2} - \frac{C_1}{B_1}$$

Each world: 2,272 invented people, fourteen days, six prompts a day of which about a third are answered, about 20,000 usable prompts, a tenth of them after a criticised interaction. Thirty worlds a row, 200 draws of whole people for each interval. Spreads over worlds in brackets.

| World | Plain difference | RATIO |
|---|---|---|
| Nothing planted | plus 0.003 (0.017); interval above zero in 0% of worlds | plus 0.009 (0.086); above zero in 0% |
| **High scorers' answers only noisier** | **plus 0.024 (0.023); above zero in 23%: false positives** | minus 0.029 (0.099); above zero in 3% |
| The trait raises first size and what is left in proportion | minus 0.053 (0.024) | plus 0.007 (0.121); above zero in 10% |
| The trait raises only what is left, by half per standard deviation | plus 0.088 (0.020); above zero in 97% | plus 0.517 (0.107); above zero in 100% |
| The same, and answers noisier too | plus 0.114 (0.021) | plus 0.499 (0.109); above zero in 100% |
| The trait raises only first size | minus 0.109 (0.027) | minus 0.305 (0.114); below zero in 77% |

**Worlds that break the form** (the independent checker's; nothing is planted about what is left in any of them; `pf_n1_results_sel_W6-W7-W8-W9_b2_0.3.txt`):

| World | Plain difference | RATIO |
|---|---|---|
| High scorers meet criticism more often | minus 0.006 (0.027) | minus 0.015 (0.109); above zero in 0%, below in 7% |
| **The feeling saturates, and the trait raises its baseline** | minus 0.011 (0.032) | **minus 0.117 (0.056); below zero in 67%** |
| Normal noise in place of logistic; the trait raises the baseline | minus 0.002 (0.039) | minus 0.031 (0.094); above zero in 3%, below in 13% |
| **The feeling saturates, and the trait lowers its baseline** | plus 0.019 (0.030) | **plus 0.124 (0.045); above zero in 70%** |

So RATIO is free of the noise fault and not of saturation. Which way saturation pushes it depends on whether high scorers start higher or lower. For Neuroticism they start higher, so the push is downward: it can hide a true excess of about 0.12 and cannot make one.

In the first table what is left was half of first size, and RATIO's interval was about 0.2 either way. A second run made what is left between a seventh and a fifth of first size, as the form reads them (`pf_n1_results_sel_W0-W1-W3_b2_0.1.txt`):

| World | Plain difference | RATIO | RATIO's interval, either way |
|---|---|---|---|
| Nothing planted | plus 0.006 (0.016) | plus 0.096 (0.235); above zero in 0% | 0.67 |
| High scorers' answers only noisier | plus 0.046 (0.025); **above zero in 50%** | minus 0.042 (0.334); above zero in 3% | 0.67 |
| The trait raises only what is left, by half | plus 0.030 (0.024) | plus 0.603 (0.367); above zero in 40% | 1.28 |

With 327 people, first setting: RATIO's interval was 0.56 to 0.90 either way, and the planted half was seen in 30% to 63% of worlds.

**What it changed.**
- The registered contrast of row NT1 is RATIO. The plain difference is filed and given no verdict.
- The row runs in two stages. The repository's own persistence grid on the same diary found little carried to the next activity, which puts the real diary near the second setting, where this design cannot decide. So the row first measures what is left, and fetches the trait file and reads RATIO only if enough is.
- The card's outcomes cover every pattern these worlds produced, including a negative RATIO that is saturation and not a finding.
- The small status diary is a description for this row.
- The same contrast is used at day level inside the sealed job (table NT1.s).

**One departure from the specification.** The helper fitted the logit with its own Newton routine, because the usual library was not installed, and drew people by weights, which is the same as duplicating their rows. The analyst checked both in the code.

## 2. Can a held-out count recover how many separate things lie between ratings and words? (`pf_rank.py`)

The curator asked for a way to see whether nine is the right number. The engine's card TP37 counts the dimensions that held-out data supports between a writer's 21 ratings of an event and the feeling word. Each world: 21 correlated ratings, K hidden channels each reading three ratings, 13 words each built from one or two channels. Two counts: the smallest number of dimensions within one standard error of the best held-out fit (first count), and the largest number up to which each added dimension helps by more than two standard errors (second count). Twenty worlds a row; median and range.

| Reports | Planted | Strengths | First count | Second count |
|---|---|---|---|---|
| 6,600 | 5 | equal | 5 (4 to 5) | 5 (5 to 5) |
| 6,600 | 5 | falling | 5 (4 to 5) | 5 (5 to 5) |
| 6,600 | 9 | equal | 8 (6 to 9) | 9 (7 to 9) |
| 6,600 | 9 | falling | 6 (4 to 8) | 7 (6 to 9) |
| 6,600 | 12 | equal | 9 (7 to 10) | 10 (9 to 11) |
| 6,600 | 12 | falling | 6 (5 to 9) | 7 (5 to 9) |
| 1,500 | 9 | equal | 6 (5 to 8) | 7 (6 to 8) |
| 1,500 | 9 | falling | 4 (3 to 6) | 5 (3 to 6) |

**A world meant to break the form** (`pf_rank_results_nonlinear.txt`): ratings on a five-point scale piled at the low end, and channels that fire only past a threshold. 6,600 reports, equal strengths.

| Planted | First count | Second count |
|---|---|---|
| 3 | 3 (2 to 3) | 3 (3 to 3) |
| 5 | 4 (4 to 5) | 5 (4 to 5) |
| 9 | 7 (6 to 8) | 8 (6 to 9) |

Neither count exceeded the planted number in any of the 300 worlds.

**What it changed.** TP37's reading rule is written before the data: the count is read as a floor. A count under nine does not say there are fewer than nine channels, because nine of uneven strength read as six or seven. A count of ten or more is a lead that at least ten separate things shape the word. The card reports both counts and leans on the second. This is what 300 worlds showed and not a proof, and the fixture folds by report where the card folds by writer.

## 3. The result sheet's renderer (`dot_table.py`)

Draws a table of signed numbers as dots on a dark background, 680 units wide: white for positive, red for negative, area in proportion to size, blank where the interval includes zero, no text under 9.5 units. `demo_cells.csv` and `demo_cells.png` are an invented example. Two runs gave the same file byte for byte.

## 4. Public records read, with no data row opened

| What | Read from | Result |
|---|---|---|
| Do the two status diaries carry a Neuroticism score, and how many prompts a day? | The public item lists of the two members; the study's data paper through a page summary | Six prompts a day for fourteen days, at least 40 minutes apart, time-stamped. No trait in the momentary tables. The data paper reports a person-level questionnaire on the first and sixteenth days (a Big Five short form in the large sample, sixteen Neuroticism adjectives in the small) and a public deposit under CC BY 4.0. So the leg is not parked for want of a score |
| Does any held open diary ask whether an event was settled? | A keyword scan of the public item lists of the 63 members in the catalogue copy the analyst read | None found. The one hit is a time stamp. The leg's settled half is parked for open diaries |
| Is the settled-or-not contrast already in print for the sealed daily diary's family? | A title lookup | Yes: [Witzel and Stawski 2021](https://doi.org/10.1093/geronb/gbab006), title and abstract opening checked, paper not opened. The sealed job's table is labelled a replication |
| What did the repository's own persistence card find on the large diary? | The repository's theory row for it, and the checker's reading of the result record | Its primary was inconclusive with limited sensitivity; by the checker's reading, anger carried at about 0.07 to 0.09 in standard units |
| Are the engine's held-out reports the ones strangers re-read? | The engine's loader at the branch head | Yes: the 1,200 held-out report ids are the re-read reports, five re-readers each. So a human reference sits on the same reports as every panel |
| Paper identifiers in the two packets | Lookups by identifier | Each title matched. A paper not opened is marked so where it is cited |

## 5. Computed bars

- **TP34.** The first draft's bar treated each named channel as having one chance in three. The checker pointed out that a reader knowing only pleasant from unpleasant would already score about ten or eleven of nineteen that way. The bar is now the 95th percentile of the score over all 17,280 ways of dealing the named sets among words of the same side, computed by the engine on its own table.
- **TP35.** With about 550 reports to a feeling word, a standardized slope has a standard error near 0.043. A slope of 0.12 is seen four times in five, and a difference of 0.17 between two words.

## 6. What this pre-flight is not

- It is not a result. A fixture says a form recovers what was planted in the analyst's world.
- The worlds of section 1 have one kind of event and a trait that acts in proportion. Four worlds break the form; others would too.
- The worlds of section 2 have sparse recipes. One of them has five-point ratings and thresholds; none has writers.
- The engine's reading cards have no pre-flight. Running a reader on their texts here would have turned the engine's tests into replications of numbers the analyst had seen.
- The queue sizes in the engine's packet are arithmetic on one day's recorded speeds.
