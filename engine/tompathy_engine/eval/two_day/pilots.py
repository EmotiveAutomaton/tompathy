"""Bounded runners for received edits, goals, RAID and human edit intentions."""
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from ...admission import implementation_hash
from ...ledger.ids import digest
from ...preview.fixed_backend import FixedQwen
from ...preview.judgments import fixed_reader
from ...preview.readers import LocalReader
from ...transcribe.cache import Cache
from ..back_half.edits import (
    compare_cascade,
    first_call_projection,
    q8_sample,
    sample_coverage,
    sample_edits,
    scores,
)
from ..back_half.goals import pilot_document, pilot_inputs, pilot_summary, without_answers
from ..back_half.reporting import bind_run, save_json
from ..back_half.resources import guard
from ..back_half.state import PilotDeadline
from .datasets import INTENTIONS
from .exports import read, sha
from .goals import lexical_order, ranks, rerank
from .robustness import ATTACKS, MomentReader, normalize, rate, robustness_report, signals

HUMAN_MAP = {'typo': 'fluency', 'grammar': 'fluency', 'wording': 'clarity', 'reorder': 'coherence',
             'tone': 'style', 'add content': 'meaning-changed', 'remove content': 'meaning-changed',
             'format': 'abstain', 'unclear': 'abstain'}


def intent_scores(truth, predictions):
    if not truth or len(truth) != len(predictions) or not set(truth) <= set(INTENTIONS) or not set(predictions) <= {*INTENTIONS, 'abstain'}:
        raise ValueError('Invalid human intention observations')
    f1 = {}
    for name in INTENTIONS:
        tp = sum(t == p == name for t, p in zip(truth, predictions, strict=True))
        denom = truth.count(name)+predictions.count(name)
        f1[name] = 2*tp/denom if denom else 0.
    return {'macroF1': float(np.mean(list(f1.values()))), 'perIntention': f1, 'pairs': len(truth),
            'abstentions': predictions.count('abstain'), 'abstentionRate': predictions.count('abstain')/len(truth)}


def edit_run(prepared, output, url, check, *, human=False, feature_output=None):
    prepared, output = Path(prepared), Path(output)
    prefix = 'human-edits' if human else 'edits'
    rows, intake = read(prepared/f'{prefix}.json'), read(prepared/f'{prefix}-intake.json')
    features = None
    if not human and feature_output is not None:
        rows, intake = read(prepared/'edits-enriched.json'), read(prepared/'edits-enrichment.json')
        feature_output = Path(feature_output)
        feature_receipt = read(feature_output/'receipt.json')
        if digest(rows) != intake['featureRowsPin'] or feature_receipt['dataPin'] != digest(intake) or feature_receipt['codePin'] != implementation_hash():
            raise ValueError('Feature classifier differs from this exact edit cohort/code')
        features = (np.asarray(read(feature_output/'probabilities.json')), read(feature_output/'gates.json'), read(feature_output/'timings.json'))
    data_pin = digest([rows, intake])
    bind_run(output, {'task': prefix, 'dataPin': data_pin, 'codePin': implementation_hash()})
    indices = list(range(len(rows))) if human else sample_edits(rows)
    deadline = PilotDeadline(output/'deadline.json', hours=6)
    path = output/'calls.json'
    complete = read(path) if path.exists() else {}
    report = {'status': 'running', 'dataPin': data_pin, 'codePin': implementation_hash(), 'requested': len(indices),
              'productionAdmission': False, 'classifier': 'authenticated recovered EX2 features' if features else 'requires completed exact feature run',
              'bar': None if human else 'unchanged registered TP3 comparison; cascade unavailable'}
    if not human:
        report['sampleCoverage'] = sample_coverage(rows, indices)
        report['upstreamHardLabelReference'] = scores([r['category'] for r in rows], [r['upstreamPrediction'] for r in rows])
    backend = None
    def bounded():
        check(); deadline.check()
    try:
        bounded(); guard(large_model=True)
        backend = FixedQwen(url, timeout=600, before_load=lambda: guard(large_model=True))
        reader = fixed_reader(backend, Cache(output/'q8.sqlite'))
        report['readerPin'] = reader.pin
        for n, index in enumerate(indices):
            if n == min(50, len(indices)):
                projection = first_call_projection(rows, indices, complete, reader.pin, data_pin)
                save_json(output/'projection.json', projection)
                if projection['projectedSeconds'] is None or projection['projectedSeconds'] >= 6*3600:
                    report['status'] = 'stopped: first-50 projection not below six hours'
                    break
            complete = q8_sample(reader, rows, [index], check=bounded, completed=complete)
            save_json(path, complete)
            save_json(output/'progress.json', {'completed': len(complete), 'requested': len(indices), 'at': datetime.now(UTC).isoformat()})
        else:
            report['status'] = 'complete direct Q8' if human or not features else 'complete comparison; cascade speed unqualified'
        if len(complete) >= min(50, len(indices)):
            save_json(output/'projection.json', first_call_projection(rows, indices, complete, reader.pin, data_pin))
    except Exception as exc:
        report.update(status='stopped', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        selected = [rows[i] for i in indices if str(rows[i]['id']) in complete]
        report['completed'] = len(selected)
        if selected and human:
            truth = [r['intention'] for r in selected]
            report['direct'] = intent_scores(truth, [HUMAN_MAP[complete[str(r['id'])]['raw']] for r in selected])
            report['majority'] = intent_scores(truth, [intake['majorityLabelFromTrain']]*len(truth))
            report['sourceSplits'] = dict(Counter(r['split'] for r in selected))
        elif selected:
            answers = [complete[str(r['id'])] for r in selected]
            report['direct'] = scores([r['category'] for r in selected],
                                      ['unclear' if a['raw'] == 'unclear' else a['category'] for a in answers])
            if features:
                report['comparison'] = compare_cascade(rows, *features, complete)
        try:
            if backend:
                backend.close(recover=True)
        except Exception:
            report.update(status='cleanup-failed', cleanup='failed')
            raise
        finally:
            save_json(output/'receipt.json', report)
    return report


def lexical_baseline(tasks):
    return [{'id': t['id'], 'author': t['author'], **ranks(lexical_order(without_answers(t['text'], t['sections'])[:12000], t['candidates']), t['truth'])} for t in tasks]


def lexical_summary(rows, draws=2000):
    authors = sorted({r['author'] for r in rows})
    if len(authors) < 2:
        return {'status': 'insufficient author support'}
    rng = np.random.default_rng(20261112)
    bank = [[r for r in rows if r['author'] == a] for a in authors]
    samples = [[r for i in rng.integers(len(bank), size=len(bank)) for r in bank[i]] for _ in range(draws)]
    return {'documents': len(rows), 'authors': len(authors),
            **{metric: {'mean': float(np.mean([r[metric] for r in rows])),
                        'interval': np.quantile([np.mean([r[metric] for r in sample]) for sample in samples], [.025, .975]).tolist()}
               for metric in ('top1', 'reciprocalRank')}}


def goal_comparison(rows, draws=2000):
    authors = sorted({r['author'] for r in rows})
    if len(authors) < 2:
        return {'status': 'insufficient author support'}
    rng = np.random.default_rng(20261112)
    bank = [[r for r in rows if r['author'] == a] for a in authors]
    samples = [[r for i in rng.integers(len(bank), size=len(bank)) for r in bank[i]] for _ in range(draws)]
    result = {'documents': len(rows), 'authors': len(authors), 'rows': {}}
    for name in ('tfidf', 'reader', 'rerank'):
        result['rows'][name] = {metric: {'mean': float(np.mean([r[name][metric] for r in rows])),
            'interval': np.quantile([np.mean([r[name][metric] for r in s]) for s in samples], [.025, .975]).tolist()}
            for metric in ('top1', 'reciprocalRank')}
    result['rerankGain'] = {'mean': float(np.mean([r['rerank']['top1']-r['tfidf']['top1'] for r in rows])),
        'interval': np.quantile([np.mean([r['rerank']['top1']-r['tfidf']['top1'] for r in s]) for s in samples], [.025, .975]).tolist()}
    return result


def goal_run(prepared, readers, output, url, check):
    prepared, output = Path(prepared), Path(output)
    tasks = read(prepared/'goals.json')
    bind_run(output, {'dataPin': digest(tasks), 'codePin': implementation_hash(), 'kind': 'TP4'})
    baseline = lexical_baseline(tasks)
    save_json(output/'tfidf.json', baseline)
    deadline = PilotDeadline(output/'deadline.json')
    path = output/'documents.json'
    completed = read(path) if path.exists() else {}
    cache, backend = Cache(output/'goals.sqlite'), None
    report = {'status': 'running', 'dataPin': digest(tasks), 'codePin': implementation_hash(),
              'productionAdmission': False, 'pilot': True, 'tfidfBaseline': lexical_summary(baseline)}
    comparisons = []
    def bounded():
        check(); deadline.check()
    try:
        bounded(); guard(large_model=True)
        reader = LocalReader(Path(readers)/'qwen', output/'scores', threads=1)
        backend = FixedQwen(url, timeout=600, before_load=lambda: guard(large_model=True))
        report['enginePin'] = digest([implementation_hash(), reader.identity, backend.settings, backend.model_id])
        for task in tasks:
            inputs, cues = pilot_inputs(task['text'], task['sections'], task['title'], task['headings'], reader, bounded)
            def progress(value):
                completed[value['id']] = value
                save_json(path, completed)
            result = pilot_document(task, inputs, cues, backend, cache, check=bounded,
                                    completed=completed.get(task['id']), on_progress=progress)
            # The same existing body-goal call provides the second-stage query;
            # candidates are never put into its prompt, and no new model call is added.
            statement = cache.get(result['readers']['body']['callKey'])
            comparisons.append({'id': task['id'], 'author': task['author'],
                **rerank(statement['label']+' '+statement['description'], inputs['body'], task['candidates'], task['truth'])})
            save_json(output/'rerank.json', comparisons)
            save_json(output/'progress.json', {'documents': len(comparisons), 'total': len(tasks)})
        report['status'] = 'complete pilot'
    except Exception as exc:
        report.update(status='stopped pilot', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        paired = [r for r in completed.values() if set(r['readers']) == {'body', 'departures', 'cues-only'}]
        report['completedDocuments'] = len(paired)
        if len({r['author'] for r in paired}) >= 2:
            report['pilotSummary'] = pilot_summary(paired)
        report['wordMatchingComparison'] = goal_comparison(comparisons)
        try:
            if backend:
                backend.close(recover=True)
        except Exception:
            report.update(status='cleanup-failed', cleanup='failed')
            raise
        finally:
            save_json(output/'receipt.json', report)
    return report


def robustness_run(dataset, readers, output, check, *, model='qwen', auxiliary=None, omit_paraphrase=False):
    dataset, output = Path(dataset), Path(output)
    manifest = read(dataset/'manifest.json')
    if manifest['status'] != 'complete' or manifest['rowsPin'] != sha(dataset/'rows.json'):
        raise ValueError('RAID intake incomplete or changed')
    rows = read(dataset/'rows.json')
    auxiliary_rows, auxiliary_pin = [], None
    if auxiliary:
        from .datasets import non_native
        auxiliary_rows, auxiliary_pin = non_native(auxiliary)
    bind_run(output, {'task': 'TP6', 'dataPin': digest(manifest), 'codePin': implementation_hash(), 'model': model,
                      'auxiliaryPin': auxiliary_pin, 'omitParaphrase': omit_paraphrase})
    deadline = PilotDeadline(output/'deadline.json')
    reader = MomentReader(Path(readers)/model, output/'tokens', threads=2, precision='float32')
    results, aux, report = {}, {}, {'status': 'running', 'dataPin': digest(manifest), 'enginePin': digest(reader.identity), 'productionAdmission': False}
    def bounded():
        check(); deadline.check()
    try:
        ordered = sorted(rows, key=lambda r: (r['attack'] != 'none', r['attack'] == 'paraphrase', r['rowIndex']))
        for row in ordered:
            if omit_paraphrase and row['attack'] == 'paraphrase':
                continue
            bounded()
            path = output/'observations'/f"{digest([report['enginePin'], row['id'], row['sha256']])}.json"
            if path.exists():
                observation = read(path)
                pin = observation.pop('observationPin', None)
                if pin != digest(observation) or observation.get('sourcePin') != row['sha256'] or observation.get('enginePin') != report['enginePin']:
                    raise ValueError('Saved robustness observation pin differs')
            else:
                observation = {'sourcePin': row['sha256'], 'enginePin': report['enginePin']}
                for mode in (('raw', 'normalized') if row['attack'] in ATTACKS else ('raw',)):
                    text = normalize(row['generation']) if mode == 'normalized' else row['generation']
                    observation[mode] = signals(text, reader.moment_score(text, bounded))
                save_json(path, {**observation, 'observationPin': digest(observation)})
            results[row['id']] = observation
            save_json(output/'progress.json', {'documents': len(results), 'total': len(rows), 'at': datetime.now(UTC).isoformat()})
        for row in auxiliary_rows:
            bounded()
            aux[row['id']] = signals(row['text'], reader.moment_score(row['text'], bounded))
            save_json(output/'auxiliary.json', aux)
    except Exception as exc:
        report.update(status='stopped', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        previous_status = report['status']
        report.update(robustness_report(rows, results))
        if previous_status == 'stopped':
            report['status'] = 'stopped; partial observations retained'
        report['omittedParaphrase'] = omit_paraphrase
        if auxiliary:
            report['nonNativeWriting'] = {'dataPin': auxiliary_pin, 'completed': len(aux), 'total': len(auxiliary_rows),
                'status': 'complete' if len(aux) == len(auxiliary_rows) else 'partial',
                'rates': {name: rate([int((1 if name == 'FD' else -1)*r[name] > threshold['orientedThreshold']) for r in aux.values()])
                          for name, threshold in report['thresholds'].items()}}
        report['completedDocuments'] = len(results)
        report['totalDocuments'] = len(rows)
        save_json(output/'receipt.json', report)
    return report
