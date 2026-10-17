# Evidence required for future owner-collected research captures

This is the collection boundary requested in the Sounding Line Stage 15 handoff.
It describes required evidence for a future explicitly authorized collector; it
does not enable collection, supply consent, or declare a new supported importer.
The existing browser capture remains final-text evidence at capture time, with
no inferred editing history or author actions.

Before a research import, its source bundle must retain:

- Consent/usage permission: source of permission, permitted purposes, collection
  scope, date and any applicable retention/withdrawal terms. Public visibility,
  a software license, or opening ToMpathy is not a participant consent record.
- Identity: pseudonymous maker IDs scoped to that source, with the identity basis.
  No joins from matching display names or across datasets.
- Choice evidence: the exact ordered offered options, their origin and immutable
  text hashes; the observed selection or edit, including exact before/after text.
  Missing selections, unseen review and inferred endorsement remain unknown.
- Chronology: independently observed opening and resolution times with explicit
  UTC offsets, source clock basis and provenance. Preserve raw timestamps and any
  documented timezone transformation. Do not substitute capture/ingestion time,
  session creation time, survey generation time or a batch name for decision time.
- Revisions: immutable text content and hashes, parent references, and exact
  capture revision/UTF-16 anchors where browser passages are referenced.
- Stated goals: exact separately stated wording, maker, scope, time and source
  witness. A later interpretation, topic label or text title is not an earlier
  stated goal.
- Missingness and exclusions: original source IDs, source-byte/manifest hashes,
  mapping codebook, and the reason each record was retained or excluded. Preserve
  raw evidence privately; do not silently drop a problematic source row.

Existing ledger types (`Maker`, `Revision`, `Decision`, `Correction`, `StatedGoal`,
`Provenance`) represent the observed records once a source-specific adapter has
been validated. Consent and raw capture manifests stay in the source bundle;
their presence and meaning must be checked before any future collector/importer
is admitted. The current native-panel importer supports its named published
datasets, not arbitrary owner activity disguised as one of those datasets.

Sounding Line owns real-data eligibility and exposed-holdout policy. Ghost Scale
owns the relevant known-world witness. Neither UI functionality nor software
regression fixtures supply those scientific permissions or validations.
