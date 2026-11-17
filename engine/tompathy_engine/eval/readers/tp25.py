"""TP25 source-held-out gate. Thresholds selected on inner development only."""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import go_comments
from .artifacts import seal
from .envent import load as envent
from .story import verify
from .tp10 import neutral_texts
from .tp23 import saved_vectors

GRID = np.arange(.05, 1, .05)


def story_affect_key(group):
    """Publisher affected flag precedes categorical annotation; no means no worker ID.

    Do not treat missing downstream emotionworkerid as missing affectedness.
    Conflicting flags remain excluded, with no fabricated annotator vote count.
    """
    values = set(group.affected.dropna().astype(str))
    if values == {'yes'}:
        return True
    if values == {'no'}:
        return False
    if not values <= {'yes', 'no'}:
        raise ValueError('Unknown publisher affectedness flag')
    return None


def source_rows(story, corpus, go, check):
    frames, pins = [], {}
    data = envent(corpus)
    f = data.reports
    frames.append(pd.DataFrame({'text': f.hidden_emo_text, 'positive': f.emotion != 'no-emotion',
                                'group': 'ev:'+f.prolific_id.astype(str), 'source': 'envent'}))
    pins['envent'] = data.pins
    f, y, labels, identity = go_comments(go)
    positive = y[:, [i for i, name in enumerate(labels) if name != 'neutral']].any(axis=1)
    negative = y[:, labels.index('neutral')].astype(bool)
    keep = (positive ^ negative) & (f.source_split.to_numpy() != 'unreleased')
    # Released writer groups where known; otherwise independent comment IDs.
    groups = ['go:'+str(w) if known else 'comment:'+str(i)
              for i, (w, known) in enumerate(zip(f.writer, f.writer_known))]
    frames.append(pd.DataFrame({'text': f.text.to_numpy()[keep], 'positive': positive[keep],
                                'group': np.asarray(groups)[keep], 'source': 'go'}))
    pins['go'] = identity
    rows = []
    story = Path(story)
    paths = [story/'csv_version'/s/'emotion/allcharlinepairs.csv' for s in ('dev', 'test')]
    verify(story, paths)
    raw = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    unsupported = 0
    for i, ((sid, _, _), group) in enumerate(raw.groupby(['storyid', 'linenum', 'char'], sort=False)):
        if i % 256 == 0:
            check()
        key = story_affect_key(group)
        if key is None:
            unsupported += 1
            continue
        if group.sentence.nunique() != 1:
            raise ValueError('Story emotion text mismatch')
        rows.append({'text': str(group.sentence.iloc[0]), 'positive': key, 'group': 'story:'+str(sid), 'source': 'story'})
    frames.append(pd.DataFrame(rows))
    pins['story'] = {'files': {p.relative_to(story).as_posix(): sha256(p) for p in paths},
                     'conflicting_or_missing_flags': unsupported,
                     'rule': 'publisher affected yes/no flag, identical across category-annotation rows; no cases legitimately have emotionworkerid none',
                     'formatReadmePin': sha256(story/'csv_version/README.txt')}
    return pd.concat(frames, ignore_index=True), pins


def split(groups):
    unique = sorted(set(groups), key=lambda s: hashlib.sha256(str(s).encode()).hexdigest())
    dev = set(unique[:max(1, len(unique)//10)])
    mask = np.array([g in dev for g in groups])
    return np.flatnonzero(~mask), np.flatnonzero(mask)


def fit(x, y, check):
    check()
    m = LogisticRegression(C=1, max_iter=3000, class_weight='balanced').fit(x, y)
    if np.any(m.n_iter_ >= m.max_iter):
        raise RuntimeError('Gate optimizer did not converge')
    return m


def curve(y, probability):
    y = np.asarray(y, bool)
    if not y.any() or y.all():
        raise ValueError('Gate evaluation needs both answer-key classes')
    return [{'threshold': float(t), 'sensitivity': float((probability[y] >= t).mean()),
             'silence': float((probability[~y] < t).mean())} for t in GRID]


def select(y, probability, sources):
    """Lowest threshold with >=.70 sensitivity and >=.80 silence per dev source.

    If none qualifies, retain the fixed .5 diagnostic and prohibit packing.
    External neutral texts and the held-out source never select the threshold.
    """
    curves = {s: curve(y[sources == s], probability[sources == s]) for s in sorted(set(sources))}
    for i, t in enumerate(GRID):
        if all(v[i]['sensitivity'] >= .7 and v[i]['silence'] >= .8 for v in curves.values()):
            return float(t), True, curves
    return .5, False, curves


def run(story, corpus, go, models, prepared, output, check, *, vector_cache=None, vector_source=None):
    output, models = Path(output), Path(models)
    frame, pins = source_rows(story, corpus, go, check)
    receipt = {'card': 'TP25', 'status': 'running', 'productionAdmission': False, 'ledger': 'no ledger row',
        'scope': 'Sentence event/stakes gate, source-held-out sensitivity; not a maker state', 'sources': pins,
        'protocol': {'encoder': 'frozen MiniLM, cap128', 'head': 'balanced logistic C1',
            'development': 'lowest SHA256 tenth of groups within each fitting source',
            'threshold': 'lowest .05-grid threshold passing .70 sensitivity/.80 silence for each development source; otherwise fixed .5 diagnostic, no pack',
            'external': 'B13 theme-free and verified revision sentences used once for evaluation, never threshold selection'},
        'rows': {}, 'pack': None}
    save = lambda: save_json(output/'receipt.json', receipt)
    save()
    reuse = {'shared': vector_cache, 'source': vector_source, 'corpus': corpus} if vector_cache or vector_source else {}
    vectors, encoder = saved_vectors(frame.text.tolist(), models, output/'vectors', check, **reuse)
    receipt['encoder'] = encoder
    y, groups, source = frame.positive.to_numpy(int), frame.group.to_numpy(), frame.source.to_numpy()
    for held in sorted(set(source)):
        save_json(output/'phase.json', {'phase': 'held-out-source', 'source': held})
        fit_ids, dev_ids = [], []
        for name in sorted(set(source)-{held}):
            ids = np.flatnonzero(source == name)
            train, dev = split(groups[ids])
            fit_ids.extend(ids[train]); dev_ids.extend(ids[dev])
        fit_ids, dev_ids = np.asarray(fit_ids), np.asarray(dev_ids)
        model = fit(vectors[fit_ids], y[fit_ids], check)
        threshold, qualified, validation = select(y[dev_ids], model.predict_proba(vectors[dev_ids])[:, 1], source[dev_ids])
        train, test = np.flatnonzero(source != held), np.flatnonzero(source == held)
        model = fit(vectors[train], y[train], check)
        probability = model.predict_proba(vectors[test])[:, 1]
        np.savez(output/(held+'-predictions.npz'), truth=y[test], probability=probability, index=test)
        receipt['rows'][held] = {'n': len(test), 'positive': int(y[test].sum()), 'threshold': threshold,
            'validation_qualified': qualified, 'development_curves': validation, 'curve': curve(y[test], probability),
            'sensitivity': float((probability[y[test] == 1] >= threshold).mean()),
            'silence': float((probability[y[test] == 0] < threshold).mean())}
        save()
    fit_ids, dev_ids = [], []
    for name in sorted(set(source)):
        ids = np.flatnonzero(source == name)
        train, dev = split(groups[ids]); fit_ids.extend(ids[train]); dev_ids.extend(ids[dev])
    fit_ids, dev_ids = np.asarray(fit_ids), np.asarray(dev_ids)
    model = fit(vectors[fit_ids], y[fit_ids], check)
    threshold, valid, validation = select(y[dev_ids], model.predict_proba(vectors[dev_ids])[:, 1], source[dev_ids])
    model = fit(vectors, y, check)
    np.savez(output/'head.npz', weights=model.coef_, bias=model.intercept_)
    np.savez(output/'envent-gate-probabilities.npz', probability=model.predict_proba(vectors[source == 'envent'])[:, 1])
    themes, revisions, neutral = neutral_texts(prepared)
    receipt['neutral_source'] = neutral
    receipt['final_threshold'] = threshold
    receipt['final_validation_qualified'] = valid
    receipt['final_development_curves'] = validation
    receipt['neutral'] = {}
    for name, texts in [('theme-free', themes), ('revisions', revisions)]:
        check()
        x, _ = saved_vectors(texts, models, output/(name+'-vectors'), check, **reuse)
        probability = model.predict_proba(x)[:, 1]
        np.savez(output/(name+'-predictions.npz'), probability=probability)
        receipt['neutral'][name] = {'n': len(texts), 'silence': float((probability < threshold).mean()),
                                  'curve': [{'threshold': float(t), 'silence': float((probability < t).mean())} for t in GRID]}
        save()
    receipt['qualifies'] = (valid and all(r['validation_qualified'] and r['sensitivity'] >= .7 for r in receipt['rows'].values())
                            and all(r['silence'] >= .8 for r in receipt['neutral'].values()))
    receipt['pack'] = 'eligible for verified research export' if receipt['qualifies'] else None
    receipt['artifactsPin'] = seal(output, [output/'head.npz', output/'envent-gate-probabilities.npz', *output.glob('*-predictions.npz')], check)
    receipt['status'] = 'complete'
    save()
