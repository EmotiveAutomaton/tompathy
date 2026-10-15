"""The eight constructed bridge contracts; no claim of external Ghost admission."""

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from tompathy_engine.ghost.bridge import ingest_reader, load_reader, reader_choices
from tompathy_engine.ledger.ids import digest
from tompathy_engine.ledger.provenance import provenance_for
from tompathy_engine.ledger.schema import Artifact, Decision, Maker, Option, Session, schema_hash
from tompathy_engine.ledger.store import Ledger
from tompathy_engine.models.backbone import Backbone, Choice

PIN = "a" * 64
START = datetime(2026, 1, 1, tzinfo=UTC)


def fixture():
    rows = [
        Artifact(
            artifact_id="art",
            maker_ids=["m"],
            kind="session",
            source_uri="fixture:ghost",
            tier="T2",
        ),
        Maker(
            maker_id="m",
            source_dataset="constructed",
            identity="synthetic",
            display_label="Constructed maker",
        ),
        Session(
            session_id="s",
            maker_id="m",
            artifact_id="art",
            t_start=START,
            t_end=START + timedelta(hours=1),
        ),
    ]
    for i in range(24):
        rows.append(
            Decision(
                decision_id=f"d{i:03}",
                maker_id="m",
                session_id="s",
                t_open=START + timedelta(minutes=i),
                t_resolve=START + timedelta(minutes=i, seconds=30),
                options=[
                    Option(
                        option_id="left", origin="env", position=0, features={"observable": 0.0}
                    ),
                    Option(
                        option_id="right", origin="env", position=1, features={"observable": 1.0}
                    ),
                ],
                taken="right" if i % 4 else "left",
                action="choose",
            )
        )
    rows.extend(provenance_for(rows, "ghost-fixture", "b" * 64))
    value = {
        "ledger_schema_hash": schema_hash(),
        "implementation_hash": PIN,
        "records": [{"type": type(r).__name__, "record": r.model_dump(mode="json")} for r in rows],
        "texts": {},
    }
    return value


def save(tmp_path, value):
    value = deepcopy(value)
    value["reader_hash"] = digest(value)
    path = tmp_path / "reader.json"
    path.write_text(json.dumps(value), encoding="utf8")
    return path


def test_1_canonical_schema_and_unknown_fields(tmp_path):
    value = fixture()
    path = save(tmp_path, value)
    rows, _ = load_reader(path, expected_implementation=PIN)
    assert len(reader_choices(rows)) == 24
    value["records"][3]["record"]["invented"] = True
    with pytest.raises(ValueError):
        load_reader(save(tmp_path, value), expected_implementation=PIN)


def test_2_reference_and_time_integrity(tmp_path):
    for field, val in [("session_id", "missing"), ("t_open", "2027-01-01T00:00:00Z")]:
        value = fixture()
        value["records"][3]["record"][field] = val
        with pytest.raises(ValueError):
            load_reader(save(tmp_path, value), expected_implementation=PIN)


def test_3_truth_sidecar_canary_and_predictability_isolation(tmp_path):
    path = save(tmp_path, fixture())
    (tmp_path / "truth.json").write_text(
        json.dumps({"canary": "random-canary-one", "creator_predictability": 99})
    )
    a, _ = load_reader(path, expected_implementation=PIN)
    (tmp_path / "truth.json").write_text(
        json.dumps({"canary": "different-canary", "creator_predictability": -99})
    )
    b, _ = load_reader(path, expected_implementation=PIN)
    assert a == b and "canary" not in str(a)
    value = fixture()
    value["records"][3]["record"]["context"] = {"observed_context": {"truth_canary": 123}}
    with pytest.raises(ValueError, match="truth"):
        load_reader(save(tmp_path, value), expected_implementation=PIN)


def test_4_native_and_ledger_exact_reader_roundtrip(tmp_path):
    path = save(tmp_path, fixture())
    ledger = Ledger(tmp_path / "ledger")
    ingest_reader(path, ledger, expected_implementation=PIN)
    native, _ = load_reader(path, expected_implementation=PIN)
    cutoff = START + timedelta(days=1)
    a = Backbone.fit(reader_choices(native), until=cutoff)
    b = Backbone.fit(reader_choices(ledger.all()), until=cutoff)
    assert np.allclose(a.predict("m", [[0], [1]]), b.predict("m", [[0], [1]]), atol=1e-12, rtol=0)


def test_5_renaming_and_row_permutation_do_not_change_forecasts(tmp_path):
    rows, _ = load_reader(save(tmp_path, fixture()), expected_implementation=PIN)
    cases = reader_choices(rows)
    renamed = [
        Choice("renamed-" + r.id, "new-maker", r.opened, r.resolved, r.features[::-1], 1 - r.taken)
        for r in cases[::-1]
    ]
    cutoff = START + timedelta(days=1)
    a = Backbone.fit(cases, until=cutoff)
    b = Backbone.fit(renamed, until=cutoff)
    assert np.allclose(
        a.predict("m", [[0], [1]]), b.predict("new-maker", [[1], [0]])[::-1], atol=1e-12, rtol=0
    )


def test_6_known_answer_frequency_and_pooling(tmp_path):
    rows, _ = load_reader(save(tmp_path, fixture()), expected_implementation=PIN)
    model = Backbone.fit(reader_choices(rows), until=START + timedelta(days=1))
    assert model.predict("m", [[0], [1]])[1] == pytest.approx(0.75, abs=0.03)
    assert model.shrinkage("unseen") == 0
    assert 0 < model.shrinkage("m") < 1


def test_7_real_adapter_shapes_share_the_same_reader_contract(tmp_path):
    # Real source shape, constructed data. Unknown review and endorsement are
    # observations of missing knowledge, not a hidden source-reliability label.
    value = fixture()
    for row in value["records"]:
        if row["type"] == "Decision":
            row["record"]["context"] = {
                "decision_index": 0,
                "previous_handling": None,
                "prompt_id": "fixture",
            }
            row["record"]["outcome"] = {
                "reviewed": "unknown",
                "understood": "unknown",
                "endorsed": "unknown",
            }
    rows, _ = load_reader(save(tmp_path, value), expected_implementation=PIN)
    assert len(reader_choices(rows)) == 24


def test_8_schema_and_implementation_pin_mismatch_refuse(tmp_path):
    for field in ["ledger_schema_hash", "implementation_hash"]:
        value = fixture()
        value[field] = "c" * 64
        with pytest.raises(ValueError, match="pin"):
            load_reader(save(tmp_path, value), expected_implementation=PIN)
