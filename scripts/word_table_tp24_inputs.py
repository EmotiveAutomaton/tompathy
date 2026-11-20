"""Verify the amended TP24 input rosters without scoring a report or opening reserved answers."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def pin(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def audit():
    base = ROOT/'.local/word-table'
    opening = base/'intake-a'
    selection = opening/'reserved-ids.json'
    if pin(selection) != '37ccfe31e919be30c47bf92e2b6223b82884941127c53e77ef28e2a3e20c650e':
        raise ValueError('Original report partitions changed')
    panels = read(selection)
    manifest = read(opening/'spark/source.json')
    for job in ('Q1', 'Q2'):
        if pin(opening/'spark'/f'{job}.json') != manifest['jobs'][job]['filePin']:
            raise ValueError('Original prompted roster changed')
    q1 = [row['id'] for row in read(opening/'spark/Q1.json')]
    q2 = [row['id'] for row in read(opening/'spark/Q2.json')]
    if q1 != panels['F1']:
        raise ValueError('F1 order differs')
    sets = {'SP1': panels['sp1'], 'Q1': q1, 'Q2': q2, 'Q5': panels['F2']}
    counts = {name: len(rows) for name, rows in sets.items()}
    all_ids = [ident for rows in sets.values() for ident in rows]
    if counts != {'SP1': 500, 'Q1': 350, 'Q2': 5400, 'Q5': 350} or len(set(all_ids)) != 6600:
        raise ValueError('Missing or duplicated cohort members')
    corpus = ROOT/'.local/readers/data/crowd-enVent2023/corpus/crowd-enVent_generation.tsv'
    if pin(corpus) != manifest['inputPins']['generation']:
        raise ValueError('Original writer roster changed')
    # Target ratings and texts are unnecessary for checking the original fold assignment.
    frame = pd.read_csv(corpus, sep='\t', quoting=3, dtype=str, usecols=['text_id','prolific_id'])
    if set(frame.text_id) != set(all_ids) or frame.text_id.duplicated().any():
        raise ValueError('Study roster differs from the released reports')
    source = base/'remaining-extension-a/inputs/source-remaining.json'
    registered = read(base/'remaining-extension-a/extension.json')['entries']['G2']
    if pin(source) != registered['sourcePin']:
        raise ValueError('Registered training source differs')
    training = base/'remaining-extension-a/inputs/G2-RD2.npz'
    with np.load(training, allow_pickle=False) as saved:
        rows, assignments = saved['train_indices'], saved['splits']
    if (read(base/'remaining-extension-a/extension.json')['files']['inputs/G2-RD2.npz'] != pin(training)
            or assignments.shape != (5, 6600) or frame.text_id.iloc[rows].tolist() != q2):
        raise ValueError('Original training or prediction order changed')
    coverage = np.zeros(len(rows), dtype=int)
    fold_counts = []
    for fold in assignments[:, rows]:
        fit, dev, forecast = (set(frame.prolific_id.iloc[rows[fold == value]]) for value in (1,2,3))
        if fit & dev or fit & forecast or dev & forecast or set(fold) != {1,2,3}:
            raise ValueError('Writer leakage or incomplete training fold')
        coverage += fold == 3
        fold_counts.append(int((fold == 3).sum()))
    if not np.all(coverage == 1):
        raise ValueError('Each missing trained forecast must have exactly one held-out writer fold')
    pilot = ROOT/'.local/nine-channel/spark/sp1-v2-reader-b-pilot-a/receipt.json'
    q1_receipt = base/'verified-spark-Q1-a/receipt.json'
    if (pin(pilot) != '3511182fa3da08e31f9dbb9ae859a143da691231e6ca641937cbd42d8d5a6156'
            or pin(q1_receipt) != '17813970705a9b72a64e7054f857f3eac8eb3b8f3a65a4b8ff9a63ecde1fa2db'):
        raise ValueError('The original B first pass or Q1 receipt changed')
    original, current = read(pilot), read(q1_receipt)['roles']['B']['binding']
    if (original['protocol']['version'] != 2 or original['row']['model']['digest'] != current['modelPin']
            or original['protocol']['promptPin'] != current['promptPin']):
        raise ValueError('The two B source protocols differ')
    return {'cohorts': counts, 'initialCohort': len(all_ids)-counts['Q5'], 'extendedCohort': len(all_ids),
            'trainingFoldSizes': fold_counts, 'trainingWritersDisjoint': True, 'originalTrainedRows': 1200,
            'modelPin': current['modelPin'], 'promptPin': current['promptPin'], 'selectionPin': pin(selection),
            'foldFilePin': pin(training), 'priorPilotPin': pin(pilot), 'Q1Pin': pin(q1_receipt),
            'stage': 'input verification', 'predictionsScored': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output.resolve()
    if output.parent != (ROOT/'.local/word-table').resolve():
        parser.error('Use a fresh private intake receipt in the current commission')
    result = audit()
    with output.open('x', encoding='utf8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result))
