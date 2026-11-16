import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from tompathy_engine.eval.back_half.reporting import save_json


@pytest.mark.parametrize('allow,converges', [(0,True),(2000,True),(2000,False)])
def test_population_continuation_keeps_default_failure_and_rejects_unconverged(monkeypatch,allow,converges):
    from tompathy_engine.eval import harness
    calls=[]
    def minimize(fun,x,jac,method,options):
        calls.append((np.array(x),options))
        loss,gradient=fun(x)
        assert np.isfinite(loss) and np.isfinite(gradient).all()
        return SimpleNamespace(success=len(calls)>1 and converges,status=1,
            nit=500 if len(calls)==1 else 22,message='STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT',
            x=np.full_like(x,.125))
    monkeypatch.setattr(harness,'minimize',minimize)
    records=[{'key':str(i),'writer':str(i),'session':'s','prompt':'p','document':'text',
        'menu':['a','b','c','d','e'],'handling':'accept','decision_index':i,
        'open_at':f'2026-01-01T00:00:0{2*i}+00:00',
        'resolved_at':f'2026-01-01T00:00:0{2*i+1}+00:00'} for i in range(2)]
    if allow and converges:
        _,meta=harness.handling_prequential(records,population_extra_iterations=allow)
        assert meta['optimizer_continuations']==[{'first_iterations':500,'additional_iterations':22,'success':True}]
        assert np.all(calls[1][0]==.125)
    else:
        with pytest.raises(ValueError,match='population MAP failed'):
            harness.handling_prequential(records,population_extra_iterations=allow)
    assert [o['maxiter'] for _,o in calls]==([500,2000] if allow else [500])


def test_restore_pins_copies_and_refuses_changed_or_completed_source(tmp_path):
    from tompathy_engine.eval.readers import tp19_resume
    from tompathy_engine.packs.registry import sha256
    source=tmp_path/'source'; reader=tmp_path/'reader'
    ok=dict.fromkeys(('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent'),True)
    save_json(reader/'receipt.json',{'card':'TP10-L3','status':'complete','selected_seed':47,
        'rows':{'47':{'files':{}}}})
    save_json(reader/'complete.json',{});save_json(reader/'exit-verification.json',ok)
    save_json(reader/'seed-47/head.npz',{})
    identity={'selectedSeed':47,'sourceReceiptPin':sha256(reader/'receipt.json'),
        'headPin':sha256(reader/'seed-47/head.npz')}
    relative='tompathy_engine/features/deterministic.py'
    live=Path(tp19_resume.__file__).resolve().parents[3]/relative
    target=source/'code'/relative;target.parent.mkdir(parents=True);target.write_bytes(live.read_bytes())
    save_json(source/'plan.json',{'snapshotFiles':{relative:sha256(target)}})
    save_json(source/'receipt.json',{'card':'TP19','status':'running','motives':None,'reader':identity,
        'rows':{str(i):{'choices':2,**({'handling':{}} if i==0 else {})} for i in range(3)}})
    save_json(source/'failed.json',{'type':'ValueError','reason':'Prequential population MAP failed'})
    save_json(source/'exit-verification.json',ok)
    save_json(source/'option-features.json',{'reader':identity,'motive':None,'names':[],'rows':{}})
    for name in ['ledger/fixture.json','intake.json','handling-0.json']:save_json(source/name,{})
    for i in range(3):np.save(source/f'choice-{i}.npy',np.full((2,5),.2))
    output=tmp_path/'continued'
    _,report,_=tp19_resume.restore(source,output,reader)
    for name,pin in json.loads((output/'continuation-artifacts.json').read_text())['files'].items():
        assert sha256(source/name)==sha256(output/name)==pin
    assert report['continuation']['completedChoiceRowsReused']==3
    target.write_text('changed')
    with pytest.raises(ValueError,match='snapshot changed'):tp19_resume.restore(source,tmp_path/'bad',reader)
    target.write_bytes(live.read_bytes());save_json(source/'complete.json',{})
    with pytest.raises(ValueError,match='incomplete'):tp19_resume.restore(source,tmp_path/'completed',reader)


def test_full_tp19_resume_skips_encoding_choices_and_finished_handling(tmp_path,monkeypatch):
    from tompathy_engine.eval.readers import tp19, tp19_resume
    from tompathy_engine.ledger.ids import digest
    names=[f'label_{i}' for i in range(13)]+[f'rated_{tp19.RATINGS.index(r)}' for r in tp19.READABLE]
    records=[];decisions=[];saved={'reader':{},'motive':None,'names':names,'rows':{}}
    for i in range(5):
        row={'key':str(i),'writer':str(i),'session':'s','prompt':'p','document':'context',
            'menu':['a','b','c','d','e'],'handling':'accept','open_at':f'2026-01-01T00:00:{2*i:02}+00:00',
            'resolved_at':f'2026-01-01T00:00:{2*i+1:02}+00:00'}
        records.append(row)
        options=[SimpleNamespace(origin='ai',content_ref='text',option_id=f'{i}-{j}') for j in range(5)]
        options.append(SimpleNamespace(origin='maker',content_ref=None,option_id=f'{i}-own'))
        decisions.append(SimpleNamespace(decision_id=str(i),options=options,taken=f'{i}-0',model_dump=lambda mode,i=i:{'i':i}))
        saved['rows'][str(i)]={o.option_id:{**dict.fromkeys(names,.1),'reader_missing':0.} for o in options[:5]}
        saved['rows'][str(i)][f'{i}-own']={'reader_missing':1.}
    class Ledger:
        def __init__(self,_):pass
        def snapshot(self):return self
        def rows(self,name):return [SimpleNamespace(source_dataset='coauthor')] if name=='Maker' else decisions
    monkeypatch.setattr(tp19,'Ledger',Ledger);monkeypatch.setattr(tp19,'handling_records',lambda _:records)
    monkeypatch.setattr(tp19,'load_head',lambda *_:pytest.fail('Completed encoder called'))
    monkeypatch.setattr(tp19,'conditional_forecasts',lambda *_:pytest.fail('Completed choice fitting called'))
    def restore(source,output,reader,**kwargs):
        return tmp_path,previous,saved
    previous={}
    monkeypatch.setattr(tp19_resume,'restore',restore)
    # Build exactly the original report once with fake encoding and fits, then
    # use it as a stopped source. This fixture performs no model inference.
    monkeypatch.setattr(tp19,'load_head',lambda *_:(None,lambda texts,check:(np.full((len(texts),13),.1),np.full((len(texts),21),.1)),{}))
    monkeypatch.setattr(tp19,'conditional_forecasts',lambda x,y,w,c:np.full((5,5),.2))
    def handling(rows,**kwargs):
        result=[{'module':module,'decision':r['key'],'maker':r['writer'],'log_loss':1.0}
            for r in rows for module in ['backbone','population']]
        return result,{'decisions':5}
    monkeypatch.setattr(tp19,'handling_prequential',handling)
    monkeypatch.setattr(tp19,'bow_forecasts',lambda *_:np.full((5,5),.2))
    first=tmp_path/'first';tp19.run(tmp_path,None,first,lambda:None)
    previous=json.loads((first/'receipt.json').read_text());previous['status']='running';previous.pop('controls')
    for i in (1,2):previous['rows'][str(i)].pop('handling');previous['gains'].pop(f'handling_{i}_over_{i-1}')
    previous['continuation']={'completedChoiceRowsReused':3}
    target=tmp_path/'continued';target.mkdir()
    import shutil
    for name in ['choice-0.npy','choice-1.npy','choice-2.npy','handling-0.json']:shutil.copyfile(first/name,target/name)
    monkeypatch.setattr(tp19,'load_head',lambda *_:pytest.fail('Completed encoder called'))
    monkeypatch.setattr(tp19,'conditional_forecasts',lambda *_:pytest.fail('Completed choice fitting called'))
    calls=[]
    def unfinished(rows,**kwargs):
        assert kwargs['additional_features'] is not None
        calls.append(1);return handling(rows,**kwargs)
    monkeypatch.setattr(tp19,'handling_prequential',unfinished)
    tp19.run(None,None,target,lambda:None,resume=first)
    final=json.loads((target/'receipt.json').read_text())
    assert len(calls)==2 and final['status']=='complete'
    assert final['gains']['choice_1_over_0']==previous['gains']['choice_1_over_0']
    assert final['sourcePin']==digest([d.model_dump(mode='json') for d in decisions])
