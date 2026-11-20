"""Guarded GPU execution of the four TP30 fits for each commissioned size and seed."""
import gc
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import types
import urllib.request
from pathlib import Path

MODELS=('sentence-transformers/all-MiniLM-L6-v2','sentence-transformers/all-mpnet-base-v2',
        'answerdotai/ModernBERT-large')


def components():
    name='word_table_fine_components'
    package=types.ModuleType(name)
    package.__path__=[str(Path(__file__).resolve().parent)]
    sys.modules[name]=package
    return [importlib.import_module(name+'.'+n) for n in
            ('tp30_encoder','tp30_fine','tp30_training','tp30_prediction')]


def remote_json(url,check):
    check()
    with urllib.request.urlopen(url,timeout=45) as stream:
        result=json.load(stream)
    check()
    return result


def encoder_files(name,initial,dest,check,core):
    if name not in MODELS:
        raise ValueError('Unregistered encoder')
    directory=dest/'encoder'
    record=dest/'source.json'
    if record.exists():
        return directory,json.loads(record.read_bytes())
    dest.mkdir(parents=True,exist_ok=True)
    directory.mkdir(exist_ok=True)
    revision=initial['revision'] if name==MODELS[0] else 'main'
    catalog=dest/'catalog.json'
    if catalog.exists():
        meta=json.loads(catalog.read_bytes())
    else:
        meta=remote_json(f'https://huggingface.co/api/models/{name}/revision/{revision}?blobs=true',check)
        core.write(catalog,meta)
    revision=meta['sha']
    license_id=meta.get('cardData',{}).get('license')
    if not license_id or not all(c in '0123456789abcdef' for c in revision) or len(revision)!=40:
        raise ValueError('Unbound encoder license or revision')
    paths={f['rfilename']:f for f in meta['siblings']}
    files=set(initial['files']) if name==MODELS[0] else {k for k in paths if '/' not in k and
        (k.endswith('.safetensors') or k in {'model.safetensors.index.json','config.json','tokenizer.json',
         'tokenizer_config.json','special_tokens_map.json','vocab.txt','vocab.json','merges.txt'})}
    if not any(k.endswith('.safetensors') for k in files) or 'tokenizer.json' not in files:
        raise ValueError('No registered native safetensors/tokenizer pair')
    pins={}
    for k in sorted(files):
        data=paths[k]
        target=directory/k
        target.parent.mkdir(parents=True,exist_ok=True)
        cache=Path('/srv/open/hf/tompathy-word-table')/name/revision/k
        cache.parent.mkdir(parents=True,exist_ok=True)
        if not cache.exists():
            check()
            with urllib.request.urlopen(f'https://huggingface.co/{name}/resolve/{revision}/{k}',timeout=60) as src, tempfile.NamedTemporaryFile(
                    dir=cache.parent,prefix=cache.name+'.',suffix='.part',delete=False) as out:
                tmp=Path(out.name)
                while block:=src.read(4*1024*1024):
                    check()
                    out.write(block)
            if tmp.stat().st_size!=data['size']:
                raise ValueError('Incomplete encoder transfer')
            wanted=data.get('lfs',{}).get('sha256')
            if wanted and core.digest(tmp)!=wanted:
                raise ValueError('Registry weight hash differs')
            if not wanted and hashlib.sha1(b'blob '+str(tmp.stat().st_size).encode()+b'\0'+tmp.read_bytes()).hexdigest()!=data['blobId']:
                raise ValueError('Registry file identity differs')
            try:
                os.link(tmp,cache)
            except FileExistsError:
                pass
            tmp.unlink()
        if not target.exists():
            os.link(cache,target)
        pins[k]=core.digest(target)
        if 'lfs' in data:
            if pins[k]!=data['lfs']['sha256']:
                raise ValueError('Registry weight hash differs')
        elif hashlib.sha1(b'blob '+str(target.stat().st_size).encode()+b'\0'+target.read_bytes()).hexdigest()!=data['blobId']:
            raise ValueError('Registry file identity differs')
        if name==MODELS[0] and pins[k]!=initial['files'][k]:
            raise ValueError('Original MiniLM source file differs')
    meta={'id':name,'revision':revision,'license':license_id,'files':pins}
    core.write(record,meta)
    return directory,meta


def source_arrays(root,contract,core):
    import numpy as np
    data={}
    for name in ('go','envent','ed'):
        filename='G2-'+name+'.npz'
        path=root/'inputs'/filename
        if core.digest(path)!=contract['files'][filename]:
            raise ValueError('G2 public payload differs')
        with np.load(path,allow_pickle=False) as saved:
            data[name]={k:saved[k] for k in saved.files}
    # F2 is never transmitted inside the G2 payload. Use only the single
    # authorized release once the earlier Q5 selection has been frozen.
    ev=data['envent']
    earlier=contract['earlierTextPins']
    previous={}
    for p in (root/'inputs/Q1.json',root/'inputs/Q2.json',root.parent/'sp1-input-v1/items.json'):
        for row in json.loads(p.read_bytes()):
            if row['id'] in earlier:
                if hashlib.sha256(row['text'].encode()).hexdigest()!=earlier[row['id']]:
                    raise ValueError('Previously authorized original report changed')
                previous[row['id']]=row['text']
    if set(previous)!=set(earlier):
        raise ValueError('An independently sourced duplicate cannot be restored exactly')
    text_values=ev['texts'].tolist()
    for i,ident in enumerate(ev['ids']):
        if ident in previous:
            if text_values[i]:
                raise ValueError('Expected a withheld duplicate')
            text_values[i]=previous[ident]
    ev['texts']=np.asarray(text_values)
    pending=ev['reserved']
    ev['releaseAvailable']=(root/'F2-release/accepted.json').exists()
    if pending.any() and ev['releaseAvailable']:
        folder=root/'F2-release'
        ack=json.loads((folder/'accepted.json').read_bytes())
        raw=folder/'F2-texts.json'
        if ack['files'][raw.name]!=core.digest(raw) or core.digest(raw)!=contract['releasedF2Pin']:
            raise ValueError('G2 cannot use an unbound F2 release')
        words={r['id']:r['text'] for r in json.loads(raw.read_bytes())}
        texts=ev['texts'].tolist()
        for i in np.flatnonzero(pending):
            if texts[i] or ev['ids'][i] not in words:
                raise ValueError('Unexpected reserved text or opaque identity')
            texts[i]=words[ev['ids'][i]]
        ev['texts']=np.asarray(texts)
    return data


def run_one(root, encdir, source, data, seed, component, jobbind, core, guard, helpers, batch):
    import numpy as np
    import torch
    encoder,targets,training,prediction=helpers
    job=root/component
    job.mkdir(parents=True,exist_ok=True)
    if (job/'completed.json').exists():
        return json.loads((job/'completed.json').read_bytes())
    view,label=component.split('-')
    parts=['go'] if view=='go_only' else ['go','envent']
    def joined(field):
        return np.concatenate([data[p][field][data[p]['train']] for p in parts])
    groups=np.concatenate([np.repeat(p,data[p]['train'].sum()) for p in parts])
    spec=targets.training_targets(joined('shares'),joined('unassigned'),groups,'sigmoid' if label=='profile' else 'softmax')
    texts=joined('texts').tolist()
    bound={**jobbind,'component':component}
    model,opt=encoder.load_original(encdir,spec,'cuda',source['files'],guard.check,seed=seed)
    stages=[('pilot',500),('full',3*len(texts))]
    prior=None
    seconds=0.
    for stage,endpoint in stages:
        status=job/(stage+'-complete.json')
        if status.exists():
            existing=json.loads(status.read_bytes())
            prior=job/existing['checkpoint'];prior_pin=existing['checkpointPin']
            if core.digest(prior)!=prior_pin:
                raise ValueError('Completed fitting weights changed')
            seconds+=existing['seconds']
            continue
        runs=sorted(job.glob(stage+'-attempt-*'))
        for path in reversed(runs):
            if (path/'progress.json').is_file():
                prog=json.loads((path/'progress.json').read_bytes())
                prior=path/'checkpoint.pt';prior_pin=prog['checkpointPin']
                if core.digest(prior)!=prior_pin:
                    raise ValueError('Saved fitting prefix changed')
                break
        options={'resume':prior,'resume_pin':prior_pin,'oom_resume':batch==8} if prior else {}
        folder=job/f'{stage}-attempt-{len(runs):03d}'
        if prior and int(torch.load(prior,map_location='cpu',weights_only=True)['examples'])==endpoint:
            state=torch.load(prior,map_location='cpu',weights_only=True)
            if state['contract']!=training.contract(texts,spec,bound,model,opt,seed,batch):
                raise ValueError('Completed boundary has a different fitting contract')
            result={'checkpointPin':prior_pin,'computeSeconds':state['computeSeconds']}
            del state
        else:
            result=training.train_segment(model,opt,texts,spec,folder,guard.check,binding=bound,stop_after=endpoint,
                                          seed=seed,batch_size=batch,**options)
            prior=folder/'checkpoint.pt';prior_pin=result['checkpointPin']
        seconds+=result['computeSeconds']
        core.write(status,{'checkpoint':prior.relative_to(job).as_posix(),'checkpointPin':prior_pin,
                   'examples':endpoint,'seconds':result['computeSeconds'],
                   'projectedThreeEpochSeconds':seconds*3*len(texts)/endpoint})
    saved=torch.load(prior,map_location='cpu',weights_only=True)
    model.load_state_dict(saved['model']);del saved,opt
    timings={}
    for name in (('go','envent') if view=='go_only' else ('ed',)):
        output=job/('predict-'+name)
        finished=job/('prediction-'+name+'.json')
        if finished.exists():
            timings[name]=json.loads(finished.read_bytes())
            continue
        ds=data[name];indices=ds['test'] if name=='go' else np.ones(len(ds['ids']),bool)
        if name=='envent' and not ds['releaseAvailable']:
            indices &= ~ds['reserved']
        pred_binding={k:v for k,v in jobbind.items() if k in ('payloadPin','sourceReceiptPin','protocolPin','implementationPin')}
        pred_binding.update(target=name,modelCheckpointPin=prior_pin)
        attempts=sorted(job.glob(output.name+'-attempt-*'));reuse=[]
        if attempts:
            previous=attempts[-1]
            for file in sorted(previous.glob('batch-*.npz')):
                reuse.append((file,core.digest(file)))
        result=prediction.predict_segment(model,ds['texts'][indices],ds['ids'][indices],spec,
                   job/f'{output.name}-attempt-{len(attempts):03d}',guard.check,binding=pred_binding,
                   stop_after=int(indices.sum()),resume_files=reuse,batch_size=batch)
        timings[name]={'rows':result['durableRows'],'seconds':result['computeSeconds'],'reused':result['reusedRows']}
        core.write(finished,timings[name])
    result={'seed':seed,'batch':batch,'component':component,'examples':3*len(texts),'seconds':seconds,
            'secondsPer100':100*seconds/(3*len(texts)),'predictions':timings}
    core.write(job/'completed.json',result)
    return result


def run(root,out,binding,core,guard):
    os.environ['TOKENIZERS_PARALLELISM']='false'
    import torch
    if not torch.cuda.is_available() or core.api('ps')['models']:
        raise RuntimeError('A released GPU with CUDA training support is required')
    torch.set_num_threads(3)
    torch.set_num_interop_threads(1)
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32=False
    cfgfile=root/'inputs/G2-contract.json'
    cfg=json.loads(cfgfile.read_bytes())
    data=source_arrays(root,cfg,core)
    helpers=components(); records={};skips={}
    for index,rung in enumerate(cfg['rungs']):
        guard.check()
        if rung['id']!=MODELS[index] or rung['seeds']!=([23] if index==0 else [23,47,71]):
            raise ValueError('Unregistered encoder ladder or seeds')
        dest=out/f'rung-{index}';dest.mkdir(exist_ok=True)
        try:
            encdir,source=encoder_files(rung['id'],cfg['initialMiniLM'],dest,guard.check,core)
        except (OSError,ValueError) as exc:
            guard.check()
            skips[rung['id']]='Fetch or source verification failed: '+str(exc)
            core.write(dest/'skipped.json',{'reason':skips[rung['id']]})
            continue
        initial=core.digest(dest/'source.json')
        jobbind={'payloadPin':core.digest(cfgfile),'sourceReceiptPin':cfg['sourceReceiptPin'],'protocolPin':cfg['protocolPin'],
                 'initialEncoderPin':initial,'implementationPin':hashlib.sha256(
                     json.dumps(binding['codePins'],sort_keys=True).encode()).hexdigest()}
        batch=8 if (dest/'half-batch.json').exists() else 16
        for seed in rung['seeds']:
            for component in ('go_only-profile','go_only-control','go_plus_envent-profile','go_plus_envent-control'):
                label=f'rung-{index}-seed-{seed}-{component}'
                if component.startswith('go_plus_envent') and not data['envent']['releaseAvailable']:
                    skips[label]='Full original Crowd training view requires the authorized F2 text release'
                    continue
                while True:
                    try:
                        result=run_one(dest/f'seed-{seed}',encdir,source,data,seed,component,jobbind,core,guard,helpers,batch)
                    except torch.OutOfMemoryError:
                        result=None
                    if result is not None:
                        records[label]=result
                        break
                    gc.collect();torch.cuda.empty_cache()
                    if batch==8:
                        skips[rung['id']]='GPU memory insufficient after the single batch reduction'
                        core.write(dest/'skipped.json',{'reason':skips[rung['id']]})
                        break
                    batch=8;core.write(dest/'half-batch.json',{'firstComponent':label,'from':16,'to':8})
                core.write(out/'progress.json',{'completed':list(records),'skipped':skips,'lastComponent':label})
                if rung['id'] in skips:break
            if rung['id'] in skips:break
        if rung['id'] not in skips:
            from word_table_rd2_trained import run as trained_side
            while True:
                try:
                    table=trained_side(root,dest,encdir,source,data['envent'],helpers,core,guard,batch)
                except torch.OutOfMemoryError:
                    table=None
                except (OSError,ImportError,subprocess.SubprocessError) as exc:
                    guard.check()
                    skips[f'RD2-{index}']='Bound regression dependency or source unavailable: '+str(exc)
                    break
                if table is not None:
                    for fold,metric in table.items():
                        records[f'RD2-rung-{index}-fold-{fold}']=metric
                    break
                gc.collect();torch.cuda.empty_cache()
                if batch==8:
                    skips[f'RD2-{index}']='GPU memory insufficient after the single batch reduction'
                    break
                batch=8;core.write(dest/'half-batch.json',{'firstComponent':'RD2','from':16,'to':8})
    core.write(out/'ladder-components.json',{'completed':records,'skipped':skips})
    return records
