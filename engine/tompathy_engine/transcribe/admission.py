"""Per-question known-answer battery, isolated from downstream scientific admission."""

import json
import math
from collections import defaultdict
from contextlib import nullcontext

from ..ledger.ids import digest
from .runner import validate_answer

BINARY = {"Q1", "Q2", "Q5", "Q7", "Q9"}
CROSSCHECK = {"Q2", "Q5", "Q6"}


def metrics_pass(record, question_id):
    """Shared fail-closed receipt gate; old aggregate-only receipts cannot admit."""
    def rate(value, floor):
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and floor <= value <= 1

    def rates(value, floor):
        return isinstance(value, dict) and bool(value) and all(rate(v, floor) for v in value.values())

    agreement = record.get("crosscheck_agreement")
    return (
        rate(record.get("valid_rate"), .95)
        and rate(record.get("accuracy"), .85)
        and rates(record.get("per_label"), .70)
        and rates(record.get("per_family"), .70)
        and all(isinstance(k, str) and k.startswith("family-") for k in record["per_family"])
        and rate(record.get("best_constant"), 0)
        and record["accuracy"] >= record["best_constant"] + .10
        and (question_id != "Q10" or rates(record.get("per_tag"), .70))
        and (agreement is None and question_id not in CROSSCHECK or rate(agreement, .80))
    )


def battery(transcriber, question_id, items):
    backend = getattr(transcriber, "backend", None)
    with backend.session() if hasattr(backend, "session") else nullcontext():
        return _battery(transcriber, question_id, items)


def _battery(transcriber, question_id, items):
    if len(items) < 200 or len({i["id"] for i in items}) != len(items):
        raise ValueError("Each question needs at least 200 distinct known-answer items")
    tags = set().union(*(set(i.get("tags", [])) for i in items))
    if not {"negation", "paraphrase"} <= tags or any(not i.get("source") for i in items):
        raise ValueError("Battery must retain source, negation and paraphrase coverage")
    families = [[t for t in i.get("tags", []) if t.startswith("family-")] for i in items]
    if any(len(f) != 1 for f in families):
        raise ValueError("Every battery item needs exactly one family-N tag")
    # Validate the entire battery before any expensive model calls.
    expected_answers = [validate_answer(question_id, {"answer": i["expected"]}) for i in items]
    crosschecks = []
    for item in items:
        if question_id in CROSSCHECK and "crosscheck" not in item:
            raise ValueError("This question requires a deterministic cross-check for every item")
        crosschecks.append(validate_answer(question_id, {"answer": item["crosscheck"]})
                           if "crosscheck" in item else None)
    valid = correct = agreements = 0
    checked = sum(value is not None for value in crosschecks)
    labels, family_scores, tag_scores = defaultdict(list), defaultdict(list), defaultdict(list)
    outcomes = []
    for item, expected, family, crosscheck in zip(items, expected_answers, families, crosschecks):
        answer = None
        is_valid = False
        try:
            result = transcriber.ask(
                question_id,
                context=item.get("context", ""),
                text=item["text"],
                before=item.get("before"),
                admission_test=True,
            )
            answer = validate_answer(question_id, {"answer": result["answer"]})
            is_valid = True
            valid += 1
            correct += answer == expected
            if crosscheck is not None:
                agreements += answer == crosscheck
            outcomes.append({"id": item["id"], "answer": answer, "valid": True})
        except (ValueError, KeyError):
            outcomes.append({"id": item["id"], "valid": False})
        labels[json.dumps(expected, sort_keys=True)].append(is_valid and answer == expected)
        family_scores[family[0]].append(is_valid and answer == expected)
        if question_id == "Q10":
            for tag in expected:
                tag_scores[tag].append(is_valid and tag in answer)
    valid_rate, accuracy = valid / len(items), correct / len(items)
    agreement = (
        agreements / len(items)
        if question_id in CROSSCHECK
        else agreements / checked
        if checked
        else None
    )
    record = {
        "admission_id": digest([transcriber.pin, question_id, items]),
        "question_id": question_id,
        "transcriber_pin": transcriber.pin,
        "battery_hash": digest(items),
        "items": len(items),
        "valid_rate": valid_rate,
        "accuracy": accuracy,
        "crosscheck_agreement": agreement,
        "per_label": {k: sum(v) / len(v) for k, v in labels.items()},
        "per_family": {k: sum(v) / len(v) for k, v in family_scores.items()},
        "best_constant": max(map(len, labels.values())) / len(items),
        "per_tag": {k: sum(v) / len(v) for k, v in tag_scores.items()} if question_id == "Q10" else None,
        "scope": "lab-tested on templated items",
        "outcomes": outcomes,
    }
    passed = metrics_pass(record, question_id)
    return record | {"passed": passed, "status": "admitted" if passed else "disabled"}
