"""TP61(e) linear-head controls on the original TP45 dated cohorts and candidate folds."""

import numpy as np
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_worry_repeat import PREP, WEEK, distribution, vector_return
from tompathy_engine.eval.readers.person_halves import (
    correlations,
    ranks,
    resamples,
    summary,
)
from week_need_losses import matching_scores, standard
from word_table_lane import write

PROFILES = "23382a2d79bc6955482e5df50bba2d496065bfb2c229098faa83ebf959081f8d"
ORIGINAL = "80c8df419d5c68ffef56d3fbacc5466d3fdc08c783e57fa3bb21d6c6f818bf8d"
SIZES = (5, 10, 20, 40)
METRICS = ("meanRepeat", "firstOne", "firstTen", "firstOneGain", "firstTenGain")


def likelihood(a, b, held):
    fit = ~held
    r = correlations(a[fit], b[fit], np.ones((1, fit.sum())))[0]
    return matching_scores(a[held], b[held], np.clip(np.nan_to_num(r), 0, 0.95))


def base_tables(a, b, fold):
    a, b = standard(a), standard(b)
    matrices = [likelihood(a, b, fold == f) for f in (0, 1)]
    original = np.empty(len(fold), dtype=int)
    for f, matrix in enumerate(matrices):
        original[fold == f] = ranks(matrix)
    return matrices, original


def forecasts(halves, w, fold, baseline):
    x, y = [v @ w.T for v in halves]
    varied = (x.std(0) > 0) & (y.std(0) > 0)
    if not np.any(varied):
        raise ValueError("All projected directions are constant")
    x, y = standard(x[:, varied]), standard(y[:, varied])
    proposed = np.empty(len(fold), dtype=int)
    for f, base in enumerate(baseline):
        held = fold == f
        proposed[held] = ranks(base + likelihood(x, y, held))
    return x, y, proposed


def rates(x, y, new, old, counts):
    repeat = correlations(x, y, counts)
    p = counts / counts.sum(axis=1, keepdims=True)
    top = np.column_stack([(new <= cut) for cut in (1, 10)]).astype(float)
    base = np.column_stack([(old <= cut) for cut in (1, 10)]).astype(float)
    return np.column_stack([repeat.mean(axis=1), p @ top, p @ (top - base)])


def cohorts():
    folder, vector = vector_return()
    prior = WEEK / "TP45-profiles-a"
    source = read(bound(prior / "receipt.json", PROFILES))
    old = read(bound(WEEK / "TP45-openings-a/receipt.json", ORIGINAL))
    if old["source"] != PROFILES:
        raise ValueError("Original TP45 comparison used different profiles")

    def saved(name):
        return np.load(bound(folder / name, vector["files"][name]), allow_pickle=False)

    with saved("author-index.npz") as f:
        members = {key: i for i, key in enumerate(f["authors"].astype(str))}
        counts = {k: [f[f"k{k}-{h}"] for h in (0, 1)] for k in SIZES}
    for k in SIZES:
        name = f"deep-date-{k}.npz"
        with np.load(
            bound(prior / name, source["profileFiles"][name]), allow_pickle=False
        ) as f:
            ix = np.asarray([members[key] for key in f["owners"]])
            fold = f["fold"]
            if len(set(ix)) != len(ix) or any(np.any(v[ix] != k) for v in counts[k]):
                raise ValueError("Dated profile author or half count mismatch")
            baseline, rank = base_tables(f["left"][:, :358], f["right"][:, :358], fold)
        for cut, key in ((1, "firstOne"), (10, "firstTen")):
            expected = old["tables"][f"deep-date-{k}"]["tagsRaw"][key]["baseline"][
                "value"
            ]
            if abs(np.mean(rank <= cut) - expected) > 1e-12:
                raise ValueError("Original TP45 baseline ranks disagree")
        halves = []
        for h in (0, 1):
            with saved(f"mean-k{k}-{h}.npz") as f:
                halves.append(f["x"][ix])
        yield k, (halves, fold, baseline, rank)


def prepare(out, check):
    with np.load(
        bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD),
        allow_pickle=False,
    ) as f:
        w = f["weights"].astype(float)
    data = dict(cohorts())
    sizes = {}
    for k, (halves, fold, baseline, old) in data.items():
        check()
        x, y, new = forecasts(halves, w, fold, baseline)
        if x.shape[1] != 19:
            raise ValueError("A trained direction is constant on this dated cohort")
        pt = rates(x, y, new, old, np.ones((1, len(fold))))[0]
        samples = []
        for batch in np.array_split(resamples(len(fold)), 40):
            check()
            samples.append(rates(x, y, new, old, batch))
        draws = np.concatenate(samples)
        sizes[str(k)] = {
            "authors": len(fold),
            "foldSizes": np.bincount(fold).tolist(),
            "baseline": {
                key: float(np.mean(old <= cut))
                for cut, key in ((1, "firstOne"), (10, "firstTen"))
            },
            "trained": {
                name: summary(pt[j], draws[:, j]) for j, name in enumerate(METRICS)
            },
            "controls": {},
        }
    write(out / "trained.json", sizes)
    files = {}
    for family in ("iso", "rot"):
        rows = []
        for i in range(1000):
            check()
            projected = heads(w, "TP61", family, i)
            stats = []
            for halves, fold, baseline, old in data.values():
                x, y, new = forecasts(halves, projected, fold, baseline)
                stats.append(rates(x, y, new, old, np.ones((1, len(fold))))[0])
            rows.append(stats)
            if (i + 1) % 20 == 0:
                shard = out / f"{family}-{i - 19:04d}.npy"
                with shard.open("xb") as f:
                    np.save(f, rows[-20:], allow_pickle=False)
                files[shard.name] = pin(shard)
                write(
                    out / "progress.json",
                    {"family": family, "sets": i + 1, "sizes": list(SIZES)},
                )
        arr = np.asarray(rows)
        for j, k in enumerate(SIZES):
            cell = sizes[str(k)]
            cell["controls"][family] = {
                name: distribution(arr[:, j, h], cell["trained"][name]["value"])
                for h, name in enumerate(METRICS)
            }
    result = {
        "vectorReceipt": PREP,
        "headPin": HEAD,
        "TP45profiles": PROFILES,
        "TP45receipt": ORIGINAL,
        "draws": 2000,
        "setsPerFamily": 1000,
        "sizes": sizes,
    }
    write(out / "shards.json", files)
    write(out / "table.json", result)
    return result
