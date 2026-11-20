"""Durable TP30 fine training segments; GPU admission belongs to the outer runner."""
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import torch

from .tp30_fine import weighted_loss


def file_pin(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def cpu_tree(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [cpu_tree(item) for item in value]
    if isinstance(value, tuple):
        return tuple(cpu_tree(item) for item in value)
    return value


def atomic_save(path, state):
    """Replace only this new segment's mutable checkpoint, after a complete write."""
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        torch.save(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    return file_pin(path)


def contract(texts, specification, binding, model, optimizer):
    required = {'payloadPin', 'sourceReceiptPin', 'protocolPin', 'initialEncoderPin', 'implementationPin', 'component'}
    if (set(binding) != required or binding['component'] not in
            {'go_only-profile', 'go_only-control', 'go_plus_envent-profile', 'go_plus_envent-control'} or
            any(not isinstance(binding[k], str) or len(binding[k]) != 64 or
                any(c not in '0123456789abcdef' for c in binding[k]) for k in required-{'component'})):
        raise ValueError('Exact source, payload, protocol, encoder, implementation and component pins required')
    if (not texts or len(specification['targets']) != len(texts) or
            len(specification['weights']) != len(texts) or not len(specification['active'])):
        raise ValueError('Aligned nonempty active fitting rows required; constants need no training')
    expected_kind = 'sigmoid' if binding['component'].endswith('-profile') else 'softmax'
    if specification['kind'] != expected_kind:
        raise ValueError('Objective differs from the registered component')
    identity = {'binding': binding, 'texts': list(texts),
                'specification': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in specification.items()}}
    names = {id(parameter): name for name, parameter in model.named_parameters()}
    groups = [{**{key: value for key, value in group.items() if key != 'params'},
               'parameterNames': [names[id(parameter)] for parameter in group['params']]}
              for group in optimizer.param_groups]
    return {'schema': 'TP30-training-state-1', 'binding': dict(binding),
            'dataPin': hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            'n': len(texts), 'epochs': 3, 'batch': 16, 'seed': 23, 'checkpointEvery': 500,
            'torchVersion': str(torch.__version__), 'device': next(model.parameters()).device.type,
            'optimizer': {'class': type(optimizer).__module__+'.'+type(optimizer).__qualname__,
                          'groups': groups}}


def train_segment(model, optimizer, texts, specification, output, check, *, binding,
                  stop_after, resume=None, resume_pin=None):
    """Resume exact updates at a fixed 500-example boundary; never replays saved updates.

    The caller verifies original native exit/leases, guards memory/storage/thermal
    floors, and admits the source payload. This helper cannot launch or qualify a study.
    """
    identity = contract(texts, specification, binding, model, optimizer)
    n, total = len(texts), 3*len(texts)
    if (type(stop_after) is not int or not 0 < stop_after <= total or
            (stop_after != total and stop_after % 500) or (resume is None) != (resume_pin is None)):
        raise ValueError('Pinned source and a fixed checkpoint boundary or final endpoint required')
    output = Path(output)
    if output.exists():
        raise ValueError('Each training segment requires a fresh output directory')
    check()
    generator = torch.Generator(device='cpu').manual_seed(23)
    epoch, cursor, examples, updates, compute_seconds = 0, 0, 0, 0, 0.
    order = torch.randperm(n, generator=generator)
    device = next(model.parameters()).device
    if resume is not None:
        if file_pin(resume) != resume_pin:
            raise ValueError('Saved checkpoint bytes changed')
        state = torch.load(resume, map_location='cpu', weights_only=True)
        if state['contract'] != identity:
            raise ValueError('Checkpoint data, model, protocol, runtime or component changed')
        epoch, cursor, examples, updates = [state[k] for k in ('epoch', 'cursor', 'examples', 'updates')]
        order = state['order']
        if (not 0 <= epoch <= 3 or not 0 <= cursor < n or examples != epoch*n+cursor or
                examples >= stop_after or len(order) != n or
                not torch.equal(order.sort().values, torch.arange(n))):
            raise ValueError('Invalid or already-complete checkpoint cursor/order')
        model.load_state_dict(state['model'], strict=True)
        optimizer.load_state_dict(state['optimizer'])
        generator.set_state(state['orderRng'])
        torch.set_rng_state(state['cpuRng'])
        if device.type == 'cuda':
            if len(state['cudaRng']) != torch.cuda.device_count():
                raise ValueError('CUDA random-state topology changed')
            torch.cuda.set_rng_state_all(state['cudaRng'])
        elif state['cudaRng']:
            raise ValueError('CPU segment cannot consume a GPU checkpoint')
        compute_seconds = state['computeSeconds']
        del state
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    initial_examples, initial_compute = examples, compute_seconds
    checkpoint_pin = None
    model.train()
    while examples < stop_after:
        check()
        # These boundaries are identical with or without a process interruption.
        count = min(16, n-cursor, 500-examples % 500, stop_after-examples)
        indices = order[cursor:cursor+count].tolist()
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        tick = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        logits = model([texts[i] for i in indices])
        targets = torch.as_tensor(specification['targets'][indices], dtype=logits.dtype, device=device)
        weights = torch.as_tensor(specification['weights'][indices], dtype=logits.dtype, device=device)
        loss = weighted_loss(logits, targets, weights, specification['kind'])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
        optimizer.step()
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        compute_seconds += time.perf_counter()-tick
        cursor += count
        examples += count
        updates += 1
        completed_epoch = cursor == n
        if completed_epoch:
            epoch += 1
            cursor = 0
            if epoch < 3:
                order = torch.randperm(n, generator=generator)
        if examples % 500 == 0 or completed_epoch or examples == stop_after:
            check()
            state = {'contract': identity, 'epoch': epoch, 'cursor': cursor, 'examples': examples,
                     'updates': updates, 'order': order.clone(), 'orderRng': generator.get_state(),
                     'cpuRng': torch.get_rng_state(),
                     'cudaRng': torch.cuda.get_rng_state_all() if device.type == 'cuda' else [],
                     'model': cpu_tree(model.state_dict()), 'optimizer': cpu_tree(optimizer.state_dict()),
                     'computeSeconds': compute_seconds}
            checkpoint_pin = atomic_save(output/'checkpoint.pt', state)
            del state
            names = (['pilot.pt'] if examples == 500 else []) + ([f'epoch-{epoch}.pt'] if completed_epoch else [])
            for name in names:
                check()
                shutil.copyfile(output/'checkpoint.pt', output/name)
                if file_pin(output/name) != checkpoint_pin:
                    raise RuntimeError('Immutable checkpoint copy differs')
            progress = {'examples': examples, 'total': total, 'epoch': epoch, 'cursor': cursor,
                        'updates': updates, 'checkpointPin': checkpoint_pin,
                        'computeSeconds': compute_seconds, 'segmentSeconds': time.perf_counter()-started}
            temporary = output/'progress.tmp'
            temporary.write_text(json.dumps(progress, allow_nan=False)+'\n')
            temporary.replace(output/'progress.json')
    check()
    return {'status': 'complete' if examples == total else 'segment-complete',
            'initialExamples': initial_examples, 'durableExamples': examples, 'updates': updates,
            'newExamples': examples-initial_examples, 'checkpointPin': checkpoint_pin,
            'computeSeconds': compute_seconds-initial_compute, 'segmentSeconds': time.perf_counter()-started,
            'sourceCheckpointPin': resume_pin, 'productionAdmission': False}
