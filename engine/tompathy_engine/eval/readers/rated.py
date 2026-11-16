"""TP15 concern/distress and TP16 worry: strict writer-held-out target-task fits."""
import gc
import hashlib
import importlib.metadata
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments, verify
from .encoders import embeddings
from .regression import fit_encoder, partial_correlation, scores


def ridge_forecast(left, targets, right):
    """Keep sklearn's scalar-target convenience from dropping our target axis."""
    if targets.ndim != 2:
        raise ValueError('Regression targets must have an explicit target axis')
    prediction = Ridge(alpha=3).fit(left, targets).predict(right)
    if prediction.ndim == 1 and targets.shape[1] == 1:
        prediction = prediction[:, None]
    if prediction.shape != (right.shape[0], targets.shape[1]):
        raise ValueError('Regression prediction shape differs from its targets')
    return prediction


def verified_host_restart(source):
    """Require host-visible recovery evidence and unchanged saved artifacts."""
    source = Path(source)
    read = lambda name: json.loads((source/name).read_text(encoding='utf8'))
    audit, owner = read('host-restart-recovery.json'), read('owner.json')
    if (audit.get('nativeExited') is not True or audit.get('ownedPythonLaunchers') != []
            or audit.get('foreignChanges') is not False or audit.get('ownerNative') != owner['native']
            or datetime.fromisoformat(audit['hostBootAt']) <= datetime.fromisoformat(owner['at'])
            or datetime.fromisoformat(audit['hostBootAt']) <= datetime.fromisoformat(audit['lastHeartbeat']['at'])):
        raise ValueError('Unverified host restart')
    original = audit['preservedFiles']
    audit['preservedFiles'] = {Path(name.replace('\\', '/')).as_posix():pin for name,pin in original.items()}
    if len(audit['preservedFiles']) != len(original):
        raise ValueError('Duplicate preserved artifact paths')
    for name, pin in audit['preservedFiles'].items():
        path = (source/name).resolve()
        if not path.is_relative_to(source.resolve()) or sha256(path) != pin:
            raise ValueError('Preserved restart artifact changed')
    return audit


def copy_initial_embeddings(source, output, texts, models, receipt):
    """Reuse exact encoding caches after the verified shape failure or host restart."""
    source, output, models = Path(source), Path(output), Path(models)
    read = lambda name: json.loads((source/name).read_text(encoding='utf8'))
    verified, failed, prior = read('exit-verification.json'), read('failed.json'), read('receipt.json')
    if not all(verified.get(k) for k in ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent')):
        raise ValueError('Cache continuation requires verified native exit and releases')
    restart = failed.get('type') == 'HostRestart'
    shape_failure = (failed.get('type') == 'ValueError' and failed.get('reason', '').startswith('shape mismatch:')
        and read('phase.json') == {'phase': 'writer-fold', 'fold': 0}
        and not list(source.glob('*forecasts.npz')) and not list(source.glob('fold-*')))
    if (not (restart or shape_failure) or failed.get('completed') != []
            or prior.get('status') != 'running' or prior.get('rows') != {} or (source/'complete.json').exists()):
        raise ValueError('Only the initial regression shape failure may reuse these caches')
    if restart:
        verified_host_restart(source)
    for key in ('card', 'source', 'n', 'writers', 'protocol'):
        if prior.get(key) != receipt.get(key):
            raise ValueError('Rated continuation source/protocol differs')
    relative = 'tompathy_engine/eval/readers/encoders.py'
    encoder_code = Path(__file__).with_name('encoders.py')
    code_pin = sha256(encoder_code)
    if read('plan.json')['snapshotFiles'].get(relative) != code_pin or sha256(source/'code'/relative) != code_pin:
        raise ValueError('Encoding code changed since the preserved cache')
    copied = {}
    for name in ('potion', 'minilm'):
        root = models/name
        intake = json.loads((root/'intake.json').read_text(encoding='utf8'))
        for file, pin in intake['files'].items():
            path = (root/file).resolve()
            if not path.is_relative_to(root.resolve()) or sha256(path) != pin:
                raise ValueError('Encoder intake hash mismatch')
        # Match the unchanged encoders.py identity before its cache is written.
        identity = {**intake, 'token_cap': 128, 'device': 'cpu', 'threads': 2,
            'versions': {n: importlib.metadata.version(n) for n in
                ('torch', 'transformers', 'model2vec', 'sentence-transformers', 'numpy')}}
        key = hashlib.sha256(json.dumps({'texts': list(texts), 'encoder': identity,
            'code': code_pin}, sort_keys=True).encode()).hexdigest()
        cache = source/'embeddings'/name/(key+'.npz')
        with np.load(cache, allow_pickle=False) as saved:
            matrix = saved['embeddings']
            if (saved.files != ['embeddings'] or matrix.ndim != 2 or matrix.shape[0] != len(texts)
                    or matrix.shape[1] < 1 or not np.isfinite(matrix).all()):
                raise ValueError('Invalid complete encoding cache')
        destination = output/'embeddings'/name/cache.name
        destination.parent.mkdir(parents=True, exist_ok=False)
        pin = sha256(cache)
        shutil.copyfile(cache, destination)
        if sha256(destination) != pin:
            raise ValueError('Copied encoding cache hash mismatch')
        copied[name] = {'key': key, 'sha256': pin, 'shape': list(matrix.shape)}
    return {'kind': 'host-restart-continuation' if restart else 'initial-regression-shape-repair', 'sourceReceiptPin': sha256(source/'receipt.json'),
        'failurePin': sha256(source/'failed.json'), 'exitVerificationPin': sha256(source/'exit-verification.json'),
        'encoderCodePin': code_pin, 'caches': copied, 'completedInferenceRepeated': False}


def restore_completed_folds(source, output, texts, y, writers, predictions):
    """Carry complete fold forecasts/models; discard no saved or partial source work."""
    source, output = Path(source), Path(output)
    audit = verified_host_restart(source)
    relative = 'tompathy_engine/eval/readers/regression.py'
    if sha256(source/'code'/relative) != sha256(Path(__file__).with_name('regression.py')):
        raise ValueError('Fold training/scoring code changed')
    partial = source/'partial-forecasts.npz'
    with np.load(partial, allow_pickle=False) as data:
        count = data['completed_folds']
        if count.shape != (1,) or not np.issubdtype(count.dtype, np.integer) or not 1 <= count[0] < 5:
            raise ValueError('Invalid completed fold count')
        count = int(count[0])
        if set(data.files) != {*predictions, 'completed_folds'}:
            raise ValueError('Fold checkpoint rows differ')
        arrays = {name: data[name] for name in predictions}
    if audit['phase'] != {'phase':'writer-fold','fold':count}:
        raise ValueError('Restart phase disagrees with durable fold boundary')
    folds = list(GroupKFold(5).split(texts, groups=writers))
    mask = np.zeros(len(y), dtype=bool)
    for _, test in folds[:count]:
        mask[test] = True
    for name, array in arrays.items():
        if array.shape != y.shape or not np.isfinite(array).all() or np.any(array[~mask] != 0):
            raise ValueError('Invalid or unmarked partial fold predictions')
        predictions[name][mask] = array[mask]
    metadata, copied = [], {}
    for fold, (train, test) in enumerate(folds[:count]):
        directory = source/f'fold-{fold}'
        epochs = json.loads((directory/'epochs.json').read_text(encoding='utf8'))
        if ([r['epoch'] for r in epochs] != [1,2,3]
                or not all(r['development_rmse'] is not None and np.isfinite(r['development_rmse']) for r in epochs)):
            raise ValueError('Completed fold lacks all development epochs')
        unique = sorted(set(writers[train]), key=lambda w: hashlib.sha256(str(w).encode()).hexdigest())
        dev_writers = set(unique[:max(1,len(unique)//10)])
        fit = np.array([i for i in train if writers[i] not in dev_writers])
        mean = y[fit].mean(axis=0).astype(np.float32)
        scale = y[fit].std(axis=0).astype(np.float32)
        scale[scale<1e-9] = 1.
        with np.load(directory/'head.npz', allow_pickle=False) as head:
            if not np.array_equal(head['mean'], mean) or not np.array_equal(head['scale'], scale):
                raise ValueError('Completed fold target scaling differs')
        if not (directory/'encoder/model.safetensors').is_file() or not (directory/'best.safetensors').is_file():
            raise ValueError('Completed fold model artifacts missing')
        destination = output/directory.name
        shutil.copytree(directory, destination)
        for path in directory.rglob('*'):
            if path.is_file():
                relative_path = path.relative_to(source).as_posix()
                pin = sha256(path)
                if audit['preservedFiles'].get(relative_path) != pin or sha256(output/relative_path) != pin:
                    raise ValueError('Completed fold copy mismatch')
                copied[relative_path] = pin
        metadata.append({'fit':len(fit),'development':len(train)-len(fit),'test':len(test),
            'selected_epoch':min(epochs,key=lambda r:r['development_rmse'])['epoch'], 'epochs':epochs,'token_cap':128})
    np.savez(output/'partial-forecasts.npz', **predictions, completed_folds=np.array([count]))
    return count, metadata, {'completedFoldsReused':count,'partialForecastsPin':sha256(partial),
        'hostRecoveryPin':sha256(source/'host-restart-recovery.json'),'foldFiles':copied,
        'unfinishedFoldRestarted':count}


def plans(text):
    import re
    sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+',text) if x.strip()]
    pattern=re.compile(r"\b(?:I|we)\s+(?:(?:am|are)\s+going to|(?:will|plan to|decided to|intend to|have arranged))\b",re.IGNORECASE)
    return sum(bool(pattern.search(s)) for s in sentences)/len(sentences) if sentences else 0.


def inputs(root,card):
    root=Path(root)
    identity=verify(root)
    if card=='TP15':
        frame=pd.read_csv(root/'data/responses/data/messages.csv',usecols=['message_id','response_id','essay','empathy','distress'])
        if len(frame)!=1860 or frame.message_id.duplicated().any() or frame.response_id.isna().any():
            raise ValueError('Empathy source census or writer key differs')
        return frame.essay.tolist(),frame[['empathy','distress']].to_numpy(float),frame.response_id.to_numpy(str),['concern','distress'],identity
    frame=pd.read_csv(root/'data_phase_1/files/meta/rwwd_full.csv',usecols=['worry','text_long'])
    if len(frame)!=2500 or frame.isna().any().any():
        raise ValueError('Worry source census or targets differ')
    return frame.text_long.tolist(),frame[['worry']].to_numpy(float),np.arange(len(frame)).astype(str),['worry'],identity


def run(card,root,models,output,check,*,ed_root=None,go_root=None,counting=None,reader_job=None,resume=None):
    output,models=Path(output),Path(models)
    texts,y,writers,names,identity=inputs(root,card)
    receipt={'card':card,'status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Writer self-report prediction; text-level benchmark, not maker estimates',
        'source':identity,'n':len(texts),'writers':len(set(writers)),'rows':{},
        'protocol':{'folds':'GroupKFold(5), writers disjoint; each source response_id is one empathy writer',
            'head':'Ridge alpha=3; BOW word 1-2 grams, min_df=2, sublinear TF',
            'fine_tuned':'Original pretrained MiniLM, fresh regression head; 3 epochs, writer dev tenth per fold, dev RMSE selection',
            'training':'batch16; encoderLR2e-5, headLR1e-3; AdamW .01; clip1; seed23; fold-local target scaling; cap128',
            'long_text_limit':'First 128 model tokens for embedding/regression rows; BOW uses whole text'},
        'external_references':{'human':'No human-reader score supplied for these sets',
            'primary':'.40 correlation on both targets' if card=='TP15' else '.16 variance explained',
            'stretch':'.54 correlation on both targets' if card=='TP15' else '.25 variance explained'}}
    save=lambda:save_json(output/'receipt.json',receipt)
    if resume is not None:
        receipt['continuation'] = copy_initial_embeddings(resume, output, texts, models, receipt)
    save()
    encoded={}
    for name in ('potion','minilm'):
        encoded[name],pin,_=embeddings(texts,models/name,name,output/'embeddings'/name,check)
        receipt.setdefault('encoders',{})[name]=pin
        save()
    predictions={name:np.zeros_like(y) for name in ('constant','bow','potion','minilm','fine_tuned')}
    fine_folds=[]
    completed_folds=0
    if resume is not None and receipt['continuation']['kind']=='host-restart-continuation':
        completed_folds,fine_folds,proof=restore_completed_folds(resume,output,texts,y,writers,predictions)
        receipt['continuation'].update(proof)
        save()
    for fold,(train,test) in enumerate(GroupKFold(5).split(texts,groups=writers)):
        if fold < completed_folds:
            continue
        check()
        save_json(output/'phase.json',{'phase':'writer-fold','fold':fold})
        if set(writers[train])&set(writers[test]):
            raise ValueError('Writer leakage')
        predictions['constant'][test]=y[train].mean(axis=0)
        vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
        inputs_={'bow':(vectorizer.fit_transform([texts[i] for i in train]),vectorizer.transform([texts[i] for i in test]))}
        inputs_.update({name:(x[train],x[test]) for name,x in encoded.items()})
        for name,(left,right) in inputs_.items():
            check()
            predictions[name][test]=ridge_forecast(left,y[train],right)
        fitted,meta,predict=fit_encoder(models/'minilm',texts,y,train,test,writers,output/f'fold-{fold}',check)
        predictions['fine_tuned'][test]=fitted
        fine_folds.append(meta)
        del predict
        gc.collect()
        np.savez(output/'partial-forecasts.npz',**predictions,completed_folds=np.array([fold+1]))
    for name,prediction in predictions.items():
        check()
        row=scores(y,prediction,writers,names)
        key='correlation' if card=='TP15' else 'r2'
        primary=.4 if card=='TP15' else .16
        stretch=.54 if card=='TP15' else .25
        row['primary']=all(r[key] is not None and r[key]>=primary for r in row['targets'].values())
        row['stretch']=all(r[key] is not None and r[key]>=stretch for r in row['targets'].values())
        if card=='TP15':
            row['concern_given_distress']=partial_correlation(prediction[:,0],y[:,0],y[:,1])
        receipt['rows'][name]=row
        save()
    receipt['fine_tuned_folds']=fine_folds
    np.savez(output/'forecasts.npz',**predictions,truth=y,writers=writers)
    if card=='TP15':
        check()
        save_json(output/'phase.json',{'phase':'fixed-full-data-descriptive-head'})
        # This fresh full-data fit serves only the separately predeclared group
        # comparison. It does not replace held-out forecasts or their gates.
        _,meta,predict=fit_encoder(models/'minilm',texts,y,np.arange(len(y)),np.array([],int),writers,output/'descriptive-head',check,final=True)
        ed,ed_pin=ed_situations(ed_root)
        go,go_y,go_labels,go_pin=go_comments(go_root)
        groups={}
        for name,frame,mask,pin in [('ed',ed,(ed.label=='caring').to_numpy(),ed_pin),
            ('go',go,go_y[:,go_labels.index('caring')].astype(bool),go_pin)]:
            eligible=np.ones(len(frame),bool) if name=='ed' else (frame.source_split!='unreleased').to_numpy()
            p=predict(frame.loc[eligible,'text'].tolist())
            m=mask[eligible]
            groups[name]={'caring_n':int(m.sum()),'other_n':int((~m).sum()),'targets':names,
                'caring_mean':p[m].mean(axis=0).tolist(),'other_mean':p[~m].mean(axis=0).tolist(),
                'difference':(p[m].mean(axis=0)-p[~m].mean(axis=0)).tolist(),'source':pin,'bar':None}
        receipt['second_check']={'head':meta,'groups':groups,'interpretation':'Analyst proposal; model group contrast is not an independent concern answer key'}
        del predict
    else:
        from .longtext import worry_checks
        receipt['long_text_channels'],receipt['plans']=worry_checks(root,reader_job,counting,output,check,plans)
    receipt['status']='complete'
    save()
