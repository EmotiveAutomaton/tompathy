import json
from types import SimpleNamespace

import numpy as np
import pytest

from tompathy_engine.eval.readers.artifacts import seal, verified
from tompathy_engine.eval.readers.tag_training import predict
from tompathy_engine.eval.readers.tp12 import apply_gate, policy_for
from tompathy_engine.eval.readers.tp23 import thresholds
from tompathy_engine.eval.readers.tp25 import select, split, story_affect_key
from tompathy_engine.features.pause_remainder import add_remainder
from tompathy_engine.packs.run import encoder_for
from tompathy_engine.packs.trigger import tense


def test_main_clause_tense_does_not_promote_possession_or_embedded_future():
    cases = {'I have a dog.': 'any', 'I am tired.': 'any',
             'I have already lost my job.': 'already', 'I felt sad but might recover.': 'already',
             'If I lose the job, I will leave.': 'ahead', 'When I arrived, I was alone.': 'already',
             'I am afraid that she will leave.': 'ahead', 'I am going to leave.': 'ahead',
             'The red car will stop.': 'ahead', 'If the alarm rings I leave.': 'any'}
    assert {text: tense(text) for text in cases} == cases


def test_shared_frozen_vectors_survive_new_batching_without_forward_repeat(tmp_path, monkeypatch):
    from tompathy_engine.eval.readers import vector_cache as cache
    identity = {'id': 'constructed', 'files': {}}
    monkeypatch.setattr(cache, 'model_identity', lambda *a: identity)
    monkeypatch.setattr(cache.importlib.metadata, 'version', lambda n: 'fixture')
    calls = []
    def load_encoder(*a, **k):
        def encode(texts):
            calls.extend(texts)
            return np.array([[len(t)]*384 for t in texts], np.float32)
        return encode, {**identity, 'token_cap': 128, 'device': 'cpu', 'threads': 2,
                        'versions': dict.fromkeys(['torch','transformers','model2vec','sentence-transformers','numpy'], 'fixture')}
    monkeypatch.setattr(cache.encoders, 'load_encoder', load_encoder)
    texts = ['one', 'twice', 'three']
    cache.vectors(texts, tmp_path, tmp_path/'first', lambda: None, shared=tmp_path/'shared')
    monkeypatch.setattr(cache.encoders, 'load_encoder', lambda *a, **k: pytest.fail('Completed forward repeated'))
    reordered, _ = cache.vectors(texts[::-1], tmp_path, tmp_path/'second', lambda: None, shared=tmp_path/'shared')
    assert calls == texts and reordered[:, 0].tolist() == [5, 5, 3]


def test_final_short_tag_batch_reuse_and_changed_identity(tmp_path):
    import torch
    calls = []
    class Model:
        head = SimpleNamespace(out_features=2)
        def eval(self):
            return self
        def __call__(self, rows):
            calls.extend(rows)
            return torch.tensor([[len(t), 1] for t in rows], dtype=torch.float32)
    texts = [str(i) for i in range(19)]
    visits = 0
    def interrupt():
        nonlocal visits
        visits += 1
        if visits == 2:
            raise RuntimeError('stop')
    with pytest.raises(RuntimeError, match='stop'):
        predict(Model(), texts, interrupt, output=tmp_path/'batches', identity='head-a')
    value = predict(Model(), texts, lambda: None, output=tmp_path/'batches', identity='head-a')
    assert value.shape == (19, 2) and calls == texts
    predict(Model(), texts, lambda: None, output=tmp_path/'batches', identity='head-a')
    assert calls == texts
    with pytest.raises(ValueError, match='changed'):
        predict(Model(), texts, lambda: None, output=tmp_path/'batches', identity='head-b')


def test_group_development_threshold_and_refusal():
    groups = np.array(['a']*3 + ['b']*2 + ['c']*4)
    train, dev = split(groups)
    assert not set(groups[train]) & set(groups[dev])
    y = np.array([0, 0, 1, 1]*2)
    source = np.array(['a']*4 + ['b']*4)
    threshold, qualified, _ = select(y, np.array([.1, .15, .8, .9]*2), source)
    assert qualified and .15 < threshold <= .2
    threshold, qualified, _ = select(y, np.full(8, .5), source)
    assert threshold == .5 and not qualified
    limits = thresholds(np.array([[0], [1]]), np.array([[-9.], [9.]]))
    assert limits[0] == pytest.approx(.95)  # Highest tie, not an outer-label choice.


def test_publisher_negative_affected_flag_has_no_downstream_emotion_annotator():
    import pandas as pd
    assert story_affect_key(pd.DataFrame({'affected': ['no'], 'emotionworkerid': ['none']})) is False
    assert story_affect_key(pd.DataFrame({'affected': ['yes', 'yes'], 'emotionworkerid': ['a', 'b']})) is True
    assert story_affect_key(pd.DataFrame({'affected': ['yes', 'no']})) is None


def test_rejected_sentence_is_neutral_before_correction_and_no_minimum_invented():
    p = np.array([[.8, .1, .1], [.1, .8, .1]])
    original = p.copy()
    gated = apply_gate(p, [.1, .9], .5, 2)
    assert np.array_equal(p, original) and np.array_equal(gated[0], [0, 0, 1])
    assert np.array_equal(gated[1], original[1])
    with pytest.raises(ValueError):
        apply_gate(p, [.1], .5, 2)
    rows = []
    for size in (20, 60, 200):
        for estimator in ('raw', 'nnls-alpha-1', 'nnls-alpha-2', 'nnls-alpha-4'):
            rows.append({'neutralSource': 'corpus', 'mixture': 'peaked', 'neutralFraction': .8,
                'size': size, 'estimator': estimator, 'mae': .01 if estimator == 'raw' else .1, 'top1': .8, 'undefined': 0})
    policy = policy_for(rows)
    assert policy['minimum'] is None and policy['status'] == 'no-policy-qualified'


def test_tfidf_pack_matches_original_transform(tmp_path):
    from sklearn.feature_extraction.text import TfidfVectorizer
    v = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(['food and family', 'family comes home'])
    (tmp_path/'encoder').mkdir()
    (tmp_path/'encoder/vocabulary.json').write_text(json.dumps({'vocabulary': v.vocabulary_, 'idf': v.idf_.tolist(),
                                                             'ngram': [1, 2], 'sublinear_tf': True}))
    pack = SimpleNamespace(root=tmp_path, manifest=SimpleNamespace(encoder=SimpleNamespace(kind='tfidf')))
    texts = ['food food family', 'unseen']
    assert np.array_equal(encoder_for(pack)(texts), v.transform(texts).toarray())


def test_artifact_mutation_and_incomplete_source_refused(tmp_path):
    (tmp_path/'saved.json').write_text('{}')
    pin = seal(tmp_path, [tmp_path/'saved.json'])
    (tmp_path/'receipt.json').write_text(json.dumps({'card': 'test', 'status': 'complete', 'artifactsPin': pin}))
    (tmp_path/'complete.json').write_text('{}')
    (tmp_path/'exit-verification.json').write_text(json.dumps(dict.fromkeys(
        ['nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent'], True)))
    verified(tmp_path, 'test')
    (tmp_path/'saved.json').write_text('{"altered":true}')
    with pytest.raises(ValueError, match='bytes changed'):
        verified(tmp_path, 'test')


def test_pause_residual_known_linear_timing_and_writer_separation():
    tables = []
    for writer, intercept in [('a', 3), ('b', 30)]:
        rows = []
        for i in range(20):
            word = 'w'*(i+1)
            rows.append({'text': word, 'source': 'writer', 'logPause': intercept+2*(i+1),
                         'sentenceStart': i == 0, 'scores': {'after_punctuation': i % 3 == 0, 'smol135_nats': i % 4}})
        tables.append({'writer': writer, 'text': ' '.join(r['text'] for r in rows), 'words': rows})
    result = add_remainder(tables)
    assert result['diagnostic_only'] and result['stop_label_uses_same_pause'] and result['writers'] == 2
    assert max(abs(w['scores']['pause_remainder']) for s in tables for w in s['words']) < 1e-10
