"""TP45 statistics. Rows are paired authors, ordered in the original matching folds."""
import hashlib

import numpy as np

from .person_halves import correlations, ranks, resamples, summary


def nested_indices(dates, ids, gap=False):
    """Keep whole dates together; prefixes of each returned array give the smaller k."""
    days=sorted(set(dates))
    mid=len(days)//(3 if gap else 2)
    if not mid:
        return [],[]
    halves=[set(days[:mid]),set(days[-mid:] if gap else days[mid:])]
    keys=[hashlib.sha256(('TP45:post:'+i).encode()).digest() for i in ids]
    return [sorted((i for i,d in enumerate(dates) if d in side),key=keys.__getitem__) for side in halves]


def fixed_profile(r5,k):
    """Spearman–Brown projection from five posts; inverse counts are per half."""
    r=np.asarray(r5,dtype=float)
    with np.errstate(divide='ignore',invalid='ignore'):
        return np.where((r>0)&(r<=1),k*r/(5+(k-5)*r),np.nan)


def posts_needed(r5,target):
    r=np.asarray(r5,dtype=float)
    with np.errstate(divide='ignore',invalid='ignore'):
        return np.where((r>0)&(r<=1),np.maximum(1,np.ceil(5*target*(1-r)/(r*(1-target)))),np.nan)


def choose_endpoint(baseline,k_values):
    for endpoint in ('firstTen','firstOne'):
        visible=[k for k in k_values if baseline[k][endpoint]<.90]
        if 5 in visible and len(visible)>1:
            return endpoint,max(visible)
    return None,None


def rank_arms(left,right,blocks,fold,check):
    """Retain paired ranks for both endpoints and every block, using TP43's scoring."""
    scales=[]
    for x in (left,right):
        sd=x.std(axis=0)
        scales.append(np.divide(x-x.mean(axis=0),sd,out=np.zeros_like(x),where=sd>0))
    a,b=scales
    result=[np.empty(len(fold),dtype=int) for _ in blocks]
    for side in (0,1):
        test=fold==side
        if min(test.sum(),(~test).sum())<2:
            raise ValueError('Two populated author folds required')
        score=np.zeros((test.sum(),test.sum()))
        for columns,out in zip(blocks,result,strict=True):
            check()
            x,y=a[:,columns],b[:,columns]
            r=correlations(x[~test],y[~test],np.ones((1,(~test).sum())))[0]
            r=np.clip(np.nan_to_num(r),0,.95)
            x,y=x[test],y[test]
            q=r*r/(2*(1-r*r))
            score+=(x*(r/(1-r*r)))@y.T-((x*x)@q)[:,None]-((y*y)@q)[None,:]
            out[test]=ranks(score)
    return result


def factor_inverse(s,floor):
    """Replicate the supplied checker's rank rule, twenty eigen steps and Woodbury inverse."""
    symmetric=(s+s.T)/2
    noise=np.linalg.norm((s-s.T)/2,2)
    rank=int((np.linalg.eigvalsh(symmetric)>noise).sum())
    psi=np.maximum(np.diag(symmetric)/2,floor)
    for _ in range(20):
        ev,u=np.linalg.eigh(symmetric-np.diag(psi))
        idx=np.argsort(ev)[::-1][:rank]
        load=u[:,idx]*np.sqrt(np.maximum(0,ev[idx]))
        psi=np.maximum(np.diag(symmetric)-(load*load).sum(1),floor)
    precision=1/psi
    w=load*precision[:,None]
    return np.diag(precision)-w@np.linalg.solve(np.eye(rank)+load.T@w,w.T),rank


def table_six(style,tag,fold,check,draws=2000):
    """Real-data dimensionality includes capitalizedShare. No threshold or verdict."""
    x1,x2=map(np.asarray,style)
    g1,g2=map(np.asarray,tag)
    n=len(x1)
    if (x1.shape!=x2.shape or x1.shape!=(n,358) or g1.shape!=g2.shape or g1.shape!=(n,19)
        or len(fold)!=n or set(fold)!={0,1} or not all(np.isfinite(a).all() for a in (x1,x2,g1,g2))):
        raise ValueError('Expected paired complete 358-reading and 19-output halves')
    sd=np.vstack([x1,x2]).std(0)
    if (sd==0).any():
        return dict(status='undefined standardization',columns=np.flatnonzero(sd==0).tolist())
    x1,x2=x1/sd,x2/sd
    s=(x1-x1.mean(0)).T@(x2-x2.mean(0))/n
    floor=2*np.sqrt(x1.var(0)*x2.var(0)/n)
    d=np.maximum(np.diag(s),floor)
    if (floor<=0).any():
        return dict(status='undefined precision floor',columns=np.flatnonzero(floor<=0).tolist())
    inv,rank=factor_inverse(s,floor)
    ws=np.vstack([np.ones(n),resamples(n,draws)])
    variance=np.empty((len(ws),19))
    removed=np.empty((2,len(ws),19))
    def cross(w,x,y):
        return (w@((x[:,:,None]*y[:,None,:]).reshape(len(x),-1))).reshape(len(w),358,19) - (w@x)[:,:,None]*(w@y)[:,None,:]
    for i in range(0,len(ws),16):
        check()
        w=ws[i:i+16]/n
        variance[i:i+len(w)]=w@(g1*g2)-(w@g1)*(w@g2)
        cs=[]
        for side in (0,1):
            mask=fold==side
            u=w[:,mask]
            with np.errstate(invalid='ignore'):
                u=u/u.sum(1)[:,None]
            cs.append((cross(u,x2[mask],g1[mask])+cross(u,x1[mask],g2[mask]))/2)
        a,b=cs
        if i==0:
            ca,cb=a[0].tolist(),b[0].tolist()
        removed[0,i:i+len(w)]=(a*b/d[None,:,None]).sum(1)
        removed[1,i:i+len(w)]=(np.matmul(a.transpose(0,2,1),inv)*b.transpose(0,2,1)).sum(2)
    lines={}
    for name,amount in zip(('diagonal','factor'),removed,strict=True):
        with np.errstate(divide='ignore',invalid='ignore'):
            shares=1-amount/variance
            pool=1-amount.sum(axis=1)/variance.sum(axis=1)
        lines[name]=dict(pooled=summary(pool[0],pool[1:]),
                         perOutput=[summary(v[0],v[1:]) for v in shares.T])
    return dict(status='descriptive',authors=n,styleReadings=58,topicReadings=300,simulationStyleReadings=57,
                lastStyleReading='capitalizedShare',rank=rank,V=variance[0].tolist(),S=s.tolist(),
                cA=ca,cB=cb,lines=lines,fittedMatrixHeldFixed=True)
