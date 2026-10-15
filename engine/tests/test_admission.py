import pytest

from tompathy_engine.admission import Admission, Admissions
from tompathy_engine.ledger.schema import schema_hash


def record(**changes):
    data = {
        "admission_id": "constructed-test-only",
        "module": "corrections",
        "status": "admitted",
        "implementation_hash": "a" * 64,
        "ledger_schema_hash": schema_hash(),
        "domain": "writing",
        "ghost_record": "fixture:ghost",
        "sounding_line_record": "fixture:real-gate",
        "ghost_passed": True,
        "real_data_passed": True,
        "explanatory_only": False,
        "notes": "Synthetic software fixture; does not admit any production module",
    }
    return Admission(**(data | changes))


def test_empty_default_and_status_pin_domain_gates():
    assert Admissions().enabled("writing") == []
    for changes in (
        {"status": "inconclusive"},
        {"status": "killed"},
        {"implementation_hash": "b" * 64},
        {"ghost_passed": False},
        {"domain": "chess"},
        {"sounding_line_record": None},
    ):
        gates = Admissions([record(**changes)], implementation="a" * 64)
        with pytest.raises(ValueError):
            gates.require("corrections", "writing")


def test_explanatory_admission_cannot_claim_probability():
    gates = Admissions(
        [record(explanatory_only=True, real_data_passed=False)], implementation="a" * 64
    )
    assert gates.enabled("writing") == ["corrections"]
    with pytest.raises(ValueError, match="Probability"):
        gates.require("corrections", "writing", probability=True)
