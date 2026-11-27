# TP72 sealed CPU reader

Verify every file in `payload/` against the separately pinned `manifest.json` before import. Mount the payload read-only. Use a fresh private scratch directory, a CPU, at most two numerical threads and a network-isolated image. The receiver controls release of all tables, cohort comparisons and timing. The reference image provides Python, NumPy and SciPy. The one additional package is tokenizers 0.22.2. Its original Linux AArch64 wheel and unmodified ABI3 library are included. The Windows rehearsal uses the corresponding Windows package.

Run the constructed rehearsal with `python -B rehearse72.py /scratch/new-fixture`. It creates invented histories and conversations. It checks both real encoders, the two-person disclosure boundary, the missing-rating cohort and the registered matching calculation. Each adapter writes CSVs to its own fresh directory. Only receiver-approved aggregate CSVs can enter the output gate.

## History input

Run `python -B run72.py history /scratch/projection /scratch/new-tables`. The receiver authenticates its archives, enforces its eligibility rules and projects the original five complete scores and the retained comments. The input headers are `author,Openness,Extraversion,Agreeableness,Conscientiousness,Neuroticism` in `traits.csv` and `author,id,day,community,text` in `comments.csv`. The calendar day uses ISO format. The program reads `excluded_communities.json` and `dropped_comments.json` as JSON string arrays computed by the receiver inside the job under DJ. Empty arrays are valid when measured. The projection can already have removed those members. The Python entry point `history.history(projection, scratch, frozen, check, observe, excluded=communities, dropped=comment_ids)` also accepts the lists directly in private memory. A receiver using the current streaming projection can supply each residual comment ID as it increments its existing dropped-comment counter. No source documentation or external list is needed.

The full-history readings average qualifying comments per person. Opening lengths, whole-date halves and the hashed nested samples follow TP58. The outside authors supply topic vocabulary and a style/topic ridge. With no outside observations, partial and matching arms are unavailable. For efficiency, the ridge is fitted to base-vector coordinates once. Averaging and projecting those residuals is algebraically equivalent to fitting the same ridge to each linear head separately. Each subset and its two original author folds are fixed across comparisons.

## Conversation input

Sounding Line's `week8_tmp3_receiver.project` produces records with `conversation`, `speaker`, ordered `turns` and `outcomes`. Pass them in memory to `conversation.conversation(speakers, fresh_scratch, frozen, check, observe)`, or pipe that projection as JSONL to `python -B run72.py conversation - /scratch/new-tables`. The optional `conversation.turn_means(ordered_speaker_text_pairs, frozen)` returns the two frozen-coordinate means per speaker inside the job. The receiver assigns reciprocal partner ratings to the person rated and trims the original recording boundaries. The producer consumes only these fields.

The two survey outcomes retain their supplied numeric orientation. Higher reader values mean more of the named linear reading. An interpretation as worse feeling requires the receiver's verified survey coding. For recurring speakers, use the turns from meetings with the relevant rating, and average their meeting ratings with one vote per meeting. Resampling and the disclosure count are by distinct person. An individual missing rating affects only that outcome. The two-person rehearsal returns no CSV.

## Output tables

Each row gives its number of distinct people, trained estimate, 95% interval from 2,000 whole-person draws, and the count, 2.5th percentile, median, 97.5th percentile and trained midrank percentile for each control family. Cells use the same people for all matched controls. Each family has 200 separately seeded head sets. The rotated family preserves the trained head geometry on its own encoder. Worry has its own frozen encoder and matched directions. Other heads share the frozen base encoder. Intercepts cancel for these statistics. A trained estimate above, within or below the rotated band is labelled accordingly. An incomplete but nonempty family gets a partial label and its valid count. Undefined cells and cells with fewer than 11 distinct people stay inside the job. The receiver also checks small complements across known cohorts. Bind `observe(filename, labels, people)` to its in-memory roster checker before release. `panels.contracts` gives the exact allowable filenames, headers, intervals and categorical values.

| File | Quantity |
|---|---|
| traits.csv | Pearson correlation of each full-history output and each of the four original composites with each of the five self-reported traits. The map and print each have a signed cell marker and their own pass column. |
| contrast.csv | Original five diagonal correlations minus the other twenty, with original positive-leader count and separate map and print passes. |
| channels.csv | Amusement and SEEKING against Neuroticism. |
| stability.csv | Observed split-half repeat by tag, plus the mean across tags. |
| fixed_profile.csv | Expected repeat at 5, 10, 20 and 40 posts per half from the five-post base. |
| posts_needed.csv | Projected posts per half at target correlations 0.5 and 0.8. |
| matching.csv | Top-one and top-ten matching from style/topic alone, with tags added, and the paired gain. |
| growth.csv | Change in matching gain from five posts on the same contributing authors. |
| curve_check.csv | Observed minus projected repeat at the largest eligible sample on common authors. |
| conversation_affect.csv | Worry and each active unpleasant output against enjoyment and affect as recorded. |
| conversation_traits.csv | Each of the 19 tags against five self-ratings and five reciprocal partner ratings. |

The first nine tables belong to history. The last two belong to conversation. A file appears only when it has eligible rows. The class-S export limit, allowable labels, cohort rules and receiver's independent rehearsal apply to the actual tables. The original TP58 standalone placebo has been expanded to two matched 200-set families on every trained row.

The individual curator-map cell requires the registered sign, a strict row and column lead in absolute magnitude among individual heads, and a whole-person interval clear of zero. Original composite map success requires four positive leaders of five and a positive lower limit on the diagonal contrast. Print's marked directions are curiosity–Openness, order–Conscientiousness, contact–Extraversion above contact–Agreeableness, acceptance–Neuroticism, and negative power– and competition–Agreeableness. Each signed interval must clear zero for its individual pass. The print summary is the conjunction of those six comparisons. Unmapped cells have a zero marker. These two maps retain separate columns and the rotated comparison has its own verdict. The present head names include acceptance, wanting, amusement and SADNESS. The four historical composites are labelled by their ingredients or scope. A constant trained head supplies no comparison.

The PANDORA source is Gjurković et al. (2021). The conversation projection uses the CANDOR Corpus from BetterUp Labs, BetterUp, Inc., described by Reece et al. (2023). Use the NaturalTurn citation of Cooney and Reece (2025) if that transcript product is used. The present receiver describes the original timed transcript. [CANDOR Tabular](https://huggingface.co/datasets/betterup/candor-tabular)
