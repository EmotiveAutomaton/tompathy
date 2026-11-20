import numpy as np

from tompathy_engine.eval.readers.tp29 import (
    bootstrap_ed,
    co_labels,
    conclusions,
    folds,
    markers,
    paired_calibration,
    rate_ratio,
)


def test_marker_boundaries_and_word_exposure():
    assert markers(['LAUGHED, awkwardly!', "funny apology laugher", '']).tolist() == [
        [2, 1, 1], [3, 1, 1], [1, 0, 0]]
    counts = np.array([[100, 10], [200, 10]], float)
    assert rate_ratio(counts, np.array([True, False]), np.array([False, True]), np.ones(2)) == 2
    counts[1, 1] = 0
    assert np.isnan(rate_ratio(counts, np.array([True, False]), np.array([False, True]), np.ones(2)))


def test_writer_folds_and_held_out_scaling():
    rng = np.random.default_rng(4)
    writers = np.repeat(np.arange(20).astype(str), 8)
    x = rng.uniform(size=(len(writers), 2))
    y = (x[:, 1]+rng.normal(scale=.2, size=len(x)) > .5).astype(int)
    predictions, assignment, coefficients = paired_calibration(x, y, writers)
    assert np.array_equal(assignment, folds(writers))
    assert np.isfinite(predictions).all()
    for row in coefficients:
        test = assignment == row['fold']
        assert not set(writers[test]) & set(writers[~test])
        assert np.allclose(row['center'], x[~test].mean(0))
        assert np.allclose(row['scale'], x[~test].std(0))


def test_constructed_writer_bootstrap_and_colabel_overlap():
    labels = np.tile(['embarrassed', 'ashamed', 'other', 'other'], 25)
    writers = np.repeat(np.arange(25).astype(str), 4)
    counts = np.tile([[10, 3, 2], [10, 1, 1], [10, 0, 0], [10, 0, 0]], (25, 1))
    scores = np.tile([[.2, .8], [.7, .1], [.3, .2], [.4, .3]], (25, 1))
    forecasts = np.tile([[.4, .9], [.7, .1], [.3, .2], [.2, .3]], (25, 1))
    result = bootstrap_ed(counts, labels, scores, forecasts, writers, draws=30)
    assert np.allclose(result['fun_rate_ratio']['interval'], [3, 3])
    assert result['auc_gain']['interval'][0] > .02
    truth = np.tile([[1, 1, 0], [0, 1, 1], [0, 0, 1], [1, 0, 0]], (25, 1))
    row = co_labels(truth, ['amusement', 'embarrassment', 'remorse'], writers, draws=30)
    assert row['amusement_with_embarrassment'] == .5
    assert row['amusement_with_remorse'] == 0
    assert row['interval'] == [.5, .5] and row['passes']


def test_verdict_requires_every_fold_sign_and_defined_gap():
    stats = {name: {'estimate': value, 'interval': bounds} for name, value, bounds in [
        ('fun_rate_ratio', 2, [1.1, 3]), ('appeasement_rate_ratio', 2, [1.1, 3]),
        ('play_gap_sd', .2, [.1, .3]), ('auc_gain', .02, [.001, .03])]}
    signs = [{'shame': 1, 'play': 1} for _ in range(5)]
    result = conclusions(stats, signs, {'passes': True})
    assert result['A_play_in_embarrassment'] and result['B_appeasement']
    assert result['combined'] == 'Both; the link to PLAY may run through yielding.'
    signs[-1]['play'] = -1
    assert not conclusions(stats, signs, {'passes': True})['read3']
    stats['play_gap_sd']['estimate'] = None
    assert conclusions(stats, signs, {'passes': True})['B_appeasement']
    assert not conclusions(stats, signs, {'passes': True})['A_play_in_embarrassment']
    stats['appeasement_rate_ratio']['interval'] = [.8, 3]
    assert not conclusions(stats, signs, {'passes': True})['B_appeasement']


def test_full_flow_has_durable_forecasts_without_corpus_text_in_receipt(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    import pandas as pd

    from tompathy_engine.eval.readers import tp29
    n = 120
    frame = pd.DataFrame({'id': np.arange(n).astype(str), 'text': ['private fixture '+str(i) for i in range(n)],
                          'writer': np.repeat(np.arange(20).astype(str), 6),
                          'label': np.tile(['embarrassed', 'ashamed', 'other'], n//3),
                          'source_split': ['train']*n, 'writer_known': [True]*n})
    truth = np.tile([[1, 1, 0], [0, 1, 1], [0, 0, 1]], (n//3, 1))
    monkeypatch.setattr(tp29, 'ed_situations', lambda p: (frame, {}))
    monkeypatch.setattr(tp29, 'go_comments', lambda p: (frame, truth, ['amusement', 'embarrassment', 'remorse'], {}))
    reports = pd.DataFrame({'hidden_emo_text': frame.text, 'emotion': ['shame', 'joy']*(n//2)})
    monkeypatch.setattr(tp29, 'load', lambda p: SimpleNamespace(reports=reports, summary=dict))
    def vectors(texts, models, target, check):
        target.mkdir()
        values = np.random.default_rng(4).normal(size=(len(texts), 4))
        np.savez(target/'0000000.npz', values=values)
        return values, {'fixture': True}
    monkeypatch.setattr(tp29, 'saved_vectors', vectors)
    original_ed, original_go = tp29.bootstrap_ed, tp29.co_labels
    monkeypatch.setattr(tp29, 'bootstrap_ed', lambda *a: original_ed(*a, draws=30))
    monkeypatch.setattr(tp29, 'co_labels', lambda *a: original_go(*a, draws=30))
    protocol = tmp_path/'protocol.md'
    protocol.write_text('fixed')
    output = tmp_path/'out'
    output.mkdir()
    tp29.run('fixture', 'fixture', 'fixture', 'fixture', output, lambda: None,
             ledger='E-fixture', protocol=protocol)
    raw = (output/'receipt.json').read_text()
    assert 'private fixture' not in raw
    assert json.loads(raw)['status'] == 'complete'
    with np.load(output/'ed-forecasts.npz', allow_pickle=False) as saved:
        assert saved['forecasts'].shape == (n, 2)
        assert np.isfinite(saved['source_scores']).all()


def test_landing_preserves_source_and_applies_bound_owner_verdict(tmp_path):
    import json
    from pathlib import Path

    import pytest

    from tompathy_engine.eval.readers.reporting import land
    from tompathy_engine.packs.registry import sha256
    job = tmp_path/'job'
    job.mkdir()
    stats = {name: {'estimate': value, 'interval': bounds} for name, value, bounds in [
        ('fun_rate_ratio', 2, [1.1, 3]), ('appeasement_rate_ratio', 2, [1.1, 3]),
        ('play_gap_sd', .3, [.2, .4]), ('auc_gain', .03, [.01, .04])]}
    source = {'card': 'TP29', 'status': 'complete', 'productionAdmission': False,
              'protocolPin': 'frozen-original', 'verdict': {'published_account': False},
              'rows': {'ed': stats, 'coefficients': [{'shame': 1, 'play': 1}], 'go': {'passes': False}}}
    (job/'receipt.json').write_text(json.dumps(source))
    before = (job/'receipt.json').read_bytes()
    (job/'exit-verification.json').write_text(json.dumps(dict.fromkeys(
        ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent'), True)))
    (job/'complete.json').write_text('{}')
    (job/'plan.json').write_text('{"snapshotFiles":{},"launcherSha256":"fixture"}')
    destination = tmp_path/'readers-embarrassment-shame-2026-11.json'
    with pytest.raises(ValueError, match='owner verdict ruling'):
        land(job, destination)
    ruling = {'schema': 'TP29-owner-verdict-1', 'receivedAt': '2026-11-19',
              'originalProtocolPin': 'wrong', 'rulingPin': sha256(Path(__file__).parents[2]/'docs/TP29_OWNER_RULING_2026-11-19.md'),
              'rule': 'A=read1+read2+read3; B=appeasement-only; read4=reported-only'}
    path = tmp_path/'ruling.json'
    path.write_text(json.dumps(ruling))
    with pytest.raises(ValueError, match='binding differs'):
        land(job, destination, tp29_ruling=path)
    ruling['originalProtocolPin'] = 'frozen-original'
    path.write_text(json.dumps(ruling))
    land(job, destination, tp29_ruling=path)
    public = json.loads(destination.read_text())
    assert public['verdict']['A_play_in_embarrassment'] and public['verdict']['B_appeasement']
    assert not public['verdict']['read4']
    assert public['originalRunnerVerdict'] == source['verdict']
    assert public['sourceReceiptPin'] == sha256(job/'receipt.json')
    assert (job/'receipt.json').read_bytes() == before
