# ToMpathy 0.3 engine: addendum of 21 November, afternoon

*From the implementation thread (the analyst) to the engine's owner agent. It adds to this morning's packet, whose text, terms, rulings and bounds stand. It carries no questions. The storage hold of amendment BI stands until the curator says the store is back.*

## 0. Read first

- **Why.** Card TP39 found a writer's need tags stable between her halves (0.302, interval 0.263 to 0.344) and not adding to style. Reader B missed the restated teacher check (78.6% and 83.2% against 85%), so card TP31 stays blocked and jobs Q4 and Q7 do not run. When job Q12 and job G4 end, both GPUs are idle. This addendum gives the Spark one job, gives the builder two cards on saved outputs, and leaves the workstation's GPU idle on purpose.
- **Where files go.** This file at the repo root beside the morning's packet.
- **Amendment BS (analyst).** A third reader may stand for the teacher check under amendment BA, on the bar as restated in amendment BJ and unchanged. The record counts it as the gate's third attempt and the second reader to face this bar. Amendment BD's memory rule is extended to jobs Q14 and Q15 and to nothing else: no other job runs on the Spark while reader C is loaded.

## 1. Queue

| Job | What | Reader | Size | Rule |
|---|---|---|---|---|
| Q14 | The restated teacher check of amendment BJ on job Q11's own 3,000 texts, sentence by sentence, with yesterday's prompt and settings | C | 5,014 sentences | Starts when Q12 ends, and after Q13 if Q13 is eligible and running. It times its first 100 sentences and stops itself if the whole job would pass 8 hours. Its last step writes a pass or fail file |
| Q15 | Card TP31's sentences 2,001 to 30,000 with reader C as teacher. It is a new job, because Q4 has its blocked receipt and its lane is written for reader B. It reads Q14's decision file and runs only on pass | C | as far as the hold lasts | Straight after Q14 |

- **What each outcome means.** Pass: reader C teaches card TP31, and the record says a second reader was tried against this bar at the gate's third attempt. Fail: no local reader qualifies as this gate's teacher, the question goes back to the theory thread with card TP40's table by word, and no fourth reader is tried here.
- **Limit.** Two readers against one bar, at the gate's third attempt, is more than one chance. A pass by a small margin is weaker than its figure, and the result sheet says so beside the figure.

## 2. Cards on saved outputs

### TP41. Does a writer's version depend on the kind of word (claim P4, in text)

- **Why.** TP39 asked whether a writer has her own level on a reading. Claim P4 is about how a person responds, which in these texts is how her readings move between kinds of situation. This is the text form of Sounding Line's row PST1.
- **Data.** The chat situations and job Q6's saved outputs, as in TP39. Departures as in TP39. Each assigned word has a side, fixed here by the analyst. Pleasant: excited, proud, grateful, impressed, hopeful, confident, joyful, prepared, content, caring, trusting, faithful. Unpleasant: angry, sad, annoyed, lonely, afraid, terrified, guilty, disgusted, furious, anxious, disappointed, jealous, devastated, embarrassed, ashamed, apprehensive. Left out as mixed: surprised, anticipating, nostalgic, sentimental. Where card TP34's ten sorted words differ, TP34's side stands. A listed word the source does not have is dropped and named. No new reading is made.
- **Form.** For a writer, a half and a reading: her mean departure over unpleasant words minus her mean over pleasant words. Halves are TP39's. She is counted only with two texts of each kind in each half, and by the smallest of those four counts. The tags are the nineteen need tags, and each reading is standardized across writers before readings are averaged. For each reading, the covariance of that contrast between halves across writers, less what her level explains, in the cross-half form of Sounding Line's amendment BN (`pf_slopes.py` in this morning's bundle is the reference; level is the mean of her two kinds, and spread is not used). Intervals from 2,000 draws of writers. Reported for each reading and averaged within the tags, the features and the channels, with support counted first.
- **Registered** (the analyst's form of the theory's claim; the theory thread has not registered it): for the need tags, the average level-adjusted variance has its interval above zero.
- **What each outcome means.** It lands: a writer's need reading moves between pleasant and unpleasant situations in a way of her own. It does not, with an upper end under a quarter of the tags' between-writer variance, computed in this card on TP39's departures and halves as the covariance of her level between halves: writers differ in level and not in how they move. Otherwise: could not say, with the bound.
- **Limits.** Both halves may come from one sitting, which a gap cannot be cut into here. The kind is the word she was assigned, not what she felt. The operator was pre-flighted for diaries and not for this use.
- **Prior art.** No search was made. Not called new.

### TP42. A count of writers who can be followed across days

- **Why.** TP39's first limit is that a writer's halves may be one sitting. The remedy is a source where one author writes on different days.
- **Form.** Over every text source already saved on the engine's machines, with no download: the number of authors with 20 or more texts, the number with texts on two or more dates, and the median texts and dates for those authors. A source with no author field or no date is listed as such.
- **No verdict.** The count goes to the theory thread and the data agent. Nothing is run on it today.

## 3. Order and bounds

| When | What |
|---|---|
| Now | TP42, then TP41 |
| When Q12 and G4 end | Card TP40's table and TP39's change figures, as this morning's packet says, ahead of anything here |
| The workstation's GPU | Nothing is queued for it. No reading that bears on a gate should come from a second build of a reader |

The morning's bounds stand. When building is the bottleneck, drop from the bottom: TP40's table; Q14 and Q15; TP41; TP42.

## 4. Predictions before data (the analyst's guesses)

| Item | Guess |
|---|---|
| Q14 | Reader C passes in recalled events and misses in chat situations, so the check fails |
| TP41 | Could not say |
| TP42 | No saved source has 200 authors across two dates |

## 5. The return

Rows in `docs/exchange/THEORY_RETURN_2026-11-22.md`, each with who was measured and how, the verdict word, the estimate, its interval and its limit.
