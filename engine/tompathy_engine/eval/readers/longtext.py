"""Unpacked page shares still obey the exact selected-head counting policy."""
from pathlib import Path

import numpy as np

from ...packs.aggregate import AggregationPolicy, error_table, shares
from ...packs.registry import sha256
from ..back_half.attention import SENTENCE
from .checkpoint import completed, load_head
from .regression import correlation, partial_correlation


def page_reader(reader_job,counting_job):
    reader_job,counting_job=Path(reader_job),Path(counting_job)
    model=completed(reader_job,'TP10-L3')
    counted=completed(counting_job,'TP12-L3')
    if counted['ladderReceiptPin']!=sha256(reader_job/'receipt.json'):
        raise ValueError('Counting policy and selected reader differ')
    policy=counted['policies']['minilm-tuned']
    pin={'readerReceiptPin':sha256(reader_job/'receipt.json'),
         'countingReceiptPin':sha256(counting_job/'receipt.json'),'unpacked':True,
         'policy':policy,'productionAdmission':False}
    if policy['status']!='complete':
        return None,pin
    row=model['rows'][str(model['selected_seed'])]
    labels=row['labels']
    table=error_table(row['development_error_counts'])
    rule=AggregationPolicy(policy['prior'],policy['minimum'],policy['bootstrap'],policy['seed'])
    _encode,predict,_identity=load_head(reader_job)

    def read(text,check):
        sentences=[m.group().strip() for m in SENTENCE.finditer(text) if m.group().strip()]
        if len(sentences)<rule.minimum:
            return None,len(sentences)
        probabilities,_=predict(sentences,check)
        result=shares(probabilities.argmax(axis=1),table,rule,neutral=labels.index('no-emotion'))
        return None if result is None else {name:r['value'] for name,r in zip(labels,result)},len(sentences)
    return read,pin


def worry_checks(root,reader_job,counting_job,output,check,plan_function):
    import pandas as pd

    from ...preview.surface import WORD
    from ..back_half.reporting import save_json
    read,pin=page_reader(reader_job,counting_job)
    if read is None:
        blocked={'status':'blocked','reason':'No learned TP12 NNLS prior/minimum policy qualifies; TS2 withholds corrected shares',**pin}
        return blocked,{'status':'blocked','reason':'Required negative corrected-share covariate unavailable',
                        'interpretation':'The analyst proposal that plans accompany lower worry remains unsettled'}
    frame=pd.read_csv(Path(root)/'data_phase_1/files/meta/rwwd_full.csv',
                      usecols=['text_long','worry','fear','anxiety','anger','sadness','disgust'])
    records=[]
    missing=0
    for i,row in frame.iterrows():
        check()
        value,n=read(row.text_long,check)
        if value is None:
            missing+=1
        else:
            records.append({'index':i,'mix':value,'ratings':row.drop('text_long').to_dict(),
                'plan':plan_function(row.text_long),'words':len(list(WORD.finditer(row.text_long))),'sentences':n})
        save_json(Path(output)/'longtext-progress.json',{'seen':i+1,'total':len(frame),'eligible':len(records),'withheld':missing})
    save_json(Path(output)/'longtext-observations.json',records)
    if len(records)<3:
        return {'status':'insufficient-support','eligible':len(records),'withheld':missing,**pin}, {'status':'insufficient-support','reason':'Too few supported corrected page shares'}
    names=['fear','anger','sadness','disgust']
    coefficients={a:{b:correlation([r['mix'][a] for r in records],[r['ratings'][b] for r in records])
                      for b in [*names,'anxiety']} for a in names}
    numeric=all(coefficients[a][b] is not None for a in names for b in names)
    passed=numeric and all(coefficients[a][a]>.15 and coefficients[a][a]>max(coefficients[a][b] for b in names if a!=b) for a in names)
    negative=['anger','disgust','fear','guilt','shame','sadness','boredom']
    controls=np.array([[r['words'],sum(r['mix'][name] for name in negative)] for r in records])
    fractions=np.array([r['plan'] for r in records]); worry=np.array([r['ratings']['worry'] for r in records])
    partial=partial_correlation(fractions,worry,controls)
    rng=np.random.default_rng(23)
    draws=[]
    for _ in range(1000):
        ix=rng.integers(len(records),size=len(records))
        value=partial_correlation(fractions[ix],worry[ix],controls[ix])
        if value is not None:
            draws.append(value)
    return {'status':'complete','eligible':len(records),'withheld':missing,'correlations':coefficients,
        'bar_passed':passed,'anxiety_above_015':coefficients['fear']['anxiety'] is not None and coefficients['fear']['anxiety']>.15,**pin}, {
        'status':'complete','partial_correlation':partial,'interval':np.quantile(draws,[.025,.975]).tolist() if draws else None,
        'controls':['word count','corrected negative-label share'],'negative_labels':negative,
        'interval_method':'1000 writer/text resamples, one long text per writer',
        'interpretation':'Analyst proposal remains unsettled; correlation in one topic/month/country does not identify a causal effect of plans'}
