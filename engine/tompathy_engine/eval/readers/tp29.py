"""Frozen away-source embarrassment/shame contrasts, not channel admission."""
import hashlib
import re
from pathlib import Path

import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .artifacts import seal
from .envent import load
from .tp23 import saved_vectors

FUN = ['laugh', 'laughs', 'laughed', 'laughing', 'laughter', 'chuckle', 'chuckles', 'chuckled', 'chuckling', 'giggle', 'giggles', 'giggled', 'giggling', 'joke', 'jokes', 'joked', 'joking', 'funny', 'funnier', 'funniest', 'humor', 'humour', 'humorous', 'playful', 'playfully']
APPEASE = ['apology', 'apologies', 'apologize', 'apologizes', 'apologized', 'apologizing', 'apologise', 'apologises', 'apologised', 'apologising', 'apologetic', 'sorry', 'awkward', 'awkwardly', 'awkwardness', 'blush', 'blushes', 'blushed', 'blushing']
LIMIT = 'Literal markers and source-trained label heads, not channel firing, writer traits or maker needs. ED research-only; source elicitation and reader/writer labels differ.'


def markers(texts):
    rows = []
    for text in texts:
        words = re.findall(r"[a-z]+(?:'[a-z]+)?", str(text).lower())
        rows.append((max(1, len(words)), sum(w in FUN for w in words),
                     sum(w in APPEASE for w in words)))
    return np.asarray(rows, float)


def folds(writers, seed=23):
    writers = np.asarray(writers, str)
    unique = sorted(set(writers), key=lambda w: hashlib.sha256(f'{seed}:{w}'.encode()).hexdigest())
    if len(unique) < 5:
        raise ValueError('Five writer-disjoint folds require five writers')
    assignment = {w: i % 5 for i, w in enumerate(unique)}
    return np.asarray([assignment[w] for w in writers])


def fit(x, y, *, balanced=False):
    if set(np.unique(y)) != {0, 1} or not np.isfinite(x).all():
        raise ValueError('Finite two-class fitting contrast required')
    model = LogisticRegression(C=3, max_iter=2000, random_state=23,
                               class_weight='balanced' if balanced else None).fit(x, y)
    if np.any(model.n_iter_ >= model.max_iter):
        raise RuntimeError('Fixed TP29 logistic objective did not converge')
    return model


def paired_calibration(scores, y, writers, check=lambda: None):
    """Training-writer scaling; one fixed prediction per ED situation."""
    assignment = folds(writers)
    forecasts = np.full((len(y), 2), np.nan)
    coefficients = []
    for fold in range(5):
        check()
        train, test = assignment != fold, assignment == fold
        center, scale = scores[train].mean(0), scores[train].std(0)
        if np.any(scale <= 1e-12):
            raise ValueError('Degenerate stand-in scores')
        x = (scores-center)/scale
        one = fit(x[train, :1], y[train])
        two = fit(x[train], y[train])
        forecasts[test, 0] = one.predict_proba(x[test, :1])[:, 1]
        forecasts[test, 1] = two.predict_proba(x[test])[:, 1]
        coefficients.append({'fold': fold, 'train': int(train.sum()), 'test': int(test.sum()),
                             'shame': float(two.coef_[0, 0]), 'play': float(two.coef_[0, 1]),
                             'center': center.tolist(), 'scale': scale.tolist()})
    if not np.isfinite(forecasts).all():
        raise RuntimeError('Missing held-out calibration forecast')
    return forecasts, assignment, coefficients


def interval(samples, draws):
    values = np.asarray(samples, float)
    values = values[np.isfinite(values)]
    return np.quantile(values, [.025, .975]).tolist() if len(values) >= .95*draws else None


def weighted_mean(values, mask, weights):
    total = weights[mask].sum()
    return float(weights[mask]@values[mask]/total) if total else np.nan


def rate_ratio(counts, positive, negative, weights):
    exposure = [weights[m]@counts[m, 0] for m in (positive, negative)]
    rates = [weights[m]@counts[m, 1]/e if e else np.nan
             for m, e in zip((positive, negative), exposure)]
    return float(rates[0]/rates[1]) if all(np.isfinite(v) and v > 0 for v in rates) else np.nan


def ed_statistics(counts, labels, scores, forecasts, weights):
    positive, negative = labels == 'embarrassed', labels == 'ashamed'
    y = positive.astype(int)
    fun = rate_ratio(counts[:, :2], positive, negative, weights)
    appease = rate_ratio(counts[:, [0, 2]], positive, negative, weights)
    both = positive | negative
    center = weighted_mean(scores[:, 1], both, weights)
    variance = weighted_mean((scores[:, 1]-center)**2, both, weights)
    gap = ((weighted_mean(scores[:, 1], positive, weights)-weighted_mean(scores[:, 1], negative, weights))
           /np.sqrt(variance)) if variance > 0 else np.nan
    if min(weights[y == 0].sum(), weights[y == 1].sum()) > 0:
        auc = [float(roc_auc_score(y, p, sample_weight=weights)) for p in forecasts.T]
    else:
        auc = [np.nan, np.nan]
    return np.asarray([fun, appease, gap, *auc, auc[1]-auc[0]])


def bootstrap_ed(counts, labels, scores, forecasts, writers, check=lambda: None, *, draws=2000):
    groups, inverse = np.unique(writers, return_inverse=True)
    rng = np.random.default_rng(23)
    point = ed_statistics(counts, labels, scores, forecasts, np.ones(len(labels)))
    samples = []
    for i in range(draws):
        if i % 16 == 0:
            check()
        weight = np.bincount(rng.integers(len(groups), size=len(groups)), minlength=len(groups))[inverse]
        samples.append(ed_statistics(counts, labels, scores, forecasts, weight))
    samples = np.asarray(samples)
    names = ('fun_rate_ratio', 'appeasement_rate_ratio', 'play_gap_sd', 'shame_auc', 'combined_auc', 'auc_gain')
    return {name: {'estimate': float(point[j]) if np.isfinite(point[j]) else None,
                   'interval': interval(samples[:, j], draws),
                   'finite_draws': int(np.isfinite(samples[:, j]).sum())}
            for j, name in enumerate(names)}


def co_labels(truth, labels, writers, check=lambda: None, *, draws=2000):
    amusement, embarrassed, remorse = [truth[:, labels.index(name)].astype(bool)
                                     for name in ('amusement', 'embarrassment', 'remorse')]
    groups, inverse = np.unique(writers, return_inverse=True)

    def contrast(weight):
        a, b = [weighted_mean(amusement, mask, weight) for mask in (embarrassed, remorse)]
        return a, b, a-b

    point = contrast(np.ones(len(truth)))
    rng = np.random.default_rng(23)
    samples = []
    for i in range(draws):
        if i % 32 == 0:
            check()
        weight = np.bincount(rng.integers(len(groups), size=len(groups)), minlength=len(groups))[inverse]
        samples.append(contrast(weight)[2])
    return {'embarrassment_n': int(embarrassed.sum()), 'remorse_n': int(remorse.sum()),
            'amusement_with_embarrassment': point[0], 'amusement_with_remorse': point[1],
            'difference': point[2], 'interval': interval(samples, draws),
            'passes': bool(np.isfinite(point[2]) and point[2] > 0), 'writers': len(groups)}


def conclusions(stats, coefficients, reading4):
    def above(name, bar, interval_required=False):
        row = stats[name]
        return bool(row['estimate'] is not None and row['estimate'] > bar
                    and (not interval_required or row['interval'] is not None and row['interval'][0] > bar))
    one = above('fun_rate_ratio', 1, True)
    two = stats['play_gap_sd']['estimate'] is not None and stats['play_gap_sd']['estimate'] >= .2
    gain = stats['auc_gain']
    three = bool(gain['estimate'] is not None and gain['estimate'] >= .02
                 and gain['interval'] is not None and gain['interval'][0] > 0
                 and all(row['shame'] > 0 and row['play'] > 0 for row in coefficients))
    account_a = bool(one and two and three)
    account_b = above('appeasement_rate_ratio', 1, True)
    combined = {
        (True, False): "SHAME under PLAY's shield, as the curator states it.",
        (False, True): 'The published account (a feeling of its own, appeasing, apart from amusement).',
        (True, True): 'Both; the link to PLAY may run through yielding.',
        (False, False): 'Neither account is supported in text.',
    }
    return {'read1': one, 'read2': bool(two), 'read3': three, 'read4': reading4['passes'],
            'A_play_in_embarrassment': account_a, 'B_appeasement': account_b,
            'combined': combined[account_a, account_b], 'scope': 'Label test (R23), not a channel test'}


def run(corpus, ed_root, go_root, models, output, check, *, ledger, protocol):
    output = Path(output)
    ed, ed_pin = ed_situations(ed_root)
    go, go_y, go_labels, go_pin = go_comments(go_root)
    keep = (go.source_split != 'unreleased').to_numpy()
    go, go_y = go[keep], go_y[keep]
    data = load(corpus)
    receipt = {'card': 'TP29', 'status': 'running', 'productionAdmission': False,
               'ledger': ledger, 'scope': LIMIT, 'protocolPin': sha256(protocol),
               'protocol': {'fun': FUN, 'appeasement': APPEASE, 'draws': 2000, 'seed': 23,
                            'heads': 'Original frozen MiniLM cap128, logistic C3, balanced classes, max_iter2000',
                            'units': 'ED writers; Go authors, unknown authors are individual comments',
                            'calibration': 'five writer-disjoint folds; fitting-writer scaling; positive coefficients in every fold',
                            'uncertainty': '95% percentile whole-writer resamples of fixed predictions; no refits'},
               'sources': {'ed': ed_pin, 'go': go_pin, 'envent': data.summary()}, 'rows': {}}
    save = lambda: save_json(output/'receipt.json', receipt)
    save()
    x = {}
    for name, texts in (('go', go.text.tolist()), ('envent', data.reports.hidden_emo_text.tolist()), ('ed', ed.text.tolist())):
        check()
        save_json(output/'phase.json', {'phase': 'vectors', 'source': name, 'n': len(texts)})
        x[name], identity = saved_vectors(texts, Path(models), output/(name+'-vectors'), check)
        receipt.setdefault('vectors', {})[name] = {'n': len(texts), 'encoder': identity}
        save()
    check()
    save_json(output/'phase.json', {'phase': 'source-heads'})
    play = fit(x['go'], go_y[:, go_labels.index('amusement')], balanced=True)
    check()
    shame = fit(x['envent'], (data.reports.emotion == 'shame').to_numpy(int), balanced=True)
    np.savez(output/'heads.npz', play_w=play.coef_, play_b=play.intercept_, shame_w=shame.coef_, shame_b=shame.intercept_)
    scores = np.column_stack([expit(shame.decision_function(x['ed'])), expit(play.decision_function(x['ed']))])
    labels = ed.label.to_numpy(str)
    writers = ed.writer.to_numpy(str)
    counts = markers(ed.text)
    save_json(output/'phase.json', {'phase': 'held-out-calibration'})
    forecasts, assignment, coefficients = paired_calibration(scores, (labels == 'embarrassed').astype(int), writers, check)
    np.savez(output/'ed-forecasts.npz', ids=ed.id.to_numpy(str), writers=writers, labels=labels,
             markers=counts, source_scores=scores, forecasts=forecasts, folds=assignment)
    save_json(output/'phase.json', {'phase': 'writer-bootstrap'})
    stats = bootstrap_ed(counts, labels, scores, forecasts, writers, check)
    exposures = {label: {'situations': int((labels == label).sum()),
                         'words_fun_appeasement': counts[labels == label].sum(0).tolist()}
                 for label in ('embarrassed', 'ashamed')}
    receipt['rows'].update(ed=stats, coefficients=coefficients, marker_exposure=exposures)
    save()
    go_writers = np.asarray([str(w) if known else 'unknown-comment-'+str(ident)
                             for w, known, ident in zip(go.writer, go.writer_known, go.id)])
    fourth = co_labels(go_y, go_labels, go_writers, check)
    receipt['rows']['go'] = fourth
    receipt['verdict'] = conclusions(stats, coefficients, fourth)
    receipt.update(status='complete', artifactsPin=seal(output,
                   [output/'heads.npz', output/'ed-forecasts.npz', *[output/(s+'-vectors') for s in x]], check))
    save()
