"""TP57 comment-date comparison, with equal-sized random partitions as the reference."""
import numpy as np
import pandas as pd
from pathlib import Path
from cb_inputs import digest
from tompathy_engine.eval.readers.affect_data import go_comments
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28, saved
from tompathy_engine.eval.readers.word_panels import pinned
from tompathy_engine.eval.readers.person_halves import summary
from week_need_losses import standard
from week_word_departures import matches, WORDS


def cosine(a,b):
    scale=np.linalg.norm(a)*np.linalg.norm(b)
    return float(a@b/scale) if scale else np.nan


def likeness(x,g,early,late,k):
    a=x[early]; b=x[late]
    raw=cosine(a.mean(0),b.mean(0))
    na=np.bincount(g[early],minlength=k)
    nb=np.bincount(g[late],minlength=k)
    # Only overlapping communities can be transported without extrapolation.
    common=nb[g[early]]>0
    wt=na[g[late]]/nb[g[late]]
    adjusted=cosine(a[common].mean(0),np.average(b,axis=0,weights=wt)) if common.any() else np.nan
    return np.array([raw,adjusted])


def comparison(x,dates,communities,key,check):
    mid=np.median(dates) if len(x) else np.nan
    e=np.flatnonzero(dates<=mid); l=np.flatnonzero(dates>mid)
    row=dict(comments=len(x),early=len(e),late=len(l))
    if min(len(e),len(l))<2:return dict(row,status="insufficient dated comments")
    _,g=np.unique(communities,return_inverse=True); k=max(g)+1
    row["commonEarly"]=int(np.isin(g[e],g[l]).sum())
    row["commonLate"]=int(np.isin(g[l],g[e]).sum())
    rng=np.random.default_rng(int(digest("TP57:23:"+key)[:16],16))
    observed=likeness(x,g,e,l,k)
    refs=[];draws=[]
    for i in range(2000):
        if i%32==0:check()
        order=rng.permutation(len(x))
        refs.append(likeness(x,g,order[:len(e)],order[len(e):],k))
        a=rng.choice(e,len(e)); b=rng.choice(l,len(l))
        pool=rng.permutation(np.r_[a,b])
        draws.append(likeness(x,g,pool[:len(e)],pool[len(e):],k)-likeness(x,g,a,b,k))
    estimate=np.nanmean(refs,axis=0)-observed
    for j,label in enumerate(("raw","communityAdjusted")):
        row[label]=summary(estimate[j],np.asarray(draws)[:,j])
    return row


def prepare(out,check):
    root=Path(".local/readers/data/go-emotions")
    frame,truth,names,identity=go_comments(root)
    keep=frame.source_split.ne("unreleased").to_numpy()
    frame=frame[keep];truth=truth[keep]
    folder=Path(".local/nine-channel/tp28-a")
    rec=pinned(folder/"receipt.json",TP28)
    if rec["sources"]["go"]["identity"]!=identity:raise ValueError("Comment source changed")
    path=saved(folder,"go/scores.npz",rec); verify_order(path,frame.id)
    with np.load(path,allow_pickle=False) as f:
        x=standard(f["scores"].astype(float))
        if not np.array_equal(f["truth"],truth):raise ValueError("Released labels changed")
    meta=pd.concat([pd.read_csv(root/f"goemotions_{i}.csv",usecols=["id","created_utc","subreddit"]) for i in (1,2,3)]).drop_duplicates()
    if meta.id.duplicated().any():raise ValueError("Inconsistent date or community")
    meta=meta.set_index("id").loc[frame.id]
    if meta.isna().any().any():raise ValueError("Missing comment metadata")
    dates=meta.created_utc.to_numpy(); communities=meta.subreddit.to_numpy()
    years=pd.to_datetime(dates,unit="s",utc=True).year
    masks=np.array([matches(t) for t in frame.text])
    result=dict(card="TP57",tagSource=TP28,yearCounts={str(y):int(sum(years==y)) for y in sorted(set(years))},labels={},words={})
    for group,items in [("labels",[(s,truth[:,i]>0) for i,s in enumerate(names)]),("words",[(s,(masks & (1<<i))!=0) for i,s in enumerate(WORDS)])]:
        for name,mask in items:
            check()
            result[group][name]=comparison(x[mask],dates[mask],communities[mask],group+name,check)
    result["mostFrequentThird"]=sorted(names,key=lambda n:(-result["labels"][n]["comments"],n))[:(len(names)+2)//3]
    result["secondaryComparison"]="Pending early blog versus assigned chat profiles."
    return result
