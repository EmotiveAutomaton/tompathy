"""New full-data worry head, three preregistered transfer contrasts, research pack."""
import gc
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from ...packs.registry import sha256
from ...packs.v2 import code_pin, load_pack
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .envent import load as envent
from .rated import inputs
from .regression import fit_encoder
from .tp10 import neutral_texts


def batch_predictions(texts, identity, directory, predict, check):
    """One-target predictions are durable after each completed batch."""
    directory=Path(directory)
    key=hashlib.sha256(json.dumps({'texts':list(texts),'identity':identity},sort_keys=True).encode()).hexdigest()
    result=[]
    for start in range(0,len(texts),16):
        check();path=directory/f'{start:08d}.json'
        if path.exists():
            row=json.loads(path.read_text(encoding='utf8'))
            if row['key']!=key or row['start']!=start: raise ValueError('Prediction source changed')
            values=np.asarray(row['values'],float)
        else:
            values=np.asarray(predict(texts[start:start+16]))
        if values.shape!=(min(16,len(texts)-start),1) or not np.isfinite(values).all():
            raise ValueError('Invalid scalar predictions')
        if not path.exists(): save_json(path,{'key':key,'start':start,'values':values.tolist()})
        result.append(values)
    return np.concatenate(result) if result else np.empty((0,1))


def export_pack(head, models, source, benchmark, output, nothing, check):
    """Export the exact normalized-vector linear calculation in key-scale units."""
    root = output/'rp-worry-1'
    root.mkdir(exist_ok=False)
    shutil.copytree(head/'encoder',root/'encoder')
    with np.load(head/'head.npz',allow_pickle=False) as arrays:
        weights=arrays['weights']*arrays['scale'][:,None]
        bias=arrays['bias']*arrays['scale']+arrays['mean']
    np.savez(root/'head.npz',weights=weights,bias=bias)
    shutil.copyfile(source/'LICENSE',root/'DATA_LICENSE.txt')
    # Preserve the original model card's license declaration rather than inventing
    # a license text for exported weights.
    shutil.copyfile(models/'minilm/README.md',root/'ENCODER_LICENSE.md')
    shutil.copyfile(benchmark/'receipt.json',root/'benchmark.json')
    save_json(root/'training.json',{'card':'TP26','headEvaluated':False,
        'benchmarkSourcePin':sha256(benchmark/'receipt.json'),'sourceHeadPin':sha256(head/'head.npz'),
        'training':'2500 writers; three fixed epochs; seed23; cap128; same TP16 hyperparameters',
        'interpretation':'Worry proposed as Stress; not a measure of this writer'})
    files={}
    for p in sorted((root/'encoder').rglob('*')):
        if p.is_file():
            check();files[p.relative_to(root).as_posix()]=sha256(p)
    def license(name,file,source,kind,commercial):
        return {'name':name,'file':file,'source':source,'license':kind,
                'license_sha256':sha256(root/file),'commercial_use':commercial}
    original=json.loads((models/'minilm/intake.json').read_text())
    bench=json.loads((benchmark/'receipt.json').read_text())
    score=bench['rows']['fine_tuned']['targets']['worry']
    manifest={'name':'rp-worry-1','version':'reader-pack-2','task':'scalar','labels':['worry'],
        'encoder':{'id':original['id'],'revision':'TP26-full-data-'+sha256(head/'best.safetensors'),
            'kind':'sentence-transformers','files':files,
            'sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'license':license('MiniLM model card','ENCODER_LICENSE.md',original['source'],'apache-2.0',True)},
        'head':{'file':'head.npz','sha256':sha256(root/'head.npz')},'token_cap':128,
        'reading_id':'S1','range':[1,9],'unit':'writer-rated worry, 1 low to 9 high',
        'key':{'corpus':'Real World Worry Dataset, phase 1','labelled_by':'writers own worry ratings','n':2500},
        'score':{'metric':'writer-held-out R-squared (five TP16 folds; packed head unscored)',
            'value':score['r2'],'interval':score['r2_interval']},
        'people':{},'floor':{'constant_r2':bench['rows']['constant']['targets']['worry']['r2']},
        'nothing_here':{'theme_free_mean_normalized':float(np.clip((nothing['mean']-1)/8,0,1))},
        'training':[license('Worry source','DATA_LICENSE.txt','Real World Worry Dataset','gpl-3.0; research-only protocol',False)],
        'research_only':True,'status':'research','mapping':{'status':'proposed','source':'TP26: worry proposed as Stress; Round24; not a measure of this writer'},
        'code_pin':code_pin()}
    save_json(root/'pack.json',manifest)
    pack=load_pack(root)
    return {'name':root.name,'pin':pack.pin,'manifestPin':sha256(root/'pack.json'),
            'headPin':sha256(root/'head.npz'),'trainingPin':sha256(root/'training.json'),
            'benchmarkPin':sha256(root/'benchmark.json'),'packedHeadEvaluated':False,'status':'research'}


def run(root, models, output, check, *, benchmark, corpus, ed_root, go_root, prepared):
    root,models,output,benchmark=map(Path,(root,models,output,benchmark))
    verified=json.loads((benchmark/'exit-verification.json').read_text())
    if not all(verified.get(k) for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent')):
        raise ValueError('TP16 requires verified native exit and exact releases')
    bench=json.loads((benchmark/'receipt.json').read_text())
    if bench['card']!='TP16' or bench['status']!='complete' or not bench['rows']['fine_tuned']['stretch']:
        raise ValueError('TP16 benchmark is not qualified for this refit')
    texts,y,writers,_,identity=inputs(root,'TP16')
    if identity!=bench['source'] or not np.isfinite(y).all() or y.min()<1 or y.max()>9:
        raise ValueError('Worry source or key range differs')
    original=json.loads((models/'minilm/intake.json').read_text())
    for name,pin in original['files'].items():
        check()
        if sha256(models/'minilm'/name)!=pin: raise ValueError('Original MiniLM bytes changed')
    receipt={'card':'TP26','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Full-data worry refit and known-group checks; no independent Stress key or maker estimate',
        'source':identity,'benchmarkSourcePin':sha256(benchmark/'receipt.json'),
        'protocol':{'fit':'All 2500 writers, 3 fixed epochs, seed23, original TP16 settings; packed head unscored',
                    'scale':[1,9],'cap':128,'group_bar':.7,'plain_prose_bar':None,
                    'known_groups':'Unchanged predeclared labels; unambiguous positive versus negative; all released splits'},
        'groups':{}}
    save=lambda:save_json(output/'receipt.json',receipt)
    save();save_json(output/'phase.json',{'phase':'full-data-worry-fit'})
    _,meta,predict=fit_encoder(models/'minilm',texts,y,np.arange(len(y)),np.array([],int),writers,
                              output/'full-head',check,final=True)
    receipt['training']=meta;save()
    def evaluate(name,texts,positive,negative,source):
        positive,negative=np.asarray(positive,bool),np.asarray(negative,bool)
        keep=positive ^ negative
        items=[text for text,yes in zip(texts,keep) if yes]
        truth=positive[keep].astype(int)
        if len(np.unique(truth))!=2: raise ValueError('Known-group check requires both groups')
        save_json(output/'phase.json',{'phase':'known-group','group':name,'n':len(items)})
        values=batch_predictions(items,{'source':source,'head':sha256(output/'full-head/head.npz')},
            output/'batches'/name,predict,check)[:,0]
        auc=float(roc_auc_score(truth,values))
        np.savez(output/(name+'-known-group.npz'),scores=values,truth=truth)
        receipt['groups'][name]={'n':len(items),'positive':int(truth.sum()),'negative':int((truth==0).sum()),
            'overlap_excluded':int((positive&negative).sum()),'auc':auc,'bar':.7,'passed':auc>=.7,'source':source}
        save()
    data=envent(corpus);f=data.reports
    evaluate('envent',f.hidden_emo_text.tolist(),f.emotion.isin(['fear','sadness','anger']),
             f.emotion.isin(['joy','pride','relief']),data.pins)
    del data,f;gc.collect()
    f,pin=ed_situations(ed_root)
    evaluate('ed',f.text.tolist(),f.label.isin(['anxious','afraid','apprehensive','terrified']),
             f.label.isin(['content','joyful','grateful']),pin)
    del f;gc.collect()
    f,truth,labels,pin=go_comments(go_root)
    eligible=(f.source_split!='unreleased').to_numpy()
    positive=(truth[:,labels.index('nervousness')]|truth[:,labels.index('fear')]).astype(bool)&eligible
    negative=truth[:,labels.index('neutral')].astype(bool)&eligible
    evaluate('go',f.text.tolist(),positive,negative,pin)
    del f,truth;gc.collect()
    themes,_,_=neutral_texts(prepared)
    values=batch_predictions(themes,{'head':sha256(output/'full-head/head.npz')},output/'batches/theme-free',predict,check)[:,0]
    receipt['nothing_here']={'n':len(values),'mean':float(values.mean()),'quantiles':np.quantile(values,[0,.25,.5,.75,1]).tolist(),
                             'keyRange':[1,9],'bar':None,'not_a_stress_measure':True}
    receipt['transferPassed']=all(g['passed'] for g in receipt['groups'].values())
    save()
    save_json(output/'phase.json',{'phase':'research-pack-export'})
    receipt['pack']=export_pack(output/'full-head',models,root,benchmark,output,receipt['nothing_here'],check)
    receipt['status']='complete';save()
