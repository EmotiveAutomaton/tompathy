"""Story Commonsense intake, original character-line majority and story folds."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

from ...packs.registry import sha256
from ...packs.trigger import TAGS


def verify(root, paths):
    manifest = json.loads((root/'intake.json').read_text(encoding='utf8'))
    if manifest.get('archiveSha256') != '989a8294fee4b825b2761ab0a201a0e316b74a297efe2be467b1ee7490907f72':
        raise ValueError('Uncommissioned Story Commonsense archive')
    for p in paths:
        if sha256(p) != manifest['files'][p.relative_to(root).as_posix()]:
            raise ValueError('Story source bytes changed')


def load(root, check=lambda: None):
    root = Path(root)
    paths = [root/'csv_version'/s/'motiv/allcharlinepairs.csv' for s in ('dev', 'test')]
    verify(root, paths)
    data = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    rows, truth, humans = [], [], []
    for index, ((story, line, character), group) in enumerate(data.groupby(['storyid', 'linenum', 'char'], sort=False)):
        if index % 256 == 0:
            check()
        if group.sentence.nunique() != 1:
            raise ValueError('Conflicting character-line text')
        annotations = []
        for _, row in group[group.motiveworkerid != 'none'].iterrows():
            labels = set(json.loads(row.reiss)) if pd.notna(row.reiss) else set()
            if labels-set(TAGS)-{'none', 'na'}:
                raise ValueError('Unknown Reiss category')
            annotations.append([int(t in labels) for t in TAGS])
        a = np.asarray(annotations, dtype=np.int8).reshape(-1, len(TAGS))
        rows.append({'story': str(story), 'line': int(line), 'character': str(character), 'text': str(group.sentence.iloc[0])})
        truth.append((a.sum(axis=0) >= 2).astype(np.int8))
        humans.append(a)
    frame, y = pd.DataFrame(rows), np.asarray(truth)
    if len(frame) != 48065 or frame.story.nunique() != 4853 or int(y.any(axis=1).sum()) != 12271:
        raise ValueError('Story census differs from commissioned key')
    folds = list(GroupKFold(5).split(frame, groups=frame.story))
    for train, test in folds:
        if set(frame.story.iloc[train]) & set(frame.story.iloc[test]):
            raise ValueError('Story leakage')
    identity = {'files': {p.relative_to(root).as_posix(): sha256(p) for p in paths},
                'rows': len(frame), 'stories': int(frame.story.nunique()), 'majority': 2,
                'labels': list(TAGS), 'researchOnly': True, 'license': 'archive states no license'}
    return frame, y, humans, folds, identity


def development(train, groups):
    """Lowest-hash tenth of training stories; never sees held-out labels."""
    unique = sorted(set(np.asarray(groups)[train]), key=lambda s: hashlib.sha256(str(s).encode()).hexdigest())
    selected = set(unique[:max(1, len(unique)//10)])
    dev = np.array([i for i in train if groups[i] in selected], int)
    fit = np.array([i for i in train if groups[i] not in selected], int)
    return fit, dev


def people(humans):
    # Exactly three actual annotators; don't invent missing worker judgments.
    answers, keys, supported = [], [], 0
    for a in humans:
        if len(a) != 3:
            continue
        supported += 1
        for i in range(3):
            answers.append(a[i])
            keys.append(np.delete(a, i, axis=0).sum(axis=0) >= 2)
    if not answers:
        raise ValueError('No three-annotator rows')
    scores = f1_score(keys, answers, average=None, zero_division=0)
    return {'lines': supported, 'judgments': len(answers), 'excluded_lines': len(humans)-supported,
            'rule': 'each actual annotator against agreement of the other two, pooled over supported lines',
            'per_tag_f1': dict(zip(TAGS, map(float, scores))), 'mean_f1': float(scores.mean())}
