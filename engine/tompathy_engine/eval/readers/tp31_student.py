"""TP31 source-separated fitting helpers; caller must verify teacher artifacts first."""
import numpy as np

from .tp25 import GRID, fit, split
from .tp31_teacher import SOURCES, text_pin


def rates(truth, probability, threshold):
    truth, probability = np.asarray(truth), np.asarray(probability, float)
    if (truth.ndim != 1 or probability.shape != truth.shape or
            not np.isfinite(probability).all() or not np.isin(truth, [0, 1]).all() or
            np.any((probability < 0) | (probability > 1))):
        raise ValueError('Finite aligned binary truth and probabilities required')
    positive, negative = truth == 1, truth == 0
    detection = float((probability[positive] >= threshold).mean()) if positive.any() else None
    silence = float((probability[negative] < threshold).mean()) if negative.any() else None
    return {'n': len(truth), 'positive': int(positive.sum()), 'negative': int(negative.sum()),
            'detection': detection, 'silence': silence,
            'passes': detection is not None and silence is not None and detection >= .7 and silence >= .8}


def threshold_on_development(truth, probability, sources, expected_sources):
    truth, probability, sources = np.asarray(truth), np.asarray(probability), np.asarray(sources)
    if truth.shape != probability.shape or truth.shape != sources.shape:
        raise ValueError('Aligned inner development arrays required')
    curves = {source: [rates(truth[sources == source], probability[sources == source], t) for t in GRID]
              for source in sorted(expected_sources)}
    for i, threshold in enumerate(GRID):
        if curves and all(curve[i]['passes'] for curve in curves.values()):
            return float(threshold), True, curves
    return .5, False, curves


def fitting_indices(rows, held_source):
    """Exclude all exact held-source text matches before grouping/development."""
    if held_source not in SOURCES or {row['source'] for row in rows} != set(SOURCES):
        raise ValueError('All six registered sources required')
    ids = [row['id'] for row in rows]
    if len(set(ids)) != len(ids) or any(not row['group'] for row in rows):
        raise ValueError('Unique identities and original groups required')
    test = np.array([i for i, row in enumerate(rows) if row['source'] == held_source], dtype=int)
    test_pins = {text_pin(rows[i]['text']) for i in test}
    eligible = np.array([i for i, row in enumerate(rows) if row['source'] != held_source
                         and text_pin(row['text']) not in test_pins], dtype=int)
    fitting, development = [], []
    for source in sorted(set(SOURCES)-{held_source}):
        index = np.array([i for i in eligible if rows[i]['source'] == source], dtype=int)
        groups = np.array([rows[i]['group'] for i in index])
        train, dev = split(groups)
        fitting.extend(index[train]); development.extend(index[dev])
    return {'fit': np.array(fitting, dtype=int), 'development': np.array(development, dtype=int),
            'refit': eligible, 'test': test,
            'excludedTextOverlaps': sum(row['source'] != held_source for row in rows)-len(eligible)}


def fit_source_fold(rows, truth, vectors, held_source, check):
    """Consume only verified, valid teacher rows; return durable-save-ready results."""
    truth, vectors = np.asarray(truth), np.asarray(vectors, float)
    if (truth.shape != (len(rows),) or not np.isin(truth, [0, 1]).all() or
            vectors.ndim != 2 or len(vectors) != len(rows) or not np.isfinite(vectors).all()):
        raise ValueError('Finite row-aligned vectors and valid teacher targets required')
    index = fitting_indices(rows, held_source)
    fit_ids, dev, refit, test = [index[name] for name in ('fit', 'development', 'refit', 'test')]
    if len(np.unique(truth[fit_ids])) != 2 or not len(dev) or len(np.unique(truth[refit])) != 2:
        return {'status': 'unavailable', 'reason': 'Missing fitting contrast or development rows',
                'heldSource': held_source, 'qualifies': False, 'indices': index}
    model = fit(vectors[fit_ids], truth[fit_ids], check)
    threshold, qualified, curves = threshold_on_development(
        truth[dev], model.predict_proba(vectors[dev])[:, 1],
        [rows[i]['source'] for i in dev], set(SOURCES)-{held_source})
    model = fit(vectors[refit], truth[refit], check)
    probability = model.predict_proba(vectors[test])[:, 1]
    check()
    metrics = rates(truth[test], probability, threshold)
    return {'status': 'complete', 'heldSource': held_source, 'threshold': threshold,
            'developmentQualified': qualified, 'developmentCurves': curves, 'metrics': metrics,
            'qualifies': qualified and metrics['passes'], 'indices': index,
            'probability': probability, 'truth': truth[test],
            'weights': model.coef_, 'bias': model.intercept_}


def acceptance(theme_probability, revision_probability, threshold):
    def count(values, size):
        values = np.asarray(values, float)
        if values.shape != (size,) or not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
            raise ValueError('Exact finite fixed acceptance set required')
        silent = int((values < threshold).sum())
        return {'n': size, 'silent': silent, 'silence': silent/size, 'passes': silent/size >= .8}
    themes, revisions = count(theme_probability, 40), count(revision_probability, 191)
    return {'themeFree': themes, 'revisions': revisions, 'passes': themes['passes'] and revisions['passes']}
