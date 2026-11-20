# Pre-flight summary, 19 November 2026

What the analyst computed before writing the two packets of 19 November, and what each result changed. Scripts and outputs: `PREFLIGHT_2026-11-19.zip` (folders `sl/` and `spark/`). One pass in one morning, then a second after the independent check. Every script was replayed from the bundle and reproduced its saved output byte for byte on the analyst's machine; the receiving repositories reproduce every number before relying on it.

No dataset was opened. Every number below comes from a constructed world and says nothing about people. The diary items named in the packets were read from openESM's public metadata repository (variable names and wordings), and no diary row was read.

## 1. Can a word's recipe be told from a channel's trigger (`sl/pf_recipes.py`)

The Round 29 handoff asks for one evening's made world before the new diary legs: when the events in a diary come correlated, can a word's recipe still be told from a channel's trigger? The world is the handoff's equation in its linear form. A moment has rated features. Each channel answers the features by its row of a trigger table. Each feeling word answers the channels by its row of a recipe table. The diary shows the features and the words, never the channels.

| Question | Result (medians over 40 worlds unless said) | What it changed |
|---|---|---|
| Is the product of the two tables recovered when events are correlated at 0.8 and most answers sit on the floor? | yes: 0.994 correlation with the truth | correlated events are not the obstacle |
| Is the space the words move in found? | yes: smallest cosine with the true space 0.97 to 1.00 from the table of coefficients, and 0.97 to 1.00 from the leftover co-movement of the words | |
| Are the two tables recovered separately with nothing else assumed? | no. Inside that space the axes are a guess (0.91 to 0.97 match after a sparse rotation, in a world built sparse) | a diary contrast reads a word's answer to an event. It never reads a trigger by itself. Every row of the lattice is stated as a word |
| With one word taken as a pure marker of each channel (an anchor)? | recipes of the other words at 0.99 when the anchors answer the rated features differently enough | new card LD4 |
| When the anchors answer alike (condition number of their rows 15 or more)? | 9 of 40 worlds with six rated features; median recipe correlation 0.45 there. With thirteen rated features every world's recipes came back above 0.9 | LD4 uses every rated feature of the interaction prompts and reports the condition number first |
| When an anchor leaks into a neighbouring channel by 0.1, and by 0.3? | 0.989 and 0.948 | anchors are named in the packet and their choice is a stated assumption |
| Do recipes from interaction prompts agree with recipes from solitary prompts (the other words only; the anchors are left out)? | 0.98 when words keep their meaning; 0.02 in a rival world where the other words mean something else when alone | LD4's one registered test |
| At the size of trigger the status diary showed (weights cut to 0.3)? | 2,272 people: recipes 0.991, agreement across contexts 0.951 (worst of 20 worlds 0.836); the rival at the same size: minus 0.064 (highest 0.420). 327 people: recipes 0.913, agreement 0.736 | the large member carries LD4; the small one is a description |

A recipe needs at least as many rated features as anchors. That is arithmetic and not a finding: five anchors on the eight solitary features at most.

## 2. Known answers for the new diary cards (`sl/pf_fixtures.py`)

**A rating floor can fake two of the handoff's designs, and the form that fixes it has a blind spot of its own.** The worlds put 73% to 89% of answers to a bad feeling on the scale's lowest point; that share is an assumption, and each card reports the real one. Two forms are compared. Raw ratings: the handler's linear form. Above the floor: whether the answer is above the lowest point, on the logit scale (Form O in the packet).

LD1, a failure's link to shame after interactions against after time alone, as a difference of differences with sad as the comparison feeling (30 worlds each, 2,272 invented people; spread in brackets):

| World | Raw ratings | Above the floor, logit |
|---|---|---|
| A. the curator's row planted (0.30 against 0.15) | plus 0.092 (0.018) | plus 0.237 (0.045), seen in every world |
| **B. no difference planted; shame alone has the heavier floor** | **plus 0.047 (0.018): a false positive** | minus 0.010 (0.051) |
| B2. the same, and sad has the heavier floor too | plus 0.003 (0.018) | plus 0.005 (0.056) |
| D. rival: company sharpens every bad feeling alike | minus 0.007 (0.018) | plus 0.008 (0.044) |
| F. no difference; both feelings 1.5 times noisier when alone | minus 0.004 (0.017) | plus 0.019 (0.039) |
| **G. no difference; shame alone 1.5 times noisier when alone** | plus 0.030 (0.018) | **plus 0.106 (0.044): a false positive in 67% of worlds** |

What it changed: amendment AH, in its corrected form. A card that compares a slope across contexts, strata or levels of a second rating reads the above-the-floor form as its primary, because that form is not moved by a shifted floor (world B). It is not a cure. A logit slope is the true slope divided by the noise in the answers, so a feeling whose answers are noisier in one context reads as a flatter slope there (world G). The comparison feeling takes out noise that both feelings share (world F) and nothing takes out noise that only one has. LD1's verdict says so, and the card files the ratio of slopes for every feeling so a shared ratio can be seen. World G was the independent checker's; the first edition of this summary claimed more for the form than the fixture showed.

LD2, the status check as a product (criticism times how far I took the lead, on angry minus the fear-like feelings; 40 worlds each):

| Planted product | Raw ratings | Above the floor, logit |
|---|---|---|
| **none** | **plus 0.0091 (0.0101); 15% of worlds past two spreads** | minus 0.0072 (0.0215); 3% |
| 0.04 | plus 0.053, always seen | plus 0.072, seen in 90% |

The handoff's leg A4 as written (products on raw ratings) would lean toward its own prediction. The same blind spot applies: if taking the lead makes a feeling's answers noisier, the logit form reads a product.

LD2, the status check by the other person's role. Under assumed shares (3% of one-partner interactions with a supervisor, 4% with an employee or a child) a world of 2,272 people holds 447 and 543 such prompts, and 84 and 89 of them with any criticism. The fixture has one fear-like rating standing for the three.

| Planted tilt | Raw ratings | Above the floor, logit |
|---|---|---|
| none | minus 0.004 (0.091) | minus 0.020 (0.206) |
| 0.05 | plus 0.119; seen in 25% | plus 0.226; seen in 25% |
| 0.10 | plus 0.241; seen in 72% | plus 0.473; seen in 62% |
| 0.20 | plus 0.482; always | plus 0.949; always |

What it changed: the role form counts its support before any outcome is read, its bar is 0.40 on the logit scale (two spreads), and the scored form of LD2 is the product with own conduct, which uses every interaction prompt.

**The lattice score.** With R rows whose interval excludes zero and k of them on the predicted side, the set passes at a level when the chance of k or more heads in R fair tosses is at or under it. At 0.05: 7 of 8, 9 of 10, 10 of 12, 12 of 16, 15 of 20, 17 of 24, 22 of 32, 28 of 44. At 0.01: 8 of 8, 10 of 10, 11 of 12, 14 of 16, 16 of 20, 19 of 24, 24 of 32, 31 of 44. Rows that share a source and a claim count once.

## 3. The sealed-run contract, rehearsed (`spark/`)

The Spark's runner returns only gated totals and withholds everything a job prints. A job that dies on the real file tells the agent nothing but an exit code. The bundle holds a copy of the gate as the setup thread installed it on 19 November (`sealed_gate.py`), a job skeleton (`run_template.py`) and a rehearsal on invented files (`rehearse.py`).

| Case | Job | Gate |
|---|---|---|
| a full invented file (400 people, eight days) | exit 0; a slope planted at 0.30 per unit reads 0.285 per unit | passed |
| a required variable is missing | exit 0; only the status table is written, naming the variable | passed |
| eight people only | exit 12 | nothing to check |
| no data file | exit 10 | nothing to check |
| the count column written as 11.0 | | refused: n is not an integer |
| one row with a count of 7 | | refused: a row has n below 11 |
| a text file beside the tables | | refused: only plain .csv files |

What it changed: the sealed cards of the Sounding Line packet require the skeleton's three habits (a status table in place of a crash, one writer that drops small cells and writes whole-number counts, a fixed table of exit codes) and a structure probe before the first real run.

## 4. What this pre-flight is not

- It is not a result. The worlds are the analyst's. A fixture says an estimator recovers what was planted in that world.
- The made world of section 1 is linear with one squashed variant. It has no attention term, no brakes and no carry.
- The fixtures of section 2 are worlds in which the fitted form is close to the form that made the data. World G shows what happens when it is not, and other departures were not tried.
- The role shares in section 2 are assumed. The card counts the real ones first.
- The engine packet's cards have no pre-flight. Their sources are public and labelled, and running a reader on them here would have turned the engine's tests into replications of numbers the analyst had seen.
- The gate copy is the text of the setup thread's install block. If the installed gate differs, the installed one governs.
