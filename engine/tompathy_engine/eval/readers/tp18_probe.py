"""One conditional hidden-state probe on the preregistered fixed third of sessions."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA

from ...packs.registry import sha256
from ...preview.readers import LocalReader
from ...preview.surface import WORD
from ..back_half.attention import word_forecast
from ..back_half.metrics import fit_logistic, paired_auc, predict
from ..back_half.reporting import save_json
from .checkpoint import completed


def hidden_words(reader,text,words,check):
    encoded=reader.encode(text)
    ids,offsets=encoded['input_ids'],encoded['offset_mapping']
    states=[]
    torch=reader.torch
    bos=reader.tokenizer.bos_token_id
    if bos is None:
        bos=reader.tokenizer.eos_token_id
    if bos is None:
        raise ValueError('Reader needs an explicit start token')
    with torch.inference_mode():
        for start in range(0,len(ids),512):
            check()
            left=max(0,start-1535)
            target=ids[start:start+512]
            context=ids[left:start]
            token=torch.tensor([[bos,*context,*target]],dtype=torch.long)
            result=reader.model.model(input_ids=token,use_cache=False,return_dict=True).last_hidden_state
            states.append(result[0,-len(target):].numpy().copy())
    vectors=np.concatenate(states)
    output=[]
    for word in words:
        chosen=[i for i,(a,b) in enumerate(offsets) if b>word['start'] and a<word['end']]
        if not chosen:
            raise ValueError('An eligible word has no token-aligned hidden state')
        output.append(vectors[chosen].mean(axis=0))
    return np.asarray(output)


def run(primary,source,model,output,check):
    primary,source,output=Path(primary),Path(source),Path(output)
    previous=completed(primary,'TP18')
    if previous['rows'][0]['clearsBar']:
        raise ValueError('Conditional probe is not eligible after a passed primary')
    path=source/'attention/window/tables.json'
    if sha256(path)!=previous['sources']['tablesPin']:
        raise ValueError('Probe source differs from primary')
    tables=json.loads(path.read_text(encoding='utf8'))
    selected=sorted(tables,key=lambda s:hashlib.sha256(s['session'].encode()).hexdigest())[:len(tables)//3]
    save_json(output/'selected-sessions.json',[s['session'] for s in selected])
    rows,base=word_forecast(selected)
    reader=LocalReader(model,threads=2,precision='float32')
    if reader.identity['id']!='HuggingFaceTB/SmolLM2-360M':
        raise ValueError('The one declared probe uses SmolLM2-360M only')
    report={'card':'TP18-probe','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'One research row on a fixed third of CoAuthor sessions; no default or original gate change',
        'sourceReceiptPin':sha256(primary/'receipt.json'),'tablesPin':sha256(path),'reader':reader.identity,
        'protocol':{'selection':'Lowest SHA-256(session ID), floor(N/3), before outcomes',
            'states':'Mean final hidden state over tokens intersecting each word; causal context <=2048, target chunks512',
            'probe':'PCA64 fitted separately on training-fold words only; five original baseline covariates plus 64 components',
            'folds':'Original five writer folds, same eligible words within the selected third',
            'bar':'Lower paired whole-writer 95% AUC gain >.02; result applies to this fixed subset only'},
        'sessions':len(selected),'words':len(rows),'pack':'No serving or maker admission'}
    save_json(output/'receipt.json',report)
    matrices=[]
    for i,session in enumerate(selected):
        check()
        eligible=[w for s,w in rows if s['session']==session['session']]
        if eligible:
            vector=hidden_words(reader,session['text'],eligible,check)
            np.save(output/f'hidden-{i}.npy',vector)
            matrices.append(vector)
        save_json(output/'progress.json',{'sessions':i+1,'total':len(selected)})
    del reader
    x=np.concatenate(matrices)
    y=np.array([w['stop'] for _,w in rows],int)
    folds=np.array([s['fold'] for s,_ in rows]);forecasts=np.zeros(len(rows))
    for fold in range(5):
        check()
        training=folds!=fold
        pca=PCA(n_components=64,svd_solver='randomized',random_state=23).fit(x[training])
        components=pca.transform(x)
        frequency=Counter(m.group().casefold() for s in selected if s['fold']!=fold for m in WORD.finditer(s['text']))
        baseline=np.array([[len(w['text']),math.log1p(frequency[w['text'].casefold()]),w['position'],w['sentenceStart'],w['paragraphStart']] for _,w in rows])
        design=np.c_[baseline,components]
        model=fit_logistic(design[training],y[training])
        forecasts[~training]=predict(model,design[~training])[:,1]
        np.savez(output/f'fold-{fold}.npz',pca=pca.components_,pca_mean=pca.mean_,**model)
    result=paired_auc(y,base,forecasts,[s['writer'] for s,_ in rows])
    result['clearsBar']=result['interval'][0]>.02
    np.savez(output/'forecasts.npz',baseline=base,probe=forecasts,labels=y)
    report.update(status='complete',row=result,controls={'constant_auc':.5,'bow':'Original five-feature frequency/length/position baseline',
        'human':'No independent human pause forecast reference'})
    save_json(output/'receipt.json',report)
