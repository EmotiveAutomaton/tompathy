"""Cross-half covariance of within-writer, between-word-kind contrasts."""
import json
from pathlib import Path

import numpy as np

from ...packs.trigger import FEATURES, TAGS
from . import person_halves as halves
from . import tp39
from .affect_data import ed_situations
from .tp34 import NAMES, PLEASANT, UNPLEASANT
from .tp36 import verify_order

PLUS=set('excited proud grateful impressed hopeful confident joyful prepared content caring trusting faithful'.split())
MINUS=set('angry sad annoyed lonely afraid terrified guilty disgusted furious anxious disappointed jealous devastated embarrassed ashamed apprehensive'.split())
MIXED=set('surprised anticipating nostalgic sentimental'.split())


def adjusted(weights, a, b, x, y):
    """Inputs are two half contrasts followed by their two half levels."""
    p=weights/weights.sum(axis=1,keepdims=True)
    def cov(u,v):
        return p@(u*v)-(p@u)*(p@v)
    level=cov(x,y)
    cross=(cov(a,y)+cov(b,x))/2
    raw=cov(a,b)
    return raw-np.divide(cross**2,level,out=np.zeros_like(raw),where=level>1e-6),level


def run(out,check):
    base=Path('.local')
    df,src=ed_situations(base/'readers/data/empathetic-dialogues')
    ids,words,writers=(df[k].to_numpy(str) for k in ('id','label','writer'))
    labels,owner,half=halves.split(writers,ids)
    plus=(PLUS-set(UNPLEASANT))|set(PLEASANT)
    minus=(MINUS-set(PLEASANT))|set(UNPLEASANT)
    if set(words)-(plus|minus|MIXED) or plus & minus:raise ValueError('Unassigned word side')
    signs=[np.isin(words,list(side)) for side in (plus,minus)]
    counts=np.stack([np.bincount(owner[(half==h)&side],minlength=len(labels)) for h in (0,1) for side in signs])
    minimum=counts.min(axis=0)
    keep=minimum>=2
    w=minimum[keep]
    support={'writers':int(keep.sum()),'textsInFourCells':int(counts[:,keep].sum()),'minimumCellHistogram':
             {str(int(v)):int((w==v).sum()) for v in np.unique(w)},'originalEligible':len(labels),
             'missingListedWords':sorted((plus|minus|MIXED)-set(words)),'mixedExcluded':sorted(MIXED)}
    (out/'support-before-outcomes.json').write_text(json.dumps(support,sort_keys=True),encoding='utf8')
    check()
    cf=base/'nine-channel/tp30-frozen-a';tf=base/'nine-channel/tp28-a'
    cr=tp39.pinned(cf/'receipt.json',tp39.FROZEN);tr=tp39.pinned(tf/'receipt.json',tp39.TP28)
    if cr['sources']['ed']!=src or tr['sources']['ed']['identity']!=src or tr['protocol']['tags']!=list(TAGS):
        raise ValueError('TP39 source mismatch')
    with np.load(tp39.saved(cf,'ed-profile-forecasts.npz',cr),allow_pickle=False) as f:
        if not np.array_equal(ids,f['ids']):raise ValueError('Channels misaligned')
        channels=f['probabilities']
    path=tp39.saved(tf,'ed/scores.npz',tr);verify_order(path,ids)
    with np.load(path,allow_pickle=False) as f:tags=f['scores']
    features,q6=tp39.q6_features(df,base/'word-table',check)
    weights=np.vstack([np.ones(len(w)),halves.resamples(len(w))])*w
    sets={};readings={}
    for block,matrix,names in [('tags',tags,TAGS),('features',features,FEATURES),('channels',channels,NAMES)]:
        if not np.isfinite(matrix).all():raise ValueError('Missing forecast')
        # The original word reference includes all other writers, even below support.
        cells=[]
        for side in signs:
            filtered=np.where(side,half,-1)
            cells.append(halves.half_departures(matrix,words,writers,owner,filtered)[:,keep,:])
        positive,negative=cells
        # One common SD per reading, from equally weighted within-cell writer variances.
        scale=np.sqrt((positive.var(axis=1)+negative.var(axis=1)).mean(axis=0)/2)
        if not (scale>0).all():raise ValueError('Unscalable reading')
        a,b=(negative-positive)/scale
        x,y=(negative+positive)/(2*scale)
        estimates=[];levels=[]
        for batch in np.array_split(weights,25):
            check()
            val,lev=adjusted(batch,a,b,x,y)
            estimates.append(val);levels.append(lev)
        val=np.vstack(estimates);lev=np.vstack(levels)
        def ci(series):return halves.summary(series[0],series[1:])
        for j,name in enumerate(names):
            readings[block+'/'+name]={'adjusted':ci(val[:,j]),'level':ci(lev[:,j])}
        sets[block]={'adjusted':ci(val.mean(axis=1)),'level':ci(lev.mean(axis=1))}
    tags=sets['tags'];lo,hi=tags['adjusted']['interval'];quarter=tags['level']['value']/4
    verdict='Lands' if lo>0 else 'Level only' if hi<quarter and quarter>0 else 'Could not say'
    return {'sources':{'Q6':q6,'channels':tp39.FROZEN,'tags':tp39.TP28,'support':tp39.sha256(out/'support-before-outcomes.json')},
            'estimate':{'support':support,'sets':sets,'readings':readings,'quarterTagLevel':quarter},
            'question':'Does each writer change her need readings differently between kinds of assigned words?',
            'interval':'2,000 whole-writer draws, paired across halves and readings, weighted by smallest cell.',
            'bar':'Mean level-adjusted tag covariance with interval above zero. If missed, compare the upper end to a quarter of tag level covariance.',
            'verdict':verdict,'scope':'Short situations written to assigned words. Both halves may come from one sitting.'}
