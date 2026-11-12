"""Training-only scaling, held-out forecasts and paired cluster uncertainty."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from scipy.stats import rankdata

from .protocol import PROTOCOL


def auc(labels, scores):
    y, score = np.asarray(labels), np.asarray(scores, dtype=float)
    if len(y) != len(score) or not np.isfinite(score).all() or not set(y) <= {0, 1}:
        raise ValueError("Invalid binary AUC inputs")
    pos, neg = (y == 1).sum(), (y == 0).sum()
    if not pos or not neg:
        return None
    return float((rankdata(score)[y == 1].sum() - pos*(pos+1)/2) / (pos*neg))


def fit_logistic(features, labels, classes=2):
    x, y = np.asarray(features, dtype=float), np.asarray(labels, dtype=int)
    if x.ndim != 2 or not len(x) or len(x) != len(y) or not np.isfinite(x).all() or not set(y) <= set(range(classes)):
        raise ValueError("Malformed logistic training set")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-12] = 1
    design = np.column_stack([np.ones(len(x)), (x-mean)/scale])
    target = np.eye(classes)[y]
    def objective(flat):
        weights = flat.reshape(design.shape[1], classes)
        logits = design @ weights
        loss = (logsumexp(logits, axis=1) - logits[np.arange(len(y)), y]).sum() + .5*(weights[1:]**2).sum()
        gradient = design.T @ (softmax(logits, axis=1)-target)
        gradient[1:] += weights[1:]
        return loss, gradient.ravel()
    result = minimize(objective, np.zeros(design.shape[1]*classes), jac=True, method="L-BFGS-B",
        options={"maxiter": 1000, "ftol": 1e-10})
    if not result.success:
        raise RuntimeError("Logistic optimization failed: " + result.message)
    return {"mean": mean, "scale": scale, "weights": result.x.reshape(design.shape[1], classes)}


def predict(model, features):
    x = np.asarray(features, dtype=float)
    if x.ndim != 2 or x.shape[1] != len(model["mean"]) or not np.isfinite(x).all():
        raise ValueError("Invalid held-out features")
    return softmax(np.column_stack([np.ones(len(x)), (x-model["mean"])/model["scale"]]) @ model["weights"], axis=1)


def cross_fit(features, labels, folds, classes=2):
    x, y, f = np.asarray(features), np.asarray(labels), np.asarray(folds)
    if len(x) != len(y) or len(x) != len(f) or len(set(f)) < 2:
        raise ValueError("Cross-fitting requires disjoint folds")
    output = np.zeros((len(x), classes))
    for fold in sorted(set(f)):
        train, test = f != fold, f == fold
        output[test] = predict(fit_logistic(x[train], y[train], classes), x[test])
    return output


def paired_auc(labels, baseline, engine, clusters, *, draws=2000, seed=20261111):
    y, a, b, groups = map(np.asarray, (labels, baseline, engine, clusters))
    if not len(y) or not len(y) == len(a) == len(b) == len(groups):
        raise ValueError("Paired metric arrays differ in length")
    values, omitted = [], 0
    for group in sorted(set(groups)):
        selected = groups == group
        left, right = auc(y[selected], a[selected]), auc(y[selected], b[selected])
        if left is None:
            omitted += 1
        else:
            values.append((left, right))
    if len(values) < 2:
        raise ValueError("Need at least two clusters with both labels")
    values = np.asarray(values)
    gains = values[:, 1]-values[:, 0]
    rng = np.random.default_rng(seed)
    boot = [float(gains[rng.integers(len(gains), size=len(gains))].mean()) for _ in range(draws)]
    return {"baseline": float(values[:,0].mean()), "engine": float(values[:,1].mean()),
        "gain": float(gains.mean()), "interval": np.quantile(boot, [.025,.975]).tolist(),
        "clusters": len(values), "singleClassClustersExcluded": omitted, "draws": draws,
        "uncertainty": "cluster bootstrap of fixed out-of-fold predictions; conditional on fitted models"}


def registered_row(ident, labels, baseline, engine, clusters, capability):
    value = paired_auc(labels, baseline, engine, clusters, draws=PROTOCOL["draws"], seed=PROTOCOL["seed"])
    value.update(id=str(ident), registered=True, bar=PROTOCOL[capability]["rows"][str(ident)])
    low, high = value["interval"]
    if str(ident) == "3":
        value["reading"] = "hers" if low > 0 else "more text of the same kind" if capability == "attention" and low >= -.01 and high <= .01 else "unresolved"
    else:
        value["clearsBar"] = low > value["bar"]
    return value
