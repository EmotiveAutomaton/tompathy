import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from tompathy_engine.eval.evidence import append
from tompathy_engine.eval.readers.tp28 import MAP, profiles
from tompathy_engine.eval.readers.trigger_export import base
from tompathy_engine.packet.bottom_box import ReadingScore
from tompathy_engine.packs.trigger import TAG_MAP, TAG_MAP_V2, TAGS


def test_versioned_map_preserves_original_and_unmapped_labels():
    assert TAG_MAP['tranquility'] == 'N2'
    assert TAG_MAP_V2 == {**TAG_MAP, 'tranquility': 'N6'}
    assert set(TAGS)-set(TAG_MAP_V2) == {'romance', 'indep'}


def test_export_records_absent_interval_explicitly():
    result = base('test', 'tags', ['family'], {}, {}, [], {}, {'metric': 'AUC', 'value': .8})
    assert ReadingScore.model_validate(result['score']).interval is None
    result = base('test', 'tags', ['family'], {}, {}, [], {}, {'metric': 'AUC', 'value': .8, 'interval': [.7, .9]})
    assert ReadingScore.model_validate(result['score']).interval == (.7, .9)


def test_stand_in_bootstrap_matches_direct_contrast_and_keeps_bad_controls_missing():
    p = np.array([[.1, .8, .5], [.2, .9, .5], [.8, .1, .5], [.9, .2, .5]])
    y = np.array([[0, 0], [0, 0], [1, 0], [1, 0]])
    mean, lift, intervals, valid = profiles(p, y, draws=100, seed=23)
    np.testing.assert_allclose(mean[0], [.85, .15, .5])
    np.testing.assert_allclose(lift[0, :2], np.array([.7, -.7])/p[:, :2].std(axis=0))
    assert np.isnan(lift[:, 2]).all() and np.isnan(intervals[:, 2]).all()
    assert np.isnan(lift[1]).all() and not valid[1].any()
    # Four units frequently resample one class only, so the finite-draw guard
    # correctly withholds this interval. A supported constructed sample clears.
    assert np.isnan(intervals[0, 0]).all()
    _, _, supported, _ = profiles(np.tile(p, (10, 1)), np.tile(y, (10, 1)), draws=100)
    assert supported[0, 0, 0] > 0
    assert all('embarrassed' not in row['ed'] and 'embarrassment' not in row['go'] for row in MAP.values())


def test_tp28_full_flow_reuses_existing_report_scores(tmp_path, monkeypatch):
    from tompathy_engine.eval.readers import tp28
    export = tmp_path/'export'
    (export/'rp-need-1').mkdir(parents=True)
    (export/'IM2').mkdir()
    (export/'receipt.json').write_text('{}')
    (export/'rp-need-1/evidence.json').write_text('{"tagMapVersion":2}')
    rows = 40
    frame = pd.DataFrame({'id': [str(i) for i in range(rows)], 'text': ['fixture']*rows,
                          'label': ['afraid', 'sad']*(rows//2), 'source_split': ['test']*rows})
    original = np.random.default_rng(3).uniform(size=(rows, 19))
    scores = pd.DataFrame(original, columns=TAGS)
    scores.insert(0, 'text_id', frame.id)
    scores.to_csv(export/'IM2/scores.csv', index=False, float_format='%.17g')
    (export/'IM2/manifest.json').write_text(json.dumps({'files': {'scores.csv': tp28.sha256(export/'IM2/scores.csv')}}))
    monkeypatch.setattr(tp28, 'completed', lambda *a: {'pack': {'pin': 'fixed'}})
    pack = SimpleNamespace(pin='fixed', root=export/'rp-need-1', manifest=SimpleNamespace(tag_map=TAG_MAP_V2),
                           weights=np.arange(19).reshape(19, 1)/19, bias=np.zeros(19))
    monkeypatch.setattr(tp28, 'load_pack', lambda *a: pack)
    calls = []
    def encode(texts):
        calls.extend(texts)
        return np.arange(len(texts)).reshape(-1, 1)/len(texts)
    monkeypatch.setattr(tp28, 'encoder_for', lambda p: encode)
    monkeypatch.setattr(tp28, 'ed_situations', lambda p: (frame, {}))
    monkeypatch.setattr(tp28, 'go_comments', lambda p: (
        frame, np.tile([1, 0, 1, 0, 1, 0], (rows, 1)),
        ['joy', 'curiosity', 'excitement', 'amusement', 'desire', 'caring'], {}))
    # Missing love must be represented in a declared source vocabulary; this
    # adapter supplies the full registered Go stand-ins even on zero support.
    go_labels = ['joy', 'curiosity', 'excitement', 'amusement', 'desire', 'caring', 'love']
    monkeypatch.setattr(tp28, 'go_comments', lambda p: (frame, np.tile([1, 0, 1, 0, 1, 0, 0], (rows, 1)), go_labels, {}))
    reports = pd.DataFrame({'text_id': frame.id, 'hidden_emo_text': frame.text,
                            'emotion': ['joy', 'fear']*(rows//2), **{k: np.ones(rows) for k in tp28.RATINGS}})
    monkeypatch.setattr(tp28, 'load', lambda p: SimpleNamespace(reports=reports, pins={'generation': 'fixture'}))
    original_profiles = tp28.profiles
    monkeypatch.setattr(tp28, 'profiles', lambda p, y, **kw: original_profiles(p, y, draws=50, **kw))
    output = tmp_path/'run'
    output.mkdir()
    tp28.run(export, 'ed', 'go', 'ev', output, lambda: None, ledger='E-fixture')
    result = json.loads((output/'receipt.json').read_text())
    assert result['status'] == 'complete' and result['sources']['envent']['inferenceReused']
    assert len(calls) == 2*rows
    with np.load(output/'envent/scores.npz', allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved['scores'], original)


def test_ledger_retries_and_corrections_preserve_prior_bytes(tmp_path):
    path = tmp_path/'ledger.jsonl'
    row = {'id': 'E-C0-20261119', 'date': '2026-11-19', 'question': 'Can the exact reader be exported?',
           'data': 'Existing saved weights and forecasts', 'estimate': {'copied': 6600}, 'interval': None,
           'bar': 'Exact preservation', 'verdict': 'verified export', 'limit': 'No new accuracy result.',
           'claims': ['M1', 'M3', 'N1'], 'family': 'stories'}
    assert append(path, row) == 'appended'
    original = path.read_bytes()
    assert append(path, row) == 'unchanged'
    with pytest.raises(ValueError, match='already exists'):
        append(path, {**row, 'verdict': 'changed'})
    assert path.read_bytes() == original
    assert append(path, {**row, 'id': 'E-C0-20261119-correction', 'verdict': 'correction to E-C0-20261119'}) == 'appended'
    assert path.read_bytes().startswith(original)
    assert len([json.loads(x) for x in path.read_text().splitlines()]) == 2
