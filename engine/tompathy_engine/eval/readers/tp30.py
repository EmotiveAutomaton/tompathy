"""Frozen soft rater-share profiles; source-held-out word-label tests only."""
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logsumexp, softmax, xlogy
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .artifacts import model_identity, seal
from .checkpoint import completed
from .envent import load
from .tp23 import saved_vectors
from .tp28 import MAP
from .tp29 import folds

CHANNELS = list(MAP)
PAIRS = list(combinations(range(9), 2))
WRITER_CHANNELS = [c for c in CHANNELS if c not in ('PLAY', 'LUST')]
LIMIT = 'Reader guesses and word stand-ins, not channel firing, page shares or maker needs. ED research-only; LUST is wanting in general. No serving admission.'


def label_matrix(labels, source):
    return np.asarray([[label in MAP[c][source] for c in CHANNELS] for label in labels], bool)


def aggregate_raters(ids, rater_ids, votes, labels, source, ordered_ids, check=lambda: None):
    """A rater counts once per mapped channel; original label sets define disagreement."""
    ids, rater_ids = np.asarray(ids, str), np.asarray(rater_ids, str)
    votes = np.asarray(votes)
    if (len(ids) != len(votes) or len(ids) != len(rater_ids) or
            not np.isin(votes, [0, 1]).all() or np.any(rater_ids == '') or
            len(set(zip(ids, rater_ids))) != len(ids)):
        raise ValueError('Invalid or duplicate rater rows')
    mapping = label_matrix(labels, source)
    mapped = (votes.astype(int) @ mapping.astype(int)) > 0
    unassigned = np.any(votes[:, ~mapping.any(1)] != 0, axis=1)
    positions = {str(ident): i for i, ident in enumerate(ordered_ids)}
    if len(positions) != len(ordered_ids) or not set(ids) <= set(positions):
        raise ValueError('Rater/report identity mismatch')
    n = len(positions)
    sums, pair_sums = np.zeros((n, 9)), np.zeros((n, len(PAIRS)))
    counts, other, empty, disagreement = [np.zeros(n) for _ in range(4)]
    groups = {}
    for r, ident in enumerate(ids):
        groups.setdefault(positions[ident], []).append(r)
    for i, rows in groups.items():
        if i % 256 == 0:
            check()
        counts[i] = len(rows)
        sums[i] = mapped[rows].mean(0)
        other[i] = unassigned[rows].mean()
        empty[i] = (~votes[rows].any(1)).mean()
        pair_sums[i] = [np.any(mapped[rows][:, [a, b]], axis=1).mean() for a, b in PAIRS]
        distances = []
        for a, b in combinations(rows, 2):
            union = np.count_nonzero(votes[a] | votes[b])
            distances.append(1-np.count_nonzero(votes[a] & votes[b])/union if union else 0.)
        disagreement[i] = np.mean(distances) if distances else np.nan
    return {'shares': sums, 'unassigned': other, 'empty': empty, 'raters': counts,
            'disagreement': disagreement, 'pair_support': pair_sums}


def intake(go_root, corpus, go, reports, labels, check=lambda: None):
    raw = pd.concat([pd.read_csv(Path(go_root)/f'goemotions_{i}.csv', keep_default_na=False,
        usecols=['id', 'rater_id', 'example_very_unclear', *labels]) for i in (1, 2, 3)], ignore_index=True)
    go_targets = aggregate_raters(raw.id, raw.rater_id, raw[labels].to_numpy(np.int8), labels, 'go', go.id, check)
    ev = pd.read_csv(Path(corpus)/'corpus/crowd-enVent_validation.tsv', sep='\t', quoting=3,
                     keep_default_na=False, usecols=['text_id', 'prolific_id', 'emotion'])
    ev_labels = sorted(ev.emotion.unique())
    ev_votes = np.asarray([[value == name for name in ev_labels] for value in ev.emotion], np.int8)
    ev_targets = aggregate_raters(ev.text_id, ev.prolific_id, ev_votes, ev_labels, 'envent', reports.text_id, check)
    if (len(raw) != 211225 or len(go) != 58011 or len(ev) != 6000 or
            np.count_nonzero(ev_targets['raters']) != 1200 or
            not np.all(ev_targets['raters'][ev_targets['raters'] > 0] == 5) or
            np.any(go_targets['raters'] < 1)):
        raise ValueError('Original rater census differs')
    return go_targets, ev_targets, {'go_ratings': len(raw), 'go_comments': len(go),
        'go_unclear_rows': int(raw.example_very_unclear.astype(str).str.lower().isin(['true', '1']).sum()),
        'go_single_rater_comments': int((go_targets['raters'] == 1).sum()),
        'envent_ratings': len(ev), 'envent_reread_reports': 1200}


def text_keys(texts):
    return np.asarray([hashlib.sha256(' '.join(str(t).casefold().split()).encode()).hexdigest() for t in texts])


def split(go, ed, reports, ev_raters):
    authors = np.asarray([str(w) if known else 'unknown-comment-'+str(ident)
                          for w, known, ident in zip(go.writer, go.writer_known, go.id)])
    assignment = folds(authors)
    test = assignment == 0
    g, e, v = [text_keys(texts) for texts in (go.text, ed.text, reports.hidden_emo_text)]
    blocked = set(e) | set(v) | set(g[test])
    train = ~test & ~np.isin(g, list(blocked))
    ev_train = (ev_raters > 0) & ~np.isin(v, list(set(e) | set(g[test])))
    if not train.any() or not test.any() or not ev_train.any():
        raise ValueError('Empty source-held-out partition')
    return train, test, ev_train, authors, assignment


def objective(theta, x, y, weights, kind):
    """C=3, weighted mean loss and sklearn-equivalent L2/N; intercept unpenalized."""
    d, k = x.shape[1], y.shape[1]
    params = theta.reshape(d+1, k)
    z = x @ params[:d]+params[d]
    if kind == 'sigmoid':
        loss = np.logaddexp(0, z)-y*z
        error = expit(z)-y
    else:
        loss = -y*z+logsumexp(z, axis=1)[:, None]*y
        error = softmax(z, axis=1)-y
    penalty = 1/(3*len(x))
    grad_z = error*weights[:, None]
    grad = np.vstack([x.T @ grad_z+penalty*params[:d], grad_z.sum(0)])
    return float(weights @ loss.sum(1)+penalty/2*np.sum(params[:d]**2)), grad.ravel()


def fit_head(x, targets, other, weights, check, kind):
    x, targets = np.asarray(x, float), np.asarray(targets, float)
    weights = np.asarray(weights, float)
    weights = weights/weights.sum()
    if not np.isfinite(x).all() or not np.isfinite(targets).all() or np.any((targets < 0) | (targets > 1)):
        raise ValueError('Finite soft targets in [0,1] required')
    supported = np.ptp(targets, axis=0) > 0
    if kind == 'sigmoid':
        y = targets[:, supported]
        active = np.flatnonzero(supported)
        constant = weights @ targets
    else:
        all_targets = np.column_stack([targets, other])
        one = all_targets.argmax(1)
        one[all_targets.sum(1) == 0] = 9
        active = np.unique(one)
        y = (one[:, None] == active).astype(float)
        constant = np.zeros(10)
    if y.shape[1] < 1:
        return np.zeros((x.shape[1]+1, 0)), active, constant, supported, 0
    if kind == 'softmax' and len(active) == 1:
        constant[active[0]] = 1
        return np.zeros((x.shape[1]+1, 0)), np.array([], int), constant, supported, 0
    def fun(theta):
        check()
        return objective(theta, x, y, weights, kind)
    result = minimize(fun, np.zeros((x.shape[1]+1)*y.shape[1]), jac=True, method='L-BFGS-B',
                      options={'maxiter': 2000, 'ftol': 1e-10, 'gtol': 1e-6, 'maxls': 50})
    if not result.success:
        raise RuntimeError(f'TP30 {kind} fixed objective did not converge: {result.message}')
    return result.x.reshape(x.shape[1]+1, -1), active, constant, supported, int(result.nit)


def predict(head, x, kind):
    parameters, active, constant, _, _ = head
    p = np.tile(constant, (len(x), 1))
    if len(active):
        z = np.asarray(x, float) @ parameters[:-1]+parameters[-1]
        p[:, active] = expit(z) if kind == 'sigmoid' else softmax(z, axis=1)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Invalid TP30 probabilities')
    return p[:, :9]


def auc_rows(truth, prediction, supported):
    return {name: {'positives': int(truth[:, j].sum()), 'n': len(truth),
                   'supported': bool(supported[j] and np.unique(truth[:, j]).size == 2),
                   'auc': float(roc_auc_score(truth[:, j], prediction[:, j]))
                   if supported[j] and np.unique(truth[:, j]).size == 2 else None}
            for j, name in enumerate(CHANNELS)}


def transfer_summary(rows):
    means = {}
    for name in WRITER_CHANNELS:
        cells = [(row['profile'][name]['auc'], row['control'][name]['auc']) for row in rows.values()]
        cells = [(a, b) for a, b in cells if a is not None and b is not None]
        means[name] = {'profile_auc': float(np.mean([a for a, _ in cells])) if cells else None,
                       'control_auc': float(np.mean([b for _, b in cells])) if cells else None,
                       'sources': len(cells)}
        means[name]['difference'] = float(np.mean([a-b for a, b in cells])) if cells else None
    passing = [c for c, r in means.items() if r['profile_auc'] is not None and r['profile_auc'] >= .70]
    return {'channels': means, 'passing': passing,
            'test1_passes': len(passing) >= 5 and bool(set(passing) & {'SEEKING', 'CARE'}),
            'test4_passes': all(r['difference'] is not None and r['difference'] >= -.01 for r in means.values())}


def mix(prediction, disagreement, pair_support):
    mass = prediction.sum(1, keepdims=True)
    q = np.divide(prediction, mass, out=np.zeros_like(prediction), where=mass > 0)
    spread = -xlogy(q, q).sum(1)/np.log(9)
    valid = np.isfinite(disagreement)
    corr = float(spearmanr(spread[valid], disagreement[valid]).statistic) if valid.sum() > 1 and np.ptp(spread[valid]) > 0 and np.ptp(disagreement[valid]) > 0 else None
    top = np.argsort(-prediction, axis=1, kind='stable')[:, :2]
    eligible = np.take_along_axis(prediction, top, axis=1).min(1) >= .25
    nominated = np.sort(top, axis=1)
    groups = []
    for index, pair in enumerate(PAIRS):
        mask = eligible & np.all(nominated == pair, axis=1)
        if mask.any():
            rates = pair_support[mask].mean(0)
            groups.append({'pair': [CHANNELS[j] for j in pair], 'n': int(mask.sum()),
                           'support_by_pair': rates.tolist(),
                           'passes': bool(rates[index] > np.max(np.delete(rates, index)))})
    return {'spread': 'normalized Shannon entropy', 'disagreement': 'original-label pairwise Jaccard distance',
            'spearman': corr, 'disagreement_defined': int(valid.sum()),
            'disagreement_undefined': int((~valid).sum()), 'correlation_passes': corr is not None and corr >= .20,
            'pair_order': [[CHANNELS[a], CHANNELS[b]] for a, b in PAIRS], 'groups': groups,
            'eligible': int(eligible.sum()), 'pairs_pass': bool(groups) and all(r['passes'] for r in groups)}


def co_rise(values):
    centered = values-values.mean(0)
    scale = np.sqrt((centered**2).sum(0))
    return [[float(centered[:, i] @ centered[:, j]/(scale[i]*scale[j]))
             if scale[i] > 1e-12 and scale[j] > 1e-12 else None for j in range(9)] for i in range(9)]


def reused_vectors(job, source, texts, receipt, files, check):
    """Read only manifest-bound completed vectors with exact original ordered input key."""
    root = Path(job)
    code = root/'code/tompathy_engine/eval/readers/tp23.py'
    identity = receipt['vectors'][source]['encoder']
    key = hashlib.sha256(json.dumps({'texts': list(texts), 'encoder': identity, 'code': sha256(code)}, sort_keys=True).encode()).hexdigest()
    if receipt['vectors'][source]['n'] != len(texts):
        raise ValueError('Completed vector input count changed')
    values = []
    for start in range(0, len(texts), 64):
        check()
        name = f'{source}-vectors/{start:07d}.npz'
        if name not in files or sha256(root/name) != files[name]:
            raise ValueError('Completed vector artifact changed')
        with np.load(root/name, allow_pickle=False) as data:
            value = data['values']
            if str(data['key']) != key or value.shape != (min(64, len(texts)-start), 384) or not np.isfinite(value).all():
                raise ValueError('Completed vector input/model/code binding changed')
            values.append(value)
    return np.concatenate(values), identity


def run(corpus, ed_root, go_root, models, output, check, *, source_job, protocol, ledger):
    output, source_job = Path(output), Path(source_job)
    source = completed(source_job, 'TP29')
    manifest = source_job/'artifact-manifest.json'
    if sha256(manifest) != source['artifactsPin']:
        raise ValueError('TP29 vector inventory changed')
    files = json.loads(manifest.read_text())['files']
    plan = json.loads((source_job/'plan.json').read_text())
    for name in ('tp23.py', 'encoders.py', 'affect_data.py', 'envent.py'):
        relative = 'tompathy_engine/eval/readers/'+name
        if sha256(source_job/'code'/relative) != plan['snapshotFiles'][relative]:
            raise ValueError('Original source helper snapshot changed')
        if name == 'encoders.py' and sha256(Path(__file__).with_name(name)) != plan['snapshotFiles'][relative]:
            raise ValueError('Fresh encoding must use the identical original feature helper')
    ed, ed_pin = ed_situations(ed_root)
    go, _, labels, go_pin = go_comments(go_root)
    ev = load(corpus)
    if source['sources'] != {'ed': ed_pin, 'go': go_pin, 'envent': ev.summary()}:
        raise ValueError('Original source intake changed')
    original_model = model_identity(Path(models)/'minilm', check)
    if any(any(row['encoder'].get(k) != v for k, v in original_model.items()) for row in source['vectors'].values()):
        raise ValueError('Original pretrained model changed')
    identities = [row['encoder'] for row in source['vectors'].values()]
    if not identities or any(identity != identities[0] for identity in identities):
        raise ValueError('Completed source vectors use different encoder identities')
    receipt = {'card': 'TP30-frozen', 'status': 'running', 'productionAdmission': False, 'ledger': ledger,
        'scope': LIMIT, 'protocolPin': sha256(protocol), 'sources': source['sources'], 'map': MAP,
        'vectorSourceReceiptPin': sha256(source_job/'receipt.json'), 'rows': {},
        'protocol': {'rung': 'frozen', 'channels': CHANNELS, 'seed': 23, 'tokenCap': 128,
                     'split': 'Go author fold zero held out; exact text overlaps excluded from training',
                     'uncertainty': 'Point-estimate bars; no additional interval qualification',
                     'heads': 'C3-equivalent L2, unpenalized intercept, maxiter2000 ftol1e-10 gtol1e-6',
                     'sourceWeight': 'equal total weight for Go/Crowd in ED prediction'}}
    save = lambda: save_json(output/'receipt.json', receipt)
    phase = lambda name: save_json(output/'phase.json', {'phase': name})
    save()
    phase('rater-intake')
    gy, vy, census = intake(go_root, corpus, go, ev.reports, labels, check)
    train, test, ev_train, authors, assignment = split(go, ed, ev.reports, vy['raters'])
    receipt['intake'] = {**census, 'go_train': int(train.sum()), 'go_test': int(test.sum()),
        'go_overlap_excluded': int((~test & ~train).sum()), 'envent_train': int(ev_train.sum()),
        'envent_overlap_excluded': int(((vy['raters'] > 0) & ~ev_train).sum()),
        'go_unassigned_mean': float(gy['unassigned'].mean()), 'go_empty_mean': float(gy['empty'].mean()),
        'envent_unassigned_mean': float(vy['unassigned'][vy['raters'] > 0].mean())}
    np.savez(output/'go-targets.npz', ids=go.id.to_numpy(str), authors=authors, folds=assignment,
             train=train, test=test, **gy)
    np.savez(output/'envent-targets.npz', ids=ev.reports.text_id.to_numpy(str), train=ev_train, **vy)
    save()
    phase('reuse-completed-vectors')
    ed_x, identity = reused_vectors(source_job, 'ed', ed.text.tolist(), source, files, check)
    ev_x, _ = reused_vectors(source_job, 'envent', ev.reports.hidden_emo_text.tolist(), source, files, check)
    released = (go.source_split != 'unreleased').to_numpy()
    old_go, _ = reused_vectors(source_job, 'go', go.loc[released, 'text'].tolist(), source, files, check)
    go_x = np.empty((len(go), 384), np.float32)
    go_x[released] = old_go
    del old_go
    phase('encode-new-go-only')
    extra, extra_identity = saved_vectors(go.loc[~released, 'text'].tolist(), Path(models), output/'new-go-vectors', check)
    if extra_identity != identity:
        raise ValueError('New and reused vector encoder identity differs')
    go_x[~released] = extra
    receipt['vectors'] = {'encoder': identity, 'reused_ed': len(ed), 'reused_envent': len(ev.reports),
                         'reused_go': int(released.sum()), 'new_go': int((~released).sum())}
    np.savez(output/'vectors.npz', ed=ed_x, envent=ev_x, go=go_x)
    save()
    views = [('go_only', go_x[train], gy['shares'][train], gy['unassigned'][train], np.ones(train.sum())),
             ('go_plus_envent', np.concatenate([go_x[train], ev_x[ev_train]]),
              np.concatenate([gy['shares'][train], vy['shares'][ev_train]]),
              np.concatenate([gy['unassigned'][train], vy['unassigned'][ev_train]]),
              np.r_[np.full(train.sum(), .5/train.sum()), np.full(ev_train.sum(), .5/ev_train.sum())])]
    source_rows = {}
    for view, x, y, other, weights in views:
        outputs = {}
        for kind, label in [('sigmoid', 'profile'), ('softmax', 'control')]:
            phase(view+'-'+label+'-fit')
            head = fit_head(x, y, other, weights, check, kind)
            np.savez(output/f'{view}-{label}-head.npz', parameters=head[0], active=head[1],
                     constants=head[2], supported=head[3], iterations=head[4])
            targets = [('envent', ev_x, label_matrix(ev.reports.emotion, 'envent')),
                       ('go', go_x[test], gy['shares'][test] > .5)] if view == 'go_only' else [('ed', ed_x, label_matrix(ed.label, 'ed'))]
            for name, vectors, truth in targets:
                check()
                p = predict(head, vectors, kind)
                outputs[(name, label)] = p
                ids = {'ed': ed.id.to_numpy(str), 'envent': ev.reports.text_id.to_numpy(str),
                       'go': go.loc[test, 'id'].to_numpy(str)}[name]
                np.savez(output/f'{name}-{label}-forecasts.npz', ids=ids, probabilities=p, truth=truth)
                row = auc_rows(truth, p, head[3])
                if name == 'go':
                    receipt['rows'].setdefault('within_source', {})[label] = row
                else:
                    source_rows.setdefault(name, {})[label] = row
        receipt['rows']['across_sources'] = source_rows
        if view == 'go_only':
            phase('held-out-go-diagnostics')
            prediction = outputs['go', 'profile']
            receipt['rows']['mix'] = mix(prediction, gy['disagreement'][test], gy['pair_support'][test])
            receipt['rows']['co_rise'] = {'channels': CHANNELS, 'n': int(test.sum()),
                                         'predicted': co_rise(prediction), 'reader_shares': co_rise(gy['shares'][test])}
        save()
    receipt['rows']['summary'] = transfer_summary(source_rows)
    receipt['status'] = 'complete'
    phase('seal')
    receipt['artifactsPin'] = seal(output, [*output.glob('*.npz'), output/'new-go-vectors'], check)
    save()
