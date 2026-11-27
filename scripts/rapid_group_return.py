"""TP70 aggregate from the verified paired control sets and whole-person draws."""

import numpy as np
from rapid_blind_groups import GROUPINGS, TAGS
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_head_check import HEAD, bound, read
from word_table_lane import write

DESIGN = "f89c4cf876b2ce4f4a4b04684423a591c450f6f7bcf939b59c0cf0ccb03b5036"
BLOCK_CODE = "87cc836e3d2d368f75091c57814c48eed7d865a3ad9b9dba825284fefa16452c"
N = len(TAGS)
DISPLAY = ["acceptance" if t == "belonging" else t for t in TAGS]


def estimate(draws):
    return {
        "value": float(draws[0]),
        "interval": np.quantile(draws[1:], [0.025, 0.975]).tolist(),
        "standardError": float(np.std(draws[1:], ddof=1)),
    }


def near_zero(stat):
    return min(abs(v) for v in stat["interval"]) <= stat["standardError"]


def difference(a, b, null):
    delta = a - b
    measured = estimate(delta)
    return {
        **measured,
        "positive": bool(delta[0] > 0),
        "nearBar": near_zero(measured),
        "orientationP": (1 + int(np.count_nonzero(null >= delta[0]))) / (1 + len(null)),
    }


def floor_count(eigenvalues, cutoffs):
    return np.cumprod(eigenvalues > cutoffs, axis=-1).sum(-1)


def rotation(matrix, n):
    if n < 2:
        return {
            "components": n,
            "reason": "The rotated-control floor retained fewer than two components.",
        }
    ev, vec = np.linalg.eigh(matrix)
    idx = np.argsort(ev)[::-1][:n]
    load = vec[:, idx] * np.sqrt(np.maximum(ev[idx], 0))
    transform = np.eye(n)
    previous = 0.0
    for _ in range(500):
        turned = load @ transform
        u, s, vt = np.linalg.svd(
            load.T @ (turned**3 - turned @ np.diag((turned**2).sum(0)) / len(load))
        )
        transform = u @ vt
        current = float(s.sum())
        if current < previous * (1 + 1.0e-10):
            break
        previous = current
    turned = load @ transform
    assignments = {}
    for name, row in zip(DISPLAY, turned, strict=True):
        best = int(np.argmax(np.abs(row)))
        assignments[name] = {
            "component": best + 1 if abs(row[best]) >= 0.4 else None,
            "signedLoading": float(row[best]),
            "loadings": row.tolist(),
        }
    return {"components": n, "tags": assignments}


def cell(trained, iso, rot):
    """Each row is the observed data or a common bootstrap draw, columns are registered statistics."""
    out = {"groups": {}, "floors": {}, "excessComparisons": {}}
    limits = {}
    for family, data in (("iso", iso), ("rot", rot)):
        q = np.quantile(data[:, :, :N], 0.95, axis=0)
        floors = floor_count(trained[:, :N], q)
        counts = np.bincount(floors[1:], minlength=N + 1)
        out["floors"][family] = {
            "count": int(floors[0]),
            "cutoffs": q[0].tolist(),
            "resampleCounts": counts.tolist(),
            "resampleInterval": np.quantile(
                floors[1:], [0.025, 0.975], method="inverted_cdf"
            ).tolist(),
        }
        limits[family] = np.quantile(data[:, :, N:], [0.025, 0.5, 0.975], axis=0)
    out["trainedEigenvalues"] = trained[0, :N].tolist()
    lo, mid, hi = limits["rot"]
    span = hi - lo
    if not np.all(span > 0):
        raise ValueError("Zero width in a grouping's ROT band")
    excess = (trained[:, N:] - mid) / span
    rotated_excess = (rot[:, 0, N:] - mid[0]) / span[0]
    for j, name in enumerate(GROUPINGS):
        scores = trained[:, N + j]
        entry = {"trained": estimate(scores), "excess": estimate(excess[:, j])}
        for family, data in (("iso", iso), ("rot", rot)):
            low, med, high = limits[family][:, :, j]
            candidate = data[:, 0, N + j]
            gap = estimate(scores - high)
            entry[family] = {
                "lower": float(low[0]),
                "median": float(med[0]),
                "upper": float(high[0]),
                "percentile": float(
                    100
                    * (
                        np.sum(candidate < scores[0])
                        + 0.5 * np.sum(candidate == scores[0])
                    )
                    / len(candidate)
                ),
                "aboveBand": bool(scores[0] > high[0]),
                "marginAboveBand": gap,
                "nearBar": near_zero(gap),
                "orientationP": (1 + int(np.count_nonzero(candidate >= scores[0])))
                / (len(candidate) + 1),
            }
        out["groups"][name] = entry
    for first, second, label in [
        (1, 0, "threadMinusMap"),
        (2, 1, "printMinusThread"),
        (2, 0, "printMinusMap"),
    ]:
        out["excessComparisons"][label] = difference(
            excess[:, first],
            excess[:, second],
            rotated_excess[:, first] - rotated_excess[:, second],
        )
    return out


def prepare(out, check):
    design = ROOT / "TP70-design-a"
    if confirmed(design) != DESIGN:
        raise ValueError("TP70 design receipt differs")
    src = read(design / "receipt.json")["result"]
    blobs = {
        k: {fam: np.empty((1000, 101, 2, N + 4)) for fam in ("iso", "rot")}
        for k in ("chat", "blog")
    }
    trained = {}
    corr = {}
    pins = {}
    for i in range(40):
        folder = ROOT / f"TP70-block-{i:02d}-a"
        pins[folder.name] = confirmed(folder)
        receipt = read(folder / "receipt.json")
        r = receipt["result"]
        if (
            receipt["codePin"] != BLOCK_CODE
            or r["designReceiptPin"] != DESIGN
            or r["tagHeadPin"] != HEAD
            or r["resamples"] != 100
            or r["block"] != i
            or r["rows"] != src["rows"]
            or r["clusters"] != src["clusters"]
        ):
            raise ValueError("Incompatible TP70 block")
        expected = {
            (family, j)
            for family in ("iso", "rot")
            for j in range(i * 25, (i + 1) * 25)
        }
        if i == 0:
            expected.add(("trained", 0))
        if set(r["files"]) != {f"{f}-{j:04d}.npz" for f, j in expected}:
            raise ValueError("Duplicate or missing grouping set")
        for fam, j in sorted(expected):
            check()
            filename = f"{fam}-{j:04d}.npz"
            with np.load(
                bound(folder / filename, r["files"][filename]), allow_pickle=False
            ) as f:
                for source in blobs:
                    a = f[source]
                    if a.shape != (101, 2, N + 4) or not np.isfinite(a).all():
                        raise ValueError("Missing a grouping or a whole-person draw")
                    if fam == "trained":
                        trained[source] = a
                        m = f[source + "Corr"]
                        if (
                            m.shape != (N, N)
                            or not np.allclose(m, m.T)
                            or not np.allclose(np.diag(m), 1)
                        ):
                            raise ValueError("Trained correlation matrix differs")
                        corr[source] = m
                    else:
                        blobs[source][fam][j] = a
    sources = {}
    for source, raw in blobs.items():
        check()
        cells = {
            key: cell(trained[source][:, k], raw["iso"][:, :, k], raw["rot"][:, :, k])
            for k, key in enumerate(("full", "removeLeading"))
        }
        matrix = corr[source]
        cells["varimax"] = rotation(matrix, cells["full"]["floors"]["rot"]["count"])
        cells["pairOrder"] = DISPLAY
        cells["pairCorrelations"] = matrix.tolist()
        sources[source] = cells
        write(out / (source + ".json"), cells)
    return {
        "card": "TP70",
        "designReceiptPin": DESIGN,
        "blockReceiptPins": pins,
        "tagHeadPin": HEAD,
        "setsPerFamily": 1000,
        "resamples": 100,
        "rows": src["rows"],
        "clusters": src["clusters"],
        "sources": sources,
        "pairInterpretation": "All pairs and rotated component assignments are descriptive.",
    }
