"""TP45 opening profiles from a verified Q20 export, with streamed outside-author fitting."""
import gzip
import itertools
import json
import zipfile
from contextlib import ExitStack
from collections import Counter
from pathlib import Path

import numpy as np

from cb_inputs import BLOG,digest,pin
from cb_tables import design,style_forms
from tompathy_engine.eval.readers import person_halves as halves
from tompathy_engine.eval.readers import week_curve as curve
from tompathy_engine.packs.trigger import TAGS

WEEK=Path('.local/week-20261122')


def rows(path):
    with gzip.open(path,'rt',encoding='utf8') as f:
        for ln in f:
            yield json.loads(ln)


def prepare(out,check,whole=False):
    audit=json.loads((WEEK/'Q20-transfer.json').read_bytes())
    root=Path(audit['mirror'])
    src=WEEK/'Q20-inputs-a'
    if whole and pin(src/'receipt.json')!='84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54':
        raise ValueError('Q20 roster receipt differs')
    cfg=json.loads((src/'receipt.json').read_bytes())
    join=src/'local-joins.jsonl.gz'
    if (not audit['nativeExited'] or not audit['priorFlockReleased'] or
            pin(root/'receipt.json')!=audit['sourceReceiptPin'] or pin(join)!=cfg['joinsPin']):
        raise ValueError('Verified Q20 transfer and original joins required')
    check()
    index={}
    references=Counter()
    dated=Counter()
    for r in rows(join):
        key=r['opening']
        if r['qualifies']:
            dated[r['author']]+=1
        keys=r['windows'] if whole and r['qualifies'] else [key]
        for window in keys:
            if window is not None:
                index.setdefault(window,len(index))
        if key is not None and not r['qualifies']:
            references[key]+=1
    count=len(index)
    def matrix(name,cols):
        return np.lib.format.open_memmap(out/(name+'.npy'),mode='w+',dtype='float64',shape=(count,cols))
    x,y=matrix('style-topic',358),matrix('tags-placebo',38)
    files=sorted(root.glob('scores-*.npz'))
    seen=np.zeros(count,bool)
    for file in files:
        check()
        if pin(file)!=audit['files'][file.name]:
            raise ValueError('Q20 forecast batch changed')
        with np.load(file,allow_pickle=False) as d:
            ids=d['ids'].tolist()
            take=[j for j,k in enumerate(ids) if k in index]
            dest=[index[ids[j]] for j in take]
            if len(set(dest))!=len(dest) or seen[dest].any():
                raise ValueError('Duplicate score')
            seen[dest]=True
            y[dest]=np.column_stack((d['tags'][take],d['placebo'][take]))
    if not seen.all():
        raise ValueError('Missing opening predictions')
    forms=style_forms()
    tokens=Counter()
    paths=sorted((src/'spark-inputs').glob('*.gz'))
    for path in paths:
        check()
        if pin(path)!=cfg['shards'][path.name]:
            raise ValueError('Text shard changed')
        for key,text in rows(path):
            if key in references:
                for w,n in Counter(halves.FORMS.findall(text.casefold())).items():
                    tokens[w]+=n*references[key]
    topics=sorted(tokens.keys()-set(forms),key=lambda w:(-tokens[w],w))[:300]
    seen[:]=False
    for path in paths:
        check()
        for batch in itertools.batched(((k,t) for k,t in rows(path) if k in index),256):
            ix=[index[k] for k,t in batch]
            x[ix]=design([t for k,t in batch],forms,topics)
            seen[ix]=True
    if not seen.all() or len(topics)!=300:
        raise ValueError('Incomplete design')
    if whole:
        # Outside authors have only registered reference openings. In the study
        # each dated post contributes once, regardless of its number of windows.
        post_index={}
        # Keep the input and output mappings out of memory at the same time.
        # At most 512 posts x 20 windows are gathered in a batch. Even mapped
        # in full, the Q20 window arrays here occupy less than 3 GiB.
        post_files=[out/'post-style.f64',out/'post-readings.f64']
        with ExitStack() as stack:
            streams=[stack.enter_context(path.open('xb')) for path in post_files]
            for batch in itertools.batched(rows(join),512):
                check()
                indices=[]; lengths=[]
                for r in batch:
                    keys=r['windows'] if r['qualifies'] else [r['opening']]
                    if not keys:
                        continue
                    if r['id'] in post_index or len(keys)>20 or None in keys:
                        raise ValueError('Invalid post/window binding')
                    post_index[r['id']]=len(post_index)
                    lengths.append(len(keys))
                    indices.extend(index[key] for key in keys)
                if indices:
                    starts=np.cumsum([0,*lengths[:-1]])
                    for stream,data in zip(streams,(x,y),strict=True):
                        means=np.add.reduceat(data[indices],starts,axis=0)/np.asarray(lengths)[:,None]
                        stream.write(means.tobytes())
        del x,y,data,index
        x,y=(np.memmap(path,dtype='float64',mode='r',shape=(len(post_index),width))
             for path,width in zip(post_files,(358,38),strict=True))
    def authors():
        for key,grp in itertools.groupby(rows(join),key=lambda r:r['author']):
            allrows=list(grp)
            valid=([r for r in allrows if r['id'] in post_index] if whole else
                   [r for r in allrows if r['opening'] is not None])
            if valid:
                indices=([post_index[r['id']] for r in valid] if whole else
                         [index[r['opening']] for r in valid])
                yield key,allrows,valid,np.array(indices)
    total=np.zeros(396); n=0; study_n=0; sums=np.zeros(19); squares=np.zeros(19)
    for key,allrows,group,ix in authors():
        check()
        total+=np.r_[x[ix].sum(0),y[ix].sum(0)]
        n+=len(ix)
        if group[0]['qualifies']:
            placebo=y[ix,19:]
            sums+=placebo.sum(0);squares+=(placebo**2).sum(0);study_n+=len(ix)
    mean=sums/study_n
    scale=np.sqrt(squares/study_n-mean**2)
    if not np.all(scale>0):
        raise ValueError('Unusable placebo scale')
    def departures(ix):
        a,b=x[ix],y[ix]
        a-=(total[:358]-a.sum(0))/(n-len(ix))
        b-=(total[358:]-b.sum(0))/(n-len(ix))
        b[:,19:]/=scale
        return a,b
    xx=np.zeros((358,358));xy=np.zeros((358,38))
    sx=np.zeros(358);sy=np.zeros(38);nr=0
    for key,allrows,group,ix in authors():
        if group[0]['qualifies']:
            continue
        check()
        a,b=departures(ix)
        xx+=a.T@a;xy+=a.T@b;sx+=a.sum(0);sy+=b.sum(0);nr+=len(ix)
    gram=xx-np.outer(sx,sx)/nr
    sd=np.sqrt(np.maximum(gram.diagonal()/nr,0));sd[sd==0]=1
    coef=np.linalg.solve(gram/np.outer(sd,sd)+np.eye(358),(xy-np.outer(sx,sy)/nr)/sd[:,None])
    deep_min=80 if cfg['counts']['authorsAt80']>=600 else 40
    if pin(BLOG)!=cfg['source']:
        raise ValueError('Source roster changed')
    fold_keys={}
    with zipfile.ZipFile(BLOG) as z:
        for name in z.namelist():
            if name.lower().endswith('.xml'):
                ident=Path(name).name.partition('.')[0]
                fold_keys[digest('TP43:23:'+ident)]=digest('TP39:fold:'+ident)
    folds={}
    for pop,minimum in [('deep',deep_min),('all',20)]:
        roster=sorted((author for author,npost in dated.items() if npost>=minimum),key=fold_keys.__getitem__)
        folds[pop]={a:i%2 for i,a in enumerate(roster)}
    containers={}
    for key,allrows,group,ix in authors():
        if not group[0]['qualifies']:
            continue
        check()
        a,b=departures(ix)
        cleared=b-((a-sx/nr)/sd@coef+sy/nr)
        values=np.column_stack((a,b,cleared))
        for gap in (False,True):
            order=curve.nested_indices([r['day'] for r in group],[r['id'] for r in group],gap)
            if not whole and not gap and all(len(side)>0 for side in order):
                containers.setdefault(('every','date','full'),[]).append(
                    (key,*(values[side].mean(0) for side in order)))
            for k in ((20,) if whole else (5,10,20,40)):
                if min(map(len,order))<k:
                    continue
                for population,keep in [('deep',len(allrows)>=deep_min and (deep_min==80 or k<=20)),
                                        ('all',not whole and k==10)]:
                    if keep:
                        slot=(population,'gap' if gap else 'date',k)
                        containers.setdefault(slot,[]).append((key,*(values[o[:k]].mean(0) for o in order)))
    for (pop,split,k),data in containers.items():
        # TP39 fold order depends on the original author key. The blog join contains its
        # TP43 hash, so recover the TP39 sort key from the original archive identifier.
        data.sort(key=lambda r:fold_keys[r[0]])
        owners,left,right=zip(*data)
        np.savez_compressed(out/f'{pop}-{split}-{k}.npz',owners=owners,left=left,right=right,
                            fold=[folds['all' if pop=='every' else pop][a] for a in owners])
    if whole:
        return whole_tables(out,check,audit['sourceReceiptPin'],nr,study_n,deep_min)
    return dict(transferPin=audit['sourceReceiptPin'],outsideOpenings=nr,columns=358,
                lastStyleReading='capitalizedShare',forms=forms,topics=topics,tags=list(TAGS),
                deepMinimum=deep_min,qualifyingOpenings=study_n)


def whole_tables(out,check,source,outside,study_posts,minimum):
    """TP45 Table 5, using fixed forecasts and the original held-out candidate folds."""
    results={}
    for split in ('date','gap'):
        path=out/f'deep-{split}-20.npz'
        with np.load(path,allow_pickle=False) as d:
            left,right,fold=(d[name] for name in ('left','right','fold'))
        n=len(left)
        w=halves.resamples(n)
        arms={}
        for arm,start in [('tagsRaw',358),('placeboRaw',377),('tagsPartial',396),('placeboPartial',415)]:
            check()
            columns=slice(start,start+19)
            c=np.vstack([halves.correlations(left[:,columns],right[:,columns],batch)
                         for batch in np.array_split(np.vstack((np.ones(n),w)),40)])
            ranks=curve.rank_arms(left,right,[slice(0,358),columns],fold,check)
            cell={'correlations':{t:halves.summary(v[0],v[1:]) for t,v in zip(TAGS,c.T,strict=True)},
                  'meanCorrelation':halves.summary(c[0].mean(),c[1:].mean(1))}
            for label,cut in [('firstTen',10),('firstOne',1)]:
                base,plus=((r<=cut).astype(float) for r in ranks)
                cell[label]={k:halves.summary(values.mean(),w@values/n)
                             for k,values in [('baseline',base),('plus',plus),('step',plus-base)]}
            endpoint=next((k for k in ('firstTen','firstOne') if cell[k]['baseline']['value']<.90),None)
            cell['endpoint']=endpoint
            cell['stepVerdict']=('blind' if endpoint is None else
                                 'pass' if cell[endpoint]['step']['interval'][0]>0 else 'miss')
            arms[arm]=cell
        results[split]=dict(authors=n,profilePin=pin(path),arms=arms)
    return dict(card='TP45-whole',transferPin=source,deepMinimum=minimum,posts=study_posts,
                outsideOpenings=outside,k=20,windowCap=20,draws=2000,tables=results)


def opening_tables(out,check):
    source=WEEK/'TP45-profiles-a'
    record=json.loads((source/'receipt.json').read_bytes())
    h=pin(source/'receipt.json')
    if json.loads((source/'complete.json').read_bytes())['sourceReceiptPin']!=h:
        raise ValueError('Profiles incomplete')
    outputs={}
    raw_ranks={}
    corr_draws={}
    for name,file_pin in record['profileFiles'].items():
        if name=='every-date-full.npz':
            continue  # TP46 uses every opening, outside the fixed-k TP45 tables.
        path=source/name
        if pin(path)!=file_pin:
            raise ValueError('Profile cache differs')
        pop,split,k=path.stem.split('-')
        k=int(k)
        with np.load(path) as f:
            a,b,fold,owners=[f[p] for p in ('left','right','fold','owners')]
        w=halves.resamples(len(a))
        weights=np.vstack((np.ones(len(a)),w))
        outputs[path.stem]={}
        for arm,lo in [('tagsRaw',358),('placeboRaw',377),('tagsPartial',396),('placeboPartial',415)]:
            block=slice(lo,lo+19)
            c=np.concatenate([halves.correlations(a[:,block],b[:,block],v) for v in np.array_split(weights,40)])
            corr_draws[pop,split,k,arm]=c
            rs=curve.rank_arms(a,b,[slice(0,358),block],fold,check)
            raw_ranks[pop,split,k,arm]=owners,rs
            cell={'authors':len(a),'correlations':[halves.summary(v[0],v[1:]) for v in c.T]}
            means=c.mean(1)
            cell['meanCorrelation']=halves.summary(means[0],means[1:])
            for title,cut in [('firstOne',1),('firstTen',10)]:
                pts=[(r<=cut).astype(float) for r in rs]
                cell[title]={lbl:halves.summary(hit.mean(),w@hit/len(a)) for lbl,hit in
                             [('baseline',pts[0]),('plus',pts[1]),('step',pts[1]-pts[0])]}
            outputs[path.stem][arm]=cell
    growth={}
    curve_checks={}
    for split in ('date','gap'):
        for arm in ('tagsRaw','placeboRaw','tagsPartial','placeboPartial'):
            ks=sorted(k for pop,s,k,t in raw_ranks if pop=='deep' and s==split and t==arm)
            if 5 not in ks:
                continue
            base=corr_draws['deep',split,5,arm][0]
            for k in ks:
                predicted=curve.fixed_profile(base,k)
                cell=outputs[f'deep-{split}-{k}'][arm]
                cell['fixedProfileFrom5']=[float(v) if np.isfinite(v) else None for v in predicted]
                if k==5:
                    cell['postsPerHalf']={str(target):[
                        int(v) if np.isfinite(v) else None for v in curve.posts_needed(base,target)]
                        for target in (.5,.8)}
            # Compare observed and predicted means on the same authors in every draw.
            with np.load(source/f'deep-{split}-5.npz') as low,np.load(source/f'deep-{split}-{max(ks)}.npz') as high:
                common=set(low['owners'])&set(high['owners'])
                weights=halves.resamples(len(common))
                weights=np.vstack((np.ones(len(common)),weights))
                series=[]
                lo={'tagsRaw':358,'placeboRaw':377,'tagsPartial':396,'placeboPartial':415}[arm]
                for frame in (low,high):
                    selected=np.isin(frame['owners'],list(common))
                    left=frame['left'][selected,lo:lo+19];right=frame['right'][selected,lo:lo+19]
                    series.append(np.concatenate([halves.correlations(left,right,w)
                                                  for w in np.array_split(weights,40)]))
                delta=(series[1]-curve.fixed_profile(series[0],max(ks))).mean(1)
                curve_checks[split+'/'+arm]=dict(k=max(ks),pairedAuthors=len(common),
                             observedMinusProjected=halves.summary(delta[0],delta[1:]))
            baseline={k:{m:outputs[f'deep-{split}-{k}'][arm][m]['baseline']['value']
                         for m in ('firstTen','firstOne')} for k in ks}
            endpoint,kmax=curve.choose_endpoint(baseline,ks)
            label=split+'/'+arm
            if endpoint is None:
                growth[label]=dict(status='blind',baseline=baseline)
                continue
            # Recompute both ranks on identical authors and candidate pools for the paired change.
            with np.load(source/f'deep-{split}-5.npz') as low,np.load(source/f'deep-{split}-{kmax}.npz') as high:
                common=set(low['owners'])&set(high['owners'])
                step=[]
                lo={'tagsRaw':358,'placeboRaw':377,'tagsPartial':396,'placeboPartial':415}[arm]
                for frame in (low,high):
                    mask=np.array([key in common for key in frame['owners']])
                    ranks=curve.rank_arms(frame['left'][mask],frame['right'][mask],
                                          [slice(0,358),slice(lo,lo+19)],frame['fold'][mask],check)
                    cut=10 if endpoint=='firstTen' else 1
                    step.append((ranks[1]<=cut).astype(float)-(ranks[0]<=cut).astype(float))
            diff=step[1]-step[0]
            result=halves.summary(diff.mean(),halves.resamples(len(diff))@diff/len(diff))
            growth[label]=dict(endpoint=endpoint,k=kmax,pairedAuthors=len(diff),result=result)
    return dict(source=h,tables=outputs,growth=growth,curveChecks=curve_checks,
                scope='Opening tables. Whole-post matching and descriptive covariance corrections have separate readouts.')


def descriptions(out,check):
    source=WEEK/'TP45-profiles-a'
    r=json.loads((source/'receipt.json').read_bytes())
    path=source/'deep-date-20.npz'
    if (pin(source/'receipt.json')!=json.loads((source/'complete.json').read_bytes())['sourceReceiptPin']
        or pin(path)!=r['profileFiles'][path.name]):
        raise ValueError('Missing source-bound k=20 profiles')
    with np.load(path) as d:
        a,b,fold=d['left'],d['right'],d['fold']
    return dict(k=20,source=pin(source/'receipt.json'),style=r['forms'],topics=r['topics'],
                outputs=r['tags'],lastStyleReading='capitalizedShare',simulationColumns=357,
                realColumns=358,bar=None,corrections={name:curve.table_six(
                    (a[:,:358],b[:,:358]),(a[:,s],b[:,s]),fold,check)
                    for name,s in [('tags',slice(358,377)),('placebo',slice(377,396))]})
