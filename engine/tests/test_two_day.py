"""Constructed implementation controls, never scientific validation."""
from types import SimpleNamespace

import pytest

from tompathy_engine.eval.two_day.attention import ladder_contexts
from tompathy_engine.eval.two_day.exports import join_words


def label(a, b, source='typed', stop=None, pause=None):
    return {'start': a, 'end': b, 'source': source, 'stop': stop, 'log_pause': pause,
                'timing_status': 'supported' if stop is not None else 'unsupported',
                'mixed_provenance': False, 'unresolved_provenance': False}


def test_export_nullable_timing_and_exact_word_join():
    rows, counts = join_words('one two_three', [label(0, 3), label(4, 7, stop=True, pause=2), label(8, 13)])
    assert rows[0]['stop'] is None and rows[0]['source'] == 'writer'
    assert rows[1]['source'] == 'unknown' and rows[1]['stop'] is None
    assert counts['unmatchedEngineWords'] == 1 and counts['unmatchedExportWords'] == 2
    with pytest.raises(ValueError, match='timing'):
        join_words('one', [label(0, 3) | {'stop': False}])
    with pytest.raises(ValueError, match='Only typed'):
        join_words('one', [label(0, 3, 'accepted_suggestion', True, 2)])


def test_ladder_never_sees_same_time_future_or_other_writer():
    sessions = [{'session': str(i), 'writer': 'a', 'time': i, 'text': str(i)} for i in range(5)]
    sessions += [{'session': 'tie', 'writer': 'a', 'time': 4, 'text': '99'}, {'session': 'foreign', 'writer': 'b', 'time': 0, 'text': '88'}]
    reader = SimpleNamespace(encode=lambda s: {'input_ids': [int(s)]*600})
    result = ladder_contexts(sessions, reader, 2)['4']
    assert result['selectedSessions'] == ['2', '3'] and result['eligible']
    assert result['own'] == [2]*424+[3]*600
    assert not ladder_contexts(sessions, reader, 8)['4']['eligible']
    assert not ladder_contexts(sessions, reader, 0)['4']['own']


def test_bottom_box_is_only_a_fixed_empty_shape():
    from tompathy_engine.packet.bottom_box import BottomBox, empty_bottom_box
    box = empty_bottom_box()
    assert BottomBox.model_validate(box).model_dump() == box
    box['readings']['stress']['value'] = .5
    with pytest.raises(ValueError):
        BottomBox.model_validate(box)
    box = empty_bottom_box()
    box['body']['warmth']['evidence'] = ['invented']
    with pytest.raises(ValueError):
        BottomBox.model_validate(box)


def test_bottom_box_rejects_uncommissioned_axes():
    from tompathy_engine.packet.bottom_box import BottomBox, empty_bottom_box
    box = empty_bottom_box()
    box['readings']['slope'] = box['readings']['stress']
    with pytest.raises(ValueError):
        BottomBox.model_validate(box)


def test_attention_unpunctuated_line_has_a_position():
    from tompathy_engine.eval.back_half.attention import positions
    assert positions('An unfinished line\nAnother line.', 3) == (1, False, False)
    assert positions('An unfinished line\nAnother line.', 19) == (0, True, True)


def test_exploratory_reader_merge_keeps_registered_scores():
    from copy import deepcopy

    from tompathy_engine.eval.two_day.attention import merge_readers
    original = [{'session': 'a', 'writer': 'w', 'fold': 0, 'words': [
        {'start': 0, 'end': 3, 'eligible': True, 'scores': {'V0': 1., 'V5': .5}}]}]
    second = deepcopy(original); second[0]['words'][0]['scores']['V0'] = 3.
    result = merge_readers(original, second)[0]['words'][0]['scores']
    assert result == {'V0': 1., 'V5': .5, 'V2': 3., 'V3': 2.}
    assert 'V2' not in original[0]['words'][0]['scores']
    second[0]['words'][0]['end'] = 4
    with pytest.raises(ValueError, match='coverage'):
        merge_readers(original, second)


def test_scoring_resume_checks_integrity_before_reusing_a_session(tmp_path, monkeypatch):
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.two_day import attention
    from tompathy_engine.eval.two_day.exports import read
    sessions = [{'session': 'one', 'text': 'a source', 'words': []}]
    calls = []
    monkeypatch.setattr(attention, 'implementation_hash', lambda: 'fixed')
    monkeypatch.setattr(attention.original, 'score_sessions', lambda rows, reader, **kwargs: calls.append(1) or rows)
    reader = SimpleNamespace(identity={'id': 'fixture'}, metrics={})
    attention.score_resumable(sessions, reader, tmp_path/'run', 'data', {}, lambda: None)
    attention.score_resumable(sessions, reader, tmp_path/'run', 'data', {}, lambda: None)
    assert calls == [1]
    path = next((tmp_path/'run/sessions').glob('*.json'))
    saved = read(path); saved['table']['text'] = 'tampered'
    save_json(path, saved)
    with pytest.raises(ValueError, match='integrity'):
        attention.score_resumable(sessions, reader, tmp_path/'run', 'data', {}, lambda: None)
