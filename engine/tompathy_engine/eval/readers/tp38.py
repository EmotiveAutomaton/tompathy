"""Food-topic removal on the saved, stratified G1 sample."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ...packs.trigger import TAGS
from ..back_half.reporting import save_json
from .affect_data import ed_situations
from .checkpoint import completed
from .tp36 import SOURCE, verify_order

FOUR = {'ashamed','guilty','embarrassed','disgusted'}
WORDS = ('ashamed','guilty')
LIMIT = 'One source of short situations; one small local reader, checked only against a word list.'


def read(path):
    return json.loads(path.read_bytes())


def unit_stats(value, words, food, design):
    """Nine moments per form: mass, sum and squared sum for all, ashamed and guilty."""
    base = np.column_stack([np.ones(len(value)),value,value**2])
    member = np.column_stack([np.ones(len(value)),*(words==name for name in WORDS)])
    moments = (member[:,:,None]*base[:,None,:]).reshape(len(value),9)
    masks = [design*(food>=0),design*(food==0),food>=0,food==0]
    return np.column_stack([moments*w[:,None] for w in masks])


def lifts(totals):
    arrays = totals.reshape(-1,4,3,3)
    mass, sums, squared = (arrays[:,:,:,i] for i in range(3))
    with np.errstate(divide='ignore',invalid='ignore'):
        mean = sums/mass
        other = (sums[:,:,:1]-sums[:,:,1:])/(mass[:,:,:1]-mass[:,:,1:])
        sd = np.sqrt(np.maximum(0,squared[:,:,0]/mass[:,:,0]-mean[:,:,0]**2))
        return (mean[:,:,1:]-other)/sd[:,:,None]


def estimate(values, draws):
    good = draws[np.isfinite(draws)]
    return {'estimate':float(values) if np.isfinite(values) else None,
            'interval':np.quantile(good,[.025,.975]).tolist() if len(good) else None,
            'finiteDraws':len(good)}


def analyze(value, words, writers, food, design, check):
    levels, inverse = np.unique(words,return_inverse=True)
    _,group = np.unique(writers,return_inverse=True)
    nw = int(group.max()+1)
    label = np.eye(len(levels))[inverse]
    summary = np.column_stack([label,label*(food>=0)[:,None],label*(food==1)[:,None]])
    rows = np.column_stack([unit_stats(value,words,food,design),summary])
    grouped = np.zeros((nw,rows.shape[1]))
    np.add.at(grouped,group,rows)
    point = grouped.sum(axis=0)
    samples = []
    rng = np.random.default_rng(23)
    for _ in range(80):
        check()
        samples.append(rng.multinomial(nw,np.full(nw,1/nw),size=25)@grouped)
    samples = np.concatenate(samples)
    observed = lifts(point[:36])[0]
    bootstrap = lifts(samples[:,:36])
    n, valid, yes = point[36:].reshape(3,-1)
    counts = samples[:,36:].reshape(len(samples),3,-1)
    with np.errstate(invalid='ignore',divide='ignore'):
        prevalence = counts[:,2]/counts[:,1]
    shares = {str(w):{**estimate(yes[i]/valid[i] if valid[i] else np.nan,prevalence[:,i]),
                      'sampled':int(n[i]),'valid':int(valid[i]),'food':int(yes[i]),
                      'unknown':int(n[i]-valid[i]),'unknownBounds':[yes[i]/n[i],(yes[i]+n[i]-valid[i])/n[i]]}
              for i,w in enumerate(levels)}
    contrasts = {}
    for i,key in [(0,'sourceWeighted'),(2,'sampleUnweighted')]:
        table={}
        for j,name in enumerate(WORDS):
            pre,post=observed[i:i+2,j]
            table[name]={'before':estimate(pre,bootstrap[:,i,j]),
                         'after':estimate(post,bootstrap[:,i+1,j]),
                         'afterMinusHalfBefore':estimate(post-.5*pre,bootstrap[:,i+1,j]-.5*bootstrap[:,i,j]),
                         'fellByMoreThanHalf':bool(pre>0 and post<.5*pre)}
        contrasts[key]=table
    return shares,contrasts


def run(ed_dir, source, root, output, check, ledger, protocol):
    source,root=Path(source),Path(root)
    previous=completed(source,'TP28')
    if sha256(source/'receipt.json')!=SOURCE or sha256(source/'artifact-manifest.json')!=previous['artifactsPin']:
        raise ValueError('TP28 source changed')
    d=root/'workstation/jobs/G1'; evidence=read(root/'Q1-G1-completion.json')['workstation']
    r=read(d/'receipt.json')
    if (not evidence['nativeExit'] or not evidence['newHoldsLock'] or evidence['launcherExit']['code']!=0
            or evidence['owner']!=r['owner'] or r['job']!='G1' or r['status']!='complete'
            or evidence['sourceReceiptPin']!=sha256(d/'receipt.json')
            or read(d/'complete.json')['receiptPin']!=evidence['sourceReceiptPin']
            or sha256(d/'artifacts.json')!=r['artifactsPin']):
        raise ValueError('G1 source or exact exit evidence differs')
    manifest=read(d/'artifacts.json')['files']
    source_ids=read(root/'intake-a/workstation/G1.json')
    binding=r['roles']['W']['binding']
    if sha256(root/'intake-a/workstation/G1.json')!=binding['inputPin']:
        raise ValueError('Original G1 study selection changed')
    template=d/'W/protocol.json'
    if sha256(template)!=manifest['W/protocol.json']:
        raise ValueError('Original word list changed')
    key=read(template)['secondKey']
    if hashlib.sha256(('\n'.join(key)+'\n').encode()).hexdigest()!=binding['wordListPin']:
        raise ValueError('G1 word-list identity differs')
    ed,ident=ed_situations(ed_dir)
    if ident!=previous['sources']['ed']['identity']:
        raise ValueError('Source situation identity differs')
    selected=[row['id'] for row in source_ids]
    target=ed.label.isin(FOUR)
    other=sorted(ed.loc[~target,'id'],key=lambda k:hashlib.sha256(('TP38:23:'+k).encode()).digest())
    if selected!=[*ed.loc[target,'id'],*other[:1000]] or len(set(selected))!=3915:
        raise ValueError('Four complete named groups and the registered control sample required')
    indices=ed.set_index('id',drop=False).index.get_indexer(selected)
    a=source/'ed/scores.npz'
    if sha256(a)!=read(source/'artifact-manifest.json')['files']['ed/scores.npz']:
        raise ValueError('Saved food-tag forecasts differ')
    verify_order(a,ed.id)
    with np.load(a,allow_pickle=False) as data:
        value=data['scores'][:,TAGS.index('food')]
    group=ed.iloc[indices]; words=group.label.to_numpy()
    food=np.full(len(indices),-1)
    agreement=np.zeros((2,2),int); kinds={}; counts=Counter()
    for i,item in enumerate(source_ids):
        if i%128==0:
            check()
        rel=f'W/row-{i:06d}.json'
        if sha256(d/rel)!=manifest[rel]:
            raise ValueError('Saved reader response differs')
        saved=read(d/rel)
        lexical=bool(set(re.findall(r'[a-z]+',item['text'].casefold())).intersection(key))
        if (item['text']!=group.iloc[i].text or saved['id']!=item['id'] or saved['index']!=i
                or saved['binding']!=binding or lexical!=saved['wordKey']):
            raise ValueError('G1 ordered answer, source text, model or lexical key differs')
        answer=saved['values']
        if answer is not None:
            food[i]=int(answer['about_food'])
            agreement[food[i],int(lexical)]+=1
            kinds.setdefault(words[i],Counter())[answer['kind']]+=1
            counts[answer['kind']]+=1
    if int((food>=0).sum())!=r['roles']['W']['valid']:
        raise ValueError('G1 missing count differs')
    design=np.where(np.isin(words,list(FOUR)),1.,len(other)/1000)
    shares,table=analyze(value[indices],words,group.writer.to_numpy(),food,design,check)
    original={}
    for w in WORDS:
        m=ed.label.to_numpy()==w
        previous_lift=previous['sources']['ed']['labels'][w]['lift'][TAGS.index('food')]
        direct=float((value[m].mean()-value[~m].mean())/value.std())
        if not np.isclose(previous_lift,direct,atol=1e-10,rtol=0):
            raise ValueError('Original full-source food lift differs')
        original[w]={'lift':previous_lift,'newAfterBelowHalfOfOriginal':bool(table['sourceWeighted'][w]['after']['estimate']<previous_lift*.5)}
    result={'card':'TP38','status':'complete','productionAdmission':False,'ledger':ledger,'scope':LIMIT,
            'protocolPin':sha256(protocol),'readerReceiptPin':evidence['sourceReceiptPin'],'tp28ReceiptPin':SOURCE,
            'writerDraws':2000,'sampled':len(food),'valid':int((food>=0).sum()),'controlsPopulation':len(other),
            'shares':shares,'contrasts':table,'originalLifts':original,'kindsByWord':kinds,'kinds':counts,
            'wordList':{'pin':binding['wordListPin'],'matrixReaderByListNoYes':agreement.tolist(),
                        'agreement':float(np.trace(agreement)/agreement.sum())},
            'bothFellByMoreThanHalf':all(row['fellByMoreThanHalf'] for row in table['sourceWeighted'].values())}
    save_json(Path(output)/'receipt.json',result)
