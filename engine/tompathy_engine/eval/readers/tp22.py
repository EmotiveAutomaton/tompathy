"""Research-only multi-page stability with corrected counting and subject controls."""
import hashlib
import heapq
import html
import json
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.cluster import MiniBatchKMeans

from ...packs.aggregate import correct, error_table
from ...packs.registry import sha256
from ...preview.surface import WORD
from ..back_half.attention import SENTENCE
from ..back_half.reporting import save_json
from .affect_data import verify
from .checkpoint import completed, load_head
from .encoders import embeddings

MONTHS={name:i+1 for i,name in enumerate(('january','february','march','april','may','june','july','august','september','october','november','december'))}
TAGS=re.compile(r'<date>\s*(.*?)\s*</date>|<post>(.*?)</post>',re.DOTALL|re.IGNORECASE)


def posts(raw):
    """Read only dates and post bodies, never demographic filename components."""
    current=None
    out=[]
    excluded=0
    for match in TAGS.finditer(raw):
        if match.group(1) is not None:
            parts=match.group(1).strip().lower().split(',')
            try:
                current=date(int(parts[2]),MONTHS[parts[1]],int(parts[0])).isoformat()
            except (ValueError,KeyError,IndexError):
                current=None
        else:
            text=html.unescape(match.group(2)).strip()
            if current is None:
                excluded+=1
            elif len(list(WORD.finditer(text)))>=100:
                out.append({'date':current,'text':text,'ordinal':len(out)})
    return sorted(out,key=lambda r:(r['date'],r['ordinal'])),excluded


def stable_estimate(parts):
    """TR1 split-half reliability: unclipped disattenuation, positive variance first.

    Axes: writer, chronological side, odd/even posts within that side, label.
    Equal odd/even averaging fixes the measurement unit in both controls and data.
    """
    x=np.asarray(parts,float)
    if x.ndim!=4 or x.shape[1:3]!=(2,2) or not np.isfinite(x).all():
        raise ValueError('Finite paired writer halves and within-half replicates required')
    out=[]
    for j in range(x.shape[-1]):
        reliability=[];variance=[]
        means=x[:,:,:,j].mean(axis=2)
        for side in range(2):
            a,b=x[:,side,0,j],x[:,side,1,j]
            r=float(np.corrcoef(a,b)[0,1]) if np.std(a)>0 and np.std(b)>0 else np.nan
            value=2*r/(1+r) if np.isfinite(r) and r>-1 else np.nan
            reliability.append(value)
            variance.append(float(np.var(means[:,side],ddof=1)*value))
        raw=float(np.corrcoef(means.T)[0,1]) if np.all(means.std(axis=0)>0) else np.nan
        stability=raw/np.sqrt(np.prod(reliability)) if min(reliability)>0 else np.nan
        out.append({'reliability':reliability,'true_variance':min(variance),
                    'raw_stability':raw,'corrected_stability':float(stability)})
    return out


def qualify():
    rows=[]
    for truth in (1.,.5,0.):
        rng=np.random.default_rng(20261115)
        a=rng.normal(size=2000); b=truth*a+np.sqrt(1-truth**2)*rng.normal(size=2000)
        latent=np.c_[a,b][:,:,None,None]
        observed=latent+rng.normal(scale=.7,size=(2000,2,2,1))
        estimate=stable_estimate(observed)[0]['corrected_stability']
        rows.append({'planted':truth,'recovered':estimate,'passed':abs(estimate-truth)<.1})
    return {'constructed':True,'writers':2000,'worlds':rows,'passed':all(r['passed'] for r in rows)}


def stability(parts,labels,draws=2000):
    point=stable_estimate(parts)
    rng=np.random.default_rng(23)
    samples=np.array([[[r['true_variance'],r['corrected_stability']] for r in
        stable_estimate(parts[rng.integers(len(parts),size=len(parts))])] for _ in range(draws)])
    result={}
    for j,label in enumerate(labels):
        undefined=(~np.isfinite(samples[:,j])).any(axis=1)
        bounds=None if undefined.any() else np.quantile(samples[:,j],[.025,.975],axis=0)
        measured=bounds is not None and bounds[0,0]>0
        result[label]={**point[j],'variance_interval':bounds[:,0].tolist() if bounds is not None else None,
            'stability_interval':bounds[:,1].tolist() if bounds is not None else None,
            'undefined_resamples':int(undefined.sum()),'variance_measurable':bool(measured),
            'stable_above_half':bool(measured and bounds[0,1]>.5),
            'interpretation':'Stability uninterpretable unless true variance is measurably positive'}
        # JSON does not encode undefined numerical evidence as NaN.
        for key in ('true_variance','raw_stability','corrected_stability'):
            if not np.isfinite(result[label][key]):
                result[label][key]=None
        result[label]['reliability']=[v if np.isfinite(v) else None for v in result[label]['reliability']]
    return result


def run(root,reader_job,counting_job,models,output,check,*,gate_job=None):
    root,output=Path(root),Path(output)
    data=verify(root)
    counted=completed(counting_job,'TP12-gated' if gate_job else 'TP12-L3')
    model=completed(reader_job,'TP10-L3')
    if counted['ladderReceiptPin']!=sha256(Path(reader_job)/'receipt.json'):
        raise ValueError('Counting policy and reader differ')
    policy=counted['policies']['minilm-tuned']
    calibration=qualify()
    report={'card':'TP22-gated' if gate_job else 'TP22','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Research-only Blog Authorship Corpus; maker tier remains closed; no age or sex fields read',
        'source':data,'readerReceiptPin':sha256(Path(reader_job)/'receipt.json'),
        'countingReceiptPin':sha256(Path(counting_job)/'receipt.json'),'policy':policy,
        'constructed_qualification':calibration,'pack':'No maker admission; voluntary subject return remains unruled',
        'protocol':{'cohort':'Lowest SHA-256 1000 writer IDs with >=40 dated posts >=100 words',
            'halves':'Chronological equal sides; each subdivided into alternating posts',
            'measurement':'Pool sentence predictions in each replicate, exact TP12 correction, then condition on emotion',
            'subject_control':'20 unsupervised Potion word-vector clusters; earlier-half other-writer cluster means only',
            'variance':'TR1 Spearman-Brown within-side reliability and observed variance times reliability',
            'stability':'Unclipped consecutive-half correlation divided by sqrt(reliabilities); 2000 whole-writer draws, undefined draw invalidates interval',
            'log_score':'Later mix under earlier writer mix versus other-writer earlier population; subject control adjusts historical departure by later subject composition; clipping 1e-6 then renormalizing',
            'reference':'Sounding Line docs/design/stage-15/week5/TR1_BACK_HALF.md; split-half measurement adaptation, no gain model',
            'bars':'After subject control: at least three labels with whole interval >.5 and positive-variance interval; own-history log-score gain interval >0'}}
    if policy['status']!='complete' or not calibration['passed']:
        report.update(status='blocked',reason='No qualified selected-head counting policy' if policy['status']!='complete' else 'Constructed estimator qualification failed')
        save_json(output/'receipt.json',report)
        return
    gate_predict = None
    if gate_job:
        from .artifacts import verified
        from .encoders import load_encoder
        gate, _ = verified(gate_job, 'TP25', check)
        if not gate.get('qualifies') or policy.get('gateReceiptPin') != sha256(Path(gate_job)/'receipt.json'):
            raise ValueError('TP22 counting and gate sources differ')
        if sha256(Path(counting_job)/'gated-error-table.json') != counted['gatedErrorTablePin'] or policy['gatedErrorTablePin'] != counted['gatedErrorTablePin']:
            raise ValueError('TP22 gated calibration bytes changed')
        gate_encode, gate_identity = load_encoder(Path(models)/'minilm', 'minilm', cap=128)
        with np.load(Path(gate_job)/'head.npz', allow_pickle=False) as d:
            gate_w, gate_b = d['weights'], d['bias']
        def gate_predict(texts):
            values = []
            for start in range(0, len(texts), 16):
                check()
                values.extend((gate_encode(texts[start:start+16])@gate_w.T+gate_b)[:, 0])
            return 1/(1+np.exp(-np.clip(values, -700, 700))) >= gate['final_threshold']
        report['gate'] = {'sourceReceiptPin': sha256(Path(gate_job)/'receipt.json'), 'encoder': gate_identity,
                          'scope': 'New gate-conditioned stability; old TP22 prerequisite block unchanged'}
    save_json(output/'receipt.json',report)
    candidates=[];excluded=0;eligible_writers=0
    with zipfile.ZipFile(root/'blogs.zip') as archive:
        for name in archive.namelist():
            if not name.lower().endswith('.xml'):
                continue
            check()
            writer=Path(name).name.split('.',1)[0]
            if not writer.isdigit():
                raise ValueError('Unexpected writer filename structure')
            rows,dropped=posts(archive.read(name).decode('latin1'))
            excluded+=dropped
            if len(rows)>=40:
                eligible_writers+=1
                item=(-int(hashlib.sha256(writer.encode()).hexdigest(),16),writer,rows)
                if len(candidates)<1000:
                    heapq.heappush(candidates,item)
                elif item[0]>candidates[0][0]:
                    heapq.heapreplace(candidates,item)
    if len(candidates)<1000:
        raise ValueError('Fewer than 1000 eligible writers; do not silently shrink cohort')
    selected=sorted(candidates,key=lambda r:-r[0]);del candidates
    records=[]
    for _,writer,rows in selected:
        middle=len(rows)//2
        for i,row in enumerate(rows):
            side=int(i>=middle)
            records.append({**row,'writer':writer,'side':side,'replicate':(i-middle if side else i)%2})
    report['cohort']={'writers':len(selected),'eligible_writers':eligible_writers,'posts':len(records),'undated_excluded':excluded}
    save_json(output/'cohort.json',records)
    vectors,topic_identity,_=embeddings([r['text'] for r in records],Path(models)/'potion','potion',output/'subjects',check)
    cluster=MiniBatchKMeans(n_clusters=20,random_state=23,batch_size=256,n_init=10).fit_predict(vectors)
    report['topic_encoder']=topic_identity
    _encode,predict,reader=load_head(reader_job)
    labels=model['rows'][str(model['selected_seed'])]['labels']
    neutral=labels.index('no-emotion'); emotion=[i for i in range(len(labels)) if i!=neutral]
    table=error_table(model['rows'][str(model['selected_seed'])]['development_error_counts'])
    if gate_job:
        error = json.loads((Path(counting_job)/'gated-error-table.json').read_text(encoding='utf8'))
        if error['labels'] != labels:
            raise ValueError('Gated counting labels differ')
        table = error_table(np.asarray(error['counts']), error['smoothing'])
    counts=np.zeros((len(records),len(labels)),int)
    for i,row in enumerate(records):
        check()
        sentences=[m.group().strip() for m in SENTENCE.finditer(row['text']) if m.group().strip()]
        if sentences:
            p,_=predict(sentences,check)
            predicted = p.argmax(axis=1)
            if gate_predict:
                predicted[~gate_predict(sentences)] = neutral
            counts[i]=np.bincount(predicted,minlength=len(labels))
        save_json(output/'post-counts'/f'{i:07d}.json', {'index': i, 'counts': counts[i].tolist(), 'cluster': int(cluster[i])})
        if (i+1)%100==0 or i+1==len(records):
            np.savez(output/'sentence-counts-partial.npz',counts=counts[:i+1],clusters=cluster[:i+1])
            save_json(output/'progress.json',{'posts':i+1,'total':len(records)})
    def mixture(c):
        if c.sum()<policy['minimum'] or c[neutral]==c.sum():
            return None
        value=correct(c,table,policy['prior']-1)[emotion]
        return value/value.sum() if value.sum()>1e-10 else None
    banks=defaultdict(list)
    for i,r in enumerate(records):
        banks[r['writer'],r['side'],r['replicate']].append(i)
    early=np.array([r['side']==0 for r in records])
    writers=sorted({r['writer'] for r in records})
    raw=[];controlled=[];own_scores=[];controlled_scores=[];withheld=0
    for writer in writers:
        check()
        other=np.array([r['writer']!=writer for r in records])&early
        population=mixture(counts[other].sum(axis=0))
        subject=[mixture(counts[other&(cluster==c)].sum(axis=0)) for c in range(20)]
        if population is None or any(s is None for s in subject):
            withheld+=1;continue
        parts=np.zeros((2,2,len(emotion)));expected=np.zeros_like(parts)
        good=True
        for side in range(2):
            for rep in range(2):
                ix=np.array(banks[writer,side,rep])
                value=mixture(counts[ix].sum(axis=0))
                if value is None:
                    good=False;break
                parts[side,rep]=value
                weights=np.bincount(cluster[ix],weights=counts[ix].sum(axis=1),minlength=20)
                expected[side,rep]=weights@np.array(subject)/weights.sum()
        if not good:
            withheld+=1;continue
        raw.append(parts);controlled.append(parts-expected)
        prior=parts[0].mean(axis=0);later=parts[1].mean(axis=0)
        clip=lambda x:np.maximum(x,1e-6)/np.maximum(x,1e-6).sum()
        own_scores.append(float(later@(np.log(clip(prior))-np.log(clip(population)))))
        contextual=expected[1].mean(axis=0)
        forecast=contextual+(parts[0]-expected[0]).mean(axis=0)
        controlled_scores.append(float(later@(np.log(clip(forecast))-np.log(clip(contextual)))))
    if len(raw)<20:
        report.update(status='insufficient-support',supported=len(raw),withheld=withheld)
    else:
        names=[labels[i] for i in emotion]
        raw_rows=stability(np.array(raw),names);adjusted=stability(np.array(controlled),names)
        def log_score(values):
            values=np.array(values);rng=np.random.default_rng(23)
            draws=[values[rng.integers(len(values),size=len(values))].mean() for _ in range(2000)]
            ci=np.quantile(draws,[.025,.975]).tolist()
            return {'gain':float(values.mean()),'interval':ci,'passed':ci[0]>0}
        report.update(status='complete',reader=reader,supported=len(raw),withheld=withheld,
            raw={'labels':raw_rows,'own_history':log_score(own_scores)},
            controlled={'labels':adjusted,'own_history':log_score(controlled_scores)},
            controls={'typical_writer':'Other-writer earlier population and subject means',
                'bow':'Word-vector subjects are a topic control, not an independently trained emotion classifier',
                'human':'No human longitudinal reference available'})
        report['bars_passed']=sum(r['stable_above_half'] for r in adjusted.values())>=3 and report['controlled']['own_history']['passed']
    save_json(output/'receipt.json',report)
