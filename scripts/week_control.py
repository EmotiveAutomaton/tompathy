"""TP54. Pool within-stratum control slopes for two contrasts with anger."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

from cb_inputs import pin
from tompathy_engine.eval.readers.person_halves import resamples, summary
from tompathy_engine.eval.readers.tp39 import TP28, saved
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.word_panels import pinned
from tompathy_engine.packs.trigger import TAGS
from week_need_losses import GROUPS, standard

QUESTIONNAIRE = "0d43c722ed99c1c6dcd501ce1944d5e1d1a8d8cc03a7627111ee1e3439486ffe"
ISEAR = "8629db4d9ba73a830c79883801ae074305c33aca4152c590ea5893b5d8e2f404"


def leaders(values, names):
    return ["+".join(name for name, value in zip(names, row, strict=True) if value == row.max())
            for row in values]


def slopes(pos, neg, x):
    """Batched unpenalized logistic fits on the five original control bins."""
    total = pos + neg
    a = np.zeros(len(total))
    b = np.zeros_like(a)
    for _ in range(60):
        prob = expit(a[:, None] + b[:, None] * x)
        wt = total * prob * (1 - prob)
        err = pos - total * prob
        h0, h1, h2 = wt.sum(1), wt @ x, wt @ (x*x)
        det = h0*h2 - h1*h1
        den = np.where(det > 1e-10, det, np.nan)
        da = (h2*err.sum(1) - h1*(err @ x))/den
        db = (h0*(err @ x) - h1*err.sum(1))/den
        if np.all((np.abs(da)+np.abs(db)<1e-8) | ~np.isfinite(db)):
            break
        a += da
        b += db
    ok = (np.abs(da)+np.abs(db)<1e-8) & (det>1e-10)
    return np.where(ok,b,0), np.divide(det,h0,out=np.zeros_like(det),where=ok)


def table(frame, groups, check):
    strata, g = np.unique(groups, return_inverse=True)
    people, who = np.unique(frame.prolific_id, return_inverse=True)
    emotions = ["anger","sadness","fear"]
    cnt = np.zeros((len(people),len(strata),3,5))
    np.add.at(cnt,(who,g,[emotions.index(e) for e in frame.emotion],frame.self_control.to_numpy(int)-1),1)
    weights = np.vstack((np.ones(len(people)),resamples(len(people))))
    x = (np.arange(1.,6.)-frame.self_control.mean())/frame.self_control.std(ddof=0)
    results = {}
    for target in (1,2):
        draws = []
        for block in np.array_split(weights,40):
            check()
            counts = (block @ cnt.reshape(len(people),-1)).reshape(len(block),len(strata),3,5)
            b,w = slopes(counts[:,:,target].reshape(-1,5),counts[:,:,0].reshape(-1,5),x)
            w=w.reshape(len(block),-1)
            if not draws:
                used=[str(s) for s in strata[w[0]>0]]
            mass=w.sum(1)
            draws.extend((b.reshape(w.shape)*w).sum(1)/np.where(mass>0,mass,np.nan))
        results[emotions[target]]=dict(summary(draws[0],np.asarray(draws[1:])),estimableStrata=used)
    return results


def prepare(out,check):
    base=Path(".local/readers/data/crowd-enVent2023")
    folder=Path(".local/nine-channel/tp28-a")
    receipt=pinned(folder/"receipt.json",TP28)
    src=base/"corpus/crowd-enVent_generation.tsv"
    if (pin(src)!=receipt["sources"]["envent"]["identity"]["files"]["generation"] or
        pin(base/"questionnaires/generation/round-9/strategy2_excludedtopics/anger.pdf")!=QUESTIONNAIRE or
        pin(Path(".local/week-20261122/TP54-isear-codebook.doc"))!=ISEAR):
        raise ValueError("TP54 source or questionnaire changed")
    resp=["self_responsblt","other_responsblt","chance_responsblt"]
    frame=pd.read_csv(src,sep="\t",quoting=3,dtype={"text_id":str},usecols=["text_id","prolific_id","emotion","self_control",*resp])
    path=saved(folder,"envent/scores.npz",receipt)
    verify_order(path,frame.text_id)
    with np.load(path,allow_pickle=False) as data:
        if frame.text_id.duplicated().any() or receipt["protocol"]["tags"]!=list(TAGS):
            raise ValueError("Tag or roster mismatch")
        tags=standard(data["scores"].astype(float))
    mask=frame.emotion.isin(["anger","sadness","fear"])
    f=frame.loc[mask].copy()
    if not f[[*resp,"self_control"]].isin(range(1,6)).all().all() or f.prolific_id.isna().any():
        raise ValueError("Unexpected rating or missing writer")
    need={k:v for k,v in GROUPS.items() if k!="unplaced"}
    levels=np.column_stack([tags[:,[TAGS.index(t) for t in group]].mean(1) for group in need.values()])
    return dict(card="TP54",writers=f.prolific_id.nunique(),reports=len(f),source=pin(src),tagSource=TP28,
                isear="void: no ordered control rating",responsibility=table(f,leaders(f[resp].to_numpy(),resp),check),
                highestNeed=table(f,leaders(levels[mask],need),check))
