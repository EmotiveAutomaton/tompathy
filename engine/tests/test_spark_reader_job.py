import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('spark_job', Path(__file__).resolve().parents[2]/'scripts/spark-reader-job.py')
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)


def test_thermal_guard_requires_known_safe_flags():
    assert not job.thermal_row('89, 92.5, Not Active, Not Active')['unsafe']
    assert job.thermal_row('90, 92.5, Not Active, Not Active')['unsafe']
    assert job.thermal_row('80, 92.5, Active, Not Active')['unsafe']
    assert job.thermal_row('80, 92.5, N/A, Not Active')['unsafe']
    with pytest.raises(ValueError):
        job.thermal_row('N/A, 20, Not Active, Not Active')


def test_structured_values_reject_booleans_missing_and_extra_fields():
    values = dict.fromkeys(job.FEATURES, 3)
    assert job.valid_features(values) == [3]*8
    for value in [True, 0, 6, 2.5, '3']:
        assert job.valid_features({**values, 'pleasantness':value}) is None
    assert job.valid_features({**values,'extra':1}) is None
    assert job.valid_features({}) is None


def test_masked_mean_unit_normalization_keeps_padding_out():
    import torch
    torch.set_num_threads(2)
    x = torch.tensor([[[3.,4.],[300.,400.]], [[1.,0.],[0.,1.]]])
    actual = job.pooled(x,torch.tensor([[1,0],[1,1]]),torch)
    assert torch.allclose(actual,torch.tensor([[.6,.8],[2**-.5,2**-.5]]))


def test_payload_rejects_changed_or_escaped_artifacts(tmp_path):
    items = [{'id':str(i),'text':'constructed'} for i in range(500)]
    (tmp_path/'items.json').write_text(json.dumps(items))
    manifest = {'schema':'SP1-open-payload-1','privateSource':False,'files':{'items.json':job.digest(tmp_path/'items.json')}}
    job.write(tmp_path/'payload.json',manifest)
    assert len(job.verify_payload(tmp_path)[1]) == 500
    (tmp_path/'items.json').write_text('changed')
    with pytest.raises(ValueError,match='artifact'):
        job.verify_payload(tmp_path)
    manifest['files'] = {'../outside.json':'no'}
    job.write(tmp_path/'payload.json',manifest)
    with pytest.raises(ValueError,match='artifact'):
        job.verify_payload(tmp_path)


def test_guard_stop_and_deadline(tmp_path):
    guard = job.Guard(tmp_path,1)
    guard.check()
    (tmp_path/'STOP').touch()
    with pytest.raises(RuntimeError): guard.check()
    other = job.Guard(tmp_path,0)
    with pytest.raises(RuntimeError): other.check()
    fixed = job.Guard(tmp_path,8,deadline=123.0)
    assert fixed.deadline == 123.0


def test_reader_guard_cancels_only_its_own_client(monkeypatch):
    class Owned:
        returncode = None
        terminated = False
        def communicate(self,*args,**kwargs): raise AssertionError('guard must stop before sending')
        def poll(self): return None
        def terminate(self): self.terminated = True
        def wait(self,timeout): self.returncode = -15
    process = Owned()
    monkeypatch.setattr(job.subprocess,'Popen',lambda *a,**kw:process)
    class Stop:
        def check(self): raise RuntimeError('thermal')
    with pytest.raises(RuntimeError,match='thermal'):
        job.guarded_generate({},Stop())
    assert process.terminated
