"""New registered composition-pause row, using only preserved raw reader scores."""
import json
from copy import deepcopy
from itertools import pairwise
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ..back_half.attention import SENTENCE, word_forecast
from ..back_half.metrics import paired_auc
from ..back_half.reporting import save_json

ADDITIONS = ('V0','V5','previous_nats','next_nats','next2_nats','sentence_tail_nats','after_punctuation')


def augment(tables):
    output=deepcopy(tables)
    for session in output:
        rows=session['words']
        text=session['text']
        if any(a['start']>=b['start'] for a,b in pairwise(rows)):
            raise ValueError('Session words must have exact ordered offsets')
        values=np.array([w['scores']['V1'] for w in rows],float)
        if not np.isfinite(values).all() or any('V5' not in w['scores'] for w in rows):
            raise ValueError('Missing original entropy or surprisal')
        sentences=list(SENTENCE.finditer(text))
        ends=[]
        for word in rows:
            match=next((s for s in sentences if s.start()<=word['start']<s.end()),None)
            if match is None:
                raise ValueError('No sentence for saved word')
            ends.append(match.end())
        prefix=np.r_[0.,values.cumsum()]
        starts=np.array([w['start'] for w in rows])
        for i,word in enumerate(rows):
            stop=int(np.searchsorted(starts,ends[i]))
            gap=text[rows[i-1]['end'] if i else 0:word['start']]
            word['scores'].update(previous_nats=float(values[i-1]) if i else 0.,
                next_nats=float(values[i+1]) if i+1<len(rows) else 0.,
                next2_nats=float(values[i+2]) if i+2<len(rows) else 0.,
                sentence_tail_nats=float(prefix[stop]-prefix[i]),
                after_punctuation=float(any(c in '.,;:!?—–-()[]{}' for c in gap)))
    return output


def run(source,output,check):
    source,output=Path(source),Path(output)
    tables_path=source/'attention/window/tables.json'
    previous_path=source/'attention/attention-window.json'
    previous=json.loads(previous_path.read_text(encoding='utf8'))
    tables=augment(json.loads(tables_path.read_text(encoding='utf8')))
    receipt={'card':'TP18','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Same saved CoAuthor writer-typed eligible words, writer folds and original reader scores',
        'sources':{'tablesPin':sha256(tables_path),'originalReceiptPin':sha256(previous_path),
                   'enginePin':previous['enginePin'],'dataPin':previous['dataPin']},
        'protocol':{'features':list(ADDITIONS),'baseline':'Original five features; fold-local frequency and scaling',
            'boundaries':'Previous/next raw nats across sentences; missing page-edge words are zero. Tail includes current word to sentence end.',
            'decision':'Lower paired whole-writer 95% bound exceeds .02',
            'scope':'Includes current word V0 and the six predeclared additions; forward context is an offline feature'},
        'rows':[]}
    save_json(output/'receipt.json',receipt)
    check()
    rows,base=word_forecast(tables)
    y=[w['stop'] for _,w in rows]
    writers=[s['writer'] for s,_ in rows]
    # No primary tuning or model selection occurs among the exploratory rows.
    for name,features,registered in [('all',ADDITIONS,True)]+[(v,(v,),False) for v in ADDITIONS[1:]]:
        check()
        save_json(output/'phase.json',{'phase':name})
        selected,prediction=word_forecast(tables,features)
        if [(s['session'],w['start'],w['end']) for s,w in selected]!=[(s['session'],w['start'],w['end']) for s,w in rows]:
            raise ValueError('New row changed original word eligibility')
        result=paired_auc(y,base,prediction,writers)
        result.update(name=name,features=list(features),registered=registered,bar=.02,
                      clearsBar=result['interval'][0]>.02,words=len(rows),sessions=len(tables))
        receipt['rows'].append(result)
        np.savez(output/f'{name}-forecasts.npz',baseline=base,forecast=prediction)
        save_json(output/'receipt.json',receipt)
    receipt['status']='complete'
    receipt['probe']='not needed' if receipt['rows'][0]['clearsBar'] else 'preplanned Smol 360M hidden-layer probe eligible; not yet run'
    save_json(output/'receipt.json',receipt)
