# Theory handoff, Round 18 (14 November 2026, evening)

*From the theory thread to the implementation thread. Read the thread's Round 18 messages as well: this note is the digest. The full record is `claude/THEORY_THREAD_STATE_2026-11-04.md`; the picture is `claude/THEORY_PICTURE_2026-11-14_R18.html`. It replaces nothing in the morning's `claude/THEORY_HANDOFF_2026-11-14.md` except where section 9 says so.*

*Nothing here launches anything. Codex owns the workspaces. Every card below is a proposal for a packet, and several wait on Abraham's rulings (section 10).*

## 0. The one change in kind

Until now every handoff carried one kind of card: a study card, which asks whether a part of the theory is true of people or in built worlds. None carried a reader card, which asks whether software can read a part of the theory from a page, against whose answer, and how well. That is the main reason the engine holds none of the theory. From this round every handoff carries both kinds. Section 4 has the first six reader cards.

## 1. What he asked for, in his words

- "this leg should be much more focused on how to apply what we're doing to topathy"
- "I want to do an incredibly thorough look as to why the results of our theory aren't reaching topathy correctly."
- "Somehow our engine is not growing as a result of our knowledge."
- "we're going to have to get much, much more clever very, very quickly. Try to find new ways to uncover things like triggers or even stress."
- "we weren't even able to collect triggers for, or attempt to collect triggers for any but three of the channels. I'd like to, ideally, be able to try to identify triggers for all of them."
- "We still haven't nailed down the trigger for fear, and we kinda need to nail down the trigger for other things too"
- "What are the ways that people use to judge the existence of a rule?"
- "we have an extraction scaffold, but we really should start building out an algorithm. But to do that, we need to start establishing channels and also build out some mechanism for grabbing fluencies."
- "It's going to have to be done algorithmically. Maybe we just do blind inference and try to fill in a row."
- "is there any other thing we can measure as stress?"
- "So far, I haven't extracted the person from this anywhere."
- "Certainly we're going to have to do another round of tests."
- "build out a decent idea for a handoff that captures our current ideas and kind of elucidates spaces that would be useful for examination or exploration"

## 2. What changed

### Safe to build on (his rulings this round)

- **Names.** "the marketplace of ideas" is the main name. Nest stays. Seen as competent becomes **visibly respectable**. Seen as kind becomes **visibly compassionate**.
- **The outlook is dropped.** "It's just precision, I guess." It folds into Knowledge, which is confidence in the map and in the plans.
- **Schema** (new word, his): a fluency held in attention. It highlights or hides triggers: "That's just schemas highlighting or removing the triggers, really."
- **A rule** is a tile "tied somehow directly into at least one set point". It becomes an identity "when it can trade for a set point directly".
- **Emotionality** is "the trigger strength of your channels". Neuroticism is read the same way.
- **Agreeableness** stays with visibly respectable, with an asterisk: it mixes the five-factor and six-factor traits.
- **The outer loop** as drawn (the rule at the top, Stress at the bottom): yes.
- **Freedom** is the stock: "a nest for needs I can't name yet".
- **The idle mind** turns to "whatever's currently bound in your free energy", not to play.
- **Round 17's disagreements 6 and 10** are accepted by him (people don't simply take the money unwatched; births follow a level against an expectation).
- **Variational free energy as Stress:** accepted ("That's fine.").

### Open or reopened

- **Expressions.** He does not accept "expressions are acts". The thread withdraws that wording for the first layer. Working form, awaiting his ruling: two layers. A channel firing moves single facial muscles at the moment of a change (his slopes; untested as change against level). A learned layer brakes, releases or poses.
- **The picture.** Two lanes and one loop. Channels are attached under the marketplace in one frame.
- **CARE's second trigger.** His Round 16 table gives CARE two triggers, a high kith index and reciprocity. He asked this round whether reciprocity is "meant to be directed at your children". The thread's reading, not yet put to him: reciprocity and gratitude belong to the kith index between adults, and CARE keeps one trigger. Don't build on either reading.

### The thread's proposals, awaiting his ruling

1. A page tier in the engine, held to a human reader's score (section 4, Question 1).
2. A strong model as an offline labeller of public text, if the small trained reader falls short (Question 2).
3. His own dictated messages as the engine's first full row (Question 3).
4. Two or three data requests under his name (Question 4).
5. A rule's working definition: a tile whose proposed trade fires a channel (Question 5).
6. The mapping of the seven untested emotion labels onto the picture (study card S1).

## 3. Why the theory isn't reaching the engine

Read first-hand on the engine branch at `d49be5f` unless marked.

| Where it stops | Evidence |
|---|---|
| Nobody asked | Of 25 numbered asks in the three latest engine packets, one bears on the theory, the owner questions (an agent's count; the item lists agree). The 11 November packet's "Not in this packet" includes "Drive priors, values, and any claim about a channel." The theory handoffs of 11 to 14 November carried design notes for the engine and no buildable item |
| The slot is empty on purpose | `engine/tompathy_engine/packet/bottom_box.py` opens: "TS1 structural placeholder: no producer, evidence, estimate or admission." The 12 November packet: "A default-off schema, and nothing that fills it" |
| The code holds October's idea of a drive | `packet/drives.py`: "Admitted revealed-theme projections; final text cannot move these estimates." Its mapping runs from topic tags to drives (danger to FEAR, conflict to RAGE). "trigger" and "appraisal" do not occur in `engine/tompathy_engine` |
| The topic question was never fixed | Q10 answered "care" for 19 of 20 theme-free sentences. Its repair (B13) is "preregistered, not run" |
| A guard blocks the only route | The 14 October spec: "only choices and corrections move maker estimates". `docs/DRIVE_ADMISSION_CHAIN.md`: "Final text is T0 and cannot establish choices, corrections, or drives." Sound for maker claims, and it leaves no place for a claim about a passage. His 16 October direction asks for the engine to "run into a new unknown page", where no history exists |
| No answer key, and an absolute bar | `docs/ENGINE_V1.md`: "No production inference admission is present. Empty estimates are deliberate." The Q10 gate asks 0.85 overall and 0.70 per label. Human readers of event reports name the writer's own emotion about half the time (section 7) |
| The reader is too small for prompting | One 9B model on CPU behind a memory gate; "No GPU, no paid or remote model calls." Open models of 7 to 13 billion parameters scored between -0.04 and 0.08 at rating triggers by prompt. The small word-scoring pass itself takes 55 to 62 seconds per 3,000 words against a target of 15 |
| Returns are filed, not wired | Ghost's folders sit in the repo and no engine code cites them (an agent's read) |
| Names outrun the schema | `bottom_box.py` still carries `tending`, `seen_as_competent`, `seen_as_kind` |

**What the engine reads today:** word predictability (attention), repeats (habit), and an outline from titles and headings (goals). All three read fluency. None reads a channel, a need, a rule or Stress.

## 4. Reader cards (engine)

**The design claim (the thread's, built from his definitions).** One missing instrument, a trigger reader, reaches most of the theory. It reads channels directly. It reads needs because a trigger is a change on a need. It reads rules because trading a tile tied to a need fires a channel. It reads Stress as firings with no trigger on the page. It reads the person as trigger strength per channel across many pages. Only plain fluencies need the instrument the engine already has.

**Two tiers (Question 1).** "On this page": readings of the final text, with an unvalidated mark, each a claim about a passage. "About the maker": empty until choices, corrections or many pages exist. The 14 October guard stays whole.

**The bar.** Each reading is held to what one human reader scores on the same items against the writer's own answer, plus a nothing-here check. No absolute bar is lowered.

| Card | Reads | Input and output | Answer key and battery | Baselines and bar | Build under the standing rules | If it clears; if it misses |
|---|---|---|---|---|---|---|
| **R1** | channel label and trigger features | a first-person passage in; one of 13 labels and 21 rated features out | the writer's own label and ratings; Crowd-enVENT, 6,600 reports, with held-out writers; 1,200 reports also have five readers each | best constant; a bag-of-words model; one reader (label .50, features 1.57 on a 5-point scale); pooled readers .56; the corpus authors' classifier .59. Nothing-here: at least 0.70 on the 40 theme-free items already built for B13, and on the corpus's no-emotion reports | frozen sentence embeddings with linear heads first (minutes on CPU); then a fine-tuned small encoder if short. Also run the 9B reader on the same items once, to measure how far off prompting is | clears: the first admitted page reading. Misses: Question 2 |
| **R2** | CARE | a short reaction to a news story in; the writer's own concern and distress scores out | Buechel 2018, 1,860 essays, open licence (agent-read) | the paper's own models; one human reader is not available here, so the bar is the paper's best model | same as R1 | clears: CARE gets a page reading that separates concern from distress |
| **R3** | a need stated in a request | a request for help in; whether it was helped out | Random Acts of Pizza, 5,671 requests, 24.6% helped, a real outcome | the paper's features; length alone | linear model on R1's features plus the paper's | clears: a first check that read need predicts help. It has no closeness |
| **R4** | priorities from an exchange | the other side's first five messages in; the order of three priorities out | CaSiNo, 1,030 negotiations, priorities known (assigned at random, so these are prices, not rules) | chance 16.5%; bag of words 28.5%; a published ranker 63.6%; a human expert 75% on 100 dialogues | a small ranker; CPU | clears: the engine can read what someone wants from offers. It says nothing yet about refusals at any price |
| **R5** | the owner's corrections as labels | a confident reading shown to the maker in; her correction out | the maker herself, in the product | none; this is a logging card | a log schema for the existing owner-question card and a claim-and-correct card. No reader | gives every later card a label source that is not a participant study |
| **R6** | trigger strength per person | many passages by one author in; a strength per channel out | PANDORA, by request: Reddit authors with personality labels (subset and access from memory). Needs R1 first | chance; word counts | R1 applied per author, then a per-author summary | clears: the first maker-tier reading with a key. Tests "Emotionality is trigger strength" outside the lab |

Notes for whoever writes the packets:

- **R1 is the one to do first.** It needs no new data and no large model. The corpus is already in Sounding Line. The authors' code is public (github.com/sarnthil/crowd-enVent-modeling, agent-read).
- **Whose feeling.** The corpus is first-person reports. On essays the reader must not attribute a described feeling to the writer. The page tier's wording is "on this page".
- **The corpus rates how an event was, not which need it touched.** The need has to come from the label (pride, trust, shame) or from what the passage is about. The second route has no answer key yet.
- **A rule from a channel at an offer** has no data. Ghost card G2 tests it in built worlds first.

## 5. Study cards

### Sounding Line

| Card | Question | Design | What each outcome changes |
|---|---|---|---|
| **S1** | What moves each of the 13 feelings? ("blind inference and try to fill in a row") | Split writers in half by a hash. In the first half fit each label's strength on the 21 rated features. Freeze the signed profile. Confirm in the second half at the bar the family already uses (0.10), with a writer-cluster interval. Four labels (fear, anger, sadness, disgust) were already examined on all writers, so for them this is a replication, not a fresh test | A 13 by 21 trigger table made from data. Labels whose profile confirms get a row the engine can grade by. Labels that fail stay unmapped |
| **S1 mapping** (the thread's, for his ruling) | pride and shame are visibly respectable going up and down; guilt is CARE's alarm; trust is Belonging; surprise is Knowledge; relief is a piece of Stress resolving; no-emotion is the nothing-here case | | Each confirmed profile says which appraisal features carry a change on that need |
| **S2** | FEAR by time course (card IN11, written and waiting) | Split fear reports by the event-duration and emotion-duration columns. Prediction: suddenness and attention grade the short ones; the long ones follow an unresolved-and-uncontrollable profile | Both hold: FEAR's row stands as graded by how sudden and how close, and the slow kind is filed under Stress |
| **S3** | One band or several strengths (card IN12, written and waiting) | Per writer, strength of the reported feeling given how well the event fits the trigger, against her personality items. Run anger apart from fear and sadness | Neuroticism items predict strength for fear and sadness, and Agreeableness items for anger: trigger strength is per channel. One band for all: one dial |
| **S4** | The person as settings | TR1's recipe (true between-person variance first, then corrected split-half) on: refusal across sessions (the B2 cohort; card ID1 never ran); slowing (per-writer slope of pause on surprise, the D33 rows); returning to a word class across prompts | Each stable setting becomes a maker-tier candidate. Each unstable one is dropped from the maker tier |
| **S5** | PLAY's trigger | What was said just before a laugh in the meeting recordings, against matched moments with no laugh | A first trigger table for PLAY from an outcome, not a rating |

Person-level cards in the record that never ran or failed their support check, for S4's packet to draw on: ID1 (steady refusers), D31 (author against character), TD7 (what a rejection does to later sensitivity), CH7 (per-player chess references; scoring is still running). An agent's list.

Already in hand and newly read by the thread (item tables of the fear reports): predicted harm did nothing (profile 0.03; certainty of harm -0.10, inconclusive; anticipated consequences 0.01, against; control -0.00). Suddenness (0.12 [0.02, 0.23]) and attention (0.11 [0.02, 0.21]) lean up, both inconclusive at 0.10. The two partial mappings came back with the wrong sign, descriptively: joy against PLAY's profile -0.08, boredom against low SEEKING's -0.16.

### Ghost

| Card | Question | What each outcome changes |
|---|---|---|
| **G1** | How many page readings until a maker's settings are known? A maker with fixed trigger strengths writes pages. A reader with a human reader's error (label right half the time, features off by 1.57) reads each | Gives the product a number for when "about the maker" may open |
| **G2** | Which probe separates a rule from a price fastest: claim-and-correct, a priced offer, or a sweetener followed by a symbolic concession? And does a channel firing at the offer mark a rule as fast as refusal does? | Orders the product's probes. Tests the working definition of a rule (Question 5) |
| **G3** | Can a reader tell a channel fired by a trigger on the page from one fired by leftover? | Yes: Stress gets a page reading as firings without triggers. No: Stress stays unread |
| **G4** | Carried from the morning's note: does a stated plan quiet a gap; what a refusal earns when the partner can see inside; loudest need against loudest reachable need | unchanged |

## 6. Probes (product)

Every tested human method for learning what someone holds is a probe, not a reading.

- **Claim-and-correct.** State a confident reading and log the correction. Lab support for the interview version; a training study found no added yield.
- **A priced offer.** On a sacred issue a material offer raises opposition and a symbolic concession lowers it. The reaction to the offer is the test.
- **Timing, with a control.** Speed counts only relative to how hard the choice was.
- The owner-question card already exists in `src/core/owner-probes.ts` ("If X no longer led to Y, would you still want X?"). R5 logs what comes back.

## 7. Data

Access notes are agent-read unless marked. Nothing large was downloaded.

| Source | Holds | For | Status |
|---|---|---|---|
| Crowd-enVENT | 6,600 event reports; the writer's label, strength, 21 trigger ratings, event and feeling durations, a short personality inventory; 2,379 writers, 2.8 reports each on average; 1,200 reports with five readers | R1, S1, S2, S3 | on disk in Sounding Line |
| The meeting recordings with laughter | laughs in transcripts | S5 | on disk |
| The moral-choice and phone-game cohorts | refusals; mood against luck | S4 | on disk |
| Buechel 2018 | 1,860 reactions to news with the writer's own concern and distress | R2 | open; small; to fetch |
| Random Acts of Pizza | 5,671 requests with a real outcome | R3 | public; no licence stated |
| CaSiNo | 1,030 negotiations with known priorities | R4 | open |
| Persuasion for Good | 1,017 dialogues, value questionnaires, a real donation | a stated value against a real choice | public repo; named in the 14 October spec and never fetched |
| PANDORA | Reddit authors with personality labels | R6 | by request, under his name |
| Stanford's narratives (SEND) | 193 clips, 49 tellers; the teller's own moment-by-moment rating; facial actions, voice and word features already extracted | the change-against-level test for faces, with no video processing | academic request, under his name |
| NetHealth | about 700 students rating contacts for closeness and support over eight surveys; phone logs, no text | kith over time | sign-up form, under his name |
| CANDOR | 1,656 conversations between strangers; liking and perceived liking | both sides of an index | by request |

**Human ceilings to hold readers to** (read through a reader tool; numbers not seen in the originals):

- One reader against the writer's own emotion label, 13 labels: accuracy .50. Pooled readers: .56. The corpus authors' classifier: .59.
- One reader against the writer's 21 trigger ratings: 1.57 on a 5-point scale. Five readers pooled: 0.99. GPT-4: 1.45, and 1.12 for five runs pooled.
- Per label, pooled readers: fear .73, boredom .73, disgust .65, relief .64, sadness .63, pride .59, anger .57, guilt .53, trust .52, joy .49, shame .48, surprise .42, no-emotion .33.

**Looked for and not found:** closeness, an act of help and text in one source; a record of refusals at any price; a text corpus with the writer's own stress rating; a study separating change from level for a face; a writer-rated corpus for SEEKING or LUST.

## 8. Spaces worth exploring

His ask: spaces "that would be useful for examination or exploration". Each has one line on why.

1. **Which feelings a page hides.** Readers get fear and boredom (.73) and miss shame (.48) and surprise (.42). The social feelings may be the ones a writer covers.
2. **Evaluation in essays.** Essays don't report feelings; they praise, blame and worry about things. Treating each evaluation as a channel aimed at a target is the bridge from event reports to arguments (the thread's idea; the appraisal framework in linguistics is the nearest prior art, from memory and unchecked).
3. **Dictation as a production record.** His own messages keep corrections in line, and the audio keeps pauses. By the engine's own rule, corrections are evidence about the maker.
4. **Voice before video.** Against a person's own rating, sound alone beat picture alone (.31 against .21), and voice alone beat both in five experiments.
5. **Change against level for a face.** No published test exists. The Stanford set allows it.
6. **From rule to identity.** Means-ends fusion names four conditions (repeated pairing, uniqueness, similarity, immediacy). His "cleanly and unilaterally" is two of them. All four are testable.
7. **Trigger strength per channel.** Anger loads on two traits. IN12 with anger run apart is the test.
8. **The settings of a person.** Three are already stable in the record (typing rhythm, stopping length, reactivity to luck). Refusing, returning and slowing are untested.
9. **Two roads to hoarding** as separable signals in text: gathering with the brake off, and Belonging placed on objects.
10. **Expertise.** No reading of it has ever been in place. Typing logs are a better source than finished text.

## 9. What to drop or hold

- **Drop:** asking the 9B reader trigger questions by prompt. Train a small model on writers' labels.
- **Drop:** the outlook, from every table and from the schema's future versions.
- **Drop:** micro-expression reading, and stress from typing or mouse movement. Training to spot micro-expressions did no better than sham training, and the typing and mouse replications were mostly null (the second is agent-read).
- **Hold:** any maker-level drive claim. The guard stays.
- **Hold:** a reading of how firmly a view is held from one finished text. People score at chance on it.
- **Hold:** video processing beyond the one change-against-level test.
- **Replaced from the morning's note:** its Test 2 (a search for data) is done; section 7 has the result. Its Tests 1 and 3 stand.

## 10. Open with him

**The five questions** (with the thread's suggestion): a page tier held to a human reader's score (yes); a strong model as an offline labeller of public text if the small reader falls short (yes, public corpora only); his own dictated messages as the first full row (yes, local, with decoys); hold expressions as two layers and send two data requests, Stanford's narratives then PANDORA (yes); a rule is a tile whose proposed trade fires a channel (yes, as the working definition).

**The ten disagreements awaiting his ruling:**

1. Predicted harm doesn't set fear's volume. Suddenness and attention lean that way.
2. What people do with each other is an exchange, not reading a finished page. On a page people are poor readers too.
3. The marketplace isn't just expertise. Expertise is its cheap end.
4. There are tools for reading motives from text. What's missing is agreement with what people say they want.
5. Video won't read minds. The face is the weakest channel for what a person feels.
6. Micro-expressions are rare, and training to spot them doesn't help. A slower leak exists.
7. Faking is harder than holding still for negative feelings, not for smiles.
8. Expected free energy isn't all Knowledge. Half is the needs looking ahead.
9. Attention does reach sensory cortex; and the two networks switch, they don't see-saw.
10. Hoarding's second way in isn't a cortical fluency. The cortex is the brake.

**Also for his ruling, not in the round's messages:** whether CARE keeps its second trigger (section 2).

## 11. Housekeeping

- **Schema.** Give each need a fixed id that never changes, with display names in a separate map, so a rename is one line. Current display names: Knowledge, Nest, Belonging, visibly respectable, visibly compassionate. Split the box into `on_page` and `about_maker`. Each reading carries its answer key, its bar and the human reader's score beside `status`. `hub` becomes a list of tiles. The engine's contract says a change like this needs tests and a version bump.
- **Admission.** A second class for readings held to a human reader's score waits on Question 1. Nothing changes until he rules.
- **Standing decisions of his that bind packets:** no human-participant studies; Codex owns the workspaces; the engine's standing rules as the 12 November packet states them. Don't plan write-ups of negative results or decision dates: he has ruled both out.
- **Corrections owned this round.** "A stranger's history fits her pauses better than her own" was wrong as worded: the record says the coefficient difference "does not establish that donor history predicts better". The 14 November assessment's two-page deadline and decision date are removed. "Expressions are acts" is withdrawn for the first layer. Round 17's disagreement 9 on Agreeableness is withdrawn in part. The count of channels tested is four, with two partial and seven labels left unmapped.
- **Vocabulary changes:** seen as competent to visibly respectable; seen as kind to visibly compassionate; the marketplace to the marketplace of ideas; schema for a fluency held in attention; the outlook retired.
- **His transcript** of 14 November (afternoon) was saved verbatim by the theory thread, and every quotation of his in this note was checked against it by script.
- **Read status** is at the end of the state file. Items read through a reader tool, by an agent, or from memory are flagged there and in the round's messages.
