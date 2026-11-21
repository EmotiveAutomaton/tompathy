"""TP44, including the curator's CD definition of the two person-disjoint folds."""
import json
from itertools import combinations

import numpy as np
import pandas as pd

from cb_features import ridge_predict
from cb_inputs import BASE, digest, pin
from cb_tables import FEATURES, TAGS, design, halves, read, scored_batches, style_forms


def writer_readings(tags, x, frame, keys, check):
    source_people = frame.person.nunique()
    complete_rows = (frame.groupby('person').feeling.transform('nunique') == 7).to_numpy()
    frame = frame.loc[complete_rows].reset_index(drop=True)
    tags, x = tags[complete_rows], x[complete_rows]
    people = frame['person'].to_numpy()
    original = ['country','city','feeling']
    counts = frame.groupby(original).person.transform('nunique')
    fallback = counts < 10
    # Country fallback includes everyone in the country for that feeling.
    def departures(mask):
        a = pd.DataFrame(tags[mask])
        g = frame.loc[mask].reset_index(drop=True)
        site_mean = a.groupby([g[k] for k in original]).transform('mean')
        country_mean = a.groupby([g.country,g.feeling]).transform('mean')
        return a.to_numpy()-np.where(fallback.to_numpy()[mask,None],country_mean,site_mean)
    raw = departures(np.ones(len(frame),bool))
    ordered = sorted(set(people),key=lambda p:digest('TP44:fold:'+keys[p]))
    folds = {p:i%2 for i,p in enumerate(ordered)}
    side = np.array([folds[p] for p in people])
    residual = np.empty_like(raw)
    for held in (0,1):
        train = side != held
        residual[~train] = raw[~train]-ridge_predict(x[train],departures(train),x[~train])
    lookup = {(p,f):i for i,(p,f) in enumerate(zip(people,frame.feeling,strict=True))}
    emotions = sorted(set(frame.feeling))
    complete = [p for p in ordered if all((p,f) in lookup for f in emotions)]
    if len(emotions)!=7 or len(complete)!=1091 or source_people!=1096:
        raise ValueError('TP44 person/feeling intake changed')
    ix = np.array([[lookup[p,f] for f in emotions] for p in complete])
    result = dict(completePeople=len(complete),incompletePeople=source_people-len(complete),
                  fallbackCells=len(frame.loc[fallback,original].drop_duplicates()),fallbackReports=int(fallback.sum()),
                  countryCityFeelingCells=len(frame[original].drop_duplicates()),
                  foldPeople=[sum(v==i for v in folds.values()) for i in (0,1)])
    weights = np.vstack([np.ones(len(ix)),halves.resamples(len(ix))])
    for label,values in [('uncleared',raw),('styleCleared',residual)]:
        sums = np.zeros((len(weights),len(TAGS)))
        for left in combinations(range(7),4):
            check()
            right = sorted(set(range(7))-set(left))
            a = values[ix[:,left]].mean(axis=1)
            b = values[ix[:,right]].mean(axis=1)
            for start in range(0,len(weights),100):
                w = weights[start:start+100]
                sums[start:start+len(w)] += halves.correlations(a,b,w)
        by_tag = sums/35
        mean = np.nanmean(by_tag,axis=1)
        result[label] = dict(mean=halves.summary(mean[0],mean[1:]),
                            tags={name:halves.summary(by_tag[0,i],by_tag[1:,i]) for i,name in enumerate(TAGS)})
    return result


def statistic(x,y,people,weights):
    ok = np.isfinite(x)&np.isfinite(y)
    x,y,p = x[ok],y[ok],people[ok]
    if not len(x):
        return dict(reports=0, people=0, value=None,interval=[None,None])
    terms = [np.ones(len(x)),x,y,x*x,y*y,x*y]
    sums = weights@np.stack([np.bincount(p,weights=z,minlength=weights.shape[1]) for z in terms]).T
    n,sx,sy,sxx,syy,sxy=sums.T
    with np.errstate(divide='ignore',invalid='ignore'):
        denominator=np.sqrt(np.maximum(sxx-sx*sx/n,0)*np.maximum(syy-sy*sy/n,0))
        r=(sxy-sx*sy/n)/denominator
    # Recompute average ranks in every whole-person bootstrap, including ties.
    _,xi=np.unique(x,return_inverse=True)
    _,yi=np.unique(y,return_inverse=True)
    nx,ny=xi.max()+1,yi.max()+1
    cells=np.bincount((p*nx+xi)*ny+yi,minlength=weights.shape[1]*nx*ny).reshape(weights.shape[1],-1)
    table=(weights@cells).reshape(-1,nx,ny)
    def midrank(margin):
        return margin.cumsum(axis=1)-margin/2-margin.sum(axis=1,keepdims=True)/2
    ax,ay=table.sum(axis=2),table.sum(axis=1)
    rx,ry=midrank(ax),midrank(ay)
    den=np.sqrt((ax*rx**2).sum(axis=1)*(ay*ry**2).sum(axis=1))
    rho=np.divide((table*rx[:,:,None]*ry[:,None,:]).sum(axis=(1,2)),den,out=np.full(len(den),np.nan),where=den>0)
    return dict(reports=len(x), people=len(set(p)), pearson=halves.summary(r[0],r[1:]),
                **halves.summary(rho[0],rho[1:]))


def report(q, frame, check):
    _, person = np.unique(frame.person,return_inverse=True)
    weights = np.vstack([np.ones(person.max()+1),halves.resamples(int(person.max()+1))])
    pleasant = frame.pleasant.to_numpy(float)
    expected = frame.expected.to_numpy(float)
    # Original PLEA 1 = pleasant, 3 = unpleasant. EXPC 1 = unexpected, 3 = expected.
    pleasant = np.where(np.isin(pleasant,[1,2,3]),4-pleasant,np.nan)
    sudden = np.where(np.isin(expected,[1,2,3]),4-expected,np.nan)
    result = {}
    for f in ['all',*sorted(set(frame.feeling))]:
        check()
        mask = np.ones(len(q),bool) if f=='all' else (frame.feeling==f).to_numpy()
        row={'pleasantness':statistic(q[mask,0],pleasant[mask],person[mask],weights),
             'suddennessVsReversedExpectedness':statistic(q[mask,7],sudden[mask],person[mask],weights)}
        causes={}
        for code,label in [('1','self'),('2','close person'),('3','other person'),('4','impersonal agency')]:
            cell=mask & (frame.cause==code).to_numpy()
            means={}
            for j in (2,5):
                valid=cell & np.isfinite(q[:,j])
                n=np.bincount(person[valid],minlength=weights.shape[1])
                totals=np.bincount(person[valid],weights=q[valid,j],minlength=weights.shape[1])
                den=weights@n
                values=np.divide(weights@totals,den,out=np.full(len(den),np.nan),where=den>0)
                means[FEATURES[j]]=dict(reports=int(valid.sum()),people=int((n>0).sum()),
                                        **halves.summary(values[0],values[1:]))
            causes[label]=means
        result[f]=dict(**row,responsibilityMeans=causes)
    return result


def tables(check):
    manifest=read(BASE/'inputs.json')['isear']
    for key,name in [('reports','isear.json'),('metadata','isear-meta.json')]:
        if pin(BASE/name)!=manifest[key]:
            raise ValueError('ISEAR input changed')
    scores=read(BASE/'isear.json')
    frame=pd.DataFrame(read(BASE/'isear-meta.json'),columns=['id','person','country','city','feeling','pleasant','expected','intensity','cause'])
    if frame.id.tolist()!=[r['id'] for r in scores]:
        raise ValueError('ISEAR row order changed')
    csv=pd.read_csv(BASE/'isear.csv',dtype=str,keep_default_na=False)
    keys={digest(s):s for s in (json.dumps(list(t)) for t in csv[['COUN','CITY','SUBJ']].drop_duplicates().itertuples(index=False,name=None))}
    if set(frame.person)!=set(keys):
        raise ValueError('Person-key mismatch')
    tags=np.vstack([v[:,:19] for _,v in scored_batches('isear',scores)])
    style=design([r['text'] for r in scores],style_forms(),[])
    second=writer_readings(tags,style,frame,keys,check)
    from pathlib import Path
    audit=read(BASE.parent/'Q18-transfer-a.json')
    folder=Path(audit['mirror'])
    receipt=read(folder/'receipt.json')
    if not (audit['nativeExited'] and audit['priorFlockReleased'] and pin(folder/'receipt.json')==audit['sourceReceiptPin']
            and receipt['job']=='Q18' and receipt['status']=='complete' and receipt['durableRows']==len(scores)
            and receipt['inputPin']==manifest['reports'] and receipt['owner']['commit']==read(BASE/'registration.json')['commit']):
        raise ValueError('Unverified Q18 source')
    q=np.full((len(scores),8),np.nan)
    for i,r in enumerate(scores):
        if i%128==0:check()
        row=read(folder/'B'/f'row-{i:06d}.json')
        if row['index']!=i or row['id']!=r['id'] or row['binding']['inputPin']!=receipt['inputPin']:
            raise ValueError('ISEAR reader alignment differs')
        if row['values'] is not None:q[i]=[row['values'][k] for k in FEATURES]
    baseline=Path('engine/validation/readers-feature-slots-2026-11.json')
    if pin(baseline)!='f95cd29d7a7d9059c22b0e62ff6f57bf88eb73cacb8c2bb56a9e5cfe00eec6db':
        raise ValueError('Filed RD1 comparison changed')
    return dict(sourceReceiptPin=audit['sourceReceiptPin'], table1=report(q,frame,check),table2=second,
                rd1Comparison={k:r['B']['candidateRho'] for k,r in read(baseline)['rows'].items()},
                correlation='Spearman with ties recomputed per person resample. Pearson beside it.')
