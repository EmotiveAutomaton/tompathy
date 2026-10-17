"""One evidence-to-fit pipeline for the companion and both research consumers.

Question batteries permit literal features. Module admissions separately permit
display. Neither fitting nor a constructed test promotes a scientific claim.
"""

from dataclasses import replace
from datetime import datetime
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..admission import implementation_hash
from ..features.augment import Features
from ..features.deterministic import option_features
from ..features.records import Labels
from ..ledger.schema import Hash, Model, schema_hash
from ..population.build import DOMAINS
from ..transcribe.runner import CATALOGUE
from .backbone import Backbone, Choice
from .bundle import Bundle, input_hash
from .corrections import classification

TEXT_QUESTIONS = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q10")


def feature_names(questions):
    return list(option_features("", "", 0)) + [
        f"{q}:{answer}" for q in questions for answer in CATALOGUE["questions"][q]["answers"]
    ]


def vector(text, context, position, answers, questions):
    base = list(option_features(text, context, position).values())
    for q in questions:
        if q not in answers:
            raise ValueError(f"Missing literal feature {q}")
        selected = answers[q] if isinstance(answers[q], list) else [answers[q]]
        base.extend(float(a in selected) for a in CATALOGUE["questions"][q]["answers"])
    return np.asarray(base)


def cases(ledger, *, domain, until, labels=None, questions=(), extra_features=None):
    if extra_features:
        extra_features.verify(ledger, domain=domain, until=until)
    if questions and labels is None:
        raise ValueError("Literal features need bound transcription records")
    if labels:
        labels.verify(ledger)
        if labels.domain != domain or labels.until < until:
            raise ValueError("Literal labels do not cover this domain/cutoff")
        for q in questions:
            labels.require(q)
    artifacts = {a.artifact_id: a for a in ledger.rows("Artifact")}
    sessions = {s.session_id: s for s in ledger.rows("Session")}
    revisions = {r.revision_id: r for r in ledger.rows("Revision")}
    decisions = {d.decision_id: d for d in ledger.rows("Decision")}
    stable = {m.maker_id for m in ledger.rows("Maker") if m.identity != "unknown"}
    options, corrections, classifications, excluded = [], [], {}, {}
    for d in decisions.values():
        if d.t_resolve >= until or artifacts[sessions[d.session_id].artifact_id].domain != domain:
            continue
        if d.taken is None:
            continue
        if d.maker_id not in stable:
            excluded[d.decision_id] = "Unknown or unstable identity cannot train a personal profile"
            continue
        if d.action == "rate":
            excluded[d.decision_id] = "Rating labels require a task-specific rating likelihood"
            continue
        context = (
            ledger.get_text(d.context["document_ref"]) if d.context.get("document_ref") else ""
        )
        try:
            x = [
                np.concatenate(
                    (
                        vector(
                            ledger.get_text(o.content_ref) if o.content_ref else "",
                            context,
                            o.position,
                            labels.answers("Decision", d.decision_id, o.option_id)
                            if labels
                            else {},
                            questions,
                        ),
                        extra_features.values("Decision", d.decision_id, o.option_id)
                        if extra_features
                        else [],
                    )
                )
                for o in d.options
            ]
        except ValueError as exc:
            excluded[d.decision_id] = str(exc)
            continue
        options.append(
            Choice(
                d.decision_id,
                d.maker_id,
                d.t_open,
                d.t_resolve,
                np.array(x),
                next(i for i, o in enumerate(d.options) if o.option_id == d.taken),
                d.context.get("prompt_id", "unknown"),
            )
        )
    for c in ledger.rows("Correction"):
        aid = (
            revisions[c.revision_id].artifact_id
            if c.revision_id
            else sessions[decisions[c.decision_id].session_id].artifact_id
        )
        if c.t >= until or artifacts[aid].domain != domain:
            continue
        if c.maker_id not in stable:
            excluded[c.correction_id] = (
                "Unknown or unstable identity cannot train a personal profile"
            )
            continue
        answer = labels.answers("Correction", c.correction_id, "edit") if labels else {}
        kind = classification(
            answer.get("Q8"), answer.get("Q9"), labels_admitted={"Q8", "Q9"} <= answer.keys()
        )
        classifications[c.correction_id] = kind
        if kind != "preference":
            continue
        try:
            before, after = [
                np.concatenate(
                    (
                        vector(
                            ledger.get_text(getattr(c, slot + "_ref")),
                            "",
                            0,
                            labels.answers("Correction", c.correction_id, slot),
                            questions,
                        ),
                        extra_features.values("Correction", c.correction_id, slot)
                        if extra_features
                        else [],
                    )
                )
                for slot in ("before", "after")
            ]
        except ValueError as exc:
            excluded[c.correction_id] = str(exc)
            continue
        delta = after - before
        corrections.append(
            Choice(
                c.correction_id, c.maker_id, c.t, c.t, np.stack((np.zeros(len(delta)), delta)), 1
            )
        )
    return options, corrections, classifications, excluded


def pack(model, rows, population, task):
    return Bundle(
        population=population,
        domain=DOMAINS[population],
        task=task,
        until=model.until,
        beta=model.beta.tolist(),
        offsets={k: v.tolist() for k, v in model.offsets.items()},
        counts=model.counts,
        penalties=model.penalties,
        information_shares=model.information_shares,
        conditional_intervals={k: v.tolist() for k, v in model.conditional_intervals.items()},
        conditional_covariances={k: v.tolist() for k, v in model.conditional_covariances.items()},
        train_ids=list(model.train_ids),
        fit_receipts=model.fit_receipts,
        input_hash=input_hash(rows, model.until),
        implementation_hash=implementation_hash(),
        ledger_schema_hash=schema_hash(),
    )


class Pipeline(Model):
    format: Literal["tompathy-pipeline-1"] = "tompathy-pipeline-1"
    population: str
    domain: str
    until: datetime
    implementation_hash: Hash
    ledger_schema_hash: Hash
    questions: list[str] = Field(default_factory=list)
    features: list[str]
    labels: Labels | None = None
    extra_features: Features | None = None
    fits: dict[str, Bundle]
    classifications: dict[str, str]
    exclusions: dict[str, str]
    diagnosticity: dict | None = None

    @model_validator(mode="after")
    def contract(self):
        if DOMAINS.get(self.population) != self.domain or self.domain == "chess":
            raise ValueError("Text pipeline requires a writing/preferences population")
        if len(set(self.questions)) != len(self.questions) or any(
            q not in TEXT_QUESTIONS for q in self.questions
        ):
            raise ValueError("Unsupported or duplicated text feature questions")
        if self.features != feature_names(self.questions) + (
            self.extra_features.names if self.extra_features else []
        ):
            raise ValueError("Pipeline feature schema mismatch")
        if not self.fits or not self.fits.keys() <= {"options", "corrections", "joint"}:
            raise ValueError("Invalid pipeline fits")
        for name, fit in self.fits.items():
            if (
                fit.task != name
                or fit.until != self.until
                or fit.domain != self.domain
                or fit.population != self.population
                or len(fit.beta) != len(self.features)
                or fit.implementation_hash != self.implementation_hash
                or fit.ledger_schema_hash != self.ledger_schema_hash
            ):
                raise ValueError("Pipeline fit metadata mismatch")
        return self

    def verify(self, ledger, *, at, implementation=None):
        if (
            self.implementation_hash != (implementation or implementation_hash())
            or self.ledger_schema_hash != schema_hash()
        ):
            raise ValueError("Pipeline implementation/schema pin mismatch")
        if self.until > at:
            raise ValueError("Pipeline training follows capture cutoff")
        options, corrections, kinds, excluded = cases(
            ledger,
            domain=self.domain,
            until=self.until,
            labels=self.labels,
            questions=self.questions,
            extra_features=self.extra_features,
        )
        if kinds != self.classifications or excluded != self.exclusions:
            raise ValueError("Pipeline input classification mismatch")
        rows = {"options": options, "corrections": corrections, "joint": options + corrections}
        if self.diagnosticity:
            rows = weighted(rows, ledger, self.diagnosticity, self.features)
        for name, fit in self.fits.items():
            if input_hash(rows[name], self.until) != fit.input_hash or set(fit.train_ids) != {
                r.id for r in rows[name]
            }:
                raise ValueError("Pipeline training fingerprint mismatch")
        return rows

    def predict(self, maker, features, *, at, task="joint"):
        """Forecast with a shared fit or the spec's additive correction term."""
        from scipy.special import softmax

        if at < self.until:
            raise ValueError("Prediction precedes pipeline cutoff")
        if task != "correction-augmented":
            if task not in self.fits:
                raise ValueError("Requested pipeline fit is unavailable")
            return self.fits[task].predictor().predict(maker, features, at=at)
        if not {"options", "corrections"} <= self.fits.keys():
            raise ValueError("Additive correction prediction needs both fitted tasks")
        x = np.asarray(features, dtype=float)
        if (
            x.ndim != 2
            or x.shape[1] != len(self.features)
            or not len(x)
            or not np.isfinite(x).all()
        ):
            raise ValueError("Additive prediction feature shape mismatch")
        coefficient = np.zeros(len(self.features))
        for task_name in ("options", "corrections"):
            fit = self.fits[task_name]
            coefficient += np.array(fit.beta) + np.array(
                fit.offsets.get(maker, np.zeros(len(self.features)))
            )
        return softmax(x @ coefficient)


def latency_z(ledger):
    """Within-maker/type history uses only previously resolved latency observations."""
    decisions = sorted(ledger.rows("Decision"), key=lambda d: (d.t_open, d.decision_id))
    result = {}
    for d in decisions:
        past = [
            np.log1p(p.cost.latency_s)
            for p in decisions
            if p.maker_id == d.maker_id
            and p.context.get("decision_type", "offered")
            == d.context.get("decision_type", "offered")
            and p.t_resolve < d.t_open
            and p.cost.latency_s is not None
        ]
        result[d.decision_id] = (
            float((np.log1p(d.cost.latency_s) - np.mean(past)) / max(0.1, np.std(past)))
            if past and d.cost.latency_s is not None
            else None
        )
    return result


def weighted(rows, ledger, config, names):
    from .diagnosticity import weights

    z = latency_z(ledger)
    result = {}
    for task, values in rows.items():
        result[task] = [
            replace(
                r,
                weight=float(
                    weights([z[r.id]], config["a"], config["b"], utility_features=names)[0]
                ),
            )
            if r.id in z and z[r.id] is not None
            else r
            for r in values
        ]
    return result


def fit_pipeline(
    ledger,
    *,
    population,
    until,
    labels=None,
    extra_features=None,
    questions=(),
    tasks=("options", "corrections", "joint"),
    diagnosticity=False,
    progress=None,
):
    ledger = ledger.snapshot()
    domain = DOMAINS[population]
    names = feature_names(questions) + (extra_features.names if extra_features else [])
    options, corrections, kinds, excluded = cases(
        ledger,
        domain=domain,
        until=until,
        labels=labels,
        questions=questions,
        extra_features=extra_features,
    )
    rows = {"options": options, "corrections": corrections, "joint": options + corrections}
    weighting = None
    if diagnosticity:
        from .diagnosticity import fit

        z = latency_z(ledger)
        eligible = [r for r in options if z.get(r.id) is not None]
        weighting = fit(eligible, z, until=until, utility_features=names)
        if not weighting["control_passed"]:
            raise ValueError("Diagnosticity failed shuffled control; keep the unweighted fit")
        rows = weighted(rows, ledger, weighting, names)
    fits = {}
    for task in tasks:
        if task not in rows:
            raise ValueError("Unknown pipeline task")
        if not rows[task]:
            continue
        if progress:
            progress("Fitting " + task)
        fits[task] = pack(Backbone.fit(rows[task], until=until), rows[task], population, task)
    if not fits:
        raise ValueError("No eligible pipeline comparisons before cutoff")
    return Pipeline(
        population=population,
        domain=domain,
        until=until,
        implementation_hash=implementation_hash(),
        ledger_schema_hash=schema_hash(),
        questions=list(questions),
        features=names,
        labels=labels.model_copy(deep=True) if labels else None,
        extra_features=extra_features.model_copy(deep=True) if extra_features else None,
        fits=fits,
        classifications=kinds,
        exclusions=excluded,
        diagnosticity=weighting,
    )
