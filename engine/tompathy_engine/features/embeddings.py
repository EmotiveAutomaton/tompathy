"""Pinned local encodings; no implicit model download or GPU acquisition."""

import json
from pathlib import Path

import numpy as np

from ..ledger.ids import digest, text_hash


class EmbeddingCache:
    def __init__(self, path, *, model_id, token_cap=128):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.model_id, self.token_cap = model_id, token_cap
        if not model_id or not isinstance(token_cap, int) or token_cap < 1:
            raise ValueError("Embeddings require a model pin and token cap")

    def key(self, text):
        return digest([self.model_id, self.token_cap, text_hash(text)])

    def get(self, text):
        path = self.path / (self.key(text) + ".json")
        if not path.exists():
            return None
        row = json.loads(path.read_text(encoding="utf8"))
        vector = np.asarray(row["vector"], dtype=float)
        if (
            row["key"] != self.key(text)
            or row["hash"] != digest(row["vector"])
            or vector.ndim != 1
            or not len(vector)
            or not np.isfinite(vector).all()
        ):
            raise ValueError("Invalid embedding cache entry")
        return vector

    def put(self, text, vector):
        vector = np.asarray(vector, dtype=float)
        if vector.ndim != 1 or not len(vector) or not np.isfinite(vector).all():
            raise ValueError("Embedding must be a finite vector")
        prior = self.get(text)
        if prior is not None:
            if not np.array_equal(prior, vector):
                raise ValueError("Conflicting pinned embedding")
            return
        value = vector.tolist()
        (self.path / (self.key(text) + ".json")).write_text(
            json.dumps({"key": self.key(text), "vector": value, "hash": digest(value)}),
            encoding="utf8",
        )


def encode_local(texts, cache, *, model_directory):
    path = Path(model_directory)
    if not path.is_dir():
        raise ValueError("Install and pin a local embedding model before encoding")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Local encoding requires the optional research extra") from exc
    model = None
    vectors = []
    for text in texts:
        vector = cache.get(text)
        if vector is None:
            if model is None:
                model = SentenceTransformer(str(path), device="cpu", local_files_only=True)
                model.max_seq_length = cache.token_cap
            vector = model.encode(text, convert_to_numpy=True)
            cache.put(text, vector)
        vectors.append(vector)
    return np.stack(vectors)
