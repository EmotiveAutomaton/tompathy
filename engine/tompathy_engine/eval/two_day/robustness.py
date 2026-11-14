"""TP6 signals, attack normalization and held-out fixed-FPR pilot reporting."""
import math
import re
import unicodedata
from collections import Counter, defaultdict

import numpy as np

from ...ledger.ids import digest
from ...preview.readers import LocalReader
from ...preview.surface import words
from ..back_half.reporting import save_json
from .exports import read

GENRES = ('abstracts', 'books', 'news', 'poetry', 'recipes', 'reddit', 'reviews', 'wiki')
ATTACKS = ('homoglyph', 'zero_width_space', 'paraphrase')
# Deliberately bounded Latin look-alikes; a normalization, not a language judgment.
CONFUSABLES = str.maketrans(dict(zip('АВЕЗКМНОРСТХаеорсхуіјѕΙΟΡΤΧΥΑΒΕΖΗΚΜΝ',
                                   'ABE3KMHOPCTXaeopcxyijsIOPTXYABEZHKMN', strict=True)))
ZERO_WIDTH = re.compile('[\u200b-\u200d\u2060\ufeff]')


def normalize(text):
    return re.sub(r'\s+', ' ', ZERO_WIDTH.sub('', unicodedata.normalize('NFKC', text)).translate(CONFUSABLES)).strip()


class MomentReader(LocalReader):
    """One forward pass yields observed loss and reference-distribution moments."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.scoring != 'window':
            raise ValueError('TP6 moment probe uses the registered float32 window')
        self.identity = {**self.identity, 'moments': 'token-logp-variance-v1'}

    def moment_score(self, text, check=lambda: None):
        key = digest([self.identity, text, 'window2048-chunk512'])
        path = self.cache/f'moments-{key}.json' if self.cache else None
        if path and path.exists():
            saved = read(path)
            if saved['key'] != key or saved['sha256'] != digest(saved['tokens']):
                raise ValueError('Moment cache integrity failure')
            return saved['tokens']
        encoded = self.encode(text)
        target, offsets = encoded['input_ids'], encoded['offset_mapping']
        bos = self.tokenizer.bos_token_id
        bos = self.tokenizer.eos_token_id if bos is None else bos
        if bos is None:
            raise ValueError('Missing beginning token')
        torch, out = self.torch, []
        for start in range(0, len(target), 512):
            check()
            chunk = target[start:start+512]
            previous = target[max(0, start-(2048-len(chunk))):start] or [bos]
            ids = previous+chunk
            with torch.inference_mode():
                logits = self.model(torch.tensor([ids]), use_cache=False,
                    logits_to_keep=torch.arange(len(previous)-1, len(ids)-1)).logits[0].float()
                logp = torch.log_softmax(logits, dim=-1)
                prob = logp.exp()
                mean = (prob*logp).sum(dim=-1)
                variance = ((prob*logp.square()).sum(dim=-1)-mean.square()).clamp_min(0)
                loss = -logp[torch.arange(len(chunk)), torch.tensor(chunk)]
                values = zip(loss.tolist(), (-mean).tolist(), variance.tolist(), strict=True)
                for i, (nats, entropy, var) in enumerate(values, start):
                    a, b = offsets[i]
                    out.append({'start': a, 'end': b, 'nats': nats, 'entropy': entropy, 'variance': var})
            del logits, logp, prob, mean, variance, loss
            check()
        if path:
            save_json(path, {'key': key, 'tokens': out, 'sha256': digest(out)})
        return out


def signals(text, tokens):
    source_words = words(text, [t for t in tokens if t['end'] > t['start']])
    if not tokens or not source_words:
        raise ValueError('Empty robustness observation')
    values = [w['nats'] for w in source_words]
    variance = sum(t['variance'] for t in tokens)
    if variance <= 0 or not all(math.isfinite(t[k]) for t in tokens for k in ('nats', 'entropy', 'variance')):
        raise ValueError('Undefined curvature denominator')
    return {'A0': float(np.mean(values)), 'A1': float(np.std(values)),
            'FD': sum(-t['nats']+t['entropy'] for t in tokens)/math.sqrt(variance)}


def human_split(rows):
    halves = ([], [])
    for genre in GENRES:
        group = sorted((r for r in rows if r['model'] == 'human' and r['domain'] == genre),
                       key=lambda r: digest(['TP6-human-split', r['id']]))
        if len(group) != 100:
            raise ValueError('TP6 requires exactly 100 human rows per main genre')
        halves[0].extend(group[:50]); halves[1].extend(group[50:])
    return halves


def rate(values):
    """Wilson 95% interval, including zero-event/small strata."""
    if not values:
        return {'n': 0, 'rate': None, 'interval': None}
    n, p, z = len(values), sum(values)/len(values), 1.959963984540054
    center = (p+z*z/(2*n))/(1+z*z/n)
    width = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return {'n': n, 'events': sum(values), 'rate': p, 'interval': [max(0, center-width), min(1, center+width)]}


def robustness_report(rows, scored):
    calibration, held = human_split(rows)
    result = {'status': 'complete' if all(r['id'] in scored for r in rows) else 'partial', 'pilot': True, 'productionAdmission': False, 'bar': None,
              'thresholds': {}, 'rates': [], 'direction': {'A0': 'lower', 'A1': 'lower', 'FD': 'higher'},
              'normalization': 'NFKC, zero-width removal, frozen bounded confusables, whitespace collapse',
              'nonNativeWriting': 'not run: no licensed auxiliary set received'}
    if not all(r['id'] in scored for r in calibration):
        result.update(status='partial: calibration incomplete', completedCalibration=sum(r['id'] in scored for r in calibration))
        return result
    for signal in ('A0', 'A1', 'FD'):
        direction = 1 if signal == 'FD' else -1
        values = sorted(direction*scored[r['id']]['raw'][signal] for r in calibration)
        # Strict exceedance avoids ties producing more than 5% calibration FPR.
        threshold = values[math.ceil(.95*len(values))-1]
        result['thresholds'][signal] = {'orientedThreshold': threshold, 'strict': True,
            'calibration': rate([v > threshold for v in values])}
        groups = defaultdict(list)
        for row in [*held, *(r for r in rows if r['model'] != 'human')]:
            if row['id'] not in scored:
                continue
            modes = ('raw', 'normalized') if row['attack'] in ATTACKS else ('raw',)
            for mode in modes:
                detected = int(direction*scored[row['id']][mode][signal] > threshold)
                population = 'human-heldout' if row['model'] == 'human' else 'machine'
                keys = [('all', 'all'), ('genre', row['domain']), ('generator', row['model']), ('attack', row['attack'])]
                for kind, name in keys:
                    groups[population, mode, kind, name].append(detected)
        result['rates'].extend({'signal': signal, 'population': pop, 'mode': mode, 'stratum': kind, 'name': name, **rate(v)}
                              for (pop, mode, kind, name), v in sorted(groups.items()))
    return result


class Quotas:
    def __init__(self):
        self.counts = Counter()
        self.generators = Counter()
        self.ids = set()

    def accept(self, row):
        if row['id'] in self.ids:
            raise ValueError('Repeated RAID row identity')
        domain, model, attack = row['domain'], row['model'], row['attack']
        if domain not in GENRES:
            return False
        if model == 'human' and attack == 'none':
            key, limit = ('human', domain), 100
        elif model != 'human' and attack == 'none':
            if self.generators[domain, model] >= 12:
                return False
            key, limit = ('machine', domain), 100
        elif model != 'human' and attack in ATTACKS:
            key, limit = ('attack', attack), 300
        else:
            return False
        if self.counts[key] >= limit:
            return False
        self.counts[key] += 1
        self.ids.add(row['id'])
        if key[0] == 'machine':
            self.generators[domain, model] += 1
        return True

    def complete(self):
        return all(self.counts[kind, genre] == 100 for kind in ('human', 'machine') for genre in GENRES) and all(self.counts['attack', a] == 300 for a in ATTACKS)
