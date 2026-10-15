from copy import deepcopy
from datetime import UTC, datetime, timedelta

import numpy as np

from tompathy_engine.eval.harness import handling_prequential


def records():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        {
            "key": f"r{i:03}",
            "writer": f"maker{i % 3}",
            "session": f"s{i % 3}",
            "prompt": "fixture",
            "open_at": (t + timedelta(minutes=i)).isoformat(),
            "resolved_at": (t + timedelta(minutes=i, seconds=30)).isoformat(),
            "handling": ["accept", "edit", "dismiss", "ignore"][i % 4],
            "document": "Observed context",
            "menu": ["An option", "Another"],
            "decision_index": i,
            "previous_handling": "accept",
        }
        for i in range(36)
    ]


def test_prequential_no_future_labels_and_order_invariance():
    rows = records()
    baseline, receipt = handling_prequential(rows)
    assert receipt["decisions"] == 36 and baseline[0]["probabilities"] == [0.25] * 4
    future = deepcopy(rows)
    for r in future[25:]:
        r["handling"] = "ignore"
    changed, _ = handling_prequential(future)
    assert baseline[:50] == changed[:50]
    reverse, _ = handling_prequential(rows[::-1])
    assert baseline == reverse
    assert all(np.isclose(sum(r["probabilities"]), 1) for r in baseline)


def test_simultaneous_labels_are_excluded_and_outcomes_irrelevant():
    rows = records()[:2]
    rows[0]["resolved_at"] = rows[1]["open_at"]
    for row in rows:
        row["outcome"] = {"truth": "must never enter features"}
    scored, _ = handling_prequential(rows)
    assert scored[-1]["training_records"] == 0
