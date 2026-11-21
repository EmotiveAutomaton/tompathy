# ToMpathy 0.3 engine: second addendum of 21 November

*From the implementation thread (the analyst) to the engine's owner agent. It adds to this morning's packet and to the afternoon addendum, whose text, terms, rulings and bounds stand. It carries no questions. The storage hold of amendment BI stands until the curator says the store is back.*

## 0. Read first

- **Why.** Card TP41 passed: a writer's need tags move between pleasant and unpleasant words in a way of her own (0.188, interval 0.141 to 0.227, 270 writers). Its first limit, and card TP39's, is that her halves may be one sitting. Card TP42 found the remedy already saved: the blog corpus has 5,530 authors with 20 or more posts on two or more dates. This addendum asks the same two questions across days, and gives both GPUs work to the morning of 22 November.
- **Where files go.** This file at the repo root beside the two earlier ones of today.
- **Amendment CB (analyst).** The Spark's order after job Q12, and Q13 if it is eligible, is: Q14 as registered; Q18; Q19; then Q15 if Q14's file says pass. This moves Q15 from straight after Q14 to last. The workstation's GPU gets job G11, whose readings enter no gate and no fit. This amends the afternoon addendum's line on card TP42, that nothing is run on its count today. No demographic column of any source is read, and of a blog file's name only the leading author id is parsed. A source's country or site column may be read only to take a mean within it.

## 1. Queue

| Job | Machine | What | Reader | Size | Time |
|---|---|---|---|---|---|
| Q18 | The Spark | The eight features on every report of the second recalled-event source of card TP44 | B | about 7,700 reports | about 2.3 hours at the measured 107 seconds a 100 |
| Q19 | The Spark | The eight features on card TP43's blog texts, whole authors in the card's order. The sampled texts are copied to the Spark first. It times its first 100 texts and files how many authors it expects to reach | B | until 08:00 PT on 22 November or 30,000 texts, whichever is first | the measured speed is for short reports, and these texts are longer |
| G11 | The workstation | The same texts in the same order, with job Q6's eight-feature prompt, as a second reading | W | until 08:00 PT on 22 November | about 36 seconds a 100 |

The frozen need reader is run on all of both cards' texts. It takes minutes and waits for no queue. The nine channel outputs are run the same way if a frozen reader for them runs on new text; if none does, the Channels set is left out and the result says so.

## 2. Cards

### TP43. A writer across days (claims P3, P4 and P2)

- **Source.** The blog corpus already saved. Authors with 20 or more posts on 5 or more dates, ordered by the SHA-256 of `TP43:23:` and the author's id; the first 2,000. For each, every post, or 40 chosen by the SHA-256 of `TP43:post:` and the post's id when she has more. A text is the post's first 150 words, cut back to the last sentence end inside them. Posts under 30 words are skipped.
- **Halves.** By date: the first half of her dates against the second. The gap split is the first third of her dates against the last third.
- **Readings.** Style is card TP39's set. Topic is the rate of each of the 300 most frequent words outside Style's fifty word forms, the list fixed on authors outside the 2,000. Tags are the nineteen need tags. Channels are the nine outputs. Features are reader B's eight, and exist only for authors job Q19 has read. Every reading is a departure from its mean over all other authors. Each tag, channel and feature is then cleared of subject and style: it is regressed across texts on the Topic and Style readings, by least squares with a ridge of 1.0 on standardized predictors, fitted on authors outside the 2,000, and the residual is the reading. The uncleared readings are filed beside.
- **Two passes.** Tables 1 and 2 are computed on all 2,000 authors without Features, and again on the authors Q19 has read with Features. The two are never mixed in one table.
- **Table 1, stability.** For each reading, the correlation across authors between her two halves, on date halves and on the gap split, averaged within each set, with 2,000 draws of authors.
- **Table 2, picking her out.** TP39's likelihood score in two folds. Arms, each added to the one before: Style; Topic; Tags; Channels; Features. First ten against chance, and the paired difference at each step.
- **Table 3, how she moves.** Card TP41's form across days, on the authors Q19 has read. A post is pleasant when reader B's pleasantness is above its unpleasantness by one scale point or more, unpleasant in the reverse case, and otherwise left out. Her contrast is her mean tag departure over unpleasant posts minus over pleasant ones. Its covariance between date halves, less what her level explains, in TP41's form, with support counted first.
- **Registered** (the theory's claims; the bars are the analyst's).
  1. The tags repeat across days once her subjects and style are cleared: their mean correlation between date halves has its interval above zero, and so does the gap split's.
  2. They add beyond style and topic: the paired difference at the Tags step has its interval above zero.
  3. She moves in her own way: Table 3's mean adjusted variance for the tags has its interval above zero.
- **What each outcome means.** All three: the engine's need reading carries something of a writer that holds across days and is not her style or her subjects, which is the strongest support in text so far. The first only: her tags repeat, as her subjects do. The first and third: she has a level and a way of moving, and neither yet tells her from others beyond her words. The first fails: TP39's stability was one sitting.
- **Limits.** A writer's subjects and circumstances repeat across days, and the Topic set removes only what 300 words can carry. The posts are from the early 2000s, the readers were trained on other text, and only a post's opening is read. In Table 3 the kind of post and her tags are read from the same text by two readers. A blog is a public face.
- **Prior art.** Telling this corpus's authors apart by style is long in print (from the analyst's memory; not looked up). Nothing here is called new.
- **Fixture.** The ranking is the one `pf_ident.py` covers. Tables 1 and 3 were not pre-flighted for this source.

### TP44. A second source of recalled events, with the writer's own ratings

- **Source.** The international recalled-emotion questionnaire set (ISEAR). The engine has no copy. Sounding Line's temporary data root on the workstation holds one, with its hash in that root's manifest and its licence recorded as noncommercial research, and that copy is used. Each person reported one event for each of seven feelings and rated it. Columns read: country, city and subject number, which together are the person key (checked by counting seven reports a key), the feeling, the report, her ratings of pleasantness, expectedness and intensity, her four-way answer on who caused the event, and nothing else.
- **Table 1, the readers against her own ratings.** Across reports, and within each feeling: reader B's pleasantness with her pleasantness; reader B's suddenness with her expectedness, sign reversed; reader B's own and other responsibility as means within each of her four answers on who caused the event. Card RD1's figures on the first source are set beside these and are not a bar.
- **Table 2, a person across feelings.** Tags as departures from the mean of her feeling within her country and city, cleared of Style as in card TP43. The figure is the average over all 35 splits of the seven feelings into four and three. The tags' mean correlation between halves, with 2,000 draws of people.
- **Registered** (the analyst's forms; the theory thread has registered neither). Table 1: pleasantness agrees across reports, with its interval above zero. Table 2: the tags' mean correlation has its interval above zero.
- **What each outcome means.** Table 1 lands within a feeling too: the reader tracks the writer's own rating and not only which feeling she was asked for. Across reports only: it reads the feeling asked for. Table 2 lands: a person's need reading holds across the different feelings she was asked to recall. It does not: TP39's stability is tied to the word.
- **Limits.** One sitting and one questionnaire. Many reports are translations, by a site's own translator. Within a feeling her ratings have little spread.
- **Prior art.** No search was made. Not called new.

## 3. Order and bounds

| When | What |
|---|---|
| Now | Build TP43's and TP44's lists, run the frozen need reader on both, and register Q18, Q19 and G11 |
| When Q12 and G4 end | Card TP40's table and TP39's change figures, ahead of anything here |
| When Q18 ends | TP44's two tables |
| At 08:00 PT on 22 November | TP43's three tables on what has been read, with the count of authors |

The morning's bounds stand. When building is the bottleneck, drop from the bottom: TP40's table; TP43's Tables 1 and 2 without Features; TP44; Table 3; G11.

## 4. Predictions before data (the analyst's guesses)

| Item | Guess |
|---|---|
| TP43, first | The tags repeat across days, near 0.3, and across the gap |
| TP43, second | Topic takes most of it. The Tags step's interval includes zero |
| TP43, third | Lands |
| TP44, Table 1 | Pleasantness agrees across reports and weakly within a feeling |
| TP44, Table 2 | Lands, under 0.15 |

## 5. The return and limits

- Rows in `docs/exchange/THEORY_RETURN_2026-11-22.md`, each with who was measured and how, the verdict word, the estimate, its interval and its limit.
- Picking her out matches a writer's halves inside one file. Nothing is matched to any outside source, and no card tries to name a writer.
- The counts of authors, the measured speeds and what is saved are from the engine's records through a helper's digest. How many authors have posts on five or more dates is not in the record.
- On the registered order job Q15 will not start before 08:00 PT on 22 November.
