import json
from types import SimpleNamespace

import numpy as np
import pytest

from tompathy_engine.eval.readers.word_ladder import (
    WRITER_CHANNELS,
    collect,
    completed_repair_seeds,
    ladder_comparison,
)


def test_completed_prediction_batch_must_match_order_and_checkpoint(tmp_path):
    folder=tmp_path/"arm"
    d=folder/"predict-ed-attempt-000"
    d.mkdir(parents=True)
    seal=folder/"prediction-ed.json"
    seal.write_text('{"rows":2}')
    ids=np.array(["private-a","private-b"])
    b={"modelCheckpointPin":"known"}
    contract=json.dumps({"schema":"TP30-prediction-batch-1","binding":b})
    x=np.repeat(np.array([[.1],[.8]]),9,axis=1)
    file=d/"batch-00000000-00000002.npz"
    np.savez(file,start=0,end=2,contract=contract,ids=ids,probabilities=x)
    job=SimpleNamespace(files={p.relative_to(tmp_path).as_posix():1 for p in [file,seal]},
                        artifact=lambda n:tmp_path/n)
    np.testing.assert_equal(collect(job,"arm","ed",ids,b,lambda:None),x)
    with pytest.raises(ValueError,match="reordered"):
        collect(job,"arm","ed",ids[::-1],b,lambda:None)
    with pytest.raises(ValueError,match="contract"):
        collect(job,"arm","ed",ids,{},lambda:None)
    job.files={}
    with pytest.raises(ValueError,match="Missing"):
        collect(job,"arm","ed",ids,b,lambda:None)


def test_all_three_seeds_and_both_bars_are_required():
    def row(mean,care):
        return {"channels":{n:{"profile_auc":care if n=="CARE" else mean} for n in WRITER_CHANNELS}}
    frozen=row(.7,.7)
    good=row(.76,.71)
    seeds={23:good,47:good,71:good}
    assert ladder_comparison(seeds,frozen)["passesAllThree"]
    assert ladder_comparison({23:good},frozen)["passesAllThree"] is None
    assert not ladder_comparison({**seeds,71:row(.85,.69)},frozen)["passesAllThree"]
    assert not ladder_comparison({**seeds,71:row(.71,.71)},frozen)["passesAllThree"]


def test_early_resource_stop_reports_only_fully_covered_seeds(tmp_path):
    path = tmp_path/"ladder-components.json"
    path.write_text(json.dumps({"completed":{},"skipped":{"answerdotai/ModernBERT-large":"Memory limit"}}))
    job = SimpleNamespace(files={f"rung-2/seed-23/{v}-{k}/completed.json":1
                                 for v in ("go_only","go_plus_envent") for k in ("profile","control")},
                          receipt={"rows":{}},artifact=lambda _:path)
    seeds,coverage = completed_repair_seeds(job)
    assert seeds==[23] and set(coverage["unavailableComponentsBySeed"])=={"47","71"}
    path.write_text(json.dumps({"completed":{},"skipped":{}}))
    with pytest.raises(ValueError,match="missing repair fits"):
        completed_repair_seeds(job)
