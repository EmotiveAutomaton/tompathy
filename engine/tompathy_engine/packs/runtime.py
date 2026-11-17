"""TS3 multi-pack execution: explicit research, shared vectors, gate first."""
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np

from ..packet.bottom_box import BottomBoxV2, empty_bottom_box
from ..preview.surface import SENTENCE
from .aggregate import shares
from .registry import sha256
from .run import Sentence, encoder_for
from .v2 import load_pack


def sentence_rows(text, offset=0):
    """Use the existing surface reader splitter, retaining exact UTF-16 spans."""
    rows = []
    for match in SENTENCE.finditer(text):
        raw = match.group()
        start = match.start() + len(raw) - len(raw.lstrip())
        end = match.end() - len(raw) + len(raw.rstrip())
        if start < end:
            rows.append(Sentence(text[start:end], offset + len(text[:start].encode('utf-16-le'))//2,
                                 offset + len(text[:end].encode('utf-16-le'))//2))
    return rows


def windows(rows, cap, count):
    """Whole consecutive sentences; singleton over-cap sentences use model truncation.

    Advance by the first sentence boundary at/after half the current token window.
    This does not invent sub-sentence exposure from a truncated long sentence.
    """
    result, start = [], 0
    while start < len(rows):
        end = start + 1
        while end < len(rows) and count(' '.join(r.text for r in rows[start:end+1])) <= cap:
            end += 1
        selected = rows[start:end]
        result.append(Sentence(' '.join(r.text for r in selected), selected[0].start, selected[-1].end))
        if end == len(rows):
            break
        total = count(result[-1].text)
        step = 1
        while start+step < end and count(' '.join(r.text for r in rows[start:start+step])) < total/2:
            step += 1
        start += step
    return result


def reading(pack, ident):
    m = pack.manifest
    return {'id': ident, 'tier': 'on_page', 'share': None, 'events': [], 'series': [],
            'pack': pack.pin, 'key': m.key.model_dump(), 'score': m.score.model_dump(),
            'people': m.people, 'floor': m.floor, 'nothing_here': m.nothing_here,
            'mapping': m.mapping.model_dump(), 'status': m.status}


def run(directories, sentences, *, enabled=False, research=False, adapters=None,
        check=lambda: None, diagnostics=None, cache_directory=None):
    if not enabled:
        return empty_bottom_box()
    packs = [p for d in directories if (p := load_pack(d)) is not None]
    packs = [p for p in packs if research or (p.manifest.status != 'research' and not p.manifest.research_only)]
    if not packs:
        return empty_bottom_box()
    if len({p.pin for p in packs}) != len(packs):
        raise ValueError('Duplicate pack')
    rows = list(sentences)
    last = 0
    for row in rows:
        if (not row.text.strip() or row.start < last or row.end <= row.start
                or row.end-row.start != len(row.text.encode('utf-16-le'))//2):
            raise ValueError('Sentences need ordered, exact UTF-16 spans')
        last = row.end
    box = {'version': 'bottom-box-2', 'on_page': [], 'about_maker': [], 'toolbox': []}
    if not rows:
        return box
    started = time.perf_counter()
    adapters = adapters or {}
    encoders, caches = {}, {}
    cache_protocol = {'encoderExecutionPin': sha256(Path(__file__).with_name('run.py')),
        'packages': {name: importlib.metadata.version(name) for name in ('numpy', 'torch', 'transformers', 'sentence-transformers', 'scikit-learn')}} if cache_directory is not None else None

    def encoder(pack):
        m = pack.manifest
        key = (m.encoder.sha256, m.token_cap)
        if key not in encoders:
            if m.encoder.sha256 in adapters:
                if m.encoder.kind != 'constructed':
                    raise ValueError('A real encoder cannot be replaced by a test adapter')
                encoders[key] = adapters[m.encoder.sha256]
            else:
                encode = encoder_for(pack)
                if m.encoder.kind == 'tfidf':
                    encoders[key] = (encode, lambda text: len(text.split()))
                else:
                    # Scalar token accounting uses this encoder's actual tokenizer.
                    from transformers import AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(str(pack.root/'encoder'),
                        local_files_only=True, trust_remote_code=False)
                    encoders[key] = (encode, lambda text: len(tokenizer.encode(text, add_special_tokens=True)))
            caches[key] = {}
        return key, encoders[key]

    def vectors(pack, items):
        key, (encode, _) = encoder(pack)
        cache = caches[key]
        missing = list(dict.fromkeys(r.text for r in items if r.text not in cache))
        def disk_path(text):
            identity = hashlib.sha256(json.dumps([key, cache_protocol, text], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            return Path(cache_directory)/(identity+'.npz')
        if cache_directory is not None:
            Path(cache_directory).mkdir(parents=True, exist_ok=True)
            for text in missing:
                path = disk_path(text)
                if path.exists():
                    check()
                    with np.load(path, allow_pickle=False) as d:
                        value = d['vector']
                        if str(d['identity']) != path.stem or value.shape != (pack.weights.shape[1],) or not np.isfinite(value).all():
                            raise ValueError('Durable reader vector differs')
                        cache[text] = value
            missing = [t for t in missing if t not in cache]
        for start in range(0, len(missing), 16):
            check()
            batch = missing[start:start+16]
            value = np.asarray(encode(batch))
            if value.shape != (len(batch), pack.weights.shape[1]) or not np.isfinite(value).all():
                raise ValueError('Invalid encoder output')
            cache.update(zip(batch, value))
            if cache_directory is not None:
                for text, row in zip(batch, value):
                    path = disk_path(text)
                    np.savez(path, identity=path.stem, vector=row)
        return np.asarray([cache[r.text] for r in items])

    def probabilities(pack, items):
        logits = vectors(pack, items) @ pack.weights.T + pack.bias
        if pack.manifest.task == 'channel':
            p = np.exp(logits-logits.max(axis=1, keepdims=True))
            return p/p.sum(axis=1, keepdims=True)
        return 1/(1+np.exp(-np.clip(logits, -700, 700)))

    gates = [p for p in packs if p.manifest.task == 'gate']
    accepted = np.ones(len(rows), bool) if gates else np.zeros(len(rows), bool)
    for pack in gates:
        m = pack.manifest
        accepted &= probabilities(pack, rows)[:, 0] >= m.thresholds[m.labels[0]]
    selected = [r for r, ok in zip(rows, accepted) if ok]
    for pack in packs:
        m = pack.manifest
        if m.task == 'gate' or m.task == 'scalar' or not selected:
            continue
        if m.task == 'trigger':
            from .trigger import CHANNELS, slots, stakes, table_scores
            if m.gate_pin not in {p.pin for p in gates}:
                raise ValueError('Trigger gate pin is absent')
            label_pack = next((p for p in packs if p.pin == m.label_pin and p.manifest.task == 'channel'), None)
            if m.label_pin is not None and label_pack is None:
                raise ValueError('Trigger label pin is absent')
            components = pack.components
            need, features = (components[k] for k in ('need', 'features'))
            n = vectors(need, selected) @ need.weights.T + need.bias
            f = vectors(features, selected) @ features.weights.T + features.bias
            z, times = slots(f, n, [r.text for r in selected], pack.rules)
            proposed = stakes(f, n, z, times, m.mapping.model_dump())
            table = table_scores(z, pack.rules['tense_qualified']).argmax(axis=1)
            labels = probabilities(label_pack, selected) if label_pack else None
            grouped = {}
            for i, row in enumerate(selected):
                if label_pack:
                    best = int(labels[i].argmax())
                    ident = label_pack.manifest.label_map.get(label_pack.manifest.labels[best])
                    confidence = float(labels[i, best])
                    if confidence < label_pack.manifest.abstention_threshold:
                        continue
                else:
                    ident = CHANNELS[table[i]] if pack.rules['table_qualified'] else None
                    confidence = 1.0  # A deterministic rule assignment, not a calibrated probability.
                if ident is None:
                    continue  # Standalone need tags carry the remaining events.
                event = {'span': [row.start, row.end], 'label': ident, 'confidence': confidence,
                         'who': 'unclear', 'words': []}
                if pack.rules['stakes_qualified']:
                    event['stake'] = proposed[i]
                    if not pack.rules['tense_qualified']:
                        event['stake']['when'] = 'any'
                if pack.rules['table_qualified']:
                    event['channel_by_table'] = {'channel': CHANNELS[table[i]], 'version': pack.rules['version']}
                grouped.setdefault(ident, reading(pack, ident))['events'].append(event)
            box['on_page'].extend(grouped.values())
            continue
        p = probabilities(pack, selected)
        grouped = {}
        if m.task == 'channel':
            predictions = p.argmax(axis=1)
            confidence = p.max(axis=1)
            valid = confidence >= m.abstention_threshold
            mapping = m.label_map
            groups = list(dict.fromkeys(mapping.values()))
            estimates = None
            if pack.policy is not None:
                counts_input = predictions[valid]
                if getattr(m, 'gate_pin', None):
                    if {p.pin for p in gates} != {m.gate_pin}:
                        raise ValueError('Gated counting requires exactly its calibrated gate')
                    counts_input = np.r_[counts_input, np.full(len(rows)-len(selected), m.labels.index(m.neutral), int)]
                estimates = shares(counts_input, pack.table, pack.policy,
                    neutral=m.labels.index(m.neutral),
                    groups=[[i for i, label in enumerate(m.labels) if mapping.get(label) == ident] for ident in groups])
            for j, ident in enumerate(groups):
                grouped[ident] = reading(pack, ident)
                if estimates is not None:
                    grouped[ident]['share'] = estimates[j]
            hits = [(i, int(label)) for i, label in enumerate(predictions) if valid[i]]
        else:
            mapping = m.tag_map
            hits = [(i, j) for i in range(len(selected)) for j, tag in enumerate(m.labels)
                    if p[i, j] >= m.thresholds[tag]]
        for i, j in hits:
            label = m.labels[j]
            ident = mapping.get(label)
            if ident is None:
                if m.task == 'channel':
                    continue  # Unmapped emotion labels do not become channels.
                if m.status != 'research':
                    raise ValueError('Unmapped tags require research status')
            out = grouped.setdefault(ident, reading(pack, ident))
            out['events'].append({'span': [selected[i].start, selected[i].end], 'label': label,
                                  'confidence': float(p[i,j]), 'who': 'unclear', 'words': []})
        box['on_page'].extend(v for v in grouped.values() if v['events'] or v['share'])
    for pack in [p for p in packs if p.manifest.task == 'scalar']:
        m = pack.manifest
        _, (_, count) = encoder(pack)
        window_rows = windows(rows, m.token_cap, count)
        values = vectors(pack, window_rows) @ pack.weights.T + pack.bias
        low, high = m.range
        scaled = np.clip((values[:,0]-low)/(high-low), 0, 1)
        out = reading(pack, m.reading_id)
        out['series'] = [{'from': r.start, 'to': r.end, 'value': float(v)} for r, v in zip(window_rows, scaled)]
        box['on_page'].append(out)
    if diagnostics is not None:
        elapsed = time.perf_counter()-started
        diagnostics.update(seconds=elapsed, sentences=len(rows), secondsPer150=150*elapsed/len(rows),
                           gatePassed=int(accepted.sum()), encoderCount=len(encoders),
                           includesLoading=True, secondsPer150Kind='linear page normalization, not a timed 150-sentence batch',
                           referenceSeconds150=2.974, referenceExcludesLoading=True)
    return BottomBoxV2.model_validate(box).model_dump(mode='json', by_alias=True)
