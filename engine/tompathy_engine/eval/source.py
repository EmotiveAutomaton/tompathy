"""Earlier-only source-use forecasts against fixed and recency comparators."""

from datetime import datetime

import numpy as np

from ..admission import implementation_hash
from ..ledger.ids import digest
from ..ledger.schema import schema_hash
from ..models.source_trust import SourceObservation, trajectory


def evaluate(ledger, *, until, maximum_targets=1000):
    view = ledger.snapshot()
    rows = sorted(
        [
            d
            for d in view.rows("Decision")
            if d.t_resolve < until
            and d.action in {"accept", "edit", "dismiss", "ignore"}
            and any(o.origin == "ai" for o in d.options)
        ],
        key=lambda d: (d.t_open, d.decision_id),
    )
    if len(rows) > maximum_targets or not 1 <= maximum_targets <= 100000:
        raise ValueError("Source-use evaluation exceeds its target bound")
    observations = [
        SourceObservation(
            d.decision_id,
            d.session_id,
            d.t_resolve,
            d.action in {"accept", "edit"},
            d.outcome.get("source_quality"),
            datetime.fromisoformat(d.outcome["source_quality_available"])
            if d.outcome.get("source_quality_available")
            else None,
            d.t_open,
        )
        for d in rows
    ]
    predicted = {
        p["decision"]: p["acceptance_propensity"] for p in trajectory(observations, until=until)
    }
    output = []
    for target in rows:
        past = [d for d in rows if d.t_resolve < target.t_open]
        recent = sorted(
            [d for d in past if d.session_id == target.session_id],
            key=lambda d: (d.t_resolve, d.decision_id),
        )[-6:]
        values = {
            "fixed": (1 + sum(d.action in {"accept", "edit"} for d in past)) / (2 + len(past)),
            "recency": (1 + sum(d.action in {"accept", "edit"} for d in recent))
            / (2 + len(recent)),
            "source-trust": predicted[target.decision_id],
        }
        y = int(target.action in {"accept", "edit"})
        for module, p in values.items():
            output.append(
                {
                    "decision": target.decision_id,
                    "maker": target.maker_id,
                    "session": target.session_id,
                    "module": module,
                    "opened": target.t_open.isoformat(),
                    "resolved": target.t_resolve.isoformat(),
                    "taken": y,
                    "probabilities": [1 - p, p],
                    "half_brier": float((p - y) ** 2),
                    "log_loss": float(-np.log(max(1e-300, p if y else 1 - p))),
                    "training_hash": digest([d.decision_id for d in past]),
                    "training_latest": max((d.t_resolve.isoformat() for d in past), default=None),
                }
            )
    return output, {
        "decisions": len(rows),
        "implementation_hash": implementation_hash(),
        "ledger_schema_hash": schema_hash(),
        "quality_observations": sum(o.quality is not None for o in observations),
        "admission": "not established; acceptance propensity does not measure source reliability",
    }
