"""Boundary and known-answer checks for the two person-disjoint curator amendments."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from cb_features import crossfit
from cb_inputs import digest
from cb_isear_tables import statistic, writer_readings
from cb_tables import both_profiles, matching


def test_cc_threshold_and_held_author_isolation():
    labels=[f'w{i}' for i in range(200)]
    owners=np.repeat(labels,2)
    rng=np.random.default_rng(5)
    x=rng.normal(size=(400,4))
    y=rng.normal(size=(400,8))
    assert crossfit(x[:-2],y[:-2],owners[:-2],labels[:-1])[0] is None
    residual,proof=crossfit(x,y,owners,labels)
    assert proof['foldSizes']==[100,100]
    changed=y.copy()
    changed[owners==labels[0]]+=2
    after,_=crossfit(x,changed,owners,labels)
    held=np.isin(owners,labels[::2])
    np.testing.assert_allclose((after-residual)[held],(changed-y)[held],atol=1e-12)


def test_cd_recomputes_tied_ranks_and_counts():
    x=np.array([2,1,4,2,5,np.nan],float)
    y=np.array([3,1,2,2,3,1],float)
    out=statistic(x,y,np.arange(6),np.ones((3,6)))
    assert out['reports']==out['people']==5
    np.testing.assert_allclose(out['value'],spearmanr(x[:5],y[:5]).statistic)


def test_cd_all_splits_and_country_fallback(monkeypatch):
    from cb_tables import halves
    monkeypatch.setattr(halves,'resamples',lambda n:np.ones((2,n)))
    rows=[]
    keys={}
    for i in range(1096):
        key=json.dumps(['country','small' if i<9 else 'large',str(i)])
        person=digest(key)
        keys[person]=key
        for feeling in range(7 if i<1091 else 6):
            rows.append((person,'country','small' if i<9 else 'large',str(feeling),i))
    frame=pd.DataFrame(rows,columns=['person','country','city','feeling','i'])
    y=np.tile(frame.i.values[:,None],(1,19)).astype(float)
    score=writer_readings(y,np.zeros((len(y),2)),frame,keys,lambda:None)
    assert score['completePeople']==1091 and score['incompletePeople']==5
    assert score['fallbackCells']==7 and score['fallbackReports']==63
    assert score['styleCleared']['mean']['value']>.99


def test_gap_drops_middle_dates():
    owners=np.array(['x']*6)
    dates=np.array(list('123456'))
    v=np.arange(6.)[:,None]
    np.testing.assert_allclose(both_profiles(v,owners,dates,['x'],True).ravel(),[.5,4.5])
    assert matching(np.ones((2,1,2)),{'style':[0],'topic':[1]},lambda:None)['pairs']==1
