"""Constructed causal-model checks; no downloaded models or admission."""
import weakref
from types import SimpleNamespace

import pytest

from tompathy_engine.preview.kv_reader import read_scores, save_scores, segments
from tompathy_engine.preview.readers import LocalReader


def tiny_reader(cache=None, scoring="kv", entropy=False):
    import torch
    from transformers import Qwen2Config, Qwen2ForCausalLM
    torch.set_num_threads(1)
    torch.manual_seed(23)
    reader = LocalReader.__new__(LocalReader)
    reader.torch, reader.device, reader.cache = torch, "cpu", cache
    reader.scoring, reader.entropy = scoring, entropy
    reader.identity = {"fixture": "tiny seeded causal transformer"}
    reader.tokenizer = SimpleNamespace(bos_token_id=0)
    reader.encode = lambda text: {"input_ids": [ord(c) % 29 for c in text], "offset_mapping": [(i, i + 1) for i in range(len(text))]}
    reader.model = Qwen2ForCausalLM(Qwen2Config(vocab_size=29, hidden_size=8, intermediate_size=16,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1, max_position_embeddings=4096)).eval()
    reader.metrics = {"cacheHits": 0, "forwardCalls": 0, "scoreMs": 0., "inputTokens": 0}
    return reader


def test_segments_preserve_minimum_context_and_use_entire_window():
    target = list(range(5100))
    plans = list(segments(target, [], -1))
    assert plans[0] == (0, [-1], target[:2047])
    assert [x for _, _, chunk in plans for x in chunk] == target
    for start, previous, chunk in plans[1:]:
        assert previous == target[start-1024:start]
        assert len(previous) + len(chunk) <= 2048
    assert list(segments([], [], 0)) == []
    assert next(segments([1, 2], list(range(2000)), -1))[1] == list(range(464, 2000))


def test_kv_first_block_parity_cache_replay_and_entropy(tmp_path):
    reader = tiny_reader(tmp_path, entropy=True)
    text = "the answer is in the evidence. " * 85
    fast = reader.score(text)
    reader.scoring, reader.entropy = "window", False
    old = reader.score(text)
    assert max(abs(a["nats"] - b["nats"]) for a, b in zip(fast[:512], old[:512], strict=True)) < .001
    assert len(fast) == len(text) and all(r["entropy"] >= 0 for r in fast)
    reader.scoring, reader.entropy = "kv", True
    calls = reader.metrics["forwardCalls"]
    assert reader.score(text) == fast and reader.metrics["forwardCalls"] == calls
    assert not reader.torch.is_inference_mode_enabled()


def test_segment_replay_after_interruption_and_context_isolation(tmp_path):
    reader = tiny_reader(tmp_path)
    text = "ordinary words " * 210
    iterator = reader.score_chunks(text)
    for _ in range(4):
        next(iterator)
    iterator.close()
    assert reader.metrics["inputTokens"] == 2048
    full = reader.score(text)
    assert len(full) == len(text) and reader.metrics["cacheHits"] == 1
    assert reader.metrics["inputTokens"] == 2048 + 1024 + 1024 + 1024 + len(text) - 3071
    assert reader.score("", "history") == []
    assert reader.score("target", "history") != reader.score("target", "elsewhere")
    def cancelled():
        raise RuntimeError("cancelled")
    with pytest.raises(RuntimeError, match="cancelled"):
        reader.score(text, check=cancelled)


def test_cache_corruption_fails_closed(tmp_path):
    path = tmp_path / "scores.json"
    save_scores(path, "key", [{"nats": 1.}])
    assert read_scores(path, "key", 1) == [{"nats": 1.}]
    assert read_scores(path, "other", 1) is None
    assert read_scores(path, "key", 2) is None
    assert read_scores(path, "key", 1, True) is None
    path.write_text('broken', encoding="utf8")
    assert read_scores(path, "key") is None


@pytest.mark.parametrize("scoring", ["window", "kv"])
@pytest.mark.parametrize("entropy", [False, True])
def test_vocabulary_logits_are_released_between_chunks(scoring, entropy):
    reader = tiny_reader(scoring=scoring, entropy=entropy)
    buffers = []

    def observe_output(model, inputs, output):
        # Starting another forward must not retain the preceding full logits.
        assert all(ref() is None for ref in buffers)
        buffers.append(weakref.ref(output.logits))

    hook = reader.model.register_forward_hook(observe_output)
    try:
        for tokens, _ in reader.score_chunks("bounded memory " * 180):
            assert tokens
            assert all(ref() is None for ref in buffers)
        assert len(buffers) > 4
    finally:
        hook.remove()
