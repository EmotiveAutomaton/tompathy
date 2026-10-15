"""Past-only latency normalization, separated from utility features."""

import math
from collections import defaultdict

import numpy as np


def standardize(decisions):
    histories, output = defaultdict(list), {}
    for row in sorted(decisions, key=lambda d: (d.t_open, d.decision_id)):
        key = (row.maker_id, row.action)
        past = [
            d.cost.latency_s
            for d in histories[key]
            if d.t_resolve < row.t_open and d.cost.latency_s is not None
        ]
        value = row.cost.latency_s
        z = None
        if value is not None and len(past) >= 2:
            values = np.log1p(past)
            scale = float(np.std(values))
            z = (math.log1p(value) - float(np.median(values))) / max(scale, 1e-6)
        output[row.decision_id] = z
        histories[key].append(row)
    return output
