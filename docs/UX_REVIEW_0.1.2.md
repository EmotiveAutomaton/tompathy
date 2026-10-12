# UX review — Chrome 0.1.2 / 0.2 development 2

Reviewed 11 October 2026, Pacific time. This is an interaction and implementation review with automated browser checks and visual inspection, not a participant usability study or a scientific evaluation of inference.

The three-box layout now supports the intended reading loop: point at the text, hold a sentence or branch, inspect alternatives, release. The main problems found in this pass involved state transitions rather than the overall layout. The next substantial investment should be making this behavior hold for realistic backend results with long labels, incomplete paths and changing evidence.

## Requested refinements

| Change | Result |
| --- | --- |
| Dot arc | Shifted right and deepened within each root lobe. Positions are chosen with clearance for the entire circle, rather than its center alone. The example's circles fit their own brick paths at three viewport heights. |
| Uncertain ordering | Every squiggle's tooltip and accessible name is exactly “Order uncertain”. The richer supplied explanation remains in the data. |
| Lock reminder | Four distinct blocked target transitions within 1.2 seconds emphasize both locks twice. Repeated movement over the same target and very short jitter are ignored. A six-second cooldown prevents nagging. The heuristic is local and ephemeral; it does not infer emotion or collect telemetry. |
| Reduced motion | The reminder becomes one steady, temporary edge emphasis. It does not flash or scale. Unlocking, clearing the page or replacing a selection cancels it. |
| Lock position | The reel lock overlaps its top-left corner and follows the first reel upward during expansion. It remains clickable in either state. The document lock is constrained to the viewport. |
| Expanded candidates | Hovering any candidate resolves from the held branch. Each leaf highlights only its own path, independent of the previously inspected sibling. |
| Language | The middle box is “Previous attention (expertise and habit)”. The empty attention cue is `<- hover`. The interface, title, Options, tabs, context reports and demo explanations use creator. |

The cue's previous color/opacity combination was already too faint for ordinary small text. The new cue uses the main text color at 70% opacity, with measured contrast at least 4.5:1 in Light, Dark and System-dark modes. Opacity alone is not a readability threshold: foreground and background matter. This follows [W3C's small-text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). The lock reminder also honors the user's [reduced-motion preference](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

## Defects found and corrected

**A wider heading could cover a top dot.** The initial Linux CI run exposed a real pointer obstruction from different font metrics. The graph now measures the heading and uses only the extra clearance needed to keep those dots reachable; no inset is added when they already clear it. A regression exercises a wider monospace heading at 320/360 pixels and 200% zoom. The bottom of the diagram and reel position stay fixed.

**Repeated graph work during pointing.** The selected creator’s node array was recreated on every pointer update, invalidating the layout cache. It now remains stable until the accepted packet, creator or analysis availability changes.

**Sibling hover depended on the previous sibling.** After inspecting one option, the next lookup searched within that option's neighborhood. A sibling was sometimes absent, causing a fallback to the whole locked group. The lookup now uses the stable locked branch. Regression checks move through all four “Show the iteration” options in both directions and revisit them out of order.

**Keyboard navigation selected too early.** Arrow keys on an expanded candidate bubbled to the reel's selection handler. They now move focus between candidates; Enter or Space makes the selection. The held node remains held during inspection. Only the selected visual instance reports itself pressed to assistive technology.

**System dark had mismatched colors.** The operating-system preference could enable light text while the reader retained light surfaces. System mode now applies the reader's dark palette as well as the document palette. Explicit Light still overrides a dark system setting.

**Pending-context readings could not round-trip.** Selecting new context invalidates the active account until a matching revision arrives. Previously, Export saved that mismatch and Import rejected it. Export now retains the previous account in reading history, saves the requested context selection and leaves the active account empty. Changed text anchors are still rejected. No outdated estimate becomes current during the round trip.

**Removing the last selected context source left the wrong scope.** It now restores artifact-only scope. An existing matching artifact-only account becomes usable again.

**Collection could not be cancelled from the timeline.** There is now a Cancel collection control while work is running. Completed byline information remains available; responses arriving after cancellation are ignored. The empty undated area no longer tells readers to enable a feature that may already be running.

**Small interaction gaps.** Creator/Global tabs support arrow keys and Home/End. Space on an example passage prevents page scrolling while locking it. The document's lock no longer extends below the viewport when its sentence ends at the bottom edge. A border-box measurement keeps the expanded reel's lock aligned with the visible corner.

## Review coverage

The final build is checked through the project's core tests, browser tests and ordinary Google Chrome native-panel workflow. Current counts and package identity are in [STATUS](../STATUS.md); generated receipts remain in ignored `evidence/` and the CI artifacts.

The review exercises:

- Idle, hovered, held, released, expanded, ambiguous and ended-path states; transitions between neighboring options; wheel navigation; small gaps and exit boundaries; both unlock buttons, Escape and double-click.
- Independent attention updates, sub-sentence input, persistent shared cloud phrases, compact headings, stable values, tooltip switching, evidence dialogs and the inert search preview.
- Three viewport heights for circle clearance, narrow panels, short windows, 200% zoom, eight hierarchy levels, nine values, Light/Dark/System-dark and reduced motion.
- Keyboard candidate inspection, tab navigation, dialog focus and dismissal, context cancellation, unavailable sources, bounded discovery, source coverage and cache behavior.
- Saved page import/export, pending context, revisions, malformed inputs, changed anchors, source identity and compatibility with earlier packet versions.
- Real native Chrome installation and panel placement, page/panel reminders in both directions, toolbar capture with the shipped permissions, switching tabs, restoring an imported revision, and relaunching after a full browser restart.

Screenshots of the quiet panel, expanded reels, Options, context timeline and native panel are visually inspected. Successful DOM checks alone are not treated as visual evidence. The controlled long-page check measures capture and content-script response; it is not an end-to-end backend latency benchmark. No live Sounding Line service, model download or paid service was used.

## Recommended next improvements

1. **Exercise a representative backend corpus before further decoration.** Include missing attention, long phrases, several creators, shallow and deep branches, shared nodes, sparse evidence, delayed results and revisions arriving out of order. These would expose the remaining constraints more effectively than adding more detail to the fictional example. The provider boundary exists, but live inference is not connected.

2. **Make density respond to available space.** The hierarchy already falls back to a list for sufficiently large graphs. Its thresholds are primarily graph counts. A future pass should also consider actual text length, brick height and panel width, so a medium-sized but crowded graph switches before it becomes difficult to target. Do not compress labels further merely to fit more columns. Candidate buttons expose descriptions, but lengthy reel labels still deserve a dedicated full-label inspection treatment.

3. **Make historical accounts easier to reach when needed.** They are retained, including during pending-context export, but the inspection interface currently lives in Development tools. Once ordinary readers can request new analyses, expose earlier accounts from the awaiting-analysis state or Help, without adding permanent clutter to the three boxes.

4. **Tune the reminder with actual use.** Four transitions and a six-second cooldown are reasonable initial defaults, not validated measurements of frustration. Keep this local. If ordinary exploration triggers it too often, raise the transition threshold or require a reversal between targets. The behavior should help explain a lock, never change the lock automatically.

5. **Optimize after measuring realistic input.** Cache the region-to-sentence/hierarchy lookup per accepted packet, and coalesce pointer updates to animation frames if larger real inputs reveal delays. Preserve within-sentence attention changes. Bound the rendered candidate lists before adding workers or another layout dependency. The new reminder itself stores only a few timestamps and uses two short browser animations.

6. **Complete a dedicated accessibility pass before public 0.2.** This pass checks contrast for the new cue, keyboard behavior, focus, reduced motion and zoom. It does not establish full WCAG conformance or substitute for screen-reader testing. Tiny graph targets, long explanations and traversing a large graph by keyboard remain the important cases.

The context timeline can also repeat the same dated statement from several source pages. A later refinement could group matching entries with expandable source lists; it should not silently treat identical wording as independent corroboration or merge distinct events merely because their labels match.

No new design decision blocks the next development iteration. Global, value search, word-level analysis and creator-like models remain clearly marked future or preview features. “Previous attention” is the chosen label, while Help continues to distinguish supplied goal structure from verified historical order. Scientific wording should receive its own pass when the model's claims are settled.

## Compatibility and review loop

Internal context/page-discovery functions use creator terminology. Existing serialized fields `authors`, `authorLabel`, `author` and `explicit-author-link`, plus standard webpage author metadata, deliberately retain their names. This avoids breaking existing readings and backend exports. Imported source quotations are preserved verbatim. See the [input contract](INPUT_CONTRACT.md).

Use **Review ToMpathy.cmd** or `npm run review`, then the guided example. The launcher keeps a separate persistent ordinary-Chrome profile and reloads changed builds. This iteration belongs to `codex/0.2-development`; main and the published 0.1 beta remain separate. There is no new public GitHub release or Chrome Web Store submission in this pass.
