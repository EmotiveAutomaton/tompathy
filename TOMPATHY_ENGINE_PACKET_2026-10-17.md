# ToMpathy engine packet, 17 October: fix the gates, warm the backend, and what the last runs changed

17 October 2026. **For the ToMpathy agent and the curator, who is working on the engine today.** This packet adds to the 16 October driver (`claude/TOMPATHY_DRIVER_2026-10-16.md`); it doesn't replace it. The driver's order still holds: the research preview (P0) wins if time runs short. This packet puts six fixes ahead of P0, because without them P0's labels would rest on gates that admit constant answers and a fitter that fails converged fits. If work already exists locally that this repository doesn't show (`codex/0.3-engine` is still `82789fd`, 15 October), keep it and apply only the deltas. Handing it over is the curator's authorization; nothing here needs a decision from him.

## 0. What the last runs taught the engine

| Source | Finding | What it changes here |
|---|---|---|
| Engine inventory (this pass) | The question gate checks accuracy only for the five yes/no questions. Readers that give one constant answer pass Q3 (0.50), Q4 (0.50), Q8 (0.125) and Q10 (0.10) | Fix 1. Q8 decides which corrections train preferences; Q10 feeds the drive prior |
| Ghost T1 | `Backbone.fit` raised "MAP fit failed: ABNORMAL" on a fit that had converged: gradient 1.16e-5, objective gap at most 6.8e-12 | Fix 2. It blocks Ghost's writing twin and probably the Stage 15 witness |
| Sounding Line V1 | Planted taste and habit were never recovered at any size; only a constant lean was | No personal taste or habit estimate shows as measured. The preview says "not yet seen by our tests" |
| Sounding Line V2 | The backbone beats population rates by 0.0240 half-Brier [0.0175, 0.0307]; no calibrated reader combination adds 0.01 | The global tab's number |
| Sounding Line G3-A0 and F4 | Haiku fails tone, contradiction and themes. Local Qwen 3.5 9B passes Q1, Q3, Q4, Q5, Q7, Q8 and Q9 on constructed items, but under Sounding Line's backend settings, so the engine's pin refuses those receipts | Section 2: the warm backend, and receipts under the engine's own pin |
| Ghost N3 | Hard half-space corrections emptied the hypothesis set in 96 of 96 settings | Corrections become soft votes (after Thursday) |
| Ghost N4c | With actions alone, a goal-directed rule and a habitual one are exactly aliased; probes separate them | "What would move this estimate" names probes, not just evidence types |
| Ghost R4, N5, N7 | A reliable root cue is worth up to 0.643 nats; correcting a reader's projection with population rates is worth 0.949; stated against revealed, 0.250. All constructed | The goal tree's root reliability is a declared prior, labeled assumed; the copy cites all three as constructed-world results |
| The curator, 17 October | One inference with three entries (function from the top, the person, the process); overlays rather than one top; recurring against one-off departures; attention as trust; beauty as fast resolution | Section 3's copy and display changes |

## 1. Six fixes before anything else (today)

### Fix 1. The question gate

**Where.** `engine/tompathy_engine/transcribe/admission.py:47-51`, and the copy at `features/records.py:110-118`.

**Rule.** Every question, binary or not, must reach:
- validity of at least 0.95;
- overall accuracy of at least 0.85;
- accuracy within each true label of at least 0.70;
- accuracy within each template family of at least 0.70;
- accuracy at least 0.10 above the best constant answer (the modal label's share);
- the cross-check where one exists (at least 0.8);
- for Q10, which answers with a set: exact-set accuracy as above, plus recall of at least 0.70 for every theme tag.

An invalid answer counts as wrong. Labels are keyed by `json.dumps(expected, sort_keys=True)`, so Q10's sorted lists key a dictionary and compare equal to themselves. Sounding Line enforces only the overall and per-label floors (`runners/next_round/literal_admission.py:58-70`); the family, constant and tag floors are new here.

**Sketch:**

```python
import json
OVERALL, PER_LABEL, PER_FAMILY, PER_TAG, CONSTANT_MARGIN = 0.85, 0.70, 0.70, 0.70, 0.10

# before the loop: exactly one family tag per item, or refuse the battery
families = [[t for t in i.get("tags", []) if t.startswith("family-")] for i in items]
if any(len(f) != 1 for f in families):
    raise ValueError("Every battery item needs exactly one family-N tag")

# inside `for n, item in enumerate(items):`, for every item; an invalid answer is recorded as wrong
rows.append({"key": json.dumps(expected, sort_keys=True), "expected": expected,
             "answer": answer if is_valid else None,
             "correct": is_valid and answer == expected, "family": families[n][0]})

def _rates(rows, key):
    groups = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r["correct"])
    return {k: sum(v) / len(v) for k, v in groups.items()}

per_label = _rates(rows, lambda r: r["key"])               # recall per true label (Q10: per exact set)
per_family = _rates(rows, lambda r: r["family"])
best_constant = max(sum(r["key"] == k for r in rows) for k in per_label) / len(rows)
per_tag = None
if question_id == "Q10":                                    # recall per theme tag
    tags = sorted({t for r in rows for t in r["expected"]})
    per_tag = {t: sum(r["answer"] is not None and t in r["answer"]
                      for r in rows if t in r["expected"])
                  / sum(t in r["expected"] for r in rows) for t in tags}
passed = (valid_rate >= 0.95 and accuracy >= OVERALL
          and min(per_label.values()) >= PER_LABEL
          and min(per_family.values()) >= PER_FAMILY
          and accuracy >= best_constant + CONSTANT_MARGIN
          and (per_tag is None or min(per_tag.values()) >= PER_TAG)
          and (agreement is None or agreement >= 0.8))
```

Template families are already carried as `family-N` tags (`transcribe/batteries.py:170`). Store `per_label`, `per_family`, `best_constant` and `per_tag` in the receipt. `Labels.require` rechecks them from the receipt, not from a `BINARY` set.

**Tests:**
- a constant reader fails every question (the inventory's probe, `binary_gate.py`, becomes a test);
- a reader perfect on all labels but one fails;
- an invalid answer counts as wrong;
- an item without a `family-N` tag is refused. The transport fixture at `tests/test_transcriber.py:47` gets `f"family-{i % 4}"` in its tags, so it still passes;
- Q10's exact-set scoring and per-tag recall have their own test.

**Also, after Thursday.** Battery coverage is cosmetic:
- items without "not" or "false" are tagged paraphrase;
- ten items get the same appended negation;
- Q5's and Q6's cross-checks reuse the rule that generated the labels, so agreement equals accuracy.

The effective sample is 4 to 10 template families. Rebuild with real negations, real paraphrases and an independent cross-check. Until then, technique notes carry "lab-tested on templated items".

### Fix 2. Certified convergence in `Backbone.fit`

**Where.** `engine/tompathy_engine/models/backbone.py:44-67` (`_fit`).

**Why it is safe to accept.** The objective is the penalty times the squared offset plus a convex log-loss, so its Hessian is at least 2 × penalty × identity. A strongly convex function with modulus μ satisfies f(x) − f* ≤ ‖∇f(x)‖² / (2μ). With μ = 2 × penalty, the gap is at most ‖g‖² / (4 × penalty). For Ghost's failing T1 fit that bound is 6.8e-12, which is exactly what Ghost's 50-digit check found.

**Sketch:**

```python
def _fit(rows, center, penalty, initial=None):
    if sum(r.weight for r in rows) <= 0:            # the early path returns the pair too
        return np.zeros_like(center), {"optimizer_message": "no weighted rows", "iterations": 0,
                                       "newton_steps": 0, "certified_gap": 0.0}
    objective, hessian = ...                         # objective as now; hessian below
    result = minimize(objective, np.zeros_like(center) if initial is None else initial,
                      method="L-BFGS-B", jac=True, options={"maxiter": 500})
    x, steps = result.x, 0
    if np.isfinite(x).all():
        x, steps = _newton_finish(objective, hessian, x)    # every fit, not only flagged ones
    f, g = objective(x)
    bound = float(g @ g) / (4 * penalty)             # certified gap, strong convexity
    tol = 1e-9 * max(1.0, abs(f))
    if not (np.isfinite(x).all() and np.isfinite(f) and (result.success or bound <= tol)):
        raise ValueError(f"MAP fit failed: {result.message}; certified gap {bound:.3e}")
    return x, {"optimizer_message": str(result.message), "iterations": int(result.nit),
               "newton_steps": steps, "certified_gap": bound}


def _newton_finish(objective, hessian, x, max_steps=20, target=1e-10):
    f, g = objective(x)
    steps = 0
    while steps < max_steps and np.isfinite(g).all() and np.abs(g).max() > target:
        step = np.linalg.solve(hessian(x), -g)
        t, noise = 1.0, 1e-12 * max(1.0, abs(f))
        while t >= 2.0 ** -30:
            fn, gn = objective(x + t * step)
            # Armijo, or, below the objective's rounding floor, a smaller gradient
            if np.isfinite(fn) and (fn <= f + 1e-4 * t * (g @ step)
                                    or (fn <= f + noise and np.abs(gn).max() < np.abs(g).max())):
                break
            t /= 2
        else:
            break                                    # no progress: the certificate decides
        x, f, g = x + t * step, fn, gn
        steps += 1
    return x, steps
```

- **The Hessian** is 2 × penalty × I plus each row's weighted softmax covariance of its features: the matrix `Backbone.fit` already builds for its intervals (lines 120-126), evaluated at the current offset.
- **Why every fit gets the finish.** Fits L-BFGS-B calls successful stop at its default gradient tolerance, and where they stop depends on rounding, which is the likely cause of Ghost's option-order failures (6.83e-6 against a 1e-7 tolerance).
- **Why the second acceptance rule.** Near the optimum the objective's changes fall below its rounding, so a plain Armijo search stalls. A first draft without the rule stalled on T1 at a gradient of 4e-6.
- **Checked on a scratch copy of today's loop objective,** 17 October:
  - T1's published input: L-BFGS-B still reports ABNORMAL; one Newton step reaches a gradient of 2.2e-13 and a certified gap of 2.5e-27.
  - The same input stopped at one L-BFGS-B iteration: two Newton steps certify it.
  - T1 with options permuted 20 times: predictions move at most 5.7e-14 with the finish, against 1.9e-8 with plain L-BFGS-B (which flagged 1 of the 21 runs ABNORMAL).
  - 72 random problems (penalties 0.005 to 10, feature scales 0.1 to 100): at most 2 Newton steps, every gradient below 1e-10, coefficients within 5.3e-11 of a direct Newton solution.

Update the four call sites in `Backbone.fit` (lines 94, 106, 109 and 117) to take the pair, and carry the receipt into the bundle, so an accepted fit is never silent about how it was accepted.

**Tests:**
- Ghost's published failing input (`results/v23/twin-profile-review-20261017/T1_FAILED_FIT_INPUTS_points.npz`) now fits, with its certificate;
- the same input truncated at `maxiter` 1 is rescued by the finish, with its certificate;
- permuting the options within every choice moves predictions by less than 1e-9;
- the result matches a direct Newton solution to 1e-8;
- `Backbone.fit([], until=..., dimensions=3)` still returns the uniform prior (`tests/test_backbone.py:59`);
- a stubbed optimizer that reports success with a non-finite x still raises, as today's code does.

**Also:** rescale the MAP features in `features/deterministic.py:22-29` (log1p of the character and token counts), not in `Backbone.fit`, so Ghost's pinned fit, which builds its own features, doesn't change. The ridge penalty currently depends on raw character counts.

**When it lands,** tag the commit `certified-fit-1` and tell Ghost and Sounding Line. Ghost looks for the tag at each health review, runs its Stage 15 witness successor if the tag arrives before Monday 12:00 PDT, and pins T1's successor to it in V24.

### Fix 3. The frontend drops what it doesn't know

**The problem.** The zod schemas are non-strict, so fields the engine adds are silently stripped (`src/core/model.ts`). Schema 1.8's labels would vanish without an error.

**The fix:**
- add the 1.8 fields;
- parse preview packets strictly;
- add a parity test: every field the engine emits survives `parsePacket`.

### Fix 4. The website demo overwrites real readings

**The problem.** On the curator's site, the hand-written demo packet is reinstalled whenever no matching packet exists (`src/App.tsx:495-503`). Expanding a section mid-talk would swap the engine's reading for the authored one.

**The fix.** In preview mode, never install it. The driver's rule stands: a cached real run is the only fallback.

### Fix 5. Silent truncation and silent refusals

- **Context length.** The backend sends no `num_ctx` (`transcribe/backends/local.py:94-100`), so Ollama's default applies, and 12,000-character windows can be cut server-side without notice. Send `num_ctx` explicitly (8,192, matching Sounding Line's receipts), and refuse a prompt that might not fit:
  - count tokens with the model's tokenizer when the backend exposes one; otherwise estimate them as characters ÷ 3, which overcounts English;
  - refuse when that count plus the reply budget (`num_predict`, 256) exceeds `num_ctx`;
  - after each call, also refuse the answer if the response's `prompt_eval_count` plus 256 reaches `num_ctx`, because then the prompt filled the window.
- **Health.** `/v1/health` shows nothing when an admission is refused: in the module admission file, `engine/tompathy_engine/admission.py:80-88`, `enabled()` swallows every failure. Report the reason.

### Fix 6. Names in packets

**The problem.** Wikipedia usernames go straight into maker labels (`packet/build.py:74-88`).

**The fix.** Pseudonymize to "Editor 1, Editor 2" in packets. Reveal locally on click, never export (driver section 5). Make `registry/publish.py` refuse per-person readings.

## 2. Speed: a warm backend (today and Sunday)

**The problem.** Every call loads its model cold, on one thread (`keep_alive: 0`, `num_thread: 1`), and the backend refuses to run if any model is already resident, so pre-warming is impossible. The measured rate is 14.8 seconds per call. Technique notes (100 calls) would take about 25 minutes, Q8 and Q9 on 35 corrections about 17 minutes, and the goal tree (21 calls) about 5 minutes. The budgets are 2 minutes.

**Build an owned lease:**
- the companion loads each model once and holds it for the session;
- `keep_alive`, threads and `num_ctx` are configurable and recorded in the pin;
- the residency guard refuses only a resident model that the lease doesn't own.

**Receipts under the engine's own pin.** Rerun the batteries for Q1, Q3, Q4, Q5, Q7, Q8 and Q9 with Qwen 3.5 9B under the warm backend and Fix 1's gate, before Wednesday. That's about 1,400 calls.
- **On CPU:** at most 2 threads, below-normal priority. While they run, they count as one of Sounding Line's CPU slots (its packet, section 4.2). A 9B model on 2 threads takes roughly a minute a call, so the set takes about a day; run the questions in the order Q8, Q9, Q5, Q1, Q3, Q4, Q7, since Q8 and Q9 gate preferences.
- **On the GPU,** only when Sounding Line's GPU queue is empty (its packet, section 4.2), as one session that holds the shared GPU lock for its whole duration and unloads the model before releasing it, so Sounding Line's cold-start memory floor still holds between its jobs.

Questions that pass get "lab-tested" badges backed by a receipt the engine accepts. Questions that fail stay off. Don't import Sounding Line's receipts; their pins differ by design.

**Measure on the demo machine and record the results** in `docs/PERFORMANCE.md`:
- the deviation map;
- each reader;
- each transcriber question;
- the goal tree;
- the history fetch.

**If a stage misses its budget, drop it in this order:**
1. the payoff map's layer 2;
2. the second reader;
3. technique notes beyond the first 30 regions;
4. the goal tree's governing call (local candidates still render).

## 3. Thursday preview: changes to the driver from today's theory

All of this is copy, labels and grouping on top of the driver's P0 and P1. No new inference needs a test to ship labeled "untested".

### 3.1 Three entries, one inference

The curator: "one big inference of empathy" with three entries:
1. functional reverse engineering from the top;
2. the person;
3. the process.

Group every panel's evidence by entry, derived from the existing `basis` field:

| Entry | Bases |
|---|---|
| **From the page** (what it seems built to do) | `text-surface`, `model-judgment` |
| **From the person** (their records, or the population's when there are none) | `choices`, `population` |
| **From the process** (how it was made) | `corrections`, `history` |

Add `entry` beside `basis` in schema 1.8. Each panel heading shows which entries fed it.

### 3.2 The goal tree is a functional reading

- **Label it:** "A functional reading: what the page seems built to do, read by assuming its maker would use it as we would." Psychology calls this the teleological stance, and anchoring on oneself is its known bias.
- **Hover:** "Goals are often several at once. This is one lens."
- **Overlays.** When the governing cover leaves more than a third of local candidates uncovered, show two trees side by side as lenses instead of forcing one root (the curator: "there's no top... different lenses... overlays").
- **Root reliability.** Use a declared prior of 0.6 for the root cue's reliability, labeled "assumed". Cite Ghost's R4 (0.643 nats when leaf evidence is sparse, at a reliability of 0.99 planted in its worlds) only as a constructed-world value: nobody has measured a root cue's reliability on real pages.

### 3.3 Recurring and one-off departures

The curator's pervasiveness test: "The biggest thing to tell a branch that has been autocompleted is the pervasiveness of similar-looking decisions."

On a page:
- a **recurring departure** is a phrasing or construction the population reader finds unusual, used across several sections;
- a **one-off departure** appears once.

Route recurring ones to the habits panel as "this writer's signatures" and one-off ones to the attention panel as "where attention likely went".

**The honest copy.** Recurrence shows the choice belongs to the writer; it doesn't show the choice was automatic. A deliberate style is recurrent too. So the habits panel says "signature (habit or deliberate style)", never "autocomplete".

**Labels.** Both stay "untested" unless Sounding Line's D30 lands positive; then cite its number, labeled descriptive. If D30 lands negative (recurring choices were slower, the mark of deliberate style), the habits panel says "signature (more likely deliberate style)". D30 measures recurrence across prompts, and a page shows recurrence across its sections, so the hover says: "Recurrence across this page's sections stands in for recurrence across a writer's work."

### 3.4 Two readers, measured on common words

**The problem.** Readers tokenize differently, so compare them on words (common byte spans), never tokens, as Sounding Line's P1 does.

**The fix.** Score each word including its trailing space or punctuation. Leading-space tokenizers otherwise misstate word probabilities ([Pimentel & Meister 2024](https://arxiv.org/abs/2406.14561); [Oh & Schuler 2024](https://arxiv.org/abs/2406.10851)).

**Readers.** Keep the driver's Qwen2.5-0.5B and SmolLM2-360M. Both are in Sounding Line's P1 roster, so its D21 convergence curve applies to them directly. If the demo machine misses budget, fall back to SmolLM2-135M, and say so on the badge.

**Copy** (the curator's attention as trust): "Where both readers flag a departure, trust it more. Attention follows how much you trust what you're seeing."

### 3.5 Resolves fast (the payoff map)

The curator: "interest is disassembly, and beauty is the rapid disassembly."

Layer 2 of the payoff map already measures re-reading gain: how much a passage makes earlier text easier.
- **Add a rate:** that gain per token of the resolving passage.
- **Label** the top three "resolves fast", with the hover: "After this short passage, what came before suddenly reads more easily. A proxy for the aha; not measured enjoyment."

The novel-span and shuffled controls from the driver apply unchanged.

### 3.6 "What would move this estimate" names probes

Ghost's N4c showed that actions alone can't separate rules that probes separate. So each card's line names the probe:

| Card | Probe line | Status |
|---|---|---|
| Constructed value | "Would it persist if the need it grew from were met another way?" | already in the driver; lab-tested by N4c |
| An absent option | "Offered directly, would they take it? Taking it means it was never considered; declining means it was weighed and refused." | Ghost N9, pending |
| Habit against goal | "Under time pressure, which way would they go?" | Ghost N11, pending |
| Attention | "After a source fails them, do they check it more?" | Sounding Line D39 and Ghost N15, pending |

### 3.7 Drives: honesty fixes

- **Remove the theme-to-drive mapping from the borrowed prior** (`packet/prior.py:8` imports Q10's mapping, against the driver's rule). Replace the seven identical cards (support 0.5, width 0.8765) with the population position and "what would move this estimate".
- **Emit the frontend's categories.** Use `valueCategory: "drive"` and the display name "Belonging" for PANIC/GRIEF, so `driveFor()` finds the frontend's definitions (`src/core/drive-systems.ts:36-39`).
- **"Bodily needs" is not one of Panksepp's systems.** By the curator's vocabulary it is a need, a set point. Move it out of the drives list, into a needs line under the header.

### 3.8 Claims ahead of evidence: relabel for Thursday

| Item | Where | Change |
|---|---|---|
| "Candidate expertise" from 3 against 3 edits | `packet/process_signals.py:126-130` | "untested", or remove |
| "Edit focus" shown as current attention, with one label for every frame | `packet/modules.py:189-214` | relabel "where edits concentrated" |
| A sign probability rendered as a support weight | `packet/drives.py:90-93`, `packet/preferences.py:144-146` | relabel "direction confidence" |
| The model's own rating of goal support shown as relative support | `models/goal_producer.py:9-25` | relabel "the model's own rating" |

### 3.9 The global tab, with this week's numbers

Add a `globalFindings` field: source, claim, number, interval, `evidenceStatus` (`descriptive` or `constructed-tested`), link. Population items currently have to reference a single maker's hypotheses (`packet/validate.py:200-205`), so this needs its own field.

**Sounding Line:**
- V2: "a model that starts from everyone and adjusts a little for each writer forecast these writers better than population rates": 0.0240 half-Brier [0.0175, 0.0307].
- V1: "in planted tests, our instruments found a writer's constant lean, not yet their taste or habits."

**Ghost, each labeled "in constructed worlds":**
- R4: 0.643 nats;
- N5: 0.949 nats;
- N7: 0.250 nats.

### 3.10 History robustness for the Wikipedia demo

- **Suppressed revisions.** Treat a suppressed revision as a boundary instead of aborting (`adapters/wiki.py:70-72`).
- **Rate limits.** Obey `Retry-After` (`:50-51`).
- **Fetch limit.** Make the revision limit a request parameter; the companion fixes it at 20.
- **Oversized hunks.** Exclude an oversized hunk per item instead of aborting the transcription.
- **Matching edits to the page.** Strip wikitext before matching edits to rendered regions. Articles over 10,000 characters diff by line, so hunks are paragraphs of markup, and "edit focus" would come up empty.
- **For the demo.** Pick pages accordingly, and cache their histories beforehand.

## 4. After Thursday, in order

1. **Corrections as soft votes with misspecification flags.** Each correction becomes a vote with slack, weighted by how well the current hypotheses explain it ([Bobu et al. 2020](https://arxiv.org/abs/2002.00941)), never a hard half-space (Ghost N3). Flag the corrections no hypothesis explains, and feed them to Ghost N10's residual test when it lands.
2. **Module-scoped implementation hashes.** Today any edit voids every admission and fitted bundle, including Ghost's reader bundles (`admission.py:27-35`). Pin each module to the files it imports.
3. **The three-entry reader with reliability weights,** once Sounding Line's D37 measures how much the page, the person and the process each carry.
4. **The personal deviation map:** score against the person's own history when records exist, if Sounding Line's D33 is positive.
5. **The consistency ceiling display,** from Sounding Line's V5: how much of this person is predictable at all, so no reading claims more.
6. **Kelley's attribution display:**
   - consensus (the population reader);
   - distinctiveness (across sections or works);
   - consistency (across revisions);

   with Sounding Line's D30 and D31 and Ghost's N14 as its tests.
7. **Statements with a shared-shift correction:** stated goals read against revealed ones, after correcting the shift everyone shares (Ghost N7).
8. **Abstention.** When the evidence is under a reliability threshold (Sounding Line's V3), say "not enough to read" instead of a weak estimate.
9. **Personal taste and habit panels,** only once Sounding Line's V4 shows a reader that sees planted taste or habit, and built on that reader.
10. **Ghost's needs:**
    - a revision-purpose target (intent classes from IteraTeR and Wikipedia's taxonomy, `basis: corrections`);
    - the module gate list in the Ghost packet, section 7, which names the witnessing study per module.
11. **The driver's own after-Thursday list** (section 10), from item 1, minus what this list absorbed.

## 5. Cross-repository

- **To Ghost and Sounding Line:** the commit that carries Fixes 1 and 2, tagged `certified-fit-1`, with its test results, as soon as it lands. Ghost looks for the tag at each health review and runs its Stage 15 witness successor on it if it arrives before Monday 12:00 PDT. Sounding Line re-pins only at its Tuesday digest.
- **From Sounding Line**, at its daily 20:00 digests:
  - D30 (recurring against one-off);
  - V5 (ceiling);
  - D33 (the personal deviation map);
  - D39 and D38 (trust);
  - D37 (entry weights);
  - D21 and D27, after its GPU pass.
- **From Ghost:**
  - N9, N11 and N15 for the probe lines;
  - N12 for overlays;
  - N14 for the attribution display;
  - the module gate list.

## 6. Acceptance tests added to the driver's

1. A constant-answer reader fails every question's battery, at both gate sites.
2. Ghost's failing T1 input fits with a certified gap under its tolerance; permuting option order moves predictions by less than 1e-9; an optimizer result with a non-finite x still raises.
3. Every engine field in a 1.8 preview packet survives frontend parsing.
4. On the curator's site, preview mode never shows the hand-written demo packet.
5. A prompt longer than `num_ctx` is refused with a reason, never truncated.
6. No packet or export contains a Wikipedia username.
7. The warm backend's measured times are in `docs/PERFORMANCE.md`, and every stage either meets its budget or is dropped in the stated order.
8. No preview output contains a theme-to-drive mapping or a "Bodily needs" drive.

## 7. Pre-mortem

| Failure | Guard |
|---|---|
| The gate fix leaves no question admitted for Thursday | That's the honest state. Technique notes show "untested" until a receipt under the engine's pin passes, and the talk can say so |
| The convergence fix accepts a fit that isn't converged | The certificate is a proof under strong convexity, not a tolerance on the flag. The Newton finish runs on every fit, and the option-order and non-finite tests guard the other side |
| Battery reruns slow Sounding Line's cards | CPU only at 2 threads and below-normal priority, counted as one of its slots; the GPU only when its GPU queue is empty, in one locked session that unloads before release |
| The warm backend still misses the budgets | The drop order in section 2, measured on the demo machine, decided before Wednesday's rehearsal |
| The recurring/one-off split reads as "habit equals automatic" | The copy says signature (habit or deliberate style), and the label stays untested until D30 |
| New copy crowds the panels | Copy changes replace text; they don't add panels. The entries are a heading line, not a new panel |
| An edit voids admissions mid-week | Nothing is admitted now. Module-scoped hashes come after Thursday |

## Sources

**Repository:** ToMpathy `codex/0.3-engine` `82789fd`:
- `engine/tompathy_engine/transcribe/admission.py`, `features/records.py`, `transcribe/backends/local.py`;
- `models/backbone.py`, `packet/prior.py`, `packet/drives.py`, `packet/build.py`;
- `src/App.tsx`, `src/core/model.ts`.

**Sounding Line:** `runners/next_round/literal_admission.py`; results V1, V2, G3-A0 and F4.

**Ghost Scale:**
- `TWIN_PROFILE_REPORT.md`;
- `results/v23/twin-profile-review-20261017/`;
- the N3, N4c, N5, N7 and R4 reports.

**Literature:**
- [Bobu et al. 2020](https://arxiv.org/abs/2002.00941)
- [Pimentel & Meister 2024](https://arxiv.org/abs/2406.14561)
- [Oh & Schuler 2024](https://arxiv.org/abs/2406.10851)
- the teleological stance, [Gergely & Csibra 2003](https://doi.org/10.1016/S1364-6613(03)00128-1)
- Kelley's covariation model, [Kelley 1973](https://doi.org/10.1037/h0034225)
