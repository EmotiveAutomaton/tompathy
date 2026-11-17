"""TP18b: commissioned circular pause-remainder diagnostic, no display admission."""
import json
import shutil
from pathlib import Path

import numpy as np

from ...features.pause_remainder import add_remainder
from ...packs.registry import sha256
from ...preview.readers import LocalReader
from ...preview.surface import words
from ..back_half.attention import word_forecast
from ..back_half.metrics import paired_auc
from ..back_half.reporting import save_json
from .artifacts import seal
from .checkpoint import completed
from .tp18 import ADDITIONS, augment


def run(source, primary, model, output, check):
    source, primary, output = map(Path, (source, primary, output))
    original = completed(primary, 'TP18')
    path = source/'attention/window/tables.json'
    if sha256(path) != original['sources']['tablesPin']:
        raise ValueError('TP18b must retain original TP18 tables')
    tables = augment(json.loads(path.read_text(encoding='utf8')))
    receipt = {'card': 'TP27', 'status': 'running', 'productionAdmission': False, 'ledger': 'no ledger row',
        'scope': 'Circular diagnostic only: stop key and residual share the timing source; no independent accuracy or maker claim',
        'sourceReceiptPin': sha256(primary/'receipt.json'), 'tablesPin': sha256(path),
        'baselineForecastPin': sha256(primary/'all-forecasts.npz'),
        'protocol': {'fit': 'within-writer OLS, intercept, length/log1p-frequency/sentence-start/preceding-punctuation/Smol135 surprisal',
            'frequency': 'each writer own saved session words', 'regression_rows': 'all writer words with observed logPause',
            'prediction_rows': 'unchanged original eligible writer words and five folds',
            'comparison': 'original five-feature baseline; second contrast against saved TP18 combined model',
            'bar': 'lower writer interval bound >.02, diagnostic only even if cleared',
            'display': 'unchanged; external Sounding Line KP1 is required'}, 'row': None}
    save = lambda: save_json(output/'receipt.json', receipt)
    save()
    model = Path(model)
    intake = json.loads((model/'intake.json').read_text(encoding='utf8'))
    if intake['id'] != 'HuggingFaceTB/SmolLM2-135M' or intake['revision'] != '93efa2f097d58c2a74874c7e644dbc9b0cee75a2':
        raise ValueError('Uncommissioned Smol135 revision')
    local = output/'smol135'
    local.mkdir()
    for name, pin in intake['files'].items():
        check()
        origin = (model/name).resolve()
        if not origin.is_relative_to(model.resolve()) or sha256(origin) != pin:
            raise ValueError('Original Smol135 bytes changed')
        shutil.copyfile(origin, local/name)
        if sha256(local/name) != pin:
            raise ValueError('Smol135 copy differs')
    save_json(local/'manifest.json', {'model': intake['id'], 'revision': intake['revision'], 'files': intake['files']})
    reader = LocalReader(local, output/'token-cache', threads=2, precision='float32')
    if reader.identity['id'] != 'HuggingFaceTB/SmolLM2-135M':
        raise ValueError('TP27 uses the pinned float32 Smol135 scorer only')
    receipt['reader'] = reader.identity
    save()
    for i, session in enumerate(tables):
        check()
        scored = words(session['text'], reader.score(session['text'], check=check))
        lookup = {(w['start'], w['end']): w['nats'] for w in scored}
        values = []
        for word in session['words']:
            key = (word['start'], word['end'])
            if key not in lookup:
                raise ValueError('Smol135 differs from original word alignment')
            word['scores']['smol135_nats'] = float(lookup[key])
            values.append(float(lookup[key]))
        save_json(output/'word-scores'/f'{i:05d}.json', {'index': i, 'source': receipt['tablesPin'], 'values': values})
        save_json(output/'progress.json', {'sessions': i+1, 'total': len(tables)})
    receipt['residual'] = add_remainder(tables, check)
    rows = [(s, w) for s in tables for w in s['words'] if w['source'] == 'writer' and type(w['stop']) is bool and w['eligible']]
    if any('pause_remainder' not in w['scores'] for _, w in rows):
        raise ValueError('A TP18 eligible word lacks timing; do not change the cohort')
    check()
    selected, prediction = word_forecast(tables, [*ADDITIONS, 'pause_remainder'])
    if [(s['session'], w['start'], w['end']) for s, w in selected] != [(s['session'], w['start'], w['end']) for s, w in rows]:
        raise ValueError('TP18b cohort differs')
    if sha256(primary/'all-forecasts.npz') != receipt['baselineForecastPin']:
        raise ValueError('Saved TP18 forecasts changed during diagnostic scoring')
    with np.load(primary/'all-forecasts.npz', allow_pickle=False) as d:
        baseline, combined = d['baseline'], d['forecast']
    if baseline.shape != prediction.shape or combined.shape != prediction.shape:
        raise ValueError('Saved TP18 predictions do not cover the same cohort')
    y, writers = [w['stop'] for _, w in rows], [s['writer'] for s, _ in rows]
    result = paired_auc(y, baseline, prediction, writers)
    result.update(diagnostic_bar_cleared=result['interval'][0] > .02, words=len(rows), sessions=len(tables), independent_accuracy=False)
    receipt['row'] = result
    receipt['versus_combined'] = paired_auc(y, combined, prediction, writers)
    np.savez(output/'forecasts.npz', baseline=baseline, combined=combined, residual=prediction)
    receipt.update(status='complete', artifactsPin=seal(output, [output/'forecasts.npz', output/'word-scores'], check))
    save()
