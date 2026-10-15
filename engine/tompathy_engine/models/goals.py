"""Explicit candidate exchange for the separately admitted goal judgment task.

Literal Q1-Q10 answers never masquerade as goal judgments. A candidate producer
has its own pinned admission; its inputs bind to the exact capture and root cues.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from ..ledger.ids import digest
from ..ledger.schema import Hash, Model
from .goal_tree import GoalCandidate, governing_cover


def root_cues(capture, ledger):
    if ledger is None:
        return []
    at = datetime.fromisoformat(capture["capturedAt"])
    aid = capture["id"]
    sessions = {s.session_id for s in ledger.rows("Session") if s.artifact_id == aid}
    revisions = {r.revision_id for r in ledger.rows("Revision") if r.artifact_id == aid}
    decisions = {d.decision_id for d in ledger.rows("Decision") if d.session_id in sessions}
    scopes = {"artifact": {aid}, "session": sessions, "revision": revisions, "decision": decisions}
    return sorted(
        (
            g.model_dump(mode="json")
            for g in ledger.rows("StatedGoal")
            if g.t < at and g.scope_id in scopes[g.scope]
        ),
        key=lambda g: g["goal_id"],
    )


class Candidate(Model):
    id: str
    maker: str
    label: str = Field(min_length=1, max_length=250)
    description: str = Field(max_length=3500)
    regions: list[str] = Field(min_length=1)
    depth: int = Field(ge=1, le=32)
    support: float = Field(ge=0, le=1)
    cue_match: float = Field(default=0, ge=0, le=1)
    cue_ids: list[str] = Field(default_factory=list)


class GoalInputs(Model):
    format: Literal["tompathy-goals-1"] = "tompathy-goals-1"
    capture_hash: Hash
    root_cues_hash: Hash
    generator_pin: Hash
    root_reliability: float = Field(default=0, ge=0, le=1)
    candidates: list[Candidate] = Field(max_length=300)

    @model_validator(mode="after")
    def distinct(self):
        if len({c.id for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicate goal candidate")
        return self

    def resolve(self, capture, ledger, admissions, domain, makers):
        producer = admissions.require("goal-candidates", domain)
        admissions.require("goal-tree", domain)
        if producer.model_pin != self.generator_pin:
            raise ValueError("Goal producer model pin mismatch")
        cues = root_cues(capture, ledger)
        if self.capture_hash != digest(capture) or self.root_cues_hash != digest(cues):
            raise ValueError("Goal candidate input fingerprint mismatch")
        ids = {g["goal_id"] for g in cues}
        regions = {r["id"] for r in capture["regions"]}
        for c in self.candidates:
            if (
                c.maker not in makers
                or not set(c.regions) <= regions
                or len(c.regions) != len(set(c.regions))
                or not set(c.cue_ids) <= ids
                or c.cue_match
                and not c.cue_ids
            ):
                raise ValueError("Goal candidate has unresolved maker, region or root evidence")
        results = {}
        for maker in sorted({c.maker for c in self.candidates}):
            choices = [
                GoalCandidate(c.id, frozenset(c.regions), c.depth, c.support, c.cue_match)
                for c in self.candidates
                if c.maker == maker
            ]
            results[maker] = governing_cover(
                regions, choices, root_reliability=self.root_reliability
            )
        return results, cues
