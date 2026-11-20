# TP30 fine rung: implementation contract before execution

This is the second rung already commissioned in the November 19 packet. The
frozen rung's failed mix and noninferiority gates remain final. No test outcome
selects this rung's training settings. The encoder parity check remains passed;
SP1's failed model-reader panel does not supply any labels to this independent
rater-share study. This contract is filed before fine-rung inference or fitting.

Retain the frozen rung's exact ordered source IDs, rater shares, unassigned
rates, Go author split, overlap exclusions and evaluation arrays. Verify their
completed source receipt and artifact pins before copying a payload. Do not
reconstruct a different cohort or rerun the frozen model. Only the already-held
public Go, Crowd-enVENT and ED texts may enter the Spark payload. Do not copy
private cross-project data. ED remains research-only.

Four separate fits retain the two source views and two objectives: Go-only
profile/control for Crowd writers and held-out Go readers; Go-plus-Crowd
profile/control for ED writers. Each starts from the original pinned pretrained
MiniLM. Reusing an encoder previously fitted on the test writers' labels would
break the source separation, so neither TP10 nor a completed fine need reader
initializes this rung. Use normalized mean-pooled cap-128 vectors and fresh
linear heads. Original source targets, constant-column treatment, channel-order
ties and unassigned control behavior remain as specified in the frozen protocol.

Use the earlier MiniLM fine-tuning recipe's fixed seed 23, batch 16, three
epochs, encoder learning rate 2e-5, head learning rate 1e-3, AdamW weight decay
.01 and gradient clipping at 1. Use float32. This rung uses the final third
epoch with no test-based selection or hyperparameter search. Both objectives
use the same rows and fixed ordering rule. Sigmoid heads sum binary soft-target
cross entropy over active channels; the control uses cross entropy on the
original largest-share category. Go and Crowd each have half the total loss
weight in their shared view. A batch mean uses full-cohort source weights,
not renormalization by each batch's accidental source mix. Constant targets
remain constant and unsupported for AUC, as in the original rung.

Before a full job, implement and verify the guarded Spark training runner,
source-bound payload, and durable continuation. Each objective's first 500
training examples form its timing segment. Save the exact weights, optimizer,
ordering and random-generator state at that boundary; subsequent work resumes
there and never repeats those updates. Record seconds per 100 separately for
training and prediction, then size bounded continuation jobs. A pilot is not a
completed model or scientific result. Predictions must be saved in bounded
ordered batches, with exact model/source identities. No full run is authorized
by implementation tests alone; the usual environment, commit, input, GPU flock,
four-thread, thermal/STOP, memory and storage checks still apply.

The fixed ordering rule uses a dedicated seed-23 CPU generator for one shuffle
per epoch. Batch size is at most 16; epoch ends and cumulative 500-example
boundaries close a short batch. The same boundaries apply in an uninterrupted
run and a resumed run. Checkpoints retain model and optimizer state, parameter
group names/settings, exact ordered-data identity, cursor, shuffle generator,
CPU/CUDA random state and runtime identity. Keep an immutable pilot and each
epoch checkpoint alongside the current durable checkpoint. Prediction batches
use the same 16-row/500-row boundaries and retain the final short batch.

The four completed forecast tables will use the existing TP30 evaluation
functions and unchanged point-estimate bars. File all per-channel/source AUCs,
mix checks, within-source PLAY/LUST figures and full co-rise tables. Keep this
rung separate from the frozen result. Rater shares are readers' guesses and
stand-in labels, not channel firing, page shares or maker needs. Passing test 1
alone still cannot enable TS4 without a qualified gate pack.

Current implementation: target/weight construction, losses, constant output
restoration, the original-model encoder wrapper, durable training segments and
ordered prediction segments have 21 passing constructed checks; Ruff passes.
Both objectives resume with bit-identical CPU weights and dropout/order state,
without repeating saved updates. Changed data, model bytes, optimizer settings
or bindings are rejected; interruption recovery preserves completed batches.
These checks use tiny constructed models, not the research encoder or corpus.
The source-bound public payload, outer Spark admission/thermal/resource wrapper,
actual GPU compatibility check and aggregate evaluation/landing remain pending.
No fine-rung research data has been fitted or scored, and no fine job is running.
