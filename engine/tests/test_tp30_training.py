import json

import numpy as np
import pytest
import torch

from tompathy_engine.eval.readers.tp30_fine import training_targets
from tompathy_engine.eval.readers.tp30_training import file_pin, train_segment


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.Sequential(torch.nn.Linear(3, 5), torch.nn.Dropout(.3), torch.nn.Linear(5, 2))
        self.seen = []

    def forward(self, texts):
        self.seen.extend(texts)
        x = torch.tensor([[int(t) % 7/7, int(t) % 13/13, 1.] for t in texts])
        return self.layers(x)


def setup(kind='sigmoid', n=521):
    torch.manual_seed(23)
    model = Tiny()
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.01)
    shares = np.zeros((n, 9))
    shares[:, 0] = np.arange(n) % 7/7
    shares[:, 1] = 1-shares[:, 0]
    specification = training_targets(shares, np.zeros(n), ['go']*n, kind)
    binding = {key: 'a'*64 for key in ('payloadPin', 'sourceReceiptPin', 'protocolPin',
                                    'initialEncoderPin', 'implementationPin')}
    binding['component'] = 'go_only-profile' if kind == 'sigmoid' else 'go_only-control'
    return model, optimizer, [str(i) for i in range(n)], specification, binding


def run(parts, output, stop_after, **kwargs):
    model, optimizer, texts, specification, binding = parts
    return train_segment(model, optimizer, texts, specification, output, kwargs.pop('check', lambda: None),
                         binding=binding, stop_after=stop_after, **kwargs)


@pytest.mark.parametrize('kind', ['sigmoid', 'softmax'])
def test_resume_matches_uninterrupted_updates_dropout_and_epoch_order(tmp_path, kind):
    full = setup(kind)
    final = run(full, tmp_path/'full', 1563)
    first = setup(kind)
    pilot = run(first, tmp_path/'pilot', 500)
    checkpoint = tmp_path/'pilot'/'checkpoint.pt'
    original_pin = file_pin(checkpoint)
    resumed = setup(kind)
    result = run(resumed, tmp_path/'resumed', 1563, resume=checkpoint, resume_pin=original_pin)
    assert result['initialExamples'] == 500 and result['newExamples'] == 1063
    assert pilot['status'] == 'segment-complete' and result['status'] == 'complete'
    assert first[0].seen + resumed[0].seen == full[0].seen
    assert len(full[0].seen) == 1563 and final['updates'] == result['updates']
    for key, value in full[0].state_dict().items():
        assert torch.equal(value, resumed[0].state_dict()[key]), key
    assert file_pin(checkpoint) == original_pin
    progress = json.loads((tmp_path/'resumed'/'progress.json').read_text())
    assert progress['examples'] == 1563 and progress['epoch'] == 3 and progress['cursor'] == 0
    assert progress['checkpointPin'] == file_pin(tmp_path/'resumed'/'checkpoint.pt')


@pytest.mark.parametrize('change', ['data', 'protocol', 'optimizer', 'bytes'])
def test_changed_identity_is_rejected_before_forward_or_output(tmp_path, change):
    first = setup()
    run(first, tmp_path/'pilot', 500)
    checkpoint = tmp_path/'pilot'/'checkpoint.pt'
    pin = file_pin(checkpoint)
    parts = setup()
    if change == 'data':
        parts[2][0] = '42'
    elif change == 'protocol':
        parts[4]['protocolPin'] = 'b'*64
    elif change == 'optimizer':
        parts[1].param_groups[0]['lr'] = .01
    else:
        with checkpoint.open('ab') as stream:
            stream.write(b'changed')
    with pytest.raises(ValueError):
        run(parts, tmp_path/'rejected', 1563, resume=checkpoint, resume_pin=pin)
    assert not parts[0].seen and not (tmp_path/'rejected').exists()


def test_guard_failure_preserves_durable_boundary_and_recovery(tmp_path):
    full = setup()
    run(full, tmp_path/'full', 1563)
    parts = setup()

    def stop_after_pilot():
        if (tmp_path/'interrupted'/'progress.json').exists():
            raise RuntimeError('STOP')

    with pytest.raises(RuntimeError, match='STOP'):
        run(parts, tmp_path/'interrupted', 1563, check=stop_after_pilot)
    checkpoint = tmp_path/'interrupted'/'checkpoint.pt'
    assert len(parts[0].seen) == 500
    recovered = setup()
    run(recovered, tmp_path/'recovered', 1563, resume=checkpoint, resume_pin=file_pin(checkpoint))
    for key, value in full[0].state_dict().items():
        assert torch.equal(value, recovered[0].state_dict()[key]), key


def test_pilot_and_epoch_at_same_boundary_are_both_retained(tmp_path):
    parts = setup(n=500)
    run(parts, tmp_path/'pilot', 500)
    assert file_pin(tmp_path/'pilot'/'pilot.pt') == file_pin(tmp_path/'pilot'/'epoch-1.pt')
