import hashlib
import json

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import check_grad

from tompathy_engine.eval.readers import tp30
from tompathy_engine.packs.registry import sha256


def test_rater_or_denominator_unassigned_and_original_disagreement():
    labels = ['caring', 'love', 'amusement', 'embarrassment']
    rows = tp30.aggregate_raters(['a']*3, ['1', '2', '3'],
        np.array([[1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 0, 0]]), labels, 'go', ['a', 'b'])
    assert rows['shares'][0, tp30.CHANNELS.index('CARE')] == 1/3
    assert rows['shares'][0, tp30.CHANNELS.index('SHAME')] == 0
    assert rows['unassigned'][0] == 1/3 and rows['empty'][0] == 1/3
    assert rows['raters'].tolist() == [3, 0]
    assert rows['disagreement'][0] == 1
    pair = tp30.PAIRS.index(tuple(sorted([tp30.CHANNELS.index('CARE'), tp30.CHANNELS.index('PLAY')])))
    assert rows['pair_support'][0, pair] == 2/3
    with pytest.raises(ValueError, match='duplicate'):
        tp30.aggregate_raters(['a', 'a'], ['1', '1'], np.zeros((2, 4)), labels, 'go', ['a'])
    single = tp30.aggregate_raters(['a'], ['1'], np.array([[1, 0, 0, 0]]), labels, 'go', ['a'])
    assert np.isnan(single['disagreement'][0]) and single['raters'][0] == 1
    assert single['shares'][0, tp30.CHANNELS.index('CARE')] == 1


@pytest.mark.parametrize('kind', ['sigmoid', 'softmax'])
def test_gradient_and_planted_soft_targets(kind):
    rng = np.random.default_rng(23)
    x = rng.normal(size=(80, 3))
    y = rng.uniform(size=(80, 4))
    if kind == 'softmax':
        y = np.eye(4)[np.arange(80) % 4]
    weights = np.r_[np.full(40, .6/40), np.full(40, .4/40)]
    theta = rng.normal(scale=.1, size=16)
    assert check_grad(lambda t: tp30.objective(t, x, y, weights, kind)[0],
                      lambda t: tp30.objective(t, x, y, weights, kind)[1], theta) < 1e-6
    targets = np.zeros((80, 9))
    targets[:, 0] = 1/(1+np.exp(-3*x[:, 0]))
    targets[:, 1] = 1-targets[:, 0]
    head = tp30.fit_head(x, targets, np.zeros(80), weights, lambda: None, kind)
    p = tp30.predict(head, x, kind)
    assert np.corrcoef(p[:, 0], targets[:, 0])[0, 1] > .98
    assert not head[3][2:].any() and np.all(p[:, 2:] == 0)


def test_author_split_and_exact_overlap_exclusion():
    n = 50
    go = pd.DataFrame({'id': [str(i) for i in range(n)], 'writer': np.repeat(np.arange(10).astype(str), 5),
                       'writer_known': True, 'text': ['go '+str(i) for i in range(n)]})
    ed = pd.DataFrame({'text': [' GO   20 ', 'ed']})
    ev = pd.DataFrame({'hidden_emo_text': ['go 25', 'ev']})
    train, test, ev_train, authors, _ = tp30.split(go, ed, ev, np.array([5, 5]))
    assert not set(authors[train]) & set(authors[test])
    assert not train[20] and not train[25]
    assert ev_train[1]
    assert not set(tp30.text_keys(go.text[train])) & set(tp30.text_keys(ed.text))


def test_pair_clause_and_constant_co_rise_are_not_fabricated():
    p = np.zeros((3, 9))
    p[:, :2] = [[.8, .7], [.6, .6], [.4, .3]]
    support = np.zeros((3, 36))
    support[:, 0] = 1
    result = tp30.mix(p, np.array([0, .5, 1]), support)
    assert result['eligible'] == 3 and result['pairs_pass']
    support[:, 1] = 1
    assert not tp30.mix(p, np.array([0, .5, 1]), support)['pairs_pass']
    assert not tp30.mix(p*.1, np.array([0, .5, 1]), support)['pairs_pass']
    matrix = tp30.co_rise(p)
    assert matrix[2][2] is None and matrix[0][0] == pytest.approx(1)


def test_missing_source_coverage_and_control_are_kept():
    rows = {}
    for source in ['ed', 'envent']:
        rows[source] = {kind: {name: {'auc': (.75 if kind == 'profile' else .755)}
                              for name in tp30.CHANNELS} for kind in ['profile', 'control']}
    rows['envent']['profile']['SHAME']['auc'] = None
    rows['envent']['control']['SHAME']['auc'] = None
    result = tp30.transfer_summary(rows)
    assert result['test1_passes'] and result['test4_passes']
    assert result['channels']['SHAME']['sources'] == 1
    rows['ed']['profile']['SHAME']['auc'] = .7
    assert not tp30.transfer_summary(rows)['test4_passes']


def test_reuse_binds_every_byte_input_order_and_original_code(tmp_path):
    code = tmp_path/'code/tompathy_engine/eval/readers/tp23.py'
    code.parent.mkdir(parents=True)
    code.write_text('original source')
    texts, identity = ['a', 'b'], {'original': True}
    key = hashlib.sha256(json.dumps({'texts': texts, 'encoder': identity, 'code': sha256(code)}, sort_keys=True).encode()).hexdigest()
    cache = tmp_path/'ed-vectors/0000000.npz'
    cache.parent.mkdir()
    np.savez(cache, key=key, values=np.zeros((2, 384)))
    files = {'ed-vectors/0000000.npz': sha256(cache)}
    receipt = {'vectors': {'ed': {'n': 2, 'encoder': identity}}}
    values, actual = tp30.reused_vectors(tmp_path, 'ed', texts, receipt, files, lambda: None)
    assert values.shape == (2, 384) and actual == identity
    with pytest.raises(ValueError, match='binding'):
        tp30.reused_vectors(tmp_path, 'ed', texts[::-1], receipt, files, lambda: None)
    cache.write_bytes(b'changed')
    with pytest.raises(ValueError, match='artifact'):
        tp30.reused_vectors(tmp_path, 'ed', texts, receipt, files, lambda: None)


def test_full_flow_reuses_all_completed_vectors_and_saves_only_private_forecasts(tmp_path, monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace

    n = 100
    rng = np.random.default_rng(33)
    go = pd.DataFrame({'id': np.arange(n).astype(str), 'text': ['private go '+str(i) for i in range(n)],
                       'writer': np.repeat(np.arange(20).astype(str), 5), 'writer_known': True,
                       'source_split': ['train']*90+['unreleased']*10})
    ed = pd.DataFrame({'id': np.arange(n).astype(str), 'text': ['private ed '+str(i) for i in range(n)],
                       'label': ['afraid', 'ashamed', 'angry', 'excited', 'caring']*20})
    ev = pd.DataFrame({'text_id': np.arange(n).astype(str), 'hidden_emo_text': ['private ev '+str(i) for i in range(n)],
                       'emotion': ['fear', 'shame', 'anger', 'sadness', 'disgust']*20})
    sources = {'ed': {}, 'go': {}, 'envent': {}}
    job = tmp_path/'original'
    job.mkdir()
    (job/'artifact-manifest.json').write_text('{"files":{}}')
    snapshot = {}
    for name in ['tp23.py', 'encoders.py', 'affect_data.py', 'envent.py']:
        relative = 'tompathy_engine/eval/readers/'+name
        path = job/'code'/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(Path(tp30.__file__).with_name(name).read_bytes())
        snapshot[relative] = sha256(path)
    (job/'plan.json').write_text(json.dumps({'snapshotFiles': snapshot}))
    (job/'receipt.json').write_text('{}')
    source = {'sources': sources, 'artifactsPin': sha256(job/'artifact-manifest.json'),
              'vectors': {name: {'encoder': {}} for name in sources}}
    monkeypatch.setattr(tp30, 'completed', lambda *a: source)
    monkeypatch.setattr(tp30, 'model_identity', lambda *a: {})
    monkeypatch.setattr(tp30, 'ed_situations', lambda p: (ed, {}))
    monkeypatch.setattr(tp30, 'go_comments', lambda p: (go, None, [], {}))
    monkeypatch.setattr(tp30, 'load', lambda p: SimpleNamespace(reports=ev, summary=dict))
    targets = {'shares': rng.uniform(size=(n, 9)), 'raters': np.full(n, 5),
               'unassigned': rng.uniform(size=n), 'empty': np.zeros(n),
               'disagreement': rng.uniform(size=n), 'pair_support': rng.uniform(size=(n, 36))}
    monkeypatch.setattr(tp30, 'intake', lambda *a: (targets, targets, {}))
    reused, encoded = [], []
    def reuse(job, name, texts, *args):
        reused.append((name, len(texts)))
        return rng.normal(size=(len(texts), 384)), {}
    def fresh(texts, models, target, check):
        encoded.extend(texts)
        assert texts == go.text.tolist()[90:]
        target.mkdir()
        values = rng.normal(size=(len(texts), 384))
        np.savez(target/'fixture.npz', values=values)
        return values, {}
    monkeypatch.setattr(tp30, 'reused_vectors', reuse)
    monkeypatch.setattr(tp30, 'saved_vectors', fresh)
    out = tmp_path/'out'
    out.mkdir()
    protocol = tmp_path/'protocol.md'
    protocol.write_text('frozen')
    tp30.run('fixture', 'fixture', 'fixture', 'fixture', out, lambda: None,
             source_job=job, protocol=protocol, ledger='E-fixture')
    result = json.loads((out/'receipt.json').read_text())
    assert result['status'] == 'complete' and not result['productionAdmission']
    assert reused == [('ed', 100), ('envent', 100), ('go', 90)] and len(encoded) == 10
    assert 'private go' not in (out/'receipt.json').read_text()
    assert len(result['rows']['co_rise']['predicted']) == 9
    with np.load(out/'ed-profile-forecasts.npz', allow_pickle=False) as saved:
        assert saved['probabilities'].shape == (100, 9) and len(saved['ids']) == 100
