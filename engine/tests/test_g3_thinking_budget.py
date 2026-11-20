import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
import word_table_g3_budget as budget
import word_table_g3_follow as follow
import word_table_lane as lane
from word_table_rd2 import prompts, template


def definition():
    examples = [{'id': str(i), 'text': 'sample', 'standards': 2, 'social_norms': 3} for i in range(8)]
    return template(prompts(lane.core, examples)['V2'])


def test_selection_is_id_only_and_order_independent():
    items = [{'id': str(i), 'text': 'original'} for i in range(600)]
    changed = [{'id': row['id'], 'text': 'other'} for row in reversed(items)]
    selected = [items[i]['id'] for i in budget.select(items)]
    assert len(set(selected)) == 20
    assert selected == [r['id'] for r in sorted(items, key=lambda r: lane.string_pin('G3:V2:3072:23:'+r['id']))[:20]]
    assert selected == [changed[i]['id'] for i in budget.select(changed)]
    with pytest.raises(ValueError):
        budget.select(items[:-1] + [items[0]])


def test_cap_is_the_only_request_change_and_saved_prefix_is_reused(tmp_path, monkeypatch):
    calls = []
    responses = ['{"standards":2,"social_norms":3}', '']
    def generate(request, guard):
        calls.append(request)
        return {'response': responses[(len(calls)-1) % 2], 'model': lane.W[0], 'done': True,
                'done_reason': 'length', 'eval_count': request['options']['num_predict'], 'eval_duration': 10**9}
    monkeypatch.setattr(lane.core, 'guarded_generate', generate)
    monkeypatch.setattr(lane.core, 'read_model', lambda *args: None)
    monkeypatch.setattr(lane.core, 'api', lambda *args: {'models': []})
    monkeypatch.setattr(lane, 'fit_or_wait', lambda *args: 100)
    items = [{'id': str(i), 'text': 'text'+str(i)} for i in range(2)]
    lengths = {'0': 10, '1': 11}
    guard = type('Guard', (), {'check': lambda self: None})()
    for job, cap in [('G3', 1024), (budget.JOB, 3072)]:
        result = lane.rate(tmp_path, tmp_path/job, items, 'W', job, {'variant':'V2'}, guard,
                           token_lengths=lengths, template=definition())
        budget.verify_binding(result['binding'], cap)
        assert result['valid'] == 1
    assert len(calls) == 4
    for old, new in zip(calls[:2], calls[2:]):
        assert new == {**old, 'options': {**old['options'], 'num_predict': 3072}}
    lane.rate(tmp_path, tmp_path/budget.JOB, items, 'W', budget.JOB, {'variant':'V2'}, guard,
              token_lengths=lengths, template=definition())
    assert len(calls) == 4
    with pytest.raises(ValueError):
        lane.rate(tmp_path, tmp_path/'wrong', items, 'W', budget.JOB, {'variant':'V5'}, guard,
                  token_lengths=lengths, template=definition())


def test_paired_replay_checks_both_bindings_and_keeps_invalid_answers(tmp_path, monkeypatch):
    v2 = definition()
    old = {'role': 'W', 'think': True, 'modelPin': lane.W[1], 'variant': 'V2', 'promptPin': budget.PROMPT,
           'schemaPin': budget.SCHEMA, 'options': budget.ORIGINAL_OPTIONS, 'job': 'G3'}
    new = {**old, 'job': budget.JOB, 'options': {**old['options'], 'num_predict': 3072}}
    items = [{'id': str(i), 'text': 'sample'} for i in range(4)]
    original = tmp_path/'jobs/G3/V2/W'
    out = tmp_path/'jobs'/budget.JOB
    original.mkdir(parents=True)
    (out/'W').mkdir(parents=True)
    (tmp_path/'inputs').mkdir()
    lane.write(tmp_path/'inputs'/budget.PROTOCOL, {})
    lane.write(tmp_path/'inputs'/(budget.JOB+'.json'), items)
    schema = {'type':'object','properties':v2[1],'required':list(v2[1]),'additionalProperties':False}
    lane.write(out/'W/protocol.json', {**new, 'schema':schema, 'prompt':v2[0], 'secondKey':None})
    valid = '{"standards":1,"social_norms":5}'
    for index, (low, high) in enumerate([(valid, valid), ('', valid), (valid, '{'), ('{"standards":true}', '')]):
        for folder, final, binding in ((original, low, old), (out/'W', high, new)):
            lane.write(folder/f'row-{index:06d}.json', {'id':str(index),'index':index,'seconds':2,'binding':binding,
                       'values':json.loads(valid) if final == valid else None,
                       'response':{'response':final, 'eval_count':4, 'eval_duration':10**9,
                                   'model':lane.W[0], 'done':True, 'done_reason':'stop' if final == valid else 'length'}})
    monkeypatch.setattr(budget, 'paired_inputs', lambda *args: (list(range(4)), old, {}, 'p', v2))
    result, _ = budget.compare(tmp_path, out, items, {'job':budget.JOB})
    assert result['paired'] == 4 and set(result['pairs'].values()) == {1}
    assert result['baseline']['rejectedValues'] == 1 and result['higher']['malformedJson'] == 1
    assert result['higher']['empty'] == 1 and result['higher']['generationSeconds'] == 4
    row = out/'W/row-000000.json'
    bad = lane.read(row)
    lane.write(row, {**bad, 'values': None})
    with pytest.raises(ValueError, match='Replayed validity'):
        budget.compare(tmp_path, out, items, {'job':budget.JOB})


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows native identity')
def test_exact_native_creation_time():
    owner = lane.identity()
    assert follow.native_alive(owner)
    assert not follow.native_alive({**owner, 'createdTicks': owner['createdTicks']+1})


def test_delivery_waits_for_native_exit_and_rejects_artifact_changes(tmp_path, monkeypatch):
    root = tmp_path/'.local/word-table/workstation'
    out = root/'jobs'/budget.JOB
    control = root/'followups'/budget.JOB
    (out/'comparison').mkdir(parents=True)
    (out/'W').mkdir()
    control.mkdir(parents=True)
    public = tmp_path/'docs/exchange/result-sheets/G3-thinking-budget.json'
    public.parent.mkdir(parents=True)
    owner = {'job':budget.JOB, 'commit':'c', 'lock':str(root/'gpu.lock')}
    result = {'paired':20, 'higher':{'valid':7}}
    lane.write(out/'owner.json', owner)
    lane.write(out/'W/protocol.json', {})
    lane.write(out/'comparison/aggregate.json', result)
    lane.write(out/'comparison/baseline-pins.json', {'sample':'b'})
    lane.write(out/'artifacts.json', {'files':{'W/protocol.json':lane.pin(out/'W/protocol.json')}})
    lane.write(out/'receipt.json', {'owner':owner, 'status':'complete', 'roles':{'W':{'valid':7}},
                                    'artifactsPin':lane.pin(out/'artifacts.json')})
    lane.write(out/'complete.json', {'receiptPin':lane.pin(out/'receipt.json')})
    monkeypatch.setattr(follow, 'native_alive', lambda owner: True)
    with pytest.raises(ValueError, match='native exit'):
        follow.deliver(root, out, control, [], {'commit':'c'})
    assert not public.exists()
    monkeypatch.setattr(follow, 'native_alive', lambda owner: False)
    monkeypatch.setattr(budget, 'compare', lambda *args: (result, {'sample':'b'}))
    with lane.lease(root/'gpu.lock'), pytest.raises(lane.Busy):
        follow.deliver(root, out, control, [], {'commit':'c'})
    assert not public.exists()
    follow.deliver(root, out, control, [], {'commit':'c'})
    assert lane.read(control/'verified.json')['aggregatePin'] == lane.pin(public)
    assert lane.read(public)['sourceReceiptPin'] == lane.pin(out/'receipt.json')
    lane.write(out/'W/protocol.json', {'mutated':True})
    with pytest.raises(ValueError, match='artifact differs'):
        follow.deliver(root, out, control, [], {'commit':'c'})
