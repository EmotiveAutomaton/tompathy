"""TP12: cross-half quantification, frozen policy selection and neutral stress."""
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from ...packs.aggregate import correct, error_table
from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .envent import load
from .metrics import confusion

SEED = 20261115
SIZES = (20, 60, 200)
PRIORS = (1, 2, 4)


def conditional(value, neutral):
    value = np.delete(np.asarray(value, float), neutral)
    return value/value.sum() if value.sum() > 1e-12 else None


def em_probabilities(probabilities, training_prior, *, iterations=300):
    """Prior-shift EM on a head's probabilities; no labels from the bag."""
    p = np.asarray(probabilities, float)
    prior = np.asarray(training_prior, float)
    if (p.ndim != 2 or (prior <= 0).any() or p.shape[1] != len(prior)
            or not np.allclose(p.sum(axis=1), 1)):
        raise ValueError('Invalid EM probabilities/prior')
    likelihood = p / prior
    mix = prior.copy()
    for _ in range(iterations):
        posterior = likelihood * mix
        posterior /= posterior.sum(axis=1, keepdims=True)
        updated = posterior.mean(axis=0)
        if np.max(np.abs(updated-mix)) < 1e-8:
            return updated
        mix = updated
    return mix


def em_counts(counts, table):
    """The supplied preflight's error-table EM when no head probabilities exist."""
    mix = np.full(len(counts), 1/len(counts))
    for _ in range(300):
        posterior = table * mix[:, None]
        posterior /= posterior.sum(axis=0, keepdims=True)
        updated = (posterior*counts[None, :]).sum(axis=1) + 1e-9
        updated /= updated.sum()
        if np.max(np.abs(updated-mix)) < 1e-8:
            return updated
        mix = updated
    return mix


def verify_preflight(root):
    """Compare every printed numeric cell, retaining both exact output pins."""
    root = Path(root)
    supplied = root/'bench/readers-preflight-20261115/PREFLIGHT_2026-11-14/corpus/out/pf_c2.txt'
    reproduced = root/'bench/readers-preflight-run-20261115-b/pf_c2.txt'
    verification = json.loads((reproduced.parent/'exit-verification.json').read_text(encoding='utf8'))
    if not all(verification.get(k) for k in ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent')):
        raise ValueError('Preflight release/exit not verified')
    numbers = lambda p: np.array([float(n) for n in re.findall(r'(?<![A-Za-z])\d+\.\d+', p.read_text(encoding='utf8'))])
    a, b = numbers(supplied), numbers(reproduced)
    if len(a) != len(b) or not len(a) or np.max(np.abs(a-b)) > .005:
        raise ValueError('pf_c2 reproduction outside 0.005 tolerance')
    return {'passed': True, 'maximumPrintedDifference': float(np.max(np.abs(a-b))),
        'cells': len(a), 'suppliedPin': sha256(supplied), 'reproducedPin': sha256(reproduced)}


def summarize(values):
    # Split means, not the correlated bags, are the uncertainty units.
    means = np.asarray([np.mean(rows, axis=0) for _, rows in sorted(values.items())])
    rng = np.random.default_rng(SEED)
    resamples = np.array([means[rng.integers(len(means), size=len(means))].mean(axis=0)
                          for _ in range(1000)])
    bounds = np.quantile(resamples, [.025, .975], axis=0)
    average = means.mean(axis=0)
    return {'mae': float(average[0]), 'top1': float(average[1]),
        'undefined': float(average[2]), 'mae_interval': bounds[:,0].tolist(),
        'top1_interval': bounds[:,1].tolist(), 'splits': len(means),
        'bags': sum(len(rows) for rows in values.values()),
        'interval_method': '1000 resamples of split means; repeated halves are not independent new corpora'}


def policy_for(rows):
    """Declared rule: minimize mean MAE across all ordinary scenarios, no stress fitting.

    Smallest minimum where neither mixture shape loses MAE or top-label accuracy
    against raw counts at any tested neutral fraction; otherwise withhold policy.
    """
    ordinary = [r for r in rows if r['neutralSource'] == 'corpus']
    prior = min(PRIORS, key=lambda a: np.mean([r['mae'] for r in ordinary if r['estimator'] == f'nnls-alpha-{a}']))
    minimum = None
    for size in SIZES:
        chosen = [r for r in ordinary if r['size'] == size and r['estimator'] == f'nnls-alpha-{prior}']
        ok = True
        for row in chosen:
            raw = next(r for r in ordinary if r['size'] == size and r['mixture'] == row['mixture']
                       and r['neutralFraction'] == row['neutralFraction'] and r['estimator'] == 'raw')
            ok &= row['mae'] <= raw['mae'] and row['top1'] >= raw['top1'] and row['undefined'] == 0
        if chosen and ok:
            minimum = size
            break
    return {'card': 'TP12', 'status': 'complete' if minimum is not None else 'no-policy-qualified',
        'prior': prior, 'minimum': minimum, 'bootstrap': 1000, 'seed': SEED,
        'selection': 'Minimum average MAE over corpus-only scenarios; smallest tested count with no MAE/top1 loss against raw in either shape at any neutral fraction',
        'productionAdmission': False}


def run(directory, ladder, output, check, *, fine_tuned=False, reference=None):
    output, ladder = Path(output), Path(ladder)
    verification = json.loads((ladder/'exit-verification.json').read_text(encoding='utf8'))
    if not all(verification.get(k) for k in ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent')):
        raise ValueError('TP10 must exit and release before TP12')
    corpus = load(directory)
    k, neutral = len(corpus.labels), corpus.labels.index('no-emotion')
    y = corpus.reports.iloc[corpus.test].y.to_numpy()
    ids = corpus.reports.iloc[corpus.test].text_id
    label_index = dict(zip(corpus.labels, range(k)))
    human = {ident: group.emotion.map(label_index).to_numpy() for ident, group in corpus.judgments.groupby('text_id')}
    votes = np.array([human[i] for i in ids])
    if votes.shape != (1200, 5):
        raise ValueError('Five judgments required for every report')
    author_path = min(Path(directory).glob('predictions/TEmodel_classifier_*.tsv'))
    authors = pd.read_csv(author_path, sep='\t').set_index('text_id').loc[ids].predicted_emotion.map(label_index).to_numpy()
    receipt = json.loads((ladder/'receipt.json').read_text(encoding='utf8'))
    expected_status='complete' if fine_tuned else 'L0-L2 complete; L3 and final pack gates pending'
    if receipt['scope'] != corpus.summary() or receipt['status'] != expected_status:
        raise ValueError('TP10 split or completion differs')
    report = {'card': 'TP12-L3' if fine_tuned else 'TP12', 'status': 'running', 'preflight': verify_preflight(Path('.local')),
        'ladderReceiptPin': sha256(ladder/'receipt.json'), 'authorFilePin': sha256(author_path),
        'scope': corpus.summary(), 'seed': SEED, 'halves': 20, 'bagsPerScenarioPerHalf': 60,
        'labels': corpus.labels, 'rows': {}, 'policies': {}, 'productionAdmission': False,
        'estimand': 'Label shares conditional on emotion, after correction of all 13 labels including neutral',
        'design': 'Dirichlet(1) or Dirichlet(.15) over 12 emotion labels; fixed neutral fraction; common bags across readers',
        'unpacked': True, 'neutralStress': 'Available B13 and verified before-revision sentences only; reference readers have no released predictions on these sets'}
    save_json(output/'receipt.json', report)
    train_counts = np.bincount(corpus.reports.iloc[corpus.train].y, minlength=k)
    prior = train_counts/train_counts.sum()
    readers = {} if fine_tuned else {'human': None, 'authors-first-released': None}
    if fine_tuned:
        from .checkpoint import completed
        completed(ladder,'TP10-L3')
        previous=completed(reference,'TP12')
        report['carriedControls']={'sourceReceiptPin':sha256(Path(reference)/'receipt.json'),
            'bars':{k:v for k,v in previous['bars'].items() if k in {'constant','bow','human','authors-first-released'}},
            'scope':'Previously completed reference rows reused unchanged; only the new L3 head is measured'}
        seed=receipt['selected_seed']
        path=ladder/f'seed-{seed}/predictions.npz'
        if sha256(path)!=receipt['rows'][str(seed)]['files']['predictions.npz']:
            raise ValueError('L3 prediction binding differs')
        paths={'minilm-tuned':path}
    else:
        paths={name:ladder/(name+'-predictions.npz') for name in receipt['rows']}
    for name,path in paths.items():
        with np.load(path, allow_pickle=False) as data:
            if not np.array_equal(data['y'], y):
                raise ValueError('TP10 prediction order differs')
            readers[name] = {key: data[key] for key in ('test_probabilities', 'theme_probabilities', 'revision_probabilities')}
    for name, data in readers.items():
        check()
        save_json(output/'phase.json', {'reader': name, 'half': 0})
        accum = defaultdict(lambda: defaultdict(list))
        for split in range(20):
            check()
            save_json(output/'phase.json', {'reader': name, 'half': split+1})
            rng = np.random.default_rng(SEED + split)
            prediction_rng = np.random.default_rng(SEED + 2000 + split)
            perm = rng.permutation(len(y))
            a, b = perm[:len(y)//2], perm[len(y)//2:]
            by_label = [b[y[b] == label] for label in range(k)]
            if any(not len(v) for v in by_label):
                raise ValueError('Cross-half sample missing label; preserve failure instead of redrawing')
            if name == 'human':
                predicted_a = votes[a, prediction_rng.integers(0, 5, len(a))]
            elif name == 'authors-first-released':
                predicted_a = authors[a]
            else:
                predicted_a = data['test_probabilities'][a].argmax(axis=1)
            matrix = error_table(confusion(y[a], predicted_a, k), .5)
            rng = np.random.default_rng(SEED + 1000 + split)
            feeling = np.delete(np.arange(k), neutral)
            for concentration, mixture in ((1., 'flat'), (.15, 'peaked')):
                for size in SIZES:
                    for fraction in (0., .5, .8):
                        check()
                        for _ in range(60):
                            emotion_n = size-round(size*fraction)
                            mixture_p = rng.dirichlet(np.full(k-1, concentration))
                            classes = np.r_[rng.choice(feeling, size=emotion_n, p=mixture_p),
                                            np.full(size-emotion_n, neutral)]
                            bag = np.array([rng.choice(by_label[c]) for c in classes])
                            truth = conditional(np.bincount(classes, minlength=k), neutral)
                            if name == 'human':
                                prediction = votes[bag, prediction_rng.integers(0, 5, size)]
                                probabilities = None
                            elif name == 'authors-first-released':
                                prediction, probabilities = authors[bag], None
                            else:
                                probabilities = data['test_probabilities'][bag]
                                prediction = probabilities.argmax(axis=1)
                            scenarios = [('corpus', prediction, probabilities)]
                            if data is not None and fraction:
                                for source, field in (('B13', 'theme_probabilities'), ('IteraTeR-before', 'revision_probabilities')):
                                    external = data[field]
                                    if len(external):
                                        q = probabilities.copy()
                                        q[emotion_n:] = external[prediction_rng.integers(len(external), size=size-emotion_n)]
                                        scenarios.append((source, q.argmax(axis=1), q))
                            for source, pred, probs in scenarios:
                                counts = np.bincount(pred, minlength=k)
                                estimates = {'raw': counts/size}
                                estimates.update({f'nnls-alpha-{alpha}': correct(counts, matrix, alpha-1) for alpha in PRIORS})
                                estimates['em-head' if probs is not None else 'em-error-table'] = (
                                    em_probabilities(probs, prior) if probs is not None else em_counts(counts, matrix))
                                for method, estimate in estimates.items():
                                    value = conditional(estimate, neutral)
                                    # Undefined conditional outputs are failures, not silently dropped bags.
                                    scores = (1., 0., 1.) if value is None else (
                                        float(np.abs(value-truth).mean()), float(value.argmax() == truth.argmax()), 0.)
                                    accum[(source, mixture, size, fraction, method)][split].append(scores)
        rows = [{'neutralSource': key[0], 'mixture': key[1], 'size': key[2], 'neutralFraction': key[3],
                 'estimator': key[4], **summarize(value)} for key,value in accum.items()]
        report['rows'][name] = rows
        policy = policy_for(rows)
        policy.update(reader=name, ladderReceiptPin=report['ladderReceiptPin'])
        report['policies'][name] = policy
        save_json(output/(name+'-policy.json'), policy)
        save_json(output/'receipt.json', report)
    report['status'] = 'complete'
    report['bars'] = {}
    for name, rows in report['rows'].items():
        primary = [r for r in rows if r['neutralSource'] == 'corpus' and r['mixture'] == 'peaked'
                   and r['size'] == 60 and r['neutralFraction'] == 0 and r['estimator'] != 'raw']
        best = min(primary, key=lambda r: r['mae'])
        report['bars'][name] = {'bestEstimator': best['estimator'], 'mae': best['mae'], 'top1': best['top1'],
            'passed': best['mae'] <= .040 and best['top1'] >= .79,
            'stretch': best['mae'] <= .033 and best['top1'] >= .83}
    save_json(output/'receipt.json', report)
    return report
