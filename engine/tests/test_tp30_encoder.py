from types import SimpleNamespace

import numpy as np
import pytest
import torch

from tompathy_engine.eval.readers.tp30_encoder import FineEncoder, load_original, optimizer_for
from tompathy_engine.eval.readers.tp30_training import file_pin


class Encoder(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.config = SimpleNamespace(hidden_size=2)
        self.embedding = torch.nn.Embedding(3, 2)
        with torch.no_grad():
            self.embedding.weight.copy_(torch.tensor([[3., 0.], [0., 4.], [100., 100.]]))

    def forward(self, input_ids, attention_mask):
        return SimpleNamespace(last_hidden_state=self.embedding(input_ids))


def test_masked_normalized_pooling_cap_and_encoder_gradient():
    calls = []

    def tokenizer(texts, **kwargs):
        calls.append((texts, kwargs))
        return {'input_ids': torch.tensor([[0, 1, 2]]), 'attention_mask': torch.tensor([[1, 1, 0]])}

    model = FineEncoder(Encoder(), tokenizer, 2)
    with torch.no_grad():
        model.head.weight.copy_(torch.eye(2)); model.head.bias.zero_()
    result = model(['constructed'])
    assert torch.allclose(result, torch.tensor([[.6, .8]]))
    assert calls[0][1] == {'return_tensors': 'pt', 'padding': True, 'truncation': True, 'max_length': 128}
    result[0, 0].backward()
    assert torch.count_nonzero(model.encoder.embedding.weight.grad[:2]) > 0
    assert torch.count_nonzero(model.encoder.embedding.weight.grad[2]) == 0
    optimizer = optimizer_for(model)
    assert [g['lr'] for g in optimizer.param_groups] == [2e-5, 1e-3]
    assert all(g['weight_decay'] == .01 for g in optimizer.param_groups)
    assert {id(p) for g in optimizer.param_groups for p in g['params']} == {id(p) for p in model.parameters()}


@pytest.mark.parametrize('change', ['extra', 'modified', 'missing'])
def test_load_rejects_changed_inventory_before_transformers_or_network(tmp_path, change):
    path = tmp_path/'config.json'; path.write_text('{}')
    original = {'config.json': file_pin(path)}
    if change == 'extra':
        (tmp_path/'extra.bin').write_bytes(b'new')
    elif change == 'modified':
        path.write_text('{"different": true}')
    else:
        original['absent.bin'] = 'a'*64
    with pytest.raises(ValueError, match='Original encoder'):
        load_original(tmp_path, {'active': np.array([0])}, 'cpu', original, lambda: None)
