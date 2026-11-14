"""Resumable, exact-pin TP2/TP5 scoring; exploratory ladders never change primaries."""
import gc
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from ...admission import implementation_hash
from ...ledger.ids import digest
from ...preview.readers import LocalReader
from ..back_half import attention as original
from ..back_half.data import history_contexts
from ..back_half.metrics import paired_auc
from ..back_half.reporting import bind_run, public_receipt, save_json
from .exports import read

RUNGS = (0, 1, 2, 4, 8, 16)


def ladder_contexts(sessions, reader, k):
    if k not in RUNGS:
        raise ValueError('Unregistered history rung')
    tokens = {s['session']: reader.encode(s['text'])['input_ids'] for s in sessions}
    output = {}
    for target in sessions:
        earlier = sorted((s for s in sessions if s['writer'] == target['writer'] and s['time'] < target['time']),
                         key=lambda s: (s['time'], s['session']))
        selected = earlier[-k:] if k and len(earlier) >= k else []
        own = [t for s in selected for t in tokens[s['session']]][-1024:]
        output[target['session']] = {'own': own, 'other': [], 'eligible': bool(k and len(earlier) >= k and len(own) >= 512),
                                     'k': k, 'priorSessions': len(earlier), 'selectedSessions': [s['session'] for s in selected]}
    return output


def score_resumable(sessions, reader, directory, data_pin, contexts, check):
    directory = Path(directory)
    identity = {'data': data_pin, 'code': implementation_hash(), 'reader': reader.identity,
                'sessions': digest(sessions), 'contexts': digest(contexts)}
    bind_run(directory, identity)
    started, fresh, tables = monotonic(), 0, []
    for index, session in enumerate(sessions):
        check()
        key = digest([identity, session['session']])
        path = directory / 'sessions' / f'{key}.json'
        if path.exists():
            saved = read(path)
            if saved.get('key') != key or saved.get('sha256') != digest(saved.get('table')):
                raise ValueError('Saved observation integrity failure')
            table = saved['table']
        else:
            table = original.score_sessions([session], reader, contexts=contexts, check=check)[0]
            save_json(path, {'key': key, 'table': table, 'sha256': digest(table)})
            fresh += 1
        tables.append(table)
        elapsed = monotonic()-started
        save_json(directory/'progress.json', {'at': datetime.now(UTC).isoformat(), 'sessions': index+1,
                    'total': len(sessions), 'newSessions': fresh, 'elapsedSeconds': elapsed,
                    'remainingSecondsAtObservedRate': (len(sessions)-index-1)*elapsed/fresh if fresh else None,
                    'readerMetrics': reader.metrics})
    save_json(directory/'tables.json', tables)
    return tables, digest(identity)


def run(intake, readers, output, check, threads=2, phases=('window', 'kv', 'smol', 'ladder')):
    sessions = read(Path(intake)/'sessions.json')
    data_pin = digest(read(Path(intake)/'intake.json'))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for phase in phases:
        if phase not in {'window', 'kv', 'smol', 'ladder'}:
            raise ValueError('Unknown attention phase')
        check()
        save_json(output/'phase.json', {'phase': phase, 'at': datetime.now(UTC).isoformat()})
        model = 'smol' if phase == 'smol' else 'qwen'
        reader = LocalReader(Path(readers)/model, output/'raw-cache', threads=threads,
                             precision='float32', scoring='kv' if phase == 'kv' else 'window',
                             entropy=phase in {'window', 'ladder'})
        try:
            if phase == 'ladder':
                results = []
                for k in RUNGS:
                    if k == 0:
                        tables = read(output/'window'/'tables.json')
                        pin = digest(read(output/'window'/'run-identity.json'))
                    else:
                        contexts = ladder_contexts(sessions, reader, k)
                        tables, pin = score_resumable(sessions, reader, output/f'k{k}', data_pin, contexts, check)
                    require = ['V4'] if k else []
                    try:
                        rows, baseline = original.word_forecast(tables, ['V0'], require=require)
                        _, score = original.word_forecast(tables, ['V4' if k else 'V0'], require=require)
                        result = paired_auc([w['stop'] for _, w in rows], baseline, score, [s['writer'] for s, _ in rows])
                        result['sessions'] = len({s['session'] for s, _ in rows})
                    except ValueError as exc:
                        result = {'status': 'insufficient-support', 'reason': str(exc)}
                    results.append({'k': k, 'registered': False, 'enginePin': pin, **result})
                    save_json(output/'history-ladder.json', {'status': 'running' if k != 16 else 'complete',
                              'contextLimit': 1024, 'minimumHistoryTokens': 512, 'dataPin': data_pin, 'rows': results})
                continue
            contexts = history_contexts(sessions, reader) if phase == 'window' else {}
            tables, pin = score_resumable(sessions, reader, output/phase, data_pin, contexts, check)
            report = original.attention_report(tables, engine_pin=pin, data_pin=data_pin)
            save_json(output/f'attention-{phase}.json', public_receipt(report))
            if phase == 'window':
                save_json(output/'involvement.json', public_receipt(original.involvement_report(tables, engine_pin=pin, data_pin=data_pin)))
            elif phase == 'kv':
                save_json(output/'binding-parity.json', original.binding_parity(read(output/'window'/'tables.json'), tables))
            elif phase == 'smol':
                reference = read(output/'attention-window.json')['rows'][0]['engine']
                delta = report['rows'][0]['engine']-reference
                save_json(output/'reader-ladder.json', {'status': 'complete', 'qwen': reference,
                          'smol': report['rows'][0]['engine'], 'difference': delta,
                          'candidateFirstPaint': abs(delta) <= .01, 'defaultChanged': False,
                          'dataPin': data_pin, 'enginePin': pin})
                combined = merge_readers(read(output/'window'/'tables.json'), tables)
                combined_pin = digest([pin, read(output/'attention-window.json')['enginePin'], 'V3 mean page-scaled readers'])
                save_json(output/'attention-exploratory.json', public_receipt(original.attention_report(
                    combined, engine_pin=combined_pin, data_pin=data_pin)))
        finally:
            del reader
            gc.collect()
    save_json(output/'complete.json', {'at': datetime.now(UTC).isoformat(), 'phases': list(phases), 'dataPin': data_pin})


def merge_readers(qwen, smol):
    if [(s['session'], s['writer'], s['fold']) for s in qwen] != [(s['session'], s['writer'], s['fold']) for s in smol]:
        raise ValueError('Reader ladder cohorts differ')
    combined = deepcopy(qwen)
    for left, right in zip(combined, smol, strict=True):
        if [(w['start'], w['end'], w['eligible']) for w in left['words']] != [(w['start'], w['end'], w['eligible']) for w in right['words']]:
            raise ValueError('Reader ladder word coverage differs')
        for a, b in zip(left['words'], right['words'], strict=True):
            a['scores']['V2'] = b['scores']['V0']
            a['scores']['V3'] = (a['scores']['V0']+b['scores']['V0'])/2
    return combined
