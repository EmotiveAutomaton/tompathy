"""Pinned optional local entity and embedding features, bound to exact inputs."""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ..ledger.ids import digest
from ..ledger.schema import Hash, Model, schema_hash
from .deterministic import cosine
from .embeddings import EmbeddingCache, encode_local
from .records import inputs, subject


def directory_pin(path):
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError("Feature model must be installed locally")
    pins = {}
    for file in sorted(root.rglob("*")):
        if file.is_file():
            with file.open("rb") as stream:
                pins[file.relative_to(root).as_posix()] = hashlib.file_digest(
                    stream, "sha256"
                ).hexdigest()
    if not pins:
        raise ValueError("Feature model directory is empty")
    return digest(pins)


class FeatureRow(Model):
    input_hash: Hash
    values: list[float]


class Features(Model):
    format: Literal["tompathy-features-1"] = "tompathy-features-1"
    domain: str
    until: datetime
    ledger_schema_hash: Hash
    names: list[str] = Field(min_length=1)
    model_pins: dict[str, Hash]
    token_cap: int = Field(default=128, ge=1)
    rows: dict[str, FeatureRow]

    @model_validator(mode="after")
    def dimensions(self):
        if len(set(self.names)) != len(self.names) or not self.model_pins:
            raise ValueError("Feature names and model pins are required")
        if any(len(r.values) != len(self.names) for r in self.rows.values()):
            raise ValueError("Feature vector dimensions disagree")
        return self

    def verify(self, ledger, *, domain, until):
        if self.domain != domain or self.until < until or self.ledger_schema_hash != schema_hash():
            raise ValueError("Feature scope/cutoff/schema mismatch")
        available = inputs(ledger, domain=self.domain, until=self.until, full_context=True)
        for key, row in self.rows.items():
            if key not in available or row.input_hash != digest(available[key]):
                raise ValueError("Optional feature input fingerprint mismatch")

    def values(self, kind, ident, slot):
        row = self.rows.get(subject(kind, ident, slot))
        if row is None:
            raise ValueError("Missing optional local features")
        return row.values


def extract(
    ledger,
    *,
    domain,
    until,
    cache_directory,
    embedding_model=None,
    entity_model=None,
    maximum=10000,
    progress=lambda _: None,
):
    if not embedding_model and not entity_model:
        raise ValueError("Choose at least one installed local feature model")
    source = inputs(ledger.snapshot(), domain=domain, until=until, full_context=True)
    if not 1 <= maximum <= 100000 or len(source) > maximum:
        raise ValueError("Optional feature extraction exceeds the explicit bound")
    names, pins, nlp, embeddings = [], {}, None, None
    if entity_model:
        import spacy

        pins["entities"] = directory_pin(entity_model)
        nlp = spacy.load(entity_model)
        names += ["entities", "new_entities"]
    if embedding_model:
        pins["embeddings"] = directory_pin(embedding_model)
        embeddings = EmbeddingCache(cache_directory, model_id=pins["embeddings"], token_cap=128)
        names += ["embedding_last_sentence", "embedding_document"]
    encoded = {}
    if embeddings:
        texts = set()
        for data in source.values():
            if max(len(data["text"]), len(data["context"])) > 200000:
                raise ValueError("Feature input exceeds bound; no silent truncation")
            texts.update(
                [
                    data["text"],
                    data["context"],
                    re.split(r"(?<=[.!?])\s+", data["context"].strip())[-1],
                ]
            )
        ordered = sorted(texts)
        if ordered:
            encoded = dict(
                zip(
                    ordered,
                    encode_local(ordered, embeddings, model_directory=embedding_model),
                    strict=True,
                )
            )
    rows = {}
    for key, data in source.items():
        progress("Extracting pinned local features")
        text, context = data["text"], data["context"]
        if max(len(text), len(context)) > 200000:
            raise ValueError("Feature input exceeds bound; no silent truncation")
        values = []
        if nlp:
            seen = {e.text.casefold() for e in nlp(context).ents}
            found = [e.text.casefold() for e in nlp(text).ents]
            values += [float(len(found)), float(sum(e not in seen for e in found))]
        if embeddings:
            sentences = re.split(r"(?<=[.!?])\s+", context.strip())
            vectors = [encoded[t] for t in (text, sentences[-1], context)]
            values += [cosine(vectors[0], vectors[1]), cosine(vectors[0], vectors[2])]
        rows[key] = FeatureRow(input_hash=digest(data), values=values)
    return Features(
        domain=domain,
        until=until,
        ledger_schema_hash=schema_hash(),
        names=names,
        model_pins=pins,
        rows=rows,
    )
