import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GroupKFold

from tompathy_engine.eval.readers import tp7, tp23, tp24, tp25, trigger_export
from tompathy_engine.packs.trigger import TAGS


@pytest.mark.parametrize('transfer_passed,story_auc', [(False, 1.), (True, .723)])
def test_bow_runner_saves_bound_forecasts_and_uses_owner_transfer_bars(tmp_path, monkeypatch, transfer_passed, story_auc):
    output = tmp_path/'job'; output.mkdir()
    frame = pd.DataFrame({'text': ['bright family picnic' if i % 2 else 'dark lonely road' for i in range(60)],
                          'story': [str(i//2) for i in range(60)]})
    y = np.tile(np.arange(60)[:, None] % 2, (1, 19))
    humans = [np.tile(row, (3, 1)) for row in y]
    folds = list(GroupKFold(5).split(frame, groups=frame.story))
    monkeypatch.setattr(tp23, 'load', lambda *a: (frame, y, humans, folds, {'rows': 60, 'test_fixture': True}))
    ev = pd.DataFrame({'hidden_emo_text': ['bright family picnic', 'dark lonely road'], 'text_id': ['fixture-a', 'fixture-b']})
    monkeypatch.setattr(tp23, 'envent', lambda *a: SimpleNamespace(reports=ev))
    monkeypatch.setattr(tp23, 'roc_auc_score', lambda *a: story_auc)
    transfer = {'transfer_passed': transfer_passed, 'twins': {'fear-sadness': dict.fromkeys(['ratings', 'needs', 'ratings+needs', 'words'], .7)},
                'thirteen_labels_macro_f1': {'ratings': .4, 'needs': .4, 'ratings+needs': .4}}
    monkeypatch.setattr(tp23, 'transfer', lambda *a, **k: transfer)
    bundle = tmp_path/'bundle/engine'; bundle.mkdir(parents=True)
    (bundle/'pf_need_out.json').write_text(json.dumps({'story_commonsense': {'mean_auc': story_auc, 'held_out_story_auc': dict.fromkeys(TAGS, story_auc)}, **transfer}))
    tp23.run(tmp_path, tmp_path, tmp_path, output, lambda: None, bundle=bundle.parent)
    receipt = json.loads((output/'receipt.json').read_text())
    assert receipt['status'] == 'complete' and receipt['qualifies'] == transfer_passed
    assert (receipt['pack'] is None) == (not transfer_passed)
    assert receipt['preflight']['reproduced'] and len(receipt['folds']) == 5 and receipt['artifactsPin']
    with np.load(output/'heldout.npz', allow_pickle=False) as d:
        assert d['logits'].shape == (60, 19) and np.isfinite(d['logits']).all() and np.array_equal(d['truth'], y)


def test_gate_runner_keeps_source_separation_and_saves_new_counting_inputs(tmp_path, monkeypatch):
    frame = pd.DataFrame([{'text': f'{source}:{group}:{label}', 'positive': bool(label),
                           'source': source, 'group': f'{source}:{group}'}
                          for source in ['envent', 'go', 'story'] for group in range(20) for label in [0, 1]])
    monkeypatch.setattr(tp25, 'source_rows', lambda *a: (frame, {'constructed': True}))
    def vectors(texts, *a):
        x = np.array([[20 if t.endswith(':1') else -20, 1] for t in texts], float)
        return x, {'constructed': True}
    monkeypatch.setattr(tp25, 'saved_vectors', vectors)
    monkeypatch.setattr(tp25, 'neutral_texts', lambda *a: (['plain:0']*40, ['revision:0']*6, {'constructed': True}))
    tp25.run(tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, lambda: None)
    r = json.loads((tmp_path/'receipt.json').read_text())
    assert r['status'] == 'complete' and r['qualifies'] and set(r['rows']) == {'envent', 'go', 'story'}
    assert all(v['n'] == 40 and v['positive'] == 20 for v in r['rows'].values())
    with np.load(tmp_path/'envent-gate-probabilities.npz', allow_pickle=False) as d:
        assert len(d['probability']) == 40
    assert r['artifactsPin']


def test_trigger_dependency_block_performs_no_forward(tmp_path, monkeypatch):
    job = tmp_path/'need'; job.mkdir()
    (job/'receipt.json').write_text(json.dumps({'card': 'TP23-bow'}))
    monkeypatch.setattr(tp24, 'verified', lambda *a: ({'qualifies': False}, {}))
    monkeypatch.setattr(tp24, 'load', lambda *a: pytest.fail('Blocked trigger read source data'))
    out = tmp_path/'output'; out.mkdir()
    tp24.run(tmp_path, tmp_path, job, tmp_path, out, lambda: None)
    r = json.loads((out/'receipt.json').read_text())
    assert r['status'] == 'blocked' and r['pack'] is None


def test_best_development_fine_seed_is_not_replaced_after_its_test_miss(tmp_path, monkeypatch):
    sources = {}
    for name, dev, qualifies in [('bow', .7, False), ('frozen', .75, False), ('fine-23', .9, False), ('fine-47', .8, True), ('fine-71', .7, True)]:
        job = tmp_path/name; job.mkdir()
        r = {'card': 'TP23-'+name, 'story': {'development_auc': dev}, 'qualifies': qualifies,
             'protocol': {'seed': int(name.split('-')[1]) if name.startswith('fine') else 23}, 'preflight': {'reproduced': True}}
        (job/'receipt.json').write_text(json.dumps(r)); sources[job] = r
    monkeypatch.setattr(trigger_export, 'verified', lambda job, *a: (sources[job], {}))
    selected, audit = trigger_export.select_need(list(sources), lambda: None)
    assert selected is None and audit['selectedFineSeed'] == 23


def test_need_export_refuses_failed_bar_before_creating_directory(tmp_path, monkeypatch):
    job = tmp_path/'source'; job.mkdir()
    (job/'receipt.json').write_text(json.dumps({'card': 'TP23-frozen'}))
    monkeypatch.setattr(trigger_export, 'verified', lambda *a: ({'qualifies': False}, {}))
    with pytest.raises(ValueError, match='both TP23 bars'):
        trigger_export.need_pack(job, tmp_path, tmp_path, tmp_path/'pack', lambda: None)
    assert not (tmp_path/'pack').exists()


def test_choice_exception_keeps_partial_pilot_summary_and_reraises(tmp_path, monkeypatch):
    source = tmp_path/'source'; source.mkdir(); (source/'MANIFEST.json').write_text('{}')
    out = tmp_path/'output'; out.mkdir()
    monkeypatch.setattr(tp7, 'LocalReader', lambda *a, **k: object())
    def interrupted(source, pilot, reader, check):
        pilot.mkdir()
        (pilot/'receipt.json').write_text(json.dumps({'status': 'stopped', 'identity': {'fixed': True},
            'all': {'questions': 3}, 'acceptedNotTopScore': {'questions': 1}, 'reason': 'constructed stop'}))
        raise RuntimeError('constructed stop')
    monkeypatch.setattr(tp7, 'choice_run', interrupted)
    with pytest.raises(RuntimeError, match='constructed stop'):
        tp7.run(source, tmp_path, out, lambda: None)
    saved = json.loads((out/'receipt.json').read_text())
    assert saved['rows']['questions'] == 3 and saved['status'] == 'stopped' and saved['reason'] == 'constructed stop'
