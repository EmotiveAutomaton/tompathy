# ToMpathy illustrated essays — complete website reconstruction handoff

Owner-directed arrangement, 17 October 2026. This handoff describes the three
short help essays, not the separate, much longer `/art/` essay. Treat the supplied
prose and captions as frozen authored material. Do not improve, paraphrase,
summarize, spell-correct, insert transitions, or invent captions. Scientific
review notes are editorial metadata, not replacement copy or text to append.

## Deliverables and source of truth

Give the website implementer this entire directory. `README.md` contains the exact
reading sequence and linkified superscripts. `content.json` contains exact
paragraphs, reference keys, shared numbers and ordered figure records, so there
is no need to infer placement from Markdown. `assets/` contains all 27 raster
images at their original bytes. `source/` preserves the implementation and
diagram source. `manifest.json` binds every delivered file to its SHA-256.

Open `preview.html` in a browser for the working reference: all three essays,
both diagrams, separate bibliography, keyboard behavior and image lightboxes.
It is a standalone local reference, needs no model service, and makes no remote
requests until a reader follows a citation. It uses the same React essay
components as ToMpathy, rather than a second handwritten interpretation.

The three section identifiers, in order, are `goals`, `process`, `values`.
Display labels are “Current attention”, “Expertise (Previous attention)” and
“Core values”. The longer title casing inside each essay is preserved in JSON.
The source text's numbered references are **local keys**, not display numbers.
Resolve those keys through the owning section before displaying a citation.

## Entry points and overlay behavior

Place a small circled question mark **after** each label (the final owner choice).
Hover or keyboard focus waits 1.5 seconds, then shows the short invitation from
`SectionTitle.tsx`; do not revert to the earlier long first-paragraph tooltip.
Only one invitation is open at a time. Moving into it retains it; Escape,
selection or window resize dismisses it. Click or keyboard activation opens the
corresponding full essay. Keep a separate Bibliography entry in the menu.

Use a modal essay panel with the underlying website visible around it: 24-pixel
outside gutters (the reference subtracts 48 pixels from both viewport dimensions).
The essay scrolls internally; preserve the underlying page's position. The header stays
visible with title and an X close button. Close on X, Escape or a genuine outside
click; a drag that starts inside and ends outside must not dismiss the essay.
Restore focus to the triggering control. Trap modal keyboard focus. Switching
essays resets the essay's scroll position. Preserve the source page's position.

Current attention ends with the link to the next essay; Expertise links back via
“(first essay here)” and forward to Core values; Core values has the same link to
the first essay. Navigation labels and positions are in `Essay.tsx`. Avoid
appending inline bibliographies to the essays.

## Typography, layout and images

Copy `source/src/essay.css` as the authoritative layout. Prose uses Georgia / Times
New Roman / serif, 18px with 1.8 line height, 48px side padding on wide screens and
the stylesheet's responsive reductions. Paragraph bottom margin is 1.35em. The
prose grows with the panel rather than remaining a tiny centered column. Captions
use Segoe UI / sans-serif, 13px / 1.6, centered with balanced wrapping and muted
color. Header is 15px / 1.4 sans-serif. Retain italics marked by single asterisks.

Ordinary single images are up to 320px wide; the first and closing images are
640px. A pair spans up to 656px with a 16px gap. Four-image groups span 328px with
8px gaps. Images/captions shrink to fit the viewport. Single captions have a
480px limit, pairs 656px, four-image captions 492px and large-image captions
960px. Keep captions below images, without side-floating text.

Use 4px solid image borders: generated art `#999`, human-sourced art `#111`.
This is attribution, not a quality judgment. There is no Pixar Cheaters exception:
it has a black border. The replacement closing image is AI-generated and grey.
Default display crops use 4:3 with `object-fit:cover`; fear portraits use 4:5.
The following images retain their complete natural aspect ratios: Art is
compressed intent, Inside out 2, Pixar schadenfreude, and And we need everyone's
help. Never resample or crop the stored image files; crops are presentation only.

The four fear images read row-major as **1, 4, 3, 2**, with their corresponding
names. All other image order is exactly the ordered content below. The final
image intentionally has no caption. There are 19 authored captions and two
reused diagrams; do not manufacture missing captions or source prose.

Click any image or diagram for a full-viewport black lightbox. Render the complete
original with `object-fit:contain`, no crop, distortion or opaque UI over the art.
One additional click anywhere closes it. Escape, Enter and Space close it too.
Return focus to the originating image and retain the underlying essay position.
For the diagrams reuse the supplied SVG geometry/components: seven channel
schematics and the illustrative preference trace with uncertainty sleeve. These
are teaching illustrations, not real fitted data. Label PANIC/GRIEF explicitly
in the channel diagram, even though the main app calls that channel Belonging.

## Citations and provenance

Every citation is a direct external link, rendered as a superscript. Repeated
destinations share one display number across all three essays and captions.
Assign numbers by first appearance in the actual reading order, including figures
before or after a paragraph. Adjacent citations share small comma separators.
Use 0.44em bold sans-serif, opacity 0.6, no surrounding brackets, and no gap before
the superscript. Each link has the reference title as its accessible label/title,
opens a new tab and uses `rel="noopener noreferrer"`. Keep keyboard focus visible.

The separate Bibliography shows only cited destinations in shared numerical
order, linking every full reference. Preserve unused manuscript entries only in
source archives. Link validity and claim support are distinct; the accompanying
citation audit records unresolved scope issues without changing the author's
argument. Do not turn an uncited personal claim into a fabricated study result.

Image attribution and original filenames/hashes are in the copied provenance
manifest and NOTICES. Copying the assets does not grant a new license to source
art. No new AI-generated prose or captions should enter the three essays. The
instructions in this guide are implementation documentation, not essay text.

## Acceptance checks for the website

1. Compare every displayed paragraph and caption to `content.json` after removing
   only citation markup; do not normalize away wording or punctuation changes.
2. Confirm 46 paragraphs across the essays (10 / 14 / 22), 27 raster images,
   2 diagrams and 19 captions. Verify every asset hash against the manifest.
3. Check the first image and Schadenfreude at their natural aspect ratios, fear
   order 1/4/3/2, black Cheaters border and grey replacement closing border.
4. Exercise all three entry points, next/back links, bibliography, outside-click
   dismissal, X, Escape, keyboard image opening and focus/scroll restoration.
5. Check narrow mobile and wide desktop layouts: no horizontal overflow, hidden
   captions, clipped natural-ratio images or modal controls covering text.
6. Confirm every superscript destination and number matches the bibliography;
   verify no bracketed image directions appear in prose.
7. Preserve the site's existing reading/capture integration and accessibility.
   This handoff contains no authorization to publish or deploy the website.

Regenerate from the ToMpathy repository with `node scripts/export-essay-handoff.mjs`
after an explicit source edit. Do not edit generated copies and expect them to
flow back to the manuscript.
