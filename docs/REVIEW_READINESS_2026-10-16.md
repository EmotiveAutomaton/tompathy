# October 16 review readiness

Prepared October 15 for the **05:00 Pacific, October 16** review. These are local
changes on `codex/0.3-engine`, not a published release or a new research admission.
The existing layout, colors, artwork and navigation remain intact.

The later October 16 driver adds a separately labeled research preview and
explicit GitHub file history. For that implementation and its measured limits,
use [driver readiness](DRIVER_IMPLEMENTATION.md) and the updated
[practice guide](LIVE_PRACTICE.md). The morning checklist below records the
earlier observed-history milestone.

## What is functional

| Capability | Current behavior and limits |
| --- | --- |
| Follow pages | A saved opt-in captures and analyzes new active webpages, new tabs and visible text changes while the panel is open. Navigation cancels stale work. It needs the configured companion and Chrome site access. It does not monitor pages with the panel closed. |
| Light context | A separate saved opt-in records the byline and automatically reads explicit creator sources where access is already granted. New origins need a user-triggered refresh/grant. One invalid link or missing grant no longer blocks other sources. |
| GitHub | Real public profile, explicitly linked repository/file, and up to three recent revisions; bounded to eight API requests. A native-panel check retrieved this repository's actual README history. Commit attribution does not establish authorship of the current webpage. This is context retrieval, not complete writing-session reconstruction. |
| Context use | Retrieved sources initially remain unselected. Selected sources enter the next exact-scope engine request; they do not silently modify an accepted account. Same-revision recapture retains context; a new page drops the previous creator's context. |
| Hierarchy | Solitary, 64-level, wide and shared-parent structures remain navigable. More than 1,800 nodes use the existing list fallback, now without unnecessary SVG construction. Duplicate IDs, missing parents and cycles fail explicitly; extreme dimensions/shares stay finite. |
| Value curves | Pointer and keyboard inspection show supplied sample values and sleeve bounds. Left/right, Home and End select samples. Interpolation cannot overshoot adjacent samples. Dates, observation labels, horizons and supplied cost are visible. |
| Current estimates | Packet 1.8 carries the fitted point, interval bounds, reference, units/method and basis. Hover and click cards render the same estimate. Missing uncertainty stays unknown with no sleeve. Observed evidence remains expandable. |
| Other controls | Reading import/export, evidence navigation, source selection and the population display are implemented. Creator-like models, word-level analysis, broad model-driven search and value search remain previews/future work. Agent search is a bounded extra link hop, not an autonomous research model. |

The small usability changes are clearer partial-access coverage, retained context
on recapture, no duplicate “Undated” label, a pointer to Creator when Current work
has no page-specific values, more precise small support numbers, and correct
recovery instructions for an older running practice engine.

## What data is arriving

Ordinary webpages supply actual captured passages, anchors and page-provided
attribution. Wikipedia practice additionally fetches bounded public revisions,
contributor labels and before/after correction evidence into the ledger. Linked
creator pages and GitHub supply source-backed context and explicit source dates.
These are observed records; final prose alone does not supply a history of choices.

The new interval display is exercised with a **real numerical fit on constructed
choices**. Its point and conditional 95% bounds come from that fit. The recorded
quantity is a coefficient difference from the pooled population, not a measured
lifetime set point. The separate authored demo supplies invented trajectories
for interaction practice. Neither fixture is evidence about a real person's values.

Production personal values, inferred goals, attention and drive mappings still
require matching scoped admissions. The display contract is ready to receive
their structured output once those gates pass. No missing estimate is filled
with a demo score. The ledger schema and existing research capsules are unchanged.

## Review in a few minutes

1. Run **Practice ToMpathy.cmd**. If it reports an older running engine, close only
   the separate ToMpathy review Chrome windows and run it again. A rebuild does
   not update an already running Python process. Normal Chrome can stay open.
2. Connect the engine if requested, enable Follow pages, and open Sneckdown from
   the practice page. Open the native panel once. Navigate to Desire path and
   inspect recorded events and source evidence without another toolbar click.
3. Enable Light context and Use GitHub when possible. On a page with explicit
   creator/source links, inspect **View context and timeline → Collection coverage**.
   Missing bylines, denied sources and rate limits should be explained, not
   treated as successfully collected material.
4. To inspect fitted values immediately, use **Reader menu → Import** and select
   `evidence/engine-interval-reading.html` from this checkout. It is a portable,
   constructed reading generated from the Python fixture. Choose **Creator**,
   then “Preference hypothesis: shorter text.” Inspect its point, interval,
   reference and Observed evidence. Switch contributor to compare the supplied fit.
5. Open the bundled fictional example to inspect the trajectory interactions.
   Click a value and move across the curve; focus the chart and try left/right,
   Home and End. Return to a live page for observed-history practice.

The imported reading is a detached snapshot. It is deliberately separate from
the live page. First-use Chrome permission confirmation remains an owner action;
native test profiles grant their own permissions through Chrome's settings API.

## Verification and evidence

- 38 core tests passed, including seeded unusual graph shapes, invalid structures,
  packet 1.8 validation, unknown intervals and partial-access context. A targeted
  rerun also passed after hardening malformed percent-encoded GitHub links.
- 22 targeted Python tests passed for model bundles, packets, engine extensions
  and the pipeline. Nine generated/example packets passed authoritative TypeScript
  validation. Python lint/format and TypeScript/build passed.
- Eight affected browser scenarios passed across the initial run and targeted
  corrections: context creators/history, existing graph navigation, existing value
  layouts, unusual graph shapes, trajectory interaction and fitted intervals.
- Native Chrome 155.0.8059.79 passed ten automatic navigation/recovery checks
  against the real companion and three context checks with live public GitHub.
  Native context checks reported zero panel errors. Test-owned browsers closed.

Browser verification found and fixed the current-estimate click view. Initial
new tests also exposed two fixture/setup mistakes (demo regeneration and the
Creator perspective). Cold dev-server loads measured 21–24 seconds; the combined
multi-page screenshot tests now allow 60 seconds. GitHub progress capture holds
its constructed final response until the screenshot, so the five-second success
indicator cannot disappear before its assertion. Product deadlines and assertions
were not loosened. This is a targeted stability pass, not a full release-suite run.

Local evidence is ignored by Git: `evidence/follow-validation.json`,
`evidence/context-stability-validation.json`, `evidence/stability-native-context.png`,
`evidence/stability-shared-graph.png`, `evidence/stability-trajectory.png`,
`evidence/stability-engine-interval.png`, and `.local/stability-intervals-tests.xml`.
Screenshots were visually inspected at narrow panel width. Exact build/pin details
are retained in `.local/review-readiness-receipt.json`; older native receipts name
the builds they actually tested and do not claim to test later copy changes.

## Bounded continuation and suggestions

Two local follow-ups are scheduled for **22:00 October 15** and **04:00 October 16
Pacific**, ending work by **05:00**. At each checkpoint, inspect new concrete
dependency returns, fix any reproducible ToMpathy integration defect within this
scope, run only affected serial checks, and update this record. If no new actionable
evidence has arrived, leave the stable build alone. Scheduling is verified;
execution/delivery will need its own receipt. No automatic publication is included.

Sounding Line's October 15 `DEPENDENCY_RETURN.md` acknowledges the earlier
[adapter handoff](SOUNDING_LINE_STAGE15_RETURN_2026-10-15.md). Its prepared profile
comparison awaits its own review of the matching Ghost result. These are separate
research responsibilities; ToMpathy does not move their pins or decide admissions.

The most useful next improvements are a source-specific response to any returned
adapter discrepancy, then a review of real-world byline/link coverage and a clear
distinction between relative model position and confidence in the user-facing
wording. Broader crawling, GitHub history ingestion beyond context, and measured
preference trajectories need explicit evidence contracts and evaluation; they
should not be implied by a polished chart. No visual redesign is needed for these
next steps.
