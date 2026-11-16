"""Before-revision controls, joined to published document domains without guessing."""
import json
from collections import Counter
from pathlib import Path

from ...packs.registry import sha256
from ..back_half.reporting import save_json


def prepare(sentences, documents, selected, output):
    domains, sources = {}, {}
    for directory in (Path(sentences), Path(documents)):
        manifest = json.loads((directory/'manifest.json').read_text(encoding='utf8'))
        for name, pin in manifest['files'].items():
            path = (directory/name).resolve()
            if not path.is_relative_to(directory.resolve()) or sha256(path) != pin:
                raise ValueError('IteraTeR source pin mismatch')
        sources[directory.name] = manifest
    for split in ('train', 'dev', 'test'):
        for line in (Path(documents)/(split+'.json')).read_text(encoding='utf8').splitlines():
            row = json.loads(line)
            key = str(row['doc_id'])
            if not row.get('domain'):
                continue
            if key in domains and domains[key] != row['domain']:
                raise ValueError('Conflicting document domains')
            domains[key] = row['domain']
    source_rows = {split: [json.loads(line) for line in
        (Path(sentences)/(split+'.json')).read_text(encoding='utf8').splitlines()]
        for split in ('train', 'dev', 'test')}
    result, exclusions = [], Counter()
    for item in json.loads(Path(selected).read_text(encoding='utf8')):
        original = source_rows[item['split']][item['sourceRow']]
        if original['before_sent'] != item['replaced'] or str(original['doc_id']) != str(item['document']):
            raise ValueError('Prepared TP9 item differs from original source row')
        domain = domains.get(str(item['document']))
        domain = 'wikipedia' if domain == 'wiki' else domain
        if domain not in {'arxiv', 'wikipedia'}:
            exclusions[domain or 'unknown domain'] += 1
            continue
        result.append({'id': item['id'], 'source': domain, 'before': original['before_sent'],
                       'document': str(item['document']), 'split': item['split'], 'sourceRow': item['sourceRow']})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    save_json(output/'readers-neutral-before.json', result[:2000])
    save_json(output/'neutral-intake.json', {'sources': sources, 'selectedPin': sha256(selected),
        'outputPin': sha256(output/'readers-neutral-before.json'), 'n': len(result[:2000]),
        'domains': dict(Counter(x['source'] for x in result[:2000])), 'excluded': dict(exclusions),
        'coverageComplete': not exclusions.get('unknown domain'),
        'scope': 'All eligible before sentences from the original TP9 sample, capped at 2000; no replacement sentences'})
