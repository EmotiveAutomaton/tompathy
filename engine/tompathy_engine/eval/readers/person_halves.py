"""Word-adjusted writer halves and held-out matching for the November 21 packet."""
import hashlib
import re
from collections import Counter

import numpy as np
import pandas as pd

FORMS = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)


def hashed(prefix, value):
    return hashlib.sha256((prefix + str(value)).encode()).digest()


def style_features(texts):
    tokens = [FORMS.findall(s) for s in texts]
    counts = Counter(t.casefold() for row in tokens for t in row)
    top = sorted(counts, key=lambda w: (-counts[w], w))[:50]
    names = ["tokens", "meanWordLength", *["form/" + w for w in top],
             "comma", "fullStop", "exclamation", "questionMark", "apostrophe", "capitalizedShare"]
    rows = []
    for text, words in zip(texts, tokens, strict=True):
        n = len(words)
        denom = max(1, n)
        freq = Counter(w.casefold() for w in words)
        punctuation = [text.count(c) for c in ",.!?"] + [text.count("'") + text.count("’")]
        rows.append([n, sum(map(len, words)) / denom, *[100 * freq[w] / denom for w in top],
                     *[100 * count / denom for count in punctuation],
                     sum(w[0].isupper() for w in words) / denom])
    return names, np.asarray(rows, float)


def split(writers, ids, minimum=8):
    groups = {}
    for i, writer in enumerate(writers):
        groups.setdefault(writer, []).append(i)
    eligible = sorted((w for w, ix in groups.items() if len(ix) >= minimum),
                      key=lambda w: hashed("TP39:fold:", w))
    half = np.full(len(writers), -1)
    owner = np.full(len(writers), -1)
    for j, writer in enumerate(eligible):
        ix = sorted(groups[writer], key=lambda i: hashed("TP39:23:", ids[i]))
        middle = len(ix) // 2
        half[ix[:middle]], half[ix[middle:]] = 0, 1
        owner[ix] = j
    return eligible, owner, half


def half_departures(values, words, writers, owner, half):
    data = pd.DataFrame(np.asarray(values, dtype=float))
    labels = [pd.Series(words).reset_index(drop=True), pd.Series(writers).reset_index(drop=True)]
    population = data.groupby(labels[0], sort=False)
    own = data.groupby(labels, sort=False)
    n = population.transform("count") - own.transform("count")
    other = (population.transform("sum") - own.transform("sum")).div(n.where(n > 0))
    diff = data - other
    return np.stack([diff[half == h].groupby(owner[half == h]).mean().reindex(
        range(int(max(owner)) + 1)).to_numpy() for h in [0, 1]])


def correlations(a, b, weights):
    valid = np.isfinite(a) & np.isfinite(b)
    n = weights @ valid.astype(float)
    a, b = np.where(valid, a, 0.), np.where(valid, b, 0.)
    with np.errstate(divide="ignore", invalid="ignore"):
        ma, mb = (weights @ a) / n, (weights @ b) / n
        va = np.maximum((weights @ (a*a)) / n - ma*ma, 0)
        vb = np.maximum((weights @ (b*b)) / n - mb*mb, 0)
        denominator = np.sqrt(va*vb)
        covariance = (weights @ (a*b)) / n - ma*mb
        return np.divide(covariance, denominator, out=np.full_like(covariance,np.nan),
                         where=(n >= 2) & (denominator > 0))


def resamples(n, draws=2000):
    return np.random.default_rng(23).multinomial(n, np.full(n, 1/n), size=draws).astype(float)


def summary(value, draws):
    available = draws[np.isfinite(draws)]
    return {"value": float(value) if np.isfinite(value) else None,
            "interval": np.quantile(available, [.025, .975]).tolist() if len(available) else None,
            "validDraws": len(available)}


def stability(profiles, names, blocks, weights, check):
    a, b = profiles
    p = correlations(a, b, np.ones((1, len(a))))[0]
    draws = []
    for batch in np.array_split(weights, 40):
        check()
        draws.append(correlations(a, b, batch))
    boot = np.vstack(draws)
    count = (np.isfinite(a) & np.isfinite(b)).sum(axis=0)
    readings = {k: {**summary(p[j], boot[:, j]), "pairedWriters": int(count[j])} for j, k in enumerate(names)}
    sets = {}
    for name, idx in blocks.items():
        ok = [k for k in idx if np.isfinite(p[k])]
        if not ok:
            raise ValueError("No supported reading in " + name)
        variances = np.nanvar(boot[:, ok], axis=0, ddof=1)
        pooling = np.isfinite(variances) & (variances > 0)
        pooled = None
        if pooling.any():
            iw = 1/variances[pooling]
            iw /= iw.sum()
            use = np.asarray(ok)[pooling]
            pooled = summary(p[use] @ iw, boot[:, use] @ iw)
        sets[name] = {**summary(p[ok].mean(), boot[:, ok].mean(axis=1)), "inverseVariance": pooled,
                      "used": [names[k] for k in ok]}
    return readings, sets


def ranks(scores):
    # Candidate columns are already in their fixed writer-hash order.
    own = np.diag(scores)[:, None]
    earlier = np.arange(len(scores))[None, :] < np.arange(len(scores))[:, None]
    return 1 + (scores > own).sum(axis=1) + ((scores == own) & earlier).sum(axis=1)


def match(profiles, blocks, weights, check):
    arms = {**blocks, **{"style+"+k: [*blocks["style"], *v] for k, v in blocks.items() if k != "style"},
            "all": [i for cols in blocks.values() for i in cols]}
    p = profiles[:, :, arms["all"]]
    if not np.isfinite(p).all():
        raise ValueError("Incomplete eligible writer half in a matching set; retain registered denominator")
    a, b = profiles
    def standardize(v):
        sd = np.std(v, axis=0)
        return np.divide(v - v.mean(axis=0), sd, out=np.zeros_like(v), where=sd > 0)
    a, b = standardize(a), standardize(b)
    folds = np.arange(len(a)) % 2
    results, fixed = {}, {}
    for arm, idx in arms.items():
        check()
        x, y = a[:, idx], b[:, idx]
        likelihood, distance = np.empty(len(a), int), np.empty(len(a), int)
        for fold in [0, 1]:
            test = folds == fold
            coeff = correlations(x[~test], y[~test], np.ones((1, sum(~test))))[0]
            r = np.clip(np.nan_to_num(coeff, nan=0., posinf=0., neginf=0.), 0, .95)
            lin, quad = r/(1-r*r), r*r/(2*(1-r*r))
            l, m = x[test], y[test]
            scores = (l*lin) @ m.T - ((l*l) @ quad)[:, None] - ((m*m) @ quad)[None, :]
            likelihood[test] = ranks(scores)
            distance[test] = ranks(2*l @ m.T - (l*l).sum(axis=1)[:, None] - (m*m).sum(axis=1)[None, :])
        def report(rank):
            return {str(k): summary(np.mean(rank <= k), weights @ (rank <= k) / len(rank)) for k in (1, 10)}
        results[arm] = {"likelihood": report(likelihood), "squaredDistance": report(distance)}
        fixed[arm] = (likelihood <= 10).astype(float)
    gain = fixed["style+tags"] - fixed["style"]
    return results, summary(gain.mean(), weights @ gain / len(gain))
