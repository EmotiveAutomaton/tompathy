"""Exact saved TP15 head/forecast continuation after a heartbeat write failure."""
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments


def prepare(source, output, root, models, check):
    from .rated import inputs
    source, output, models = Path(source), Path(output), Path(models)
    read = lambda p: json.loads(p.read_text(encoding='utf8'))
    proof_path = source.parent/(source.name+'-descriptive-preservation.json')
    proof = read(proof_path)
    prior, failure = read(source/'receipt.json'), read(source/'failed.json')
    exit_ = read(source/'exit-verification.json')
    if (not all(exit_.get(k) for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent'))
            or prior.get('card') != 'TP15' or prior.get('status') != 'running'
            or (source/'complete.json').exists() or failure.get('type') != 'PermissionError'
            or 'heartbeat.tmp' not in failure.get('reason','') or '[WinError 5]' not in failure['reason']
            or read(source/'phase.json').get('phase') not in {'fixed-full-data-descriptive-head','descriptive-group'}
            or set(prior['rows']) != {'constant','bow','potion','minilm','fine_tuned'}):
        raise ValueError('Only verified unfinished TP15 heartbeat failure can continue')
    for name, pin in proof['files'].items():
        check()
        p = (source/name).resolve()
        if not p.is_relative_to(source.resolve()) or sha256(p) != pin:
            raise ValueError('Preserved TP15 artifact changed')
    plan = read(source/'plan.json')
    for name,pin in plan['snapshotFiles'].items():
        if sha256(source/'code'/name) != pin:
            raise ValueError('Original TP15 snapshot changed')
    required = {'forecasts.npz','receipt.json','failed.json','exit-verification.json',
                'descriptive-head/head.npz','descriptive-head/best.safetensors',
                'descriptive-head/epochs.json'}
    if not required.issubset(proof['files']):
        raise ValueError('Incomplete preservation manifest')
    for name in ('regression.py','affect_data.py','encoders.py'):
        relative = 'tompathy_engine/eval/readers/'+name
        if sha256(Path(__file__).with_name(name)) != plan['snapshotFiles'][relative]:
            raise ValueError('TP15 data/training/encoding helper changed')
    for name in ('potion','minilm'):
        identity = prior['encoders'][name]
        for package,version in identity['versions'].items():
            if importlib.metadata.version(package) != version:
                raise ValueError('TP15 package versions changed')
        for file,pin in identity['files'].items():
            path=(models/name/file).resolve()
            if not path.is_relative_to((models/name).resolve()) or sha256(path) != pin:
                raise ValueError('Original pretrained model changed')
    texts,y,writers,_names,identity = inputs(root,'TP15')
    if identity != prior['source'] or len(texts) != prior['n'] or len(set(writers)) != prior['writers']:
        raise ValueError('TP15 source identity changed')
    with np.load(source/'forecasts.npz',allow_pickle=False) as saved:
        if (set(saved.files) != {*prior['rows'],'truth','writers'}
                or not np.array_equal(saved['truth'],y) or not np.array_equal(saved['writers'],writers)
                or any(saved[k].shape != y.shape or not np.isfinite(saved[k]).all() for k in prior['rows'])):
            raise ValueError('TP15 saved forecast census/order differs')
    head = source/'descriptive-head'
    epochs = read(head/'epochs.json')
    if epochs != [{'epoch':i,'development_rmse':None} for i in (1,2,3)]:
        raise ValueError('Descriptive training incomplete')
    with np.load(head/'head.npz',allow_pickle=False) as saved:
        mean,scale = y.mean(axis=0).astype(np.float32),y.std(axis=0).astype(np.float32)
        scale[scale<1e-9] = 1.
        if not np.array_equal(saved['mean'],mean) or not np.array_equal(saved['scale'],scale):
            raise ValueError('Descriptive target scaling changed')
    from sklearn.model_selection import GroupKFold
    folds=[]
    for fold,(train,test) in enumerate(GroupKFold(5).split(texts,groups=writers)):
        fold_epochs=read(source/f'fold-{fold}/epochs.json')
        if [e['epoch'] for e in fold_epochs] != [1,2,3]:
            raise ValueError('Missing completed fold epochs')
        unique=sorted(set(writers[train]),key=lambda w:hashlib.sha256(str(w).encode()).hexdigest())
        dev=set(unique[:max(1,len(unique)//10)])
        fitting=[i for i in train if writers[i] not in dev]
        folds.append({'fit':len(fitting),'development':len(train)-len(fitting),'test':len(test),
            'selected_epoch':min(fold_epochs,key=lambda e:e['development_rmse'])['epoch'],
            'epochs':fold_epochs,'token_cap':128})
    prior['fine_tuned_folds']=folds
    # Independent copies of the completed head and forecasts; original folds stay pinned.
    copied = {}
    for name,pin in proof['files'].items():
        if name == 'forecasts.npz' or name.startswith(('descriptive-head/','descriptive-batches/')):
            check()
            dest = output/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                raise ValueError('Fresh continuation artifacts required')
            shutil.copyfile(source/name,dest)
            if sha256(dest) != pin or sha256(source/name) != pin:
                raise ValueError('TP15 artifact copy mismatch')
            copied[name] = pin
    prior['continuation'] = {'kind':'saved-descriptive-head-heartbeat-repair',
        'sourceReceiptPin':sha256(source/'receipt.json'),'failurePin':sha256(source/'failed.json'),
        'exitVerificationPin':sha256(source/'exit-verification.json'),'preservationPin':sha256(proof_path),
        'forecastPin':sha256(output/'forecasts.npz'),'copiedArtifactCount':len(copied),
        'completedHeldOutInferenceRepeated':False,'completedTrainingRepeated':False,
        'unsavedDescriptiveScoringRestarted':True,
        'limitation':'Original in-memory group forecasts were not durable; their count is unknown.'}
    save_json(output/'continuation-artifacts.json',copied)
    group_proof_path=source.parent/(source.name+'-descriptive-inputs.json')
    group_proof=read(group_proof_path)
    prerequisite=Path(group_proof['prerequisite'])
    if sha256(prerequisite) != group_proof['prerequisitePin']:
        raise ValueError('Original group prerequisite audit changed')
    groups=read(prerequisite)['descriptiveGroups']
    prior['continuation']['groupInputProofPin']=sha256(group_proof_path)
    prior['continuation']['groupSourcePins']={k:v['source']['intakePin'] for k,v in groups.items()}
    return prior, {'fit':len(y),'development':0,'test':0,'selected_epoch':3,'epochs':epochs,'token_cap':128}


def load_predict(directory, check):
    """Restore the same Torch forward computation, not a NumPy approximation."""
    import torch
    from safetensors.torch import load_file
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    directory = Path(directory)
    encoder = SentenceTransformer(str(directory/'encoder'),device='cpu',local_files_only=True,trust_remote_code=False)
    encoder.max_seq_length = 128
    class Regressor(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.head = torch.nn.Linear(encoder.get_sentence_embedding_dimension(),2)
        def forward(self,items):
            vector = self.encoder(self.encoder.tokenize(items))['sentence_embedding']
            return self.head(torch.nn.functional.normalize(vector,p=2,dim=1))
    model = Regressor()
    state = load_file(str(directory/'best.safetensors'))
    # Exported encoder must be the exact selected training state.
    for name,tensor in encoder.state_dict().items():
        if not torch.equal(tensor,state['encoder.'+name]):
            raise ValueError('Exported descriptive encoder differs from saved state')
    model.load_state_dict(state,strict=True)
    model.eval()
    with np.load(directory/'head.npz',allow_pickle=False) as saved:
        if (not np.array_equal(saved['weights'],state['head.weight'].numpy())
                or not np.array_equal(saved['bias'],state['head.bias'].numpy())):
            raise ValueError('Exported descriptive head differs from saved state')
        mean,scale = saved['mean'].copy(),saved['scale'].copy()
    def predict(items):
        values=[]
        with torch.inference_mode():
            for start in range(0,len(items),16):
                check()
                values.append(model(items[start:start+16]).numpy())
        return np.concatenate(values)*scale+mean if values else np.empty((0,2))
    return predict


def batch_predictions(texts, identity, directory, predict, check):
    """Each batch becomes durable before another batch is evaluated."""
    directory = Path(directory)
    key = hashlib.sha256(json.dumps({'texts':list(texts),'identity':identity},sort_keys=True).encode()).hexdigest()
    values=[]
    for start in range(0,len(texts),16):
        check()
        path=directory/f'{start:08d}.json'
        if path.exists():
            value=json.loads(path.read_text(encoding='utf8'))
            if value.get('key') != key or value.get('start') != start:
                raise ValueError('Descriptive batch identity mismatch')
            array=np.asarray(value['values'],float)
        else:
            array=predict(texts[start:start+16])
            value={'key':key,'start':start,'values':array.tolist()}
        if array.shape != (min(16,len(texts)-start),2) or not np.isfinite(array).all():
            raise ValueError('Invalid descriptive batch')
        if not path.exists():
            save_json(path,value)
        values.append(array)
    return np.concatenate(values)


def run(root, models, output, check, source, ed_root, go_root):
    output=Path(output)
    receipt,meta=prepare(source,output,root,models,check)
    save_json(output/'receipt.json',receipt)
    save_json(output/'phase.json',{'phase':'fixed-full-data-descriptive-head'})
    predict=load_predict(output/'descriptive-head',check)
    ed,ed_pin=ed_situations(ed_root)
    go,go_y,go_labels,go_pin=go_comments(go_root)
    for name,pin in [('ed',ed_pin),('go',go_pin)]:
        if pin['intakePin'] != receipt['continuation']['groupSourcePins'][name]:
            raise ValueError('Descriptive source differs from original preflight')
    groups={}
    for name,frame,mask,pin in [('ed',ed,(ed.label=='caring').to_numpy(),ed_pin),
            ('go',go,go_y[:,go_labels.index('caring')].astype(bool),go_pin)]:
        eligible=np.ones(len(frame),bool) if name=='ed' else (frame.source_split!='unreleased').to_numpy()
        save_json(output/'phase.json',{'phase':'descriptive-group','group':name,'total':int(eligible.sum())})
        p=batch_predictions(frame.loc[eligible,'text'].tolist(),
            {'source':pin,'head':sha256(output/'descriptive-head/best.safetensors')},
            output/'descriptive-batches'/name,predict,check)
        m=mask[eligible]
        groups[name]={'caring_n':int(m.sum()),'other_n':int((~m).sum()),'targets':['concern','distress'],
            'caring_mean':p[m].mean(axis=0).tolist(),'other_mean':p[~m].mean(axis=0).tolist(),
            'difference':(p[m].mean(axis=0)-p[~m].mean(axis=0)).tolist(),'source':pin,'bar':None}
        receipt['second_check']={'head':meta,'groups':groups,
            'interpretation':'Analyst proposal; model group contrast is not an independent concern answer key'}
        save_json(output/'receipt.json',receipt)
    receipt['status']='complete'
    save_json(output/'receipt.json',receipt)
