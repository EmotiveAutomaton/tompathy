"""Registered stand-in/need-tag contrasts; no claim that a channel fired."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import expit

from ...packs.registry import sha256
from ...packs.run import encoder_for
from ...packs.trigger import TAG_MAP_V2, TAGS
from ...packs.v2 import load_pack
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .artifacts import seal
from .checkpoint import completed
from .envent import RATINGS, load

# Source-specific, exact words; no embarrassment-to-shame alias.
MAP = {
    'SEEKING': {'tags': ['curiosity'], 'go': ['curiosity', 'excitement'], 'ed': ['excited', 'anticipating', 'hopeful'], 'envent': []},
    'PLAY': {'tags': ['contact'], 'go': ['amusement'], 'ed': [], 'envent': []},
    'LUST': {'tags': ['romance'], 'go': ['desire'], 'ed': [], 'envent': []},
    'CARE': {'tags': ['family'], 'go': ['caring', 'love'], 'ed': ['caring', 'sentimental'], 'envent': []},
    'PANIC/GRIEF': {'tags': ['family'], 'go': ['grief', 'sadness'], 'ed': ['sad', 'lonely', 'devastated'], 'envent': ['sadness']},
    'RAGE': {'tags': ['power', 'order'], 'go': ['anger'], 'ed': ['angry'], 'envent': ['anger']},
    'FEAR': {'tags': ['tranquility', 'health'], 'go': ['fear'], 'ed': ['afraid'], 'envent': ['fear']},
    'DISGUST': {'tags': ['food'], 'go': ['disgust'], 'ed': ['disgusted'], 'envent': ['disgust']},
    'SHAME': {'tags': ['approval', 'status'], 'go': [], 'ed': ['ashamed'], 'envent': ['shame']},
}
SECONDARY = {'ed': {'furious': 'RAGE', 'terrified': 'FEAR'}}
JOY_TAGS = ('curiosity', 'contact', 'romance', 'family')
LIMIT = 'Stand-in words and model tag contrasts, not observed channel firing or maker needs. Reader labels are guesses; LUST is uncovered beyond its unmapped romance tag.'


def profiles(scores, labels, *, draws=2000, seed=23, check=lambda: None):
    """Exact unit bootstrap, recomputing source SD and both contrast means."""
    p, y = np.asarray(scores, float), np.asarray(labels, float)
    if (p.ndim != 2 or y.ndim != 2 or len(p) != len(y) or len(p) < 2
            or not np.isfinite(p).all() or not np.isin(y, [0, 1]).all()):
        raise ValueError('Finite unit scores and binary label membership required')
    n, tags = p.shape
    k = y.shape[1]
    # Every row is one original comment/conversation/report. A multi-label
    # comment has several memberships but enters each bootstrap only once.
    stats = np.column_stack([p, p*p, y, (y[:, :, None]*p[:, None, :]).reshape(n, k*tags)])

    def contrast(sums):
        total = sums[..., :tags]
        sd = np.sqrt(np.maximum(0, sums[..., tags:2*tags]/n-(total/n)**2))
        count = sums[..., 2*tags:2*tags+k]
        positive = sums[..., 2*tags+k:].reshape(*sums.shape[:-1], k, tags)
        with np.errstate(divide='ignore', invalid='ignore'):
            mean = positive/count[..., :, None]
            other = (total[..., None, :]-positive)/(n-count[..., :, None])
            lift = (mean-other)/sd[..., None, :]
        return mean, np.where(sd[..., None, :] > 1e-12, lift, np.nan)

    mean, point = contrast(stats.sum(axis=0))
    rng = np.random.default_rng(seed)
    samples = np.empty((draws, k, tags), float)
    for start in range(0, draws, 8):
        check()
        batch = min(8, draws-start)
        weights = np.stack([np.bincount(rng.integers(n, size=n), minlength=n) for _ in range(batch)])
        samples[start:start+batch] = contrast(weights@stats)[1]
    intervals = np.full((k, tags, 2), np.nan)
    valid = np.isfinite(samples).sum(axis=0)
    for label in range(k):
        for tag in range(tags):
            finite = samples[:, label, tag][np.isfinite(samples[:, label, tag])]
            if len(finite) >= .95*draws:
                intervals[label, tag] = np.quantile(finite, [.025, .975])
    return mean, point, intervals, valid


def finite_list(values):
    return [float(v) if np.isfinite(v) else None for v in values]


def cell_rows(source, labels, scores, truth, check):
    mean, lifts, intervals, valid = profiles(scores, truth, check=check)
    result = {}
    for i, label in enumerate(labels):
        supported = np.isfinite(lifts[i]).all()
        top = TAGS[int(np.argmax(lifts[i]))] if supported else None
        result[label] = {'n': int(truth[:, i].sum()), 'mean_scores': finite_list(mean[i]),
                         'lift': finite_list(lifts[i]), 'interval': [finite_list(x) for x in intervals[i]],
                         'finite_draws': valid[i].tolist(), 'highest_tag': top}
    cells = []
    for channel, mapping in MAP.items():
        expected_needs = {TAG_MAP_V2[t] for t in mapping['tags'] if t in TAG_MAP_V2}
        for label in mapping[source]:
            row = result.get(label)
            top = row['highest_tag'] if row else None
            lo, hi = row['interval'][TAGS.index(top)] if top else (None, None)
            clear = lo is not None and hi is not None and (lo > 0 or hi < 0)
            cells.append({'channel': channel, 'label': label, 'n': row['n'] if row else 0,
                          'predicted_tags': mapping['tags'], 'highest_tag': top,
                          'highest_tag_interval': [lo, hi], 'interval_excludes_zero': clear,
                          'tag_filled': bool(clear and top in mapping['tags']),
                          'need_filled': bool(clear and TAG_MAP_V2.get(top) in expected_needs) if expected_needs else None,
                          'available': bool(row and row['n'] > 0),
                          'prior_bow_replication': source == 'envent' and label in ('fear', 'disgust', 'sadness')})
    secondary = {label: {'channel': channel, 'profile': result.get(label)}
                 for label, channel in SECONDARY.get(source, {}).items()}
    return {'labels': result, 'cells': cells, 'intensity_second_readings': secondary}


def joy_split(source, labels, scores, truth, ratings=None):
    name = 'joyful' if source == 'ed' else 'joy'
    if name not in labels:
        return {'status': 'label unavailable', 'label': name}
    selected = truth[:, labels.index(name)].astype(bool)
    split = np.argmax(scores[:, [TAGS.index(t) for t in JOY_TAGS]], axis=1)
    result = {'label': name, 'n': int(selected.sum()), 'ties': 'first in fixed curiosity/contact/romance/family order', 'splits': {}}
    for i, tag in enumerate(JOY_TAGS):
        mask = selected & (split == i)
        row = {'n': int(mask.sum())}
        if source == 'go':
            channels = ('SEEKING', 'PLAY', 'LUST', 'CARE')
            shares = []
            for channel in channels:
                columns = [labels.index(label) for label in MAP[channel]['go']]
                shares.append(float(truth[mask][:, columns].any(axis=1).mean()) if mask.any() else None)
            row['co_label_shares'] = dict(zip(channels, shares))
            row['matching_largest'] = bool(shares[i] is not None and shares[i] > max(x for j, x in enumerate(shares) if j != i))
        if ratings is not None:
            row['writer_rating_means'] = dict(zip(RATINGS, finite_list(ratings[mask].mean(axis=0)))) if mask.any() else None
        result['splits'][tag] = row
    if source == 'go':
        result['all_four_match'] = all(r['matching_largest'] for r in result['splits'].values())
    return result


def run(export_job, ed, go, corpus, output, check, *, ledger):
    output, export_job = Path(output), Path(export_job)
    exported = completed(export_job, 'TRIGGER-export-need')
    pack = load_pack(export_job/'rp-need-1')
    if pack.pin != exported['pack']['pin'] or pack.manifest.tag_map != TAG_MAP_V2:
        raise ValueError('TP28 requires the exact C0 version-2 mapped pack')
    evidence = json.loads((pack.root/'evidence.json').read_text(encoding='utf8'))
    if evidence['tagMapVersion'] != 2:
        raise ValueError('Unregistered tag map')
    receipt = {'card': 'TP28', 'status': 'running', 'productionAdmission': False, 'ledger': ledger,
               'scope': LIMIT, 'reader': {'pack': pack.pin, 'exportReceiptPin': sha256(export_job/'receipt.json')},
               'protocol': {'mapping': MAP, 'secondary': SECONDARY, 'tags': list(TAGS), 'tag_map': TAG_MAP_V2,
                            'draws': 2000, 'seed': 23, 'unit': {'go': 'comment', 'ed': 'conversation', 'envent': 'report'},
                            'standardizer': 'source-wide probability SD, recomputed inside bootstrap',
                            'interval': '2.5/97.5 percentiles; undefined if fewer than 95 percent finite draws',
                            'row': 'strict majority of registered available cells at need level; unmapped need does not count as filled',
                            'table_bar': 'six of nine rows, including two of SEEKING/PLAY/CARE/LUST',
                            'joy': 'strict matching-share maximum; ties do not pass'}, 'sources': {}}
    save = lambda: save_json(output/'receipt.json', receipt)
    save()
    encode = None
    artifacts = []
    for source in ('ed', 'go', 'envent'):
        check()
        save_json(output/'phase.json', {'phase': 'intake', 'source': source})
        ratings = None
        if source == 'ed':
            frame, identity = ed_situations(ed)
            labels = sorted(frame.label.unique())
            truth = np.column_stack([(frame.label == label).to_numpy() for label in labels])
            texts, ids = frame.text.tolist(), frame.id.astype(str).to_numpy()
        elif source == 'go':
            frame, truth, labels, identity = go_comments(go)
            keep = (frame.source_split != 'unreleased').to_numpy()
            frame, truth = frame[keep], truth[keep]
            texts, ids = frame.text.tolist(), frame.id.astype(str).to_numpy()
        else:
            data = load(corpus)
            frame = data.reports
            labels = sorted(frame.emotion.unique())
            truth = np.column_stack([(frame.emotion == label).to_numpy() for label in labels])
            texts, ids = frame.hidden_emo_text.tolist(), frame.text_id.astype(str).to_numpy()
            ratings = frame[RATINGS].to_numpy(float)
            identity = {'files': data.pins, 'qualificationSetReuse': True}
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate source units')
        directory = output/source
        directory.mkdir()
        if source == 'envent':
            # All C0 transfer scores are already durable: never repeat that inference.
            import pandas as pd
            manifest = json.loads((export_job/'IM2/manifest.json').read_text(encoding='utf8'))
            if sha256(export_job/'IM2/scores.csv') != manifest['files']['scores.csv']:
                raise ValueError('IM2 scores changed')
            saved = pd.read_csv(export_job/'IM2/scores.csv', float_precision='round_trip')
            index = {str(v): i for i, v in enumerate(saved.text_id)}
            if set(index) != set(ids) or len(index) != len(saved):
                raise ValueError('IM2 source units differ')
            scores = saved.loc[:, list(TAGS)].to_numpy()[[index[v] for v in ids]]
        else:
            key = hashlib.sha256(json.dumps({'pack': pack.pin, 'texts': texts, 'ids': ids.tolist()}, sort_keys=True).encode()).hexdigest()
            batches = []
            save_json(output/'phase.json', {'phase': 'score-tags', 'source': source, 'total': len(texts)})
            for start in range(0, len(texts), 128):
                check()
                if encode is None:
                    encode = encoder_for(pack)
                vectors = np.asarray(encode(texts[start:start+128]))
                batch = expit(vectors@pack.weights.T+pack.bias)
                if batch.shape != (min(128, len(texts)-start), 19) or not np.isfinite(batch).all():
                    raise ValueError('Invalid tag forecasts')
                path = directory/f'{start:08d}.npz'
                np.savez(path, key=key, start=start, scores=batch)
                batches.append(batch)
                save_json(output/'progress.json', {'phase': 'score-tags', 'source': source,
                                                   'saved': start+len(batch), 'total': len(texts)})
            scores = np.concatenate(batches)
        np.savez(directory/'scores.npz', ids=np.asarray(ids, dtype=str), scores=scores, truth=truth)
        artifacts.append(directory)
        save_json(output/'phase.json', {'phase': 'contrasts-bootstrap', 'source': source, 'draws': 2000})
        row = cell_rows(source, list(labels), scores, truth, check)
        row.update(n=len(texts), identity=identity, joy=joy_split(source, list(labels), scores, truth, ratings),
                   inferenceReused=source == 'envent', limit=LIMIT if source != 'envent' else LIMIT+' Qualification-set reuse, not fresh transfer.')
        receipt['sources'][source] = row
        save()
    cells = [cell for source in receipt['sources'].values() for cell in source['cells']]
    rows = {}
    for channel in MAP:
        available = [c for c in cells if c['channel'] == channel and c['available']]
        count = sum(c['need_filled'] is True for c in available)
        rows[channel] = {'available_cells': len(available), 'need_filled_cells': count,
                         'filled': bool(available and count > len(available)/2),
                         'unmapped_cells': sum(c['need_filled'] is None for c in available)}
    filled = sum(r['filled'] for r in rows.values())
    new = sum(rows[c]['filled'] for c in ('SEEKING', 'PLAY', 'CARE', 'LUST'))
    receipt.update(status='complete', rows=rows, filled=filled, newChannelRowsFilled=new,
                   tablePassed=filled >= 6 and new >= 2, artifactsPin=seal(output, artifacts, check))
    save()
