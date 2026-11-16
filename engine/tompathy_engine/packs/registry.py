"""Verify a local reader before loading any weights. No pickle or remote code."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from pydantic import Field, model_validator

from ..ledger.schema import Model
from ..packet.bottom_box import AnswerKey, Mapping, ReadingId, ReadingScore
from .aggregate import AggregationPolicy, error_table

Sha = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


def sha256(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def code_pin():
    root = Path(__file__).parent
    files = [root / n for n in ('registry.py', 'run.py', 'aggregate.py')]
    files += [root.parent / 'packet' / n for n in ('names.py', 'bottom_box.py')]
    return hashlib.sha256(''.join(sha256(p) for p in files).encode()).hexdigest()


class FilePin(Model):
    file: str
    sha256: Sha


class License(Model):
    name: str
    source: str
    license: str = Field(min_length=1)
    license_sha256: Sha
    file: str
    commercial_use: bool


class Encoder(Model):
    id: str
    revision: str
    kind: Literal['model2vec', 'sentence-transformers', 'constructed']
    files: dict[str, Sha] = Field(min_length=1)
    sha256: Sha
    license: License


class Aggregation(Model):
    prior: float = Field(ge=1)
    minimum: int = Field(ge=1)
    bootstrap: int = Field(ge=100, le=10000)
    seed: int
    # TP12's actual selection receipt, not a guessed prior/minimum.
    selection: FilePin


class Manifest(Model):
    name: str = Field(pattern=r'^[a-z0-9][a-z0-9-]*$')
    version: Literal['reader-pack-1']
    task: Literal['channel']
    labels: list[str] = Field(min_length=2, max_length=100)
    neutral: str
    encoder: Encoder
    head: FilePin
    table: FilePin
    token_cap: int = Field(ge=1, le=4096)
    abstention_threshold: float = Field(ge=0, le=1)
    unread_share: float = Field(ge=0, le=1)
    key: AnswerKey
    score: ReadingScore
    people: dict[str, float]
    floor: dict[str, float]
    nothing_here: dict[str, float | None]
    training: list[License] = Field(min_length=1)
    research_only: bool
    code_pin: Sha
    aggregation: Aggregation
    label_map: dict[str, ReadingId]
    mapping: Mapping
    status: Literal['benchmarked']

    @model_validator(mode='after')
    def coherent(self):
        if len(set(self.labels)) != len(self.labels) or self.neutral not in self.labels:
            raise ValueError('Labels must be unique and include neutral')
        if not set(self.label_map) <= set(self.labels) - {self.neutral}:
            raise ValueError('Unknown or neutral label mapping')
        licenses = [self.encoder.license, *self.training]
        if any(not item.commercial_use for item in licenses) and not self.research_only:
            raise ValueError('Restricted or unstated license requires research_only')
        if any(v is not None and not 0 <= v <= 1 for v in self.nothing_here.values()):
            raise ValueError('Invalid nothing-here rate')
        return self


def local_file(root, name):
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Pack file missing or outside its directory: {name}')
    return path


def verify_file(root, pin):
    path = local_file(root, pin.file)
    if sha256(path) != pin.sha256:
        raise ValueError(f'Pack hash mismatch: {pin.file}')
    return path


@dataclass(frozen=True)
class VerifiedPack:
    root: Path
    manifest: Manifest
    pin: str
    weights: np.ndarray
    bias: np.ndarray
    table: np.ndarray
    policy: AggregationPolicy


def load_pack(directory, *, release=False):
    root = Path(directory).resolve()
    if not root.exists():
        return None
    manifest_file = local_file(root, 'pack.json')
    m = Manifest.model_validate_json(manifest_file.read_text(encoding='utf8'))
    if release and (m.research_only or m.encoder.kind == 'constructed'):
        raise ValueError('Research-only or constructed reader cannot enter a release')
    if m.code_pin != code_pin():
        raise ValueError('Reader execution code hash mismatch')
    for name, pin in m.encoder.files.items():
        if not name.startswith('encoder/'):
            raise ValueError('Encoder files must live under encoder/')
        verify_file(root, FilePin(file=name, sha256=pin))
    actual = {p.relative_to(root).as_posix() for p in (root/'encoder').rglob('*') if p.is_file()}
    if actual != set(m.encoder.files):
        raise ValueError('Unpinned encoder files')
    for license in [m.encoder.license, *m.training]:
        verify_file(root, FilePin(file=license.file, sha256=license.license_sha256))
    encoder_pin = hashlib.sha256(json.dumps(m.encoder.files, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    if encoder_pin != m.encoder.sha256:
        raise ValueError('Encoder manifest hash mismatch')
    selection = json.loads(verify_file(root, m.aggregation.selection).read_text(encoding='utf8'))
    if (selection.get('status') != 'complete' or selection.get('card') != 'TP12'
            or selection.get('prior') != m.aggregation.prior
            or selection.get('minimum') != m.aggregation.minimum):
        raise ValueError('Aggregation policy differs from TP12 selection')
    table = json.loads(verify_file(root, m.table).read_text(encoding='utf8'))
    if (table.get('labels') != m.labels or table.get('orientation') != 'key-by-reader'
            or table.get('abstention_threshold') != m.abstention_threshold
            or table.get('held_out') is not True):
        raise ValueError('Error table labels, orientation or held-out policy mismatch')
    counts = np.asarray(table['counts'], float)
    matrix = error_table(counts, table['smoothing'])
    if matrix.shape != (len(m.labels), len(m.labels)):
        raise ValueError('Error table shape mismatch')
    with np.load(verify_file(root, m.head), allow_pickle=False) as head:
        if set(head.files) != {'weights', 'bias'}:
            raise ValueError('Unexpected head arrays')
        w, b = head['weights'], head['bias']
    if (w.ndim != 2 or w.shape[0] != len(m.labels) or b.shape != (len(m.labels),)
            or not np.isfinite(w).all() or not np.isfinite(b).all()):
        raise ValueError('Invalid linear head')
    for a in (w, b, matrix):
        a.flags.writeable = False
    return VerifiedPack(root, m, f'{m.name}@{sha256(manifest_file)}', w, b, matrix,
        AggregationPolicy(m.aggregation.prior, m.aggregation.minimum,
                          m.aggregation.bootstrap, m.aggregation.seed))
