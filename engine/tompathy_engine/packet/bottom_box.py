"""TS2 page readings; maker estimates remain closed pending scoped admission."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ..ledger.schema import Model

KEYS = {
    'set_points': ('knowledge', 'tending', 'belonging', 'seen_as_competent', 'seen_as_kind'),
    'body': ('warmth', 'food', 'sleep'),
    'readings': ('stress', 'freedom'),
    'channels': ('SEEKING', 'FEAR', 'RAGE', 'PANIC_GRIEF', 'CARE', 'PLAY', 'LUST', 'DISGUST', 'SHAME'),
}


class EmptyReading(Model):
    value: None
    evidence: list[str] = Field(max_length=0)
    status: Literal['unvalidated']
    ledgerRows: list[str] = Field(max_length=0)


class LegacyBottomBox(Model):
    version: Literal['bottom-box-0']
    set_points: dict[str, EmptyReading]
    body: dict[str, EmptyReading]
    readings: dict[str, EmptyReading]
    hub: str | None = Field(max_length=250)
    channels: dict[str, EmptyReading]

    @model_validator(mode='after')
    def fixed_shape(self):
        for group, names in KEYS.items():
            if set(getattr(self, group)) != set(names):
                raise ValueError('Bottom box keys differ from bottom-box-0')
        return self


Unit = Annotated[float, Field(ge=0, le=1)]
ReadingId = Literal['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'C1', 'C2', 'C3', 'C4',
                    'C5', 'C6', 'C7', 'C8', 'C9', 'S1', 'K1']


class Share(Model):
    value: Unit
    interval: tuple[Unit, Unit]
    of: Literal['sentences read as carrying a feeling']
    method: Literal['corrected']

    @model_validator(mode='after')
    def ordered(self):
        if not self.interval[0] <= self.value <= self.interval[1]:
            raise ValueError('Share must lie in its interval')
        return self


class Mapping(Model):
    status: Literal['proposed', 'ruled'] = 'proposed'
    source: str = Field(min_length=1, max_length=2000)


class Stake(Model):
    need: Literal['N1', 'N2', 'N3', 'N4', 'N5', 'N6']
    direction: Literal['up', 'down', 'threatened', 'restored', 'unfed', 'either']
    by: Literal['self', 'other', 'circumstance', 'any']
    when: Literal['ahead', 'already', 'now', 'any']
    mapping: Mapping


class ReadingEvent(Model):
    # Offsets are UTF-16 code units in the supplied sentence stream, end-exclusive.
    span: tuple[int, int]
    label: str = Field(min_length=1, max_length=200)
    confidence: Unit
    stake: Stake | None = None
    who: Literal['writer', 'other', 'unclear'] = 'unclear'
    words: list[tuple[int, int]] = Field(default_factory=list, max_length=200)
    channel_by_table: dict[str, str] | None = None

    @model_validator(mode='after')
    def spans(self):
        a, b = self.span
        if not 0 <= a < b or any(not a <= x < y <= b for x, y in self.words):
            raise ValueError('Invalid event or attribution span')
        if self.channel_by_table is not None and (
                set(self.channel_by_table) != {'channel', 'version'}
                or self.channel_by_table['channel'] not in ('C2', 'C3', 'C6', 'C8', 'C9')
                or not self.channel_by_table['version']):
            raise ValueError('Invalid trigger-table channel')
        return self


class SeriesPoint(Model):
    from_: int = Field(alias='from', ge=0)
    to: int = Field(gt=0)
    value: Unit

    @model_validator(mode='after')
    def ordered(self):
        if self.to <= self.from_:
            raise ValueError('Invalid series span')
        return self


class AnswerKey(Model):
    corpus: str = Field(min_length=1, max_length=300)
    labelled_by: str = Field(min_length=1, max_length=300)
    n: int = Field(gt=0)


class ReadingScore(Model):
    metric: str = Field(min_length=1, max_length=100)
    value: float
    interval: tuple[float, float] | None

    @model_validator(mode='after')
    def ordered(self):
        if self.interval and not self.interval[0] <= self.value <= self.interval[1]:
            raise ValueError('Invalid score interval')
        return self


class PageReading(Model):
    id: ReadingId
    tier: Literal['on_page']
    share: Share | None
    events: list[ReadingEvent] = Field(max_length=10000)
    series: list[SeriesPoint] = Field(max_length=2000)
    pack: str = Field(pattern=r'^[a-z0-9][a-z0-9-]*@[0-9a-f]{64}$')
    key: AnswerKey
    score: ReadingScore
    people: dict[str, float]
    floor: dict[str, float]
    nothing_here: dict[str, Unit | None]
    mapping: Mapping
    status: Literal['benchmarked', 'research']


class MarketplaceTile(Model):
    id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=250)
    source: str = Field(min_length=1, max_length=2000)


class BottomBoxV1(Model):
    version: Literal['bottom-box-1']
    on_page: list[PageReading] = Field(max_length=100)
    # No producer is admitted yet. Neither text nor a benchmark opens this tier.
    about_maker: list[dict] = Field(max_length=0)
    marketplace: list[MarketplaceTile] = Field(max_length=100)

    @model_validator(mode='after')
    def unique(self):
        keys = [(r.id, r.pack) for r in self.on_page]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate reading in pack')
        if len({t.id for t in self.marketplace}) != len(self.marketplace):
            raise ValueError('Duplicate marketplace tile')
        return self


class BottomBoxV2(Model):
    version: Literal['bottom-box-2']
    on_page: list['PageReadingV2'] = Field(max_length=100)
    about_maker: list[dict] = Field(max_length=0)
    toolbox: list[MarketplaceTile] = Field(max_length=100)

    @model_validator(mode='after')
    def unique(self):
        keys = [(r.id, r.pack) for r in self.on_page]
        if len(keys) != len(set(keys)) or len({t.id for t in self.toolbox}) != len(self.toolbox):
            raise ValueError('Duplicate reading or toolbox tile')
        return self


class PageReadingV2(PageReading):
    # Owner ruling: labels without a theory home stay inspectable, unassigned.
    id: ReadingId | None

    @model_validator(mode='after')
    def label_only(self):
        if self.id is None and (self.status != 'research' or self.share is not None
                or self.series or any(e.stake is not None for e in self.events)):
            raise ValueError('Unmapped research labels cannot imply a level or stake')
        return self


BottomBoxV2.model_rebuild()


def empty_bottom_box():
    return {'version': 'bottom-box-1', 'on_page': [], 'about_maker': [], 'marketplace': []}


def upgrade_bottom_box(value):
    if isinstance(value, dict) and value.get('version') == 'bottom-box-0':
        LegacyBottomBox.model_validate(value)  # Never launder nonempty legacy claims.
        return empty_bottom_box()
    return value


class BottomBox(BottomBoxV1):
    @model_validator(mode='before')
    @classmethod
    def upgrade(cls, value):
        return upgrade_bottom_box(value)
