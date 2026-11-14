"""TP7 receiving contract and choice-vs-rarity controls. No value inference."""
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

from ...admission import implementation_hash
from ...ledger.ids import digest
from ...models.goals import Candidate
from ...preview.judgments import goal_call
from ...preview.surface import WORD, words
from ..back_half.reporting import bind_run, save_json
from ..back_half.state import PilotDeadline
from .exports import read, verify_export
from .goals import lexical_order, ranks

METHODS = ('B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'E1')


def load_choice(directory):
    manifest, pin = verify_export(directory, 'EX5')
    if manifest.get('schema') != 'EX5-choice-v1':
        raise ValueError('EX5 actual format needs a reviewed adapter; provisional contract is EX5-choice-v1')
    rows = read(Path(directory)/'QUESTIONS.json')
    ids = set()
    for row in rows:
        if row['id'] in ids or not 3 <= len(row['answers']) <= 8 or not row['question'].strip() or not row['asker'] or not row['attribution'].startswith('https://'):
            raise ValueError('Invalid public question/attribution')
        ids.add(row['id'])
        answers = row['answers']
        if len({a['id'] for a in answers}) != len(answers):
            raise ValueError('Duplicate answer identity')
        true = [a for a in answers if a['id'] == row['accepted']]
        if len(true) != 1 or not true[0]['author'] or true[0]['author'] == row['asker']:
            raise ValueError('Accepted answer absent or self-authored')
        for answer in answers:
            if not answer['text'].strip() or not math.isfinite(answer['score']) or datetime.fromisoformat(answer['created']).tzinfo is None:
                raise ValueError('Invalid answer text/score/chronology')
    if len(rows) != 2000 or len({r['site'] for r in rows}) != 5:
        raise ValueError('EX5 requires the frozen 2000-question/five-site cohort')
    return rows, pin


def frequencies(rows):
    return Counter(m.group().casefold() for row in rows for a in row['answers'] for m in WORD.finditer(a['text']))


def rank_question(row, tokens, frequency):
    answers = row['answers']
    candidates = [{'id': a['id'], 'text': a['text']} for a in answers]
    bags = [Counter(m.group().casefold() for m in WORD.finditer(a['text'])) for a in answers]
    vocab = sorted(set().union(*bags))
    if not vocab:
        raise ValueError('No candidate words')
    idf = np.array([math.log((1+len(bags))/(1+sum(w in b for b in bags)))+1 for w in vocab])
    query = Counter(m.group().casefold() for m in WORD.finditer(row['question']))
    attended = defaultdict(list)
    for word in words(row['question'], tokens):
        if word['content'] and not word['held']:
            attended[word['text'].casefold()].append(word['nats'])
    total, v = sum(frequency.values()), max(1, len(frequency))
    factors = {
        'B3': np.ones(len(vocab)), 'B4': np.ones(len(vocab)),
        'B5': np.array([-math.log((frequency[w]+1)/(total+v)) for w in vocab]),
        'E1': np.array([np.mean(attended[w]) if w in attended else 1. for w in vocab]),
    }
    orders = {}
    for name, factor in factors.items():
        weight = idf**2 if name == 'B4' else idf
        matrix = np.array([[b[w] for w in vocab] for b in bags])*weight
        vector = np.array([query[w] for w in vocab])*weight*factor
        norm = np.linalg.norm(matrix, axis=1)*np.linalg.norm(vector)
        score = np.divide(matrix@vector, norm, out=np.zeros(len(bags)), where=norm > 0)
        orders[name] = [answers[i]['id'] for i in sorted(range(len(answers)), key=lambda i: (-score[i], answers[i]['id']))]
    orders.update(B0=[a['id'] for a in sorted(answers, key=lambda a: (-a['score'], a['id']))],
                  B1=[a['id'] for a in sorted(answers, key=lambda a: (datetime.fromisoformat(a['created']), a['id']))],
                  B2=[a['id'] for a in sorted(answers, key=lambda a: (-len(list(WORD.finditer(a['text']))), a['id']))])
    accepted = next(a for a in answers if a['id'] == row['accepted'])
    return {'id': row['id'], 'site': row['site'], 'acceptedNotTopScore': accepted['score'] < max(a['score'] for a in answers),
            'rows': {name: ranks(order, row['accepted']) for name, order in orders.items()},
            'contentWordsWeighted': sum(map(len, attended.values())), 'candidateIdsPin': digest(candidates)}


def choice_summary(rows, *, draws=2000):
    if not rows:
        return {'status': 'no observations'}
    banks = [np.array([i for i, row in enumerate(rows) if row['site'] == site]) for site in sorted({r['site'] for r in rows})]
    rng = np.random.default_rng(20261112)
    samples = [np.concatenate([rng.choice(bank, len(bank), replace=True) for bank in banks]) for _ in range(draws)]
    results, means = {}, {}
    names = [name for name in (*METHODS, 'E2') if all(name in r['rows'] for r in rows)]
    for name in names:
        results[name] = {}
        for metric in ('top1', 'reciprocalRank'):
            value = np.array([r['rows'][name][metric] for r in rows])
            results[name][metric] = {'mean': float(value.mean()), 'interval': np.quantile([value[s].mean() for s in samples], [.025, .975]).tolist()}
            if metric == 'top1':
                means[name] = value
    base = max(('B3', 'B4', 'B5'), key=lambda n: means[n].mean())
    bootstrap = [float(means['E1'][s].mean()-max(means[n][s].mean() for n in ('B3', 'B4', 'B5'))) for s in samples]
    interval = np.quantile(bootstrap, [.025, .975]).tolist()
    return {'status': 'complete', 'questions': len(rows), 'sites': len(banks), 'rows': results,
            'primary': {'gain': float(means['E1'].mean()-means[base].mean()), 'bestRarityBaseline': base,
                        'interval': interval, 'bar': .02, 'clearsBar': interval[0] > .02,
                        'uncertainty': 'paired question bootstrap within site; best rarity baseline reselected in each draw'},
            'B0': 'descriptive only; acceptance can raise final answer scores',
            'productionAdmission': False, 'scope': 'accepted-answer choice; not set points or values'}


def choice_run(directory, output, reader, check):
    rows, data_pin = load_choice(directory)
    output = Path(output)
    identity = {'task': 'TP7-E1', 'dataPin': data_pin, 'codePin': implementation_hash(), 'reader': reader.identity}
    bind_run(output, identity)
    deadline = PilotDeadline(output/'deadline.json', hours=8)
    freq, results = frequencies(rows), []
    report = {'identity': identity, 'status': 'running', 'productionAdmission': False}
    def bounded():
        check(); deadline.check()
    try:
        for row in rows:
            bounded()
            path = output/'questions'/f"{digest(row['id'])}.json"
            key = digest([identity, row])
            if path.exists():
                result = checked_observation(read(path), key)
            else:
                result = rank_question(row, reader.score(row['question'], check=bounded), freq)
                save_json(path, {'key': key, 'result': result, 'sha256': digest(result)})
            results.append(result)
            save_json(output/'progress.json', {'questions': len(results), 'total': len(rows)})
        report['status'] = 'complete'
    except Exception as exc:
        report.update(status='stopped', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report.update(all=choice_summary(results), acceptedNotTopScore=choice_summary([r for r in results if r['acceptedNotTopScore']]))
        save_json(output/'receipt.json', report)
    return report


def checked_observation(saved, key):
    if saved.get('key') != key or saved.get('sha256') != digest(saved.get('result')):
        raise ValueError('Choice observation pin differs')
    return saved['result']


def completed_e1(directory, rows, data_pin):
    directory = Path(directory)
    receipt = read(directory/'receipt.json')
    identity = receipt['identity']
    if (receipt.get('status') != 'complete' or identity['dataPin'] != data_pin
            or identity['codePin'] != implementation_hash() or receipt['all']['questions'] != len(rows)):
        raise ValueError('E2 requires complete E1 on the identical cohort and implementation')
    return {row['id']: checked_observation(read(directory/'questions'/f"{digest(row['id'])}.json"), digest([identity, row])) for row in rows}


def choice_goals(rows, completed_e1, backend, cache, check, on_progress):
    selected = sorted(rows, key=lambda r: digest(['TP7-E2', r['id']]))[:150]
    results = []
    for row in selected:
        check()
        key, answer = goal_call(backend, cache, [], row['question'], check=check)
        candidate = Candidate(id=key, maker='pilot', regions=[row['id']], depth=1, **answer)
        if candidate.cue_ids or candidate.cue_match:
            raise ValueError('E2 goal cites nonexistent cues')
        cache.put(key, answer)
        order = lexical_order(candidate.label+' '+candidate.description, [{'id': a['id'], 'text': a['text']} for a in row['answers']])
        previous = completed_e1[row['id']]
        results.append({**previous, 'rows': {**previous['rows'], 'E2': ranks(order, row['accepted'])}})
        on_progress(results)
    return {'all': choice_summary(results), 'acceptedNotTopScore': choice_summary([r for r in results if r['acceptedNotTopScore']])}
