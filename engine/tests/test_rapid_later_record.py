"""Constructed checks for the fixed TP67 scale and for the later aggregate delivery path."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import rapid_family
import rapid_later_record as record
from rapid_head_check import pin, read
from rapid_land import put
from rapid_pride_scale import scaled


def test_standardization_uses_the_same_eligible_people_in_each_draw():
    x = np.array([1.0, 3.0, 4.0, 7.0, 90.0])
    writers = np.array([5, 5, 9, 12, 17])
    left = np.array([True, False, False, True, False])
    right = np.array([False, True, True, False, False])
    weights = np.array([[1.0, 1.0, 1.0], [1.0, 2.0, 0.0]])
    raw, sd, z = scaled(x, writers, left, right, weights)
    assert np.allclose(raw, [0.5, 1.0 - 11.0 / 3])
    assert np.allclose(sd, [np.std([1, 3, 4, 7]), np.std([1, 3, 4, 4])])
    assert np.allclose(raw / sd, z)


def test_completed_return_is_source_bound_and_private_fields_stay_local(monkeypatch):
    packet = Path(__file__).resolve().parents[2] / rapid_family.PACKET
    with TemporaryDirectory(dir=Path.cwd()) as directory, monkeypatch.context() as m:
        m.chdir(directory)
        m.setattr(rapid_family, "PACKET", packet)
        root = Path("private")
        m.setattr(record, "ROOT", root)
        test_sheet = Path("docs/exchange/result-sheets/TP67.md")
        test_sheet.parent.mkdir(parents=True)
        test_sheet.write_text("# TP67\n", encoding="utf8")
        record.STATUS.write_text("# Status\n", encoding="utf8")
        record.SCOREBOARD.write_text("# Scoreboard\n", encoding="utf8")
        record.RETURN.write_text(
            "Before\n\n## Registered predictions\n\n| TP67 · Whose rise | Pending | Protocol |\n",
            encoding="utf8",
        )
        put(root / "TP78-measurements.json", {})

        def terminal(stage, result):
            folder = root / (stage + "-a")
            put(
                folder / "receipt.json",
                {
                    "at": "2026-11-27T18:00:00+00:00",
                    "status": "complete",
                    "card": stage,
                    "result": result,
                },
            )
            h = pin(folder / "receipt.json")
            put(folder / "complete.json", {"sourceReceiptPin": h})
            put(
                folder / "exit-verification.json",
                {
                    k: True
                    for k in (
                        "nativeExited",
                        "releaseMatches",
                        "sharedLeaseAbsent",
                        "localLeaseAbsent",
                    )
                },
            )
            put(folder / "table.json", result)
            return h

        words = {
            "proud": {"own": 20, "other": 20, "invalid": 2, "ties": 8, "reason": "Below minimum"}
        }
        h = terminal(
            "TP67-original",
            {
                "card": "TP67-original",
                "sourceReceiptPin": "b" * 64,
                "reports": words,
                "draws": 2000,
                "scope": "Constructed",
                "productionAdmission": False,
                "privateRow": "never-export-this-value",
            },
        )
        terminal(
            "TP67-scale",
            {
                "card": "TP67-scale",
                "inputReceiptPin": h,
                "words": {"proud": {"reason": "Below minimum"}},
                "scale": "Within word",
                "draws": 2000,
            },
        )
        state = {
            "checkedAt": "2026-11-27T18:00:00+00:00",
            "spark": {"state": "running", "job": "Q27"},
            "workstation": {"gpu": {"state": "running", "job": "G12"}, "card": None},
        }
        proof = record.file_card("TP67-original", state)
        assert proof == record.file_card("TP67-original", state)
        public = read(Path(proof["public"]))
        assert public["sourceReceiptPin"] == h and public["inputReceiptPin"] == "b" * 64
        assert (
            "privateRow" not in public
            and len((record.PUBLIC / "EVIDENCE_LEDGER.jsonl").read_text("utf8").splitlines()) == 1
        )
        p = root / "TP67-original-a/table.json"
        p.write_text("{}", encoding="utf8")
        with pytest.raises(ValueError, match="source table"):
            record.source_result("TP67-original")


def test_registered_direction_and_missing_comparisons():
    def cell(value, low, high, near=False):
        return {"value": value, "interval": [low, high], "nearBar": near, "pAboveBar": 0.01}

    positive = cell(0.32, 0.22, 0.42)
    negative = cell(-0.34, -0.42, -0.26)
    near = cell(0.03, 0.001, 0.07, True)
    assert [record.direction(x) for x in (positive, negative, near, {})] == [1, -1, 0, 0]
    blend = {
        "unfittedBlend": {
            "rank": 8,
            "againstBestOtherPair": negative,
            "againstBetterSingle": positive,
        },
        "leadOverCovered": positive,
        "firstLastPlay": {"embarrassed": positive, "ashamed": near},
        "dedicatedVsFittedPair": {"dedicatedMinusPair": positive},
    }
    _, _, predictions, _, _ = record.blend(blend)
    assert predictions["TP68.1"]["against"] and predictions["TP68.2"]["p"] == 0.01
    empty = {"reason": "Unmatched"}
    loss = {
        "sources": {
            s: {"comparisons": {k: empty for k in ("sadnessMinusFear", "sadnessMinusRage")}}
            for s in ("ed", "envent")
        }
    }
    _, _, predictions, _, _ = record.loss(loss)
    assert predictions["TP66.analyst"]["p"] is None
    assert not predictions["TP66.analyst"]["against"]
