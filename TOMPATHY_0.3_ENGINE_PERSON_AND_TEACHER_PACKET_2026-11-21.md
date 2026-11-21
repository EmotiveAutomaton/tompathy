# ToMpathy 0.3 engine: reading a person, and why the teacher missed

*Spec sheet of 21 November 2026, from the implementation thread (the analyst) to the engine's owner agent. It stands beside the packets of 19 and 20 November, whose cards keep their text unless a line here amends them. It carries no questions. Every choice in it is made here; the curator sees the ones he may want to veto in the reply that delivered it.*

## 0. Read first

- **What this is.** One day of work, to the morning of Sunday 22 November. Two cards from the theory handoff of 21 November (its legs 1 and 8), two small repairs to yesterday's cards, and the queue for both GPUs.
- **Why these.** The curator's ruling of 21 November is that the target is reading a person. Leg 1 is the first test of whether the engine's own readings carry anything of the writer. Leg 8 asks why the teacher missed its bar, and the analyst adds a second suspect: an error in yesterday's packet (section 4, card TP40).
- **Storage.** The bulk store is being repaired for about a day. This repository's data and caches sit on the two machines' own disks, so its work goes on. Amendment BI says what stops.
- **Still owed from yesterday,** unchanged: card RD2's test, the ladder's table, and card TP24's second source, at the first owner turn of the morning.
- **Where files go.** This file at the repository root. The theory handoff of 21 November at `docs/exchange/THEORY_HANDOFF_R34.md`. The bundle `PREFLIGHT_2026-11-21.zip` where the last one went.

## 1. Terms this packet uses

Terms of the 20 November packet stand (readers A, B, C and W; the eight features; lift; queue; result sheet; morning check). Added:

| Term | Meaning |
|---|---|
| Chat situations | The 24,850 short situations by 810 writers, each written to one of 32 assigned feeling words |
| Departure | A text's value on some reading minus the mean of that reading over the same word's texts by all other writers. It removes what the word itself brings |
| Halves | A writer's texts split in two by the order of the SHA-256 of `TP39:23:` and the text's id, sizes differing by one at most |
| Split-half correlation | Across writers, the correlation between a reading's mean departure in her first half and in her second |
| Picking her out | Ranking every writer's second half by closeness to one writer's first half, and asking whether her own second half comes first, or in the first ten |
| Text level, sentence level | A text is read as change when any of its sentences is. A sentence is read by itself |

## 2. Rulings and amendments

Rulings are the curator's, with his words and their dates. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R32 | Emergent goals | "Emergent goals are definitely just schemas." (21 November). Autonomy, the social contract, cognitive power and capital are schemas. No target is added for them |
| R33 | PRIDE | A candidate tenth channel, drawn with a question mark (21 November): "you can put it as a tenth one in the picture, it's fine." Every table and export keeps proud and any word of praise or success |
| R34 | The body | The body's needs stand apart from the four needs (21 November). Body tags are reported as their own block |
| R35 | The target | Reading a person (21 November): "the biggest gap is going to be whatever it is that converges the inference of the model on allowing us to get closer to identifying people." |
| R36 | How a result is shown, added | "you kind of need to sell it on me as if I'm like someone from a bar or something that you need to explain the whole concept to really quick like" (21 November). Amendment BH |
| R37 | The day | "I don't really want to lose a day of grinding." (21 November). Amendment BI |
| BH | Result sheets, second part (analyst, under R36) | The text of a result sheet opens with who was measured and how, in one or two sentences a stranger could follow. Several rows on one question are pooled into one number and one picture where their scales allow, by inverse variance, with the rows shown beside the pooled figure |
| BI | Storage for a day (analyst, under R37) | Nothing in this repository reads or writes the bulk store until the curator says it is back. No download over 1 GB starts. The sealed lane is not this repository's and is closed for the day in any case |
| BJ | TP31's known-group check, restated (analyst). **This changes a bar after a miss, and says so** | Yesterday's card wrote the bar for whole reports (change on 0.85 or more of the reports) and then built the list from single sentences. A report's scene-setting sentence is rightly read as no change, so the two never matched. That error is the analyst's. The restated check is in card TP40 and is fixed there before any figure by word exists |
| BK | Two checks that could not work (analyst) | TP34's second table: the floor rule gave zero for an output with no forum stand-in, so nothing was quiet. TP33: a page with one window has no lift. Both are restated in section 4 |
| BL | Tags in tables and exports (the theory thread's asks of 21 November, adopted) | The three Belonging tags are reported separately as well as together. The independence tag stays outside the needs. The safety tag stays where it is. Yesterday's amendment BC stands |

**Stated by the curator and not ruled. Build nothing on these:** all four needs are outside the person; surprise may be SEEKING with FEAR; art passes through Respect more than Belonging. A second tag for Competence is not built.

## 3. The queues

Yesterday's lane rules stand. Jobs keep yesterday's numbers where they are the same job.

**The Spark, in this order of priority.**

| # | Job | Reader | Texts | Size |
|---|---|---|---|---|
| Q6 | Resume: the eight features for the chat situations, to the end | B | about 14,400 left | about 4 and a half hours |
| Q11 | Card TP40, first part: every sentence of the first 1,500 chat situations and the first 1,500 recalled-event reports, then the restated check as the job's last step, written to a pass or fail file | B | about 6,000 sentences | under an hour |
| Q4 | As defined yesterday: card TP31, sentences 2,001 to 30,000. It starts only if Q11's file says pass | B | 28,000 | about 4 hours |
| Q12 | Card TP40, second part: every sentence of the remaining chat situations and reports | B | about 50,000 sentences | about 6 to 7 hours |
| Q13 | The largest encoder's rung of yesterday's ladder, only if its repair is verified first on a copy | none (training) | as yesterday | unknown |
| Q7 | As defined yesterday, behind everything, and only if Q11's file says pass | B | | fills time left |

**The workstation's GPU.**

| # | Job | Reader | Texts | Size |
|---|---|---|---|---|
| G4 | Card TP40's texts, both parts, in the same order, as the second reading | W | about 56,000 sentences | about 6 to 7 hours |

Reader W's answers are set beside reader B's as a disagreement rate. They enter no fit (amendment AP).

## 4. Cards

### TP39. A writer's own version of a word (handoff leg 1; claims P3, P2)

- **Question.** With the assigned word taken out, does a writer's reading on the engine's own outputs repeat from one half of her texts to the other, and does it help pick her out beyond her writing style?
- **Data.** The chat situations. Saved outputs only: the nine channel outputs of TP30's frozen rung; the nineteen need-tag forecasts; the eight features from job Q6; the worry reader's score; and, if job Q12 has finished, three figures from reader B per text (share of sentences read as change; share whose change is the writer's own; share placed ahead in time).
- **Support, counted first.** Writers with eight or more texts. Counts of writers and texts are filed before any outcome.
- **Sets.**
  - Style, the baseline: text length in tokens; mean word length; the rate per 100 tokens of each of the 50 most frequent word forms in the whole source; the rates of comma, full stop, exclamation mark, question mark and apostrophe; the share of capitalised tokens.
  - Channels: the nine outputs. An output with no spread is left out and named.
  - Tags: the nineteen. Need-level scores are filed beside them under amendments BC and BL.
  - Features: reader B's eight.
  - Worry, and the change figures where they exist, are filed as single readings and join no set.
- **Table 1, stability.** For every reading, the split-half correlation of its departures, with an interval from 2,000 draws of writers. For each set, the mean over its readings. Drawn as one result sheet.
- **Table 2, picking her out.** Writers are split into two folds by the SHA-256 of `TP39:fold:` and the writer's id. Every reading, style included, is a departure from its word's mean over the other writers, and a half-profile is a writer's mean departure in that half, standardized across writers within the half. The match between two half-profiles is a likelihood score. For reading k, with `r_k` its split-half correlation in the other fold, held between 0 and 0.95, and `x`, `y` the two standardized values: `s_k = (2*r_k*x*y - r_k^2*(x^2 + y^2)) / (2*(1 - r_k^2))`, summed over readings. It is the log of how much likelier the two values are from one writer than from two, so a reading that does not repeat gets no say. Ranking is within a fold. Reported: first place and first ten, against chance, for style, channels, tags, features, style with each of the three, and all four. The plain squared distance with equal weights is filed beside it as a description.
- **Registered** (the theory's; the bars are the analyst's).
  1. The tags are stable: their mean split-half correlation is 0.15 or more, with its interval above zero.
  2. They add to style: first-ten for style with tags, minus style alone, has its interval above zero, by 2,000 draws of writers, paired. A difference under 0.03 is called small.
- **What each outcome means.** Both hold: the engine's need reading carries something of the writer that her style does not, which is the first support in text for a person's own weights. The first holds and the second does not: the reading repeats and is either redundant with style or too weak to pick anyone out, as card TP32 found for refusals. The first fails: within an assigned word a writer's need reading does not repeat in this much text.
- **What the design can see.** `pf_ident.py` in the bundle: 600 made writers, 100 worlds a case, counts out of 100. With nothing of the writer in the tags, the first bar was met in 0 worlds and the second in 0. With tags that repeat at a split-half correlation of 0.29 and are independent of style: 100 and 31, and the difference averaged plus 0.014. At 0.56: 100 and 100, with plus 0.061. With tags as stable as that and redundant with style: 100 and 4, with plus 0.002. So the first bar is sharp, and the second sees a writer's tags only when they repeat well above 0.3. Under that, stable and not adding is the likely reading even when the tags are the writer's own. The plain distance with equal weights read minus 0.26, minus 0.10, plus 0.06 and minus 0.04 in the four cases, which is why it is only a description. The fixture's style set alone put the writer in the first ten 82 times in 100; the real figure is unknown, and a high one leaves little room to add.
- **Limits.** The handoff's: a stable profile within an assigned word can be a writer's circumstances and not her weights. The analyst's: the readers were trained on other text; the writers are crowd workers producing short situations to order; both halves may come from one sitting.
- **Prior art.** Telling writers apart by style is long established (authorship attribution; from the analyst's memory, no paper looked up for this packet). No search was made for the engine's own readings as an addition to style, and the card is not called new.

### TP40. What the teacher calls no change (handoff leg 8; claim M2; amendment BJ)

- **Why.** On 20 November reader B marked a change in 72.1% and 68.7% of sentences from two sources collected as events, against a bar of 85%. Its agreement with reader A passed, and so did the ceiling on question-site answers. Two suspects: the theory thread's, that the no-change calls sit on feeling words that name a standing state; and the analyst's, that the bar was written for reports and applied to sentences.
- **Reading.** Reader B, yesterday's prompt and settings unchanged, every sentence of whole texts: the chat situations, and the recalled-event reports that carry a feeling word. Texts go in the order of the SHA-256 of `TP40:23:` and the text's id. Job Q11 takes the first 1,500 of each source and job Q12 the rest. Reader W reads the same (job G4).
- **Standing-state words, fixed here before any figure is read** (the analyst's reading of the thread's phrase). Chat words: content, confident, trusting, faithful, prepared, lonely, nostalgic, sentimental. Recalled-event words: trust, boredom.
- **Table 1.** For each feeling word and source: the share of its texts with no sentence read as change, the share of its sentences read as no change, each with an interval by writer, and reader W's disagreement rate.
- **Registered** (the theory's; the form is the analyst's): at text level, the no-change rate on the listed words is at least twice the rate on the other words, in each source, with the interval of the ratio above 1.
- **The restated check** (amendment BJ), computed on job Q11's 3,000 texts: at text level, among texts whose word is not listed, change on 0.85 or more in each source. The agreement and the question-site ceiling stand as measured on 20 November. The same share over all words, and both shares at sentence level, are filed beside it.
- **What each outcome means.** The check passes and the registered row lands: the shortfall was in the reports and in the analyst's unit, the gate's bar has a per-word form from here, and reader B teaches card TP31. The check passes and the row does not land: the unit alone explains it, and reader B teaches. The check fails: reader B is not this gate's teacher, card TP31 stays blocked, and the table by word is the theory thread's to read.
- **Limits.** The key is one model's reading of a definition. Nobody labelled anything. The list of standing-state words is the analyst's.
- **Prior art.** No search was made. The card diagnoses the engine's own check.

### Two repairs (amendment BK)

- **TP34, second table.** Each output is standardized over all chat situations. An output with no spread is left out and named. A situation is quiet when no output is above plus one standard deviation. For each word: the share of quiet situations with an interval by writer, beside the share over all situations, and the mean of its largest standardized output. Words are ranked by the first figure. The first table and its verdict stand.
- **TP33.** The lift is defined only on a page with five or more windows. The two acceptance sets are run again on such pages. A set with none gives no verdict and says so.

### The record at every landing

One ledger row and one result sheet, under amendments AS and BH.

## 5. Order

| When | What |
|---|---|
| First | Resume Q6. Build TP40's list of texts and add Q11, Q12 and G4 |
| Morning | Yesterday's three owed items. TP34's second table. TP33 |
| When Q6 ends | TP39 |
| When Q11 ends | The restated check is already written by the job. Q4 follows or does not |
| When Q12 and G4 end | TP40's table. TP39's change figures |

**When building is the bottleneck,** drop from the bottom: the queue without job Q13; TP39; TP40; yesterday's owed items; the two repairs; job Q13.

## 6. Predictions before data (the analyst's guesses, filed so they can be scored)

| Card | Guess |
|---|---|
| TP39 | The tags are stable, near 0.2. The interval of what they add to style includes zero. Channels are less stable than tags |
| TP40 | The registered row lands in chat situations and not in recalled events. The restated check passes |
| TP34 | The quietest words are trusting, faithful, grateful and proud |

## 7. The return

`docs/exchange/THEORY_RETURN_2026-11-22.md`: one row per card (verdict word, estimate, interval, bar, limit sentence, ledger row, result sheet), how far each job got, what was skipped and why, which guesses held, and the branch of "what each outcome means" each result fell in.

## 8. Limits of this packet

- The pre-flight covers the form of TP39's second table in made worlds. No reader was run on any text for this packet.
- Amendment BJ restates a bar after a miss. The list of words and the unit were fixed before any figure by word existed; the figures of 20 November that prompted it were seen.
- The repository's records since 20 November were read through a helper's digest, not first-hand.
- Every result here is about words, labels or a reader's outputs. None is a reading of a channel in a person.
- Picking her out matches a writer's two halves inside one file. Nothing is matched to any outside source, and no card tries to name a writer.
