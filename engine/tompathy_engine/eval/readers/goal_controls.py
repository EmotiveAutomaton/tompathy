"""New TP4 lexical controls on the unchanged prepared proposal pilot."""
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ...preview.surface import WORD
from ..back_half.goals import without_answers
from ..back_half.reporting import save_json
from ..two_day.goals import lexical_order, ranks
from ..two_day.pilots import lexical_summary


def orders(query,candidates,frequency):
    bags=[Counter(m.group().casefold() for m in WORD.finditer(c['text'])) for c in candidates]
    terms=sorted(set().union(*bags))
    q=Counter(m.group().casefold() for m in WORD.finditer(query))
    count=len(bags)
    df={w:sum(w in b for b in bags) for w in terms}
    length=np.array([sum(b.values()) for b in bags],float)
    average=float(length.mean())
    if not average:
        raise ValueError('No candidate terms')
    bm25=np.zeros(count)
    for w in q:
        if w not in df:
            continue
        tf=np.array([b[w] for b in bags],float)
        idf=math.log(1+(count-df[w]+.5)/(df[w]+.5))
        bm25+=idf*tf*2.2/(tf+1.2*(1-.75+.75*length/average))*q[w]
    # Same TP7 B5 cosine definition; frequency is candidate text only, with
    # duplicate candidate documents counted once across the fixed pilot.
    idf=np.array([math.log((1+count)/(1+df[w]))+1 for w in terms])
    matrix=np.array([[b[w] for w in terms] for b in bags])*idf
    total=sum(frequency.values())+len(frequency)
    rarity=np.array([-math.log((frequency[w]+1)/total) for w in terms])
    vector=np.array([q[w] for w in terms])*idf*rarity
    norm=np.linalg.norm(matrix,axis=1)*np.linalg.norm(vector)
    overlap=np.divide(matrix@vector,norm,out=np.zeros(count),where=norm>0)
    return {name:[candidates[i]['id'] for i in sorted(range(count),key=lambda i:(-scores[i],candidates[i]['id']))]
            for name,scores in [('bm25',bm25),('rarity',overlap)]}


def run(prepared,baseline_job,output,check):
    prepared,baseline_job,output=Path(prepared),Path(baseline_job),Path(output)
    path=prepared/'goals.json'
    tasks=json.loads(path.read_text(encoding='utf8'))
    saved=json.loads((baseline_job/'pilot/tfidf.json').read_text(encoding='utf8'))
    unique={}
    for task in tasks:
        for c in task['candidates']:
            if c['id'] in unique and unique[c['id']]!=c['text']:
                raise ValueError('Candidate source differs across queries')
            unique[c['id']]=c['text']
    freq=Counter(m.group().casefold() for text in unique.values() for m in WORD.finditer(text))
    result={name:[] for name in ('tfidf','bm25','rarity')}
    for task in tasks:
        check()
        body=without_answers(task['text'],task['sections'])[:12000]
        ranked=orders(body,task['candidates'],freq)
        ranked['tfidf']=lexical_order(body,task['candidates'])
        for name,order in ranked.items():
            result[name].append({'id':task['id'],'author':task['author'],**ranks(order,task['truth'])})
    if result['tfidf']!=saved:
        raise ValueError('New controls do not reproduce the original TF-IDF pilot exactly')
    save_json(output/'observations.json',result)
    receipt={'card':'TP4-controls','status':'complete','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Fixed 40-proposal lexical ranking; no 9B judgments or maker estimates',
        'inputPin':sha256(path),'baselinePin':sha256(baseline_job/'pilot/tfidf.json'),
        'protocol':{'bm25':'k1=1.2,b=.75; candidate-only IDF; raw query frequency',
            'rarity':'TP7 B5 cosine; corpus frequencies from unique pilot candidate Motivation texts',
            'ties':'candidate ID','query':'Same 12000-character answer-withheld body'},
        'rows':{name:lexical_summary(rows) for name,rows in result.items()},'baselineReproduced':True}
    save_json(output/'receipt.json',receipt)
