"""Construct RD2 writer folds locally. Only assignments and public training labels travel."""
import hashlib
import json
from collections import Counter

from word_table_inputs import ROOT, pin, write


def prepare(source,dest):
    import numpy as np
    from tompathy_engine.eval.readers.envent import RATINGS, load
    corpus=load(ROOT/'.local/readers/data/crowd-enVent2023')
    frame=corpus.reports
    rows=frame.text_id.astype(str).to_numpy()
    train=np.ones(len(rows),bool);train[corpus.test]=False
    if int(train.sum())!=5400:
        raise ValueError('Original training population required')
    groups=frame.prolific_id.astype(str).to_numpy()
    group_pin=lambda g: hashlib.sha256(('RD2:writer:23:'+g).encode()).digest()
    census=Counter(groups[train]);sizes=[0]*5;slots={}
    for name,n in sorted(census.items(),key=lambda e:(-e[1],group_pin(e[0]))):
        fold=min(range(5),key=lambda j:sizes[j])
        slots[name]=fold;sizes[fold]+=n
    fold=np.asarray([slots[g] if g in slots else int.from_bytes(group_pin(g)[:4],'big')%5 for g in groups])
    splits=[]
    for i in range(5):
        eligible={g for g,f in slots.items() if f!=i}
        dev=set(sorted(eligible,key=lambda g:hashlib.sha256(('RD2:dev:23:'+g).encode()).digest())[:max(1,len(eligible)//10)])
        dev_mask=train & np.isin(groups,list(dev))
        fit=train & (fold!=i) & ~dev_mask
        if set(groups[fit])&set(groups[fold==i]) or set(groups[fit])&set(groups[dev_mask]):
            raise ValueError('Outer or development writer leakage')
        splits.append(np.where(fit,1,np.where(dev_mask,2,np.where(train&(fold==i),3,0))))
    dest.mkdir(exist_ok=False)
    target=dest/'G2-RD2.npz'
    # writer targets exist for 5,400 training reports only. No ID mapping or
    # raw participant identifiers need to leave this machine.
    np.savez_compressed(target,train_indices=np.flatnonzero(train),folds=fold,splits=np.array(splits),
                        ratings=frame.loc[train,RATINGS].to_numpy(np.float32),labels=frame.loc[train,'y'].to_numpy(int))
    cfg=json.loads((source/'specification.json').read_bytes())
    cfg['modules'].append('scripts/word_table_rd2_trained.py')
    cfg['pins'][target.name]=pin(target)
    cfg['jobs']['G2']['files'][target.name]=str(target)
    wheels=ROOT/'.local/word-table/rd2-wheel-pins/wheels.json'
    cfg['pins']['G2-wheels.json']=pin(wheels)
    cfg['jobs']['G2']['files']['G2-wheels.json']=str(wheels)
    cfg['provenance'].update(rd2TrainingRows=int(train.sum()),rd2HeldOutWriterTargetsTransferred=0,
                             outerFoldSizes=sizes)
    write(dest/'specification.json',cfg)
    return sizes


if __name__=='__main__':
    import os
    for var in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[var]='2'
    base=ROOT/'.local/word-table'
    print(prepare(base/'fine-transfer-c',base/'fine-with-rd2-b'))
