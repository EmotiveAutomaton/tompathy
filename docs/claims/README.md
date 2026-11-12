# Pinned claim snapshot

`SNAPSHOT.json` is the single receiving snapshot bundled into the app and read
at run time by the engine. It is evidence metadata, not an admission registry.
Missing files, missing reader identity, non-passing controls, changed wording,
or superseded rows remove a field badge. Saved readings resolve against this
snapshot again at display time. Changing a JSON snapshot does not require model
calls or imply that a cached model result was re-evaluated.

The two interim Sounding Line rows come from the byte-verified EV4 table and
retain its row IDs, public wording, source hashes and scope. Their reader field
is deliberately null: the export identity handoff has not arrived. Do not fill
it from the locally installed reader. A receiving update must verify the supplied
model, revision, manifest hash, runtime/precision and departure definition.

`GHOST_CLAIMS_20261025.json` preserves the current local companion ledger bytes.
It is not in Ghost's inspected HEAD, so the snapshot records a file hash and
base commit, with `sourceCommit: null`. Do not present that base commit as the
ledger's publication commit. R4/N5/N7 use its exact permitted wording. N16's
corrected stress wording supersedes its earlier row; the pilot remains
descriptive, not powered confirmation. These rows do not license live badges.

Legacy Sounding Line V1/V2 and EV3 have no applicable Stage 15 ledger rows yet.
Their aggregate figures retain pinned source paths and “No ledger row” wording.
The global findings' status enum is unchanged.

`EV4_DELIVERY_20261023.json` is the original delivery receipt. All twelve receiving
files were checked against it. The source package is preserved unchanged and
marked `-text` in `.gitattributes` to protect its hashes on Windows.
