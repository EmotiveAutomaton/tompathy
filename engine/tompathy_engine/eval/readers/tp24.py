"""TP24 text-only slot comparisons and explicitly non-blind fixed trigger table."""
import gc
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from ...packs.registry import sha256
from ...packs.trigger import AHEAD, ALREADY, FEATURES, TAG_MAP, table_scores, tense
from ..back_half.reporting import save_json
from .artifacts import seal, verified
from .checkpoint import load_head
from .envent import RATINGS, load
from .need_transfer import PAIRS, fit_scaled
from .tp23 import saved_vectors

LOSS = ('anger', 'fear', 'sadness', 'shame', 'disgust')


def forecasts(x, y, groups, check):
    labels = sorted(set(y))
    prediction = np.empty(len(y), dtype=object)
    probabilities = np.zeros((len(y), len(labels)))
    for train, test in GroupKFold(5).split(x, y, groups):
        model, xt = fit_scaled(x, y, train, test, check)
        prediction[test] = model.predict(xt)
        if list(model.classes_) != labels:
            raise ValueError('Classification fold lacks a label')
        probabilities[test] = model.predict_proba(xt)
    return prediction.astype(str), probabilities, labels


def evaluate(x, labels, writers, check):
    pred, p, classes = forecasts(x, labels, writers, check)
    result = {'macro_f1': float(f1_score(labels, pred, average='macro')), 'twins': {}}
    for pair in PAIRS:
        a, b = pair.split('-')
        ids = np.flatnonzero(np.isin(labels, [a, b]))
        _, probability, names = forecasts(x[ids], labels[ids], writers[ids], check)
        result['twins'][pair] = float(roc_auc_score(labels[ids] == a, probability[:, names.index(a)]))
    ids = np.flatnonzero(np.isin(labels, LOSS))
    chosen, _, _ = forecasts(x[ids], labels[ids], writers[ids], check)
    result['five_way'] = {'n': len(ids), 'accuracy': float(accuracy_score(labels[ids], chosen)),
                          'labels': list(LOSS), 'confusion': confusion_matrix(labels[ids], chosen, labels=list(LOSS)).tolist()}
    return result, p, classes


def run(corpus, reader_job, needs_job, models, output, check, *, vector_cache=None, vector_source=None):
    output, needs_job, reader_job = Path(output), Path(needs_job), Path(reader_job)
    needs_receipt = json.loads((needs_job/'receipt.json').read_text(encoding='utf8'))
    if not needs_receipt['card'].startswith('TP23-'):
        raise ValueError('A TP23 source is required')
    needs_receipt, _ = verified(needs_job, needs_receipt['card'], check)
    receipt = {'card': 'TP24', 'status': 'running', 'productionAdmission': False, 'ledger': 'no ledger row',
        'scope': 'Text-derived slots; proposed non-blind trigger table, not writer need levels',
        'needsReceiptPin': sha256(needs_job/'receipt.json'), 'rows': {}, 'pack': None,
        'protocol': {'classifier': 'five writer-group folds, logistic C1, training-only scale',
            'feature_head': 'unchanged TP10 selected head; upstream training contains some of these reports',
            'heldout_limit': 'writer-held-out downstream label classifier only; not a new fully nested upstream-reader evaluation',
            'table': 'analyst operationalization, not blind; unit weights; no forecast-error slot',
            'tense': 'fixed first-main-clause finite-predicate rules; subordinate-prefix boundary/auxiliary/perfect/modality handling, conservative unclear; heuristic, no learned syntactic parse or human when key',
            'packing': 'needs and gate must qualify; independent source encoder pins retained'}}
    save = lambda: save_json(output/'receipt.json', receipt)
    if not needs_receipt.get('qualifies'):
        receipt.update(status='blocked', reason='TP23 did not qualify a need head; no substitute tag reader')
        save()
        return
    save()
    data = load(corpus)
    frame = data.reports
    with np.load(needs_job/'envent-tags.npz', allow_pickle=False) as d:
        if not np.array_equal(d['text_id'], frame.text_id):
            raise ValueError('Need rows differ from original Crowd-enVENT order')
        needs = d['logits']
    if needs.shape != (len(frame), 19) or not np.isfinite(needs).all():
        raise ValueError('Invalid need scores')
    texts = frame.hidden_emo_text.tolist()
    encode, _, identity = load_head(reader_job)
    selected = json.loads((reader_job/'receipt.json').read_text(encoding='utf8'))['selected_seed']
    with np.load(reader_job/f'seed-{selected}/predictions.npz', allow_pickle=False) as saved:
        original = saved['ratings']
    if original.shape != (len(data.test), len(RATINGS)) or not np.isfinite(original).all():
        raise ValueError('Original held-out readable-feature rows differ')
    rated = np.empty((len(texts), len(RATINGS)))
    rated[data.test] = original
    missing = np.setdiff1d(np.arange(len(texts)), data.test)
    with np.load(reader_job/f'seed-{selected}/head.npz', allow_pickle=False) as h:
        w, b = h['ratings_weights'], h['ratings_bias']
    for i in range(0, len(missing), 16):
        check()
        ids = missing[i:i+16]
        path = output/'feature-vectors'/f'{i:07d}.npz'
        x = encode([texts[j] for j in ids], check)
        path.parent.mkdir(exist_ok=True)
        np.savez(path, index=ids, embeddings=x)
        rated[ids] = x@w.T+b
    features = rated[:, [RATINGS.index(n) for n in FEATURES]]
    receipt['featureReuse'] = {'completedHeldOutRows': len(data.test), 'newRows': len(missing),
        'predictionsPin': sha256(reader_job/f'seed-{selected}/predictions.npz')}
    del encode, rated, x
    gc.collect()
    receipt['reader'] = identity
    reuse = {'shared': vector_cache, 'source': vector_source, 'corpus': corpus} if vector_cache or vector_source else {}
    direct, identity = saved_vectors(texts, Path(models), output/'direct-vectors', check, **reuse)
    labels, writers = frame.emotion.to_numpy(), frame.prolific_id.to_numpy()
    slots = np.column_stack([features, needs])
    np.savez(output/'slots.npz', features=features, needs=needs, text_id=frame.text_id.to_numpy())
    for name, matrix in [('direct', direct), ('slots', slots), ('both', np.column_stack([direct, slots]))]:
        save_json(output/'phase.json', {'phase': name})
        row, p, classes = evaluate(matrix, labels, writers, check)
        receipt['rows'][name] = row
        np.savez(output/(name+'-forecasts.npz'), probabilities=p, labels=np.asarray(classes))
        save()
    receipt['stakes_qualified'] = receipt['rows']['slots']['five_way']['accuracy'] >= receipt['rows']['direct']['five_way']['accuracy']-.10
    times = [tense(t) for t in texts]
    when = np.column_stack([np.asarray(times) == 'ahead', np.asarray(times) == 'already']).astype(float)
    ids = np.flatnonzero(np.isin(labels, ['fear', 'sadness']))
    raw = when[ids, 0] + .5*(np.asarray(times)[ids] == 'any')
    auc = float(roc_auc_score(labels[ids] == 'fear', raw))
    _, combined, names = forecasts(np.column_stack([needs, when])[ids], labels[ids], writers[ids], check)
    receipt['tense'] = {'auc': auc, 'bar': .60, 'qualified': auc >= .60,
                        'needs_plus_tense_auc': float(roc_auc_score(labels[ids] == 'fear', combined[:, names.index('fear')]))}
    all_slots = np.column_stack([slots, when])
    chosen = np.empty(len(labels), dtype=object)
    for train, test in GroupKFold(5).split(all_slots, labels, writers):
        check()
        z = (all_slots[test]-all_slots[train].mean(0))/(all_slots[train].std(0)+1e-9)
        chosen[test] = np.asarray(LOSS)[table_scores(z, auc >= .60).argmax(axis=1)]
    ids = np.flatnonzero(np.isin(labels, LOSS))
    accuracy = float(accuracy_score(labels[ids], chosen[ids].astype(str)))
    receipt['table'] = {'accuracy': accuracy, 'bar': .33, 'qualified': accuracy >= .33,
                        'labels': list(LOSS), 'confusion': confusion_matrix(labels[ids], chosen[ids], labels=list(LOSS)).tolist(),
                        'blind': False, 'when_included': auc >= .60}
    if not receipt['stakes_qualified']:
        receipt['ablations'] = {}
        for name, removed in [(name, [i]) for i, name in enumerate(FEATURES)]+[('need-tags', list(range(8, 27)))]:
            keep = [i for i in range(27) if i not in removed]
            pred, _, _ = forecasts(slots[ids][:, keep], labels[ids], writers[ids], check)
            receipt['ablations'][name] = float(accuracy_score(labels[ids], pred))
            save()
    rules = {'version': 'trigger-table-1', 'mean': all_slots.mean(0).tolist(), 'scale': (all_slots.std(0)+1e-9).tolist(),
             'tag_map': TAG_MAP, 'tense': {'ahead': AHEAD, 'already': ALREADY},
             'stakes_qualified': receipt['stakes_qualified'], 'table_qualified': accuracy >= .33, 'tense_qualified': auc >= .60}
    save_json(output/'trigger-rules.json', rules)
    receipt.update(status='complete', rulesPin=sha256(output/'trigger-rules.json'),
                   pack='await verified TP25 gate and component export; no automatic live attachment')
    receipt['artifactsPin'] = seal(output, [output/'slots.npz', output/'trigger-rules.json', *output.glob('*-forecasts.npz')], check)
    save()
