# Final website changes — 17 October 2026

Apply this delta to the three ToMpathy help essays from the previous handoff.
These are separate from the long `/art/` essay. Preserve the author's wording,
captions, image order and image bytes. The notes below are implementation
instructions, not text to insert into the essays.

1. In the opening essay, render `here [abrahamhaskins.org/art]` as the single
   linked word [here](https://abrahamhaskins.org/art/). Hide the bracketed URL.
2. Remove the citation following “Art is physical evidence of compressed
   decision-making.” Leave the sentence itself intact. Do not substitute Dennett:
   the exact attribution was not established, and the owner chose removal.
3. Keep only the three closing project citations: ToMpathy, SoundingLine and
   Ghost-Scale-Sim, linking directly to their GitHub repositories. Remove the
   additional citation after “the theory documentation in SoundingLine.”
   Do not cite the owner's Zenodo paper or repository theory as outside evidence.
4. Remove the Schwabe/Wolf citation after “expert transition map” in Core values
   (old local key 45). Its stress-and-habit result does not support the adjoining
   claim about expanded creative possibilities. Preserve the sentence.
5. Point Kautz and Allen's *Generalized Plan Recognition* to the official
   [AAAI PDF](https://cdn.aaai.org/AAAI/1986/AAAI86-006.pdf).
6. Regenerate shared display numbering from the delivered `content.json`:
   **97 unique cited destinations**, across paragraphs and captions. Manuscript
   numbers are local keys, not display numbers. Keep small linked superscripts
   and the separate Bibliography view; do not append bibliographies to essays.

The rebuilt handoff still contains 46 paragraphs, 27 raster images, 19 captions
and two diagrams. Use the [complete reconstruction guide](WEBSITE_ESSAY_HANDOFF_GUIDE.md)
and regenerate with `node scripts/export-essay-handoff.mjs`. Deliver the resulting
`website-essay-handoff.zip`; its `WEBSITE_CHANGES.md` is this delta and its manifest
verifies the content and asset bytes. The [final reference audit](REFERENCE_AUDIT_FINAL_2026-10-17.md)
records unresolved claim scope separately; it is not replacement essay copy.

If the website mirrors the app's drive cards, all seven use the same setpoint,
uncertainty-sleeve and numbered-vector format as constructed values. Supplied
measurements retain their existing rendering. Missing measurements show a clearly
labelled instructional diagram; confidence remains unspecified. This does not
alter the essay's channel collage or introduce measured drive data.

## Live-site observations

A text/accessibility extraction of the homepage and `/art/` found the long art
essay, but did not establish that the three help essays are deployed or linked
from the homepage. Confirm their intended entry point. Several art images expose
the generic label “Figure”; review their alternative text using existing authored
descriptions. The homepage extraction repeats the Alaska description and the
skills sequence. These may be intentional animation/hover duplicates: check
whether decorative copies should be hidden from assistive technology before
changing visible layout. A rendered website inspection was unavailable because
the in-app browser connection failed; these are checks to make, not confirmed
visual defects. No website deployment was performed.
