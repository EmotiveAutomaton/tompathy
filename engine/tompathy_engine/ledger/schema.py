"""Canonical v1 ledger contract. Truth is never a reader record type.

Every model is strict about unknown fields. Flexible context is observed input,
not a route for evaluator sidecars. Transport headers pin schema_hash().
"""

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .ids import digest

SCHEMA_VERSION = "1.0"
Identifier = Annotated[str, Field(min_length=1, max_length=500)]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_assignment=True)

    @field_validator("*", mode="after")
    @classmethod
    def aware_time(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("Timestamp must include a timezone")
            return value.astimezone(UTC)
        return value


class Record(Model):
    supersedes: Identifier | None = None


class Maker(Record):
    maker_id: Identifier
    source_dataset: Identifier
    identity: Literal["unknown", "pseudonymous", "supplied", "synthetic"]
    display_label: str
    identity_basis: list[str] = Field(default_factory=list)


class Artifact(Record):
    artifact_id: Identifier
    maker_ids: list[Identifier]
    kind: Literal["essay", "article", "code", "game", "session", "other"]
    source_uri: str
    revisions: list[Identifier] = Field(default_factory=list)
    tier: Literal["T0", "T1", "T2"]
    domain: Identifier = "writing"


class Revision(Record):
    revision_id: Identifier
    artifact_id: Identifier
    parent_revision_ids: list[Identifier] = Field(default_factory=list)
    maker_id: Identifier | None = None
    t: datetime
    content_ref: Hash
    stated_goal_ids: list[Identifier] = Field(default_factory=list)


class Session(Record):
    session_id: Identifier
    maker_id: Identifier
    artifact_id: Identifier
    t_start: datetime
    t_end: datetime
    stated_goal_ids: list[Identifier] = Field(default_factory=list)

    @model_validator(mode="after")
    def order(self):
        if self.t_end < self.t_start:
            raise ValueError("Session ends before it begins")
        return self


class StatedGoal(Record):
    goal_id: Identifier
    maker_id: Identifier
    scope: Literal["session", "artifact", "revision", "decision"]
    scope_id: Identifier
    text: str
    source: Literal["prompt", "edit_summary", "commit_message", "assignment", "title", "request"]
    t: datetime


class StatedPreference(Record):
    pref_id: Identifier
    maker_id: Identifier
    attribute: str
    value: float | str
    scale: list[float] | list[str]
    source: Literal["survey", "profile", "self_description"]
    t: datetime | None = None


class Option(Model):
    option_id: Identifier
    origin: Literal["maker", "ai", "system", "env"]
    content_ref: Hash | None = None
    position: int = Field(ge=0)
    features: dict[str, float] = Field(default_factory=dict)


class Cost(Model):
    latency_s: float | None = Field(default=None, ge=0)
    keystrokes: int | None = Field(default=None, ge=0)
    chars_typed: int | None = Field(default=None, ge=0)
    time_left_s: float | None = Field(default=None, ge=0)


class Decision(Record):
    decision_id: Identifier
    maker_id: Identifier
    session_id: Identifier
    t_open: datetime
    t_resolve: datetime
    options: list[Option] = Field(min_length=1)
    taken: Identifier | None = None
    action: Literal[
        "accept",
        "edit",
        "dismiss",
        "ignore",
        "write",
        "delete",
        "revise",
        "move",
        "submit",
        "rate",
        "choose",
    ]
    cost: Cost = Field(default_factory=Cost)
    context: dict[str, Any] = Field(default_factory=dict)
    outcome: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_choice(self):
        ids = [o.option_id for o in self.options]
        if len(set(ids)) != len(ids) or (self.taken is not None and self.taken not in ids):
            raise ValueError("Taken option must belong to a uniquely identified offered set")
        if self.t_resolve < self.t_open:
            raise ValueError("Decision resolves before opening")
        return self


class Span(Model):
    region: Identifier
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def order(self):
        if self.end <= self.start:
            raise ValueError("Span must be nonempty")
        return self


class Correction(Record):
    correction_id: Identifier
    maker_id: Identifier
    decision_id: Identifier | None = None
    revision_id: Identifier | None = None
    span: Span | None = None
    before_ref: Hash
    after_ref: Hash
    t: datetime
    stated_reason: str | None = None

    @model_validator(mode="after")
    def subject(self):
        if self.decision_id is None and self.revision_id is None:
            raise ValueError("Correction needs a decision or revision witness")
        return self


class ContextEvent(Record):
    event_id: Identifier
    session_id: Identifier
    t: datetime
    kind: Literal["clock", "opponent_move", "environment", "prime", "other"]
    payload: dict[str, Any]


class Evidence(Record):
    evidence_id: Identifier
    source_uri: str
    excerpt: str
    captured_at: datetime
    relationship: str


class Provenance(Model):
    record_id: Identifier
    record_type: Identifier
    adapter: str
    adapter_version: str
    source_file_sha256: Hash
    created_at: datetime


RECORDS = {
    c.__name__: c
    for c in (
        Maker,
        Artifact,
        Revision,
        Session,
        StatedGoal,
        StatedPreference,
        Decision,
        Correction,
        ContextEvent,
        Evidence,
        Provenance,
    )
}
ID_FIELDS = dict(
    zip(
        RECORDS,
        (
            "maker_id",
            "artifact_id",
            "revision_id",
            "session_id",
            "goal_id",
            "pref_id",
            "decision_id",
            "correction_id",
            "event_id",
            "evidence_id",
            "record_id",
        ),
        strict=True,
    )
)


def schema_hash() -> str:
    return digest({k: v.model_json_schema() for k, v in RECORDS.items()})
