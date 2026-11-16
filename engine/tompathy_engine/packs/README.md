# Reader packs

TS2 implements the `bottom-box-1` benchmark contract in packet 1.11. It adds no
admission and changes no live reader. `run(..., enabled=False)` is the default;
missing packs return empty tiers. `about_maker` is deliberately closed.

The canonical vocabulary is `packet/names.py`; `src/core/reader-names.json` is its
generated frontend mirror, checked by tests. A valid pack lives entirely below
one local directory. `registry.load_pack` checks manifest, encoder files, linear
head, held-out error counts, aggregation selection receipt and execution code.
No pickle, remote code or automatic download is accepted. Data and weights stay
under `.local`, outside the extension bundle.

Sentence spans use UTF-16 code units, matching page captures. Unknown experiencers
stay `unclear`. A channel mapping is a theory proposal, distinct from the scored
emotion label. Page shares invert the held-out key-by-reader table using NNLS,
then add `alpha - 1` per label for TP12's symmetric Dirichlet prior. Alpha 1
is flat and adds no shrinkage. Correction includes the
neutral label before conditioning on feeling-carrying sentences. Bootstrap
intervals resample sentences and condition on the fixed error table; they do not
estimate its uncertainty. Below the selected minimum, or with no identified
feeling mass, the runtime emits no share. The runtime does not synthesize stake
arrows or attribution words from a label.

Packs require the actual TP12 selection receipt. No default prior or minimum has
been scientifically selected. Research-only dependencies cannot enter release
packaging. Benchmark scores alone never qualify a pack for the live default.
