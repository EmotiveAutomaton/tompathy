"""Session-local acceptance propensity, not a claim about endorsement or values."""

from dataclasses import dataclass
from datetime import datetime

import numpy as np
from scipy.special import expit


@dataclass(frozen=True)
class SourceObservation:
    decision: str
    session: str
    t: datetime
    accepted: bool
    quality: float | None = None
    quality_available: datetime | None = None


def trajectory(observations, *, until, step_variance=0.1, quality_effect=0.2):
    if (
        until.tzinfo is None
        or step_variance < 0
        or not np.isfinite([step_variance, quality_effect]).all()
    ):
        raise ValueError("Invalid source trajectory parameters")
    rows = sorted((r for r in observations if r.t < until), key=lambda r: (r.t, r.decision))
    if len({r.decision for r in rows}) != len(rows):
        raise ValueError("Duplicate source observations")
    states, pending, seen_quality, out = {}, [], set(), []
    for row in rows:
        if row.t.tzinfo is None:
            raise ValueError("Source observation time must be aware")
        # A later survival outcome cannot explain an earlier acceptance.
        for prior in pending:
            if prior.decision not in seen_quality and prior.quality_available < row.t:
                mean, variance = states[prior.session]
                states[prior.session] = (mean + quality_effect * prior.quality, variance)
                seen_quality.add(prior.decision)
        mean, variance = states.get(row.session, (0.0, 1.0))
        variance += step_variance
        p = float(expit(mean))
        out.append(
            {
                "decision": row.decision,
                "session": row.session,
                "t": row.t.isoformat(),
                "acceptance_propensity": p,
                "interval": [
                    float(expit(mean - 1.96 * np.sqrt(variance))),
                    float(expit(mean + 1.96 * np.sqrt(variance))),
                ],
                "interpretation": "relative session source-use hypothesis",
            }
        )
        posterior_variance = 1 / (1 / variance + p * (1 - p))
        states[row.session] = (
            mean + posterior_variance * (int(row.accepted) - p),
            posterior_variance,
        )
        if row.quality is not None:
            if (
                not -1 <= row.quality <= 1
                or row.quality_available is None
                or row.quality_available < row.t
            ):
                raise ValueError("Quality needs its actual observation time and [-1,1] value")
            pending.append(row)
    return out
