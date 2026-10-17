import json
from typing import ClassVar

import pytest

from tompathy_engine.transcribe.admission import battery
from tompathy_engine.transcribe.backends.local import LocalBackend, gpu_lease
from tompathy_engine.transcribe.cache import Cache
from tompathy_engine.transcribe.runner import Transcriber, validate_answer


class FixtureBackend:
    model_id = "constructed-known-answer@sha256:fixture"
    settings: ClassVar[dict] = {"temperature": 0, "seed": 0}
    calls = 0

    def complete(self, prompt, schema):
        self.calls += 1
        data = json.loads(prompt.split("\nInput data: ", 1)[1])
        return {"text": json.dumps({"answer": "yes" if '"' in data["text"] else "no"})}


def test_cache_pins_and_literal_admission(tmp_path):
    backend = FixtureBackend()
    reader = Transcriber(backend, Cache(tmp_path / "cache.sqlite"))
    with pytest.raises(ValueError, match="disabled"):
        reader.ask("Q5", text='"Hello," she said.')
    first = reader.ask("Q5", text='"Hello," she said.', admission_test=True)
    assert reader.ask("Q5", text='"Hello," she said.', admission_test=True) == first
    assert backend.calls == 1
    with pytest.raises(ValueError):
        validate_answer("Q5", {"answer": "yes", "maker_motive": "care"})
    with pytest.raises(ValueError):
        validate_answer("Q10", {"answer": ["care", "unclear"]})
    assert validate_answer("Q10", {"answer": ["discovery", "care"]}) == ["care", "discovery"]


def test_two_hundred_item_battery_is_per_question_and_model_pin(tmp_path):
    # A constructed transport test; this is not an admission of any language model.
    backend = FixtureBackend()
    cache = Cache(tmp_path / "cache.sqlite")
    reader = Transcriber(backend, cache)
    items = [
        {
            "id": str(i),
            "source": "constructed-dialogue-fixture",
            "tags": ["negation", "paraphrase", f"family-{i % 4}"],
            "text": f'"Item {i} is not missing," she said.' if i % 2 else f"Item {i} exists.",
            "expected": "yes" if i % 2 else "no",
            "crosscheck": "yes" if i % 2 else "no",
        }
        for i in range(200)
    ]
    receipt = battery(reader, "Q5", items)
    assert receipt["passed"] and receipt["valid_rate"] == 1
    admitted = Transcriber(backend, cache, [receipt])
    assert admitted.ask("Q5", text=items[0]["text"])["answer"] == "no"
    backend.model_id = "different-model"
    with pytest.raises(ValueError, match="disabled"):
        admitted.ask("Q5", text=items[0]["text"])
    with pytest.raises(ValueError, match="200"):
        battery(reader, "Q5", items[:199])


def test_local_transport_and_shared_gpu_ownership(tmp_path):
    with pytest.raises(ValueError, match="loopback"):
        LocalBackend(url="https://paid.example", model="m", model_digest="pin")
    lock = tmp_path / ".gpu.lock"
    lock.write_text("12345 another-owner")
    with pytest.raises(FileExistsError), gpu_lease(lock):
        pass
    assert lock.read_text() == "12345 another-owner"
    lock.unlink()
    with gpu_lease(lock):
        assert lock.exists()
    assert not lock.exists()
    with pytest.raises(RuntimeError), gpu_lease(lock):
        raise RuntimeError("unknown server completion")
    assert lock.exists()
