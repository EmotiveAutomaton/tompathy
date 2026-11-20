import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
import word_table_g3_budget as budget
import word_table_g3_follow as follow
import word_table_g3_resume as resume
import word_table_lane as lane
from word_table_rd2 import template


def test_resume_only_requests_unsaved_rows_with_original_options(tmp_path, monkeypatch):
    definition = template({'prompt':'A','steps':False,'think':True})
    guard = type('Guard',(),{'check':lambda self:None})()
    reports = [{'id':str(i),'text':'text'} for i in range(2)]
    monkeypatch.setattr(lane.core,'read_model',lambda *args:None)
    monkeypatch.setattr(lane.core,'api',lambda *args,**kwargs:{'models':[]})
    monkeypatch.setattr(lane,'fit_or_wait',lambda *args:1)
    calls = []
    def read_request(route, request, guard, seconds):
        calls.append((route,request,seconds))
        return {'response':'{}','done':True}
    monkeypatch.setattr(lane.core,'guarded_request',read_request)
    kwargs = {'template':definition,'token_lengths':{'0':1,'1':1}}
    out = tmp_path/'V5'
    lane.rate(tmp_path,out,reports[:1],'W','G3',{'variant':'V5'},guard,**kwargs)
    old = (out/'W/row-000000.json').read_bytes()
    lane.rate(tmp_path,out,reports,'W','G3',{'variant':'V5'},guard,g3_recovery='a'*40,**kwargs)
    assert [c[2] for c in calls] == [120,300]
    assert calls[0][1] == calls[1][1] and calls[1][1]['options']['num_predict'] == 1024
    assert (out/'W/row-000000.json').read_bytes() == old
    assert lane.read(out/'W/row-000001.json')['execution']['continuationCommit'] == 'a'*40
    with pytest.raises(ValueError,match='V5 repair'):
        lane.rate(tmp_path,tmp_path/'wrong',reports,'W','G3',{'variant':'V2'},guard,g3_recovery='a'*40,**kwargs)


def test_copy_rejects_wrong_durable_count_before_inference(tmp_path):
    src = tmp_path/'source'
    folder = src/'V0/W'
    folder.mkdir(parents=True)
    lane.write(folder/'protocol.json',{'variant':'V0','modelPin':lane.W[1]})
    with pytest.raises(ValueError,match='prefix'):
        resume.restore(src,tmp_path/'dest',[],None)


def test_handoff_requires_full_continued_source_and_two_commits(tmp_path, monkeypatch):
    root = tmp_path/'workstation'
    parent = root/'jobs'/resume.ATTEMPT
    parent.mkdir(parents=True)
    (root/'inputs').mkdir()
    owner = {'job':resume.ATTEMPT,'commit':'e'*40,'lock':str(root/'gpu.lock')}
    prior = {'entry':{'commit':budget.ORIGINAL},'owner':{'job':'G3'}}
    monkeypatch.setattr(resume,'source',lambda root:prior)
    lane.write(root/'inputs/G3-resume-a-execution.json',{'commit':owner['commit']})
    lane.write(parent/'restored.json',{'files':{}})
    lane.write(parent/'owner.json',owner)
    chain = {'attempt':resume.ATTEMPT,'executionCommit':owner['commit'],'sourceReceiptPin':resume.SOURCE_RECEIPT,
             'sourceOwner':prior['owner'],'restoredInventoryPin':lane.pin(parent/'restored.json')}
    receipt = {'status':'complete','owner':owner,'entry':prior['entry'],'continuation':chain,
               'roles':{f'V{i}':{'rows':600} for i in range(6)}}
    def save():
        lane.write(parent/'receipt.json',receipt)
        lane.write(parent/'complete.json',{'receiptPin':lane.pin(parent/'receipt.json')})
    save()
    assert budget.terminal_source(root,resume.ATTEMPT)[0] == receipt
    receipt['roles']['V5']['rows'] -= 1
    save()
    with pytest.raises(ValueError,match='pinned original'):
        budget.terminal_source(root,resume.ATTEMPT)
    with pytest.raises(ValueError,match='Unknown G3 predecessor'):
        follow.execution_code(root,{},'unregistered')


@pytest.mark.parametrize(('free','occupied','commit','eligible'),[
    (4500,0,32,False),(6080,1,32,False),(6080,0,8,False),(6080,0,32,True)])
def test_workstation_admission_uses_measured_reader_fit(tmp_path,monkeypatch,free,occupied,commit,eligible):
    path = tmp_path/'jobs/G3/V5'
    path.mkdir(parents=True)
    lane.write(path/'progress.json',{'residentBytes':5994383931})
    monkeypatch.setattr(resume.subprocess,'check_output',lambda *args,**kwargs:str(free))
    monkeypatch.setattr(lane.core,'api',lambda *args,**kwargs:{'models':[{}]*occupied})
    monkeypatch.setattr(lane,'commit_free_gib',lambda:commit)
    assert resume.capacity(tmp_path)['eligible'] is eligible
