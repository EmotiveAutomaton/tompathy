"""Aggregate TP43 and TP44 readouts. All intermediate arrays and report joins stay private."""
import json
import sys
from collections import Counter
from itertools import batched, combinations
from pathlib import Path

import numpy as np
import pandas as pd

from cb_features import crossfit, read, ridge_predict, verified_q19
from cb_inputs import BASE, digest, pin

sys.path.insert(0, str(Path('engine').resolve()))
from tompathy_engine.eval.readers import person_halves as halves
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp41 import adjusted
from tompathy_engine.packs.trigger import FEATURES, TAGS

FROZEN = BASE/'frozen-b'
STYLE = Path('.local/word-table/tp39-a/receipt.json')
STYLE_PIN = '8de7eec0f2b0f947b097c2c114e4d10fa30f92aa283001abd2cc74690e4bad4c'


def style_forms():
    if pin(STYLE) != STYLE_PIN:
        raise ValueError('TP39 style source changed')
    forms = [k.removeprefix('style/form/') for k in read(STYLE)['estimate']['readings'] if k.startswith('style/form/')]
    if len(forms) != 50:
        raise ValueError('Expected fifty original TP39 forms')
    return forms


def design(texts, forms, topics):
    result = []
    for text in texts:
        words = halves.FORMS.findall(text)
        n = max(1,len(words))
        counts = Counter(w.casefold() for w in words)
        result.append([len(words), sum(map(len,words))/n, *[100*counts[k]/n for k in forms],
                       *[100*text.count(k)/n for k in ',.!?'], 100*(text.count("'")+text.count('’'))/n,
                       sum(w[0].isupper() for w in words)/n, *[100*counts[k]/n for k in topics]])
    return np.asarray(result)


def scored_batches(group, roster):
    for i, batch in enumerate(batched(roster, 128)):
        with np.load(FROZEN/group/f'{i*128:07d}.npz',allow_pickle=False) as d:
            y = d['values']
            if (d['ids'].tolist() != [r['id'] for r in batch] or y.shape != (len(batch),28)
                    or not np.isfinite(y).all()):
                raise ValueError('Misaligned frozen scores for '+group)
        yield batch, y


def both_profiles(values, owners, dates, roster, gap):
    frame = pd.DataFrame(values)
    frame['owner'] = owners
    frame['date'] = dates
    left, right = [], []
    for _, group in frame.groupby('owner',sort=False):
        days = sorted(set(group.date))
        n = len(days)//(3 if gap else 2)
        if n:
            left.extend(group.index[group.date.isin(days[:n])])
            right.extend(group.index[group.date.isin(days[-n:] if gap else days[n:])])
    def take(ix):
        return frame.loc[ix].drop(columns='date').groupby('owner').mean().reindex(roster).to_numpy()
    return np.stack([take(left), take(right)])


def depart(values, owner):
    frame = pd.DataFrame(values)
    group = frame.groupby(owner)
    return (frame-(frame.sum()-group.transform('sum'))/(frame.count()-group.transform('count'))).to_numpy()


def matching(profiles, blocks, check):
    # Fixed TP39 hash-order folds; missing half pairs excluded jointly from the compared arms.
    cols = np.concatenate(list(blocks.values()))
    complete = np.isfinite(profiles[:,:,cols]).all(axis=(0,2))
    if complete.sum() < 4:
        return {'status':'insufficient complete pairs','pairs':int(complete.sum())}
    weights = halves.resamples(int(complete.sum()))
    side = np.arange(len(complete))[complete] % 2
    if any(sum(side==i)<2 for i in (0,1)):
        return {'status':'insufficient fold support'}
    a,b = profiles[:,complete]
    def standard(v):
        sd = v.std(axis=0)
        return np.divide(v-v.mean(axis=0),sd,out=np.zeros_like(v),where=sd>0)
    a,b = standard(a),standard(b)
    result = {'pairs':len(side), 'chanceFirstTen':sum(min(10,sum(side==s)) for s in (0,1))/len(side)}
    previous = None
    arm = []
    for name, idx in blocks.items():
        check()
        arm.extend(idx)
        hit = np.zeros(len(side))
        for fold in (0,1):
            held = side==fold
            x,y = a[~held][:,arm],b[~held][:,arm]
            r = np.clip(np.nan_to_num(halves.correlations(x,y,np.ones((1,len(x))))[0]),0,.95)
            u,v = a[held][:,arm],b[held][:,arm]
            q = r*r/(2*(1-r*r))
            scores = (u*(r/(1-r*r)))@v.T - ((u*u)@q)[:,None] - ((v*v)@q)[None,:]
            hit[held] = halves.ranks(scores)<=10
        result[name] = {'firstTen':halves.summary(hit.mean(),weights@hit/len(hit))}
        if previous is not None:
            gain = hit-previous
            result[name]['pairedGain'] = halves.summary(gain.mean(),weights@gain/len(gain))
        previous = hit
    return result


def movement(tags, raw, owners, dates, roster, check):
    score = tags
    all_cells = []
    counts = []
    for sign in (1,-1):
        mask = sign*(raw[:,0]-raw[:,1]) >= 1
        values = np.where(mask[:,None],score,np.nan)
        all_cells.append(both_profiles(values,owners,dates,roster,False))
        # Sum cell counts explicitly on the same original date split.
        f = pd.DataFrame(dict(owner=owners,date=dates,chosen=mask))
        table = {}
        for key,g in f.groupby('owner'):
            ds = sorted(set(g.date))
            mid = len(ds)//2
            table[key] = [g.loc[g.date.isin(part),'chosen'].sum() for part in (ds[:mid],ds[mid:])]
        counts.append(np.array([table[k] for k in roster]))
    minimum = np.min(counts,axis=(0,2))
    keep = minimum>=2
    result = {'readAuthors':len(roster),'twoPerCell':int(keep.sum()),
              'cellMinimumCounts':dict(sorted(Counter(minimum.tolist()).items()))}
    if keep.sum()<2:
        return dict(result,status='insufficient support')
    pos,neg = [x[:,keep,:] for x in all_cells]
    scale = np.sqrt((pos.var(axis=1)+neg.var(axis=1)).mean(axis=0)/2)
    use = scale>0
    if not use.any():
        return dict(result,status='no variable tag')
    a,b = ((neg-pos)[:,:,use]/scale[use])
    x,y = ((neg+pos)[:,:,use]/(2*scale[use]))
    weights = np.vstack([np.ones(keep.sum()),halves.resamples(int(keep.sum()))])*minimum[keep]
    estimates = []
    for batch in np.array_split(weights,25):
        check()
        estimates.extend(adjusted(batch,a,b,x,y)[0].mean(axis=1))
    return dict(result,meanAdjustedCovariance=halves.summary(estimates[0],np.asarray(estimates[1:])))


def blog_tables(with_features, check):
    check()
    q19 = verified_q19() if with_features else None
    if q19 is not None and len(q19[0]) == 0:
        return {'passes': {}, 'readerB': q19[3], 'status': 'no whole author read',
                'featureAdjustment': {'status': 'unavailable: no whole author read'}}
    from cb_frozen import reference
    manifest = read(BASE/'inputs.json')['blogs']
    for field,name in [('posts','blogs.json'),('metadata','blog-meta.json'),('chosen','selected.json')]:
        if pin(BASE/name) != manifest[field]:
            raise ValueError('Changed blog roster')
    selected = read(BASE/'selected.json')
    ref = lambda: reference(set(selected),check)
    forms = style_forms()
    words = Counter()
    for r in ref():
        words.update(w.casefold() for w in halves.FORMS.findall(r['text']))
    topics = sorted(words.keys()-set(forms),key=lambda w:(-words[w],w))[:300]
    # Sufficient statistics reproduce standardized ridge with an unpenalized intercept.
    metadata = read(BASE/'blog-meta.json')
    rows = read(BASE/'blogs.json')
    if [r['id'] for r in rows] != [r[0] for r in metadata]:
        raise ValueError('Post/date alignment differs')
    raw = np.vstack([y for _,y in scored_batches('blogs',rows)])
    x_selected = design([r['text'] for r in rows],forms,topics)
    owners = np.asarray([r[1] for r in metadata])
    combined = np.column_stack([x_selected, raw])
    selected_sums = pd.DataFrame(combined).groupby(owners).sum()
    selected_counts = Counter(owners)
    outside = {}
    n=0
    sx=np.zeros(358); sy=np.zeros(28)
    xx=np.zeros((358,358)); xy=np.zeros((358,28))
    for batch,y in scored_batches('reference',ref()):
        check()
        x = design([r['text'] for r in batch],forms,topics)
        n += len(y); sx += x.sum(axis=0); sy += y.sum(axis=0)
        xx += x.T@x; xy += x.T@y
        group = np.asarray([r['author'] for r in batch])
        v = np.column_stack([x,y])
        for key in set(group):
            take = group == key
            size,total = outside.get(key,(0,np.zeros(386)))
            outside[key] = (size+int(take.sum()),total+v[take].sum(axis=0))
    total = combined.sum(axis=0)+np.r_[sx,sy]
    size = len(combined)+n
    # Subtract every author's own texts from the population reference before regression.
    for key,(count,v) in outside.items():
        dx,dy = np.split((total-v)/(size-count),[358])
        xx += count*np.outer(dx,dx)-np.outer(dx,v[:358])-np.outer(v[:358],dx)
        xy += count*np.outer(dx,dy)-np.outer(dx,v[358:])-np.outer(v[:358],dy)
        sx -= count*dx
        sy -= count*dy
    offsets = {k:(total-v.to_numpy())/(size-selected_counts[k]) for k,v in selected_sums.iterrows()}
    for i,k in enumerate(owners):
        combined[i] -= offsets[k]
    x, raw = np.split(combined,[358],axis=1)
    mean = sx/n
    gram = xx-n*np.outer(mean,mean)
    sd = np.sqrt(np.maximum(gram.diagonal()/n,0))
    sd[sd==0] = 1.
    scaled = gram/np.outer(sd,sd)
    scaled.flat[::359] += 1.
    coef = np.linalg.solve(scaled,(xy-np.outer(mean,sy))/sd[:,None])
    residual = raw-((x-mean)/sd@coef+sy/n)
    dates = np.asarray([r[2] for r in metadata])
    order = [digest('TP43:23:'+a) for a in sorted(selected,key=lambda a:digest('TP39:fold:'+a))]
    result = {'selected':len(order),'selectedWithOpenings':len(set(owners)),
              'referenceTexts':n,'topicWordListPin':digest(json.dumps(topics)), 'passes':{}}
    features = None
    if q19 is not None:
        features, own, order, provenance = q19
        size = len(features)
        if not np.array_equal(own,owners[:size]):
            raise ValueError('Feature prefix differs')
        x,raw,residual,owners,dates = (v[:size] for v in (x,raw,residual,owners,dates))
        result['table3'] = movement(residual[:,:19],features,owners,dates,order,check)
        cleared,cc = crossfit(x_selected[:size],features,owners,order)
        features = depart(features,owners)
        result.update(readerB=provenance, featureAdjustment=cc)
        if cleared is not None:
            result['limit'] = 'The feature fit used about half the read authors. It is noisier than the outside-author tag and channel fits and is not comparable step for step.'
    for variant,y in [('raw',raw),('adjusted',residual)]:
        names = ['tokens','meanWordLength',*forms,'comma','fullStop','exclamation','questionMark','apostrophe','capitalizedShare',*topics,*TAGS,*CHANNELS]
        blocks = {'style':range(58),'topic':range(58,358),'tags':range(358,377),'channels':range(377,386)}
        data = np.column_stack([x,y])
        f = features if variant=='raw' or features is None else cleared
        if f is not None:
            data=np.column_stack([data,f])
            blocks['features']=range(386,394)
            names+=list(FEATURES)
        names=[k+'/'+names[i] for k,v in blocks.items() for i in v]
        weights=halves.resamples(len(order))
        tables={}
        for gap in (False,True):
            profile=both_profiles(data,owners,dates,order,gap)
            valid=halves.correlations(*profile,np.ones((1,len(order))))[0]
            supported={k:v for k,v in blocks.items() if np.isfinite(valid[list(v)]).any()}
            readings,sets=halves.stability(profile,names,supported,weights,check)
            for k in blocks.keys()-supported.keys():
                sets[k]={'value':None,'interval':[None,None],'status':'no supported correlation'}
            tables['gap' if gap else 'dateHalves']={'table1':sets,'readings':readings}
            if not gap:
                tables['table2']=matching(profile,blocks,check)
        result['passes'][variant]=tables
    return result
