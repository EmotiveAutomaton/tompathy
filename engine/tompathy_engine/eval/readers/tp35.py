"""Within-word intensity regressions and a paired between-writer duration test."""
import csv
from pathlib import Path

import numpy as np
import pandas as pd

from ...packs.registry import sha256
from ..back_half.reporting import save_json

WORDS = ('anger', 'boredom', 'disgust', 'fear', 'guilt', 'sadness', 'shame')
CONTROLS = ['other_responsblt', 'self_responsblt', 'unpleasantness']
TRAITS = ['anxious', 'calm', 'event_duration', 'emotion_duration', 'intensity']
SOURCE = '3d2536b555ac7005080c2cd35aadb4d570992bca70d2017e4d8939525fa3a86b'
DURATION = {'I had none': 0, 'seconds': 1, 'minutes': 2, 'hours': 3, 'days': 4, 'weeks': 5}
LIMIT = ("A report is a remembered case of a word, chosen to fit it, and not a sample of moments. "
         "Suddenness and intensity are one person's ratings made together afterwards. "
         "The Neuroticism score is two items and the comparison is between people.")


class WriterMoments:
    """Retain each writer's sufficient statistics for paired whole-writer draws."""

    def __init__(self, frame, columns, weight=None):
        data = frame.dropna(subset=columns)
        values = data[columns].to_numpy(float)
        writers, group = np.unique(data['writerIndex'], return_inverse=True)
        augmented = np.column_stack([np.ones(len(data)), values])
        self.upper = np.triu_indices(augmented.shape[1])
        cross = augmented[:, self.upper[0]] * augmented[:, self.upper[1]]
        if weight is not None:
            cross *= data[weight].to_numpy()[:, None]
        self.writers = writers
        self.n = len(data)
        self.size = augmented.shape[1]
        self.moments = np.zeros((len(writers), cross.shape[1]))
        np.add.at(self.moments, group, cross)

    def correlation(self, draws):
        sums = draws[:, self.writers] @ self.moments
        total = np.zeros((len(draws), self.size, self.size))
        i, j = self.upper
        total[:, i, j] = total[:, j, i] = sums
        mass = total[:, 0, 0]
        with np.errstate(divide='ignore', invalid='ignore'):
            mean = total[:, 0, 1:] / mass[:, None]
            cov = total[:, 1:, 1:] / mass[:, None, None] - mean[:, :, None]*mean[:, None, :]
            sd = np.sqrt(np.maximum(0, np.diagonal(cov, axis1=1, axis2=2)))
            corr = cov / (sd[:, :, None]*sd[:, None, :])
        return mass, corr, sd


def slopes(corr, predictors):
    """First-predictor slopes for all outcome columns, with singular draws missing."""
    x = corr[:, :predictors, :predictors]
    y = corr[:, :predictors, predictors:]
    out = np.full((len(x), y.shape[-1]), np.nan)
    good = np.isfinite(corr).all(axis=(1, 2))
    if good.any():
        good[good] = np.linalg.eigvalsh(x[good])[:, 0] > 1e-12
        out[good] = np.linalg.solve(x[good], y[good])[:, 0, :]
    return out


def tables(frame):
    models, trait_models, metadata, void = {}, {}, {}, {}
    present = set(frame.columns)
    for word in WORDS:
        group = frame[frame.emotion == word].copy()
        for label, predictor, outcome in [('suddenness','suddenness','intensity'),
                                           ('predictability','predict_event','intensity'),
                                           ('ceiling','suddenness','ceiling')]:
            key = f'{label}/{word}'
            fields = [predictor, *CONTROLS, outcome]
            missing = sorted(set(fields) - present)
            if missing:
                void[key] = {'missing': missing}
                continue
            model = WriterMoments(group, fields)
            models[key] = model
            metadata[key] = {'reports': model.n, 'writers': len(model.writers)}
            if label == 'ceiling':
                metadata[key]['atMaximumShare'] = float(group.dropna(subset=fields).ceiling.mean())
    missing = sorted(set(TRAITS) - present)
    if missing:
        void['betweenWriter'] = {'missing': missing}
        return models, trait_models, metadata, void
    selected = frame[frame.emotion.isin(WORDS)].dropna(subset=['trait','event_duration','emotion_duration','intensity'])
    grouped = selected.groupby(['writerIndex','emotion'],as_index=False)[
        ['trait','event_duration','intensity','emotion_duration']].mean()
    grouped['weight'] = 1 / grouped.groupby('writerIndex').emotion.transform('size')
    for word in WORDS:
        part = grouped[grouped.emotion == word]
        trait_models[word] = WriterMoments(part, ['trait','event_duration','intensity','emotion_duration'], 'weight')
        metadata[f'betweenWriter/{word}'] = {'writerWordRows': len(part)}
    metadata['betweenWriter/pooled'] = {'reports':len(selected), 'writerWordRows':len(grouped),
                                        'writers':int(grouped.writerIndex.nunique())}
    return models, trait_models, metadata, void


def estimates(draws, models, traits):
    result = {}
    for key, model in models.items():
        _, corr, sd = model.correlation(draws)
        estimate = slopes(corr, 4)[:, 0]
        result[key] = estimate*sd[:, -1] if key.startswith('ceiling/') else estimate
    if 'suddenness/anger' in result and 'suddenness/sadness' in result:
        result['angerMinusSadness'] = result['suddenness/anger'] - result['suddenness/sadness']
    if traits:
        total = np.zeros((len(draws),4,4))
        def store(key, corr):
            effect = slopes(corr, 2)
            result[key+'/intensity'] = effect[:, 0]
            result[key+'/duration'] = effect[:, 1]
            result[key+'/difference'] = effect[:, 1]-effect[:, 0]
        for word, model in traits.items():
            mass, corr, _ = model.correlation(draws)
            total += mass[:, None, None]*corr
            store('betweenWriter/'+word, corr)
        store('betweenWriter/pooled', total)
    return result


def load_generation(corpus):
    path = Path(corpus)/'corpus/crowd-enVent_generation.tsv'
    if sha256(path) != SOURCE:
        raise ValueError('Original Crowd-enVENT generation file differs')
    with path.open(encoding='utf8', newline='') as stream:
        header = set(next(csv.reader(stream, delimiter='\t')))
    allowed = {'emotion','prolific_id','suddenness','predict_event',*CONTROLS,*TRAITS}
    cols = sorted(allowed & header)
    if not {'prolific_id','emotion'} <= header:
        return None, cols
    frame = pd.read_csv(path, sep='\t', usecols=cols, keep_default_na=False)
    if len(frame) != 6600 or (frame.prolific_id == '').any():
        raise ValueError('Missing original report or writer identity')
    frame['writerIndex'] = pd.factorize(frame.prolific_id,sort=True)[0]
    for field in set(cols) - {'emotion','prolific_id','event_duration','emotion_duration'}:
        value = pd.to_numeric(frame[field],errors='coerce')
        maximum = 7 if field in ('anxious','calm') else 5
        if ((value < 1) | (value > maximum)).any():
            raise ValueError(f'Out-of-scale value in {field}')
        frame[field] = value
    for field in ('emotion_duration','event_duration'):
        if field in cols:
            if set(frame[field])-set(DURATION)-{''}:
                raise ValueError(f'Unspecified duration band in {field}')
            frame[field] = frame[field].map(DURATION)
    if 'intensity' in cols:
        frame['ceiling'] = (frame.intensity == 5).astype(float).where(frame.intensity.notna())
    if {'anxious','calm'} <= header:
        score = (frame.anxious + 8-frame.calm)/2
        frame['trait'] = score.groupby(frame.writerIndex).transform('mean')
    return frame, cols


def run(corpus, output, check, ledger, protocol):
    frame, cols = load_generation(corpus)
    receipt = {'card':'TP35','status':'complete','productionAdmission':False,'ledger':ledger,
               'sourcePin':SOURCE,'protocolPin':sha256(protocol),'scope':LIMIT,'columns':cols}
    if frame is None:
        receipt.update(status='blocked', void={'all':'Missing original writer or feeling-word field'})
    else:
        models, traits, sizes, void = tables(frame)
        nw = int(frame.writerIndex.max()+1)
        point = estimates(np.ones((1,nw)), models, traits)
        samples = {key:[] for key in point}
        rng = np.random.default_rng(23)
        for _ in range(80):
            check()
            draws = rng.multinomial(nw, np.full(nw,1/nw), size=25)
            for key, values in estimates(draws, models, traits).items():
                samples[key].append(values)
        rows = {}
        for key, estimate in point.items():
            v = np.concatenate(samples[key]); v = v[np.isfinite(v)]
            rows[key] = {'estimate':float(estimate[0]) if np.isfinite(estimate[0]) else None,
                         'interval':np.quantile(v,[.025,.975]).tolist() if len(v) else None,
                         'finiteDraws':len(v)}
        bars = {}
        for key, threshold in [('suddenness/anger',.08),('angerMinusSadness',.08),
                               ('betweenWriter/pooled/difference',0.)]:
            r = rows.get(key)
            if r and r['estimate'] is not None and r['interval'] is not None:
                bars[key] = r['estimate'] >= threshold and r['interval'][0] > 0
        if 'suddenness/anger' in bars:
            lo, hi = rows['suddenness/anger']['interval']
            bars['angerIntervalWithinEquivalenceBand'] = lo >= -.08 and hi <= .08
        receipt.update(rows=rows, groups=sizes, void=void, bars=bars, writerDraws=2000,
                       releasedReports=len(frame), writers=nw)
    save_json(Path(output)/'receipt.json',receipt)
