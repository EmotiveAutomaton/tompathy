"""Optional bounded KV scoring. A rebuild never reuses position-shifted KV states.

The first block matches the old path. BOS stays until the first rebuild. Thereafter
rebuild from exactly 1,024 preceding tokens, within the existing 2,048-token ceiling.
With this ceiling and minimum context, a full cache leaves the maximum 1,024 new
tokens per rebuild. Partial blocks fill the ceiling instead of wasting its tail.
Completed segments cache losses, not private model state, under new namespaces.
"""

import json
import math
from time import monotonic

from ..ledger.ids import digest

TEXT_SCHEME = "surface-kv-v1-window2048-context1024"
WINDOW_SCHEME = "surface-kv-segment-v1"


def segments(target, prefix, bos):
    start = 0
    while start < len(target):
        previous = prefix[-1536:] if start == 0 else (prefix[-(1024 - start):] if start < 1024 else []) + target[max(0, start - 1024):start]
        previous = previous or [bos]
        count = min(2048 - len(previous), len(target) - start)
        yield start, previous, target[start:start + count]
        start += count


def read_scores(path, key, count=None, entropy=False):
    if not path or not path.exists() or path.stat().st_size > 32_000_000:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf8"))
        rows = value["scores"]
        if value["key"] != key or value["sha256"] != digest(rows) or not isinstance(rows, list):
            return None
        if count is not None and len(rows) != count:
            return None
        fields = ["nats", "entropy"] if entropy else ["nats"]
        if any(any(type(row.get(f)) not in (int, float) or not math.isfinite(row[f]) or row[f] < 0 for f in fields) for row in rows):
            return None
        return rows
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def save_scores(path, key, rows):
    if path:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"key": key, "sha256": digest(rows), "scores": rows}), encoding="utf8")
        temporary.replace(path)


def score_chunks(reader, text, context, check):
    check()
    entropy = getattr(reader, "entropy", False)
    key = digest([TEXT_SCHEME, reader.identity, entropy, text, context])
    path = reader.cache / f"{key}.json" if reader.cache else None
    saved = read_scores(path, key, entropy=entropy)
    if saved is not None:
        reader.metrics["cacheHits"] += 1
        yield saved, True
        return
    encoded = reader.encode(text)
    target, offsets = encoded["input_ids"], encoded["offset_mapping"]
    prefix = (context if isinstance(context, list) else reader.encode(context)["input_ids"])[-2047:]
    bos = reader.tokenizer.bos_token_id
    if bos is None:
        bos = reader.tokenizer.eos_token_id
    if bos is None:
        raise ValueError("Reader has no beginning-of-text token")
    out, torch = [], reader.torch
    for start, previous, chunk in segments(target, prefix, bos):
        check()
        window_key = digest([WINDOW_SCHEME, reader.identity, entropy, previous, chunk])
        window = reader.cache / f"window-{window_key}.json" if reader.cache else None
        rows = read_scores(window, window_key, len(chunk), entropy)
        if rows is not None:
            reader.metrics["cacheHits"] += 1
            for i, row in enumerate(rows, start):
                a, b = offsets[i]
                if b > a:
                    out.append({"start": a, "end": b, **row})
            yield list(out), start + len(chunk) == len(target)
            continue
        past, following, rows = None, None, []
        for local in range(0, len(chunk), 512):
            check()
            block = chunk[local:local + 512]
            ids = previous + block if local == 0 else block
            started = monotonic()
            with torch.inference_mode():
                tensor = torch.tensor([ids], dtype=torch.long, device=reader.device)
                # Include one final logit to predict the next block's first token.
                first = len(previous) - 1 if local == 0 else 0
                positions = torch.arange(first, len(ids), device=reader.device)
                result = reader.model(tensor, past_key_values=past, use_cache=True, logits_to_keep=positions)
                logits = result.logits[0].float()
                predictions = logits[:-1] if local == 0 else torch.cat([following, logits[:-1]], dim=0)
                # A view of the last row would retain all vocabulary logits
                # while the generator yields and during the next forward pass.
                following, past = logits[-1:].clone(), result.past_key_values
                losses = torch.nn.functional.cross_entropy(predictions, torch.tensor(block, device=reader.device), reduction="none").tolist()
                entropies = None
                if entropy:
                    logp = torch.log_softmax(predictions, dim=-1)
                    entropies = -(logp.exp() * logp).sum(dim=-1)
                    entropies = entropies.tolist()
                    del logp
                del predictions, logits, result, tensor, positions
            reader.metrics["forwardCalls"] += 1
            reader.metrics["inputTokens"] += len(ids)
            reader.metrics["scoreMs"] += (monotonic() - started) * 1000
            for j, loss in enumerate(losses):
                row = {"nats": loss}
                if entropy:
                    row["entropy"] = entropies[j]
                rows.append(row)
                a, b = offsets[start + local + j]
                if b > a:
                    out.append({"start": a, "end": b, **row})
            check()
            if local + len(block) == len(chunk):
                save_scores(window, window_key, rows)
            yield list(out), start + local + len(block) == len(target)
        # The next segment starts a fresh positional history.
        del past, following
    save_scores(path, key, out)
    if not target:
        yield [], True
