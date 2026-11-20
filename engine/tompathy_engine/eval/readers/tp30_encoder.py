"""Original pretrained MiniLM plus a fresh TP30 head; no network or study admission."""
from pathlib import Path

import torch

from .tp30_training import file_pin


class FineEncoder(torch.nn.Module):
    def __init__(self, encoder, tokenizer, outputs):
        super().__init__()
        if type(outputs) is not int or outputs <= 0:
            raise ValueError('Constant-only targets require no fitted encoder')
        self.encoder, self.tokenizer = encoder, tokenizer
        self.head = torch.nn.Linear(encoder.config.hidden_size, outputs)

    def forward(self, texts):
        device = next(self.parameters()).device
        batch = self.tokenizer(list(texts), return_tensors='pt', padding=True, truncation=True, max_length=128)
        batch = {key: value.to(device) for key, value in batch.items()}
        hidden = self.encoder(**batch).last_hidden_state
        mask = batch['attention_mask'].unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden*mask).sum(1)/mask.sum(1).clamp(min=1.)
        normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return self.head(normalized)


def optimizer_for(model):
    return torch.optim.AdamW([
        {'params': model.encoder.parameters(), 'lr': 2e-5},
        {'params': model.head.parameters(), 'lr': 1e-3},
    ], weight_decay=.01)


def load_original(root, specification, device, expected_files, check):
    """Load only the exact original model files admitted by the outer payload guard.

    expected_files must come from the independently verified original-model manifest,
    never from a candidate's own unverified directory listing.
    """
    root = Path(root).resolve()
    if not expected_files or not specification['active'].size:
        raise ValueError('Pinned original model and active targets required')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(expected_files):
        raise ValueError('Original encoder file inventory changed')
    for name, pin in expected_files.items():
        check()
        path = (root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or file_pin(path) != pin:
            raise ValueError('Original encoder bytes or path changed')
    check()
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(23)
    tokenizer = AutoTokenizer.from_pretrained(root, local_files_only=True, trust_remote_code=False)
    encoder = AutoModel.from_pretrained(root, local_files_only=True, trust_remote_code=False,
                                       dtype=torch.float32, attn_implementation='eager')
    model = FineEncoder(encoder, tokenizer, len(specification['active'])).to(device=device, dtype=torch.float32)
    check()
    return model, optimizer_for(model)
