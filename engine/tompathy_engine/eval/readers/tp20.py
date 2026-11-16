"""Assigned negotiation priorities from the first five opponent messages."""
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

from ..back_half.reporting import save_json
from .affect_data import verify
from .checkpoint import load_head

ISSUES=('Food','Water','Firewood')


def examples(dialogues):
    records=[]
    excluded=0
    for dialogue in dialogues:
        for participant in ('mturk_agent_1','mturk_agent_2'):
            # Only ordinary messages, never terminal allocation task data or
            # the supplied private reasons, outcomes, demographics/personality.
            messages=[m['text'] for m in dialogue['chat_logs'] if m['id']==participant and not m['task_data']]
            if len(messages)<5:
                excluded+=1
                continue
            assigned=dialogue['participant_info'][participant]['value2issue']
            order=[assigned[k] for k in ('High','Medium','Low')]
            if set(order)!=set(ISSUES):
                raise ValueError('Invalid assigned priority permutation')
            records.append({'dialogue':str(dialogue['dialogue_id']),'messages':messages[:5],
                            'target':[3-order.index(i) for i in ISSUES]})
    return records,excluded


def rank_scores(truth,prediction,groups):
    order=np.argsort(-prediction,axis=1,kind='stable')
    gold=np.argsort(-truth,axis=1)
    correct=(order==gold).all(axis=1)
    _,inverse=np.unique(groups,return_inverse=True)
    totals=np.bincount(inverse,weights=correct)
    counts=np.bincount(inverse)
    rng=np.random.default_rng(23)
    draws=[]
    for _ in range(1000):
        ix=rng.integers(len(counts),size=len(counts))
        draws.append(totals[ix].sum()/counts[ix].sum())
    accuracy=float(correct.mean())
    return {'exact_order_accuracy':accuracy,'top_priority_accuracy':float((order[:,0]==gold[:,0]).mean()),
        'interval':np.quantile(draws,[.025,.975]).tolist(),'cluster':'whole dialogue, 1000 resamples',
        'bar':.45,'passes':accuracy>=.45,'n':len(correct),'dialogues':len(counts)}


def run(root,reader_job,output,check):
    root,output=Path(root),Path(output)
    identity=verify(root)
    records,excluded=examples(json.loads((root/'data/casino.json').read_text(encoding='utf8')))
    texts=['\n'.join(r['messages']) for r in records]
    groups=np.array([r['dialogue'] for r in records])
    y=np.array([r['target'] for r in records],float)
    encode,_,reader=load_head(reader_job)
    vectors=encode([m for r in records for m in r['messages']],check).reshape(len(records),5,-1)
    # Preserve message positions; do not truncate five messages to one sentence.
    x=vectors.reshape(len(records),-1)
    receipt={'card':'TP20','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Randomly assigned resource priorities, not values or refusals','source':identity,'reader':reader,
        'protocol':{'input':'Five ordinary messages from the target participant only; fewer than five excluded',
            'folds':'Five dialogue-disjoint folds; both perspectives always share a fold',
            'ranker':'Ridge alpha=3 predicts three ordinal scores; descending order, stable fixed issue-order ties',
            'encoder':'Five separately encoded capped messages concatenated in chronological order',
            'writerLimitation':'Global participant IDs unavailable; role names are not writer IDs'},
        'excluded_short_perspectives':excluded,'rows':{},
        'external_references':{'source':'https://aclanthology.org/2022.findings-naacl.50.pdf',
            'Table1_k5':{'random':.1646,'bow':.2849,'roberta_CD_CA_DND':.6357},
            'section5_3_expert_100_dialogues':.75,
            'limitation':'Published model sees partial dialogue context and adapted additional training data; our opponent-only input and folds differ'}}
    save_json(output/'receipt.json',receipt)
    predictions={name:np.zeros_like(y) for name in ('constant','bow','reader')}
    for fold,(train,test) in enumerate(GroupKFold(5).split(x,groups=groups)):
        check()
        save_json(output/'phase.json',{'phase':'fold','fold':fold})
        predictions['constant'][test]=y[train].mean(axis=0)
        vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
        a=vectorizer.fit_transform([texts[i] for i in train])
        b=vectorizer.transform([texts[i] for i in test])
        predictions['bow'][test]=Ridge(alpha=3).fit(a,y[train]).predict(b)
        predictions['reader'][test]=Ridge(alpha=3).fit(x[train],y[train]).predict(x[test])
    receipt['rows']={name:rank_scores(y,p,groups) for name,p in predictions.items()}
    receipt['chance']=1/6
    np.savez(output/'forecasts.npz',truth=y,**predictions)
    receipt['status']='complete'
    save_json(output/'receipt.json',receipt)
