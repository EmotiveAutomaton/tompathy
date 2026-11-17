"""Pinned, opt-in reader-pack-2 contracts. No model fetch or scientific admission."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..ledger.schema import Model
from ..packet.bottom_box import AnswerKey, Mapping, ReadingId, ReadingScore
from .registry import Aggregation, Encoder, FilePin, License, Sha, local_file, sha256, verify_file


def code_pin():
    root = Path(__file__).parent
    files = [root/n for n in ('v2.py', 'runtime.py', 'run.py', 'trigger.py', 'registry.py', 'aggregate.py')]
    files += [root.parent/'packet'/n for n in ('bottom_box.py', 'names.py')]
    return hashlib.sha256(''.join(sha256(p) for p in files).encode()).hexdigest()


class EncoderV2(Encoder):
    kind: Literal['model2vec', 'sentence-transformers', 'constructed', 'tfidf']


class Component(Model):
    directory: Literal['need', 'features']
    encoder: EncoderV2
    head: FilePin
    labels: list[str]
    token_cap: int = Field(ge=1, le=4096)


class Manifest(Model):
    name: str = Field(pattern=r'^[a-z0-9][a-z0-9-]*$')
    version: Literal['reader-pack-2']
    task: Literal['channel', 'tags', 'scalar', 'gate', 'trigger']
    encoder: EncoderV2
    head: FilePin
    labels: list[str] = Field(min_length=1, max_length=100)
    token_cap: int = Field(ge=1, le=4096)
    neutral: str | None = None
    thresholds: dict[str, float] = Field(default_factory=dict)
    abstention_threshold: float = Field(default=0, ge=0, le=1)
    label_map: dict[str, ReadingId] = Field(default_factory=dict)
    tag_map: dict[str, ReadingId] = Field(default_factory=dict)
    reading_id: ReadingId | None = None
    range: tuple[float, float] | None = None
    unit: str | None = None
    table: FilePin | None = None
    aggregation: Aggregation | None = None
    gate_pin: str | None = None
    label_pin: str | None = None
    trigger_rules: FilePin | None = None
    evidence: FilePin | None = None
    # Owner-approved separate encoders, each bound to its original score head.
    need_head: Component | None = None
    feature_head: Component | None = None
    key: AnswerKey
    score: ReadingScore
    people: dict[str, float]
    floor: dict[str, float]
    nothing_here: dict[str, float | None]
    training: list[License] = Field(min_length=1)
    research_only: bool
    status: Literal['benchmarked', 'research']
    mapping: Mapping
    code_pin: Sha

    @model_validator(mode='after')
    def coherent(self):
        if len(set(self.labels)) != len(self.labels):
            raise ValueError('Duplicate labels')
        if any(not x.commercial_use for x in [self.encoder.license, *self.training]) and not self.research_only:
            raise ValueError('Restricted or unstated license requires research_only')
        if self.research_only and self.status != 'research':
            raise ValueError('Research-only pack requires research status')
        if any(x is not None and not 0 <= x <= 1 for x in self.nothing_here.values()):
            raise ValueError('Invalid nothing-here rate')
        if not set(self.tag_map) <= set(self.labels) or not set(self.label_map) <= set(self.labels):
            raise ValueError('Unknown label mapping')
        if self.task == 'channel':
            if self.neutral not in self.labels or self.neutral in self.label_map:
                raise ValueError('Channel requires an unmapped neutral label')
            if self.status == 'benchmarked' and (self.table is None or self.aggregation is None):
                raise ValueError('Benchmarked channel requires qualified aggregation')
        elif self.aggregation is not None or self.table is not None:
            raise ValueError('Only channels may report corrected shares')
        if self.task in ('tags', 'gate') and (set(self.thresholds) != set(self.labels)
                or any(not 0 <= x <= 1 for x in self.thresholds.values())):
            raise ValueError('Every sigmoid head requires a fixed threshold')
        if self.task in ('gate', 'scalar') and len(self.labels) != 1:
            raise ValueError('Gate and scalar require one head')
        if self.task == 'scalar' and (self.range is None or self.range[0] >= self.range[1]
                or not self.unit or self.reading_id is None):
            raise ValueError('Scalar requires its key range, unit and reading id')
        if self.task == 'trigger' and not all((self.gate_pin, self.need_head, self.feature_head, self.trigger_rules)):
            raise ValueError('Trigger requires pinned component heads, gate and rules')
        return self


@dataclass(frozen=True)
class VerifiedPack:
    root: Path
    manifest: Manifest
    pin: str
    weights: np.ndarray
    bias: np.ndarray
    table: np.ndarray | None = None
    policy: object = None
    components: dict | None = None
    rules: dict | None = None


def linear_head(root, pin, outputs=None):
    with np.load(verify_file(root, pin), allow_pickle=False) as arrays:
        if set(arrays.files) != {'weights', 'bias'}:
            raise ValueError('Unexpected linear head arrays')
        w, b = arrays['weights'], arrays['bias']
    if (w.ndim != 2 or b.shape != (w.shape[0],) or (outputs is not None and w.shape[0] != outputs)
            or not np.isfinite(w).all() or not np.isfinite(b).all()):
        raise ValueError('Invalid linear head')
    w.flags.writeable = b.flags.writeable = False
    return w, b


def verify_encoder(root, encoder):
    for name, pin in encoder.files.items():
        if not name.startswith('encoder/'):
            raise ValueError('Encoder files must live under encoder/')
        verify_file(root, FilePin(file=name, sha256=pin))
    actual = {p.relative_to(root).as_posix() for p in (root/'encoder').rglob('*') if p.is_file()}
    if actual != set(encoder.files):
        raise ValueError('Unpinned encoder files')
    expected = hashlib.sha256(json.dumps(encoder.files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if expected != encoder.sha256:
        raise ValueError('Encoder manifest hash mismatch')
    verify_file(root, FilePin(file=encoder.license.file, sha256=encoder.license.license_sha256))


def load_pack(directory, *, release=False):
    root = Path(directory).resolve()
    if not root.exists():
        return None
    raw = json.loads(local_file(root, 'pack.json').read_text(encoding='utf8'))
    if raw.get('version') == 'reader-pack-1':
        from .registry import load_pack as legacy
        return legacy(root, release=release)
    m = Manifest.model_validate(raw)
    if release and (m.status == 'research' or m.research_only or m.encoder.kind == 'constructed'):
        raise ValueError('Research or constructed reader cannot enter a release')
    if m.code_pin != code_pin():
        raise ValueError('Reader execution code hash mismatch')
    verify_encoder(root, m.encoder)
    if m.evidence is not None:
        verify_file(root, m.evidence)
    for license in [m.encoder.license, *m.training]:
        verify_file(root, FilePin(file=license.file, sha256=license.license_sha256))
    w, b = linear_head(root, m.head, len(m.labels))
    matrix = policy = None
    if m.aggregation is not None:
        from .aggregate import AggregationPolicy, error_table
        a = m.aggregation
        selection = json.loads(verify_file(root, a.selection).read_text(encoding='utf8'))
        if (selection.get('card') != 'TP12' or selection.get('status') != 'complete'
                or selection.get('prior') != a.prior or selection.get('minimum') != a.minimum):
            raise ValueError('Aggregation policy differs from TP12 selection')
        if selection.get('gateReceiptPin') and (not m.gate_pin or selection.get('gatePackPin') != m.gate_pin):
            raise ValueError('Gated aggregation requires its exact gate pack')
        t = json.loads(verify_file(root, m.table).read_text(encoding='utf8'))
        if (t.get('labels') != m.labels or t.get('orientation') != 'key-by-reader'
                or t.get('held_out') is not True or t.get('abstention_threshold') != m.abstention_threshold):
            raise ValueError('Error table differs from held-out channel policy')
        matrix = error_table(np.asarray(t['counts'], float), t['smoothing'])
        if matrix.shape != (len(m.labels), len(m.labels)):
            raise ValueError('Error table shape mismatch')
        policy = AggregationPolicy(a.prior, a.minimum, a.bootstrap, a.seed)
    components, rules = {}, None
    if m.task == 'trigger':
        from types import SimpleNamespace

        from .trigger import validate_rules
        for key, spec, count in (('need', m.need_head, 19), ('features', m.feature_head, 8)):
            if spec.directory != key or len(spec.labels) != count:
                raise ValueError('Composite score-head labels differ')
            component_root = root / spec.directory
            verify_encoder(component_root, spec.encoder)
            hw, hb = linear_head(component_root, spec.head, count)
            components[key] = SimpleNamespace(root=component_root, manifest=spec, weights=hw, bias=hb)
        rules = json.loads(verify_file(root, m.trigger_rules).read_text(encoding='utf8'))
        validate_rules(rules, m.need_head.labels, m.feature_head.labels)
        if not m.research_only or m.status != 'research':
            raise ValueError('Proposed trigger components are research only')
    return VerifiedPack(root, m, f'{m.name}@{sha256(root / "pack.json")}', w, b, matrix, policy, components, rules)
