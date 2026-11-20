import numpy as np
import pytest
import torch

from tompathy_engine.eval.readers.tp30_fine import training_targets
from tompathy_engine.eval.readers.tp30_prediction import predict_segment
from tompathy_engine.eval.readers.tp30_training import file_pin


class Predictor(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.ones(1))
        self.seen = []

    def forward(self, texts):
        self.seen.extend(texts)
        return torch.tensor([[int(t)/521] for t in texts])*self.anchor


def inputs():
    shares = np.zeros((2, 9)); shares[:, 0] = [.1, .9]
    spec = training_targets(shares, [0, 0], ['go']*2, 'sigmoid')
    binding = {key: 'a'*64 for key in ('payloadPin', 'sourceReceiptPin', 'protocolPin',
                                    'modelCheckpointPin', 'implementationPin')}
    binding['target'] = 'envent'
    return [str(i) for i in range(521)], [f'id-{i}' for i in range(521)], spec, binding


def run(model, output, stop=521, **kwargs):
    texts, ids, spec, binding = inputs()
    binding.update(kwargs.pop('change', {}))
    return predict_segment(model, texts, ids, spec, output, kwargs.pop('check', lambda: None),
                           binding=binding, stop_after=stop, **kwargs)


def test_pilot_continuation_reuses_exact_rows_and_final_short_batch(tmp_path):
    first, second = Predictor(), Predictor()
    pilot = run(first, tmp_path/'pilot', 500)
    prefix = [(tmp_path/'pilot'/r['file'], r['sha256']) for r in pilot['files']]
    final = run(second, tmp_path/'final', resume_files=prefix)
    assert first.seen + second.seen == inputs()[0]
    assert final['reusedRows'] == 500 and final['newRows'] == 21 and final['status'] == 'complete'
    assert final['files'][-1]['end']-final['files'][-1]['start'] == 5
    for source, pin in prefix:
        assert file_pin(source) == pin == file_pin(tmp_path/'final'/source.name)


@pytest.mark.parametrize('change', ['model', 'order', 'bytes'])
def test_changed_saved_predictions_are_rejected_before_new_inference(tmp_path, change):
    run(Predictor(), tmp_path/'pilot', 500)
    sources = sorted((tmp_path/'pilot').glob('batch-*.npz'))
    prefix = [(path, file_pin(path)) for path in sources]
    alterations = {}
    if change == 'model':
        alterations = {'modelCheckpointPin': 'b'*64}
    elif change == 'order':
        prefix[0], prefix[1] = prefix[1], prefix[0]
    else:
        with sources[0].open('ab') as stream:
            stream.write(b'changed')
    model = Predictor()
    with pytest.raises(ValueError):
        run(model, tmp_path/'rejected', resume_files=prefix, change=alterations)
    assert not model.seen and not (tmp_path/'rejected').exists()


def test_interrupted_prediction_recovers_durable_batch_without_progress_dependency(tmp_path):
    model = Predictor()

    def stop():
        if list((tmp_path/'interrupted').glob('batch-*.npz')):
            raise RuntimeError('STOP')

    with pytest.raises(RuntimeError, match='STOP'):
        run(model, tmp_path/'interrupted', check=stop)
    sources = sorted((tmp_path/'interrupted').glob('batch-*.npz'))
    resumed = Predictor()
    result = run(resumed, tmp_path/'recovered', resume_files=[(p, file_pin(p)) for p in sources])
    assert model.seen + resumed.seen == inputs()[0]
    assert result['reusedRows'] == 16 and result['newRows'] == 505
