"""Q20 and Q21. Run one registered worker on the open Spark, under its shared flock."""
import argparse
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.special import expit

from word_table_lane import Checks, core, identity, lease, now, pin, read, write

ROOT = Path('/home/agent/tompathy-open/week-20261122')
MODELS = ROOT/'models'
PREVIOUS = ROOT.parent/'person-teacher-20261121'


def encoder(name, cap):
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.set_num_threads(3)
    if not torch.cuda.is_available():
        raise RuntimeError('Spark GPU required')
    tokenizer=AutoTokenizer.from_pretrained(MODELS/name,local_files_only=True,trust_remote_code=False)
    model=AutoModel.from_pretrained(MODELS/name,local_files_only=True,trust_remote_code=False,
                                    dtype=torch.float32,attn_implementation='eager').to('cuda').eval()
    def encode(texts):
        vectors=[]
        with torch.inference_mode():
            for i in range(0,len(texts),32):
                inputs=tokenizer(texts[i:i+32],max_length=cap,padding=True,truncation=True,
                                 return_tensors='pt').to('cuda')
                vectors.append(core.pooled(model(**inputs).last_hidden_state,inputs.attention_mask,torch).cpu().numpy())
        return np.concatenate(vectors)
    return encode


def channels(vectors):
    with np.load(MODELS/'channels.npz') as h:
        params = h['parameters']
        y = np.tile(h['constants'],(len(vectors),1))
        y[:, h['active']] = expit(vectors.astype(float) @ params[:-1]+params[-1])
    return y


def persist(path, **arrays):
    if any(not np.isfinite(a).all() for a in arrays.values() if np.asarray(a).dtype.kind in 'fc'):
        raise ValueError('Nonfinite prediction')
    with path.open('xb') as stream:
        np.savez_compressed(stream, **arrays)


def score_blogs(out, manifest, check):
    base = encoder('base',128)
    need = encoder('need',128)
    worry = encoder('worry',128)
    with np.load(MODELS/'tags.npz') as h:
        weights, bias = h['weights'],h['bias']
    with np.load(MODELS/'worry.npz') as h:
        ww, wb = h['weights'],h['bias']
    seed = int.from_bytes(hashlib.sha256(b'TP45:placebo:23').digest()[:8],'big')
    placebo = np.random.default_rng(seed).normal(size=weights.shape)
    placebo /= np.linalg.norm(placebo,axis=1,keepdims=True)
    persist(out/'placebo-heads.npz',weights=placebo)
    n = 0
    start = time.monotonic()
    for name in sorted(manifest['files']):
        path = ROOT/'Q20-inputs'/name
        with gzip.open(path,'rt',encoding='utf8') as stream:
            rows = [json.loads(line) for line in stream]
        for pos in range(0,len(rows),100):
            check()
            ids, texts = zip(*rows[pos:pos+100],strict=True)
            if any(hashlib.sha256(t.encode()).hexdigest()!=i for i,t in zip(ids,texts,strict=True)):
                raise ValueError('Text binding differs')
            x = base(list(texts))
            y = worry(list(texts))
            need_x = need(list(texts))
            persist(out/f'scores-{n:08d}.npz',ids=np.asarray(ids),tags=expit(need_x @ weights.T+bias),
                    placebo=need_x @ placebo.T,worry=y @ ww.T+wb,channels=channels(x))
            persist(out/'vectors'/f'{n:08d}.npz',x=x)
            n += len(texts)
            if n==500:
                write(out/'pilot.json',dict(texts=n,secondsPer100=(time.monotonic()-start)/5,
                                            total=manifest['counts']['uniqueTexts']))
        write(out/'progress.json',dict(texts=n,shard=name))
    if n!=manifest['counts']['uniqueTexts']:
        raise ValueError('Incomplete text coverage')
    return dict(texts=n)


def pride(out, manifest, check):
    from scipy.optimize import minimize
    folder = ROOT/'Q21-inputs'
    arrays = []
    for src in ('go','envent'):
        with np.load(folder/(src+'-fit.npz')) as d:
            arrays.append((d['x'].astype(float),d['y']))
    x,y = (np.concatenate(v) for v in zip(*arrays,strict=True))
    w = np.concatenate([np.full(len(a),.5/len(a)) for a,_ in arrays])
    def objective(theta):
        check()
        z=x @ theta[:-1]+theta[-1]
        error=(expit(z)-y)*w
        penalty=1/(3*len(x))
        loss=w @ (np.logaddexp(0,z)-y*z)+penalty/2*np.sum(theta[:-1]**2)
        return loss,np.r_[x.T @ error+penalty*theta[:-1],error.sum()]
    fit=minimize(objective,np.zeros(x.shape[1]+1),jac=True,method='L-BFGS-B',
                 options={'maxiter':2000,'ftol':1e-10,'gtol':1e-6,'maxls':50})
    if not fit.success:
        raise RuntimeError(f'PRIDE fit failed: {fit.message}')
    theta=fit.x
    persist(out/'pride.npz',theta=theta)
    for src in ('go','envent','ed'):
        check()
        with np.load(folder/(src+'-forecast.npz')) as d:
            ten=np.column_stack((d['nine'],expit(d['x'].astype(float) @ theta[:-1]+theta[-1])))
            if not np.array_equal(ten[:,:9],d['nine']):
                raise ValueError('Original forecasts differ')
        persist(out/(src+'-ten.npz'),ten=ten)
    enc=encoder('base',128)
    n=0
    start=time.monotonic()
    for block in ('Q11','Q12'):
        with gzip.open(folder/(block+'-sentences.jsonl.gz'),'rt',encoding='utf8') as f:
            from itertools import islice
            index=0
            while batch:=list(islice(f,100)):
                check()
                v=enc([json.loads(line) for line in batch])
                ten=np.column_stack((channels(v),expit(v.astype(float) @ theta[:-1]+theta[-1])))
                persist(out/f'{block}-{index:07d}.npz',ten=ten)
                index+=len(v)
                n+=len(v)
                if n==500:
                    write(out/'pilot.json',dict(texts=n,secondsPer100=(time.monotonic()-start)/5))
    prior=ROOT/'jobs/Q20'
    q20=read(prior/'receipt.json')
    for name,h in q20['vectors'].items():
        check()
        path=prior/'vectors'/name
        if pin(path)!=h:
            raise ValueError('Saved Q20 vectors changed')
        with np.load(path) as batch:
            values=expit(batch['x'].astype(float) @ theta[:-1]+theta[-1])
        persist(out/('blog-pride-'+name),pride=values)
    return dict(sourceCounts=manifest['counts'],sentences=n,iterations=int(fit.nit))


def run(job, registration):
    cfg=read(ROOT/'registration.json')
    if pin(ROOT/'registration.json')!=registration or pin(Path(__file__))!=cfg['code'][Path(__file__).name]:
        raise ValueError('Registration or worker changed')
    for name,h in cfg['code'].items():
        if pin(Path(__file__).parent/name)!=h:
            raise ValueError('Helper snapshot differs')
    with lease(Path('/home/agent/gpu.lock')):
        out=ROOT/'jobs'/job
        out.mkdir(parents=True,exist_ok=False)
        owner=dict(identity(),job=job,commit=cfg['commit'],registration=registration,at=now())
        write(out/'owner.json',owner)
        try:
            with core.Guard(out,96) as thermal:
                guards=Checks(ROOT,out,thermal)
                def check():
                    guards.check()
                    if (PREVIOUS/'STOP').exists() or time.time()>=cfg['endUTC']:
                        raise RuntimeError('Stop or week deadline reached')
                check()
                m=read(ROOT/(job+'-inputs.json'))
                if pin(ROOT/(job+'-inputs.json'))!=cfg['manifests'][job]:
                    raise ValueError('Input manifest differs')
                for folder,files in [(MODELS,cfg['models']),(ROOT/(job+'-inputs'),m['files'])]:
                    for name,h in files.items():
                        check()
                        path=(folder/name).resolve()
                        if not path.is_relative_to(folder) or pin(path)!=h:
                            raise ValueError('Model or input file changed')
                if job=='Q20':
                    (out/'vectors').mkdir()
                result={'Q20':score_blogs,'Q21':pride,'Q22':news}[job](out,m,check)
                check()
            outputs={p.name:pin(p) for p in out.glob('*.npz')}
            vectors={p.name:pin(p) for p in (out/'vectors').glob('*.npz')}
            write(out/'receipt.json',dict(status='complete',owner=owner,outputs=outputs,vectors=vectors,result=result))
            write(out/'complete.json',dict(sourceReceiptPin=pin(out/'receipt.json')))
        except Exception as exc:
            write(out/'failed.json',dict(owner=owner,error=str(exc)))
            raise


def news(out,manifest,check):
    from types import SimpleNamespace
    from word_table_lane import rate
    from tp31_teacher import PROMPT,SCHEMA,valid_label
    counts=manifest['counts']
    write(out/'source-counts.json',counts)
    result={}
    for block in ('essays','sentences'):
        path=ROOT/'Q22-inputs'/(block+'.json')
        items=read(path)
        folder=out/block
        folder.mkdir()
        template=(PROMPT,SCHEMA['properties'],valid_label,False) if block=='sentences' else None
        prompt=PROMPT if template else core.CORRECTED_PROMPT
        lengths={r['id']:len((prompt+r['text']).encode()) for r in items}
        def guard_news():
            check()
            if not (folder/'first100.json').exists() and (folder/'progress.json').exists():
                p=read(folder/'progress.json')
                if p['rows']>=100:
                    if p['rows']!=100:
                        raise ValueError('Missed the 100-text timing boundary')
                    write(folder/'first100.json',dict(p,projectedSeconds=len(items)*p['secondsPer100']/100,
                                                       total=len(items)))
        result[block]=rate(ROOT,folder,items,'B','Q22',dict(job='Q22',block=block,inputPin=pin(path)),
                           SimpleNamespace(check=guard_news),template=template,token_lengths=lengths)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('job',choices=['Q20','Q21','Q22'])
    parser.add_argument('registration')
    args=parser.parse_args()
    from word_table_lane import Busy
    from word_table_lane import settings
    settings()
    if args.job != 'Q22':
        import torch
        torch.set_num_interop_threads(1)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        torch.use_deterministic_algorithms(True)
    try:
        run(args.job,args.registration)
    except Busy:
        raise SystemExit(74)
