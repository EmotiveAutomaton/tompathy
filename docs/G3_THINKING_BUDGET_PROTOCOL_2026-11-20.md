# G3 development check of the thinking token limit

Registered November 20, 2026, at the owner's request, before the first higher-limit call.

Reader W will answer the G3 V2 questionnaire again on 20 of its 600 development reports. Order all 600 by the SHA-256 digest of the UTF-8 string `G3:V2:3072:23:` followed by the report ID, breaking ties by ID. Take the first 20 in that order. Selection uses only the IDs. Use the saved V2 answers on the same reports as the 1,024-token baseline.

Change the output allowance to 3,072 tokens. Keep the original reader digest, questionnaire, JSON schema and validator, thinking setting, temperature 0, seed 23, context 4,096 and two numerical threads. All 20 inputs must fit the original input guard with the larger allowance. Make one new call per report and retain invalid answers in the denominator. Keep raw envelopes and per-report results in private storage.

Report valid final answers out of 20 at each limit, and the four paired counts (valid at both, newly valid, lost validity, invalid at both). For each limit record empty answers, malformed JSON, rejected field values, length stops, tokens used and elapsed generation time. A valid answer has exactly the two registered fields, each an integer from 1 through 5. Interpret validity as the ability to return that format. This batch supplies no evidence about agreement with writers or the choice of an RD2 prompt.

The workstation runs this check after the original G3 process exits and releases its GPU lock. Use the original memory, thermal, slowdown and owner-stop guards, with a one-hour bound from the first diagnostic admission. A pause can reuse durable responses within that hour. If the comparison is interrupted, retain the partial rows and report coverage. The Spark continues its separate queue.
