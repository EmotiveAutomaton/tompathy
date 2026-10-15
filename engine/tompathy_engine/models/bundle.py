"""Portable, pinned MAP fits. Fitting is not scientific admission.

Only witnessed choices train this bundle. Relative preference displays require a
separate backbone-preferences admission; handling forecasts do not become values.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..admission import implementation_hash
from ..eval.ledger import choices
from ..ledger.ids import digest
from ..ledger.schema import Hash, Model, schema_hash
from ..population.build import DOMAINS
from .backbone import Backbone


def input_hash(rows, until):
    return digest(
        [
            {
                "id": r.id,
                "maker": r.maker,
                "opened": r.opened.isoformat(),
                "resolved": r.resolved.isoformat(),
                "features": r.features.tolist(),
                "taken": r.taken,
                "prompt": r.prompt,
                "weight": r.weight,
            }
            for r in sorted(rows, key=lambda r: r.id)
            if r.resolved < until
        ]
    )


class Bundle(Model):
    format: Literal["tompathy-map-1"] = "tompathy-map-1"
    population: str
    domain: str
    task: Literal["options", "handling", "corrections", "joint"]
    until: datetime
    beta: list[float] = Field(min_length=1)
    offsets: dict[str, list[float]]
    counts: dict[str, int]
    penalties: dict[str, float]
    information_shares: dict[str, float]
    conditional_intervals: dict[str, list[list[float]]]
    conditional_covariances: dict[str, list[list[float]]] = Field(default_factory=dict)
    train_ids: list[str] = Field(min_length=1)
    input_hash: Hash
    implementation_hash: Hash
    ledger_schema_hash: Hash

    @model_validator(mode="after")
    def dimensions(self):
        d, makers = len(self.beta), set(self.offsets)
        if DOMAINS.get(self.population) != self.domain:
            raise ValueError("Model population/domain mismatch")
        if any(
            set(v) != makers
            for v in (
                self.counts,
                self.penalties,
                self.information_shares,
                self.conditional_intervals,
            )
        ):
            raise ValueError("Model maker parameters disagree")
        if len(set(self.train_ids)) != len(self.train_ids) or sum(self.counts.values()) != len(
            self.train_ids
        ):
            raise ValueError("Model training counts disagree")
        for maker in makers:
            bounds = self.conditional_intervals[maker]
            if (
                len(self.offsets[maker]) != d
                or len(bounds) != d
                or any(len(b) != 2 or b[0] > b[1] for b in bounds)
            ):
                raise ValueError("Model parameter dimensions disagree")
            if (
                self.counts[maker] < 1
                or self.penalties[maker] <= 0
                or not 0 <= self.information_shares[maker] <= 1
            ):
                raise ValueError("Invalid model count, penalty or information share")
        if self.conditional_covariances:
            if set(self.conditional_covariances) != makers:
                raise ValueError("Covariance maker keys disagree")
            for value in self.conditional_covariances.values():
                matrix = np.asarray(value)
                if (
                    matrix.shape != (d, d)
                    or not np.allclose(matrix, matrix.T)
                    or np.linalg.eigvalsh(matrix).min() <= 0
                ):
                    raise ValueError("Invalid conditional covariance")
        return self

    def verify(self, ledger, *, at, implementation=None):
        if (
            self.implementation_hash != (implementation or implementation_hash())
            or self.ledger_schema_hash != schema_hash()
        ):
            raise ValueError("Model implementation/schema pin mismatch; refit explicitly")
        if self.until > at:
            raise ValueError("Model contains training after the capture cutoff")
        rows = choices(ledger, domain=self.domain, task=self.task)
        if input_hash(rows, self.until) != self.input_hash or set(self.train_ids) != {
            r.id for r in rows if r.resolved < self.until
        }:
            raise ValueError("Model training ledger fingerprint mismatch")
        return rows

    def predictor(self):
        return Backbone(
            beta=np.array(self.beta),
            until=self.until,
            offsets={k: np.array(v) for k, v in self.offsets.items()},
            counts=self.counts,
            penalties=self.penalties,
            information_shares=self.information_shares,
            conditional_intervals={k: np.array(v) for k, v in self.conditional_intervals.items()},
            conditional_covariances={
                k: np.array(v) for k, v in self.conditional_covariances.items()
            },
            train_ids=tuple(self.train_ids),
        )


def fit_bundle(ledger, *, population, until, task="options"):
    rows = choices(ledger, domain=DOMAINS[population], task=task)
    if not any(r.resolved < until for r in rows):
        raise ValueError("No eligible observed choices before the fit cutoff")
    model = Backbone.fit(rows, until=until)
    return Bundle(
        population=population,
        domain=DOMAINS[population],
        task=task,
        until=until,
        beta=model.beta.tolist(),
        offsets={k: v.tolist() for k, v in model.offsets.items()},
        counts=model.counts,
        penalties=model.penalties,
        information_shares=model.information_shares,
        conditional_intervals={k: v.tolist() for k, v in model.conditional_intervals.items()},
        conditional_covariances={k: v.tolist() for k, v in model.conditional_covariances.items()},
        train_ids=list(model.train_ids),
        input_hash=input_hash(rows, until),
        implementation_hash=implementation_hash(),
        ledger_schema_hash=schema_hash(),
    )


def load_bundle(path):
    if not path:
        return None
    import json

    value = json.loads(Path(path).read_text(encoding="utf8"))
    if value.get("format") == "tompathy-pipeline-1":
        from .pipeline import Pipeline

        return Pipeline.model_validate(value)
    return Bundle.model_validate(value)
