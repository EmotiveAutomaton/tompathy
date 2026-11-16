"""Unpacked research head reuse with exact completed-job binding."""
import json
from pathlib import Path

import numpy as np
from scipy.special import softmax

from ...packs.registry import sha256


def completed(job, card):
    job=Path(job)
    value=json.loads((job/'receipt.json').read_text(encoding='utf8'))
    audit=json.loads((job/'exit-verification.json').read_text(encoding='utf8'))
    if (value['card']!=card or value['status']!='complete' or not (job/'complete.json').exists()
            or not all(audit.get(k) for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent'))):
        raise ValueError('A completed, exited and released source card is required')
    return value


def load_head(job):
    """L3 development-selected seed is reused even if unpacked; gates stay failed."""
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    job=Path(job)
    receipt=completed(job,'TP10-L3')
    seed=receipt['selected_seed']
    root=job/f'seed-{seed}'
    row=receipt['rows'][str(seed)]
    for name,pin in row['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path)!=pin:
            raise ValueError('Source reader checkpoint binding differs')
    model=SentenceTransformer(str(root/'encoder'),device='cpu',local_files_only=True,trust_remote_code=False)
    model.max_seq_length=receipt['hyperparameters']['token_cap']
    model.eval()
    with np.load(root/'head.npz',allow_pickle=False) as data:
        heads={k:data[k].copy() for k in data.files}
    identity={'sourceReceiptPin':sha256(job/'receipt.json'),'selectedSeed':seed,
              'headPin':sha256(root/'head.npz'),'unpacked':True,'productionAdmission':False,
              'sourceGates':row['gates'],'token_cap':model.max_seq_length,'threads':2}

    def encode(texts,check):
        batches=[]
        with torch.inference_mode():
            for start in range(0,len(texts),16):
                check()
                batches.append(model.encode(texts[start:start+16],batch_size=16,
                                             normalize_embeddings=True,show_progress_bar=False))
        return np.concatenate(batches)

    def predict(texts,check):
        x=encode(texts,check)
        return softmax(x@heads['weights'].T+heads['bias'],axis=1), x@heads['ratings_weights'].T+heads['ratings_bias']
    return encode,predict,identity
