"""Per-question known-answer battery, isolated from downstream scientific admission."""

from ..ledger.ids import digest
from .runner import validate_answer

BINARY = {"Q1", "Q2", "Q5", "Q7", "Q9"}
CROSSCHECK = {"Q2", "Q5", "Q6"}


def battery(transcriber, question_id, items):
    if len(items) < 200 or len({i["id"] for i in items}) != len(items):
        raise ValueError("Each question needs at least 200 distinct known-answer items")
    tags = set().union(*(set(i.get("tags", [])) for i in items))
    if not {"negation", "paraphrase"} <= tags or any(not i.get("source") for i in items):
        raise ValueError("Battery must retain source, negation and paraphrase coverage")
    valid = correct = checked = agreements = 0
    outcomes = []
    for item in items:
        expected = validate_answer(question_id, {"answer": item["expected"]})
        if question_id in CROSSCHECK and "crosscheck" not in item:
            raise ValueError("This question requires a deterministic cross-check for every item")
        try:
            result = transcriber.ask(
                question_id,
                context=item.get("context", ""),
                text=item["text"],
                before=item.get("before"),
                admission_test=True,
            )
            answer = result["answer"]
            valid += 1
            correct += answer == expected
            if "crosscheck" in item:
                checked += 1
                agreements += answer == validate_answer(question_id, {"answer": item["crosscheck"]})
            outcomes.append({"id": item["id"], "answer": answer, "valid": True})
        except (ValueError, KeyError):
            outcomes.append({"id": item["id"], "valid": False})
    valid_rate, accuracy = valid / len(items), correct / len(items)
    agreement = (
        agreements / len(items)
        if question_id in CROSSCHECK
        else agreements / checked
        if checked
        else None
    )
    passed = (
        valid_rate >= 0.95
        and (question_id not in BINARY or accuracy >= 0.85)
        and (agreement is None or agreement >= 0.8)
    )
    return {
        "admission_id": digest([transcriber.pin, question_id, items]),
        "question_id": question_id,
        "transcriber_pin": transcriber.pin,
        "battery_hash": digest(items),
        "items": len(items),
        "valid_rate": valid_rate,
        "accuracy": accuracy,
        "crosscheck_agreement": agreement,
        "passed": passed,
        "status": "admitted" if passed else "disabled",
        "outcomes": outcomes,
    }
