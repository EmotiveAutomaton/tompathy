# SP1-v2: corrected feature meanings

The owner authorized this separate panel on November 19 after the original
prompt's direction errors were identified. The original SP1-v1 responses,
prompt, results and stopped runtime are retained unchanged. No v1 prediction
is relabelled, flipped, pooled with v2 or reused as a v2 response.

The source is the [Crowd-enVENT questionnaire, section 4.1 and Appendix A3](https://aclanthology.org/2023.cl-1.1.pdf).
High `social_norms` means violation, and high `standards` means conflict with
personal ideals. The original prompt mistakenly asked for compatibility on
both fields. Goal support concerns expected favorable consequences, rather
than a retrospective judgment that goals were achieved. Responsibility items
ask whose actions caused the event. This correction is an implementation
correction frozen before v2 responses; the original raw scores do not establish
failure of an accurately specified reader.

| Feature | High score means |
|---|---|
| pleasantness | More pleasure for the writer |
| unpleasantness | More unpleasantness for the writer |
| self_responsblt | The writer's own actions caused what happened |
| goal_support | The writer expected favorable consequences for themself |
| social_norms | Actions behind the event broke laws or social norms |
| other_responsblt | Another person's actions caused what happened |
| standards | More conflict with the writer's personal ideals and standards |
| suddenness | Greater abruptness |

The committed script keeps v1 and v2 prompts distinct. V2 explicitly sets the
writer's perspective at the time of the event. Ratings remain integers 1–5,
from not at all to extremely. The schema, temperature zero, seed 23, thinking
disabled, context 4096 and output cap 256 stay fixed. There is no prompt repair
or invalid-response retry. Exact prompt and model hashes are recorded.

Use the same previously fixed 500 held-out public reports and original writer
ratings/comparator. The first 300 form the panel; all 500 provide the timing
pilot. Each model gets fresh v2 predictions. Reuse that model's own first 300
v2 responses for its first panel pass, then score the same 300 once more after
sizing from its actual pilot. No new encoder parity run is needed: neither
the original encoder nor its saved head/input binding has changed.

The original thresholds remain: mean first-pass Spearman at least the saved
comparator on the same valid rows; identical canonical eight values on at
least 99% of 300 pairs; valid structured output on at least 99.5% of 600 calls.
Invalid pairs remain in denominators, and constant columns are unavailable.
Average-tie ranks and Pearson correlation implement Spearman with NumPy;
the implementation matches the original SciPy reference within 1e-14 on
constructed ties and the eight original saved feature comparisons.

Reader A remains the installed full digest beginning 56671c2ab938. Reader B
is the separately pinned candidate from the unchanged catalog rule. Compare
their first-pass means on common valid rows; retain both standalone results.
All new outputs and aggregate/ledger IDs carry SP1-v2. Teacher agreement and
downstream prerequisites remain separate; no serving or maker admission follows.

The same Spark GPU lock, total four-thread budget, below-normal priority,
thermal/STOP controls and measured-pilot sizing apply. Each v2 job has a fresh
explicit bound because this is a separately authorized study, not an extension
of the expired v1 retry window. Any future engineering continuation retains its
own original v2 deadline. Failed scientific gates are never rerun.
