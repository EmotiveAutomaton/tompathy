import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rapid_agency_record import predictions
from rapid_inputs import key
from rapid_pride_agency import align, compare


def data(n_close=50):
    a = np.repeat([0, 1, 2, 3, -1], [60, n_close, 70, 4, 3])
    w = np.arange(len(a)) % 10
    y = np.select([a == 0, a == 1, a == 2], [0.8, 0.65, 0.5], default=0.9)
    return y, np.repeat("proud", len(a)), w, a


def test_same_report_and_writer_required_even_with_the_same_shape():
    native = ["p1", "p2", "p3"]
    ids = [key("ed", item) for item in native]
    owners = ["ed:w1", "ed:w2", "ed:w1"]
    align(native, ids, owners, [0, 1, 0])
    with pytest.raises(ValueError, match="forecast IDs"):
        align(native, list(reversed(ids)), owners, [0, 1, 0])
    with pytest.raises(ValueError, match="writer assignments"):
        align(native, ids, owners, [0, 0, 1])


def test_means_and_cw_gates_use_only_registered_rows():
    y, labels, writers, agency = data()
    for gate in ("usable", "weak", "not used"):
        row = compare(y, labels, writers, agency, gate, lambda: None)["proud"]
        assert row["counts"] == {"own": 60, "close": 50, "other": 70, "no_one": 4, "invalid": 3}
        if gate == "not used":
            assert all("difference" not in cell for cell in row["pairs"].values())
        else:
            assert row["pairs"]["own-other"]["difference"]["value"] == pytest.approx(0.3)
            assert row["pairs"]["close-other"]["difference"]["validDraws"] == 2000
    row = compare(*data(49), "usable", lambda: None)["proud"]
    assert "difference" in row["pairs"]["own-other"]
    assert "difference" not in row["pairs"]["own-close"]


def test_direct_results_preserve_previous_tests_and_exclusions():
    prior = {
        k: {"p": p, "against": False}
        for k, p in (("TP67.1", 0.9), ("TP67.2", None), ("TP67.3", None), ("TP67.analyst", 0.8))
    }
    support = {"TP67.1": False, "TP67.analyst": False}
    rows = compare(*data(), "usable", lambda: None)
    primary = predictions(rows, "usable", prior, support)
    assert primary["TP67.1"]["p"] == 0.9
    assert "Unresolved" in primary["TP67.1"]["verdict"]
    assert primary["TP67.3"]["p"] < 0.01
    assert primary["TP67.2"]["p"] is None
    assert primary["TP67.analyst"]["against"]
    assert predictions(rows, "weak", prior, support)["TP67.3"]["p"] is None
    too_few = compare(*data(49), "usable", lambda: None)
    assert predictions(too_few, "usable", prior, support)["TP67.3"]["p"] is None


def test_private_forecast_and_agency_files_join_through_the_normal_readout(tmp_path, monkeypatch):
    import rapid_pride_agency as study
    from rapid_head_check import pin
    from rapid_marks import CHOICES

    def save(path, obj):
        path.write_text(json.dumps(obj), encoding="utf8")
        return pin(path)

    def release(folder, result):
        source = save(folder / "receipt.json", {"result": result})
        save(folder / "complete.json", {"sourceReceiptPin": source})
        save(
            folder / "exit-verification.json",
            dict.fromkeys(
                ("nativeExited", "releaseMatches", "localLeaseAbsent", "sharedLeaseAbsent"), True
            ),
        )
        return source

    frozen, bridge, original, panel, output = (
        tmp_path / s for s in ("frozen", "TP69-a", "TP67-original-a", "TP77-standing-a", "out")
    )
    for path in (frozen, bridge, original, panel, output):
        path.mkdir()
    n = 24850
    ids = [str(i) for i in range(n)]
    artifact = frozen / "ed-profile-forecasts.npz"
    np.savez(artifact, ids=ids)
    manifest = save(frozen / "artifact-manifest.json", {"files": {artifact.name: pin(artifact)}})
    frozen_pin = save(frozen / "receipt.json", {"artifactsPin": manifest})
    monkeypatch.setattr(study, "SOURCE", frozen_pin)
    monkeypatch.setattr(study, "FROZEN", frozen)
    monkeypatch.setattr(study, "ROOT", tmp_path)
    words = np.repeat(
        [*study.WORDS, "other"], [*study.WORDS.values(), n - sum(study.WORDS.values())]
    )
    writers = np.arange(n) % 5
    archive = bridge / "pride-responsibility.npz"
    np.savez(archive, pride=np.zeros(n), word=words, writer=writers)
    bridge_pin = release(bridge, {"futureJoinPin": pin(archive)})
    release(
        original,
        {
            "sourceReceiptPin": bridge_pin,
            "reports": {w: {"total": k} for w, k in study.WORDS.items()},
        },
    )
    marks = np.zeros((n, 4), dtype=np.int8)
    marks[:, 0] = np.arange(n) % 4
    marks[0] = -1
    aligned = panel / "aligned.npz"
    np.savez(
        aligned,
        sources=np.repeat("ed", n),
        ids=[key("ed", i) for i in ids],
        persons=[f"ed:{w}" for w in writers],
        B=marks,
    )
    field = {
        "value": 0.39,
        "CW": "not used",
        "levels": CHOICES["whose"],
        "jointlyValid": n - 3,
        "BOnly": 2,
    }
    release(
        panel,
        {
            "card": "TP77-standing",
            "fields": list(CHOICES),
            "counts": {"ed": n},
            "tables": {k: {"whose": field} for k in ("all", "ed")},
            "privateAlignmentPin": pin(aligned),
        },
    )
    result = study.prepare(output, lambda: None)
    assert result == json.loads((output / "table.json").read_bytes())
    assert result["reports"]["proud"]["counts"]["invalid"] == 1
    assert all(
        "difference" not in pair
        for row in result["reports"].values()
        for pair in row["pairs"].values()
    )
    assert result["sourceReceipts"]["TP69-a"] == bridge_pin
