"""TP55. Equal-word profiles and temporal placement, paired over chat writers."""
from collections import Counter
from pathlib import Path

import numpy as np

from .affect_data import ed_situations
from .person_halves import resamples, summary
from .tp36 import verify_order
from .tp39 import SUPPORT, TP28, saved
from .tp40 import MANIFEST
from .word_panels import pinned, sha256

GROUPS = [('anxious', 'apprehensive'), ('sad', 'disappointed', 'lonely'), ('afraid', 'terrified')]
TP40 = '42f8573f4d71b0d47732512c347ab975728a9b4579f17dc45d9cdf2a3620fd53'


def estimate(tags, labels, writers, ahead, counts, check):
    words, word = np.unique(labels, return_inverse=True)
    people, person = np.unique(writers, return_inverse=True)
    group = [[words.tolist().index(w) for w in ws] for ws in GROUPS]
    # Keep per-writer sufficient statistics so each draw re-estimates all normalizers.
    cells = np.zeros((len(people), len(words), tags.shape[1] + 3))
    np.add.at(cells, (person, word), np.column_stack((np.ones(len(tags)), ahead, counts, tags)))
    squares = np.zeros((len(people), tags.shape[1]))
    np.add.at(squares, person, tags**2)
    draws = np.vstack((np.ones(len(people)), resamples(len(people))))
    values = []
    for weights in np.array_split(draws, 40):
        check()
        totals = (weights @ cells.reshape(len(people), -1)).reshape(len(weights), *cells.shape[1:])
        n = totals[:, :, 0]
        with np.errstate(invalid='ignore', divide='ignore'):
            means = totals[:, :, 3:] / n[:, :, None]
            overall = totals[:, :, 3:].sum(axis=1) / n.sum(axis=1)[:, None]
            sd = np.sqrt((weights @ squares) / n.sum(axis=1)[:, None] - overall**2)
            profiles = (means - means.mean(axis=1, keepdims=True)) / sd[:, None, :]
            rates = totals[:, :, 1] / totals[:, :, 2]
            vectors = [profiles[:, g].mean(axis=1) for g in group]
            centered = [v - v.mean(axis=1, keepdims=True) for v in vectors]
            unit = [v / np.linalg.norm(v, axis=1, keepdims=True) for v in centered]
            sad, fear = [(unit[0] * v).sum(axis=1) for v in unit[1:]]
            a, s, f = [rates[:, g].mean(axis=1) for g in group]
            values.append(np.column_stack((sad, fear, sad-fear, a, s, f, abs(a-s)-abs(a-f))))
    result = {}
    names = ('sadLikeness', 'fearLikeness', 'profileDifference', 'anxiousAhead', 'sadAhead',
             'fearAhead', 'timeGapDifference')
    for name, col in zip(names, np.vstack(values).T, strict=True):
        result[name] = summary(col[0], col[1:])
    return result


def run(check):
    root = Path('.local/person-teacher')
    tp28 = Path('.local/nine-channel/tp28-a')
    tp40 = Path('.local/word-table/tp40-a')
    frame, source = ed_situations('.local/readers/data/empathetic-dialogues')
    old = pinned(tp28/'receipt.json', TP28)
    if old['sources']['ed']['identity'] != source:
        raise ValueError('Original chat source differs')
    archive = saved(tp28, 'ed/scores.npz', old)
    verify_order(archive, frame.id)
    with np.load(archive, allow_pickle=False) as data:
        tags = data['scores'].astype(float)
    change = pinned(tp40/'receipt.json', TP40)
    shares_path = tp40/'ed-change-shares.npz'
    if sha256(shares_path) != change['sources']['privateChangeScoresPin']:
        raise ValueError('Reader B time scores differ')
    with np.load(shares_path, allow_pickle=False) as data:
        ids, rates = data['ids'].astype(str), data['shares'][:, 2]
    order = frame.set_index('id').index.get_indexer(ids)
    if sorted(order.tolist()) != list(range(len(frame))):
        raise ValueError('Reader B roster differs')
    rates = rates[np.argsort(order)]
    support = pinned(root/'tp39-support.json', SUPPORT)
    parents = pinned(root/'private-parents.json', support['parentsPin'])
    ed = {p: i for p, src, i, *_ in parents if src == 'ed'}
    manifest = pinned(root/'inputs/manifest.json', MANIFEST)
    cnt = Counter()
    for job, h in manifest['files'].items():
        check()
        for row in pinned(root/'inputs'/(job+'.json'), h):
            if row['source'] == 'ed':
                cnt[ed[row['parent']]] += 1
    counts = np.array([cnt[i] for i in frame.id])
    ahead = rates * counts
    if (tags.shape != (24850, 19) or not np.isfinite(tags).all() or
        (counts <= 0).any() or not np.allclose(ahead, np.rint(ahead), rtol=0, atol=1e-8)
        or not np.all((rates >= 0) & (rates <= 1))):
        raise ValueError('Incomplete tags, counts or ahead marks')
    tables = estimate(tags, frame.label, frame.writer, np.rint(ahead), counts, check)
    return dict(card='TP55', estimates=tables, reports=len(frame), writers=frame.writer.nunique(),
                wordCounts={w:dict(reports=int((frame.label==w).sum()),
                                   sentences=int(counts[frame.label==w].sum()),
                                   writers=frame.loc[frame.label==w,'writer'].nunique())
                            for ws in GROUPS for w in ws},
                sources=dict(TP28=TP28, TP40=TP40, manifest=MANIFEST, support=SUPPORT,
                             tags=sha256(archive), ahead=sha256(shares_path)))
