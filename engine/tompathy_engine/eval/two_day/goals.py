"""EX3 pinned Git reconstruction and a candidate-only lexical rerank control."""
import hashlib
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np

from ...preview.surface import WORD
from ..back_half.goals import pilot_sample
from .exports import read, verify_export


def pinned_document(record, roots):
    root = Path(roots[record['repository']]).resolve()
    revision, name = record['commit'], record['relative_path']
    if not re.fullmatch('[a-f0-9]{40}', revision) or name.startswith(('/', '-')) or '..' in Path(name).parts or ':' in name or '\\' in name:
        raise ValueError('Unsafe Git source reference')
    result = subprocess.run(['git', '-C', str(root), 'show', f'{revision}:{name}'], capture_output=True, check=True, timeout=30,
                            env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})
    raw = result.stdout
    if hashlib.sha256(raw).hexdigest() != record['source_sha256']:
        raise ValueError('EX3 source Git bytes differ')
    text = raw.decode('utf8').replace('\r\n', '\n').replace('\r', '\n')
    if hashlib.sha256(text.encode()).hexdigest() != record['decoded_lf_sha256']:
        raise ValueError('EX3 decoded source differs')
    return text


def parts(text, sections):
    output = []
    previous = -1
    for section in sections:
        a, b, end, tree = (section[k] for k in ('start_codepoint', 'body_start_codepoint', 'end_codepoint', 'subtree_end_codepoint'))
        if not previous < a < b <= end <= tree <= len(text):
            raise ValueError('EX3 section offsets are invalid')
        heading = re.sub(r'^#+\s*|\s*#+$', '', text[a:b].splitlines()[0]).strip()
        output.append({**section, 'heading': heading, 'body': text[b:end].strip(), 'subtree': text[b:tree].strip()})
        previous = a
    return output


def ex3_tasks(directory, roots):
    _, pin = verify_export(directory, 'EX3')
    task = read(Path(directory)/'TASK.json')
    docs = {d['document_id']: d for d in task['documents']}
    if len(docs) != len(task['documents']):
        raise ValueError('Duplicate EX3 document')
    roster = [{'id': q['document_id'], 'repository': docs[q['document_id']]['repository'], 'query': q} for q in task['queries']]
    chosen = pilot_sample(roster)
    needed = {cid for q in chosen for cid in q['query']['candidate_ids']} | {q['id'] for q in chosen}
    source = {}
    for cid in sorted(needed):
        record = docs[cid]
        text = pinned_document(record, roots)
        sections = parts(text, record['sections'])
        motivation = '\n\n'.join(p['subtree'] for p in sections if p['role'] == 'motivation')
        if not motivation:
            raise ValueError('Missing candidate Motivation')
        source[cid] = (text, sections, motivation)
    output = []
    for item in chosen:
        ident, query = item['id'], item['query']
        ids = query['candidate_ids']
        if len(ids) != 50 or len(set(ids)) != 50 or ids[query['truth_position']] != ident:
            raise ValueError('EX3 candidate order/truth binding differs')
        text, sections, _ = source[ident]
        # Start with the exact received query parts; additionally hide answer-like
        # abstract/summary sections for the engine pilot, as preregistered.
        kept = [p for p in sections if p['retained_in_query']]
        hidden = [(p['start_codepoint'], p['subtree_end_codepoint'], p['heading'].casefold()) for p in kept
                  if p['heading'].casefold() in {'abstract', 'simple summary'}]
        body, spans, headings = '', [], []
        for p in kept:
            fragment = p['heading']+'\n'+p['body']+'\n\n'
            start = len(body)
            body += fragment
            headings.append({'text': p['heading'], 'level': p['level'], 'start': start})
            hidden_kind = next((kind for a, b, kind in hidden if a <= p['start_codepoint'] < b), None)
            if hidden_kind:
                spans.append({'start': start, 'end': len(body), 'kind': hidden_kind})
        # without_answers requires a pinned Motivation section. Add its real
        # withheld text at the end, with a real span, then remove it there.
        begin = len(body)
        body += 'Motivation\n'+source[ident][2]
        spans.append({'start': begin, 'end': len(body), 'kind': 'motivation'})
        title = re.search(r'(?mi)^title:\s*(.+)$', text)
        output.append({'id': ident, 'repository': item['repository'], 'author': docs[ident]['hashed_first_author'],
            'text': body, 'sections': spans, 'headings': headings, 'title': title.group(1) if title else '',
            'truth': ident, 'candidates': [{'id': cid, 'text': source[cid][2]} for cid in ids],
            'sourcePin': docs[ident]['source_sha256'], 'commit': docs[ident]['commit']})
    return output, {'exportPin': pin, 'documents': len(output), 'candidateDocuments': len(source),
                    'queryRule': 'received retained sections; Abstract/Simple Summary/description excluded; Motivation withheld'}


def lexical_order(statement, candidates, *, restrict=None):
    bags = [Counter(m.group().casefold() for m in WORD.finditer(c['text'])) for c in candidates]
    vocab = sorted(set().union(*bags))
    if not vocab:
        raise ValueError('Empty candidate vocabulary')
    idf = np.array([np.log((1+len(bags))/(1+sum(w in b for b in bags)))+1 for w in vocab])
    matrix = np.array([[b[w] for w in vocab] for b in bags])*idf
    query = Counter(m.group().casefold() for m in WORD.finditer(statement))
    vector = np.array([query[w] for w in vocab])*idf
    norm = np.linalg.norm(matrix, axis=1)*np.linalg.norm(vector)
    score = np.divide(matrix@vector, norm, out=np.zeros(len(bags)), where=norm > 0)
    indices = [i for i, c in enumerate(candidates) if restrict is None or c['id'] in restrict]
    return [candidates[i]['id'] for i in sorted(indices, key=lambda i: (-score[i], candidates[i]['id']))]


def ranks(order, truth):
    rank = order.index(truth)+1 if truth in order else None
    return {'top1': int(rank == 1), 'reciprocalRank': 1/rank if rank else 0., 'rank': rank}


def rerank(statement, body, candidates, truth):
    base = lexical_order(body, candidates)
    top = lexical_order(statement, candidates, restrict=set(base[:5]))
    return {'tfidf': ranks(base, truth), 'reader': ranks(lexical_order(statement, candidates), truth),
            'rerank': ranks(top+base[5:], truth), 'truthInTopFive': truth in base[:5]}
