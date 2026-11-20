"""Make the fine-rung payload from the frozen study's original ordered arrays."""
import json
import os

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
        ids=ids.astype(str).to_numpy()
        if len(set(ids))!=len(texts):
            raise ValueError('Source identity collision')
        payload={'ids':ids,'texts':texts.to_numpy(str)}
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


if __name__=='__main__':
    for variable in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[variable]='2'
    print(prepare(ROOT/'.local/word-table/fine-input-a'))
