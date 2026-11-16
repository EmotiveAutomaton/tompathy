"""Verified reuse of completed TP19 artifacts after a population optimizer limit."""
import json
import shutil
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .checkpoint import completed


def restore(source, output, reader_job, *, ledger_path=None, motive_job=None, check=lambda: None):
    source, output = Path(source).resolve(), Path(output)
    read = lambda name: json.loads((source/name).read_text(encoding='utf8'))
    report, failed, audit, plan = (read(n) for n in
        ('receipt.json', 'failed.json', 'exit-verification.json', 'plan.json'))
    if not all(audit.get(k) for k in ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent')):
        raise ValueError('TP19 continuation requires verified native exit and releases')
    if (report.get('card') != 'TP19' or report.get('status') != 'running'
            or (source/'complete.json').exists() or failed.get('type') != 'ValueError'
            or not failed.get('reason', '').startswith('Prequential population MAP failed')
            or ledger_path is not None or motive_job is not None or report.get('motives') is not None):
        raise ValueError('Only the incomplete TP19 population-fit failure can continue')
    if set(report['rows']) != {'0', '1', '2'} or 'handling' not in report['rows']['0']:
        raise ValueError('Expected completed choice rows and baseline handling')
    current_root = Path(__file__).resolve().parents[3]
    allowed_changes = {'tompathy_engine/eval/harness.py',
        'tompathy_engine/eval/readers/tp19.py', 'tompathy_engine/eval/readers/reporting.py'}
    for name, pin in plan['snapshotFiles'].items():
        old = (source/'code'/name).resolve()
        if not old.is_relative_to(source/'code') or sha256(old) != pin:
            raise ValueError('Source snapshot changed')
        if name not in allowed_changes and sha256(current_root/name) != pin:
            raise ValueError('Continuation data/feature code changed')
    reader_job = Path(reader_job)
    reader = completed(reader_job, 'TP10-L3')
    identity = report['reader']
    if (identity['sourceReceiptPin'] != sha256(reader_job/'receipt.json')
            or identity['selectedSeed'] != reader['selected_seed']):
        raise ValueError('Reader source differs')
    root = (reader_job/f"seed-{reader['selected_seed']}").resolve()
    for name, pin in reader['rows'][str(reader['selected_seed'])]['files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root) or sha256(path) != pin:
            raise ValueError('Reader file binding differs')
    if sha256(root/'head.npz') != identity['headPin']:
        raise ValueError('Reader head binding differs')
    files = [p for p in (source/'ledger').rglob('*') if p.is_file()]
    files += [source/n for n in ['intake.json','option-features.json',
        'choice-0.npy','choice-1.npy','choice-2.npy','handling-0.json']]
    for stage in (1, 2):
        if 'handling' in report['rows'][str(stage)]:
            files.append(source/f'handling-{stage}.json')
    pins = {}
    for index, path in enumerate(files):
        if index % 64 == 0:
            check()
            save_json(output/'phase.json', {'phase':'restore-artifacts','files':index,'total':len(files)})
        name = path.relative_to(source).as_posix()
        dest = output/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise ValueError('Preserve previous continuation output')
        pin = sha256(path)
        shutil.copyfile(path, dest)
        if sha256(dest) != pin or sha256(path) != pin:
            raise ValueError('Copied TP19 artifact differs')
        pins[name] = pin
    saved = json.loads((output/'option-features.json').read_text(encoding='utf8'))
    if saved['reader'] != identity or saved['motive'] is not None:
        raise ValueError('Saved feature reader identity differs')
    for stage in range(3):
        p = np.load(output/f'choice-{stage}.npy', allow_pickle=False)
        if (p.shape != (report['rows'][str(stage)]['choices'], 5)
                or not np.isfinite(p).all() or np.any(p < 0)
                or not np.allclose(p.sum(1), 1)):
            raise ValueError('Invalid preserved choice forecasts')
    continuation = {'kind': 'population-iteration-limit-continuation',
        'sourceReceiptPin': sha256(source/'receipt.json'), 'failurePin': sha256(source/'failed.json'),
        'exitVerificationPin': sha256(source/'exit-verification.json'),
        'artifactCount': len(pins), 'completedChoiceRowsReused': 3,
        'completedHandlingRowsReused': sum('handling' in r for r in report['rows'].values()),
        'completedReaderInferenceRepeated': False, 'completedResearchGatesRepeated': False}
    save_json(output/'continuation-artifacts.json', {'source':str(source), 'files':pins,
        'sourceSnapshot':plan['snapshotFiles'], 'continuation':continuation})
    report['continuation'] = continuation
    check()
    return output/'ledger', report, saved
