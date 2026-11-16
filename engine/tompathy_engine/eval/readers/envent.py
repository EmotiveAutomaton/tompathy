"""Crowd-enVENT's fixed report split, explicit writer overlap and answer keys."""
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ...packs.registry import sha256

RATINGS = ['suddenness', 'familiarity', 'predict_event', 'pleasantness', 'unpleasantness',
    'goal_relevance', 'chance_responsblt', 'self_responsblt', 'other_responsblt',
    'predict_conseq', 'goal_support', 'urgency', 'self_control', 'other_control',
    'chance_control', 'accept_conseq', 'standards', 'social_norms', 'attention',
    'not_consider', 'effort']
READABLE = ['pleasantness', 'unpleasantness', 'self_responsblt', 'goal_support',
            'social_norms', 'other_responsblt', 'standards', 'suddenness']


@dataclass
class Corpus:
    reports: pd.DataFrame
    judgments: pd.DataFrame
    labels: list[str]
    train: np.ndarray
    dev: np.ndarray
    test: np.ndarray
    pins: dict[str, str]

    def summary(self):
        frame = self.reports
        train_writers = set(frame.iloc[self.train].prolific_id)
        return {'reports': len(frame), 'judgments': len(self.judgments),
            'writers': int(frame.prolific_id.nunique()), 'train': len(self.train),
            'dev': len(self.dev), 'test': len(self.test),
            'testReportsWithTrainingWriter': int(frame.iloc[self.test].prolific_id.isin(train_writers).sum()),
            'split': 'fixed 1200 validation report IDs; lowest SHA-256 tenth of remaining writers for development',
            'writerDisjointTest': False, 'files': self.pins}


def load(directory):
    root = Path(directory)
    gp, vp = root/'corpus/crowd-enVent_generation.tsv', root/'corpus/crowd-enVent_validation.tsv'
    g = pd.read_csv(gp, sep='\t', quoting=3,
        usecols=['text_id', 'hidden_emo_text', 'emotion', 'prolific_id', *RATINGS])
    v = pd.read_csv(vp, sep='\t', quoting=3,
        usecols=['text_id', 'emotion', 'original_emotion', *RATINGS])
    if g.text_id.duplicated().any() or not set(v.text_id) <= set(g.text_id):
        raise ValueError('Invalid report/judgment join')
    if not (v.original_emotion.to_numpy() == g.set_index('text_id').loc[v.text_id].emotion.to_numpy()).all():
        raise ValueError('Writer keys disagree across files')
    if len(g) != 6600 or v.text_id.nunique() != 1200 or len(v) != 6000:
        raise ValueError('Corpus differs from preregistered census')
    test_mask = g.text_id.isin(v.text_id).to_numpy()
    writers = sorted(g.loc[~test_mask].prolific_id.unique(),
                     key=lambda s: hashlib.sha256(str(s).encode()).hexdigest())
    dev_writers = set(writers[:max(1, len(writers)//10)])
    dev_mask = ~test_mask & g.prolific_id.isin(dev_writers).to_numpy()
    train_mask = ~test_mask & ~dev_mask
    labels = sorted(g.emotion.unique())
    g['y'] = g.emotion.map(dict(zip(labels, range(len(labels)))))
    g['hidden_emo_text'] = g.hidden_emo_text.fillna('')
    return Corpus(g, v, labels, np.flatnonzero(train_mask), np.flatnonzero(dev_mask),
                  np.flatnonzero(test_mask), {'generation': sha256(gp), 'validation': sha256(vp)})


def human_rows(corpus):
    """Majority ties go to the label encountered first in the original file order."""
    g, v = corpus.reports, corpus.judgments
    key = g.set_index('text_id').y
    index = dict(zip(corpus.labels, range(len(corpus.labels))))
    votes = v.emotion.map(index).to_numpy()
    majorities = {}
    for ident, group in v.groupby('text_id', sort=False):
        labels = group.emotion.tolist()
        counts = {label: labels.count(label) for label in dict.fromkeys(labels)}
        majorities[ident] = index[max(counts, key=counts.get)]
    ids = g.iloc[corpus.test].text_id
    return {'single': (key.loc[v.text_id].to_numpy(), votes),
            'majority': (key.loc[ids].to_numpy(), np.array([majorities[i] for i in ids]))}
