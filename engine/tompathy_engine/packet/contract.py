"""Pydantic mirror of engine-emitted packet 1.7 fields.

ToMpathy's zod PacketSchema remains authoritative. CI validates every emitted
fixture through it. The engine does not emit contribution or Ghost Scale guesses.
"""

from typing import Annotated, Literal

from pydantic import Field, PlainValidator, model_validator

from ..ledger.schema import Model


class Support(Model):
    value: float
    scale: tuple[float, float]
    semantics: Literal["relative", "probability"] = "relative"
    meaning: str = Field(min_length=1, max_length=1000)
    calibration: str | None = Field(default=None, max_length=1000)
    candidateSet: str | None = None

    @model_validator(mode="after")
    def bounds(self):
        if not self.scale[0] <= self.value <= self.scale[1] or self.scale[0] >= self.scale[1]:
            raise ValueError("Support outside declared scale")
        if self.semantics == "probability" and (
            self.scale != (0, 1) or not self.candidateSet or not self.calibration
        ):
            raise ValueError("Probability needs calibration and a [0,1] candidate set")
        return self


def _anchor_context(value):
    # JS slice can leave a lone surrogate at either edge. Pydantic's ordinary
    # string validator rejects it, but changing it would break exact matching.
    from ..adapters.capture import utf16_length

    if not isinstance(value, str) or utf16_length(value) > 160:
        raise ValueError("Anchor context must be at most 160 UTF-16 units")
    return value


class Anchor(Model):
    exact: str = Field(min_length=1, max_length=20000)
    prefix: Annotated[str, PlainValidator(_anchor_context)]
    suffix: Annotated[str, PlainValidator(_anchor_context)]
    start: int = Field(ge=0)
    index: int = Field(ge=0)


class PageHint(Model):
    heading: int | None = Field(default=None, ge=1, le=6)
    unit: Literal["group"] | None = None
    section: str | None = Field(default=None, max_length=300)
    involvement: Literal["original", "edited", "curated", "ghost", "unknown"] | None = None


class Offset(Model):
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Empty/reversed span")
        return self


class Span(Offset):
    region: str


class Region(Model):
    id: str
    anchor: Anchor
    pageHint: PageHint | None = None
    emphasis: list[Offset] | None = Field(default=None, max_length=2000)


class Author(Model):
    label: str = Field(min_length=1, max_length=250)
    basis: Literal["page-metadata", "byline", "structured-data"]


class CaptureMethod(Model):
    method: Literal["article", "main", "content-container", "page"]
    note: str = Field(max_length=1000)


class Artifact(Model):
    id: str = Field(min_length=1, max_length=200)
    revision: str = Field(min_length=1, max_length=200)
    title: str = Field(max_length=1000)
    source: str = Field(max_length=4000)
    capturedAt: str
    regions: list[Region] = Field(min_length=1, max_length=1500)
    truncated: bool = False
    authors: list[Author] | None = Field(default=None, max_length=20)
    capture: CaptureMethod | None = None

    @model_validator(mode="after")
    def anchors(self):
        from ..adapters.capture import utf16_length, validate_capture

        validate_capture(self.model_dump(exclude_unset=True))
        for region in self.regions:
            if any(span.end > utf16_length(region.anchor.exact) for span in region.emphasis or []):
                raise ValueError("Emphasis outside its region")
        return self


class Maker(Model):
    id: str
    label: str = Field(max_length=250)
    identity: Literal["unknown", "supplied", "synthetic"]
    relationship: str = Field(max_length=1000)
    predictability: Support | None = None


class Hypothesis(Model):
    id: str
    kind: Literal["goal", "process", "value", "attention"]
    label: str = Field(min_length=1, max_length=250)
    description: str = Field(max_length=4000)
    makers: list[str] = Field(min_length=1)
    regions: list[str]
    status: Literal["hypothesis", "creator-reported", "observed", "unknown"]
    support: Support | None = None
    evidence: list[str]
    spans: list[Span] | None = Field(default=None, max_length=1500)
    alternativeSet: str | None = None
    decisionNodes: list[str] | None = None
    valueCategory: Literal["drive", "constructed"] | None = None
    interpretation: (
        Literal[
            "current-attention",
            "governing-purpose",
            "local-goal",
            "historical-event",
            "reader-route",
            "repertoire",
            "preference",
            "value",
            "drive",
        ]
        | None
    ) = None
    icon: (
        Literal["seeking", "rage", "fear", "lust", "care", "panic-grief", "play", "body", "value"]
        | None
    ) = None


class Evidence(Model):
    id: str
    source: str = Field(max_length=4000)
    excerpt: str = Field(max_length=20000)
    capturedAt: str
    relationship: str = Field(min_length=1, max_length=2000)


class Alternative(Model):
    id: str
    kind: Literal["competing", "independent", "coexisting"]
    members: list[str] = Field(min_length=1)
    exhaustive: bool


class ProcessEdge(Model):
    from_: str = Field(alias="from")
    to: str
    relationship: str = Field(min_length=1, max_length=500)
    kind: (
        Literal["precedes", "enables", "revises", "alternative", "related", "order-unknown"] | None
    ) = None
    status: Literal["hypothesis", "creator-reported", "observed", "unknown"] | None = None
    evidence: list[str] | None = None


class Process(Model):
    interpretation: Literal["historical-production", "functional", "unspecified"] | None = None
    nodes: list[str]
    edges: list[ProcessEdge]


class HierarchyNode(Model):
    id: str
    parentId: str | None = None
    parentIds: list[str] | None = Field(default=None, min_length=1, max_length=16)
    maker: str
    label: str = Field(min_length=1, max_length=250)
    description: str = Field(max_length=4000)
    level: str | None = Field(default=None, min_length=1, max_length=100)
    regions: list[str] = Field(min_length=1)
    span: Span | None = None
    evidence: list[str]


class Hierarchy(Model):
    nodes: list[HierarchyNode] = Field(min_length=1, max_length=3000)


class AttentionItem(Model):
    hypothesis: str
    support: Support | None = None


class Attention(Model):
    maker: str
    span: Span
    items: list[AttentionItem] = Field(max_length=40)


class Uncertainty(Model):
    level: Literal["low", "medium", "high", "unknown"]
    meaning: str = Field(min_length=1, max_length=500)


class Estimate(Model):
    region: str
    uncertainty: Uncertainty


class PopulationPoint(Model):
    records: int = Field(ge=0)
    intervalWidth: float = Field(ge=0)


class PopulationItem(Model):
    hypothesis: str
    populationSupport: Support
    makerRecords: int = Field(ge=0)
    shrinkage: float = Field(ge=0, le=1)
    curve: list[PopulationPoint] = Field(max_length=100)


class Population(Model):
    populationId: str
    makersPooled: int = Field(ge=0)
    description: str = Field(min_length=1, max_length=4000)
    items: list[PopulationItem] = Field(max_length=1000)


class Provider(Model):
    id: str
    method: str = Field(min_length=1, max_length=1000)


class Scope(Model):
    kind: Literal["artifact", "context"]
    contextIds: list[str]


class Packet(Model):
    schemaVersion: Literal["1.7"] = "1.7"
    id: str
    revision: int = Field(gt=0)
    artifact: Artifact
    provider: Provider
    origin: Literal["synthetic example", "imported", "live provider"]
    scope: Scope
    makers: list[Maker] = Field(min_length=1)
    hypotheses: list[Hypothesis] = Field(max_length=1000)
    alternatives: list[Alternative]
    process: Process
    estimates: list[Estimate]
    evidence: list[Evidence]
    currentAttention: list[Attention] | None = Field(default=None, max_length=3000)
    goalHierarchy: Hierarchy | None = None
    population: Population | None = None
    revisionOf: str | None = None
    changeExplanation: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def references(self):
        from .validate import validate_relations

        validate_relations(self)
        return self

    def wire(self):
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
