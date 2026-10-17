"""Literal labels bound to exact ledger inputs and independently tested questions.

This exchange contains observations, never maker judgments. Research may inspect
failed batteries, but only matching passed questions become model features.
"""

from contextlib import nullcontext
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from ..ledger.ids import digest
from ..ledger.schema import Hash, Model, schema_hash
from ..transcribe.runner import CATALOGUE, validate_answer


def subject(kind, ident, slot):
    return digest([kind, ident, slot])


def inputs(ledger, *, domain, until, full_context=False):
    artifacts = {a.artifact_id: a for a in ledger.rows("Artifact")}
    sessions = {s.session_id: s for s in ledger.rows("Session")}
    revisions = {r.revision_id: r for r in ledger.rows("Revision")}
    decisions = {d.decision_id: d for d in ledger.rows("Decision")}
    out = {}

    def add(kind, ident, slot, text, context="", before=None):
        out[subject(kind, ident, slot)] = {
            "context": context if full_context else context[-1200:],
            "text": text,
            "before": before,
        }

    for d in decisions.values():
        if d.t_resolve >= until or artifacts[sessions[d.session_id].artifact_id].domain != domain:
            continue
        context = (
            ledger.get_text(d.context["document_ref"]) if d.context.get("document_ref") else ""
        )
        for o in d.options:
            add(
                "Decision",
                d.decision_id,
                o.option_id,
                ledger.get_text(o.content_ref) if o.content_ref else "",
                context,
            )
    for c in ledger.rows("Correction"):
        aid = (
            revisions[c.revision_id].artifact_id
            if c.revision_id
            else sessions[decisions[c.decision_id].session_id].artifact_id
        )
        if c.t >= until or artifacts[aid].domain != domain:
            continue
        before, after = ledger.get_text(c.before_ref), ledger.get_text(c.after_ref)
        add("Correction", c.correction_id, "before", before)
        add("Correction", c.correction_id, "after", after)
        add("Correction", c.correction_id, "edit", after, before=before)
    return out


class Label(Model):
    input_hash: Hash
    answers: dict[str, str | list[str]]

    @model_validator(mode="after")
    def valid_answers(self):
        for question, answer in self.answers.items():
            if question not in CATALOGUE["questions"]:
                raise ValueError("Unknown literal question")
            validate_answer(question, {"answer": answer})
        return self


class Labels(Model):
    format: Literal["tompathy-labels-1"] = "tompathy-labels-1"
    domain: str
    until: datetime
    transcriber_pin: Hash
    ledger_schema_hash: Hash
    question_records: dict[str, dict]
    labels: dict[str, Label]
    exclusions: dict[str, str] = Field(default_factory=dict)

    def verify(self, ledger):
        if self.ledger_schema_hash != schema_hash():
            raise ValueError("Literal label schema pin mismatch")
        available = inputs(ledger, domain=self.domain, until=self.until)
        for key, label in self.labels.items():
            if key not in available or digest(available[key]) != label.input_hash:
                raise ValueError("Literal label input fingerprint mismatch")
            for question in label.answers:
                self.require(question)
        return self

    def require(self, question):
        r = self.question_records.get(question, {})
        if (
            r.get("question_id") != question
            or r.get("transcriber_pin") != self.transcriber_pin
            or not r.get("passed")
            or r.get("status") != "admitted"
            or r.get("items", 0) < 200
            or r.get("valid_rate", 0) < 0.95
            or not r.get("battery_hash")
            or not r.get("admission_id")
        ):
            raise ValueError(f"Literal question {question} lacks a matching battery")
        from ..transcribe.admission import metrics_pass

        if not metrics_pass(r, question):
            raise ValueError(f"Literal question {question} failed its battery")
        return r["admission_id"]

    def answers(self, kind, ident, slot):
        row = self.labels.get(subject(kind, ident, slot))
        return row.answers if row else {}


def transcribe(ledger, reader, *, domain, until, questions, maximum=500, progress=None):
    backend = getattr(reader, "backend", None)
    with backend.session() if hasattr(backend, "session") else nullcontext():
        return _transcribe(ledger, reader, domain=domain, until=until, questions=questions, maximum=maximum, progress=progress)


def _transcribe(ledger, reader, *, domain, until, questions, maximum=500, progress=None):
    """Bounded serial work; cache resumes completed calls, no silent truncation."""
    available = inputs(ledger, domain=domain, until=until)
    exclusions = {key: "Literal text window exceeds 12,000 characters; item excluded without truncation"
                  for key, data in available.items() if len(data["text"]) > 12000 or len(data["before"] or "") > 12000}
    jobs = [
        (key, data, q)
        for key, data in sorted(available.items())
        for q in questions
        if key not in exclusions and (data["before"] is not None) == (q in {"Q8", "Q9"})
    ]
    if len(jobs) > maximum or maximum < 1:
        raise ValueError(f"Transcription needs {len(jobs)} calls; explicit maximum is {maximum}")
    labels = {}
    for n, (key, data, q) in enumerate(jobs):
        if progress:
            progress(f"Literal transcription {n + 1}/{len(jobs)}")
        answer = reader.ask(q, **data)["answer"]
        labels.setdefault(key, {"input_hash": digest(data), "answers": {}})["answers"][q] = answer
    result = Labels(
        domain=domain,
        until=until,
        transcriber_pin=reader.pin,
        ledger_schema_hash=schema_hash(),
        labels=labels,
        exclusions=exclusions,
        question_records={q: reader.admissions[q] for q in questions},
    )
    return result.verify(ledger)
