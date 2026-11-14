"""TS1 structural placeholder: no producer, evidence, estimate or admission."""
from typing import Literal

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


class BottomBox(Model):
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


def empty_bottom_box():
    return {'version': 'bottom-box-0', 'hub': None, **{
        group: {name: {'value': None, 'evidence': [], 'status': 'unvalidated', 'ledgerRows': []}
                for name in names} for group, names in KEYS.items()}}
