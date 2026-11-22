"""TP48. Preserve historical nine-output tables and bootstrap PRIDE checks over writers."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from cb_inputs import pin
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.person_halves import resamples,summary
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp39 import saved
from week_pride_inputs import FROZEN,SOURCE


def checks(ten,words,writers,check):
    words=np.asarray(words)
    names,labels=np.unique(words,return_inverse=True)
    people,ix=np.unique(writers,return_inverse=True)
    weights=np.vstack([np.ones(len(people)),resamples(len(people))])
    active=ten.std(0)>0
    if not active[-1]:
        raise ValueError('PRIDE predictions have zero spread')
    peaks=((ten[:,active]-ten[:,active].mean(0))/ten[:,active].std(0)).max(1)
    counts=np.zeros((len(people),len(names)))
    quiet=np.zeros_like(counts)
    np.add.at(counts,(ix,labels),1); np.add.at(quiet,(ix,labels),peaks<=1)
    with np.errstate(invalid='ignore',divide='ignore'):
        rates=(weights@quiet)/(weights@counts)
    differences=rates[:,names.tolist().index('proud')]-np.median(rates,axis=1)
    out={'quietShares':{str(k):dict(reports=int(n),**summary(v[0],v[1:])) for k,n,v in
                        zip(names,counts.sum(0),rates.T,strict=True)},
         'proudMinusMedian':summary(differences[0],differences[1:])}
    for other in ('joyful','excited'):
        take=np.isin(words,['proud',other])
        truth=words[take]=='proud'
        scores=ten[take,-1]
        owner=ix[take]
        values=[]
        for i,w in enumerate(weights):
            if i%100==0:
                check()
            sw=w[owner]
            values.append(roc_auc_score(truth,scores,sample_weight=sw) if
                          min(sw[truth].sum(),sw[~truth].sum()) else np.nan)
        out['proudVs'+other.capitalize()]=summary(values[0],np.asarray(values[1:]))
    return out


def prepare(out,check):
    week=Path('.local/week-20261122')
    read=lambda p:json.loads(p.read_bytes())
    audit=read(week/'Q21-transfer.json')
    src=Path(audit['mirror'])
    old=read(FROZEN/'receipt.json')
    if (not audit['nativeExited'] or not audit['priorFlockReleased'] or pin(FROZEN/'receipt.json')!=SOURCE
        or pin(src/'receipt.json')!=audit['sourceReceiptPin']):
        raise ValueError('Unverified Spark output or original reference')
    ed,identity=ed_situations('.local/readers/data/empathetic-dialogues')
    if identity!=old['sources']['ed']:
        raise ValueError('Original chat roster differs')
    result={}
    for source in ('ed','go','envent'):
        check()
        fname=source+'-ten.npz'
        if pin(src/fname)!=audit['files'][fname]:
            raise ValueError('Changed ten-output batch')
        with np.load(src/fname) as a,np.load(saved(FROZEN,source+'-profile-forecasts.npz',old)) as ref:
            ten=a['ten']
            if ten.shape!=(len(ref['ids']),10) or not np.isfinite(ten).all() or not np.array_equal(ten[:,:9],ref['probabilities']):
                raise ValueError('Nine original columns differ')
            if source=='ed':
                if not np.array_equal(ed.id,ref['ids']):
                    raise ValueError('Chat IDs differ')
                result['checks']=checks(ten,ed.label,ed.writer,check)
                shame=ed.label.eq('ashamed');proud=ed.label.eq('proud')
            elif source=='envent':
                f=Path('.local/readers/data/crowd-enVent2023/corpus/crowd-enVent_generation.tsv')
                if pin(f)!=old['sources']['envent']['files']['generation']:
                    raise ValueError('Changed event source')
                data=pd.read_csv(f,sep='\t',quoting=3,usecols=['text_id','emotion'],dtype=str).set_index('text_id')
                labels=data.loc[ref['ids'],'emotion']
                shame=labels.eq('shame');proud=labels.eq('pride')
            else:
                # Comments have a pride label but no literal shame label.
                data=pd.concat([pd.read_csv(Path('.local/readers/data/go-emotions')/f'goemotions_{i}.csv',
                                    usecols=['id','pride'],dtype={'id':str}) for i in (1,2,3)])
                proud=data.groupby('id').pride.mean().loc[ref['ids']].gt(0)
                shame=np.zeros(len(ten),bool)
        matrix=pd.DataFrame(ten).corr().to_numpy()
        sj=CHANNELS.index('SHAME')
        result[source]=dict(rows=len(ten),nineExact=True,
             correlations=[[float(v) if np.isfinite(v) else None for v in row] for row in matrix],
             proudTexts=int(proud.sum()),shameTexts=int(shame.sum()),prideMean=float(ten[:,-1].mean()),
             shameMean=float(ten[:,sj].mean()),shameOnPride=float(ten[proud,sj].mean()) if np.any(proud) else None,
             prideOnShame=float(ten[shame,-1].mean()) if np.any(shame) else None)
    result.update(card='TP48',source=audit['sourceReceiptPin'],columns=[*CHANNELS,'PRIDE'],
                  prefitCounts=read(week/'Q21-inputs-a/receipt.json')['counts'])
    return result
