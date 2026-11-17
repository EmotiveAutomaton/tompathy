"""Exact frozen-vector reuse; source bytes, ordered texts and execution are bound."""
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from . import encoders
from .artifacts import model_identity
from .envent import load


def vectors(texts, models, output, check, *, shared=None, source=None, corpus=None):
    texts, models, output = list(texts), Path(models), Path(output)
    identity = {**model_identity(models/'minilm', check), 'token_cap': 128,
                'device': 'cpu', 'threads': 2,
                'versions': {n: importlib.metadata.version(n) for n in
                             ('torch', 'transformers', 'model2vec', 'sentence-transformers', 'numpy')}}
    protocol = {'encoder': identity, 'code': sha256(encoders.__file__)}
    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    key = digest({'texts': texts, **protocol})
    output.mkdir(parents=True, exist_ok=True)
    memory = {}
    if source is not None:
        source = Path(source)
        receipt = json.loads((source/'receipt.json').read_text(encoding='utf8'))
        audit = json.loads((source/'exit-verification.json').read_text(encoding='utf8'))
        if (receipt['card'] != 'TP10' or receipt['status'] != 'L0-L2 complete; L3 and final pack gates pending'
                or not (source/'complete.json').exists() or not all(audit.get(k) for k in
                    ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent'))):
            raise ValueError('Original frozen ladder must be completed and exited')
        previous = receipt['rows']['minilm']['encoder'].copy()
        cache_pin = previous.pop('embeddingCacheSha256')
        data = load(corpus)
        if previous != identity or receipt['scope']['files'] != data.pins:
            raise ValueError('Original frozen-vector model/packages/corpus changed')
        if sha256(source/'code/tompathy_engine/eval/readers/encoders.py') != protocol['code']:
            raise ValueError('Original frozen-vector execution code changed')
        original_texts = data.reports.hidden_emo_text.tolist()
        original_key = digest({'texts': original_texts, **protocol})
        path = source/'embeddings/minilm'/(original_key+'.npz')
        if sha256(path) != cache_pin:
            raise ValueError('Original frozen-vector bytes changed')
        with np.load(path, allow_pickle=False) as d:
            rows = d['embeddings']
        if rows.shape != (len(original_texts), 384) or not np.isfinite(rows).all():
            raise ValueError('Invalid original frozen vectors')
        memory = dict(zip(original_texts, rows))
    shared = Path(shared) if shared is not None else None
    if shared is not None:
        shared.mkdir(parents=True, exist_ok=True)
    encode = None
    result = []
    for start in range(0, len(texts), 64):
        check()
        batch = texts[start:start+64]
        destination = output/f'{start:07d}.npz'
        if destination.exists():
            with np.load(destination, allow_pickle=False) as d:
                if str(d['key']) != key:
                    raise ValueError('Embedding source changed')
                values = d['values']
        else:
            values = np.empty((len(batch), 384), np.float32)
            missing = []
            for i, text in enumerate(batch):
                cache_key = digest([protocol, text])
                path = shared/(cache_key+'.npz') if shared is not None else None
                if text in memory:
                    values[i] = memory[text]
                elif path is not None and path.exists():
                    with np.load(path, allow_pickle=False) as d:
                        if str(d['key']) != cache_key:
                            raise ValueError('Shared vector identity changed')
                        values[i] = d['value']
                else:
                    missing.append(i)
            if missing:
                if encode is None:
                    encode, loaded = encoders.load_encoder(models/'minilm', 'minilm', cap=128)
                    if loaded != identity:
                        raise ValueError('Loaded encoder identity differs')
                values[missing] = encode([batch[i] for i in missing])
            if not np.isfinite(values).all():
                raise ValueError('Invalid frozen vectors')
            for text, value in zip(batch, values):
                memory[text] = value
                if shared is not None:
                    cache_key = digest([protocol, text])
                    path = shared/(cache_key+'.npz')
                    if not path.exists():
                        np.savez(path, key=cache_key, value=value)
            np.savez(destination, key=key, values=values)
        if values.shape != (len(batch), 384) or not np.isfinite(values).all():
            raise ValueError('Invalid durable vectors')
        result.append(values)
    return np.concatenate(result), identity
