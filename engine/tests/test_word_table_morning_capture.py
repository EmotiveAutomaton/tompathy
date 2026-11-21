import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

script = Path(__file__).resolve().parents[2]/'scripts/word_table_morning_boundary.py'
spec = importlib.util.spec_from_file_location('word_table_morning_boundary',script)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def test_boundary_precedes_stop_and_survives_an_extra_durable_row(tmp_path,monkeypatch):
    entry = {'commit':'example'}
    job = tmp_path/'jobs/Q6'
    (job/'B').mkdir(parents=True)
    owner = {'job':'Q6','commit':'example','pid':7}
    (job/'owner.json').write_text(json.dumps(owner))
    (job/'receipt.json').write_text(json.dumps({'owner':owner,'entry':entry,'status':'running'}))
    (tmp_path/'queue.json').write_text(json.dumps({'jobs':{'Q6':entry,'Q7':entry}}))
    (job/'B/row-000000.json').write_text('{}')
    stamp = '2026-11-21T08:00:00-08:00'
    monkeypatch.setattr(capture,'owns_flock',lambda value:False)
    monkeypatch.setattr(capture,'owner_time',lambda value,now:None)
    with pytest.raises(ValueError,match='current native owner'):
        capture.capture(tmp_path,stamp)
    assert not (job/'STOP').exists()
    (job/'B/row-000001.json').write_text('{}')
    monkeypatch.setattr(capture,'owns_flock',lambda value:value==owner)
    first = capture.capture(tmp_path,stamp)
    assert (job/'STOP').exists() and not (tmp_path/'jobs/Q7').exists()
    assert first['durableRows']==1
    assert capture.capture(tmp_path,stamp)==first


def test_owner_stamp_is_timezone_aware_and_cannot_precede_or_anticipate_review():
    edge = capture.MORNING
    for value in ('2026-11-21T06:59:00-08:00','2026-11-21T07:00:01-08:00','2026-11-21T07:00:00'):
        with pytest.raises(ValueError):
            capture.owner_time(value,edge)
    assert capture.owner_time(edge.isoformat(),edge)==datetime.fromisoformat('2026-11-21T15:00:00+00:00')
