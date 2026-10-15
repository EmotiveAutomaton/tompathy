# Ported from Sounding Line, copyright 2026 Abraham Haskins (MIT).
# See engine/NOTICE-SOUNDING-LINE.txt and reference-sources.json.
from collections import defaultdict
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
ACTIONS = ("accept", "edit", "dismiss", "ignore")

def features(r,prior,annotated):
    doc=set(r['document'][-1200:].lower().split());menus=r['menu']
    overlap=max((len(doc & set(s.lower().split()))/max(1,len(set(s.lower().split()))) for s in menus),default=0)
    prev=r.get('previous_handling',prior[-1]['handling'] if prior else None)
    x=[1,len(menus)/10,np.log1p(np.mean([len(s) for s in menus]))/8,overlap,
       np.log1p(r['decision_index'])/10]+[float(prev==c) for c in ACTIONS]
    if annotated:
        for c in ACTIONS:
            rows=[p for p in prior if p['handling']==c]
            chars=[p['effort']['chars_typed_after'] for p in rows]
            latency=[p['effort']['decide_seconds'] for p in rows if p['effort']['decide_seconds'] is not None]
            x.extend([np.log1p(np.mean(chars))/8 if chars else 0,np.log1p(np.median(latency))/8 if latency else 0,float(not latency)])
    return np.array(x,dtype=float)

def matrix(rows,annotated):
    histories=defaultdict(list);out=[]
    for r in rows:
        past=[p for p in histories[r['writer']] if p['resolved_at']<=r['open_at']]
        out.append(features(r,past,annotated));histories[r['writer']].append(r)
    return np.array(out)

def global_fit(x,y):
    d=x.shape[1]
    def f(v):
        w=v.reshape(d,4);p=softmax(x@w,axis=1)
        loss=-np.log(np.maximum(p[np.arange(len(y)),y],1e-300)).mean()+.005*(w[1:]**2).sum()
        p[np.arange(len(y)),y]-=1;p/=len(y);grad=x.T@p;grad[1:]+=.01*w[1:]
        return loss,grad.ravel()
    result=minimize(f,np.zeros(d*4),jac=True,method='L-BFGS-B',options={'maxiter':500})
    if not result.success:raise ValueError('pooled optimization failed')
    return result.x.reshape(d,4)

def intercept_fit(logits,y,weights,penalty):
    weights=np.asarray(weights,dtype=float);weights=weights/weights.sum()
    def f(r):
        p=softmax(logits+r,axis=1);loss=-np.sum(weights*np.log(np.maximum(p[np.arange(len(y)),y],1e-300)))+penalty*np.sum(r*r)
        p[np.arange(len(y)),y]-=1
        return loss,(p*weights[:,None]).sum(0)+2*penalty*r
    result=minimize(f,np.zeros(4),jac=True,method='L-BFGS-B')
    if not result.success:raise ValueError('writer optimization failed')
    return result.x

def proper(p,y):
    return dict(half_brier=float(.5*np.sum((p-np.eye(4)[y])**2)),log_loss=float(-np.log(max(p[y],1e-300))))
