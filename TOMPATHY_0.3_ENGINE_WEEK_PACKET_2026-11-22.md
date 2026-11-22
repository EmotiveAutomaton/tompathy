# ToMpathy 0.3 engine: the week to Friday 27 November

*Spec sheet of 22 November 2026, from the implementation thread (the analyst) to the engine's owner agent. It is the engine's part of the theory handoff of 22 November (Round 35). The packets and addenda of 19 to 21 November stand unless a line here amends them. It carries no questions. Every choice in it is made here; the curator sees the ones he may want to veto in the reply that delivered it.*

## 0. Read first

- **What this is.** Fourteen cards and a queue for the Spark, for the week. Results are read on the morning of Friday 27 November.
- **Why.** The curator's words of 22 November: "with a focus first and foremost, as always, on driving the engine forward." The handoff's tree has three trunks for the engine: reading a person (cards TP45 to TP47), what the engine can display (TP48 to TP53), and triggers, drift and the long histories (TP54 to TP58).
- **Sizing, from what landed.** A card on saved outputs lands within hours here. The slow part is reader B, at 107 seconds a hundred short reports. The one figure on record for blog openings is 137, with the reader not named. Fourteen cards are fewer than this week can build, so the theory thread's midweek round has room to add.
- **One correction comes first** (amendment CP). Card TP43 cleared each tag of style and subject post by post, and its result was read as tags adding beyond style and topic. The pre-flight for this packet shows two things. Clearing post by post removes almost nothing when one post's style readings are noisy: tags that were only a second reading of a writer's style still passed the Tags step in 76 to 100 of every 100 made worlds, wherever the baseline left room. The analyst's stronger adjustments, composites of all 357 readings built three ways, read 0.36 to 0.62 where they should have read zero. The checker's correction for each reading's own reliability read 0.00 and 0.20 at 20 posts in the same worlds, where 0 and 0.2 were planted, but those worlds' readings are uncorrelated by construction and real ones are not. In the checker's later worlds, where the readings were made to correlate, it read about minus 3.1 with nothing planted. Of three further corrections the nearest, a factor fit, read minus 0.045 to 0.141 at nothing at 20 posts and 0.065 to 0.133 at 40. So no adjustment is registered this week. TP43 is read as showing that the tags repeat across days and help tell authors apart, and no more.
- **Storage.** Amendment BI holds until the curator says the store is back. No card here reads the bulk store. Card TP58 is run sealed by Sounding Line.
- **Where files go.** This file at the repo root. The handoff as `docs/exchange/THEORY_HANDOFF_R35.md`. The bundle `PREFLIGHT_2026-11-22.zip` beside the earlier bundles; its `pf_curve.py` is the known answer for card TP45.

## 1. Terms added

| Term | Meaning |
|---|---|
| Qualifying authors | The 5,428 blog authors with 20 or more dated posts on five or more dates |
| Outside authors | Every other author of the blog corpus. They are used only to fit things that must not see a scored author |
| Deep set | Qualifying authors with 80 or more dated posts. If fewer than 600 have that many, the deep set is those with 40 or more and the largest k below is 20 |
| k | Posts read in each half of an author's dates. The posts for a smaller k are among those for a larger one |
| Placebo heads | Nineteen heads with random weights on the same frozen encoder as the need reader, fixed by the seed `TP45:placebo:23` and standardized. They are read and scored exactly as the tags are, and show what any nineteen readings of that encoder do |
| Step | What adding a set of readings does to the rate at which an author's second half is ranked in the first ten for her first half |
| Standing words | content, faithful, nostalgic, sentimental, trusting: the five the handoff names |
| Loudness | For a word and a family of outputs: the standardized mean, over the word's texts, of the one output in the family that leads for that word, with the leader chosen on other writers. Card TP50 |
| Ten outputs | The nine channel outputs and the PRIDE output of card TP48 |

## 2. Rulings and amendments

Rulings are the curator's, with his words of 22 November. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R38 | PRIDE | "I think I'm officially going to call pride as a channel at this point." Ten channels. The theory's claim id is T11. Its trigger is not ruled |
| R39 | Respect and Belonging | "I don't think similarity is a reason to copy." "I think it's a gate." Respect is the reason and sets its strength. Belonging is the gate |
| R40 | How a result is shown | "this style of reporting is absolutely worth carrying forward." A pooled table carries a ring where a guess was registered beforehand and a small X where the result parts from it |
| R41 | Odd results | "if we find weird results, it's worth quickly glancing a research pass at it to see whether other people have found similar weird results". The look is the theory thread's. Amendment CE says what the return owes it |
| R42 | The week | "this is going to be the first one, I think, where we have the full week of the spark burning through." |
| R43 | Smaller rulings, by his agreement to the theory thread's questions | Suddenness is not RAGE's own and is not scored as its trigger. The tag named belonging is on a watch list ("Watch list. Agreed.") and is reported apart from family and contact. The safety tag stays where it is. Nothing is built on stake and expected yield |
| CE | Result sheets, third part (analyst, under R40 and R41) | Amendment BH stands. Added: a pooled table marks each cell that had a registered guess and each cell that parts from it. The return has one line for every result that goes against its registered direction with its whole interval clear of zero, under the heading "Against, and clear". A single result whose interval includes zero is never listed there |
| CF | The store's return (analyst; shared with Sounding Line) | Amendment BI ends when the curator says the store is back, and not before. For the engine nothing changes on that day except that card TP58's bundle may be handed over. Sounding Line's order for that day is in its own packet |
| CG | The queue for the week (analyst) | Section 3. One queue on the Spark. Job Q24 is a filler: it runs only when nothing else is queued and yields to any other job at the end of the author it is on. For job Q24 alone this amends amendment AZ, under which a long job is launched at once |
| CH | Ten channels in every export (analyst, under R38 and R43) | PRIDE is written in capitals with the other nine and is the tenth column wherever the nine appear. The three Belonging tags are reported apart. The independence tag stays outside the needs. The four body tags are reported as their own block. No output is labelled as suddenness's channel |
| CI | The teacher, regraded (analyst; the handoff's leg DS6) | Amendment BS ended the search for a teacher at a miss by reader C. This amends it: the search by a flat share of reports ends there, and card TP53 grades the readers once more against the writers' own ratings, on a bar fixed here. The record counts it as the gate's fourth attempt |
| CJ | A frozen bundle for sealed reading (analyst) | Card TP58. The engine hands Sounding Line a bundle that runs on a CPU with no network. The engine's agent reads no row of a sealed set and receives only what the sealed gate releases |
| CP | What card TP43 showed, restated (analyst) | Its two registered checks stand as filed: the tags repeat across days, and they add to matching. Neither is reported as beyond style and topic. Clearing post by post is called partial clearing. No card this week registers that a reading carries something other than a writer's style and subjects on the strength of an adjustment. Two corrections are run as a description (card TP45, Table 6). The evidence that bears on that is the assigned-word cards (TP39, TP41), where the subject is given, and card TP58, where an outside trait score is the test |

**Stated by the curator and not ruled. Build nothing on these,** though several are tested below as his statements: stress raises the need for play; any large emotion shuts PLAY off; shame leads to isolation; impotent rage becomes sadness and fear is a second channel for fleeing; anxiety joins sadness's trigger to fear's effect; SADNESS reads second derivatives; his list of what should weigh on Competence; a cultural overlay on Respect and Belonging. **No analysis by sex is made anywhere, and no demographic column is read.**

## 3. The queue for the week (amendment CG)

Jobs still running from 21 November finish first as registered: Q19 and G11 to 08:00, then TP43's remaining tables and TP44.

| Job | What | Reader | Size | Time |
|---|---|---|---|---|
| Q20 | The frozen need reader, the worry reader and the channel reader on every opening of every qualifying author, and on whole posts cut into windows (card TP45) | frozen | every dated post of 5,428 authors | minutes to a few hours |
| Q21 | The PRIDE head's fit, its checks, and the ten outputs on every saved text and on every sentence card TP49 reads (cards TP48, TP49) | frozen | all saved texts and marked sentences | under an hour |
| Q22 | The eight features and the sentence reading on the news articles and their essays (card TP56). It times its first 100 texts and files what it expects to reach | B | the set's articles in windows, with their count filed first, and 1,860 essays | a few hours |
| Q23 | Only if card TP53 names a teacher: card TP31's sentences 2,001 to 30,000, then the student's fit as registered. On a pass by job Q14, job Q15 runs as registered instead | the teacher | 28,000 sentences | about 9 hours for reader B |
| Q25 | Only after Q23 or Q15: the roster's remaining sentences in their filed order | the teacher | up to 258,000 | to the end of the week |
| Q24 | The filler. The eight features on the openings of qualifying authors that job Q19 did not reach, whole authors, in card TP43's author order | B | about 94,000 openings | about 36 hours if the one speed on record for openings is reader B's. The record does not name the reader, so the job times its first 100 first |

- Order: Q20, Q21, Q22, then Q23 and Q25 if they open, with Q24 in every gap.
- Job Q24 is not make-work: it widens cards TP51 and TP52 and card TP43's third table from hundreds of authors to thousands. It is also the first thing dropped.
- If neither Q23 nor Q25 opens, the Spark's GPU has about two days of work in this packet and is idle after that. The record says so plainly. No job is invented to fill it.
- The workstation's GPU has no job this week. Its memory is shared with Sounding Line's builds, and a second build of a reader feeds no gate (amendment AP).

## 4. The cards

Every card files a result sheet (amendments BH and CE) and a ledger row with its claim ids. Departures, halves by date, the gap split, Style, Topic, partial clearing, the two folds and the likelihood score are card TP43's unless a line says otherwise.

### Trunk PA: reading a person

#### TP45. The person, scaled up, with a learning curve (handoff leg PA1; claims P3, P2)

- **Why.** It is the engine's own target as a curve: how many of a writer's posts must be read before her settings are known.
- **Reading.** Job Q20. An opening is card TP43's. A whole post is read as windows of 150 words cut at sentence ends, at most 20 a post, and its reading is the mean over windows. Tags are partly cleared as in card TP43, with the Topic list and the fit made on outside authors.
- **Table 1, how fast her settings become known.** On the deep set, for k of 5, 10, 20 and 40: each tag's correlation between halves, raw and partly cleared, on date halves and on the gap split. Beside them the curve a fixed profile would follow (Spearman-Brown, from the k of 5), and the number of posts at which that curve reaches 0.5 and 0.8.
- **Table 2, the step.** On the deep set, in two folds, for each k: the first-ten and first-one rates for Style with Topic, and the step when the tags are added.
- **Table 3, a placebo.** Tables 1 and 2 with the placebo heads in place of the tags.
- **Table 4, everyone.** Tables 1 and 2 at a k of 10 on all qualifying authors.
- **Table 5, whole posts.** Tables 1 and 2 at a k of 20 with whole posts in place of openings.
- **Table 6, a description with no bar** (`chk_beyond.py` and `chk_beyond2.py` in the bundle are the references). At a k of 20, for each tag: its covariance between halves, `V`; the covariance between halves of each of the 357 Style and Topic readings with the tag, taken on two separate halves of the authors (`cA`, `cB`); and the readings' own covariance between halves, the matrix `S`. A correction says how much of `V` to remove. The share left is one minus the sum over the nineteen tags of what is removed, over the sum of their `V`. That pooled share is the form the made worlds tested; shares for single tags are filed beside it and are noisier. Two corrections are filed. Line (a), reading by reading, removes `sum of cA*cB/d`, with `d` the diagonal of `S` floored at twice its standard error. It is exact only if the readings do not correlate with one another. Where they do, it takes the shared part away once for every reading that carries it and falls far below zero, so it is filed as a mark of how much the readings share and is not read as a share left. Line (b), with a factor fit, removes `cA' M cB`, where `M` is the inverse of a fit of `S` by shared factors and a diagonal (`fa_inv` in `chk_beyond2.py`, the diagonal floored at twice its standard error). Line (b) is the one to read, at a k of 20 only, beside the same line for the nineteen placebo heads. With nothing planted, the 95th percentile over made worlds reached 0.247 at 2,000 authors and 0.062 at 5,400, so a share left under 0.25 is not read. Nothing is registered on either line.
- **Registered** (the theory's): the step that tags add grows with the number of posts read, and does not vanish with whole posts. **Bars** (the analyst's).
  1. Grows: the step at the largest k at which Style with Topic is under 0.90 on the first-ten rate, less the step at a k of 5, has its interval above zero, paired over authors and 2,000 draws. If only the k of 5 is under 0.90, the same is read on the first-one rate, and if that too leaves one k the row is declared blind, as the handoff asks. With nothing in the tags this bar was met in 8 of 100 made worlds.
  2. Whole posts: the step in Table 5 has its interval above zero, read on the first-ten rate if Style with Topic is under 0.90 there, on the first-one rate if not, and declared blind if both are over.
  3. The curve (the analyst's): the tags' mean correlation between halves at a k of 5 has its interval above zero, and at the largest k it is within its interval of the fixed-profile curve.
- **What each outcome means.** Bar 1 holds: reading more of her keeps adding to what tells her apart. Bar 1 fails where it could be read: more posts sharpen her style and subjects as fast as her tags, and the tags add no more. Bar 1 blind: the baseline filled first, and Table 1 is the learning curve. Bar 2 holds: the step is not a matter of openings. Bar 2 fails: it is. Bar 2 blind: as bar 1. Bar 3 fails from below: her settings drift, or she writes in spells, and the gap split says which. The tags do no better than the placebo in Tables 1 and 2: what repeats is what the encoder sees of an author, and the need heads add nothing of their own to that.
- **What the design can see.** `pf_curve.py`, 1,500 made authors, 50 worlds a cell. Where the tags were a writer's own, their correlation between halves followed the fixed-profile curve (0.12, 0.21, 0.34 and 0.51 at 5, 10, 20 and 40 posts) and fell short of it only when her profile drifted (0.36 against 0.41 at 40). The step did not grow. It was 0.023, 0.030, 0.002 and 0.000 as the baseline's first-ten rate went 0.40, 0.84, 0.997 and 1.00, and the step at 40 less the step at 5 was above zero in no world. With a weaker baseline it rose to 0.081 at 20 posts and fell to 0.004 at 40, and the first-one rate kept room longer (a step of 0.14 at 20). So growth is readable only while the baseline is far from full, which is what bar 1's rule is for. And a step is not evidence of something beyond style: where the tags were only a second reading of her style it was above zero in 76 to 100 of every 100 worlds, while the baseline was under 0.85. `pf_beyond.py`, at the real count of 357 style and topic readings: composites of all 357 readings, built three ways, left 0.36 to 0.62 of the tags' stable variance in place with nothing planted. `chk_beyond.py` and `chk_beyond2.py`, the checker's: Table 6's line (a) left 0.00 to 0.06 at nothing and 0.19 to 0.23 at a planted 0.2, in worlds whose readings are uncorrelated by construction. In worlds whose readings correlate (the stable parts of the Style readings share one factor at a correlation of 0.3, those of the Topic readings sit in blocks at 0.5, and each tag rests on 10 Style and 20 Topic readings; 2,000 and 5,400 authors, 20 worlds a cell) line (a) left about minus 3.1 at nothing. Line (b) at 20 posts left minus 0.045 to 0.141 at nothing, with its interval above zero in 0 of 20 worlds in each of four cells; 0.247 and 0.207 at a planted 0.2, above zero in 12 and 20 of 20; and 0.545 and 0.504 at a planted 0.5. At 40 posts it left 0.065 to 0.133 at nothing and was above zero in 5 to 19 of 20 worlds. The checker notes that its rule for the number of factors chose 39 where the made world had 31; whether that is the cause was not tested. The intervals hold the fitted matrix fixed, so they are somewhat too narrow and the counts at a planted share are generous. Two corrections that keep only the largest directions of `S` left 0.56 to 0.74 at nothing. That is why Table 6 is a description, read at 20 posts beside the placebo's share. What would make line (b) a check is made tags of known zero, built from the real readings of posts outside both halves, that read zero under it. That is not in this card.
- **Limits.** The handoff's, as card TP43 filed it: "Repeated circumstances and topics beyond the 300 measured words can still account for similarity." The analyst's: within the measured words too, by the pre-flight. The posts are from the early 2000s, and a blog is a public face.
- **Prior art.** Telling this corpus's authors apart by style is long in print (from the analyst's memory; not looked up). Nothing here is called new.

#### TP46. Which needs carry her (leg PA2; claim P2)

- **Setting.** All qualifying authors, every opening, date halves, tags partly cleared as in card TP43.
- **Table 1, leaving one need out.** The step with all tags, and the step without each of: Competence (curiosity); Meaning (order, savings, serenity); family and contact; the tag named belonging; Respect (status, approval, power, competition, honor); Compassion (idealism); the body (food, rest, health, tranquility); and the two unplaced tags (romance, independence). Respect and Compassion are the handoff's names for what this repository's names file calls visibly respectable and visibly compassionate, and under ruling R26 and amendment BC the Belonging and Compassion rows are also given merged. The loss is the first minus the second, paired over authors, and is also given for each tag left out.
- **Table 2, her highest need.** Need scores for each author and half: the mean of the need's standardized tags. Belonging is family and contact, the tag named belonging is its own score (ruling R43), and Compassion is given apart and merged with Belonging (amendment BC). The share of authors whose highest need in the first half is highest in the second, minus the same share when second halves are dealt at random among authors (1,000 deals).
- **Registered** (the theory's): Respect's and the body's tags carry the most; the tag named belonging adds nothing by itself; her highest need repeats above chance. **Bars** (the analyst's): each need's loss is taken less the loss of a placebo group of the same size, and the two largest of those are Respect's and the body's, each with its interval above zero; the loss for the tag named belonging, less a single placebo head's, has an interval that includes zero and an upper end under a quarter of the full step; Table 2's difference has its interval above zero.
- **A reference for size.** The same leaving-out on the placebo heads, in groups of the same sizes drawn at random, says what a group of that many readings loses whatever it reads.
- **Limits.** A need with more tags can lose more by count alone, which is why the loss for each tag and the placebo's loss are beside it. A highest need is the highest reading, not the largest weight. A loss says the need's tags help tell her apart, not that they are other than her subjects (amendment CP).
- **Prior art.** No search was made. Not called new. No fixture beyond card TP45's: the operator is the same.

#### TP47. Her own version of a word, in free text (leg PA3; claim P3)

- **Words,** two forms each, matched as whole words in an opening: sad, sadness; angry, anger; afraid, scared; proud, pride; happy, happiness; lonely, loneliness; anxious, anxiety; ashamed, shame.
- **Form.** For an author, a half and a word: her mean tag reading over openings that use the word, minus her mean over her openings that use none of the sixteen forms. This is card TP41's contrast with the word's presence as the kind. Its covariance between date halves across authors, less what her level explains, by card TP41's operator. She counts for a word only with two openings of each sort in each half.
- **Reported** for each word: authors counted; the tags' mean adjusted variance with its interval, and the same as a share of the tags' variance between authors; the crowd's mean contrast, which is the word's own recipe in this corpus.
- **Registered** (his): the departure is stable, for every word with 200 or more authors counted. Bar (the analyst's): the adjusted variance has its interval above zero. **Registered** (the theory's): the departures are larger for the widened words than for the common ones. The handoff names anxious among the widened and gives no list, so the registered row is anxious against the mean of sad, angry, afraid and happy, with the difference's interval above zero. All eight are filed so that any other grouping can be read off.
- **Limits.** A word in an opening may be denied, or be about someone else. A stable departure can be her kind of occasion and not her meaning of the word.
- **Prior art.** No search was made. Not called new. The operator is the one pre-flighted for cards TP41 and PST1.

### Trunk DS: what the engine can display

#### TP48. PRIDE as a tenth output (leg DS1; claim T11; ruling R38)

- **Fit.** A tenth head on the frozen rung of card TP30, by the same recipe and from the same two sources as the nine, with the pride label of each. The chat situations never enter the fit. Before fitting, the count of texts with a pride share above zero in each source is filed. Under 300 in the comment source is stated as a weak head.
- **Checks.**
  1. Card TP34's second table again with ten outputs. **Registered** (his ruling, the theory's form): proud stops being the quietest word. Bar (the analyst's): proud's quiet share is below the median word's, with the difference's interval below zero, over writers.
  2. On the chat situations: how well the PRIDE output tells proud from joyful, and proud from excited, as the area under the curve. **Registered:** it separates both. Bar: 0.70 or more for each, the bar job G2 set for CARE, with its interval above 0.5.
  3. The nine outputs are unchanged to the last digit, since the heads share nothing but the frozen encoder.
- **A description, with no bar.** The ten by ten table of how the outputs rise together across texts, in each source. And the question the ruling leaves open: do the PRIDE and SHAME outputs sit at two ends of one axis or move apart? Filed as their correlation across texts, and as each one's mean on texts labelled with the other's word, against its mean on all texts.
- **Then** amendment CH applies, and job Q21 reads every saved text with ten outputs.
- **Limits.** A head trained on labels reads what labellers called pride. The events' side of the fit is the reread reports of card TP30's protocol, and their pride count is filed first, with the comment source's.
- **Prior art.** No search was made. Not called new.

#### TP49. A move or a level, sentence by sentence (leg DS2; claim A1)

- **Data.** The sentences of the chat situations and the recalled events that readers B and W have marked. A report counts if it has a change sentence and a no-change sentence on which the two readers agree.
- **Form.** The ten outputs on each sentence. For a report and an output: its mean over change sentences minus its mean over no-change sentences, in units of the output's spread over all sentences of the source. Averaged over reports, with 2,000 draws of reports, for each source and pooled. Filed again with sentence length and position (first, middle, last) regressed out of each output.
- **Registered** (his, that channels read moves): every output is higher on the change sentences, and DISGUST's difference is the least. Bars (the analyst's): all ten intervals above zero in the form with length and position out; DISGUST's is the smallest, and below the median output's with the difference's interval below zero.
- **What each outcome means.** All ten: the outputs follow moves inside a report. Some and not others: the list of which is the finding. None once length is out: the earlier difference was sentence length.
- **Limit,** as card TP40 filed it: "The benchmark measures a model’s definition of change." And the channel reader was fitted on whole comments.
- **Prior art.** No search was made. Not called new.

#### TP50. A need in its band (leg DS3; claim A1)

- **Form.** Writers are split in two. On one half, each word's leading tag and leading output are found: the tag, and the one of the ten outputs, whose standardized mean over the word's situations is highest. On the other half, the word's tag loudness is the standardized mean of that tag over its situations, and its channel loudness the same for that output. The halves are then swapped and the two figures averaged, with intervals over writers.
- **Registered** (the theory's): the standing words are loud on tags and quiet on channels, and event words are loud on both. Bar (the analyst's): the standing words' tag loudness has its interval above zero, so that they have a need of their own to show; their channel loudness is below the other words', with the difference's interval below zero; and the channel difference less the tag difference has its interval below zero.
- **If it lands,** the three states are filed as a proposal for the display: nothing at stake (both low), a need in its band (tags high, channels low), a need on the move (both high). For a text, tags are high when its largest standardized tag is above the median of that value over all situations, and channels likewise. The share of each word's texts in each state is the table.
- **Limits.** Five words carry the standing side. The leader is chosen on other writers so that picking the largest of 19 or of 10 does not make its own loudness. The channel half of this is already in card TP34's second table.

#### TP51. Competence taken two ways (leg DS4; claim N1)

- **Data.** Saved outputs for the chat situations' writers and for the blog authors reader B has read. The count of each comes first.
- **The Competence side** (the analyst's construction, since Competence has one tag): the mean of reader B's goal support, own responsibility and own standards, each standardized. Each of the three is also filed alone.
- **Two numbers** for the curiosity tag against that side, and for every tag against it and against curiosity. Within a writer: the correlation from text to text with her means removed, for writers with five or more texts. Between writers: the correlation of their true averages, as the covariance of means between halves over the root of the two stable variances.
- **Registered** (his expectations of 22 November). Curiosity against the Competence side: below zero within a writer, and 0.3 or more between writers. Savings, status and approval: above zero between writers and under 0.3; power under each of those three; competition under 0.3. The four body tags: their mean between-writer value is above the mean of the other tags'. Independence: above zero, and with status held its interval includes zero. Each line gets its own verdict. There is no pooled verdict.
- **Limits.** Two tags from one reader share that reader's errors on a text, so the within-writer rows between tags are inflated. The curiosity row is across two readers and is the clean one. No second Competence tag is built.

#### TP52. Saying I, and worry (leg DS5; claim S1)

- **Data.** Qualifying authors' posts of 300 words or more.
- **Form.** The worry reader's score on the opening. The rate of I, me, my, mine and myself in the rest of the post, so that the two share no word. Within an author with ten or more such posts, the slope of the rate on worry, both standardized inside the author, pooled over authors with 2,000 draws.
- **Registered** (his): above zero. **Registered** (the theory's): worry is among her steadiest readings. Bar (the analyst's): the worry score's correlation between date halves, less the median of the 19 tags', has its interval above zero.
- **Limits.** The worry reader was fitted on 2,500 writers and explains three tenths of their ratings. Saying I also marks a way of telling a story.

#### TP53. The teacher, regraded (leg DS6; amendment CI). It runs only if job Q14's file says fail

- **Data.** The recalled events with readers' sentence marks and the writers' own ratings of suddenness, of how long the event lasted and of how long the feeling lasted.
- **Table.** For reader B, and for reader C where it read: three summaries of a report (the share of sentences marked as a change; whether any is; the share marked as a change already happened), each against each of the writer's three ratings, as rank correlations with intervals over writers. Reader W's marks are filed beside them and cannot qualify, since a second build feeds no gate (amendment AP). Also beside them: the readers' agreement with each other on each summary, and the agreement of a second human reader with the writer on suddenness that card RD1 filed (0.525).
- **Bar** (the analyst's reading of the handoff's line, that a teacher's marks follow the writers' ratings at the level two readers agree). A reader qualifies when its best summary's correlation with the writer's suddenness is 0.26 or more, half of what a second human reaches with a full rating, with its interval above zero. Which summary is best is chosen on half the writers and scored on the other half.
- **What follows.** A reader qualifies: it teaches card TP31, by jobs Q23 and Q25. None does: no local reader teaches this gate, card TP31 rests, and the table is the finding.
- **Limits.** A sentence mark is a coarser thing than a rating, which is why the bar is half the human figure. Four attempts at one gate are four chances, and the sheet says so.
- If job Q14's file says pass, reader C teaches as registered and this table is filed as a description.

### Trunk TG: triggers

#### TP54. Does control tip anger into sadness (leg TG2; claims T1, T3, A1)

- **The curator's statement:** "impotent rage doesn't become fear it becomes sadness".
- **Data.** The recalled events labelled anger, sadness and fear, with the writer's own rating of her control. A codebook check for that rating comes first, in both sources. A source without one is void here.
- **The same kind of event.** Reports are grouped by which of the writer's three ratings of responsibility is largest (her own, another's, chance). The fit is made inside each group and pooled by inverse variance. The same with the reports grouped by their largest need is filed beside it.
- **Form.** Whether a report is of sadness and not anger, on her control rating, standardized. The same for fear and not anger.
- **Registered** (his): low control goes with sadness over anger; control does little to part anger from fear. Bars (the analyst's): the first coefficient has its interval below zero; the second's interval lies inside half the first's size either side of zero.
- **What each outcome means.** Both: control tips anger toward sadness and not toward fear, as he says. The second coefficient as large as the first: control parts fear from anger as well, the appraisal literature's picture. The first holds and the second sits between: control leans anger toward sadness more than toward fear, short of his statement. The first fails: control does not tip anger into sadness here, whatever it does for fear.
- **Limits.** The writer was asked for a feeling and rated the event afterwards. One report a writer for each feeling.
- **Prior art.** Low power to cope has long been tied to sadness and to fear against anger in appraisal theory (from the analyst's memory; not looked up). The contrast between the two pairings is the question. Not called new.

#### TP55. Anxiety as a loss ahead (leg TG3; claim W1)

- **Data.** Saved outputs for the chat situations of seven words. The sad group: sad, disappointed, lonely. The fear group: afraid, terrified. The anxious pair: anxious, apprehensive.
- **Form.** A word's need profile is its mean over the 19 standardized tags less the mean over all 32 words. Likeness is the correlation of two profiles over the tags. A word's placing in time is the share of its sentences that reader B placed ahead.
- **Registered** (the theory's plain form of his statement). The anxious pair's profile is more like the sad group's than the fear group's: the difference of the two likenesses has its interval above zero, over writers. Its placing in time is nearer the fear group's than the sad group's: the gap to the sad group less the gap to the fear group has its interval above zero.
- **Limits.** The words were assigned. Apprehensive and afraid are near in meaning, which works against the first row.

#### TP56. CARE's first real test (leg TG6; claim T8)

- **Data.** The reactions-to-news set: 1,860 essays by 372 writers, each with the writer's own concern and distress. If the articles' texts are not held they are fetched from the set's public repository, which is small. If they cannot be had, the card runs with each article as its own level and says so.
- **Reading** (job Q22). Each article in windows of 150 words. The handoff asks the need reader for whose need dropped and how far. The need reader says which need a text is about and not how far it fell, so the size of the drop is reader B's unpleasantness less pleasantness, averaged over the article's windows, and the need reader's largest need says which need; the result is also filed by need. That substitution is the analyst's. Closeness is read from her essay: the share of its sentences whose change reader B gives to the writer herself, and her rate of I, me and my, each standardized, averaged.
- **Form.** Inside a writer, with her means removed: concern on the drop and on closeness; distress on the same. Intervals over writers and over articles, and the wider is the one reported.
- **Registered** (his trigger for CARE, the theory's design): concern follows the drop, with its interval above zero; distress follows closeness, with its interval above zero. The two crossed slopes and the two differences are a description.
- **Limits.** Concern and distress rise together. The essay was written after the ratings. Closeness is read from what she chose to say.
- **Prior art.** The set's own paper (the handoff names it; not opened). Not called new.

### Trunk CU: drift

#### TP57. Does a word's recipe drift (leg CU1; claims W1, P3)

- **Data.** The comment source, which carries dates. A count of comments by year comes first.
- **Two forms.** By label: the comments carrying a label, split at the label's median date. By word: the comments that contain one of card TP47's sixteen forms, split the same way. The labels were all given by readers at one time, so the first form asks whether what readers now call a feeling has changed in what it is about, and only the second is about writers' own words.
- **Form.** A profile is the mean of the 19 standardized tags. Drift is the likeness of two random halves of the pooled comments, each the size of the early and late sets, less the likeness of the early and late profiles, with intervals over comments. Filed again with the later period reweighted to the earlier period's mix of communities, which is a field of the comment and not of a person.
- **Registered** (the theory's): the common labels hold their profile. Bar (the analyst's): for the third of labels with the most comments, drift's interval includes zero and its upper end is under 0.10. All labels and words are filed, so that the widened words can be read off.
- **A second look, with no bar.** The eight words in the early blog openings against the same words as assigned in the chat situations, with the difference in kind of text stated.
- **Limits.** A few years of one site. A label is a reader's.

### Trunk SD: the long histories

#### TP58. The map's trait labels (leg SD2; claims S3, T6, T7, P2; amendment CJ). Phase 1

- **The engine's part** is the bundle: the frozen need reader, the worry reader and the ten heads; the Style and Topic code; the code of card TP45's tables; all runnable on a CPU with no network, with a hash for each file and a test on made text. It is handed to Sounding Line, whose row TMP1 runs it sealed on the comment histories that carry trait scores.
- **Tables** (made inside the sealed job). Each author's levels on five readings (the curiosity tag for Competence, Respect's tags, Belonging's three, Meaning's three, and worry) against her five trait scores, 25 correlations with intervals. The PLAY and SEEKING outputs against Neuroticism. Card TP45's first three tables on authors with 80 or more comments.
- **Left out:** comments in the communities where the trait scores were gathered, by the set's own documentation.
- **Registered** (his map): Competence with Openness, Respect with Extraversion, Belonging with Agreeableness, Meaning with Conscientiousness, worry with Neuroticism, and each leads its row and its column. Bar (the analyst's): four or more of the five are above zero and the largest in both their row and their column, and the mean of the five less the mean of the other twenty has its interval above zero. **Registered** (register row S3): PLAY's and SEEKING's readings fall as Neuroticism rises, each interval below zero.
- **Limits.** These authors chose to post a test result. Scores from several tests sit on one scale. Aggregate figures only.

### Phase 2, if room remains

- **TP59.** The pooled word table again, with the ten outputs and with the tag named belonging apart (the handoff's ask).
- **TP44** finishes as registered.
- **TP60** (the analyst's addition, last of all). The display's contract, written from landed results only: for a text, the ten outputs, the tags by need under amendment CH, and the state of card TP50 if it landed; for an author, her need profile with the reliability card TP45's first table gives for her number of posts. No new reading and no bar.

## 5. Order

| When | What |
|---|---|
| First | The jobs still running end as registered. Queue Q20 and Q21. Card TP55 needs only saved outputs and starts at once |
| Then | TP45, and TP46 and TP47 on its reading. TP48's checks, and after them TP49 and TP50, which need the ten outputs. TP51, TP52, TP57 |
| When job Q14's file is read | TP53, or reader C teaches |
| As the queue allows | Q22 and TP56. TP54 |
| When Sounding Line asks for it | TP58's bundle |

**When building is the bottleneck,** drop from the bottom: TP45's first three tables; TP48; TP53; TP46; TP49; TP50; TP56; TP47; TP52; TP51; TP54; TP55; TP57; TP58's bundle; TP45's last three tables; phase 2; job Q24.

## 6. Predictions before data (the analyst's guesses, filed so they can be scored)

| Card | Guess |
|---|---|
| TP45 | The step rises to a k of 10 or 20 and then shrinks as the baseline fills, so on the first-ten rate only the k of 5 is under 0.90, and bar 1, read on the first-one rate, holds. The placebo heads add as much as the tags. Table 1 falls short of its curve by a k of 40 |
| TP46 | Respect's tags lose the most. The body's do not. Her highest need repeats |
| TP47 | Stable for sad and happy. Too few authors for ashamed. The row on anxious cannot say |
| TP48 | Proud is no longer quietest. The separation reaches 0.70 for joyful and not for excited. PRIDE and SHAME move apart, with a correlation near zero |
| TP49 | Seven or more of ten. DISGUST is not the least |
| TP50 | Lands |
| TP51 | Curiosity is above zero both ways |
| TP52 | Above zero. Worry is not among her steadiest |
| TP53 | No reader reaches 0.26 |
| TP54 | Control parts sadness from anger, and fear from anger as much |
| TP55 | The first row lands. The second does not |
| TP56 | Concern follows the drop. Distress does not follow closeness |
| TP57 | The labels hold |
| TP58 | Three of five |

## 7. The return

`docs/exchange/THEORY_RETURN_2026-11-27.md`, pushed at least once a day as it grows, so that a midweek round can read it. For each result: who was measured and how, in a sentence or two a stranger could follow; the verdict word; the estimate, its interval and its bar; its limit; which branch of "what each outcome means" it fell in; and which of section 6's guesses held. The heading "Against, and clear" of amendment CE comes first.

## 8. Limits of this packet

- The pre-flight covers card TP45 in made worlds. It changed that card twice and withdrew a claim made for card TP43. Nothing else here was pre-flighted anew.
- What is saved, the speeds, the counts and the readers' recipes are from the engine's records through a helper's digest, with two spot checks by the analyst, and the checkers' own checks.
- The analyst read the handoff and the curator's turn of 22 November first-hand.
- Job Q14's result was not in the record when this was written, so card TP53 is written for both cases.
- Every result here is about words, labels or a reader's outputs. None is a reading of a channel in a person.
- Picking her out matches a writer's halves inside one file. Nothing is matched to any outside source, and no card tries to name a writer.
