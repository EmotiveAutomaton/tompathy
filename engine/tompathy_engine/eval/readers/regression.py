"""Fixed grouped regression and uncertainty for writer-rated reader cards."""
import hashlib
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import r2_score

from ..back_half.reporting import save_json


def correlation(x,y):
    x,y=np.asarray(x,float),np.asarray(y,float)
    if len(x)<3 or np.std(x)==0 or np.std(y)==0:
        return None
    return float(np.corrcoef(x,y)[0,1])


def partial_correlation(x,y,controls):
    controls=np.asarray(controls,float)
    if controls.ndim==1:
        controls=controls[:,None]
    matrix=np.c_[np.ones(len(x)),controls]
    residuals=[np.asarray(v)-matrix@np.linalg.lstsq(matrix,v,rcond=None)[0] for v in (x,y)]
    return correlation(*residuals)


def scores(y,prediction,writers,names,*,bootstrap=1000):
    y,prediction=np.asarray(y,float),np.asarray(prediction,float)
    if y.shape!=prediction.shape or y.ndim!=2 or y.shape[1]!=len(names):
        raise ValueError('Regression outcome dimensions differ')
    if not np.isfinite(y).all() or not np.isfinite(prediction).all():
        raise ValueError('Nonfinite regression outcome')
    writers=np.asarray(writers)
    indices=[np.flatnonzero(writers==w) for w in np.unique(writers)]
    rng=np.random.default_rng(20261115)
    draws={name:[] for name in names}
    variances={name:[] for name in names}
    errors={name:[] for name in names}
    for _ in range(bootstrap):
        ix=np.concatenate([indices[j] for j in rng.integers(len(indices),size=len(indices))])
        for j,name in enumerate(names):
            if np.var(y[ix,j])>0:
                variances[name].append(float(r2_score(y[ix,j],prediction[ix,j])))
            errors[name].append(float(np.sqrt(np.mean((y[ix,j]-prediction[ix,j])**2))))
            value=correlation(y[ix,j],prediction[ix,j])
            if value is not None:
                draws[name].append(value)
    return {'n':len(y),'writers':len(indices),
        'interval_method':f'{bootstrap} whole-writer resamples of fixed held-out predictions',
        'targets':{name:{'correlation':correlation(y[:,j],prediction[:,j]),
            'r2':float(r2_score(y[:,j],prediction[:,j])),
            'rmse':float(np.sqrt(np.mean((y[:,j]-prediction[:,j])**2))),
            'r2_interval':np.quantile(variances[name],[.025,.975]).tolist() if variances[name] else None,
            'rmse_interval':np.quantile(errors[name],[.025,.975]).tolist(),
            'undefined_correlation_resamples':bootstrap-len(draws[name]),
            'undefined_r2_resamples':bootstrap-len(variances[name]),
            'correlation_interval':np.quantile(draws[name],[.025,.975]).tolist() if draws[name] else None}
            for j,name in enumerate(names)}}


def fit_encoder(directory,texts,y,train,test,writers,output,check,*,final=False):
    """A fresh target-task regression head and encoder; dev writers select epoch.

    The held-out test is never used for scaling, model fitting or epoch choice.
    Final descriptive-model fitting uses three fixed epochs on all examples.
    """
    import torch
    from safetensors.torch import load_file, save_file
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    torch.manual_seed(23)
    torch.use_deterministic_algorithms(True)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    train,test=np.asarray(train),np.asarray(test)
    if set(writers[train]) & set(writers[test]):
        raise ValueError('Fine-tuned regression writer leakage')
    unique=sorted(set(writers[train]),key=lambda w:hashlib.sha256(str(w).encode()).hexdigest())
    dev_writers=set(unique[:max(1,len(unique)//10)]) if not final else set()
    dev=np.array([i for i in train if writers[i] in dev_writers],dtype=int)
    fit=np.array([i for i in train if writers[i] not in dev_writers],dtype=int)
    mean=y[fit].mean(axis=0).astype(np.float32)
    scale=y[fit].std(axis=0).astype(np.float32)
    scale[scale<1e-9]=1.
    target=((y-mean)/scale).astype(np.float32)
    encoder=SentenceTransformer(str(directory),device='cpu',local_files_only=True,trust_remote_code=False)
    encoder.max_seq_length=128

    class Regressor(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder=encoder
            self.head=torch.nn.Linear(encoder.get_sentence_embedding_dimension(),y.shape[1])

        def forward(self,items):
            vector=self.encoder(self.encoder.tokenize(items))['sentence_embedding']
            return self.head(torch.nn.functional.normalize(vector,p=2,dim=1))

    model=Regressor()
    optimizer=torch.optim.AdamW([{'params':model.encoder.parameters(),'lr':2e-5},
                                {'params':model.head.parameters(),'lr':1e-3}],weight_decay=.01)

    def predict(items):
        model.eval()
        values=[]
        with torch.inference_mode():
            for start in range(0,len(items),16):
                check()
                values.append(model(items[start:start+16]).numpy())
        return np.concatenate(values)*scale+mean if values else np.empty((0,y.shape[1]))

    rng=np.random.default_rng(23)
    best=float('inf')
    epochs=[]
    started=time.perf_counter()
    for epoch in range(3):
        model.train()
        order=rng.permutation(fit)
        for start in range(0,len(order),16):
            check()
            ix=order[start:start+16]
            optimizer.zero_grad(set_to_none=True)
            loss=torch.nn.functional.mse_loss(model([texts[i] for i in ix]),torch.from_numpy(target[ix]))
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite regression loss')
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step()
            save_json(output/'progress.json',{'epoch':epoch+1,'examples':min(start+16,len(order)),
                'total':len(order),'elapsed_seconds':time.perf_counter()-started})
        rmse=float(np.sqrt(np.mean((predict([texts[i] for i in dev])-y[dev])**2))) if len(dev) else None
        epochs.append({'epoch':epoch+1,'development_rmse':rmse})
        if final or rmse<best:
            best=rmse if rmse is not None else best
            save_file({n:t.detach().contiguous() for n,t in model.state_dict().items()},str(output/'best.safetensors'))
            chosen=epoch+1
        save_json(output/'epochs.json',epochs)
    model.load_state_dict(load_file(str(output/'best.safetensors')))
    prediction=predict([texts[i] for i in test])
    encoder.save(str(output/'encoder'),safe_serialization=True,create_model_card=False)
    np.savez(output/'head.npz',weights=model.head.weight.detach().numpy(),bias=model.head.bias.detach().numpy(),mean=mean,scale=scale)
    return prediction,{'fit':len(fit),'development':len(dev),'test':len(test),'selected_epoch':chosen,
                       'epochs':epochs,'token_cap':128},predict
