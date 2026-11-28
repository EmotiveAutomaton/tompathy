"""TP73 two-reader agreement and date-half repeat on the same complete blog authors."""

import numpy as np
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import HEAD, bound, pin, read
from rapid_nulls import heads
from rapid_worry_repeat import PREP, WEEK, distribution, repeats
from tompathy_engine.eval.readers.person_halves import correlations, resamples, summary
from word_table_lane import core, write

INPUT = "60cba495151dbaa70eec4104748955f81a0301f653c029aa456ea414130b1bef"
MOMENTS = "6785cc434153f1759482a154853685034c9601fb281817c9395103741ca5cca4"
ENDPOINTS = ("openingAgreement", "authorAgreement", "WDateRepeat")


def measured(y, weights):
    a, b = y[:, :, 0], y[:, :, 1]
    n = weights.sum(1)[:, None] * a.shape[1]
    sa, sb = weights @ a.sum(1), weights @ b.sum(1)
    cov = weights @ (a * b).sum(1) - sa * sb / n
    va = weights @ (a * a).sum(1) - sa**2 / n
    vb = weights @ (b * b).sum(1) - sb**2 / n
    denominator = np.sqrt(np.maximum(va, 0) * np.maximum(vb, 0))
    opening = np.divide(
        cov, denominator, out=np.full_like(cov, np.nan), where=denominator > 0
    )
    return np.stack(
        (
            opening,
            correlations(a.mean(1), b.mean(1), weights),
            correlations(b[:, :10].mean(1), b[:, 10:].mean(1), weights),
        ),
        axis=1,
    )


def projected(h, m):
    result = []
    for level in ("post", "author"):
        var = np.einsum("ij,ij->i", h @ m[level + "XX"], h)
        scale = np.sqrt(np.maximum(var[:, None], 0) * m[level + "YY"][None, :])
        cov = h @ m[level + "XY"]
        result.append(
            np.divide(cov, scale, out=np.full_like(cov, np.nan), where=scale > 0)
        )
    result.append(repeats((m["left"], m["between"], m["right"]), h)[:, None])
    return np.concatenate(result, axis=1)


def bands(x, target):
    if not np.isfinite(target) or not np.isfinite(x).all():
        return None
    return {
        "individual": distribution(x.ravel(), target),
        "setMedian": distribution(np.median(x, axis=1), target),
    }


def prepare(out, check):
    data = ROOT / "TP73-paired-inputs-a"
    if confirmed(data) != INPUT:
        raise ValueError("Paired author source differs")
    intake = read(data / "receipt.json")["result"]
    transfer = ROOT / "TP73-paired-moments-transfer"
    receipt = read(bound(transfer / "receipt.json", MOMENTS))
    verified = read(transfer / "verified.json")
    if (
        not verified["nativeExited"]
        or not verified["cpuLeaseReacquired"]
        or verified["sourceReceiptPin"] != MOMENTS
        or verified["receipt"] != receipt
        or read(transfer / "complete.json") != {"sourceReceiptPin": MOMENTS}
        or read(transfer / "owner.json") != receipt["owner"]
        or receipt["source"] != PREP
        or receipt["inputPin"] != pin(transfer / "request.npz")
    ):
        raise ValueError("Incomplete return or source binding for pooled statistics")
    with np.load(
        bound(data / "paired.npz", intake["pairedPin"]), allow_pickle=False
    ) as f:
        y = f["values"].astype(float)
        with np.load(transfer / "request.npz", allow_pickle=False) as sent:
            if not np.array_equal(sent["values"], y) or not np.array_equal(
                sent["opening"], f["opening"].astype("S64")
            ):
                raise ValueError(
                    "Returned statistics used different readers or openings"
                )
    n = len(y)
    if y.shape != (receipt["authors"], 20, 2, 8) or receipt["posts"] != n * 20:
        raise ValueError("Incomplete paired ratings")
    with np.load(
        bound(transfer / "moments.npz", receipt["momentsPin"]), allow_pickle=False
    ) as f:
        m = dict(f)
    with np.load(
        bound(WEEK / "TP58-candidate-b/payload/models/tags.npz", HEAD),
        allow_pickle=False,
    ) as f:
        w = f["weights"].astype(float)
    for level, expected in (
        ("post", y.reshape(-1, 16)),
        ("author", y.mean(1).reshape(n, 16)),
    ):
        if not np.allclose(
            m[level + "YY"],
            ((expected - expected.mean(0)) ** 2).sum(0),
            atol=1e-8,
            rtol=0,
        ):
            raise ValueError("Remote and local rating sums of squares disagree")
    point = measured(y, np.ones((1, n)))[0]
    boots = []
    for draws in np.array_split(resamples(n), 40):
        check()
        boots.append(measured(y, draws))
    boot = np.concatenate(boots)
    tables = {
        name: {
            feat: summary(point[i, j], boot[:, i, j])
            for j, feat in enumerate(core.FEATURES)
        }
        for i, name in enumerate(ENDPOINTS)
    }
    for kind in ("iso", "rot"):
        rows = []
        for start in range(0, 1000, 10):
            check()
            h = np.vstack([heads(w, "TP61", kind, i) for i in range(start, start + 10)])
            rows.append(projected(h, m).reshape(10, 19, 33))
            if (start + 10) % 50 == 0:
                write(
                    out / "progress.json", {"family": kind, "completeSets": start + 10}
                )
        x = np.concatenate(rows)
        with (out / (kind + ".npy")).open("xb") as f:
            np.save(f, x, allow_pickle=False)
        for i, name in enumerate(ENDPOINTS):
            for j, feat in enumerate(core.FEATURES):
                target = point[i, j]
                tables[name][feat][kind] = (
                    {"repeat": bands(x[:, :, 32], target)}
                    if i == 2
                    else {
                        role: bands(x[:, :, 16 * i + 8 * r + j], target)
                        for r, role in enumerate(("BWithControl", "WWithControl"))
                    }
                )
    result = {
        "inputReceipt": INPUT,
        "momentsReceipt": MOMENTS,
        "headPin": HEAD,
        "authors": n,
        "posts": 20 * n,
        "eligibleAuthors": intake["eligibleAuthors"],
        "cohort": intake["cohort"],
        "coverage": intake["coverage"],
        "draws": 2000,
        "setsPerFamily": 1000,
        "headsPerSet": 19,
        "tables": tables,
    }
    write(out / "table.json", result)
    return result
