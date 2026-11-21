import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def module(name):
    path = Path(__file__).resolve().parents[2] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("damaged", [False, True])
def test_only_new_rung_uses_original_source(tmp_path, monkeypatch, damaged):
    fine = module("word_table_fine_runtime")
    root = tmp_path / "root"
    (root / "inputs").mkdir(parents=True)
    out = tmp_path / "new"
    out.mkdir()
    original = tmp_path / "original"
    (original / "encoder").mkdir(parents=True)
    cfg = {"rungs":[{"id":m,"seeds":[23] if i==0 else [23,47,71]} for i,m in enumerate(fine.MODELS)],
           "sourceReceiptPin":"data","protocolPin":"protocol","initialMiniLM":{}}
    (root / "inputs/G2-contract.json").write_text(json.dumps(cfg))
    src = {"id":fine.MODELS[2],"files":{"weights":"frozen"}}
    (original / "source.json").write_text(json.dumps(src))
    (original / "encoder/weights").write_text("damaged" if damaged else "frozen")
    pin = "51c188e92b3473af802af78fd3ec4b10baceef0b13fc783516c4ef3c445194fe"
    def digest(p):
        return pin if p.name=="source.json" else p.read_text()
    core = SimpleNamespace(api=lambda _:{"models":[]}, digest=digest,
                           write=lambda p,v:p.write_text(json.dumps(v)))
    torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:True),set_num_threads=lambda n:None,
        set_num_interop_threads=lambda n:None,set_float32_matmul_precision=lambda s:None,
        backends=SimpleNamespace(cuda=SimpleNamespace(matmul=SimpleNamespace(allow_tf32=False))))
    monkeypatch.setitem(sys.modules,"torch",torch)
    monkeypatch.setattr(fine,"source_arrays",lambda *args:{"envent":{"releaseAvailable":True}})
    monkeypatch.setattr(fine,"components",lambda:())
    monkeypatch.setattr(fine,"encoder_files",lambda *args:pytest.fail("Original model was fetched again"))
    seen = []
    def component(path, enc, source, data, seed, label, *args):
        assert enc==original/"encoder" and source==src
        seen.append((seed,label))
        return {"saved":True}
    monkeypatch.setattr(fine,"run_one",component)
    monkeypatch.setitem(sys.modules,"word_table_rd2_trained",SimpleNamespace(run=lambda *a:{i:{} for i in range(5)}))
    kwargs = {"restored_modernbert":original}
    inputs = root,out,{"codePins":{"a":"b"}},core,SimpleNamespace(check=lambda:None)
    if damaged:
        with pytest.raises(ValueError,match="encoder bytes"):
            fine.run(*inputs,**kwargs)
        assert not seen
    else:
        result = fine.run(*inputs,**kwargs)
        assert len(seen)==len(set(seen))==12 and len(result)==17
        assert {seed for seed,_ in seen}=={23,47,71}
        assert not (out/"rung-0").exists() and not (out/"rung-1").exists()


def test_predecessors_and_stop(tmp_path, monkeypatch):
    repair=module("word_table_g2_repair")
    monkeypatch.setattr(repair,"ROOT",tmp_path)
    state={"Q6":True,"Q7":False}
    monkeypatch.setattr(repair,"exited",lambda path:state[path.name])
    assert not repair.predecessors()
    state["Q7"]=True
    assert repair.predecessors()
    assert not repair.stop()
    (tmp_path/"STOP").touch()
    assert repair.stop()
