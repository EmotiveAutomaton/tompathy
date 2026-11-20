# SP1 Spark verification and timing protocol

Only the public Crowd-enVENT reports and open-data-derived model weights enter
this lane. The owner-pinned environment, explicit model IDs and original files
stay fixed. No source behind the private tree is accessed. Each remote script
must match a committed repository version before copying and running.

Select 500 reports from the original 1,200 held-out report IDs, ordered by
SHA-256 of `SP1:23:ID`. The first 200 are the parity set; the first 300 are the
reader panel. Selection occurs before any Spark model output. The remaining
200 make the required timing pilot. No selection by model score or rating.
The held-out reports include writers also present in fitting; this is the
original report-held-out split, not a writer-held-out claim.

The selected C0 frozen need pack uses its exact original encoder and linear
head. A direct Transformers adapter applies float32 masked mean pooling and
unit normalization with cap 128, then the unchanged head. TF32 is disabled;
attention uses eager evaluation. Run 500 reports on CPU and GPU, retain durable
16-report batches, and compare the first 200 against the original workstation
probabilities. CPU/reference, GPU/reference and CPU/GPU maximum gaps must all
be <=.0001. Loading is excluded from the two timing rates. A failure is a result;
do not retry a failed numerical gate with changed settings.

The local reader A is the already installed full ID beginning `56671c2ab938`;
do not update its tag from the catalog or mix it with workstation predictions.
The [Ollama catalog](https://ollama.com/library/qwen3.5/tags), inspected November
19, lists 35b at 22 GB and the available 122b variants at 81 GB. Reader B's
candidate is the default 35b tag, the largest listed parameter count whose
listed weight size is under the card's 64 GB limit. Its actual full digest,
quantization and resident size must be recorded after one pull and loading;
listed size alone is not measured runtime fit. The model remains fixed thereafter.

Each reader first performs the 500-report pilot. The prompt and JSON schema
live in the committed job script: eight original feature names, integer 1–5
ratings, temperature 0, seed 23, thinking disabled, 4,096 context and 256 output
tokens. Complete text is sent; a report too long for that fixed context must
be stopped/recorded rather than silently truncated. No repair prompt or retry
for invalid JSON. Every raw response and its parsed values are retained privately.
Pilot timing includes request loading and is reported as such. The first 300
responses are the panel's first pass, not repeated to manufacture a fresh sample.
The second 300-report pass is separately sized from pilot timing before launch.

Panel mean Spearman correlation is calculated over valid paired rows, with
the saved readable-feature comparator scored on precisely those same rows.
Report missing/constant columns. Repeatability means identical canonical eight
integer values for >=99% of the 300 pairs; invalid pairs are not identical.
Structured validity must be >=99.5% across all 600 panel calls. Compare readers'
scores on their common valid first-pass rows before selecting the higher score;
keep per-reader figures beside that comparison. Qualification requires the
correlation, repeatability and validity bars. Teacher studies cannot use an
unqualified result. Nothing is pooled across model IDs.

Every GPU job holds the shared `/home/agent/gpu.lock` exclusively. Three numerical
threads and one light telemetry worker stay within the four-thread allowance;
tokenizer parallelism is disabled. Lower process priority, fresh owned outputs,
an eight-hour maximum, STOP checks and five-second temperature/power/thermal
reason sampling apply. Stop at 90 C or any reported thermal slowdown, preserving
saved batches. A guard trip during a reader call cancels this job's HTTP client;
only its own initially absent, subsequently loaded model may be unloaded.
Foreign resident models are left untouched. A 64 GiB resident-memory check follows
the first model response. Outputs are copied back and hash-verified before any
owned remote result cleanup; open model caches are retained. Scheduling alone is
not completion or result delivery.
