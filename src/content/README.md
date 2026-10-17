# Section essays

`essays-source.txt` is the working manuscript, with the owner's October 17
walkthrough edits. The complete original, including superseded bracketed image
directions, is preserved byte-for-byte at
`archive/essays-source-2026-10-16.txt`. Original SHA-256:
`7aae80b00f5ce57ea3e84abf1d010ff6e2c0e88ac2d36884c4f2c3e96e3503d3`.

The [walkthrough checklist](../../docs/TOOLTIP_WALKTHROUGH_2026-10-17.md)
records every requested change. Edit the working manuscript for prose; keep its
section headings and local numbered-reference keys. `*word*` renders in italics.
`essay-figures.ts` holds the owner's verbatim captions and image arrangements.
Figures use unique prose anchors and a before/after position. An unmatched or
ambiguous anchor fails explicitly, so paragraph edits cannot silently move art.
There is no newly generated explanatory prose or caption text.

`essays.ts` resolves the supplied DOI, arXiv and HTTPS destinations. Display
numbers run across all three essays, including captions, in first-citation order;
repeated destinations reuse one number. Options → Bibliography opens the full
cited list in that order. Unused original reference entries remain in the
manuscript for editing but are not displayed. Citations to the owner's repositories
have been removed from explanatory prose; the four explicit closing invitations
remain. These are direct source links, not a comprehensive source-validity audit.

The newly requested arithmetic source is Kantamneni and Tegmark (2025),
[Language Models Use Trigonometry to Do Addition](https://arxiv.org/abs/2502.00873).
It supplies the mechanistic example; it does not establish a general impossibility
of reverse engineering. Existing RLHF references support the training discussion.
The doctor's caption links to the existing Budzyń et al. (2025)
[colonoscopy study](https://wrap.warwick.ac.uk/id/eprint/191005/): the reported
adenoma detection rate fell from 28.4% to 22.4% (about 21% relative), a specific
observational measure rather than general clinical accuracy. The owner requested
the original caption and later dictated “skill decay should account for less than
1.5%”; this remains uncited by explicit instruction. No sufficiently comparable source was established to
replace that number.

Images are packaged locally without pixel edits. `../assets/essays/provenance.json`
records original filenames and hashes. The owner-authorized cleanup moved the
complete curator folder, including its editor backup, to
`../../docs/archive/essay-curation/2026-10-17/`; all 27 archived files were
hash-verified. Current displayed files live in `../assets/essays/`.
Grey borders follow the owner's generated-image attribution, including AI Slop,
The Hatred of Inefficiency and And We Need Everyone's Help. Bot Farms and the other
human imagery use black borders, including Pixar Cheaters. Compact frames crop
without distortion, while full-screen image viewers show the originals.
The first image, Schadenfreude, Inside Out 2 and the final image remain uncropped;
the first and final images are doubled. Captions extend to 1.5 times a single
image's width and across paired images, constrained by the viewport.
The channel collage reuses `DriveBrain`, with PANIC/GRIEF labelled explicitly;
the static preference illustration reuses the existing authored demo trace.
Neither graphic introduces inferred measurements.

Question marks sit after their labels and show a small invitation after 1.5 seconds.
Clicking opens the shared essay surface. The extension uses an isolated iframe
over the connected webpage, with the same local dialog as a fallback. The essay
and its prose expand with the viewport while retaining a 24-pixel outside gutter.
X, Escape and outside clicks close it; dragging out does not. Frame messages check
identity, origin and nonce. Page capture excludes the overlay.

Click any image for a full-viewport black lightbox; one more click closes it.
Escape, keyboard activation and focus restoration are supported. Small links
connect the three essays. The second-pass source and figure metadata are archived;
the walkthrough document includes a separate impact-ranked reader review with
no replacement prose. Superscript citations are 20% smaller and 60% opaque.

The final owner-directed arrangement includes fear order 1/4/3/2, revised captions
and the replacement closing image (generated attribution reconfirmed). The
self-contained [website handoff](../../docs/WEBSITE_ESSAY_HANDOFF_GUIDE.md)
contains exact content, assets, layout rules, bibliography and a working preview.
Regenerate with `node scripts/export-essay-handoff.mjs` after authorized edits.

Verification: `npm run build`, `npx playwright test tests/essays.spec.ts`, and
`node scripts/essay-validation.mjs`. Native checks use one disposable Chrome
profile closed in `finally`. October 17 verification additionally exercised the
three browser checks against the packaged build because the local Vite server left
image requests pending. Screenshots and receipts are in ignored `evidence/`.
