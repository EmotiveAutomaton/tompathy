"""Serial, offline small encoders with file-bound embedding caches."""
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np

from ...packs.registry import sha256


def load_encoder(directory, kind, *, cap=128):
    root = Path(directory)
    intake = json.loads((root/'intake.json').read_text(encoding='utf8'))
    for name, pin in intake['files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path) != pin:
            raise ValueError('Encoder intake hash mismatch')
    import torch
    torch.set_num_threads(2)
    if kind == 'potion':
        from model2vec import StaticModel
        model = StaticModel.from_pretrained(str(root))
        encode = lambda texts: model.encode(texts, max_length=cap, use_multiprocessing=False,
                                            show_progress_bar=False)
    elif kind == 'minilm':
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(str(root), local_files_only=True, trust_remote_code=False,
                                    device='cpu')
        model.max_seq_length = cap
        encode = lambda texts: model.encode(texts, batch_size=16, show_progress_bar=False,
                                            normalize_embeddings=True)
    else:
        raise ValueError('Unknown small encoder')
    identity = {**intake, 'token_cap': cap, 'device': 'cpu', 'threads': 2,
        'versions': {n: importlib.metadata.version(n) for n in
                     ('torch', 'transformers', 'model2vec', 'sentence-transformers', 'numpy')}}
    return encode, identity


def embeddings(texts, directory, kind, output, check):
    texts = list(texts)
    encode, identity = load_encoder(directory, kind)
    key = hashlib.sha256(json.dumps({'texts': texts, 'encoder': identity,
        'code': sha256(__file__)}, sort_keys=True).encode()).hexdigest()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    cache = output/(key+'.npz')
    if cache.exists():
        with np.load(cache, allow_pickle=False) as data:
            return data['embeddings'], identity, {'cache': True, 'seconds': None}
    start = time.perf_counter()
    vectors = []
    for i in range(0, len(texts), 64):
        check()
        vectors.append(encode(texts[i:i+64]))
    result = np.concatenate(vectors)
    elapsed = time.perf_counter()-start
    check()
    # Time the exact 150-sentence call separately from load and batching/checks.
    timing_texts = (texts*max(1, (150+len(texts)-1)//len(texts)))[:150]
    start = time.perf_counter()
    encode(timing_texts)
    seconds150 = time.perf_counter()-start
    np.savez(cache, embeddings=result)
    identity['embeddingCacheSha256'] = sha256(cache)
    return result, identity, {'cache': False, 'seconds': elapsed, 'sentences': len(texts),
        'sentences_per_second': len(texts)/elapsed, 'seconds150': seconds150,
        'excludes_loading': True, 'live_speed_target_met': seconds150 < 1}
