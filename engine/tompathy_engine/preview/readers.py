"""Hash-pinned CPU readers. Loading/scoring never performs network access."""

import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from time import monotonic

from ..ledger.ids import digest

MODELS = {"qwen": "Qwen/Qwen2.5-0.5B", "smol": "HuggingFaceTB/SmolLM2-360M", "smol-small": "HuggingFaceTB/SmolLM2-135M"}


def file_hash(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def install(directory, model, revision=None):
    """Only called by the explicit install-reader CLI, never by analysis."""
    from huggingface_hub import HfApi, snapshot_download

    name = MODELS[model]
    pin = HfApi().model_info(name, revision=revision).sha
    root = Path(directory) / model
    if (root / "manifest.json").exists():
        raise ValueError("Reader already installed; use a new directory for a different pin")
    snapshot_download(name, revision=pin, local_dir=root,
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.tiktoken"])
    files = {p.relative_to(root).as_posix(): file_hash(p) for p in sorted(root.glob("*")) if p.is_file()}
    manifest = {"model": name, "revision": pin, "files": files}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    return {"directory": str(root), "model": name, "revision": pin, "sha256": digest(manifest)}


class LocalReader:
    def __init__(self, directory, cache=None, device="cpu", threads=1, precision="int8"):
        started = monotonic()
        self.directory, self.cache = Path(directory), Path(cache) if cache else None
        self.manifest = json.loads((self.directory / "manifest.json").read_text(encoding="utf8"))
        if self.manifest["model"] not in MODELS.values() or not self.manifest["files"]:
            raise ValueError("Unrecognized preview reader")
        actual = {p.name for p in self.directory.iterdir() if p.is_file() and p.name != "manifest.json"}
        if actual != set(self.manifest["files"]) or not {"config.json", "tokenizer.json", "model.safetensors"} <= actual:
            raise ValueError("Reader manifest must pin every local model/tokenizer file")
        for name, expected in self.manifest["files"].items():
            path = (self.directory / name).resolve()
            if not path.is_relative_to(self.directory.resolve()) or file_hash(path) != expected:
                raise ValueError("Preview reader file hash mismatch")
        import torch
        import transformers

        if device not in {"cpu", "cuda"}:
            raise ValueError("Choose cpu or explicitly assign cuda")
        if device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA was requested but is unavailable; no silent backend fallback")
        self.device = device
        # CPU is the default; CUDA requires the explicit service flag.
        if not 1 <= threads <= 16 or precision not in {"int8", "int8-channel", "float32"}:
            raise ValueError("Reader threads must be 1–16 and precision int8, int8-channel or float32")
        torch.set_num_threads(threads)
        self.torch = torch
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.directory, local_files_only=True, trust_remote_code=False)
        if not self.tokenizer.is_fast:
            raise ValueError("Preview scoring requires a tokenizer with source offsets")
        self.model = transformers.AutoModelForCausalLM.from_pretrained(self.directory, local_files_only=True, trust_remote_code=False,
                                                                     dtype=torch.float32 if device == "cpu" else torch.float16, use_safetensors=True).eval().to(device)
        if device == "cpu" and precision != "float32":
            config = {torch.nn.Linear: torch.ao.quantization.per_channel_dynamic_qconfig} if precision == "int8-channel" else {torch.nn.Linear}
            self.model = torch.ao.quantization.quantize_dynamic(self.model, config, dtype=torch.qint8)
        label = {"int8": "dynamic-int8 linear, float32 embeddings", "int8-channel": "per-channel dynamic-int8 linear, float32 embeddings", "float32": "float32"}[precision]
        backend = f"CPU {label}, {threads} thread{'s' if threads != 1 else ''}" if device == "cpu" else "CUDA float16"
        self.identity = {"id": self.manifest["model"], "revision": self.manifest["revision"], "sha256": digest(self.manifest),
                         "backend": f"torch {torch.__version__}; transformers {transformers.__version__}; {backend}"}
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=True)
        self.encodings = OrderedDict()
        self.encoding_bytes = 0
        self.metrics = {"loadMs": (monotonic() - started) * 1000, "scoreMs": 0.0, "cacheHits": 0, "forwardCalls": 0, "inputTokens": 0}

    def encode(self, text):
        if text in self.encodings:
            self.encodings.move_to_end(text)
            return self.encodings[text]
        encoded = self.tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        size = len(text) * 4 + len(encoded["input_ids"]) * 96
        if size <= 8_000_000:
            while self.encodings and self.encoding_bytes + size > 8_000_000:
                old_text, old = self.encodings.popitem(last=False)
                self.encoding_bytes -= len(old_text) * 4 + len(old["input_ids"]) * 96
            self.encodings[text] = encoded
            self.encoding_bytes += size
        return encoded

    def score(self, text, context="", check=lambda: None):
        result = []
        for result, _ in self.score_chunks(text, context, check):
            pass
        return result

    def score_chunks(self, text, context="", check=lambda: None):
        """Return source character offsets and nats per token, window <= 2048.

        Context and target are tokenized separately so the scored target boundary
        is stable across conditions. First token is conditioned on BOS/EOS when
        context is absent. Long targets advance in 512-token blocks.
        """
        check()
        key = digest(["surface-v1-window2048-chunk512", self.identity, text, context])
        path = self.cache / f"{key}.json" if self.cache else None
        if path and path.exists() and path.stat().st_size <= 32_000_000:
            try:
                saved = json.loads(path.read_text(encoding="utf8"))
            except (ValueError, UnicodeError):
                saved = None
            if isinstance(saved, dict) and saved.get("key") == key and saved.get("sha256") == digest(saved.get("tokens")):
                self.metrics["cacheHits"] += 1
                yield saved["tokens"], True
                return
        encoded = self.encode(text)
        target, offsets = encoded["input_ids"], encoded["offset_mapping"]
        prefix = (context if isinstance(context, list) else self.encode(context)["input_ids"])[-2047:]
        bos = self.tokenizer.bos_token_id
        if bos is None:
            bos = self.tokenizer.eos_token_id
        if bos is None:
            raise ValueError("Reader has no beginning-of-text token")
        out = []
        for start in range(0, len(target), 512):
            check()
            chunk = target[start:start + 512]
            previous = (prefix + target[:start])[-(2048 - len(chunk)):]
            if not previous:
                previous = [bos]
            ids = previous + chunk
            window_key = digest(["surface-window-v1", self.identity, ids, len(previous)])
            window_path = self.cache / f"window-{window_key}.json" if self.cache else None
            losses = None
            if window_path and window_path.exists() and window_path.stat().st_size <= 100_000:
                try:
                    saved = json.loads(window_path.read_text(encoding="utf8"))
                    candidate = saved.get("losses")
                    import math
                    if saved.get("key") == window_key and saved.get("sha256") == digest(candidate) and isinstance(candidate, list) and len(candidate) == len(chunk) and all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in candidate):
                        losses = candidate
                        self.metrics["cacheHits"] += 1
                except (ValueError, UnicodeError):
                    pass
            if losses is not None:
                for index, loss in enumerate(losses, start):
                    a, b = offsets[index]
                    if b > a:
                        out.append({"start": a, "end": b, "nats": loss})
                yield list(out), start + len(chunk) == len(target)
                continue
            started = monotonic()
            with self.torch.inference_mode():
                tensor = self.torch.tensor([ids], dtype=self.torch.long, device=self.device)
                # Avoid projecting the unscored context to the 150k-word vocabulary.
                positions = self.torch.arange(len(previous) - 1, len(ids) - 1, device=self.device)
                logits = self.model(tensor, use_cache=False, logits_to_keep=positions).logits[0].float()
                labels = self.torch.tensor(chunk, dtype=self.torch.long, device=self.device)
                losses = self.torch.nn.functional.cross_entropy(logits, labels, reduction="none").tolist()
            self.metrics["forwardCalls"] += 1
            self.metrics["scoreMs"] += (monotonic() - started) * 1000
            self.metrics["inputTokens"] += len(ids)
            if window_path:
                temporary = window_path.with_suffix(".tmp")
                temporary.write_text(json.dumps({"key": window_key, "losses": losses, "sha256": digest(losses)}), encoding="utf8")
                temporary.replace(window_path)
            for index, loss in enumerate(losses, start):
                a, b = offsets[index]
                if b > a:
                    out.append({"start": a, "end": b, "nats": loss})
            check()
            yield list(out), start + len(chunk) == len(target)
        if path:
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"key": key, "tokens": out, "sha256": digest(out)}), encoding="utf8")
            temporary.replace(path)
        if not target:
            yield [], True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Explicitly download and hash-pin a local preview reader (no analysis is run).")
    parser.add_argument("model", choices=MODELS)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--revision")
    args = parser.parse_args()
    print(json.dumps(install(args.directory, args.model, args.revision), indent=2))


if __name__ == "__main__":
    main()
