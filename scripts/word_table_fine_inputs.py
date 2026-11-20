"""Make the fine-rung payload from the frozen study's original ordered arrays."""
import hashlib
import json
import os
from pathlib import Path

from word_table_inputs import ROOT, pin, write


def prepare(destination):
    import numpy as np
    from tompathy_engine.eval.readers.affect_data import ed_situations, go_comments
    from tompathy_engine.eval.readers.envent import load
    source=ROOT/'.local/nine-channel/tp30-frozen-a'
    intake=ROOT/'.local/readers/data'
    public=json.loads((ROOT/'engine/validation/readers-profile-frozen-2026-11.json').read_bytes())
    receipt=json.loads((source/'receipt.json').read_bytes())
    inventory=source/'artifact-manifest.json'
    if pin(source/'receipt.json')!=public['sourceReceiptPin'] or pin(inventory)!=receipt['artifactsPin']:
        raise ValueError('Original frozen source receipt or array inventory changed')
    files=json.loads(inventory.read_bytes())['files']
    go,_,_,gp=go_comments(intake/'go-emotions')
    ed,ep=ed_situations(intake/'empathetic-dialogues')
    ev=load(intake/'crowd-enVent2023')
    if {'ed':ep,'go':gp,'envent':ev.summary()}!=receipt['sources']:
        raise ValueError('Original open-source intake changed')
    destination.mkdir(parents=True,exist_ok=False)
    data={}
    for name,ids,texts in [('ed',ed.id,ed.text),('envent',ev.reports.text_id,ev.reports.hidden_emo_text),
                           ('go',go.id,go.text)]:
        ids=np.asarray(ids.astype(str).tolist(),dtype=str)
        if len(set(ids))!=len(texts):
            raise ValueError('Source identity collision')
        payload={'ids':ids,'texts':np.asarray(texts.tolist(),dtype=str)}
        mask=np.ones(len(ids),bool)
        if name!='ed':
            key=name+'-targets.npz'
            if pin(source/key)!=files[key]:
                raise ValueError('Original target arrays changed')
            with np.load(source/key,allow_pickle=False) as z:
                if not np.array_equal(ids,z['ids']):
                    raise ValueError('Original target order differs')
                for k in ('train','shares','unassigned','test','disagreement','pair_support'):
                    if k in z:
                        payload[k]=z[k]
                if name=='go':
                    mask=payload['test']
        key=name+'-profile-forecasts.npz'
        if pin(source/key)!=files[key]:
            raise ValueError('Original evaluation truth changed')
        with np.load(source/key,allow_pickle=False) as z:
            if not np.array_equal(ids[mask],z['ids']):
                raise ValueError('Held-out forecast identity differs')
            payload['truth']=z['truth']
        dest=destination/('G2-'+name+'.npz')
        np.savez_compressed(dest,**payload)
        data[dest.name]=pin(dest)
    encoder=receipt['vectors']['encoder']
    manifest={'sourceReceiptPin':public['sourceReceiptPin'],'frozenArtifactManifestPin':pin(inventory),
              'protocolPin':pin(ROOT/'docs/TP30_FINE_PROTOCOL_2026-11-20.md'),'files':data,
              'initialMiniLM':{k:encoder[k] for k in ('id','revision','files','license_as_read')},
              'rungs':[{'id':encoder['id'],'seeds':[23]},
                       {'id':'sentence-transformers/all-mpnet-base-v2','seeds':[23,47,71]},
                       {'id':'answerdotai/ModernBERT-large','seeds':[23,47,71]}],
              'scope':'Public rater shares. ED research only. Original writer identifiers stay local.'}
    write(destination/'G2-contract.json',manifest)
    return data


def transfer(source,release,dest):
    import numpy as np
    cfg=json.loads((source/'G2-contract.json').read_bytes())
    aliases=json.loads((release/'local-original-id-map.json').read_bytes())
    norm=lambda text:' '.join(text.casefold().split())
    protected={norm(r['text']) for r in json.loads((release/'F2-texts.json').read_bytes())}
    if len(aliases)!=350 or len(set(aliases.values()))!=350:
        raise ValueError('Expected the approved 350 original-to-opaque local links')
    dest.mkdir(exist_ok=False)
    for name,h in list(cfg['files'].items()):
        if pin(source/name)!=h:
            raise ValueError('Original fine-rung source payload changed')
        with np.load(source/name,allow_pickle=False) as a:
            keep={'texts','ids','train','test','shares','unassigned'}
            fields={k:a[k] for k in a.files if k in keep}
        if name=='G2-envent.npz':
            ids=fields['ids'].tolist();text=fields['texts'].tolist()
            mask=np.array([k in aliases for k in ids])
            if mask.sum()!=350:
                raise ValueError('F2 source order does not match')
            fields['reserved']=mask
            fields['ids']=np.asarray([aliases.get(k,k) for k in ids])
            duplicate_mask=np.asarray([not hide and norm(v) in protected for hide,v in zip(mask,text)])
            cfg['earlierTextPins']={ids[i]:hashlib.sha256(text[i].encode()).hexdigest() for i in np.flatnonzero(duplicate_mask)}
            fields['texts']=np.asarray(['' if hide else v for hide,v in zip(mask|duplicate_mask,text)])
        if any(s and norm(s) in protected for s in fields['texts']):
            raise ValueError('Transfer still includes a reserved text or normalized duplicate')
        np.savez_compressed(dest/name,**fields)
        cfg['files'][name]=pin(dest/name)
    for rung in cfg['rungs'][1:]:
        rung['seeds']=[23,47,71]
    cfg['releasedF2Pin']=pin(release/'F2-texts.json')
    write(dest/'G2-contract.json',cfg)
    write(dest/'G2.json',[{'id':m['id'],'seeds':m['seeds']} for m in cfg['rungs']])
    names=[*cfg['files'],'G2-contract.json','G2.json']
    modules=['scripts/word_table_fine_runtime.py',*['engine/tompathy_engine/eval/readers/'+k+'.py'
             for k in ('tp30_encoder','tp30_fine','tp30_training','tp30_prediction')]]
    spec={'modules':modules,'jobs':{'G2':{'rows':3,'files':{n:str(dest/n) for n in names}}},
          'pins':{n:pin(dest/n) for n in names},'provenance':{'originalSourceReceiptPin':cfg['sourceReceiptPin'],
          'protocolPin':cfg['protocolPin'],'reservedTextsInTransfer':0,'writerRatingsInTransfer':0,
          'edLicense':'CC BY-NC 4.0; research only'}}
    write(dest/'specification.json',spec)
    return spec['provenance']


if __name__=='__main__':
    for variable in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[variable]='2'
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transfer',action='store_true')
    parser.add_argument('--source',default='fine-input-b')
    parser.add_argument('--output')
    args=parser.parse_args()
    base=ROOT/'.local/word-table'
    target=base/(args.output or ('fine-transfer-c' if args.transfer else args.source))
    if target.resolve().parent!=base.resolve() or (base/args.source).resolve().parent!=base.resolve():
        parser.error('Use fresh direct children of the private word-table directory')
    print(transfer(base/args.source,base/'F2-release-local',target) if args.transfer else prepare(Path(target)))
