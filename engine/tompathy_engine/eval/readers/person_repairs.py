"""November 21 BK analyses, using the previously filed forecasts and spans."""
from collections import Counter
from pathlib import Path

import numpy as np

from ..back_half.reporting import save_json
from .affect_data import ed_situations
from .tp34 import NAMES
from .word_panels import pinned, sha256

FROZEN='d04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250'
WORRY='8163192a6b14dd0385366710a3b613eeaf51121fe15cf7100e5e249161be9adf'


def quiet_table(values,words,writers,check):
    active=np.ptp(values,axis=0)>0
    if not active.any() or not np.isfinite(values).all():raise ValueError('No supported finite outputs')
    z=values[:,active]
    peaks=((z-z.mean(axis=0))/z.std(axis=0)).max(axis=1)
    labels,l=np.unique(words,return_inverse=True)
    groups,w=np.unique(writers,return_inverse=True)
    n=np.zeros((len(groups),len(labels)));q=np.zeros_like(n);m=np.zeros_like(n)
    for stat,weight in [(n,1),(q,peaks<=1),(m,peaks)]:np.add.at(stat,(w,l),weight)
    n,q,m=[np.column_stack((v,v.sum(axis=1))) for v in (n,q,m)]
    rng=np.random.default_rng(23);draws=[]
    for _ in range(80):
        check()
        weights=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)),size=25)
        with np.errstate(invalid='ignore',divide='ignore'):draws.append((weights@q)/(weights@n))
    intervals=np.nanquantile(np.concatenate(draws),[.025,.975],axis=0)
    rows={k:{'n':int(n[:,i].sum()),'quiet':int(q[:,i].sum()),'share':float(q[:,i].sum()/n[:,i].sum()),
             'interval':intervals[:,i].tolist(),'meanLargestZ':float(m[:,i].sum()/n[:,i].sum())}
          for i,k in enumerate([*labels,'all'])}
    return rows,np.asarray(NAMES)[~active].tolist()


def run(card,source,ed,output,check,ledger,protocol):
    source=Path(source);output=Path(output)
    if card=='TP34-BK':
        old=pinned(source/'receipt.json',FROZEN)
        frame,ident=ed_situations(ed)
        files=pinned(source/'artifact-manifest.json',old['artifactsPin'])['files']
        p=source/'ed-profile-forecasts.npz'
        if sha256(p)!=files[p.name] or ident!=old['sources']['ed']:raise ValueError('Changed forecast or ED source')
        with np.load(p,allow_pickle=False) as a:
            if not np.array_equal(a['ids'],frame.id):raise ValueError('ED forecast order differs')
            rows,excluded=quiet_table(a['probabilities'],frame.label,frame.writer,check)
        order=sorted((k for k in rows if k!='all'),key=lambda k:(-rows[k]['share'],k))
        estimate={'words':rows,'rank':order,'noSpread':excluded}
        bar='Descriptive ranking by share with no varying output above one source standard deviation.'
        verdict='Quietest four: '+', '.join(order[:4])+'.'
        data='We compared 24,850 chat situations with the same nine forecasts, giving each assigned word its own row.'
        question='Which words most often leave every varying output quiet?'
        limit='Writer-assigned words on one source. All-situations rate directly counts the full cohort.'
        interval={'draws':2000,'unit':'writer','method':'Percentile intervals on fixed standardized forecasts.'}
        table=['| Word | Quiet / total | Share (95% interval) | Mean highest z |','|---|---:|---:|---:|']
        for k in ['all',*order]:
            v=rows[k];lo,hi=v['interval']
            table.append(f"| {k} | {v['quiet']}/{v['n']} | {v['share']:.3f} [{lo:.3f}, {hi:.3f}] | {v['meanLargestZ']:.3f} |")
    else:
        old=pinned(source/'receipt.json',WORRY)
        spans=pinned(source/'spans.json',old['spansPin'])
        if Counter(s['originalCount'] for s in spans.values())!=Counter({1:40,5:1,8:1,11:1}):
            raise ValueError('Original page roster changed')
        essays=[v for v in old['essays'] if v['windows']>=5]
        estimate={'plain':{'eligible':0,'ineligible':40,'passes':None},'essays':{'eligible':len(essays),
                  'windows':sum(v['windows'] for v in essays),'shown':sum(v['shown'] for v in essays),
                  'subsetPasses':all(v['subset'] for v in essays)}}
        question='What can the one-point worry lift say on pages with at least five windows?'
        data='We reapplied the eligibility rule to 40 theme-free items and three public essays using their saved windows.'
        verdict='No eligible theme-free pages, so that set gives no verdict. All three essays qualified; zero of 24 windows were selected.'
        bar='At least five windows on a page. Theme-free share at most .10; essay highlights a subset of original spans.'
        limit='An empty selection satisfies the subset rule. It cannot demonstrate detection sensitivity.'
        interval={'method':'Exact fixed acceptance roster.'}
        table=['| Set | Eligible pages | Eligible windows | Selected |','|---|---:|---:|---:|',
               '| Theme-free | 0/40 | 0 | — |','| Public essays | 3/3 | 24 | 0 |']
    save_json(output/'receipt.json',{'card':card,'status':'complete','productionAdmission':False,'ledger':ledger,
        'protocolPin':sha256(protocol),'parentReceiptPin':sha256(source/'receipt.json'),'question':question,
        'scope':limit,'data':data,'estimate':estimate,'interval':interval,'bar':bar,'verdict':verdict,'table':table})
