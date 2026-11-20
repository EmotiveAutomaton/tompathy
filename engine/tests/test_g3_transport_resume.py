import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
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
