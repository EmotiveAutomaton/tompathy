"""Writer-held-out dimension counts from the curator's supplied rank preflight."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .envent import RATINGS
from .tp35 import SOURCE as WRITER_SOURCE

LIMIT = "One source, one kind of data, words chosen by the task and not by the writer."
FLOOR = 1e-15


def rank_counts(loss):
    mean = loss.mean(axis=0)
    best = int(mean.argmin())
    se = loss[:, best].std(ddof=1) / np.sqrt(len(loss))
    one = int(np.flatnonzero(mean <= mean[best] + se)[0])
    consecutive = 0
    for rank, gain in enumerate((-np.diff(loss, axis=1)).T, 1):
        if gain.mean() <= 2 * gain.std(ddof=1) / np.sqrt(len(gain)):
            break
        consecutive = rank
    return one, consecutive


def standardized(x):
    sd = x.std(axis=0)
    return (x - x.mean(axis=0)) / np.where(sd > 0, sd, 1.0)


def rank_curve(x, labels, writers, check, *, save_fold=None):
    words = int(labels.max() + 1)
    losses = np.empty((5, words))
    folds = np.full(len(labels), -1)
    effective = []
    for f, (fit, test) in enumerate(GroupKFold(5).split(x, labels, writers)):
        check()
        if set(writers[fit]) & set(writers[test]):
            raise ValueError("Writer appears on both sides of a fold")
        folds[test] = f
        prior = np.bincount(labels[fit], minlength=words) / len(fit)
        losses[f, 0] = -np.log(np.clip(prior[labels[test]], FLOOR, 1)).mean()
        sd = x[fit].std(axis=0)
        scale = np.where(sd > 0, sd, 1.0)
        mu = x[fit].mean(axis=0)
        xt = (x[fit] - mu) / scale
        lda = LinearDiscriminantAnalysis(solver="svd").fit(xt, labels[fit])
        train_z, test_z = lda.transform(xt), lda.transform((x[test] - mu) / scale)
        effective.append(train_z.shape[1])
        for rank in range(1, words):
            check()
            if rank > train_z.shape[1]:
                losses[f, rank] = losses[f, rank - 1]
                continue
            model = LogisticRegression(penalty=None, max_iter=500).fit(
                train_z[:, :rank], labels[fit]
            )
            probabilities = np.full((len(test), words), FLOOR)
            probabilities[:, model.classes_] = model.predict_proba(test_z[:, :rank])
            losses[f, rank] = -np.log(
                np.clip(probabilities[np.arange(len(test)), labels[test]], FLOOR, 1)
            ).mean()
        if save_fold is not None:
            save_fold(f, test, losses[f], effective[-1])
    if not np.isfinite(losses).all() or np.any(folds < 0):
        raise ValueError("Incomplete held-out loss curve")
    return losses, folds, effective


def rotate(x, basis, labels):
    """Orthogonal varimax, deterministic sign, then order by between-word variance."""
    n, rank = basis.shape
    scores = standardized(basis)
    load = x.T @ scores / n
    rotation = np.eye(rank)
    prior = 0.0
    for _ in range(500):
        current = load @ rotation
        target = current**3 - current * np.mean(current**2, axis=0)
        left, singular, right = np.linalg.svd(load.T @ target, full_matrices=False)
        rotation = left @ right
        objective = singular.sum()
        if objective <= prior * (1 + 1e-8):
            break
        prior = objective
    scores = standardized(scores @ rotation)
    load = x.T @ scores / n
    anchor = np.argmax(np.abs(load), axis=0)
    scores *= np.where(load[anchor, np.arange(rank)] < 0, -1.0, 1.0)
    variance = np.zeros(rank)
    for word in np.unique(labels):
        mask = labels == word
        variance += mask.mean() * scores[mask].mean(axis=0) ** 2
    return scores[:, np.argsort(-variance, kind="stable")]


def dimension_tables(x, z, words, clusters, rating_names, word_names, check):
    n, rank = z.shape
    k = x.shape[1]
    labels = np.eye(len(word_names))[words]
    stats = np.column_stack(
        [
            np.ones(n),
            x,
            x * x,
            z,
            z * z,
            (z[:, :, None] * x[:, None, :]).reshape(n, -1),
            labels,
            (labels[:, :, None] * z[:, None, :]).reshape(n, -1),
        ]
    )
    writer_n = int(clusters.max() + 1)
    grouped = np.zeros((writer_n, stats.shape[1]))
    np.add.at(grouped, clusters, stats)
    cuts = np.cumsum([1, k, k, rank, rank, rank * k, len(word_names)])

    def cells(total):
        mass, sx, sxx, sz, szz, products, word_n, word_z = np.split(total, cuts, axis=1)
        mx, mz = sx / mass, sz / mass
        vx = np.maximum(sxx / mass - mx**2, 0)
        vz = np.maximum(szz / mass - mz**2, 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            covariance = (
                products.reshape(-1, rank, k) / mass[:, :, None] - mz[:, :, None] * mx[:, None, :]
            )
            corr = covariance / np.sqrt(vz[:, :, None] * vx[:, None, :])
            means = word_z.reshape(-1, len(word_names), rank) / word_n[:, :, None]
            location = (means - mz[:, None, :]) / np.sqrt(vz[:, None, :])
        return np.concatenate([corr, location.transpose(0, 2, 1)], axis=2)

    point = cells(grouped.sum(axis=0, keepdims=True))[0]
    draws = []
    rng = np.random.default_rng(23)
    for _ in range(80):
        check()
        weights = rng.multinomial(writer_n, np.full(writer_n, 1 / writer_n), size=25)
        draws.append(cells(weights @ grouped))
    draws = np.concatenate(draws)
    axes = []
    for j in range(rank):
        row = {}
        for t, name in enumerate([*rating_names, *word_names]):
            finite = draws[:, j, t]
            finite = finite[np.isfinite(finite)]
            row[name] = {
                "estimate": float(point[j, t]) if np.isfinite(point[j, t]) else None,
                "interval": np.quantile(finite, [0.025, 0.975]).tolist() if len(finite) else None,
                "finiteDraws": len(finite),
            }
        axes.append(
            {
                "ratings": {name: row[name] for name in rating_names},
                "words": {name: row[name] for name in word_names},
            }
        )
    return axes


def run(corpus, output, check, ledger, protocol):
    source = Path(corpus) / "corpus/crowd-enVent_generation.tsv"
    if sha256(source) != WRITER_SOURCE:
        raise ValueError("Original writer source changed")
    frame = pd.read_csv(
        source, sep="\t", quoting=3, usecols=["text_id", "prolific_id", "emotion", *RATINGS]
    )
    x = frame[RATINGS].to_numpy(float)
    if (
        len(frame) != 6600
        or frame.text_id.duplicated().any()
        or frame[["emotion", "prolific_id"]].isna().any().any()
        or not np.isfinite(x).all()
        or np.any((x < 1) | (x > 5))
    ):
        raise ValueError("Incomplete original writer ratings")
    names, labels = np.unique(frame.emotion.to_numpy(str), return_inverse=True)
    writers, clusters = np.unique(frame.prolific_id.to_numpy(str), return_inverse=True)
    if len(names) != 13 or len(writers) != 2379:
        raise ValueError("Original prompted words or writers differ")
    output = Path(output)
    working = {
        "card": "TP37",
        "status": "running",
        "ledger": ledger,
        "productionAdmission": False,
        "scope": LIMIT,
        "sourcePin": WRITER_SOURCE,
        "protocolPin": sha256(protocol),
        "reports": len(frame),
        "writers": len(writers),
        "completedFolds": [],
    }
    save_json(output / "receipt.json", working)

    def save_fold(f, test, losses, effective_rank):
        fold = output / f"fold-{f}.json"
        save_json(
            fold,
            {
                "fold": f,
                "heldOut": len(test),
                "effectiveRank": effective_rank,
                "lossByRank": losses.tolist(),
            },
        )
        working["completedFolds"].append({"fold": f, "filePin": sha256(fold)})
        save_json(output / "receipt.json", working)

    loss, folds, effective = rank_curve(x, labels, clusters, check, save_fold=save_fold)
    one, consecutive = rank_counts(loss)
    report_ids = frame.text_id.to_numpy(dtype=str)
    np.savez(output / "held-out-losses.npz", loss=loss, folds=folds, reportIds=report_ids)
    working.update(
        oneSE=one,
        consecutiveTwoSE=consecutive,
        lossArchivePin=sha256(output / "held-out-losses.npz"),
    )
    save_json(output / "receipt.json", working)
    check()
    standardized_x = standardized(x)
    basis = LinearDiscriminantAnalysis(solver="svd").fit_transform(standardized_x, labels)
    tables = {}
    working["axisArchivePins"] = {}
    for rank in sorted({one, consecutive}):
        if rank > basis.shape[1]:
            raise ValueError("Selected rank exceeds the descriptive basis")
        key = str(rank)
        if rank == 0:
            tables[key] = []
            continue
        check()
        axes = rotate(standardized_x, basis[:, :rank], labels)
        archive = output / f"rotated-rank-{rank}.npz"
        np.savez(archive, reportIds=report_ids, scores=axes)
        working["axisArchivePins"][key] = sha256(archive)
        save_json(output / "receipt.json", working)
        tables[key] = dimension_tables(
            standardized_x, axes, labels, clusters, RATINGS, names.tolist(), check
        )
    result = {
        **working,
        "status": "complete",
        "words": names.tolist(),
        "ratings": RATINGS,
        "foldSizes": np.bincount(folds).tolist(),
        "effectiveRanks": effective,
        "foldLosses": loss.tolist(),
        "rankMeanLoss": loss.mean(0).tolist(),
        "rankStandardError": (loss.std(0, ddof=1) / np.sqrt(5)).tolist(),
        "oneSE": one,
        "consecutiveTwoSE": consecutive,
        "tablesByRank": tables,
        "writerDraws": 2000,
    }
    save_json(output / "receipt.json", result)
