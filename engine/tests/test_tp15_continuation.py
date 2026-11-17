import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tompathy_engine.eval.back_half import reporting
from tompathy_engine.eval.readers import rated, tp15_resume


def launcher():
    spec=importlib.util.spec_from_file_location('reader_launcher',Path(__file__).parents[2]/'scripts/engine-readers-job.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('failures', [1,5,6])
def test_heartbeat_bounded_permission_retry(tmp_path,monkeypatch,failures):
    module=launcher()
    calls=[]
    slept=[]
    def save(*_):
        calls.append(1)
        if len(calls)<=failures:
            error=PermissionError('locked');error.winerror=5;raise error
    monkeypatch.setattr(reporting,'save_json',save)
    monkeypatch.setattr(module.time,'sleep',slept.append)
    resources=[]
    def headroom():
        resources.append(1);return {'commitGiB':24}
    if failures==6:
        with pytest.raises(PermissionError):module.heartbeat(tmp_path,float('inf'),headroom)
    else:module.heartbeat(tmp_path,float('inf'),headroom)
    assert len(calls)==min(failures+1,6)==len(resources)
    assert len(slept)==min(failures,5)


def test_heartbeat_stop_and_floor_are_not_bypassed(tmp_path,monkeypatch):
    module=launcher()
    def locked(*_):
        error=PermissionError('locked');error.winerror=32;raise error
    monkeypatch.setattr(reporting,'save_json',locked)
    monkeypatch.setattr(module.time,'sleep',lambda _:(tmp_path/'STOP').touch())
    with pytest.raises(RuntimeError,match='requested stop'):
        module.heartbeat(tmp_path,float('inf'),dict)
    (tmp_path/'STOP').unlink()
    def floor():raise RuntimeError('memory floor')
    with pytest.raises(RuntimeError,match='memory floor'):
        module.heartbeat(tmp_path,float('inf'),floor)
    with pytest.raises(RuntimeError,match='deadline'):
        module.heartbeat(tmp_path,0,dict)


def test_saved_batches_survive_interruption_and_reject_different_inputs(tmp_path):
    texts=[str(i) for i in range(35)]
    calls=[]
    def predict(items):
        calls.append(items)
        if len(calls)==2:raise InterruptedError('test')
        return np.array([[float(i),-float(i)] for i in items])
    with pytest.raises(InterruptedError):
        tp15_resume.batch_predictions(texts,{'pin':'same'},tmp_path,predict,lambda:None)
    assert len(list(tmp_path.glob('*.json')))==1
    calls.clear()
    def finish(items):calls.append(items);return np.array([[float(i),-float(i)] for i in items])
    result=tp15_resume.batch_predictions(texts,{'pin':'same'},tmp_path,finish,lambda:None)
    assert [len(c) for c in calls]==[16,3]
    assert result.shape==(35,2) and result[0,0]==0 and result[-1,0]==34
    with pytest.raises(ValueError,match='identity'):
        tp15_resume.batch_predictions(texts,{'pin':'different'},tmp_path,finish,lambda:None)


def test_resume_routes_without_any_completed_fit_or_gate_repetition(tmp_path,monkeypatch):
    source=tmp_path/'source';source.mkdir();(source/'forecasts.npz').touch()
    output=tmp_path/'retry';output.mkdir()
    (output/'descriptive-head').mkdir();(output/'descriptive-head/best.safetensors').write_bytes(b'mock')
    original_rows={'fine_tuned':{'primary':False,'stretch':False}}
    monkeypatch.setattr(tp15_resume,'prepare',lambda *_:({'rows':original_rows.copy(),'status':'running',
        'continuation':{'groupSourcePins':{'ed':'ed','go':'go'}}},{}))
    def forbidden(*_,**__):raise AssertionError('completed inference/gate rerun')
    for name in ('inputs','embeddings','fit_encoder','scores','ridge_forecast'):
        monkeypatch.setattr(rated,name,forbidden)
    monkeypatch.setattr(tp15_resume,'load_predict',lambda *_:lambda texts:np.ones((len(texts),2)))
    monkeypatch.setattr(tp15_resume,'ed_situations',lambda *_:(pd.DataFrame({'text':['a','b'],'label':['caring','other']}),{'intakePin':'ed'}))
    monkeypatch.setattr(tp15_resume,'go_comments',lambda *_:(pd.DataFrame({'text':['c','d','e'],'source_split':['test','test','unreleased']}),np.array([[1],[0],[1]]),['caring'],{'intakePin':'go'}))
    rated.run('TP15',tmp_path,tmp_path,output,lambda:None,resume=source)
    receipt=json.loads((output/'receipt.json').read_text())
    assert receipt['rows']==original_rows and receipt['status']=='complete'
    assert receipt['second_check']['groups']['go']['caring_n']==1
    assert receipt['second_check']['groups']['go']['other_n']==1


@pytest.mark.parametrize('kind',['complete','exit','corrupt'])
def test_restore_refuses_completed_unreleased_or_changed_source(tmp_path,kind):
    source=tmp_path/'source';source.mkdir()
    rows={k:{} for k in ('constant','bow','potion','minilm','fine_tuned')}
    reporting.save_json(source/'receipt.json',{'card':'TP15','status':'complete' if kind=='complete' else 'running','rows':rows})
    reporting.save_json(source/'failed.json',{'type':'PermissionError','reason':'[WinError 5] heartbeat.tmp'})
    reporting.save_json(source/'exit-verification.json',{k:kind!='exit' for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent')})
    reporting.save_json(source/'phase.json',{'phase':'fixed-full-data-descriptive-head'})
    (source/'forecasts.npz').write_bytes(b'changed')
    reporting.save_json(tmp_path/'source-descriptive-preservation.json',{'files':{'forecasts.npz':'wrong'}})
    with pytest.raises(ValueError,match='Only verified|Preserved TP15'):
        tp15_resume.prepare(source,tmp_path/'out',tmp_path,tmp_path,lambda:None)
