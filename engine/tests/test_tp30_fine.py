import numpy as np
import pytest
import torch

from tompathy_engine.eval.readers.tp30_fine import probabilities, training_targets, weighted_loss


def test_source_weights_preserve_equal_source_mass_and_original_tie_rule():
    shares = np.zeros((4, 9)); shares[:, 0] = [.2, .6, .4, .8]
    shares[0, 1] = .2
    row = training_targets(shares, [.2, 0, 0, 0], ['go', 'go', 'go', 'envent'], 'softmax')
    assert row['weights'][:3].sum() == pytest.approx(row['weights'][3])
    assert row['active'].tolist() == []  # All ties resolve to the first channel.
    assert probabilities(torch.empty((3, 0)), row).tolist() == [[1.]+[0.]*8]*3
    silent = training_targets(np.zeros((2, 9)), [0, 0], ['go', 'go'], 'softmax')
    assert probabilities(torch.empty((2, 0)), silent).sum() == 0  # Unassigned is not a channel.


@pytest.mark.parametrize('kind', ['sigmoid', 'softmax'])
def test_weighted_loss_matches_source_average_and_gradient(kind):
    shares = np.zeros((4, 9)); shares[:, 0] = [.2, .9, .3, .6]; shares[:, 1] = [.8, .1, .7, .4]
    row = training_targets(shares, [0]*4, ['go', 'go', 'go', 'envent'], kind)
    targets = torch.tensor(row['targets'], dtype=torch.double)
    weights = torch.tensor(row['weights'], dtype=torch.double)
    logits = torch.tensor([[.2, -.7], [.1, .4], [-.3, .9], [.8, -.2]], dtype=torch.double, requires_grad=True)
    actual = weighted_loss(logits, targets, weights, kind)
    go = weighted_loss(logits[:3], targets[:3], torch.ones(3, dtype=torch.double), kind)
    ev = weighted_loss(logits[3:], targets[3:], torch.ones(1, dtype=torch.double), kind)
    assert actual.item() == pytest.approx(((go+ev)/2).item())
    assert torch.autograd.gradcheck(lambda x: weighted_loss(x, targets, weights, kind), (logits,))


def test_constant_profile_columns_and_invalid_data_remain_explicit():
    shares = np.zeros((2, 9)); shares[:, 0] = [.2, .8]; shares[:, 1] = .3
    row = training_targets(shares, [0, 0], ['go', 'go'], 'sigmoid')
    result = probabilities(torch.zeros((2, 1), dtype=torch.double), row).numpy()
    assert np.allclose(result[:, :2], [[.5, .3], [.5, .3]])
    assert row['supported'].tolist() == [True]+[False]*8
    with pytest.raises(ValueError):
        training_targets(shares, [0, 0], ['go', 'ed'], 'sigmoid')
    shares[0, 0] = np.nan
    with pytest.raises(ValueError):
        training_targets(shares, [0, 0], ['go', 'go'], 'sigmoid')
