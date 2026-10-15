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
    opened: datetime | None = None


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
    out = []
    for row in rows:
        opened = row.opened or row.t
        if row.t.tzinfo is None or opened.tzinfo is None or opened > row.t:
            raise ValueError("Source observation needs valid aware chronology")
        if row.quality is not None and (
            not np.isfinite(row.quality)
            or not -1 <= row.quality <= 1
            or row.quality_available is None
            or row.quality_available.tzinfo is None
            or row.quality_available < row.t
        ):
            raise ValueError("Quality needs its actual observation time and [-1,1] value")
    for row in rows:
        opened = row.opened or row.t
        events = []
        for prior in rows:
            if prior.session != row.session or prior.t >= opened:
                continue
            events.append((prior.t, 0, prior.decision, prior))
            if prior.quality is not None and prior.quality_available < opened:
                events.append((prior.quality_available, 1, prior.decision, prior))
        mean, variance = 0.0, 1.0
        for _, kind, _, prior in sorted(events, key=lambda e: e[:3]):
            if kind == 1:
                mean += quality_effect * prior.quality
            else:
                variance += step_variance
                prior_p = float(expit(mean))
                variance = 1 / (1 / variance + prior_p * (1 - prior_p))
                mean += variance * (int(prior.accepted) - prior_p)
        variance += step_variance
        p = float(expit(mean))
        out.append(
            {
                "decision": row.decision,
                "session": row.session,
                "t": opened.isoformat(),
                "acceptance_propensity": p,
                "interval": [
                    float(expit(mean - 1.96 * np.sqrt(variance))),
                    float(expit(mean + 1.96 * np.sqrt(variance))),
                ],
                "interpretation": "relative session source-use hypothesis",
            }
        )
    return out
