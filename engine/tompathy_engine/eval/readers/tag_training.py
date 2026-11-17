"""TP23 bounded MiniLM multilabel fitting, with inner-story development only."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file, save_file
from sentence_transformers import SentenceTransformer
from sklearn.metrics import roc_auc_score

from ..back_half.reporting import save_json


def mean_auc(y, p):
    values = [float(roc_auc_score(y[:, j], p[:, j])) for j in range(y.shape[1]) if len(np.unique(y[:, j])) == 2]
    if not values:
        raise ValueError('No two-class tag support')
    return float(np.mean(values))


class TagHead(torch.nn.Module):
    def __init__(self, directory, outputs):
        super().__init__()
        self.encoder = SentenceTransformer(str(directory), device='cpu', local_files_only=True, trust_remote_code=False)
        self.encoder.max_seq_length = 128
        self.head = torch.nn.Linear(self.encoder.get_sentence_embedding_dimension(), outputs)

    def forward(self, texts):
        vector = self.encoder(self.encoder.tokenize(texts))['sentence_embedding']
        return self.head(torch.nn.functional.normalize(vector, p=2, dim=1))


def predict(model, texts, check, *, output=None, identity=None):
    model.eval()
    result = []
    key = hashlib.sha256(json.dumps({'texts': texts, 'identity': identity}, sort_keys=True).encode()).hexdigest() if output is not None else None
    with torch.inference_mode():
        for i in range(0, len(texts), 16):
            check()
            path = Path(output)/f'{i:07d}.npz' if output is not None else None
            if path and path.exists():
                with np.load(path, allow_pickle=False) as saved:
                    if str(saved['key']) != key:
                        raise ValueError('Tag prediction cache source changed')
                    values = saved['values']
            else:
                values = model(texts[i:i+16]).numpy()
                if path:
                    path.parent.mkdir(exist_ok=True, parents=True)
                    np.savez(path, key=key, values=values)
            if values.shape != (min(16, len(texts)-i), model.head.out_features) or not np.isfinite(values).all():
                raise ValueError('Invalid durable tag forecasts')
            result.append(values)
    return np.concatenate(result)


def fit(directory, texts, y, train, dev, output, seed, check, *, final=False):
    output = Path(output)
    output.mkdir(exist_ok=False)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = TagHead(directory, y.shape[1])
    optimizer = torch.optim.AdamW([{'params': model.encoder.parameters(), 'lr': 2e-5},
        {'params': model.head.parameters(), 'lr': 1e-3}], weight_decay=.01)
    started, best, epochs = time.perf_counter(), -1., []
    for epoch in range(3):
        model.train()
        order, loss_sum = rng.permutation(train), 0.
        for start in range(0, len(order), 16):
            check()
            ids = order[start:start+16]
            optimizer.zero_grad(set_to_none=True)
            logits = model([texts[i] for i in ids])
            loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, torch.as_tensor(y[ids], dtype=torch.float32))
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite multilabel loss')
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optimizer.step()
            loss_sum += float(loss.detach())*len(ids)
            save_json(output/'progress.json', {'epoch': epoch+1, 'examples': min(start+16, len(order)),
                      'total': len(order), 'seconds': time.perf_counter()-started})
        validation = None if final else predict(model, [texts[i] for i in dev], check)
        score = None if final else mean_auc(y[dev], validation)
        epochs.append({'epoch': epoch+1, 'loss': loss_sum/len(train), 'development_auc': score})
        if final or score > best:
            best = score if score is not None else best
            save_file({k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}, str(output/'best.safetensors'))
            if validation is not None:
                np.savez(output/'development.npz', index=dev, logits=validation)
        save_json(output/'epochs.json', epochs)
    model.load_state_dict(load_file(str(output/'best.safetensors')))
    model.encoder.save(str(output/'encoder'), safe_serialization=True)
    np.savez(output/'head.npz', weights=model.head.weight.detach().numpy(), bias=model.head.bias.detach().numpy())
    save_json(output/'training.json', {'seed': seed, 'epochs': epochs, 'fit': len(train), 'development': len(dev),
        'final_unscored': final, 'selection': 'highest inner-development mean AUC, earliest epoch on ties',
        'cap': 128, 'batch': 16, 'loss': 'unweighted binary cross entropy', 'encoder_lr': 2e-5, 'head_lr': 1e-3})
    return model, best


def load_saved(directory):
    directory = Path(directory)
    with np.load(directory/'head.npz', allow_pickle=False) as h:
        outputs = h['weights'].shape[0]
    model = TagHead(directory/'encoder', outputs)
    model.load_state_dict(load_file(str(directory/'best.safetensors')))
    return model, json.loads((directory/'training.json').read_text(encoding='utf8'))
