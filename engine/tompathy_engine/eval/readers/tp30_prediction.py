"""Durable ordered predictions for TP30; the outer runner owns admission and loading."""
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import numpy as np
import torch

from .tp30_fine import probabilities
from .tp30_training import file_pin


def predict_segment(model, texts, ids, specification, output, check, *, binding,
                    stop_after, resume_files=()):
    """Copy a verified saved prefix and infer only the unsaved suffix, at most 16 rows per batch.

    Each resume entry is an exact (path, SHA-256) pair from an independently verified
    exited source. A batch is self-contained and durable even if progress writing fails.
    No source directory or completed forecast file is overwritten.
    """
    required = {'payloadPin', 'sourceReceiptPin', 'protocolPin', 'modelCheckpointPin', 'implementationPin', 'target'}
    if (set(binding) != required or binding['target'] not in ('go', 'envent', 'ed') or
            any(not isinstance(binding[k], str) or len(binding[k]) != 64 or
                any(c not in '0123456789abcdef' for c in binding[k]) for k in required-{'target'})):
        raise ValueError('Exact input, model, implementation, protocol and target binding required')
    texts, ids = list(texts), np.asarray(ids, str)
    if (not texts or ids.shape != (len(texts),) or len(set(ids)) != len(ids) or
            type(stop_after) is not int or not 0 < stop_after <= len(texts) or
            (stop_after != len(texts) and stop_after % 500)):
        raise ValueError('Unique aligned rows and a fixed pilot boundary or final endpoint required')
    identity = {'binding': binding, 'texts': texts, 'ids': ids.tolist(),
                'specification': {k: v.tolist() if hasattr(v, 'tolist') else v
                                  for k, v in specification.items() if k != 'targets' and k != 'weights'}}
    contract = json.dumps({'schema': 'TP30-prediction-batch-1', 'binding': binding,
        'dataPin': hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False).encode()).hexdigest(),
        'torchVersion': str(torch.__version__), 'device': next(model.parameters()).device.type}, sort_keys=True)
    output = Path(output)
    if output.exists():
        raise ValueError('Each prediction segment requires a fresh output directory')
    verified, cursor = [], 0
    for source, pin in resume_files:
        check()
        source = Path(source)
        if file_pin(source) != pin:
            raise ValueError('Saved prediction bytes changed')
        end = min(cursor+16, cursor+500-cursor % 500, len(texts))
        with np.load(source, allow_pickle=False) as saved:
            if (str(saved['contract'].item()) != contract or int(saved['start'].item()) != cursor or
                    int(saved['end'].item()) != end or end > stop_after or
                    not np.array_equal(saved['ids'], ids[cursor:end]) or
                    saved['probabilities'].shape != (end-cursor, 9) or
                    not np.isfinite(saved['probabilities']).all() or
                    np.any((saved['probabilities'] < 0) | (saved['probabilities'] > 1))):
                raise ValueError('Saved prediction contract, order, shape or probabilities differ')
        verified.append((source, pin, cursor, end))
        cursor = end
    check()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for source, pin, start, end in verified:
        check()
        destination = output/f'batch-{start:08d}-{end:08d}.npz'
        shutil.copyfile(source, destination)
        if file_pin(destination) != pin:
            raise RuntimeError('Restored prediction copy differs')
        records.append({'file': destination.name, 'sha256': pin, 'start': start, 'end': end, 'reused': True})
    initial = cursor
    compute_seconds = 0.
    started = time.perf_counter()
    device = next(model.parameters()).device
    model.eval()
    with torch.inference_mode():
        while cursor < stop_after:
            check()
            end = min(cursor+16, cursor+500-cursor % 500, stop_after)
            if device.type == 'cuda':
                torch.cuda.synchronize(device)
            tick = time.perf_counter()
            predicted = probabilities(model(texts[cursor:end]), specification).cpu().numpy()
            if device.type == 'cuda':
                torch.cuda.synchronize(device)
            compute_seconds += time.perf_counter()-tick
            if predicted.shape != (end-cursor, 9) or not np.isfinite(predicted).all():
                raise ValueError('Invalid complete prediction batch')
            check()
            destination = output/f'batch-{cursor:08d}-{end:08d}.npz'
            temporary = destination.with_suffix('.tmp')
            with temporary.open('xb') as stream:
                np.savez(stream, contract=contract, start=cursor, end=end,
                         ids=ids[cursor:end], probabilities=predicted)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(destination)
            records.append({'file': destination.name, 'sha256': file_pin(destination),
                            'start': cursor, 'end': end, 'reused': False})
            cursor = end
            progress = {'durableRows': cursor, 'total': len(texts), 'newRows': cursor-initial,
                        'computeSeconds': compute_seconds, 'files': records}
            temporary = output/'progress.tmp'
            temporary.write_text(json.dumps(progress, allow_nan=False)+'\n')
            temporary.replace(output/'progress.json')
    check()
    return {'status': 'complete' if cursor == len(texts) else 'segment-complete',
            'durableRows': cursor, 'reusedRows': initial, 'newRows': cursor-initial,
            'computeSeconds': compute_seconds, 'segmentSeconds': time.perf_counter()-started,
            'files': records, 'productionAdmission': False}
