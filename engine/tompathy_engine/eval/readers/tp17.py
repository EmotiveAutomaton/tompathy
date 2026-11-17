"""EmoCause top-k hit rate for fixed held-out ED label-head word deletion."""
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import softmax
from sklearn.feature_extraction.text import TfidfVectorizer

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, verify
from .checkpoint import completed, load_head


def token_spans(text,tokens):
    """Monotonic literal matching keeps deletion on original source characters."""
    position=0
    spans=[]
    replacements={'``':'"',"''":'"','-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']'}
    for token in tokens:
        token=replacements.get(token,token)
        start=text.find(token,position)
        if start<0 or text[position:start].strip():
            raise ValueError('EmoCause token does not align exactly to original situation')
        end=start+len(token)
        spans.append((start,end))
        position=end
    if text[position:].strip():
        raise ValueError('EmoCause tokenization omits source text')
    return spans


def hit_rates(values,annotations):
    order=np.argsort(-np.asarray(values),kind='stable')
    gold=set(annotations)
    return {str(k):int(bool(gold&set(order[:k]))) for k in (1,3,5)}


def supplied_label(raw, labels, source_label):
    """Decode the publisher's label delimiters, retaining exact ED agreement."""
    label = raw[2:-2] if raw.startswith('__') and raw.endswith('__') else raw
    if label not in labels or label != source_label:
        raise ValueError('EmoCause emotion does not match its original ED label')
    return label


def run(root,ed_root,coverage_job,reader_job,output,check):
    root,coverage_job,output=Path(root),Path(coverage_job),Path(output)
    identity=verify(root)
    completed(coverage_job,'TP13')
    meta=json.loads((coverage_job/'ed-head.json').read_text(encoding='utf8'))
    if sha256(coverage_job/'ed-head.npz')!=meta['headPin'] or meta['training_split']!='train only':
        raise ValueError('ED training-only attribution head binding differs')
    encode,_,reader=load_head(reader_job)
    if reader!=meta['reader']:
        raise ValueError('Attribution encoder does not match the ED training head')
    with np.load(coverage_job/'ed-head.npz',allow_pickle=False) as data:
        weights,bias=data['weights'].copy(),data['bias'].copy()
    bow_meta=json.loads((coverage_job/'ed-bow-head.json').read_text(encoding='utf8'))
    if sha256(coverage_job/'ed-bow-head.npz')!=bow_meta['headPin']:
        raise ValueError('BOW attribution control hash differs')
    vectorizer=TfidfVectorizer(vocabulary=bow_meta['vocabulary'],ngram_range=(1,2),sublinear_tf=True)
    with np.load(coverage_job/'ed-bow-head.npz',allow_pickle=False) as data:
        bow_weights,bow_bias=data['weights'].copy(),data['bias'].copy()
        vectorizer.idf_=data['idf'].copy()
    ed,ed_pin=ed_situations(ed_root)
    by=ed.set_index('id')
    rows=[]
    for split in ('valid','test'):
        for r in json.loads((root/f'{split}.json').read_text(encoding='utf8')):
            if (r['conv_id'] not in by.index or by.loc[r['conv_id'],'source_split']=='train'
                    or r['original_situation']!=by.loc[r['conv_id'],'text']):
                raise ValueError('Attribution item is not an exact held-out ED situation')
            if any(r['tokenized_situation'][j]!=word for word,j in r['annotation']):
                raise ValueError('Annotation indices differ from the provided tokens')
            label = supplied_label(r['emotion'], meta['labels'], by.loc[r['conv_id'],'label'])
            if label not in bow_meta['labels']:
                raise ValueError('EmoCause emotion is absent from the BOW head')
            rows.append((split,r,label))
    if len({r['conv_id'] for _,r,_ in rows})!=len(rows):
        raise ValueError('Attribution splits overlap')
    receipt={'card':'TP17','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Words marked as causes in held-out situations, not the maker\'s motives',
        'source':identity,'ed':ed_pin,'reader':reader,'headPin':meta['headPin'],
        'protocol':{'method':'Drop each original token span and measure fall in supplied emotion-label probability',
            'head':'ED training split only; TP13 fixed head',
            'metric':'At least one annotated token among top k; deterministic original-order ties',
            'denominator':'All exactly aligned items, exclusions explicit; no token-level tuning'},
        'references':{'human':[.413,.811,.95],'chance':[.107,.306,.485],'paper':[.173,.481,.684]},
        'total':len(rows),'completed':0,'excluded_alignment':0,'rows':{}}
    save=lambda:save_json(output/'receipt.json',receipt)
    save()
    observations=[]
    observation_path=output/'observations.jsonl'
    with observation_path.open('x',encoding='utf8') as stream:
        for index,(split,r,label) in enumerate(rows):
            check()
            try:
                spans=token_spans(r['original_situation'],r['tokenized_situation'])
            except ValueError:
                receipt['excluded_alignment']+=1
                continue
            text=r['original_situation']
            items=[text]+[text[:a]+text[b:] for a,b in spans]
            x=encode(items,check)
            probabilities=softmax(x@weights.T+bias,axis=1)[:,meta['labels'].index(label)]
            deltas=probabilities[0]-probabilities[1:]
            outcome={'split':split,'id':r['conv_id'],'tokens':len(spans),
                     'writer':str(by.loc[r['conv_id'],'writer']),
                     'hits':hit_rates(deltas,[a[1] for a in r['annotation']]),'scores':deltas.tolist()}
            bow_probability=softmax(vectorizer.transform(items)@bow_weights.T+bow_bias,axis=1)[:,bow_meta['labels'].index(label)]
            annotation=[a[1] for a in r['annotation']]
            outcome['bow']=hit_rates(bow_probability[0]-bow_probability[1:],annotation)
            outcome['constant']=hit_rates(np.zeros(len(spans)),annotation)
            n,m=len(spans),len(set(annotation))
            outcome['chance']={str(k):1-math.comb(n-m,min(k,n))/math.comb(n,min(k,n)) if n-m>=min(k,n) else 1. for k in (1,3,5)}
            observations.append(outcome)
            stream.write(json.dumps(outcome,ensure_ascii=True)+'\n')
            stream.flush()
            receipt['completed']=len(observations)
            if index%25==0:
                save_json(output/'progress.json',{'completed':len(observations),'seen':index+1,'total':len(rows)})
                save()
    for split in ('valid','test','all'):
        subset=[r for r in observations if split=='all' or r['split']==split]
        groups={w:[r for r in subset if r['writer']==w] for w in sorted({r['writer'] for r in subset})}
        bank=list(groups.values())
        rng=np.random.default_rng(23)
        sums=np.array([[sum(r['hits'][str(k)] for r in group) for k in (1,3,5)] for group in bank])
        counts=np.array([len(g) for g in bank])
        samples=[]
        for _ in range(1000):
            ix=rng.integers(len(bank),size=len(bank))
            samples.append(sums[ix].sum(axis=0)/counts[ix].sum())
        bounds=np.quantile(samples,[.025,.975],axis=0)
        result={'n':len(subset),'hit_rates':{str(k):float(np.mean([r['hits'][str(k)] for r in subset])) for k in (1,3,5)},
            'intervals':{str(k):bounds[:,i].tolist() for i,k in enumerate((1,3,5))},
            'interval_method':'1000 whole-writer resamples, fixed predictions',
            'controls':{name:{str(k):float(np.mean([r[name][str(k)] for r in subset])) for k in (1,3,5)} for name in ('bow','constant','chance')}}
        result.update(primary=result['hit_rates']['3']>=.481,stretch=result['hit_rates']['3']>=.60)
        receipt['rows'][split]=result
    receipt['status']='complete' if not receipt['excluded_alignment'] else 'partial'
    save()
