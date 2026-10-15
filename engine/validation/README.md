# Retained literal-reader validation

These inputs are constructed writing examples, not human dataset records.
They and their results are retained so another consumer can inspect the exact
failed gate without making model calls or treating a software test as admission.

On 15 October 2026 the installed, digest-pinned Llama 3.1 8B reader answered the
200-item Q5 dialogue battery on one CPU inference thread. Outputs were all valid;
accuracy and quote-mark cross-check agreement were **0.755**, below the required
0.85 and 0.80 thresholds. It correctly labeled all 100 dialogue examples and
misclassified 49 of 100 non-dialogue examples as dialogue. Runtime was 2,951.68
seconds. The result is **disabled**. No prompt, threshold or test item was tuned
against this failure.

The complete outcomes, exact inputs, model/transcriber/battery hashes and runtime
are retained beside this file. A cache-only replay reproduced all 200 outcomes
without inference, and attempting normal Q5 use with this record was refused.
These template families do not establish performance on natural writing.
Other question batteries and downstream scientific admissions remain separate.
