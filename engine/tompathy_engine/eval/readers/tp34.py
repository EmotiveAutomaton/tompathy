"""Word recipes and quiet outputs, using the completed frozen forecasts."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .checkpoint import completed
from .tp30 import CHANNELS

NAMES=['SADNESS' if channel=='PANIC/GRIEF' else channel for channel in CHANNELS]
PLEASANT={'proud':('SEEKING','PLAY'),'hopeful':('SEEKING','FEAR'),'joyful':('PLAY','SEEKING'),'grateful':('CARE','PLAY')}
UNPLEASANT={'embarrassed':('SHAME','PLAY'),'ashamed':('SHAME','SADNESS'),'guilty':('CARE','SHAME'),
            'anxious':('FEAR','SADNESS'),'jealous':('SADNESS','RAGE'),'lonely':('SADNESS',)}
LIMIT=('The reader was trained on strangers\' labels of forum comments. SHAME\'s output rests on one source. '
       'LUST\'s stand-in means wanting in general. A row is a recipe for a word and not a reading of a channel.')


def writer_lifts(p,labels,writers,check,draws=2000):
    p=np.asarray(p,float)
    if p.ndim!=2 or not np.isfinite(p).all() or len(p)!=len(labels) or len(p)!=len(writers):
        raise ValueError('Finite aligned forecasts, words and original writers required')
    words,y=np.unique(labels,return_inverse=True);groups,w=np.unique(writers,return_inverse=True)
    ng,nw,nc=len(groups),len(words),p.shape[1]
    count=np.zeros((ng,nw));sums=np.zeros((ng,nw,nc));sq=np.zeros((ng,nc))
    np.add.at(count,(w,y),1);np.add.at(sums,(w,y),p);np.add.at(sq,w,p*p)
    stats=np.column_stack((count,sums.reshape(ng,-1),sq))
    def contrast(v):
        n=v[:,:nw,None];total=n.sum(axis=1,keepdims=True)
        pos=v[:,nw:-nc].reshape(-1,nw,nc);all_sums=pos.sum(axis=1,keepdims=True)
        sd=np.sqrt(np.maximum(0,v[:,-nc:][:,None,:]/total-(all_sums/total)**2))
        with np.errstate(divide='ignore',invalid='ignore'):
            return (pos/n-(all_sums-pos)/(total-n))/sd
    point=contrast(stats.sum(axis=0,keepdims=True))[0]
    rng=np.random.default_rng(23)
    samples=[]
    for start in range(0,draws,25):
        check()
        weights=rng.multinomial(ng,np.full(ng,1/ng),size=min(25,draws-start))
        samples.append(contrast(weights@stats))
    samples=np.concatenate(samples);valid=np.isfinite(samples).sum(axis=0)
    if not np.isfinite(point).all() or np.any(valid<.95*draws):
        raise ValueError('Insufficient supported writer draws for the full word table')
    return words,point,np.nanquantile(np.where(np.isfinite(samples),samples,np.nan),[.025,.975],axis=0),valid


def permutation_reference(words,lifts,top):
    top_by_word={word:{NAMES[i] for i in np.argsort(-v,kind='stable')[:top]} for word,v in zip(words,lifts)}
    by_group=[]
    for mapping in (PLEASANT,UNPLEASANT):
        by_group.append(np.array([sum(len(top_by_word[word]&set(names)) for word,names in zip(mapping,dealt))
                                     for dealt in itertools.permutations(mapping.values())]))
    all_deals=(by_group[0][:,None]+by_group[1]).ravel()
    hits={w:sorted(top_by_word[w]&set(names)) for w,names in {**PLEASANT,**UNPLEASANT}.items()}
    observed=sum(map(len,hits.values()));bar=float(np.quantile(all_deals,.95))
    return {'hits':observed,'named':19,'perWordHits':hits,'cutoff':bar,'deals':len(all_deals),
            'passes':bool(observed>bar),'histogram':np.bincount(all_deals,minlength=20).tolist()}


def run(source,ed_root,go_root,output,check,ledger,protocol):
    source,output=Path(source),Path(output)
    previous=completed(source,'TP30-frozen')
    manifest=source/'artifact-manifest.json'
    if sha256(source/'receipt.json')!='d04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250' or sha256(manifest)!=previous['artifactsPin']:
        raise ValueError('Previously landed TP30 source binding differs')
    paths=['ed-profile-forecasts.npz','go-profile-forecasts.npz','go-targets.npz']
    pins={k:sha256(source/k) for k in paths}
    if any(json.loads(manifest.read_bytes())['files'][k]!=h for k,h in pins.items()):
        raise ValueError('Saved original forecast or split bytes changed')
    ed,es=ed_situations(ed_root);go,_,labels,gs=go_comments(go_root)
    if es!=previous['sources']['ed'] or gs!=previous['sources']['go']:
        raise ValueError('Original ED or Go release changed')
    with np.load(source/paths[0],allow_pickle=False) as a:
        if not np.array_equal(a['ids'],ed.id):raise ValueError('ED forecast order differs')
        p=a['probabilities']
    with np.load(source/paths[2],allow_pickle=False) as a:
        if not np.array_equal(a['ids'],go.id):raise ValueError('Go roster differs')
        test=go.loc[a['test'],'id'].to_numpy(str)
    with np.load(source/paths[1],allow_pickle=False) as a:
        if not np.array_equal(a['ids'],test):raise ValueError('Go held-out forecast order differs')
        forum=a['probabilities']
    raw=pd.concat([pd.read_csv(Path(go_root)/f'goemotions_{i}.csv',usecols=['id','rater_id',*labels],
                               keep_default_na=False) for i in (1,2,3)])
    if raw.duplicated(['id','rater_id']).any() or not set(test)<=set(raw.id):
        raise ValueError('Invalid source rater keys')
    neutral=raw.groupby('id').neutral.min().reindex(test).to_numpy()==1
    if not neutral.any():raise ValueError('No unanimous-neutral held-out comments')
    floors=np.quantile(forum[neutral],.95,axis=0)
    quiet=(p<=floors).all(axis=1);peak=p.max(axis=1);original=ed.label.to_numpy()
    words,point,ci,n_valid=writer_lifts(p,original,ed.writer.to_numpy(),check)
    if len(words)!=32 or p.shape!=(24850,9):raise ValueError('Original word table differs')
    summary={str(word):{'n':int((original==word).sum()),'lifts':point[i].tolist(),
                        'low':ci[0,i].tolist(),'high':ci[1,i].tolist(),'finiteDraws':n_valid[i].tolist(),
                        'meanLargestOutput':float(peak[original==word].mean()),'quietShare':float(quiet[original==word].mean())}
             for i,word in enumerate(words)}
    disappointed=summary['disappointed']['lifts'][NAMES.index('SEEKING')]
    receipt={'card':'TP34','status':'complete','productionAdmission':False,'ledger':ledger,'scope':LIMIT,
             'sourceReceiptPinFrozen':sha256(source/'receipt.json'),'protocolPin':sha256(protocol),
             'sources':{'ED':es['intakePin'],'Go':gs['intakePin'],'arrays':pins},
             'channels':NAMES,'rows':summary,'writerDraws':2000,'writers':int(ed.writer.nunique()),
             'floor':{'heldOut':len(test),'unanimousNeutral':int(neutral.sum()),'perChannel':floors.tolist()},
             'baseline':{'meanLargestOutput':float(peak.mean()),'quietShare':float(quiet.mean())},
             'quietRanking':sorted(summary,key=lambda word:-summary[word]['quietShare']),
             'blindTopTwo':permutation_reference(words,point,2),'blindTopThree':permutation_reference(words,point,3),
             'disappointedSeeking':{'lift':disappointed,'belowZero':disappointed<0}}
    save_json(output/'receipt.json',receipt)
