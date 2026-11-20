"""RD2 trained arm using writer-disjoint folds and the original TP10 two-head recipe."""
import importlib.metadata
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


def dependencies(root,out,core,check):
    pins=json.loads((root/'inputs/G2-wheels.json').read_bytes())
    if set(pins)!={'scipy','scikit-learn','joblib','threadpoolctl'}:
        raise ValueError('Unknown linear head dependency set')
    target=out/'linear-libraries'; wheels=out/'linear-wheels'
    wheels.mkdir(exist_ok=True)
    files=[]
    for row in pins.values():
        url=urllib.parse.urlparse(row['url'])
        if url.scheme!='https' or url.hostname!='files.pythonhosted.org' or Path(row['filename']).name!=row['filename']:
            raise ValueError('Unrecognized pinned wheel location')
        dest=wheels/row['filename']
        if not dest.exists():
            check()
            tmp=dest.with_suffix('.partial')
            with urllib.request.urlopen(row['url'],timeout=60) as stream,tmp.open('wb') as writer:
                while block:=stream.read(1024**2):
                    check()
                    writer.write(block)
            if core.digest(tmp)!=row['sha256']:
                raise ValueError('Linear-head wheel transfer differs')
            tmp.replace(dest)
        if core.digest(dest)!=row['sha256']:
            raise ValueError('Linear-head wheel changed')
        files.append(str(dest))
    if not (target/'verified.json').exists():
        check()
        subprocess.run([sys.executable,'-m','pip','--disable-pip-version-check','install','--no-index','--no-deps',
                        '--no-compile','--target',str(target),*files],check=True,timeout=240)
        core.write(target/'verified.json',pins)
    sys.path.insert(0,str(target))
    for name,row in pins.items():
        if importlib.metadata.version(name)!=row['version']:
            raise ValueError('Linear-head solver version differs')


def current_map(ids,data,split):
    import numpy as np
    if len(split['folds'])!=len(data['ids']) or split['splits'].shape!=(5,len(data['ids'])):
        raise ValueError('RD2 source and fold shapes differ')
    if len(ids)!=5400 or len(set(ids))!=5400 or split['ratings'].shape!=(5400,21):
        raise ValueError('Exact public training labels required')
    return np.asarray(ids)


def embedded(texts,path,model,guard,batch):
    import numpy as np
    import torch
    path.mkdir(exist_ok=True)
    arrays=[]
    model.head=torch.nn.Identity();model.eval()
    with torch.inference_mode():
        for start in range(0,len(texts),16):
            guard.check()
            dest=path/f'block-{start:05d}.npy'
            if not dest.exists():
                part=texts[start:start+16]
                x=torch.cat([model(part[k:k+batch]) for k in range(0,len(part),batch)]).cpu().numpy()
                temp=dest.with_suffix('.tmp')
                with temp.open('wb') as stream:np.save(stream,x)
                os.replace(temp,dest)
            arr=np.load(dest,allow_pickle=False)
            if len(arr)!=min(16,len(texts)-start) or not np.isfinite(arr).all():
                raise ValueError('Incomplete original-encoder vectors')
            arrays.append(arr)
    return np.concatenate(arrays)


def initial_heads(x,y,rating,fit):
    import numpy as np
    from sklearn.linear_model import LogisticRegression, Ridge
    classifier=LogisticRegression(C=10,max_iter=2000,random_state=20261114).fit(x[fit],y[fit])
    if len(classifier.classes_)<3 or not np.array_equal(classifier.classes_,np.arange(len(np.unique(y)))):
        raise ValueError('Missing original feeling label during fold initialization')
    regression=Ridge(alpha=3).fit(x[fit],rating[fit])
    return np.vstack((classifier.coef_,regression.coef_)),np.concatenate((classifier.intercept_,regression.intercept_))


def forecast(model,texts,indices,batch,check):
    import numpy as np
    import torch
    model.eval()
    with torch.inference_mode():
        output=[]
        for start in range(0,len(indices),batch):
            check()
            output.append(model([texts[i] for i in indices[start:start+batch]]).cpu().numpy())
    return np.concatenate(output)


def fit_seed(model,opt,texts,fit,dev,y,ratings,seed,directory,batch,core,guard,atomic_save):
    import numpy as np
    import torch
    from sklearn.metrics import f1_score
    directory.mkdir(parents=True,exist_ok=True)
    result=directory/'development.json'; ckpt=directory/'continue.pt'
    if result.exists():
        return json.loads(result.read_bytes())
    rng=np.random.default_rng(seed);epoch=0;cursor=0;epochs=[];best=-1.;order=rng.permutation(fit)
    if ckpt.exists():
        state=torch.load(ckpt,map_location='cpu',weights_only=True)
        if state['seed']!=seed or not np.array_equal(np.sort(state['order']),np.sort(fit)):
            raise ValueError('RD2 saved seed or fitting rows changed')
        model.load_state_dict(state['model']);opt.load_state_dict(state['opt'])
        epoch,cursor,order,epochs,best=[state[k] for k in ('epoch','cursor','order','epochs','best')]
        order=order.numpy()
        rng.bit_generator.state=state['orderRng'];torch.set_rng_state(state['cpuRng'])
        torch.cuda.set_rng_state_all(state['cudaRng']);del state
    classes=int(y.max()+1)
    while epoch<3:
        model.train()
        while cursor<len(order):
            guard.check()
            indices=order[cursor:cursor+batch]
            opt.zero_grad(set_to_none=True); logits=model([texts[i] for i in indices])
            loss=(torch.nn.functional.cross_entropy(logits[:,:classes],torch.as_tensor(y[indices],device='cuda'))
                  +.1*torch.nn.functional.mse_loss(logits[:,classes:],torch.as_tensor(ratings[indices],device='cuda')))
            if not torch.isfinite(loss):raise ValueError('Nonfinite two-head loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True);opt.step()
            cursor+=len(indices)
            if cursor<len(order) and cursor%512!=0:
                continue
            if cursor==len(order):
                p=forecast(model,texts,dev,batch,guard.check)
                score=float(f1_score(y[dev],p[:,:classes].argmax(1),average='macro'))
                epochs.append(score)
                if score>best:
                    best=score
                    atomic_save(directory/'best.pt',model.state_dict())
                epoch+=1;cursor=0
                if epoch<3:order=rng.permutation(fit)
                finished_epoch=True
            else:
                finished_epoch=False
            atomic_save(ckpt,{'seed':seed,'model':model.state_dict(),'opt':opt.state_dict(),'epoch':epoch,
                'cursor':cursor,'order':torch.as_tensor(order),'epochs':epochs,'best':best,'orderRng':rng.bit_generator.state,
                'cpuRng':torch.get_rng_state(),'cudaRng':torch.cuda.get_rng_state_all()})
            if finished_epoch:break
    summary={'seed':seed,'developmentMacroF1':best,'epochs':epochs,'bestPin':core.digest(directory/'best.pt')}
    core.write(result,summary)
    return summary


def run(root,out,encdir,source,data,helpers,core,guard,batch):
    import numpy as np
    import torch
    directory=out/'rd2-trained'
    directory.mkdir(exist_ok=True)
    dependencies(root,out.parent,core,guard.check)
    encoder,_,training,_=helpers
    with np.load(root/'inputs/G2-RD2.npz',allow_pickle=False) as z:
        split={k:z[k] for k in z.files}
    rows=current_map(split['train_indices'],data,split);all_text=data['texts'].tolist()
    texts=[all_text[i] for i in rows];y=split['labels'];ratings=split['ratings'];classes=int(y.max())+1
    shape={'active':np.arange(classes+21)}
    def fresh(seed):
        return encoder.load_original(encdir,shape,'cuda',source['files'],guard.check,seed=seed)
    model,opt=fresh(23);del opt
    x=embedded(texts,directory/'frozen-train',model,guard,batch);del model
    timings={}
    for fold in range(5):
        d=directory/f'fold-{fold}';d.mkdir(exist_ok=True)
        if (d/'complete.json').exists():
            timings[fold]=json.loads((d/'complete.json').read_bytes())
            continue
        tic=time.monotonic()
        marks=split['splits'][fold][rows];fit=np.flatnonzero(marks==1);dev=np.flatnonzero(marks==2)
        weights,bias=initial_heads(x,y,ratings,fit);scores=[]
        for seed in (23,47,71):
            model,opt=fresh(seed)
            with torch.no_grad():
                model.head.weight.copy_(torch.as_tensor(weights));model.head.bias.copy_(torch.as_tensor(bias))
            scores.append(fit_seed(model,opt,texts,fit,dev,y,ratings,seed,d/f'seed-{seed}',batch,core,guard,training.atomic_save))
            del model,opt
        best=max(scores,key=lambda a:a['developmentMacroF1'])
        core.write(d/'selection.json',{'selected':best,'candidates':scores})
        model,opt=fresh(best['seed']);del opt
        source_weights=d/f"seed-{best['seed']}"/'best.pt'
        if core.digest(source_weights)!=best['bestPin']:raise ValueError('Fitted development winner changed')
        model.load_state_dict(torch.load(source_weights,weights_only=True,map_location='cpu'))
        chosen=list(rows[marks==3])
        if data['releaseAvailable']:
            chosen.extend(np.flatnonzero(data['reserved']&(split['folds']==fold)).tolist())
        # Partition-fixed output files keep OOF and F2 reusable after an interruption.
        for start in range(0,len(chosen),16):
            dest=d/f'forecasts-{start:04d}.npz'
            part=chosen[start:start+16]
            if dest.exists():
                with np.load(dest,allow_pickle=False) as saved:
                    if not np.array_equal(saved['ids'],data['ids'][part]) or not np.isfinite(saved['ratings']).all():
                        raise ValueError('Saved RD2 forecast batch differs')
                continue
            predicted=forecast(model,all_text,part,batch,guard.check)
            tmp=dest.with_suffix('.tmp')
            with tmp.open('wb') as stream:
                np.savez(stream,ids=data['ids'][part],ratings=predicted[:,classes:],F2=data['reserved'][part])
            os.replace(tmp,dest)
        del model
        elapsed=time.monotonic()-tic
        timings[fold]={'rows':len(chosen),'seconds':elapsed,'selectedSeed':best['seed'],
                       'secondsPer100':elapsed*100/len(chosen),'developmentMacroF1':best['developmentMacroF1']}
        core.write(d/'complete.json',timings[fold])
        if fold==0:
            core.write(directory/'fold-timing-pilot.json',{'fold':0,'seconds':elapsed,'projectedFiveFoldsSeconds':elapsed*5})
    return timings
