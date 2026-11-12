# ToMpathy 0.3 engine, week packet (26 October to 1 November): the process pyramid, attention and field-tested badges

> *Checked three times by an independent reviewer and fixed after each round. The third round found no major problems.*

*Spec sheet for the ToMpathy agent. It supersedes the 25 October "wing" addendum and runs to Sunday 1 November, 22:00 PST (2026-11-02T06:00Z). Every decision is made here. Return to the curator only on the existing triggers.*

**Scope.**
- Engine updates only, chosen where Sounding Line's and Ghost's findings license them and the change is cheap.
- The curator is reworking the Core values panel himself (bottom right: `ValueTabs.tsx`, `ValueList.tsx` and what they render). Don't touch it.
- **Order:** B13 stays first. Then the items here, TE1 to TE9. Then the rest of Track B and the 18 October carry-forward, in their order.
- Items carry a TE prefix so they can't be confused with Sounding Line's or Ghost's card ids.

**The curator's product need.** It isn't a values readout yet. He wants:
- to fill out the process pyramid (the process hierarchy pane, `ProcessHierarchy.tsx`) from the record;
- to mark divergences from it as candidate attention;
- to show current attention as following the active higher-order process.

## What the engine has today (`5f3ad0a`), and what it doesn't

**The pyramid is the page's functional outline.**
- In preview readings (`preview/judgments.py`), `goalHierarchy.nodes` is one document node over at most 20 paragraph-group nodes, each located by `regions`.
  - Groups run `ceil((n - 1) / 19)` regions long, so on pages of up to about 20 regions every group is a single region.
  - The admitted path (`packet/goals.py`) builds "governing goal" and "local goal" levels by region containment instead.
- The schema's optional `span` is used only by the authored safe example's sentence nodes. No engine path emits it.
- For preview readings, the pane shows every non-document node on one tier (`ProcessHierarchy.tsx` 299 to 306).
- On history pages the outline belongs to the unattributed page maker, not to any editor.

**Departures are phrases and sentences, not words.**
- `preview/surface.py` scores words internally, then emits:
  - the top 15 non-overlapping phrases of 1 to 3 words;
  - every sentence at or above the page's 90th percentile.
- `preview/build.py` turns each into a hypothesis with one span and, if it doesn't recur, a current-attention frame.
- Departure hypotheses carry no type field. The code finds them by the description prefix "Where this text went somewhere".

**Current-attention frames can't carry time.**
- A frame is `{maker, span, items}`, with no node tag, step or time.
- Frames for one maker may not overlap. `partition_attention` cuts overlapping frames into cells, and payoff items share them.

**Records lack per-change events.**
- The CoAuthor adapter keeps order and timing per suggestion episode only. `replay.py` applies each change's text delta, and `coauthor.py` reads each event's time (`eventTimestamp`); neither keeps a per-change list.
- Wikipedia histories carry revision order and timestamps. Their changes are wikitext hunks with no position on the captured page.
- `packet/process_signals.py` holds located inspection events, but they are dormant: region-level, admitted path only, and produced by no collector.

**What this packet builds.**
- Attention marks on the outline, by region (TE3).
- A time-ordered attention structure, plus a per-change event extractor that TE4 and TE8 share.
- Badges for the two Sounding Line results that already pass their controls (TE2).

## 0. How to run this

- **Push first.** As last fetched in the curator's review clone (18 October), `origin/codex/0.3-engine` shows nothing after `5f3ad0a` (tagged `certified-fit-1`). Push local Track B work there with the first daily status line, so this week's routes see it. Don't move or re-tag `certified-fit-1`.
- **Missing Track B pieces.** If a Track B item this packet builds on (B2, B4, B8, B11 or B12) isn't in your local work, build the minimal piece the item needs and say so in the status line.
- **Standing amendments (permanent).** There is no `AGENTS.md` here. Create one at the repository root, with a section headed "Standing amendments, 25 October". Sounding Line and Ghost use the same heading. These rules outlast the window.
  - **A. Never idle.** While commissioned items remain, keep the next one built and tested before reporting a stop.
  - **B. Healing passes, for engineering failures only.**
    - A crash, a dependency or build failure, a timeout, a memory failure, or a test broken by a known code change gets a diagnosed repair and a rerun, up to twice, without waiting to be asked.
    - Record each in the daily status line.
    - A battery that fails its gate is a result, not a fault. It is recorded as failed and stays disabled. Any prompt or item change is pre-registered as a new run under B6 and B13.
  - **C. Follow-ups.** When a Sounding Line or Ghost result lands that touches an engine module, check it against the companion's claim ledger and open the matching engine item, gated as below, without being asked.
  - **D. Claims by id.** Every badge and status text that cites research quotes the companion repository's claim-ledger row: its id, public wording and control status.
    - The hand-copied figures in `engine/tompathy_engine/preview/findings.py` (Sounding Line's V1 and V2; Ghost's R4, N5 and N7 from V23) move to ledger lookups.
    - Where no row exists yet, keep the figure with its source path and pinned commit, marked "no ledger row".
    - `GlobalFinding` has no field for a ledger id; its `claim` field is the finding's sentence and stays that way. Add an optional `ledgerRows` list beside it, in both schemas, with the same entries as TE2's.
- **No admission changes** beyond those named here.
- **Privacy:** unchanged. Owner-only probes, `PRIVACY.md`'s promises, and no cross-source identity matching.

## 1. Items, in order (after B13)

**TE1. Commit Sounding Line's EV4 package.**
- **The files.**
  - 12 files in `docs/sounding-line-engine-features-2026-10-20`.
  - Sounding Line delivered them on 23 October with the curator's approval. They are uncommitted here.
  - Ghost committed its copy (`ceb9859fa`).
- **Do.**
  - Check every file against the hashes in Sounding Line's `results/phase_2_4_stage_15/DRIVE/EV4_DELIVERY_20261023.json` (its commit `4800d2675`).
  - Add a `-text` rule for `docs/sounding-line-engine-features-2026-10-20/**` to `.gitattributes`, as the repository already does for archived files, so Windows checkouts keep the hashed bytes.
  - Commit the files unchanged.
  - Point B8 at the table as a badge source.

**TE2. A "field-tested" status for preview items, and the two badges already licensed.**
- **Why.**
  - The item-level vocabulary (`previewLabels`) has three statuses: admitted ("tested"), constructed-tested ("lab-tested") and unvalidated ("untested"). It has none for a field result that passes its controls under scoped wording.
  - Sounding Line's results aren't admission witnesses by themselves. `globalFindings` already reports Sounding Line's V2 as "descriptive".
  - Two Sounding Line routes pass their references and license scoped wording. Both are pinned to `5f3ad0a`, the preview reader (Qwen2.5-0.5B) and its departure definition.
    - EV4 records the engine commit but not the reader's identity. Sounding Line sends the export's reader identity (model revision and manifest sha256) by Monday 26 October, 20:00 PDT. Compare it with `packet.preview.readers`; until they match, the badges below stay "untested".
    - **EV1:** "tested on human writing logs: flagged words came after longer pauses".
      - +0.073 log-pause per page interquartile range of departure, interval +0.060 to +0.086, conditional on frequency, length and surprisal covariates.
      - Its within-session permutation reference passes.
      - It covers surviving writer-typed words. Deleted words and accepted AI text are excluded.
    - **EV2:** "recurs in the writer's other work".
      - +1.38 per 10,000 words, interval 0.05 to 3.14.
      - Its fake-writer reassignment reference passes.
      - It is a recurrence contrast, not an identification test, so its own ledger row governs it, not TE6's identity rule.
- **Do.**
  - **The status.**
    - Add `field-tested` to `previewLabels` in `src/core/preview.ts` and to `PreviewLabels` in `engine/tompathy_engine/packet/contract.py`.
    - Leave the maker-evidence and `globalFindings` enums in `src/core/model.ts` unchanged.
  - **Its display.**
    - Label it "tested on logs". Its reason: "Supported on human writing logs under scoped wording; not an admission gate."
    - Add both to the label and reason maps in `EvidenceBadge` (`src/components/PreviewStatus.tsx`).
    - Add an `.evidence-field-tested` class to `src/mind.css`.
    - Widen the badge allowance in `GoalCloud.tsx`, which sizes badges by status (54 px for "lab-tested", 46 otherwise), so the longer label doesn't clip.
    - `EvidenceBadge` is shared: `ValueList.tsx`, in the panel the curator is reworking, renders it too. The change is additive, but say in the status line that `PreviewStatus.tsx` changed.
  - **A `ledgerRows` list.**
    - Add an optional `ledgerRows` list to preview items in both schemas, each entry `{ledgerId, wording, controlStatus, source}`. A phrase signature can carry both EV1's and EV2's rows.
    - Leave `basis` as it is: departures stay `text-surface`. It is a closed enum that also sets `entry`.
  - **A departure marker with its unit.**
    - Add an explicit marker on departure hypotheses in both schemas, carrying the unit from `surface.py`: `finding: "departure-phrase"` or `"departure-sentence"`. Retire the description-prefix match.
    - `render_deviation` keeps the first row with a given span, and phrases are listed before sentences, so today a phrase row wins a collision. Set the unit to `departure-sentence` when a later sentence row shares the span, so the item stays "untested". Collisions are rare: only a short, unpunctuated, region-final line such as a heading.
- **Apply.**
  - EV1's wording goes on phrase departures (1 to 3 words) produced by the pinned reader and definition, in both their current-attention and signature roles.
  - EV2's wording goes on phrase signatures only.
  - Sentence departures stay "untested" until Sounding Line's PP2 licenses them.
  - Until Sounding Line's Stage 15 ledger exists (it is backfilled at its handoff), cite `S15-EV1-PAUSES-V1` and `S15-EV2-SIGNATURES-V1` with the EV4 table row and file hash.
- **Habit and style** stay "untested" unless WA0 licenses them this week under Sounding Line's identification rule.
  - **Habit:** if WA0 passes EV3's final-document variant both raw and residualised on accepted AI text, each under both of Sounding Line's identification tests.
  - **Style (B2):** if WA0 passes its final-document variant of PMAP's style features, raw and residualised the same way.
  - Quote WA0's figures with "45 writers, one interface, final documents".
  - A pass on PMAP's own channel reads typed text, so it licenses no page badge.
- **Rhythm.** B2's timing rhythm stays owner-capture only, with the device caveat. The preview's "Sentence rhythm" item (sentence length) follows the habit rule.
- **Tests.**
  - Schema round trip for the status, the `ledgerRows` list and the unit marker, in both schemas.
  - A phrase departure renders "tested on logs" with EV1's wording in its title.
  - A sentence departure and an unlicensed habit item stay "untested".
  - The new badge doesn't clip in the goal cloud.

**TE3. Attention on the page's outline.**
- **Why.**
  - The curator wants divergences marked on the pyramid. The live pyramid is the document node over paragraph groups, located by regions, and departures sit in regions.
  - Counting departures per group shows where they concentrate within the page's functional outline.
  - It displays where marks fall. It is not a tested reading.
- **Engine.** For each paragraph-group node, compute from departure hypotheses' own spans, deduplicated by hypothesis id:
  - `attentionDensity`: departures in the node's regions per 100 content words;
  - `attentionShare`: the node's share of the page's departures.
- **What counts.**
  - Count non-recurring departures only, the ones that enter current attention. Recurring departures are signatures, not attention.
  - Content words follow the engine's own definition (not in `STOP`, not held out), over regions in `preview.coverage`. Regions not read show "not read", not zero.
  - Don't count from partitioned frames, which double count and include payoff items.
- **Fields.** Emit both figures as optional node fields in both schemas, with `attentionEvidence` (status plus ledger rows) and `divergence` (true or false) beside them. The node's own `evidenceStatus` is unchanged. No new model calls.
- **Divergence.**
  - Single-region groups are common on short pages: the engine's reading of the bundled example has nine single-region groups of 30 to 41 content words. So shrink each node's density toward the page's rate before ranking:

    $$\text{shrunk density} = \frac{d + k\,r}{w + k}$$

    where $d$ is the node's departures, $w$ its content words, $r$ the page's departures per content word, and $k = 50$ content words.
  - Mark the nodes in the top decile of shrunk density that have at least one departure and a raw density above the page's rate. A page with no departures marks nothing.
  - The description reads: "this part departs most from expected wording".
- **Evidence.**
  - Density and divergence stay "untested" at the paragraph-group level. PP2 tests sentences and PP5 tests plan roles; neither tests paragraph-group density, so neither licenses it.
  - The phrase marks inside a node keep their own TE2 badges.
- **Rare words.**
  - The page-normalized departure is a rescaling within the page, so it removes neither frequency nor topic effects.
  - Until a frequency table is pinned in the engine, the density carries the note "may track rare words and topic changes".
  - Once one is pinned, residualise per-word departure on log frequency and word length (EV1's covariates) for the density count only. Departure items and their EV1 badge keep the unresidualised definition they are pinned to. The frequency table is its own later item.
- **Panel.**
  - An optional density shading per node in the process hierarchy pane.
  - The node tooltip (its SVG title) and the label badge name the evidence.
  - Leave the Core values panel alone.
- **Tests.** The authored safe example has neither departures nor an engine reading, so test on engine readings:
  - On the engine's reading of the bundled example (`src/core/example.ts`, A4), nine single-region groups: densities match the deduplicated departures, and exactly one node is marked. Read the group count from the reading rather than hard-coding it. The reading needs the pinned reader, which CI lacks, so save it as a fixture.
  - A page with no departures shows no shading.
  - Unread regions show "not read".
  - A page where one paragraph repeats a rare technical term (routine for the topic) and dominates the shading. Keep the repeats within one paragraph: repeated across paragraphs, the term becomes a signature, which density excludes. Build it with a fake reader that returns stated per-word losses. Keep it as a known-failure test that flips when residualisation lands.

**TE4. Current attention through time: an attention timeline.**
- **Why.**
  - The curator: current attention follows whatever higher-order process is active ("a paragraph about X").
  - A current-attention frame has no node tag, step or time, and frames can't overlap, so one frame per step can't carry order.
- **Schema.**
  - Add an optional `attentionTimeline` to preview and imported packets, in both schemas. Each entry is `{maker, step, t, located, region, node, evidence, evidenceStatus, basis, description}`, ordered by step:
    - `region` and `node` are null when `located` is false, and `node` is also null whenever no paragraph-group node covers the region (no goal producer configured, a dropped governing call, an unjudged group, or a CoAuthor document outside the sample);
    - `goals` is optional and used only by TE8;
    - `basis` is `history`;
    - `node` is the paragraph-group node whose regions contain the change.
  - Extend the preview validation (both schemas) to cover the entries; it requires `evidenceStatus` and `basis` on every item and rejects unknown fields.
  - Add one packet evidence entry per revision (Wikipedia) or per session (CoAuthor), so each entry's `evidence` has something to point at. Keep each excerpt to the changed fragment, a few hundred characters at most: packets over 2,000,000 characters are rejected, and the history window can be raised to 500 revisions.
- **Wikipedia histories (this week, live preview).**
  - For each revision, locate its surviving inserted text with the admitted path's matcher (`packet/modules.py`: an exact, unique match of at least 3 characters in a surviving region). Record unlocated changes as unlocated.
  - Give each revision one entry per located hunk, sharing the revision's `step`, and one unlocated entry for the hunks that don't match.
  - The capture keeps inline citation markers ("[12]") that the revision text lacks. Strip citation-marker forms (`[12]`, `[a]`, `[note 3]`, `[citation needed]`) from region text at match time, and leave other brackets such as "[sic]". Don't change the capture, which would move anchors and cache keys.
  - The preview fetches the 20 most recent revisions by default, so the timeline shows when each part of today's outline changed within that window. It doesn't show any editor's plan.
  - Revision gaps (minutes to years) are not pauses.
  - Evidence must not quote editor usernames. `hide_usernames` leaves excerpts and sources untouched.
- **CoAuthor (this week, imported packets only).**
  - **The extractor.** Build a per-change event extractor beside the adapter. It takes each event's time from the raw log, as `coauthor.py` does (`eventTimestamp`), and applies text deltas through `quill.apply_delta`, as `replay.py` does. It emits time, position, inserted and deleted units, and menu events. The compiled ledger rows aren't enough.
  - **Placing changes.** A session has no regions until an artifact is built from its final document. Build one (paragraph regions and a title). Tag every inserted unit with its change index through `apply_delta`'s `insertion_owner` argument, map surviving units to their final regions, and mark changes whose text was later deleted as unlocated. The Wikipedia matcher can't do this: most CoAuthor changes are single characters.
    - `make_capture` collapses whitespace and trims each paragraph, so keep a map from final-document offsets to (region, offset).
    - Units present at initialization, such as a pre-filled prompt, carry no owner and aren't changes.
    - Pure deletions insert nothing; record them as unlocated.
  - **The hierarchy's cost.** A CoAuthor document gets a hierarchy only if the goal module runs on it. That is one call per paragraph group plus one governing call, up to 21 per document: about 170 s per call on the art essay's long groups, less on short paragraphs.
    - Measure the first three documents.
    - Cap the sample at 3 CPU-hours or 20 documents, whichever comes first.
    - Start only when one of Sounding Line's counted slots is free. While it runs, write the lock at `results/.cpu-slots-20261017/tompathy-demo-prep.lock` in Sounding Line's working directory: a JSON file with `created_at`, and `expires_at` set to the run's projected end, no later than 2026-11-02T04:00Z. Remove it when done. Sounding Line keeps one counted slot free while an unexpired lock exists, ignores expired ones, and treats any lock as expiring at most 6 hours after its `created_at`, so a longer run renews it.
    - Locally, don't load the goal model unless at least 16 GiB of RAM is free.
- **Evidence.**
  - Every timeline entry reads "untested", with the description the engine already uses for edit-location frames: "weak evidence of attention".
  - Calling an edit location attention is an inference, not structure.
- **Pause marks wait for PP1.**
  - If PP1 passes, adopt its definition and hesitation probability as delivered: writer-typed text only; intervals touching suggestions or multi-character inserts dropped; residualised on the within-word interval; a lognormal mixture, never a fixed threshold.
  - They read "untested" unless PP6 (do process marks find the sentences that matter to the writer?) passes. PP3 runs on ScholaWrite only, so it licenses no "what the writer is doing now" wording on CoAuthor or live pages.
- **Owner captures** carry no timing (`docs/OWNER_CAPTURE_EVIDENCE.md`), so live pages get timelines only through revision histories.
- **Tests.**
  - A Wikipedia fixture with one located change, one unlocated change, and a paragraph carrying a "[12]" marker.
  - On a CoAuthor session, the extracted changes rebuild `final_document` exactly, and their count equals `replay.py`'s `deltas`.

**TE5. Plan-boundary layer: record now, build later (only if Sounding Line's PP5 (i) is positive).**
- **This week:** record PP5's role definitions and result in B12, with a short design note.
- **The classifier is its own later item.** It needs:
  - a named training source: a public corpus with discourse labels, or a model Sounding Line trains and delivers under its privacy rule (raw CoAuthor text leaves Sounding Line only for the Gear 3 provider);
  - a pin;
  - its own validation;
  - a layout change, so the pane can show a third tier. It flattens non-document tiers now.

**TE6. Claim rules in the admission chain.** Add these to `docs/DRIVE_ADMISSION_CHAIN.md` (B12), creating the file if B12 hasn't:
- **Identity badges** need Sounding Line's new rule: a writer-label permutation, a context-only reference and disjoint samples.
  - A pass needs permutation p below 0.05, and real minus context-only with its writer-cluster 95% interval above zero.
  - A same-row fake-writer reference with a chance-centred flag no longer counts, for or against.
  - Recurrence contrasts such as EV2 follow their own ledger row.
- **Constructed-world witnesses** (Ghost's) are quoted as "miniature, architecture untested" (Ghost's own wording), with their exact aliases. Their readers are named as exact finite-library enumeration, and their assumed choice model is stated.
- **Any display of what someone is after** names its route:
  - an intervention;
  - a natural removal in the record: an option unavailable before the choice (Ghost's "remove");
  - an emotion-like signature that fires on a logged outcome block, after the choice. Ghost's W6 sets which aliases this can break: level-shifted and habit aliases, not shared-piece ones;
  - or "aliased: passive records can't separate these".
- **Field-tested badges** cite a claim-ledger row and resolve their state at render time, from a pinned claims snapshot shipped with the app.
  - Then cached and saved readings drop a superseded badge too.
  - The preview cache key covers only `.py` and `.yaml` files, and saved sessions store whole packets, so a build-time rule would leave stale badges.
  - One snapshot file serves both: `docs/claims/SNAPSHOT.json`. The engine reads it at run time and the app bundles it at build time.
  - A superseded or non-passing snapshot row turns "field-tested" into "untested". Nothing else changes.

**TE7. Owner questions ordered by the alias map.** B4's owner probe card asks three kinds of question, one per Ghost intervention. Order them by the share of alias pairs each separates in Ghost's W1 map (due Thursday 29 October, 12:00 PDT). Until it lands, use this order:

| Intervention | Owner question |
|---|---|
| Satiate (devaluation) | B11's question: "If X no longer led to Y, would you still want X?" |
| Switch | B4's first question: "Would you keep this phrase for a different audience?" |
| Remove (before the choice) | New: "If this way were closed, what would you do instead?" |

If Ghost's W12 finds an observation that separates an end from a habit that carries affect within 32 observations (devaluation, substitution, its own affect, or a novel context), record the matching owner question for when drawn tips exist. Record the micro-sacrifice question too: "Would you give up a little of [Y] to keep [X]? Would you give up a lot?" In Ghost's V23 N4d, varying the stakes separated a lexicographic rule, the formal shape of a sacred value, from a weighted one (constructed). Insensitivity to the amount is the sacred-value marker. No tips are drawn this week: the preview strips drive items, and there are no admissions.

**TE8. Pieces and goals on imported CoAuthor packets.** Pieces: only if Sounding Line's WB1 routes to pieces. Goals: only if WC1 beats situation-conditioned frequency and the Markov comparator.
- **Pieces.**
  - Port WB1's event alphabet, piece definitions and classes as a module that reads raw CoAuthor events through TE4's extractor. The alphabet needs per-change times and positions: bursts with no gap of 2 s or more, pauses of 2 s or more, deletion runs, revision moves, and menu events, with tercile bins.
  - Output token-use rates per 100 events, beside Sounding Line's population rates per situation.
  - Badge "untested" until WB2 or WB3 is positive.
- **Goals.**
  - Port WC1's five-goal inverse planner with Sounding Line's fitted β and ρ and its progress table. Only do this if WC1 beats both the Markov chain (its primary comparator) and situation-conditioned frequency.
  - Show the goal readout per stretch in TE4's timeline, on imported CoAuthor packets only, as "what the writer seems to be doing now". Fill TE4's optional `goals` field (goal to relative support) on the entry that closes each stretch. TE8's own rule: relative support, never a probability.
  - Never label it values or wants.
- **Timing on any live display** follows B2's rule: owner captures only, with the device caveat.

**TE9. Recency weighting: record now (only if Sounding Line's TR4 is positive).**
- Record TR4's adaptive rate and its definition in `docs/B15_READING_MANY_WORKS.md` (create it from B15's carry-forward text) and in B12.
- TR4's adaptive reader is a per-writer filter fitted on that writer's earlier sessions. Record which of two things Sounding Line sent: a population distribution of rates, or a filter to fit per maker. Sounding Line's packet sends the definition with the rate.
- Build the weighting with B15, after B16's privacy update. `PRIVACY.md` promises ToMpathy doesn't create a model of the creator.

## 2. Receiving this week

| From | What | Where it goes |
|---|---|---|
| Sounding Line | Claim-ledger rows that license or change a badge | TE2; TE6 |
| Sounding Line | WA0's figures | TE2's habit and style rules |
| Sounding Line | PP1, PP2, PP3, PP5 and PP6's definitions and results | TE3 to TE5 |
| Sounding Line | The EV1 and EV2 export's reader identity (model revision and manifest sha256) | TE2 |
| Sounding Line | WB1's alphabet, pieces and classes; WB3's population rates; WC1's goals, β, ρ and progress table | TE8 |
| Sounding Line | TR4's adaptive rate and its definition | TE9 |
| Sounding Line | WD1's lean and sensitivity definitions | B3: "lean (criterion)", with sensitivity shown separately if WD1 is positive |
| Ghost | W1's alias map and separation shares (Thursday 29 October) | TE7 |
| Ghost | W6's signature result; W7's attention result | TE6; the badge text of TE3 and TE4 |
| Ghost | W12's result | TE7's owner questions |
| Ghost | W4's records-needed curve (Saturday 31 October) | Recorded in `docs/B15_READING_MANY_WORKS.md`: how many records before a maker's deviation from its population shows |
| Ghost | W3's route on selective uptake | Recorded in B12 as the condition for any future "useful, but carries this maker's end" display |
| Ghost | N16's confirmation state | B1's scheduler gate |
| Ghost | The corrected stress-map sentence | B1's notes on N16 |

## 3. Pre-mortem

- **"Tested on logs" is read as validation of the reading.** EV1 supports an association between departures and pauses, not that a departure is attention.
  - *Guard:* the badge's title quotes the scoped wording; only phrase items get it; density, divergence and timeline entries stay "untested".
- **Density just tracks rare words or topic shifts.** The page-normalized departure doesn't remove them.
  - *Guard:* the note shows until residualisation lands, and the known-failure test keeps the problem visible.
- **The timeline is read as an editor's plan.**
  - *Guard:* the outline is the page's functional reading, owned on history pages by the unattributed page maker, and each entry says "weak evidence of attention".
- **The CoAuthor hierarchy run crowds Sounding Line's slots.** At up to 21 calls per document it can take hours.
  - *Guard:* the 3 CPU-hour or 20-document cap, measured on the first three documents; the lock file, which Sounding Line's week 3 packet honours; and the 16 GiB free-RAM check before loading the goal model.
- **Pieces built for CoAuthor don't transfer.**
  - *Guard:* TE8 is research-path only. Nothing reaches live pages this week.
- **A badge goes up on a weak licence, or stays up after its row is superseded.**
  - *Guard:* badges quote the ledger row's estimate (identity badges quote real minus context-only), and they resolve at render time.
- **Badges and warnings are taken as protection.** Warning writers that an AI assistant was biased, before or after writing, didn't reduce the attitude shift co-writing produced (Williams-Ceci et al. 2026: two experiments, more than 2,500 participants, per the abstract and Cornell's release).
  - *Guard:* badges describe evidence. Nothing in the panel claims to protect the reader from a maker's influence.

## Sources

- [Williams-Ceci et al. 2026](https://doi.org/10.1126/sciadv.adw5578) (abstract), and [Cornell's release](https://www.news.cornell.edu/stories/2026/03/ai-assistants-can-sway-writers-attitudes-even-when-theyre-watching-bias)
