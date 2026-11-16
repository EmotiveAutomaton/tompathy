"""Fixed metrics and writer-cluster uncertainty; no test-set threshold selection."""
import numpy as np


def confusion(y, predicted, k):
    return np.bincount(np.asarray(y)*k + np.asarray(predicted), minlength=k*k).reshape(k, k)


def from_table(table):
    m = np.asarray(table, float)
    diagonal = np.diagonal(m, axis1=-2, axis2=-1)
    support, predicted = m.sum(axis=-1), m.sum(axis=-2)
    f1 = np.divide(2*diagonal, support+predicted, out=np.zeros_like(diagonal), where=support+predicted > 0)
    return {'accuracy': diagonal.sum(axis=-1)/m.sum(axis=(-1, -2)), 'macro_f1': f1.mean(axis=-1)}


def classification(y, probabilities, writers, labels, *, bootstrap=1000, seed=20261114):
    y, p, writers = np.asarray(y, int), np.asarray(probabilities, float), np.asarray(writers)
    k = len(labels)
    if (p.shape != (len(y), k) or not np.isfinite(p).all() or (p < 0).any()
            or not np.allclose(p.sum(axis=1), 1) or len(writers) != len(y)):
        raise ValueError('Invalid classification probabilities or grouping')
    prediction = p.argmax(axis=1)
    table = confusion(y, prediction, k)
    scores = from_table(table)
    clusters = np.array([confusion(y[writers == w], prediction[writers == w], k) for w in np.unique(writers)])
    rng = np.random.default_rng(seed)
    draws = np.array([from_table(clusters[rng.integers(len(clusters), size=len(clusters))].sum(axis=0))['macro_f1']
                      for _ in range(bootstrap)])
    conf = p.max(axis=1)
    order = np.argsort(-conf, kind='stable')
    bins = []
    for lo, hi in zip(np.linspace(0, 1, 11)[:-1], np.linspace(0, 1, 11)[1:]):
        selected = (conf >= lo) & (conf < hi if hi < 1 else conf <= hi)
        bins.append({'from': float(lo), 'to': float(hi), 'n': int(selected.sum()),
            'confidence': float(conf[selected].mean()) if selected.any() else None,
            'accuracy': float((prediction[selected] == y[selected]).mean()) if selected.any() else None})
    neutral = labels.index('no-emotion') if 'no-emotion' in labels else None
    return {**{key: float(value) for key, value in scores.items()},
        'macro_f1_interval': np.quantile(draws, [.025, .975]).tolist(),
        'interval_method': f'{bootstrap} writer-cluster bootstrap draws, fixed label set',
        'n': len(y), 'writers': len(clusters), 'labels': labels, 'error_counts': table.tolist(),
        'recall': {label: float(table[i,i]/table[i].sum()) if table[i].sum() else None for i,label in enumerate(labels)},
        'calibration': bins,
        'selective_accuracy': {str(c): float((prediction[order[:int(c*len(y))]] == y[order[:int(c*len(y))]]).mean()) for c in (.22, .5)},
        'no_emotion_recall': float((prediction[y == neutral] == neutral).mean()) if neutral is not None else None,
        'false_no_emotion': float((prediction[y != neutral] == neutral).mean()) if neutral is not None else None}


def channel_gates(result, baseline, neutral_checks):
    b1 = result['macro_f1'] >= .49 and result['macro_f1_interval'][0] > baseline['macro_f1']
    complete = (neutral_checks.get('theme_free_n') == 40 and neutral_checks.get('revision_n', 0) > 0
                and neutral_checks.get('revision_coverage_complete', False))
    b3 = (complete and result['no_emotion_recall'] >= .4 and result['false_no_emotion'] <= .05
          and neutral_checks['theme_free_silent'] >= 36 and neutral_checks['revision_silent_rate'] >= .9)
    return {'B1': b1, 'B2_stretch': result['macro_f1'] >= .565,
            'B3': bool(b3) if complete else None,
            'B4': result['selective_accuracy']['0.5'] >= .70 and result['selective_accuracy']['0.22'] >= .78,
            'pack_eligible': bool(b1 and b3), 'productionAdmission': False}
