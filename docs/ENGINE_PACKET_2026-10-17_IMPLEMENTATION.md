# October 17 engine packet implementation

Local implementation on `codex/0.3-engine`. Software verification does not grant
scientific admission. Existing source archives, working edits and research jobs
are preserved. No release/tag or cross-project notification has been issued.

Verification: build `4903a4f38479`, 43 frontend checks, targeted engine groups
(including the Ghost fixture and every question's constant-reader control),
three essay browser checks and one goal-lens/global-findings browser check passed.
Native Chrome 155 verified the essay overlay/lightbox on the preceding build;
the final build changes only preview panel layout. The final lease check also
refuses missing residency metadata instead of treating it as an unloaded model.
Focused Ruff checks and the source/image provenance audit pass. Test browsers and
servers are disposable and closed after verification.

| Packet item | Implemented behavior | Evidence or remaining limit |
|---|---|---|
| All-question gate | Shared overall, per-label, per-family, constant-margin, cross-check and Q10 exact-set/tag-recall gate; invalid answers count wrong; both consumers recheck receipts | Constant-reader controls cover all ten questions. Old aggregate-only receipts refuse |
| Certified fit | Newton finish on every fit; finite objective/gradient and a strong-convexity gap certificate; receipt retained in bundles | Ghost's original T1 input, early-stop rescue, direct Newton and 20 option permutations pass |
| Feature scale | log1p character/token counts in deterministic features | Ghost's custom features remain untouched |
| Packet parity | Preview rejects unknown fields at every depth; entry labels and global findings retained; goal-lens references checked | Engine-produced software fixture round-trips through frontend parser |
| Demo fallback | Preview never installs authored website readings | Existing fallback protections retained |
| Context limits | Explicit 8,192 context setting; conservative preflight and post-call token count checks; missing counts refuse | No silent acceptance of a possibly truncated answer |
| Warm backend | Owned endpoint lease, optional whole-session GPU lease, configurable pinned keep-alive/threads/context; verified unload before release | Local transport controls test reuse, foreign residency, overflow and failed cleanup. Dedicated preview remains CPU-only |
| Health | Refused admission reasons are returned | API integration control verifies stale-pin reason |
| Privacy | Wikipedia makers use Editor aliases with local-only reveal; export strips local names; registry rejects per-person and preview readings | Captured source text/excerpts remain authentic, not rewritten |
| Three entries | Page/person/process derived from basis and shown at panel headings | Entry mismatch rejects |
| Goal lenses | Functional reading, assumed 0.6 root cue, model's own rating; uncovered candidates kept as a second lens | No forced invented second root; coverage is the model's judgment, unvalidated |
| Departures | Repeated unusual phrases route to signatures, single departures to attention | Paragraph proxy disclosed where section metadata is absent; habit versus deliberate style remains untested |
| Common-word comparison | UTF-8 spans with following punctuation/space; incomplete words deferred | Byte-overlap allocation of token loss is approximate, not normalized word probability |
| Payoff | Layer 2 ranked by gain per token of resolving context; novel/shuffled controls retained | Proxy for resolution, not enjoyment |
| Probes | Time pressure, source failure, need substitution and offering absent options | A later acceptance is not treated as proof the option was previously unconsidered |
| Drive honesty | No borrowed theme-to-drive prior; no mapped drive cards in preview; Belonging/category fields and bodily-needs distinction | Personal drive position stays unknown without measurement |
| Global findings | V1/V2 and Ghost R4/N5/N7 with numbers, intervals, source and limitations | Ghost nominated-setting intervals are not selection-adjusted confirmation |
| History | Suppressed boundaries, bounded Retry-After, configurable limit, conservative wikitext matching, per-item oversized-hunk exclusions | No diff or revert inference across missing parents |
| Budget handling | Shed layer 2, second reader, technique regions beyond 30, then governing call after budget misses; keep validated partials | Existing 20-region technique cap is already stricter than the requested cap |

## Deliberate corrections to the sketch

An optimizer's success flag alone cannot override a failed numerical certificate.
The implemented accept rule requires the finite gap bound in every case.

The absent-option probe remains a question. Taking an option when later offered
does not logically prove it was never considered; declining it does not prove it
was previously weighed. No such conclusion is displayed.

The cited word-boundary papers require probability mass at boundaries, not just
observed-token losses. The current API supplies the latter. Shared spans and
trailing separators are implemented, but full boundary marginalization remains
pending a reader API extension and known-probability controls. The UI identifies
the approximation. References: [Pimentel and Meister](https://arxiv.org/abs/2406.14561),
[Oh and Schuler](https://arxiv.org/abs/2406.10851).

## Remaining execution and research dependencies

- Fresh Q8, Q9, Q5, Q1, Q3, Q4 and Q7 batteries must run under the engine's new
  pin. `scripts/engine-question-batteries.py` prepares serial, one-thread CPU
  execution against an explicitly assigned dedicated service. It requires a
  confirmed shared CPU slot and writes fresh receipts/timing files separately.
  It has not run the roughly 1,400 calls. No old Sounding Line receipt earns a
  badge under the new gate. Failed questions stay off; untested previews say so.
- To run it, reserve a Sounding Line CPU slot, start an owned CPU-only service
  through `startFixedQwen` (which applies below-normal priority), then invoke the
  script with `--url`, `--cpu-slot` and a fresh `--out` directory. Close that owned
  service in the caller's `finally`. Pass its receipt directory to the companion
  through `--preview-question-admissions`. Do not use another job's service.
- The updated context guard and goal-cover prompt change cache identity. Earlier
  partial goal caches remain preserved but cannot supply current goal judgments.
  A full refreshed goal tree and fresh per-question timings still need CPU time.
- D30, D33, D39, V5 and related conditional changes require a reviewed handoff,
  not merely a raw result file. No newly landed admission was established here.
  Post-talk battery redesign, correction likelihood work and new research studies
  remain with their scoped research workflows.
- See [performance measurements](PERFORMANCE.md). Publication of the certified-fit
  commit/tag and coordination messages remain a separate owner action.
