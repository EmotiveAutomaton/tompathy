"""TP23 per-rung jobs. Fixed five outer story folds and untouched transfer bars."""
import gc
import json
import shutil
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score

from ...packs.registry import sha256
from ...packs.trigger import TAGS
from ..back_half.reporting import save_json
from .artifacts import model_identity, seal, verified
from .encoders import load_encoder
from .envent import load as envent
from .need_transfer import transfer
from .preflight_scope import reproduction as verify_reproduction
from .story import development, load, people
from .tag_training import fit as fine_fit
from .tag_training import predict as fine_predict


def sigmoid(x):
    return 1/(1+np.exp(-np.clip(x, -700, 700)))


def thresholds(y, scores):
    """Inner-development F1, grid fixed before scoring, highest threshold on ties."""
    p = sigmoid(scores)
    grid = np.arange(.05, 1, .05)
    return np.asarray([max(grid, key=lambda t: (f1_score(y[:, j], p[:, j] >= t, zero_division=0), t))
                       for j in range(y.shape[1])])


def heads(x, y, check):
    models = []
    for j in range(y.shape[1]):
        check()
        if len(np.unique(y[:, j])) != 2:
            raise ValueError('A tag has no fitting contrast')
        m = LogisticRegression(C=3, max_iter=2000, class_weight='balanced').fit(x, y[:, j])
        if np.any(m.n_iter_ >= m.max_iter):
            raise RuntimeError('Tag optimizer did not converge')
        models.append(m)
    return models


def score(models, x):
    return np.column_stack([m.decision_function(x) for m in models])


def saved_vectors(texts, models, output, check, *, shared=None, source=None, corpus=None):
    """Durable 64-row batches; all input/code/model pins bind every saved batch."""
    if shared is not None or source is not None:
        from .vector_cache import vectors
        return vectors(texts, models, output, check, shared=shared, source=source, corpus=corpus)
    encode, identity = load_encoder(models/'minilm', 'minilm', cap=128)
    # Generic vectors have a separate cache rather than scalar batch semantics.
    import hashlib
    key = hashlib.sha256(json.dumps({'texts': texts, 'encoder': identity, 'code': sha256(__file__)}, sort_keys=True).encode()).hexdigest()
    output.mkdir(exist_ok=True)
    result = []
    for i in range(0, len(texts), 64):
        check()
        path = output/f'{i:07d}.npz'
        if path.exists():
            with np.load(path, allow_pickle=False) as d:
                if str(d['key']) != key:
                    raise ValueError('Embedding source changed')
                value = d['values']
        else:
            value = encode(texts[i:i+64])
            np.savez(path, key=key, values=value)
        if value.shape != (len(texts[i:i+64]), 384) or not np.isfinite(value).all():
            raise ValueError('Invalid durable vectors')
        result.append(value)
    del encode
    gc.collect()
    return np.concatenate(result), identity


def run(root, corpus, models, output, check, *, rung='bow', seed=23, bundle=None, fold=None, fold_jobs=(), preflight_job=None, vector_cache=None, vector_source=None, preflight_decision=None):
    root, models, output = Path(root), Path(models), Path(output)
    frame, y, humans, folds, source = load(root, check)
    ev = envent(corpus)
    texts, groups = frame.text.tolist(), frame.story.to_numpy()
    card = 'TP23-'+rung+(f'-{seed}' if rung == 'fine' else '')
    trained = rung in {'fine', 'base'}
    model_root = models/('base' if rung == 'base' else 'minilm')
    if rung == 'base' and seed != 23:
        raise ValueError('The optional base rung has one predeclared seed, 23')
    if trained and ((fold is None and len(fold_jobs) != 5) or (fold is not None and fold_jobs)):
        raise ValueError('Fine rung uses five separately bounded fold jobs, then one full-data/aggregation job')
    if fold is not None and (not trained or fold not in range(5)):
        raise ValueError('Only the five preplanned fine-fold jobs may use --fold')
    receipt = {'card': card+(f'-fold-{fold}' if fold is not None else ''), 'status': 'running',
        'productionAdmission': False, 'ledger': 'no ledger row', 'source': source,
        'scope': 'Character-line motive tags; proposed need map, no maker inference',
        'protocol': {'rung': rung, 'seed': seed, 'outer': 'original GroupKFold(5), story disjoint',
            'inner': 'lowest SHA256 tenth of training stories; fixed before labels',
            'fine': 'three epochs, '+('base seed23' if rung == 'base' else 'MiniLM seeds23/47/71')+'; inner-dev AUC selection, no outer-fold tuning',
            'bar': {'story_auc': None if rung == 'bow' else .76, 'transfer_mean_gain': .06, 'transfer_pairs_ge_03': 4},
            'packing': 'All rungs including BOW must pass both transfer bars. The .76 story bar is the encoder bar; BOW reports story AUC as its control. N5 hidden; unmapped labels unassigned'},
        'people': people(humans), 'folds': [], 'pack': None}
    save = lambda: save_json(output/'receipt.json', receipt)
    if trained:
        receipt['encoder'] = model_identity(model_root, check)
        if rung == 'base' and receipt['encoder']['id'] != 'sentence-transformers/all-mpnet-base-v2':
            raise ValueError('Optional base encoder differs from predeclared source')
    if rung != 'bow':
        if preflight_job is None:
            raise ValueError('The ladder requires completed BOW preflight reproduction first')
        reproduction, _ = verified(preflight_job, 'TP23-bow', check)
        if reproduction['source'] != source:
            raise ValueError('BOW preflight/source does not qualify the ladder prerequisites')
        receipt['preflightScope'] = verify_reproduction(preflight_job, reproduction, preflight_decision)
        receipt['preflightSourcePin'] = sha256(Path(preflight_job)/'receipt.json')
    save()
    del humans
    vectors = ev_vectors = None
    if rung == 'frozen':
        reuse = {'shared': vector_cache, 'source': vector_source, 'corpus': corpus} if vector_cache or vector_source else {}
        vectors, identity = saved_vectors(texts, models, output/'story-vectors', check, **reuse)
        ev_vectors, _ = saved_vectors(ev.reports.hidden_emo_text.tolist(), models, output/'envent-vectors', check, **reuse)
        receipt['encoder'] = identity
        save()
    oof, decisions = np.full(y.shape, np.nan), np.zeros(y.shape, dtype=bool)
    per_fold, cutoffs, dev_scores = [], [], []
    for fold_index, (train, test) in enumerate(folds):
        if fold is not None and fold_index != fold:
            continue
        check()
        fit, dev = development(train, groups)
        dest = output/f'fold-{fold_index}'
        save_json(output/'phase.json', {'phase': 'story-fold', 'fold': fold_index, 'rung': rung, 'seed': seed})
        if fold_jobs:
            source_job = Path(fold_jobs[fold_index])
            original, _ = verified(source_job, card+f'-fold-{fold_index}', check)
            if original['source'] != source or original['protocol'] != receipt['protocol'] or original['encoder'] != receipt['encoder']:
                raise ValueError('Fine fold data or training protocol changed')
            source_fold = source_job/f'fold-{fold_index}'
            dest.mkdir()
            shutil.copyfile(source_fold/'predictions.npz', dest/'predictions.npz')
            if sha256(source_fold/'predictions.npz') != sha256(dest/'predictions.npz'):
                raise ValueError('Completed fold copy differs')
            with np.load(dest/'predictions.npz', allow_pickle=False) as d:
                if not np.array_equal(d['test'], test) or not np.array_equal(d['truth'], y[test]):
                    raise ValueError('Completed fold order differs')
                prediction, cutoff = d['logits'], d['threshold']
            row = original['folds'][0]
            dev_auc = row['development_auc']
            receipt.setdefault('foldSources', []).append(sha256(source_job/'receipt.json'))
        elif trained:
            model, dev_auc = fine_fit(model_root, texts, y, fit, dev, dest, seed, check)
            with np.load(dest/'development.npz', allow_pickle=False) as d:
                if not np.array_equal(d['index'], dev):
                    raise ValueError('Development selection differs')
                validation = d['logits']
            prediction = fine_predict(model, [texts[i] for i in test], check, output=dest/'test-batches', identity=sha256(dest/'best.safetensors'))
            del model
        else:
            if rung == 'bow':
                v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
                x = v.fit_transform([texts[i] for i in train])
                xt = v.transform([texts[i] for i in test])
                # Match the supplied preflight fit on all outer-training rows.
                fitted = heads(x, y[train], check)
                prediction = score(fitted, xt)
                inner = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
                inner_model = heads(inner.fit_transform([texts[i] for i in fit]), y[fit], check)
                validation = score(inner_model, inner.transform([texts[i] for i in dev]))
            elif rung == 'frozen':
                fitted = heads(vectors[train], y[train], check)
                prediction = score(fitted, vectors[test])
                validation = score(heads(vectors[fit], y[fit], check), vectors[dev])
            else:
                raise ValueError('Unknown TP23 rung')
            dest.mkdir()
            dev_auc = float(np.mean([roc_auc_score(y[dev, j], validation[:, j]) for j in range(len(TAGS)) if len(np.unique(y[dev, j])) == 2]))
        if not fold_jobs:
            cutoff = thresholds(y[dev], validation)
        cutoffs.append(cutoff)
        dev_scores.append(dev_auc)
        oof[test] = prediction
        decisions[test] = sigmoid(prediction) >= cutoff
        auc = [float(roc_auc_score(y[test, j], prediction[:, j])) if len(np.unique(y[test, j])) == 2 else None for j in range(len(TAGS))]
        per_fold.append(auc)
        row = {'fold': fold_index, 'fitting': len(fit) if trained else len(train), 'test': len(test),
               'development': len(dev), 'development_auc': dev_auc, 'auc': dict(zip(TAGS, auc)), 'thresholds': cutoff.tolist()}
        np.savez(dest/'predictions.npz', test=test, truth=y[test], logits=prediction, threshold=cutoff)
        receipt['folds'].append(row)
        save()
        gc.collect()
    if fold is not None:
        receipt.update(status='complete', artifactsPin=seal(output, [output/f'fold-{fold}'], check))
        save()
        return
    np.savez(output/'heldout.npz', truth=y, logits=oof, decisions=decisions)
    means = np.nanmean(np.asarray(per_fold, float), axis=0)
    receipt['story'] = {'mean_auc': float(means.mean()), 'auc': dict(zip(TAGS, map(float, means))),
        'reader_f1': dict(zip(TAGS, map(float, f1_score(y, decisions, average=None, zero_division=0)))),
        'development_auc': float(np.mean(dev_scores)), 'thresholds': np.mean(cutoffs, axis=0).tolist()}
    save()
    save_json(output/'phase.json', {'phase': 'full-data-tag-head', 'rung': rung})
    if trained:
        model, _ = fine_fit(model_root, texts, y, np.arange(len(y)), np.array([], int), output/'full-head', seed, check, final=True)
        needs = fine_predict(model, ev.reports.hidden_emo_text.tolist(), check,
                             output=output/'transfer-batches', identity=sha256(output/'full-head/best.safetensors'))
        del model
    else:
        if rung == 'bow':
            v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
            x = v.fit_transform(texts)
            fitted = heads(x, y, check)
            needs = score(fitted, v.transform(ev.reports.hidden_emo_text))
            save_json(output/'vocabulary.json', {'vocabulary': {k: int(n) for k, n in v.vocabulary_.items()}, 'idf': v.idf_.tolist(), 'ngram': [1, 2], 'sublinear_tf': True})
        else:
            fitted = heads(vectors, y, check)
            needs = score(fitted, ev_vectors)
        np.savez(output/'head.npz', weights=np.concatenate([m.coef_ for m in fitted]), bias=np.concatenate([m.intercept_ for m in fitted]))
    np.savez(output/'envent-tags.npz', text_id=ev.reports.text_id.to_numpy(), logits=needs, scores=sigmoid(needs))
    receipt['transfer'] = transfer(ev.reports, needs, check, words=rung == 'bow')
    receipt['qualifies'] = (rung == 'bow' or receipt['story']['mean_auc'] >= .76) and receipt['transfer']['transfer_passed']
    if rung == 'bow':
        expected = json.loads((Path(bundle)/'engine/pf_need_out.json').read_text(encoding='utf8'))
        differences = {'story_mean_auc': abs(receipt['story']['mean_auc']-expected['story_commonsense']['mean_auc'])}
        for tag, value in receipt['story']['auc'].items():
            differences['story:'+tag] = abs(value-expected['story_commonsense']['held_out_story_auc'][tag])
        for name, value in receipt['transfer']['thirteen_labels_macro_f1'].items():
            differences['macro_f1:'+name] = abs(value-expected['thirteen_labels_macro_f1'][name])
        for pair, row in receipt['transfer']['twins'].items():
            for name in ('ratings', 'needs', 'ratings+needs', 'words'):
                differences[pair+':'+name] = abs(row[name]-expected['twins'][pair][name])
        receipt['preflight'] = {'absolute_differences': differences, 'tolerance': .02,
                                'reproduced': all(v <= .02 for v in differences.values()), 'sourcePin': sha256(Path(bundle)/'engine/pf_need_out.json')}
    receipt['status'] = 'complete'
    receipt['pack'] = 'await combined rung selection and verified export' if receipt['qualifies'] else None
    required = [output/'heldout.npz', output/'envent-tags.npz']
    required += [output/'full-head'] if trained else [output/'head.npz']
    if rung == 'bow':
        required.append(output/'vocabulary.json')
    receipt['artifactsPin'] = seal(output, required, check)
    save()
