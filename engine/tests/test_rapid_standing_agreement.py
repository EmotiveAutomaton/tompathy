import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_standing_agreement import decode, table
from rapid_standing_return import spark_window


def test_return_waits_through_reader_c_and_preserves_a_failed_q27():
    state = {
        "q27Release": True,
        "q27Failed": False,
        "q28Started": True,
        "q28Release": False,
        "q28Left": 6000,
        "q28Failed": False,
        "q32Started": False,
        "q32Done": False,
    }
    assert spark_window(state)
    assert not spark_window({**state, "q27Release": False})
    assert not spark_window({**state, "q28Left": 15})
    assert not spark_window({**state, "q32Started": True})
    assert spark_window({**state, "q32Started": True, "q32Done": True})
    with pytest.raises(RuntimeError):
        spark_window({**state, "q27Failed": True})


def test_decode_preserves_missing_and_requires_exact_original_response():
    item = {"whose": "own", "standing": "rose", "known": "yes", "earned": "no"}
    assert decode({"response": json.dumps(item), "values": item}) == [0, 0, 0, 1]
    assert decode({"response": None, "values": None}) == [-1] * 4
    invalid = {**item, "earned": "no_rise"}
    assert decode({"response": json.dumps(invalid), "values": None}) == [-1] * 4
    with pytest.raises(ValueError):
        decode({"response": json.dumps(invalid), "values": item})


def test_missing_pairs_and_unknown_kappa_remain_visible():
    a = np.array([0, 0, 1, 1, -1, 1, -1])
    b = np.array([0, 0, 1, 1, 0, -1, -1])
    owners = np.array(["w", "w", "y", "z", "t", "u", "v"])
    r = table(a, b, owners, ["one", "two"], lambda: None)
    assert r["contingency"] == [[2, 0], [0, 2]] and r["value"] == 1
    assert (r["BOnly"], r["WOnly"], r["bothMissing"], r["jointlyValid"], r["clusters"]) == (
        1,
        1,
        1,
        4,
        6,
    )
    empty = table(a[:0], b[:0], owners[:0], ["one", "two"], lambda: None)
    assert empty["value"] is None and empty["CW"] == "not used" and empty["validDraws"] == 0


def test_earned_uses_the_full_protocol_and_keeps_a_near_boundary_unresolved():
    from rapid_marks import CHOICES
    from rapid_standing_record import describe

    cell = {
        "value": 0.5,
        "interval": [0.46, 0.54],
        "bootstrapSE": 0.01,
        "CW": "weak",
        "atOrAboveUsable": 0.001,
        "atOrBelowWeakFloor": 0.002,
    }
    when = {"value": 0.65, "interval": [0.63, 0.67], "bootstrapSE": 0.01, "atOrBelowUsable": 0.005}
    data = {"tables": {"all": {k: dict(cell) for k in CHOICES}}, "originalTimingTail": when}
    data["tables"]["all"]["earnedAmongJointRises"] = {"value": 0}
    assert describe(data)[1]["p"] == 0.005 and "clear" in describe(data)[1]["verdict"]
    when["interval"] = [0.601, 0.67]
    assert "Unresolved" in describe(data)[1]["verdict"]
