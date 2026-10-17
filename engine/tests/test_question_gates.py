"""Constructed gate controls, never a production reader admission."""
import json
from datetime import UTC, datetime

import pytest

from tompathy_engine.features.records import Labels
from tompathy_engine.ledger.schema import schema_hash
from tompathy_engine.transcribe.admission import battery, metrics_pass
from tompathy_engine.transcribe.runner import CATALOGUE


class Reader:
    pin = "a" * 64

    def __init__(self, answer):
        self.answer = answer

    def ask(self, question, **kwargs):
        return {"answer": self.answer(json.loads(kwargs["text"]))}


def items(question):
    labels = CATALOGUE["questions"][question]["answers"]
    return [{"id": str(i), "source": "constructed-gate-control", "tags": ["negation", "paraphrase", f"family-{i % 4}"],
             "expected": [labels[i % len(labels)]] if question == "Q10" else labels[i % len(labels)],
             "text": json.dumps([labels[i % len(labels)]] if question == "Q10" else labels[i % len(labels)]),
             "crosscheck": [labels[i % len(labels)]] if question == "Q10" else labels[i % len(labels)]}
            for i in range(200)]


def require(receipt):
    return Labels(domain="writing", until=datetime(2026, 1, 1, tzinfo=UTC), transcriber_pin=Reader.pin,
                  ledger_schema_hash=schema_hash(), question_records={receipt["question_id"]: receipt}, labels={}).require(receipt["question_id"])


@pytest.mark.parametrize("question", CATALOGUE["questions"])
def test_constant_fails_both_gates_even_with_forged_pass_flag(question):
    data = items(question)
    receipt = battery(Reader(lambda _: data[0]["expected"]), question, data)
    assert not receipt["passed"]
    with pytest.raises(ValueError):
        require(receipt | {"passed": True, "status": "admitted"})
    good = battery(Reader(lambda x: x), question, data)
    assert good["passed"] and require(good)


def test_bad_label_invalid_and_missing_family():
    data = items("Q8")
    receipt = battery(Reader(lambda x: "typo" if x == "unclear" else x), "Q8", data)
    assert receipt["accuracy"] > .85 and not receipt["passed"]
    invalid = battery(Reader(lambda _: "not-a-label"), "Q8", data)
    assert invalid["valid_rate"] == invalid["accuracy"] == 0
    data[0]["tags"] = ["negation", "paraphrase"]
    with pytest.raises(ValueError, match="family"):
        battery(Reader(lambda x: x), "Q8", data)


def test_q10_exact_sets_and_tag_recall():
    data = items("Q10")
    for row in data:
        if row["expected"] == ["care"]:
            row.update(expected=["care", "danger"], text='["danger", "care"]', crosscheck=["care", "danger"])
    exact = battery(Reader(lambda x: x), "Q10", data)
    assert exact["passed"] and exact["per_tag"]["care"] == 1
    bad = battery(Reader(lambda x: ["danger"] if "care" in x else x), "Q10", data)
    assert bad["accuracy"] == .9 and bad["per_tag"]["care"] == 0 and not bad["passed"]
    assert not metrics_pass(exact | {"per_family": {}}, "Q10")
    assert not metrics_pass(exact | {"accuracy": float("nan")}, "Q10")


def test_preview_identity_changes_when_gate_evidence_changes():
    from types import SimpleNamespace

    from tompathy_engine.preview.judgments import techniques
    reader = SimpleNamespace(pin="a" * 64, admissions={}, backend=SimpleNamespace())
    before = techniques(reader).identity
    reader.admissions = {"Q1": {"passed": False}}
    failed = techniques(reader).identity
    reader.admissions["Q1"]["passed"] = True
    passed = techniques(reader).identity
    assert len({before, failed, passed}) == 3
    assert techniques(reader).identity == passed
