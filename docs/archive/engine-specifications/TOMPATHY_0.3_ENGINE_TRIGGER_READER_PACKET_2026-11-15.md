# ToMpathy 0.3 engine packet: the trigger reader, wired through

15 November 2026, late evening. For the agent on branch `codex/0.3-engine`. Sized for the week of 16 to 22 November. It continues `TOMPATHY_0.3_ENGINE_READERS_PACKET_2026-11-14.md`: every card there keeps its identifier and its record, and section 8 says what happens to each. File this packet at the repository root beside that one. Pre-flight bundle: `PREFLIGHT_2026-11-15.zip`, folder `engine/` (unpack to `.local/preflight-2026-11-15/`).

This is a spec sheet. It carries no questions for the owner. Where a choice had to be made it is made here and listed in section 10.

The only theory file this packet needs is `claude/THEORY_HANDOFF_2026-11-15_R24_OFFICIAL.md` (Round 24). Everything quoted from the owner below is from that file or from his turns behind it, and every term a card uses is defined in the card.

## 0. Read first

**Sources.** The branch at `8e07ac1` (15 November, 16:17; unchanged at a re-fetch before sending): `docs/ENGINE_READERS_2026-11-17.md` in full, `packs/registry.py`, `packs/run.py`, `packs/README.md`, `packet/build.py`, `packet/bottom_box.py`, `src/core/bottom-box.ts`, `src/core/need-view.ts`, `src/core/reader-names.json`, the head of `src/components/NeedLandscape.tsx`. The Round 24 handoff and the owner's seven turns of 15 November behind it, read in full. Sounding Line at `f2471dcc7` and Ghost at `efc21f376`. Two public sources fetched and read by the analyst for the pre-flight: Crowd-enVENT (as on 14 November) and Story Commonsense (section 3).

**One correction to the handoff.** Its section 3 says the branch had no commit since `d49be5f`, and its section 5 tells this agent to "Start the readers packet of 14 November". The branch moved at 16:17 on 15 November and most of that packet has run. This packet builds on the results.

**The owner's words that set this week** (15 November):

- "tompathy is nowhere near correct... I thought we'd have more on the back end than that by now."
- "we need a trigger reader. That's the piece that we need to connect everything."
- "We need to build the actual slow version first before we start speeding it up."
- "it feels like it's much more buildable than it was."
- The top-right window should show the schema: "what is the person actively thinking about".

**Standing rules, unchanged.** The 14 October guard: only choices and corrections move maker estimates, and final text establishes neither. `about_maker` stays closed. No pack loads by default. Nothing paid, nothing remote, no GPU, no local language model reading this week (the owner lifted that for the Spark only, from next week). No demographic column is read. A result's sentence about what it does not establish travels with its number. New rows have no ledger row.

**Names.** The Toolbox (not the marketplace of ideas). Capital (not the stock; it is not a need). A fluency's four kinds are habit, heuristic, value, identity ("The word is identity, not rule"). Needs: Knowledge, Nest, Belonging, visibly respectable, visibly compassionate, the body.

## 1. What the readers record says (the analyst's reading)

| Card | Result on the branch | What it means for this week |
|---|---|---|
| TP10, the label reader | fine-tuned MiniLM 0.476 macro-F1 on 13 labels, against one human reader at 0.492 and a bag of words at 0.389. Missed its bar of 0.49 by 0.014 | label accuracy is at the level of one person. It is not the wall |
| TP10, nothing here | silent on 14 of 40 theme-free items and on 20.4% of verified revision sentences; no-emotion recall 0.43 | this is the wall. The reader was trained on a corpus that is 92% feeling and has no idea what plain prose looks like |
| TP12, corrected counting | clears on bags without neutral (error 0.038, top label right 0.848). With 80% neutral it does not beat raw counts (0.112 against 0.109) | counting cannot repair a reader that fires on everything. A gate has to come first (TP25) |
| TP11, twins | MiniLM tells all five near-twin pairs apart from the words (0.70 to 0.92). The stake columns failed, and the record says: "There is no independent stake answer key and no admitted need pack." | the engine has no reader of which need an event touched, and no key to train one on. Section 3 supplies a key |
| TP13, transfer | Crowd-enVENT to GoEmotions 0.232 against 0.776 in domain | a reader of event reports does not travel to comments. Every reader below is tested off its home corpus |
| TP16, worry | fine-tuned MiniLM R² 0.301, r 0.554, against the writer's own worry rating. The only reader that cleared its main and stretch bars | the first reading that can go through the wire end to end (TP26) |
| TP18, where she stops | gain 0.021 [0.010, 0.031] against a bar of 0.02 on the lower end: the estimate clears and its lower end does not. A hidden-state probe on the same data went the wrong way (-0.022) | open; the pause remainder is tried as a new row (TP27) |
| TP19, choices | reader features did not predict which suggestion she took | parked; no follow-on this week |

And three links are missing between a reader and the screen (the analyst's count):

1. No pack exists, and the pack runtime handles one kind of head (a choice among labels).
2. `packet/build.py` attaches `empty_bottom_box()` and never calls `packs.run`.
3. `src/core/need-view.ts` builds the panel from goal roots and drive hypotheses and never reads `bottom_box.on_page`.

So nothing a reader finds can reach the Core values panel today, whatever its score. This week closes the three links with whatever readers clear, slow first, and builds the reader the owner asked for.

## 2. TS3. The wire, end to end

"See whether we can set it up at all" is this section. It is built and tested on a constructed pack first, so it does not wait for any benchmark.

### 2.1 `reader-pack-2`

Extend `packs/registry.py`. `reader-pack-1` packs stay valid.

| `task` | Head | What it emits |
|---|---|---|
| `channel` | softmax over labels with a neutral label; error table; aggregation receipt | as today |
| `tags` | one sigmoid head per tag, a fixed threshold per tag set on validation rows | events with `label` set to the tag; `share` is null (TS2 allows no raw share, and no error table exists for tags) |
| `scalar` | one linear head; `range` and `unit` of the key's own scale | `series`: one value per window, mapped onto 0 to 1 by the key's range |
| `gate` | one sigmoid head, one threshold | nothing on its own. A sentence the gate rejects is not read by any other pack |
| `trigger` | a composite. Its own directory holds per-sentence heads that write scores, not events (nineteen need-tag heads; the eight-feature head) and one pinned rule file (4.3). It names a gate pack, and optionally a label pack, by pin (4.4) | one event per sentence the gate passes, with its `stake` filled; `share` is null |

Rules: one manifest per pack; `aggregation` is required only for a `channel` pack with `status: benchmarked`. A `channel` pack with `status: research` may omit it, and then every reading it writes has `share: null`: sentence events do not need a counting receipt, shares do; `tag_map` and `label_map` map to `N1` to `N6`, `C1` to `C9` or `S1` from `reader-names.json`; a tag with no home in the list stays unmapped and is emitted only as an event label. `status` gains a second value, `research`: a pack whose key is research-only or whose primary bar was cleared only on its home corpus. Release packaging refuses `research` exactly as it refuses `research_only`.

### 2.2 `packs/run.py`

- Take a list of pack directories. Encode each sentence once per distinct encoder pin and reuse the vectors across packs.
- Order: gate, then tags, channel and trigger, then scalar over windows. A window is as many consecutive sentences as fit the pack's token cap (TP16's head saw the first 128 tokens of a text), stepping by half a window; a text under the cap is one window.
- With no gate pack present, nothing but a `scalar` pack may run. This is the lesson of TP10 and TP12 turned into a rule.
- Speed is recorded and not tuned: "We need to build the actual slow version first before we start speeding it up." Report seconds per 150 sentences beside TP10's 2.974.

### 2.3 `packet/build.py`

- New arguments `packs` (a sequence of directories, default empty) and `research` (default false). With `bottom_box=True` and no packs the packet is byte-identical to today's.
- Sentences come from the same splitter the readers benchmarks used. Add a parity test against `src/core/sentences.ts` on the fixture page of 2.6: same count, same UTF-16 spans. Where they differ the engine's spans stand and the front end maps by overlap.
- The packet id digests the pack pins. A pack with `status: research` is attached only when `research` is true, and the packet then carries `provider.method` text saying research readers are present.

### 2.4 `bottom-box-2`

- `marketplace` becomes `toolbox` (the owner's ruling on the name). `bottom-box-2` is written only when at least one pack is attached. With no pack the empty box stays exactly as it is today (`bottom-box-1`), so 2.3's and 2.6's byte-for-byte promises hold. The front end reads both, and its upgrade function maps a `bottom-box-1` box to `bottom-box-2` by renaming the key.
- `status` is `benchmarked` or `research`.
- An event may carry `channel_by_table`: the channel the trigger table names for its stake (TP24), with the table's version. It is absent unless TP24's pack wrote it.
- Nothing else changes. `about_maker` stays an empty list by schema.

### 2.5 The front end's first real input (`src/core/need-view.ts`)

The owner called the panel "just a skeleton for now" and will direct its design himself. This card adds plumbing and one flagged path, and changes no visual design.

- `pageNeedSources(packet): NeedSource[]`, a pure function. For each `on_page` reading with a channel id: one source of type `channel`, labelled from `reader-names.json`, `confidence` the mean event confidence, `regions` the ids of the artifact regions whose character range overlaps an event span (empty, and said so in the record, if the packet's regions carry no ranges), and `needs` the distinct pairs of need and direction among its events' stakes, each with `illustration: false`. `NeedSource` knows two directions: a stake of `up` or `restored` maps to 1; `down`, `threatened` or `unfed` to -1; `either` stays in the event and is left out of `needs`. A reading with no stakes yields a source with an empty `needs` list.
- `pageNeedActivity(packet)`: for each of `N1` to `N6`, the event spans of the reading with that id and their tags. The need diagrams keep their notional bands. A need touched on the page gets a count and its spans, nothing more: a reading says a sentence touches a need, and says nothing about the need's level.
- `S1`: when a `scalar` reading is present, expose its series for the Stress detail. The detail's caption stops saying the lines "do not calculate a person's stress from a text" only in the research view, and says instead what the reader is: trained on writers' own worry ratings in one corpus, its score there, and that it is not a measure of this writer.
- `workNeedSources` appends `pageNeedSources(packet)` when the packet carries research readings and the app's research flag is on. The synthetic example keeps its illustration tables.
- A zod test: a `bottom-box-2` fixture parses, and `pageNeedSources` returns the expected sources (snapshot).

### 2.6 Acceptance

1. **Constructed.** A three-sentence page, a constructed encoder, and four constructed packs (gate, tags, channel, scalar) with hand-set weights. Expected `on_page` JSON written by hand before the run. `build` then `pageNeedSources` reproduce it. A second page of three plain sentences yields an empty `on_page`.
2. **Real, research view.** The packs that exist by Thursday (section 9's order) run on B13's 160 themed items and 40 theme-free items and on three CoAuthor essays from the public corpus that TP19's adapter already loads. Deliverable: the packet JSON for each, and a screenshot of the panel in the research view for one essay.
3. **Default off.** With the research flag off, the three essays' packets are byte-identical to today's.

## 3. TP23. A reader of which need an event touches

**Why.** The owner: "A trigger is a change on a need", and an appraisal carries, per need, which way it moved, by whose doing and, provisionally, whether it has happened or is still to come. The engine reads labels and 21 rated features. It has never had a reader for the first slot, which need, because it had no answer key.

**The key.** Story Commonsense ([Rashkin and others 2018](https://aclanthology.org/P18-1213/); archive at `https://uwnlp.github.io/storycommonsense/data/storycommonsense_data.zip`, SHA-256 `989a8294fee4b825b2761ab0a201a0e316b74a297efe2be467b1ee7490907f72` as fetched on 15 November). About 15,000 five-sentence stories. In the development and test splits (4,853 stories), three annotators marked, for each character in each line, the motive behind what the character did, in Maslow's five categories and Reiss's nineteen, and separately the feeling in Plutchik's eight. The archive's readme states no licence, and the stories come from ROCStories. Treat it as research-only: every pack trained on it is `research_only: true` and `status: research`.

**What a label is.** A line gets a tag when at least two of its annotators chose it (the authors' own rule). 48,065 character-lines; 12,271 carry at least one tag. Positives per tag run from 1,473 (contact) down to 39 (belonging).

**The map to the theory's needs (the analyst's, proposed, for the owner to overrule).**

| Need | Reiss tags |
|---|---|
| Knowledge (`N1`) | curiosity |
| Nest (`N2`) | order, savings, tranquility (the archive's word for safety), serenity |
| Belonging (`N3`) | belonging, family, contact |
| visibly respectable (`N4`) | status, approval, power, competition, honor |
| visibly compassionate (`N5`) | idealism |
| the body (`N6`) | food, rest, health |
| no home in the list | romance (it is LUST's opening, a channel and not a need); independence (nearest to Capital, which is not a need) |

The reader is trained on the nineteen tags and the map is applied afterwards, so a ruling that moves a tag costs nothing.

**The analyst's pre-flight** (`engine/pf_need.py`; one pass, a bag of words, default settings; not a result).

- In the stories, held out by story, the nineteen heads average an area under the curve of 0.723 (romance 0.866, food 0.859, family 0.815; idealism 0.612, honor 0.613).
- Applied cold to the 6,600 Crowd-enVENT reports, which it never saw, the mean tag profile of each label is what the theory would write. Pride: status, competition, approval. FEAR: tranquility. DISGUST: food. Trust: contact. Sadness: family. Relief: savings, rest, health. Shame: idealism, approval, status. Anger: power, order.
- Does the need slot add to the writer's own 21 ratings? Telling the near-twins apart, writers held out:

| Pair | 21 ratings | ratings and need tags | gain | need tags alone | the words (for scale) |
|---|---|---|---|---|---|
| pride and joy | 0.613 | 0.708 | +0.095 | 0.701 | 0.757 |
| guilt and shame | 0.627 | 0.632 | +0.005 | 0.586 | 0.700 |
| fear and sadness | 0.728 | 0.785 | +0.057 | 0.722 | 0.863 |
| anger and disgust | 0.749 | 0.785 | +0.036 | 0.699 | 0.787 |
| trust and joy | 0.798 | 0.838 | +0.040 | 0.750 | 0.891 |

- On all 13 labels: macro-F1 0.375 from the ratings, 0.421 with the need tags.
- Predictions written before the run (`need_predictions_written_before_numbers.json`): a gain of 0.03 or more on at least three pairs (it was four), and 32 of 39 predicted signs right. One prediction was wrong: the analyst expected fear and sadness to gain least, because the theory's table separates them by when. Guilt and shame gained least. Which need was touched does not tell those two apart.

**Do.**

1. Reproduce the pre-flight from the bundle (bag of words). Expected: the table above within 0.02.
2. The ladder, on the same split by story: the bag of words; frozen MiniLM with nineteen logistic heads; fine-tuned MiniLM, three seeds. A fourth rung, a base-size encoder, only if memory allows; it is the slow version and nobody will mind its speed.
3. A people row: for each tag, the F1 of one annotator against the majority of the other two, averaged over lines. Report the reader's F1 at its thresholds beside it.
4. The transfer test, which is the one that matters: the table above, with each rung's tags in place of the bag of words.
5. Write `rp-need-1`, a `tags` pack, from the best rung that clears.

**Bars.** In the stories: mean area of 0.76 for frozen MiniLM. Off them: a mean gain over the five pairs of 0.06 (the bag of words gives 0.047), and 0.03 or more on four pairs. A reader that clears the first and not the second is not packed.

**Not shown, whatever the score.** The tag for visibly compassionate rests on 208 lines of one category and the lowest area on the list. Its events are computed and kept out of the panel until a better key exists. Guilt and shame are reported as not separated by need.

**Export IM2 to Sounding Line** (replaces IM1). A table of `text_id` and nineteen tag scores for all 6,600 reports, from the packed reader, written to `.local/exchange/IM2/` with a manifest of SHA-256 hashes and the reader's pins. Sounding Line's owner copies it and checks the hashes on arrival, the way EX5 travelled in the other direction. Sounding Line's packet of this date runs it under its own controls as IN13 Part D, with a bar of 0.03 on the mean gain: that bar asks whether the need slot adds anything. The bar here is higher (under Bars, above) because it asks whether an encoder is worth packing over the bag of words. TP14's motive models (52 seconds per 150 texts) are retired from the queue; the 8,873 scores already saved are kept as a second coder.

**What each outcome changes.** Both bars clear: the engine has its first slot of the trigger, and the panel's need diagrams have real input. The story bar clears and transfer fails with MiniLM where the bag of words passed: the encoder is reading story style, and the bag of words is packed in its place. Neither clears: the key does not carry, and the need slot waits for labels made on the Spark (section 11).

## 4. TP24. The trigger reader: slots, then the table

**Why.** "we need a trigger reader. That's the piece that we need to connect everything." The label reader names a feeling. A trigger reader says why: which need moved, which way, by whose doing, already or still ahead. Then the theory's table names the channel. A reading that carries its reason can be shown, checked by the owner against the sentence, and corrected, which is the only thing that moves a maker estimate.

**The slots, and what can be read today.**

| Slot | Source | Read from text? (five readers against the writer, Crowd-enVENT, 14 November pre-flight) |
|---|---|---|
| which need | TP23's tags | section 3 |
| which way | pleasantness, unpleasantness, goal support | 0.82, 0.78, 0.64 |
| by whose doing | own responsibility, another's responsibility | 0.71, 0.63 (chance: 0.48) |
| how it lands on standing | others' standards broken, own standards broken | 0.64, 0.61 |
| sudden | suddenness | 0.58 |
| what can be done | own, others', chance control | 0.51, 0.52, 0.45: weak |
| already or ahead | nobody rated it | no key; see 4.3 |

TP10 already trained a head for the eight readable features (pooled error 1.309, under the floors). TP24 uses that head as it is.

### 4.1 Does the reason carry the label?

Crowd-enVENT, writers held out, text only (no rating of the writer's enters as an input).

- **Slots only.** A logistic model on the eight predicted features and the nineteen predicted tags: 27 numbers per report.
- **Direct.** TP10's frozen MiniLM reader (0.4252 on 13 labels).
- **Both.**
- Report 13-label macro-F1, the five twin areas, and, on the five labels that are channels of loss in the table (anger for RAGE, fear for FEAR, sadness for PANIC/GRIEF, shame for SHAME, disgust for DISGUST), five-way accuracy against a chance of 0.20.
- **Bar for showing reasons.** On the five-way task the slots-only model is within 0.10 of the direct reader's accuracy. Then an event's stake is a fair account of why the reader said what it said. If the gap is wider, stakes are computed and not shown, and the report says which slot is weakest by dropping each in turn.

### 4.2 The table as written (`trigger-table-1`)

The same five-way task with nothing fitted. Each report gets five scores, each a sum of standardised slots with unit weights, and the highest names the channel. The operational reading of the handoff's table is the analyst's:

| Channel | Table row | Score |
|---|---|---|
| RAGE | a sudden drop; I can get it back by pushing | unpleasantness, plus suddenness, plus another's responsibility |
| FEAR | a drop coming, fast; get clear of it | unpleasantness, plus ahead (4.3), plus tags tranquility and health, minus own responsibility |
| PANIC/GRIEF | a drop that has already happened; only someone else can undo it | unpleasantness, plus already (4.3), plus tags family, contact, belonging and romance, minus own responsibility, minus another's responsibility |
| SHAME | a drop in how I'm seen, below what I'd forecast; it can't be contested | unpleasantness, plus own responsibility, plus others' standards broken, plus tags approval and status |
| DISGUST | something that would spoil what I hold; keep it out | unpleasantness, plus tags food, health and order, plus another's responsibility, minus suddenness |

- **Two gaps, stated.** "Below what I'd forecast" has no slot that text carries and is not scored. If 4.3 misses its bar, the FEAR and PANIC/GRIEF scores drop their when term and the report says so.
- **Not blind.** The analyst has seen pairwise gaps on this corpus (14 November) and the tag profiles above. The tests of the table filed before data are Sounding Line's this week: four contrasts in the MIDUS daily interview, which nobody has seen, and five in an open diary set, where a published paper on the same data reports the average links and the contrasts are new.
- **Report.** Accuracy, the confusion table, and beside it the same confusion table for a logistic model fitted on the same slots. Where the fitted model is right and the table wrong, the row of the table is the finding. Send both tables to the theory thread through the return.
- **Bar.** 0.33. Under that, the table as the analyst operationalised it does not read reports, and events carry no `channel_by_table`.

### 4.3 Already or ahead

No corpus on the branch rates when. Build a rule tagger from the main verb's tense and modality (future, conditional, "about to", "might", "afraid that" against completed past and perfect), two values and unclear. Test: among Crowd-enVENT fear and sadness reports, the area under the curve of "ahead" for fear. Bar 0.60. Then the same pair with the need tags added, to see whether when adds to which need (the pre-flight says need alone gives 0.722). The slot is provisional in the theory, and this is the first number on whether text carries it.

### 4.4 The packs

- **`rp-label-1`.** TP10's fine-tuned head as a `channel` pack with `status: research` and no aggregation receipt: events only, never a share. Its label map is TS2's: anger to RAGE, fear to FEAR, sadness to PANIC/GRIEF, shame to SHAME, disgust to DISGUST. The other eight labels have no channel in the theory ("Pride, guilt and embarrassment are labels, not channels") and write nothing.
- **`rp-trigger-1`,** a `trigger` pack (2.1). Its directory holds the nineteen need-tag heads and the eight-feature head as per-sentence score heads on one encoder, and the tense rules of 4.3 as a pinned file. It names the gate (TP25) by pin, and `rp-label-1` when that exists. For each sentence the gate passes it computes the scores and writes one event with `stake` filled: `need` from the highest-scoring mapped tag, `direction` from the valence pair, `by` from the responsibility pair, `when` from the rules, `mapping.status: proposed`. The event goes on the reading of the channel `rp-label-1` names; with no label pack it goes on the channel the table names, and only if 4.2 cleared. If 4.2 cleared, the event also carries `channel_by_table`. Where the label reader and the table disagree, both are in the event, and the research view can show the disagreement beside the sentence. That disagreement, on text the owner knows, is the most direct look at the table he can have this week.
- `rp-need-1` (section 3) is the same nineteen heads packed alone as a `tags` pack, with thresholds, for the need diagrams.
- A sentence the gate passes that the label reader gives to a label with no channel writes need events only.

## 5. TP25. Nothing here

**Why.** Section 1. On plain prose the label reader invents a feeling two times in three or more.

**Design.** A gate ahead of every other reader: is anything at stake for someone in this sentence. One sigmoid head on the frozen encoder.

**Keys, all labelled by people, all on the branch or in section 3's archive.**

| Source | Something at stake | Nothing |
|---|---|---|
| GoEmotions | any of 27 feelings | neutral |
| Story Commonsense, emotion files | the character is marked affected | marked not affected |
| Crowd-enVENT | the twelve feelings | the no-emotion reports |

**Test.** Train on two sources, test on the third, all three ways; then train on all three and test on text nobody labelled for this: B13's 40 theme-free items and the verified revision sentences from TP10's record.

**Bars.** Silent on 0.80 of the theme-free items and of the revision sentences (the label reader managed 0.35 and 0.20), while passing 0.70 of the sentences people marked as carrying a feeling in each held-out source. Report the whole curve, and where no threshold reaches both numbers say so and pack nothing.

**Then rerun TP12 behind the gate.** Corrected counting failed when eight sentences in ten were neutral. With the gate removing most of them first, repeat its 80%-neutral condition. If the corrected share now beats the raw one, write TP12's selection receipt, which unblocks `channel` packs and TP22.

**By construction.** A gate learns genre as easily as stakes: stories are full of stakes and forum posts are not. The leave-one-source-out rows are there to show how much of it is genre.

## 6. TP26. The first reading through the wire: worry as a Stress reading

**Why this one.** It is the only reader that cleared both its main bar and its stretch bar, its key is the writer's own number, and a `scalar` series needs neither a gate nor a counting receipt. It is the fastest way to find out whether the wire holds.

**Do.**

1. TP16 Part A scored five models, one per fold of writers. Refit one head on all writers with the same settings and pack it as `rp-worry-1`. The five fold scores stand as its benchmark, and the manifest says the packed head itself was never scored. Manifest: `scalar`; range 1 to 9, as the corpus paper gives the worry scale, to be confirmed against the data file; `research_only: true`, because the Real World Worry Dataset is treated as research-only; `status: research`; reading id `S1`; `mapping.status: proposed`, because worry is offered as a reading of Stress and the theory has not ruled that it is one.
2. **Off its home corpus,** three known-group checks with data on the branch. The area under the curve of predicted worry for: Crowd-enVENT fear, sadness and anger reports against joy, pride and relief; EmpatheticDialogues situations labelled anxious, afraid, apprehensive or terrified against content, joyful or grateful; GoEmotions nervousness and fear against neutral. Bar 0.70 on each. These say only that the reader's number rises where people say they are afraid. They do not say it measures Stress.
3. **On plain prose:** the distribution of predicted worry on the 40 theme-free items. Reported, with no bar. A reader that puts plain prose at 5 of 9 is shown with that fact in its caption.
4. Attach through TS3 and open the Stress detail in the research view on one long text.

**Parts B and C of TP16** stay closed here. Sounding Line's RW1 tests "a plan is resolved energy" on the same corpus under its controls, and this week's packet there adds first-person share as a rider (the owner: "Saying I is a stress marker, huh?").

## 7. TP27. The pause remainder, as plumbing

**Why.** The owner's new idea in Round 24: "If they hesitate before a word that's an indicator that they noticed something that's relevant". The thread's form: part of a pause is explained by how surprising the word is, and the remainder marks a swap of attention. Sounding Line tests it this week on the typing fit it already holds (its card KP1). If it lands, the engine's attention row has its first marker inside a typing log. TP18's estimate cleared 0.02 and the lower end of its interval did not, and a hidden-state probe on the same data lost ground (-0.0218 [-0.0379, -0.0082]).

**Do, and claim nothing.**

- A feature in `features/`: for a process capture with word onsets, the remainder of log pause after a regression, fitted within writer, on word length, log frequency, sentence start, preceding punctuation and the word's surprisal under SmolLM2-135M run locally as a scorer (already on the branch; scoring is not reading in the sense the standing rule forbids, and TP18 already used it).
- Run TP18's combined model with the remainder added, on the sessions TP18 used, as a new row (TP18b). Same gate: a gain of 0.02 with the lower bound above it. The record is right that nothing added afterwards recovers TP18's own primary; TP18 stays as filed.
- The top-right window is not touched. When Sounding Line's KP1 lands, its verdict decides whether stops with a large remainder are shown as places where the schema changed.

## 8. Carried cards

| Card | Disposition |
|---|---|
| TP7, the choice benchmark on Stack Exchange questions | run now; EX5 arrived on 15 November |
| TP17, TP20, TP1c | finish as specified on 14 November |
| TP22 | stays blocked until TP12's receipt exists (section 5) |
| TP14 | retired from the queue; IM2 replaces IM1 (section 3) |
| TP13 Part B | closed; its gate failed and nothing here reopens it |
| TP15, CARE | stays at 0.388 against 0.40; no pack; no follow-on |
| TP19 | parked |
| TP10's top rung, a 9B model as labeller | parked for the Spark (section 11) |
| E1 in the handoff's register: the goal tree is an unscored guess | relabel now: the packet field and the panel caption say "unscored", in the research view and the default view alike. Finishing the pilot waits for a key |

## 9. Order and budget

One long job at a time under the host's 8 GiB commit floor; the short ones fill the gaps.

| Day | Work | Why here |
|---|---|---|
| 1 | TS3 on the constructed packs (2.1 to 2.6, step 1). TP26 steps 1 and 2. TP7 | the wire does not wait for a benchmark; worry is ready |
| 2 | TP26 through the wire into the research view. TP23 steps 1 to 3 | first real reading on screen |
| 3 | TP23 transfer and pack; IM2 export. TP25 | Sounding Line can start IN13 Part D |
| 4 | TP24 4.1 to 4.3; `rp-label-1`. TP12 behind the gate | the label reader can show events as soon as a gate exists |
| 5 | TP24 4.4 (`rp-trigger-1`); TS3 acceptance step 2 with every pack that exists | the panel shows needs, channels with reasons, and Stress, in the research view |
| 6 and 7 | TP27; TP17, TP20, TP1c; the return | |

If the week is cut short, the order above is the priority. A wire carrying one honest reading is worth more than five readers with no wire.

## 10. Choices made here

1. The need key is Story Commonsense, with Reiss's nineteen tags mapped to the six needs by the table in section 3. The map is a proposal.
2. Packs trained on it are research-only, on the analyst's reading of an archive that states no licence.
3. A gate is required before any reader of feeling may run. Without one the engine shows a `scalar` series or nothing.
4. The label reader may show sentence events in the research view without TP12's counting receipt. It may never show a share without it.
5. `marketplace` becomes `toolbox` in the wire format, as `bottom-box-2`.
6. Research readers appear only behind the research flag, and the default packet does not change.
7. The front-end work is plumbing and one flagged path. No visual design is decided here.
8. TP14 is retired in favour of IM2.
9. The goal tree is relabelled unscored now.
10. Speed is recorded and not tuned this week.

## 11. For the Spark, next week (no work here)

The owner asked for first thoughts on design decisions for the machine arriving on 16 November. These are the analyst's, for the engine's side only. None of them depends on a particular specification of the machine.

- **One job the engine needs from it first: labels.** A large local model reads the Crowd-enVENT reports, the Story Commonsense lines and a few hundred essay sentences and writes the four slots directly (which need of the six, which way, by whose doing, already or ahead), under a fixed prompt, with the model's hash and the prompt's hash in every row. The small heads are then trained on those labels. The owner said it himself on 15 November: "learning is a bit like distilling." The reader that ships stays small; the teacher never ships.
- **Measure the teacher before trusting it.** Its labels are scored against the same keys the small readers faced (the writers' labels, the annotators' tags, the five readers) before any head is trained on them.
- **Pin for same answers.** The readers record already shows a pre-flight number moving by up to 0.012 between two machines. Fix the library versions, the thread count and the decoding (temperature zero, one seed) and run the same-answers check the handoff lists before anything else.
- **The top rung that never ran:** the published RoBERTa-large reader of event reports scores 0.594 where MiniLM scores 0.476. A large encoder fine-tuned on the Spark is the slow version of TP10, and its outputs can teach the small one.
- **Sealed sets stay on that machine.** ValueEval, CANDOR and anything else under a request form are read there by a script that writes totals, in the same pattern as Sounding Line's sealed MIDUS run. The engine receives heads and scores, never rows.
- **Voice** (the owner: "video's not worth the cost, but sound absolutely will be"): word onsets and pitch from CANDOR's audio feed TP27's remainder in speech. Nothing in this week's wire assumes text only: an event's span is a span of the transcript.

## 12. The return

One file, `docs/ENGINE_TRIGGER_READER_2026-11-22.md`, in the form of the readers record: what was implemented, what ran, what is outstanding. In it:

- one line per card with its bar, its number and whether it cleared;
- for TP24, both confusion tables;
- the packet JSON and one screenshot from TS3's acceptance;
- every licence as read at download;
- a short list headed "for the theory thread": the tag map's weak rows, guilt and shame, the result on already or ahead, and any row of the trigger table that the fitted model contradicts.

## 13. Limits

- The need key is annotators' reading of why characters in invented five-sentence stories act. It is naive psychology by design, in the third person, and its transfer to first-person reports is one bag-of-words pre-flight by the analyst.
- The stakes written into events are a reader's account of a sentence. They are not the maker's appraisal, and nothing here moves a maker estimate.
- Worry is one corpus, one month, one country, and is offered as a reading of Stress on the analyst's proposal.
- The trigger table's operational form in 4.2 is the analyst's and was written after seeing related numbers.
- Every pre-flight number is one pass in one evening and is to be reproduced on the branch before it is relied on.
