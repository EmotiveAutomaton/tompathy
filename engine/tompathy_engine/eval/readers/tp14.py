"""Two published motive instruments on commissioned public text; never maker wants."""
import gc
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from scipy.special import expit
from scipy.stats import pearsonr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations
from .envent import RATINGS, load
from .tp11 import PAIRS, grouped_auc

MOTIVES=('achievement','affiliation','power')
SIGNS={'pride-joy':[(0,1),(2,1)],'guilt-shame':[(1,1)],'fear-sadness':[(1,-1)],
       'anger-disgust':[(2,1)],'trust-joy':[(1,1)]}


def verify_model(root):
    root=Path(root)
    intake=json.loads((root/'intake.json').read_text(encoding='utf8'))
    for name,pin in intake['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path)!=pin:
            raise ValueError('Motive model hash differs')
    return intake


def motive_config(root):
    """Preserve the publisher's binary labels when id2label was omitted."""
    from transformers import AutoConfig
    raw=json.loads((Path(root)/'config.json').read_text(encoding='utf8'))
    labels=raw.get('label2id')
    reverse={str(value):key for key,value in (labels or {}).items()}
    if (labels!={'No':0,'Yes':1} or raw.get('num_labels',2)!=2
            or raw.get('id2label',reverse)!=reverse):
        raise ValueError('Published motive output labels differ')
    # Newer Transformers generates LABEL_0/1 if id2label is missing, replacing
    # the saved label2id. Supply the exact inverse without changing source bytes.
    return AutoConfig.from_pretrained(str(root),local_files_only=True,
        trust_remote_code=False,label2id=labels,id2label={int(k):v for k,v in reverse.items()})


def instrument(root, name, converted):
    import torch
    torch.set_num_threads(2)
    identity=verify_model(root)
    if name=='motive-setfit':
        from sentence_transformers import SentenceTransformer
        converted=Path(converted)
        receipt=json.loads((converted/'conversion.json').read_text(encoding='utf8'))
        if (receipt['sourceHeadPin']!=identity['files']['model_head.pkl']
                or receipt['headPin']!=sha256(converted/'head.npz')):
            raise ValueError('Converted motive head binding differs')
        with np.load(converted/'head.npz',allow_pickle=False) as arrays:
            weight,bias=arrays['weights'].copy(),arrays['bias'].copy()
        model=SentenceTransformer(str(root),device='cpu',local_files_only=True,trust_remote_code=False)
        model.max_seq_length=512
        model.eval()

        def score(texts):
            with torch.inference_mode():
                x=model.encode(texts,batch_size=8,normalize_embeddings=False,show_progress_bar=False)
            return expit(x@weight.T+bias)[:,:3]
        identity['headConversion']=receipt
    else:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
        model=AutoModelForSequenceClassification.from_pretrained(str(root),local_files_only=True,
                 trust_remote_code=False,use_safetensors=True,config=motive_config(root)).to('cpu').eval()
        if model.config.label2id!={'No':0,'Yes':1}:
            raise ValueError('Published motive output labels differ')

        def score(texts):
            batch=tokenizer(texts,padding=True,truncation=True,max_length=512,return_tensors='pt')
            with torch.inference_mode():
                return model(**batch).logits.softmax(dim=1)[:,1:2].numpy()
    identity.update(device='cpu',threads=2,token_cap=512,batch=8,
                    score='Independent motive presence probability, fixed 0.5 classification threshold',
                    versions={n:importlib.metadata.version(n) for n in ('torch','transformers','sentence-transformers','numpy')})
    return score,identity


def score_instrument(root,name,converted,texts,output,check):
    check()
    score,identity=instrument(root,name,converted)
    dimensions=3 if name=='motive-setfit' else 1
    values=np.full((len(texts),dimensions),np.nan)
    elapsed=0.
    timings={}
    start=0
    last_saved=0
    while start<len(texts):
        check()
        end=min(len(texts),start+8,150 if start<150 else len(texts))
        t=time.perf_counter()
        batch=score(texts[start:end])
        elapsed+=time.perf_counter()-t
        if batch.shape!=(end-start,dimensions) or not np.isfinite(batch).all() or ((batch<0)|(batch>1)).any():
            raise ValueError('Invalid motive probability output')
        values[start:end]=batch
        start=end
        if end==150:
            timings={'seconds150':elapsed,'excludes_loading':True,'includes_tokenization':True,
                     'offline_only':elapsed>5,'threads':2}
        # The 150-text timing boundary shifts later batches off multiples of 64.
        if end-last_saved>=64 or end==len(texts):
            np.save(output/f'{name}-partial.npy',values)
            last_saved=end
        save_json(output/'progress.json',{'instrument':name,'completed':end,'total':len(texts),
                                         'forward_seconds':elapsed})
    np.save(output/f'{name}-scores.npy',values)
    save_json(output/f'{name}-identity.json',{'model':identity,'timing':timings,
                'scorePin':sha256(output/f'{name}-scores.npy'),
                'orderedTextPin':hashlib.sha256(json.dumps(texts,ensure_ascii=False).encode()).hexdigest()})
    del score
    gc.collect()
    return values,identity,timings


def twins(frame,values,check):
    result={}
    for a,b in PAIRS:
        check()
        ix=np.flatnonzero(frame.emotion.isin([a,b]))
        y=(frame.iloc[ix].emotion==a).to_numpy(int)
        writers=frame.iloc[ix].prolific_id.to_numpy()
        ratings=frame.iloc[ix][RATINGS].to_numpy(float)
        matrices={'constant':np.ones((len(ix),1)),'ratings':ratings,
                  'ratings_plus_motives':np.c_[ratings,values[ix]]}
        scores={name:np.zeros(len(ix)) for name in matrices}
        aucs={name:[] for name in matrices}
        for tr,te in GroupKFold(5).split(ix,y,writers):
            check()
            for name,x in matrices.items():
                if name=='constant':
                    z=np.full(len(te),.5)
                else:
                    mean,sd=x[tr].mean(axis=0),x[tr].std(axis=0)+1e-9
                    model=LogisticRegression(C=1,max_iter=2000).fit((x[tr]-mean)/sd,y[tr])
                    z=model.decision_function((x[te]-mean)/sd)
                scores[name][te]=z
                aucs[name].append(float(roc_auc_score(y[te],z)))
        key=f'{a}-{b}'
        differences=values[ix[y==1]].mean(axis=0)-values[ix[y==0]].mean(axis=0)
        gain=float(np.mean(aucs['ratings_plus_motives'])-np.mean(aucs['ratings']))
        signs=all(differences[column]*direction>0 for column,direction in SIGNS[key])
        result[key]={'n':len(ix),'writers':len(np.unique(writers)),
                     'rows':{name:{'mean_fold_auc':float(np.mean(aucs[name])),**grouped_auc(y,z,writers)}
                             for name,z in scores.items()},
                     'mean_motive_differences':dict(zip(MOTIVES,differences.tolist())),
                     'gain':gain,'predicted_signs':SIGNS[key],'signs_passed':signs,
                     'passed':gain>=.03 and signs}
    return result


def run(directory,ed_directory,models,prepared,converted,twins_job,output,check):
    output,models,prepared=Path(output),Path(models),Path(prepared)
    corpus=load(directory)
    twins_job=Path(twins_job)
    previous=json.loads((twins_job/'receipt.json').read_text(encoding='utf8'))
    exit_check=json.loads((twins_job/'exit-verification.json').read_text(encoding='utf8'))
    if (previous['card']!='TP11' or previous['status']!='complete' or previous['scope']!=corpus.summary()
            or not all(exit_check.get(k) for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent'))):
        raise ValueError('TP14 needs completed source-bound TP11 control rows')
    frame=corpus.reports
    ed,ed_identity=ed_situations(ed_directory)
    ed_ids=ed.id.tolist()
    crowd_ids=frame.text_id.tolist()
    ed=ed.iloc[sorted(range(len(ed)),key=lambda i:hashlib.sha256(str(ed_ids[i]).encode()).hexdigest())[:2000]]
    crowd_ix=np.array(sorted(range(len(frame)),key=lambda i:hashlib.sha256(str(crowd_ids[i]).encode()).hexdigest())[:2000])
    theme_path=Path('engine/validation/q10-empty-v2.items.json')
    themes=json.loads(theme_path.read_text(encoding='utf8'))
    neutral_path=prepared/'readers-neutral-before.json'
    neutral_intake=json.loads((prepared/'neutral-intake.json').read_text(encoding='utf8'))
    if sha256(neutral_path)!=neutral_intake['outputPin']:
        raise ValueError('Neutral before rows changed')
    arxiv=[r for r in json.loads(neutral_path.read_text(encoding='utf8')) if r['source']=='arxiv']
    texts=frame.hidden_emo_text.tolist()+ed.text.tolist()+[r['text'] for r in themes]+[r['before'] for r in arxiv]
    report={'card':'TP14','status':'running','scope':{'crowd':len(frame),'agreement_per_corpus':2000,
            'constructed':len(themes),'arxiv':len(arxiv),'corpus':corpus.summary(),'ed':ed_identity,
            'themePin':sha256(theme_path),'neutralPin':sha256(neutral_path)},
            'rows':{},'mapping':{'status':'proposed','affiliation':'N3','power':'N4','achievement':None},
            'twinsControlReceiptPin':sha256(twins_job/'receipt.json'),
            'threshold':.5,'productionAdmission':False,'ledger':'no ledger row',
            'human_reference':'Expert-coded validation corpus unavailable; published person-level correlations are not a per-text floor here',
            'pack':'pending; page content only, never self-stated wants or maker need estimates'}
    save_json(output/'receipt.json',report)
    scores={}
    for name in (*MOTIVES,'motive-setfit'):
        values,identity,timing=score_instrument(models/name,name,converted,texts,output,check)
        scores[name]=values
        report['rows'][name]={'identity':identity,'timing':timing,'scorePin':sha256(output/f'{name}-scores.npy')}
        save_json(output/'receipt.json',report)
    harmony=np.concatenate([scores[m] for m in MOTIVES],axis=1)
    setfit=scores['motive-setfit']
    agreement={}
    for name,ix in [('Crowd-enVENT',crowd_ix),('EmpatheticDialogues',np.arange(6600,8600))]:
        agreement[name]={m:(float(pearsonr(harmony[ix,j],setfit[ix,j]).statistic)
                            if np.std(harmony[ix,j])>0 and np.std(setfit[ix,j])>0 else None)
                         for j,m in enumerate(MOTIVES)}
    report['agreement']={'correlations':agreement,'passed':all(v is not None and v>=.5 for row in agreement.values() for v in row.values())}
    report['instruments']={}
    theme_start=6600+2000
    quiet=np.array([i for i,r in enumerate(themes) if not r['expected']])+theme_start
    for name,values in [('HarmonyLab',harmony),('SetFit',setfit)]:
        check()
        groups=twins(frame,values[:6600],check)
        for pair,result in groups.items():
            result['rows']['bow']=previous['twins'][pair]['rows']['bow']
            result['people']=previous['twins'][pair]['people']
        quiet_count=int((values[quiet]<.5).all(axis=1).sum())
        arxiv_quiet=float((values[-len(arxiv):]<.5).all(axis=1).mean()) if arxiv else None
        themes_summary={label:{'n':sum(label in r['expected'] for r in themes),
                'means':dict(zip(MOTIVES,values[[theme_start+i for i,r in enumerate(themes) if label in r['expected']]].mean(axis=0).tolist()))}
                for label in sorted({l for r in themes for l in r['expected']})}
        report['instruments'][name]={'twins':groups,'known_groups_passed':sum(r['passed'] for r in groups.values())>=3,
            'neutral':{'B13_silent':quiet_count,'B13_n':len(quiet),'arxiv_silent_rate':arxiv_quiet,'arxiv_n':len(arxiv),
                       'coverage_complete':neutral_intake['coverageComplete'],
                       'observed_passed':quiet_count>=36 and arxiv_quiet is not None and arxiv_quiet>=.9},
            'constructed_themes':themes_summary}
        save_json(output/'receipt.json',report)
    # Only this commissioned ID/score table is eligible for local IM1 handoff.
    import pandas as pd
    im1=pd.DataFrame({'text_id':frame.text_id})
    for name,values in [('harmony',harmony),('setfit',setfit)]:
        for i,motive in enumerate(MOTIVES):
            im1[name+'_'+motive]=values[:6600,i]
    im1.to_csv(output/'IM1.csv',index=False)
    report['IM1']={'rows':len(im1),'pin':sha256(output/'IM1.csv'),'columns':im1.columns.tolist(),
                   'handoff':'pending separate verified local copy; no text or writer IDs included'}
    report['status']='complete'
    report['pack']='No independent public per-text expert key; benchmarked motive instruments only. Any future pack remains offline-only when measured >5 seconds/150.'
    save_json(output/'receipt.json',report)
    return report
