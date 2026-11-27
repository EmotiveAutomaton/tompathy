import importlib
from pathlib import Path

import pytest


def module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("rapid_marks")


def test_prompt_variants_and_conditional_field(monkeypatch):
    m = module(monkeypatch)
    assert len({m.protocol(k)["promptPin"] for k in ("standing", "standing2", "standing3")}) == 3
    good = {"whose": "own", "standing": "rose", "known": "no", "earned": "yes"}
    assert m.standing(good) == good
    assert m.standing(dict(good, standing="fell")) is None
    assert m.standing(dict(good, standing="fell", earned="no_rise")) is not None
    assert m.standing(dict(good, extra="yes")) is None


def test_width_requires_every_valid_output_and_better_clock(monkeypatch):
    m = module(monkeypatch)
    rows = [{"id": str(i), "values": {"a": True}, "response": "same"} for i in range(200)]
    missing = [*rows[:-1], dict(rows[-1], values=None)]
    a = m.compare({1: (rows, 200), 2: (rows, 150), 4: (missing, 100)})
    assert a["selectedWidth"] == 2
    assert a["arms"][4]["identicalValid"] == 199
    assert m.compare({1: (missing, 200), 2: (missing, 100)})["selectedWidth"] == 1
    with pytest.raises(ValueError):
        m.compare({1: (rows, 200), 2: (list(reversed(rows)), 100)})
