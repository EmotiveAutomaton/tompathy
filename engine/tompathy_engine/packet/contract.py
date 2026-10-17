"""Pydantic mirror of engine-emitted packet 1.7/1.8 fields.

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
    codeSpans: list[Offset] | None = Field(default=None, max_length=2000)


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
    metaDescription: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def anchors(self):
        from ..adapters.capture import utf16_length, validate_capture

        validate_capture(self.model_dump(exclude_unset=True))
        for region in self.regions:
            if any(span.end > utf16_length(region.anchor.exact) for span in region.emphasis or []):
                raise ValueError("Emphasis outside its region")
        return self


class MakerEvidence(Model):
    tier: Literal["signed", "declared", "flagged", "trace", "statistical"]
    source: str = Field(max_length=1000)
    detail: str = Field(max_length=2000)
    evidenceStatus: Literal["admitted", "constructed-tested", "unvalidated"]


class MakerDecisions(Model):
    drafted: int | None = Field(default=None, ge=0)
    selected: int | None = Field(default=None, ge=0)
    edited: int | None = Field(default=None, ge=0)
    reverted: int | None = Field(default=None, ge=0)
    housekeeping: int | None = Field(default=None, ge=0)
    commits: int | None = Field(default=None, ge=0)


class Maker(Model):
    id: str
    label: str = Field(max_length=250)
    identity: Literal["unknown", "supplied", "synthetic"]
    relationship: str = Field(max_length=1000)
    predictability: Support | None = None
    kind: Literal["person", "model", "tool", "bot", "unknown"] | None = None
    evidence: list[MakerEvidence] | None = Field(default=None, max_length=100)
    decisions: MakerDecisions | None = None
    revisions: list[str] | None = Field(default=None, max_length=500)
    localLabel: str | None = Field(default=None, max_length=250)
    bytesChanged: int | None = Field(default=None, ge=0)
    role: Literal["fully human", "human-written, then machine-polished", "machine-written, then machine-humanized", "human-initiated, then machine-continued", "deeply mixed", "machine-written, then human-edited"] | None = None


class PreferenceInterval(Model):
    lower: float = Field(allow_inf_nan=False)
    upper: float = Field(allow_inf_nan=False)
    level: float = Field(gt=0, lt=1)
    method: str = Field(min_length=1, max_length=500)


class PreferenceEstimate(Model):
    quantity: str = Field(min_length=1, max_length=200)
    value: float = Field(allow_inf_nan=False)
    reference: float | None = Field(default=None, allow_inf_nan=False)
    interval: PreferenceInterval | None
    basis: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def bounds(self):
        if self.interval and not self.interval.lower <= self.value <= self.interval.upper:
            raise ValueError("Preference interval must contain its estimate")
        return self


class PreviewLabels(Model):
    evidenceStatus: Literal["admitted", "constructed-tested", "unvalidated"] | None = None
    basis: Literal["choices", "corrections", "history", "text-surface", "population", "model-judgment"] | None = None
    entry: Literal["page", "person", "process"] | None = None

    @model_validator(mode="after")
    def derive_entry(self):
        if self.basis:
            expected = {"text-surface": "page", "model-judgment": "page", "choices": "person", "population": "person", "corrections": "process", "history": "process"}[self.basis]
            if self.entry is not None and self.entry != expected:
                raise ValueError("Entry does not match its evidence basis")
            object.__setattr__(self, "entry", expected)
            self.__pydantic_fields_set__.add("entry")
        return self


class Hypothesis(PreviewLabels):
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
    preferenceEstimate: PreferenceEstimate | None = None
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


class DocumentedAI(Model):
    basis: Literal["documented"]
    evidence: list[str] = Field(min_length=1, max_length=30)


class CalibratedAI(Model):
    basis: Literal["calibrated"]
    evidence: list[str] = Field(min_length=1, max_length=30)
    probability: float = Field(ge=0, le=1, allow_inf_nan=False)
    calibration: str = Field(min_length=1, max_length=2000)


class HierarchyNode(PreviewLabels):
    id: str
    parentId: str | None = None
    parentIds: list[str] | None = Field(default=None, min_length=1, max_length=16)
    maker: str
    label: str = Field(min_length=1, max_length=250)
    aiAttribution: Annotated[DocumentedAI | CalibratedAI, Field(discriminator="basis")] | None = None
    description: str = Field(max_length=4000)
    level: str | None = Field(default=None, min_length=1, max_length=100)
    regions: list[str] = Field(min_length=1)
    span: Span | None = None
    evidence: list[str]


class Hierarchy(Model):
    nodes: list[HierarchyNode] = Field(min_length=1, max_length=3000)


class AttentionItem(PreviewLabels):
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
    quantiles: list[float] | None = Field(default=None, min_length=20, max_length=20)


class Population(Model):
    populationId: str
    makersPooled: int = Field(ge=0)
    description: str = Field(min_length=1, max_length=4000)
    items: list[PopulationItem] = Field(max_length=1000)


class Provider(Model):
    id: str
    method: str = Field(min_length=1, max_length=1000)
    admissions: list[str] | None = Field(default=None, max_length=100)
    mode: Literal["admitted", "preview"] | None = None
    previewNotice: str | None = Field(default=None, min_length=1, max_length=500)


class PreviewModule(Model):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    status: Literal["pending", "running", "complete", "unavailable", "failed", "skipped"]
    detail: str = Field(max_length=2000)
    elapsedMs: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    completed: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def progress_bounds(self):
        if (self.completed is None) != (self.total is None) or self.completed is not None and self.completed > self.total:
            raise ValueError("Progress must have bounded completed and total counts")
        return self


class PreviewReader(Model):
    id: str = Field(max_length=200)
    revision: str = Field(max_length=200)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    backend: str = Field(max_length=200)


class SurfaceStatistics(Model):
    mean: float = Field(ge=0, allow_inf_nan=False)
    median: float = Field(ge=0, allow_inf_nan=False)
    iqr: float = Field(ge=0, allow_inf_nan=False)
    words: int = Field(ge=0)
    heldOut: int = Field(ge=0)
    heldOutExamples: list[str] = Field(max_length=20)


class AgreementMetric(Model):
    spearman: float | None = Field(ge=-1, le=1, allow_inf_nan=False)
    overlap: float = Field(ge=0, le=1)
    words: int = Field(ge=1)


class AgreementRegion(Model):
    region: str
    readers: list[Literal[0, 1]] = Field(min_length=1, max_length=2)


class Agreement(Model):
    short: AgreementMetric
    full: AgreementMetric
    regions: list[AgreementRegion] = Field(max_length=1500)
    method: str = Field(max_length=1000)


class PayoffSummary(Model):
    sentencesScored: int | None = Field(default=None, ge=0)
    totalSentences: int | None = Field(default=None, ge=0)
    layer1NovelRetention: float = Field(ge=0, le=1)
    layer2NovelRetention: float | None = Field(default=None, ge=0, le=1)
    layer1Seconds: float = Field(ge=0)
    contextFreeMean: float | None = Field(ge=0)
    easyWithoutContext: bool
    layer2Status: str = Field(max_length=500)


class GitHubSummary(Model):
    quotaRemaining: int | None = Field(ge=0)
    commits: int = Field(ge=1)
    declaredAiCommitShare: float = Field(ge=0, le=1)


class Preview(Model):
    modules: list[PreviewModule] = Field(max_length=20)
    readers: list[PreviewReader] = Field(default_factory=list, max_length=4)
    statistics: SurfaceStatistics | None = None
    agreement: Agreement | None = None
    payoff: PayoffSummary | None = None
    github: GitHubSummary | None = None
    cachedAt: str | None = None
    completedAt: str | None = None
    latestSummary: str | None = Field(default=None, max_length=2000)
    resumable: bool = False
    priorityRegion: str | None = None
    coverage: list[str] | None = Field(default=None, max_length=1500)
    layoutGroups: list[list[str]] | None = Field(default=None, max_length=20)
    historySource: Literal["wikipedia", "github"] | None = None
    timings: dict[str, float] | None = None
    rootCueReliability: float = Field(default=.6, ge=0, le=1)
    rootCueStatus: Literal["assumed"] = "assumed"
    goalLenses: list[list[str]] | None = Field(default=None, max_length=2)
    budgetDrops: list[Literal["payoff-layer-2", "second-reader", "techniques-after-30", "governing-call"]] = Field(default_factory=list)


class GlobalFinding(Model):
    source: str = Field(max_length=500)
    claim: str = Field(max_length=2000)
    number: float | None = None
    interval: tuple[float, float] | None = None
    unit: str | None = Field(default=None, max_length=100)
    evidenceStatus: Literal["descriptive", "constructed-tested"]
    link: str = Field(pattern=r"^https://", max_length=4000)


class Scope(Model):
    kind: Literal["artifact", "context"]
    contextIds: list[str]


class Packet(Model):
    schemaVersion: Literal["1.7", "1.8", "1.9"] = "1.7"
    id: str
    revision: int = Field(gt=0)
    artifact: Artifact
    provider: Provider
    preview: Preview | None = None
    globalFindings: list[GlobalFinding] | None = Field(default=None, max_length=30)
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
