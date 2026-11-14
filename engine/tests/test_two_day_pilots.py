"""Known-answer controls for pilot statistics; no real benchmark scores."""
import math
from copy import deepcopy
from types import SimpleNamespace

import pytest

from tompathy_engine.eval.two_day import choice, goals, pilots, robustness, weightonly


def test_curvature_uses_probability_variance_not_word_variance():
    result = robustness.signals('word', [{'start': 0, 'end': 4, 'nats': 2, 'entropy': 1, 'variance': .5}])
    assert result['A0'] == 2 and result['A1'] == 0
    assert result['FD'] == pytest.approx(-math.sqrt(2))
    with pytest.raises(ValueError, match='denominator'):
        robustness.signals('word', [{'start': 0, 'end': 4, 'nats': 2, 'entropy': 1, 'variance': 0}])


def test_unicode_normalization_and_zero_event_interval():
    assert robustness.normalize('Ｆ\u200b  а\u2060') == 'F a'
    result = robustness.rate([0]*50)
    assert result['rate'] == 0 and 0 < result['interval'][1] < .08


def test_raid_quota_caps_generator_in_file_order():
    quota = robustness.Quotas()
    rows = [{'id': str(i), 'domain': 'books', 'model': 'same-generator', 'attack': 'none'} for i in range(13)]
    assert [quota.accept(r) for r in rows] == [True]*12+[False]
    assert not quota.complete()
    with pytest.raises(ValueError, match='Repeated'):
        quota.accept(rows[0])


def test_human_split_is_exactly_half_within_each_genre():
    rows = [{'id': f'{genre}-{i}', 'model': 'human', 'domain': genre} for genre in robustness.GENRES for i in range(100)]
    left, right = robustness.human_split(rows)
    assert len(left) == len(right) == 400
    assert not {r['id'] for r in left} & {r['id'] for r in right}
    assert robustness.human_split(list(reversed(rows))) == (left, right)


def test_human_intentions_keep_abstentions_as_errors():
    truth = list(pilots.INTENTIONS)
    assert pilots.intent_scores(truth, truth)['macroF1'] == 1
    result = pilots.intent_scores(truth, ['abstain']*5)
    assert result['macroF1'] == 0 and result['abstentionRate'] == 1
    assert pilots.HUMAN_MAP['tone'] == 'style' and pilots.HUMAN_MAP['format'] == 'abstain'


def test_reranker_cannot_promote_outside_initial_top_five():
    candidates = [{'id': str(i), 'text': 'shared '+('rare' if i == 8 else 'common')} for i in range(10)]
    result = goals.rerank('rare', 'common', candidates, '8')
    assert result['reader']['top1'] == 1
    assert result['rerank']['top1'] == 0 and not result['truthInTopFive']


def test_choice_primary_compares_best_rarity_control_in_every_draw():
    rows = [{'id': str(i), 'site': str(i % 5), 'rows': {name: {'top1': int(name in ('B4', 'E1')), 'reciprocalRank': 1 if name in ('B4', 'E1') else .5}
             for name in choice.METHODS}} for i in range(50)]
    result = choice.choice_summary(rows, draws=30)
    assert result['primary']['bestRarityBaseline'] == 'B4'
    assert result['primary']['gain'] == 0 and result['primary']['interval'] == [0, 0]
    assert not result['primary']['clearsBar']


def test_choice_score_baseline_never_enters_primary_rarity_set():
    row = {'id': 'q', 'site': 'test', 'question': 'The orbit.', 'accepted': 'a', 'answers': [
        {'id': 'a', 'text': 'The orbit.', 'score': 0, 'created': '2020-01-01T00:00:00+00:00'},
        {'id': 'b', 'text': 'Other unrelated prose.', 'score': 900, 'created': '2019-01-01T00:00:00+00:00'},
        {'id': 'c', 'text': 'Something else entirely.', 'score': 1, 'created': '2019-02-01T00:00:00+00:00'}]}
    result = choice.rank_question(row, [{'start': 0, 'end': len(row['question']), 'nats': 8}], choice.frequencies([row]))
    assert result['acceptedNotTopScore'] and result['rows']['B0']['top1'] == 0
    assert result['rows']['B3']['top1'] == 1 and result['rows']['E1']['top1'] == 1


def test_weightonly_gate_rejects_id_mismatch_and_extra_tokens():
    tokenizer = SimpleNamespace(get_vocab=lambda: {'a': 0, 'b': 1})
    def runtime(vocab):
        return SimpleNamespace(n_vocab=lambda: len(vocab), _model=SimpleNamespace(token_get_text=lambda i: vocab[i], token_get_attr=lambda i: 2))
    assert weightonly.vocabulary_gate(tokenizer, runtime(['a', 'b']), 2)['passed']
    assert not weightonly.vocabulary_gate(tokenizer, runtime(['b', 'a']), 2)['passed']
    assert not weightonly.vocabulary_gate(tokenizer, runtime(['a', 'b', '[PAD2]']), 3)['passed']
    assert weightonly.vocabulary_gate(tokenizer, runtime(['a', 'b', '[PAD2]']), 3, allow_unused_padding=True)['passed']
    assert not weightonly.vocabulary_gate(tokenizer, runtime(['a', 'b', 'other']), 3, allow_unused_padding=True)['passed']
    assert not weightonly.vocabulary_gate(tokenizer, runtime(['a', 'b', '[PAD2]']), 4, allow_unused_padding=True)['passed']
    receipt = {'status': 'complete', 'readerPin': 'r', 'dataPin': 'd', 'gates': {k: {'passed': True} for k in 'abcde'}}
    assert weightonly.ready(receipt, reader_pin='r', data_pin='d')
    for name in 'abcde':
        broken = deepcopy(receipt); broken['gates'][name]['passed'] = False
        assert not weightonly.ready(broken, reader_pin='r', data_pin='d')


def test_pending_weightonly_route_never_loads_a_model(tmp_path, monkeypatch):
    from tompathy_engine.eval.back_half.reporting import save_json
    monkeypatch.setattr(weightonly, 'implementation_hash', lambda: 'code')
    monkeypatch.setattr(weightonly, 'sha', lambda _: 'weights')
    monkeypatch.setattr(weightonly, 'WeightOnlyReader', lambda *a, **k: pytest.fail('Pending route must not load'))
    path = tmp_path/'receipt.json'
    save_json(path, {'codePin': 'code', 'dataPin': 'data', 'ggufPin': 'weights', 'status': 'pending', 'gates': {}})
    with pytest.raises(ValueError, match='five parity gates'):
        weightonly.load_admitted_route(tmp_path, tmp_path/'model', path, threads=2)


def test_q8_projection_halts_before_the_remaining_sample(tmp_path, monkeypatch):
    from tompathy_engine.eval.back_half.edits import CATEGORIES
    from tompathy_engine.eval.back_half.reporting import save_json
    prepared, output = tmp_path/'prepared', tmp_path/'run'
    rows = [{'id': str(i), 'fold': i % 5, 'category': CATEGORIES[i % 5], 'upstreamPrediction': CATEGORIES[i % 5],
             'replaced': 'before', 'replacement': 'after'} for i in range(100)]
    save_json(prepared/'edits.json', rows); save_json(prepared/'edits-intake.json', {'pin': 'fixture'})
    closed, called = [], []
    backend = SimpleNamespace(close=lambda **kwargs: closed.append(True))
    monkeypatch.setattr(pilots, 'guard', lambda **kwargs: None)
    monkeypatch.setattr(pilots, 'FixedQwen', lambda *args, **kwargs: backend)
    monkeypatch.setattr(pilots, 'fixed_reader', lambda *args: SimpleNamespace(pin='reader'))
    def score(reader, rows, indices, *, check, completed):
        check()
        result = dict(completed)
        for i in indices:
            called.append(i)
            result[rows[i]['id']] = {'raw': 'grammar', 'category': 'grammar', 'seconds': 300.,
                                      'inferenceMeasured': True, 'readerPin': reader.pin}
        return result
    monkeypatch.setattr(pilots, 'q8_sample', score)
    result = pilots.edit_run(prepared, output, 'http://127.0.0.1:1', lambda: None)
    assert len(called) == 50 and closed == [True]
    assert result['status'].startswith('stopped: first-50') and result['completed'] == 50


def test_robustness_retains_partial_rates_without_refitting_thresholds():
    rows = [{'id': f'{genre}-{i}', 'model': 'human', 'domain': genre, 'attack': 'none'} for genre in robustness.GENRES for i in range(100)]
    calibration, held = robustness.human_split(rows)
    scored = {r['id']: {'raw': {'A0': 1., 'A1': 1., 'FD': 0.}} for r in calibration}
    result = robustness.robustness_report(rows, scored)
    assert result['status'] == 'partial' and len(result['thresholds']) == 3 and not result['rates']
    scored[held[0]['id']] = {'raw': {'A0': 0., 'A1': 0., 'FD': 1.}}
    partial = robustness.robustness_report(rows, scored)
    assert partial['thresholds'] == result['thresholds']
    assert all(r['rate'] == 1 for r in partial['rates'])
    assert robustness.robustness_report(rows, {})['status'] == 'partial: calibration incomplete'


def test_edit_summary_counts_unclear_as_error_in_both_classes(tmp_path, monkeypatch):
    from tompathy_engine.eval.back_half.edits import CATEGORIES
    from tompathy_engine.eval.back_half.reporting import save_json
    rows = [{'id': str(i), 'fold': i, 'category': category, 'upstreamPrediction': category,
             'replaced': 'before', 'replacement': 'after'} for i, category in enumerate(CATEGORIES)]
    prepared, output = tmp_path/'prepared', tmp_path/'run'
    save_json(prepared/'edits.json', rows)
    save_json(prepared/'edits-intake.json', {'pin': 'fixture'})
    monkeypatch.setattr(pilots, 'guard', lambda **kwargs: None)
    monkeypatch.setattr(pilots, 'FixedQwen', lambda *a, **k: SimpleNamespace(close=lambda **kwargs: None))
    monkeypatch.setattr(pilots, 'fixed_reader', lambda *args: SimpleNamespace(pin='reader'))
    def score(reader, rows, indices, *, check, completed):
        check()
        return {**completed, **{rows[i]['id']: {'raw': 'unclear', 'category': 'other', 'seconds': 1.,
                'inferenceMeasured': True, 'readerPin': reader.pin} for i in indices}}
    monkeypatch.setattr(pilots, 'q8_sample', score)
    result = pilots.edit_run(prepared, output, 'http://127.0.0.1:1', lambda: None)
    assert result['completed'] == 5
    assert result['direct']['macroF1'] == 0
    assert result['direct']['twoWayAccuracy'] == 0


def test_choice_partial_is_not_accepted_as_completed_and_hashes_are_checked(tmp_path, monkeypatch):
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.ledger.ids import digest
    identity = {'dataPin': 'pin', 'codePin': 'code'}
    monkeypatch.setattr(choice, 'implementation_hash', lambda: 'code')
    save_json(tmp_path/'receipt.json', {'status': 'stopped', 'identity': identity, 'all': {'questions': 0}})
    with pytest.raises(ValueError, match='complete E1'):
        choice.completed_e1(tmp_path, [], 'pin')
    result = {'rows': {'E1': {'top1': 1}}}
    saved = {'key': 'key', 'result': result, 'sha256': digest(result)}
    assert choice.checked_observation(saved, 'key') == result
    saved['result']['rows']['E1']['top1'] = 0
    with pytest.raises(ValueError, match='pin'):
        choice.checked_observation(saved, 'key')


def test_public_landing_omits_individuals_prose_and_error_payloads():
    from tompathy_engine.eval.two_day.reporting import public
    value = public('goals', {'status': 'stopped', 'reason': 'private source text', 'text': 'private',
        'documents': [{'id': 'person', 'text': 'private'}], 'enginePin': 'a'*64,
        'pilotSummary': {'documents': 2, 'readers': {'body': {'top1': {'mean': .5, 'text': 'private'}}}}})
    assert value['status'] == 'stopped' and value['enginePin'] == 'a'*64
    assert 'private' not in str(value) and 'person' not in str(value)
    assert value['pilot']['readers']['body']['top1']['mean'] == .5
    assert public('goals', {'status': 'cleanup-failed'})['status'] == 'stopped'
    corrected = public('edit-reasons', {'status': 'stopped', 'aggregationCodePin': 'b'*64,
                                      'originalReceiptPin': 'c'*64})
    assert corrected['aggregationCodePin'] == 'b'*64 and corrected['originalReceiptPin'] == 'c'*64


def test_timing_report_keeps_reader_pins_and_can_repair_same_source(tmp_path):
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.two_day.exports import read
    from tompathy_engine.eval.two_day.reporting import land, public
    from tompathy_engine.ledger.ids import digest

    identity = {'id': 'fixture', 'revision': 'fixed', 'backend': 'private path must not escape'}
    raw = {'status': 'complete', 'readerLadderPin': 'a'*64,
           'measurements': [{'model': 'qwen', 'reader': identity, 'text': 'manuscript-3000', 'totalSeconds': 1.}]}
    source, directory = tmp_path/'source.json', tmp_path/'public'
    save_json(source, raw)
    expected = public('first-paint', raw)
    previous = {**expected, 'measurements': [{'totalSeconds': 1.}]}
    target = directory/'first-paint-2026-11.json'
    save_json(target, previous)
    landed = land('first-paint', source, directory)
    assert read(target) == landed == expected
    assert landed['readerLadderPin'] == 'a'*64
    assert landed['measurements'][0]['readerPin'] == digest(identity)
    assert 'private path' not in str(landed)
    archives = list((directory/'two-day-history').glob('*.json'))
    assert len(archives) == 1 and read(archives[0]) == previous
    assert land('first-paint', source, directory) == expected
    assert list((directory/'two-day-history').glob('*.json')) == archives


def test_goal_cleanup_failure_does_not_leave_complete_receipt(tmp_path, monkeypatch):
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.two_day.exports import read
    def fail(**kwargs):
        raise RuntimeError('owned fixture unload failed')
    monkeypatch.setattr(pilots, 'guard', lambda **kwargs: None)
    monkeypatch.setattr(pilots, 'FixedQwen', lambda *args, **kwargs: SimpleNamespace(close=fail, settings={}, model_id='test'))
    monkeypatch.setattr(pilots, 'LocalReader', lambda *args, **kwargs: SimpleNamespace(identity={'test': True}))
    save_json(tmp_path/'prepared/goals.json', [])
    with pytest.raises(RuntimeError, match='unload'):
        pilots.goal_run(tmp_path/'prepared', tmp_path/'readers', tmp_path/'run', 'http://127.0.0.1:1', lambda: None)
    assert read(tmp_path/'run/receipt.json')['status'] == 'cleanup-failed'


def test_weightonly_predicts_each_chunk_from_preceding_logit():
    import numpy as np
    from scipy.special import logsumexp
    reader = object.__new__(weightonly.WeightOnlyReader)
    reader.cache, reader.identity = None, {'test': True}
    reader.tokenizer = SimpleNamespace(bos_token_id=0)
    reader.encode = lambda text: {'input_ids': [1, 2, 3], 'offset_mapping': [(0, 1), (1, 2), (2, 3)]}
    class Runtime:
        def reset(self):
            self.n_tokens = 0
            self.scores = np.zeros((2048, 4))
        def eval(self, ids):
            for token in ids:
                self.scores[self.n_tokens] = np.arange(4)*(token+1)
                self.n_tokens += 1
    reader.model = Runtime()
    reader.metrics = {'forwardCalls': 0, 'inputTokens': 0, 'scoreMs': 0.}
    actual = reader.score('abc', context=[])
    expected = [logsumexp(np.arange(4)*(previous+1))-(previous+1)*target for previous, target in [(0, 1), (1, 2), (2, 3)]]
    assert [r['nats'] for r in actual] == pytest.approx(expected)
