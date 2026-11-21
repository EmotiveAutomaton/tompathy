"""The extended prompted archive reuses the initial rows and only the standard Q5 arm."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"scripts"))
import word_table_tp24_prompted as assemble


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf8")
    return assemble.sha256(path)


@pytest.fixture
def source(tmp_path, monkeypatch):
    base = tmp_path/"study"
    base.mkdir()
    monkeypatch.setattr(assemble, "BASE", base)
    monkeypatch.setattr(assemble, "ROOT", tmp_path)
    opening = base/"tp24-prompted-initial-a"
    identifiers = [f"initial-{i}" for i in range(6250)]
    groups = np.repeat(["SP1", "Q1", "Q2"], [500, 350, 5400])
    matrix = np.full((6250,8), 3.)
    receipt = {"stage":"initial", "options":{"num_predict":256}, "modelPin":"B",
               "promptPin":"prompt", "schemaPin":"schema", "features":list(assemble.FEATURES),
               "sourceReceiptPins":{"SP1":"pilot","Q1":"a","Q2":"b"}, "cohorts":{},
               "newInference":False, "writerRatingsRead":False}
    assemble.save_archive(opening, identifiers, groups, matrix, receipt)
    initial_pin = assemble.sha256(opening/"receipt.json")
    monkeypatch.setattr(assemble, "INITIAL_RECEIPT", initial_pin)
    added_ids = [f"held-{i}" for i in range(350)]
    opaque_ids = [f"opaque-{i}" for i in range(350)]
    selection = put(base/"intake-a/reserved-ids.json", {"F2":added_ids})
    monkeypatch.setattr(assemble, "SELECTION", selection)
    crosswalk = put(base/"F2-release-local/local-original-id-map.json", dict(zip(added_ids, opaque_ids, strict=True)))
    monkeypatch.setattr(assemble, "CROSSWALK", crosswalk)
    mirror = base/"mirror"
    selected = put(mirror/"development-selection.json", {"winners":{"standards":"V0","social_norms":"V1"}})
    proof_file = base/"transfer.json"
    owner = {"job":"Q5", "pid":123}
    put(proof_file, {"mirror":"study/mirror","owner":owner,"status":"complete","sourceReceiptPin":"terminal",
                     "nativeExited":True,"priorFlockReleased":True})
    put(base/"F2-release-local/release-monitor.json", {"receipt":{"selectionPin":selected}})
    summary = {"binding":{**{k:receipt[k] for k in ("options","modelPin","promptPin","schemaPin")},
                          "think":False}, "valid":349}
    put(mirror/"F2-standard/B/complete.json", summary)
    answers = np.full((350,8), 2.)
    answers[61] = np.nan
    def rows(arm, role, ids, features, check):
        assert arm == "F2-standard" and role == "B" and list(features) == list(assemble.FEATURES)
        assert ids == opaque_ids
        return answers
    fake = SimpleNamespace(pin="terminal",receipt={"roles":{"F2-standard":summary},"owner":owner},
                           artifact=lambda name:mirror/name,answers=rows)
    def verified(path, job):
        assert path == mirror and job == "Q5"
        return fake
    monkeypatch.setattr(assemble, "Mirror", verified)
    return base, proof_file, initial_pin, added_ids, summary


def test_extends_exact_original_rows_and_retains_invalid(source):
    base, transfer, original_pin, added, _ = source
    out = base/"extended"
    receipt = assemble.extend(out, transfer)
    assert receipt["initialReceiptPin"] == original_pin and receipt["reservedIncluded"] == 350
    assert receipt["cohorts"]["Q5"] == {"attempted":350, "valid":349}
    assert assemble.sha256(base/"tp24-prompted-initial-a/receipt.json") == original_pin
    with np.load(out/"prompted.npz", allow_pickle=False) as extended:
        assert extended["reportIds"].tolist()[-350:] == added
        assert extended["ratings"].shape == (6600,8) and np.isnan(extended["ratings"][6250+61]).all()
        assert np.all(extended["ratings"][:6250] == 3.)
    with pytest.raises(ValueError, match="fresh direct child"):
        assemble.extend(out, transfer)


@pytest.mark.parametrize("change", ["release", "selection", "prompt"])
def test_missing_handoff_or_changed_prompt_prevents_extension(source, change):
    base, transfer, _, _, summary = source
    if change == "release":
        put(transfer, {**assemble.read(transfer), "priorFlockReleased":False})
    elif change == "selection":
        put(base/"F2-release-local/release-monitor.json", {"receipt":{"selectionPin":"different"}})
    else:
        summary["binding"]["promptPin"] = "different"
        put(base/"mirror/F2-standard/B/complete.json", summary)
    with pytest.raises(ValueError):
        assemble.extend(base/"extended", transfer)
    assert not (base/"extended").exists()
