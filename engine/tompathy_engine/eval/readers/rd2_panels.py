"""Apply RD2's fixed slot rule to the two owner-approved views of F2."""
import numpy as np
from scipy.stats import rankdata


def _spearman(x, y):
    """Tied average ranks, independently recomputed for every report draw."""
    x = rankdata(x, axis=-1)
    y = rankdata(y, axis=-1)
    x -= np.mean(x, axis=-1, keepdims=True)
    y -= np.mean(y, axis=-1, keepdims=True)
    scale = np.sqrt(np.sum(x*x, axis=-1) * np.sum(y*y, axis=-1))
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.sum(x*y, axis=-1) / scale


def _common(candidate, reference, truth):
    values = np.asarray((candidate, reference, truth), dtype=float)
    if values.ndim != 2:
        raise ValueError('Expected three aligned report vectors')
    return values[:, np.isfinite(values).all(axis=0)]


def comparison(candidate, reference, truth, check, *, draws=2000):
    a, b, y = _common(candidate, reference, truth)
    n = len(y)
    row = {'reports': len(truth), 'commonValid': n, 'candidateRho': None,
           'trainedRho': None, 'difference': None, 'interval': None,
           'requestedDraws': draws, 'finiteDraws': 0, 'namedOnF2': False}
    if n < 2:
        return row
    correlations = _spearman(np.stack((a, b)), np.stack((y, y)))
    row['candidateRho'], row['trainedRho'] = (
        float(v) if np.isfinite(v) else None for v in correlations)
    if not np.isfinite(correlations).all():
        return row
    row['difference'] = float(correlations[0] - correlations[1])
    diffs = []
    rng = np.random.default_rng(23)
    for start in range(0, draws, 50):
        check()
        indices = rng.integers(n, size=(min(50, draws-start), n))
        diffs.extend(_spearman(a[indices], y[indices]) - _spearman(b[indices], y[indices]))
    finite = np.asarray(diffs)[np.isfinite(diffs)]
    row['finiteDraws'] = len(finite)
    if len(finite):
        row['interval'] = np.quantile(finite, [.025, .975]).tolist()
        row['namedOnF2'] = row['interval'][0] > 0
    return row


def panel_masks(ordered_ids, overlap_ids):
    """The sensitivity cut is id-based, independent of predictions and targets."""
    ids, overlaps = list(ordered_ids), set(overlap_ids)
    if len(ids) != 350 or len(set(ids)) != 350 or len(overlaps) != 2 or not overlaps <= set(ids):
        raise ValueError('Require the registered 350 IDs and both audited overlap IDs')
    return {'registered350': np.ones(350, dtype=bool),
            'textFresh348': np.array([i not in overlaps for i in ids])}


def slot_comparison(ordered_ids, overlap_ids, candidate, trained, truth, check, *, f3=None):
    """Pass F3 only after proving its independent eligibility and exact alignment."""
    values = np.asarray((candidate, trained, truth), dtype=float)
    if values.shape != (3, 350):
        raise ValueError('Candidate, trained and writer rows must align to all 350 IDs')
    confirmation = None
    if f3 is not None:
        if np.shape(f3) != (3, 200):
            raise ValueError('Independent F3 must align all 200 reports')
        a, b, y = _common(*f3)
        if len(y) >= 2:
            r = _spearman(np.stack((a, b)), np.stack((y, y)))
            if np.isfinite(r).all():
                confirmation = {'commonValid': len(y), 'difference': float(r[0]-r[1])}
    panels = {}
    for label, keep in panel_masks(ordered_ids, overlap_ids).items():
        result = comparison(*values[:, keep], check)
        result['wouldTakeSlot'] = bool(result['namedOnF2'] and confirmation
                                       and confirmation['difference'] >= 0)
        panels[label] = result
    registered, fresh = panels.values()
    return {'panels': panels, 'independentF3': confirmation,
            'nominationChanges': registered['namedOnF2'] != fresh['namedOnF2'],
            'slotConclusionChanges': registered['wouldTakeSlot'] != fresh['wouldTakeSlot']}


def research_reader(ordered_ids, overlap_ids, reader_c, reader_b, truth):
    """Separate eight-feature description, conditional on C's general checks."""
    arrays = np.asarray((reader_c, reader_b, truth), dtype=float)
    if arrays.shape != (3, 350, 8):
        raise ValueError('Expected eight aligned features on all 350 reports')
    panels = {}
    for name, keep in panel_masks(ordered_ids, overlap_ids).items():
        differences, counts, reader_c_rhos, reader_b_rhos = [], [], [], []
        for feature in range(8):
            a, b, y = _common(*arrays[:, keep, feature])
            counts.append(len(y))
            rc, rb = (_spearman(a, y), _spearman(b, y)) if len(y) >= 2 else (np.nan, np.nan)
            reader_c_rhos.append(float(rc) if np.isfinite(rc) else None)
            reader_b_rhos.append(float(rb) if np.isfinite(rb) else None)
            d = rc - rb
            differences.append(float(d) if np.isfinite(d) else None)
        wins = sum(d is not None and d >= 0 for d in differences)
        panels[name] = {'commonValid': counts, 'readerCRho': reader_c_rhos, 'readerBRho': reader_b_rhos,
                        'differences': differences,
                        'atOrAboveB': wins, 'candidateResearchReader': wins >= 6}
    a, b = panels.values()
    return {'panels': panels,
            'conclusionChanges': a['candidateResearchReader'] != b['candidateResearchReader'],
            'featureComparisonsChanged': [
                i for i, (x, y) in enumerate(zip(a['differences'], b['differences']))
                if (None if x is None else x >= 0) != (None if y is None else y >= 0)]}
