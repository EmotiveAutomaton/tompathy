"""TP30 fine-rung target/loss contract; not a complete or admitted study runner."""
import numpy as np
import torch


def training_targets(shares, unassigned, sources, kind):
    """Preserve the frozen rung's targets and equal total source weights."""
    shares, other = np.asarray(shares, float), np.asarray(unassigned, float)
    sources = np.asarray(sources, str)
    if (shares.ndim != 2 or shares.shape[1] != 9 or not len(shares) or
            other.shape != (len(shares),) or sources.shape != other.shape or
            not np.isfinite(shares).all() or not np.isfinite(other).all() or
            np.any((shares < 0) | (shares > 1)) or np.any((other < 0) | (other > 1)) or
            not set(sources) <= {'go', 'envent'} or kind not in ('sigmoid', 'softmax')):
        raise ValueError('Finite nine-channel shares, unassigned rates and registered training sources required')
    unique = sorted(set(sources))
    # A batch mean with these full-cohort weights estimates the registered loss.
    weights = np.zeros(len(shares))
    for source in unique:
        mask = sources == source
        weights[mask] = len(shares)/(len(unique)*mask.sum())
    supported = np.ptp(shares, axis=0) > 0
    if kind == 'sigmoid':
        active = np.flatnonzero(supported)
        targets = shares[:, active]
        constant = (weights[:, None]*shares).mean(0)
    else:
        all_targets = np.column_stack([shares, other])
        selected = all_targets.argmax(1)
        selected[all_targets.sum(1) == 0] = 9
        active = np.unique(selected)
        targets = (selected[:, None] == active).astype(float)
        constant = np.zeros(10)
        if len(active) == 1:
            constant[active[0]] = 1
            active, targets = np.array([], int), np.empty((len(shares), 0))
    return {'targets': targets, 'active': active, 'constant': constant,
            'supported': supported, 'weights': weights, 'kind': kind}


def weighted_loss(logits, targets, weights, kind):
    """Sum channel losses per row, then source-weighted batch mean; no test selection."""
    if (kind not in ('sigmoid', 'softmax') or logits.ndim != 2 or logits.shape != targets.shape or
            not len(logits) or not logits.shape[1] or weights.shape != (len(logits),) or
            not torch.isfinite(logits).all() or not torch.isfinite(targets).all() or
            not torch.isfinite(weights).all() or torch.any(weights <= 0) or
            torch.any((targets < 0) | (targets > 1))):
        raise ValueError('Aligned finite active logits, targets and positive weights required')
    if kind == 'sigmoid':
        per_row = torch.nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction='none').sum(1)
    else:
        if not torch.allclose(targets.sum(1), torch.ones_like(weights)):
            raise ValueError('One selected control category per training row required')
        per_row = -(targets*torch.nn.functional.log_softmax(logits, dim=1)).sum(1)
    return (weights*per_row).mean()


def probabilities(logits, specification):
    """Restore unsupported constants; unassigned remains a control category only."""
    active = specification['active']
    if logits.ndim != 2 or logits.shape[1] != len(active) or not torch.isfinite(logits).all():
        raise ValueError('Finite logits aligned with the registered active columns required')
    constant = torch.as_tensor(specification['constant'], device=logits.device, dtype=logits.dtype)
    result = constant.repeat(len(logits), 1)
    if len(active):
        result[:, active] = logits.sigmoid() if specification['kind'] == 'sigmoid' else logits.softmax(1)
    return result[:, :9]
