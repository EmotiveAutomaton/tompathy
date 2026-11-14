"""Explicit bounded intake of the two public datasets commissioned in the packet."""
import argparse
import csv
import hashlib
import io
import json
import time
import urllib.request
from collections import Counter
from pathlib import Path

from ...ledger.ids import digest
from ..back_half.reporting import save_json
from .exports import read, sha
from .robustness import Quotas

RAID_REVISION = '865cac74188466cb0c3b7574a10204007b57a459'
INTENTIONS = ('clarity', 'fluency', 'coherence', 'style', 'meaning-changed')


class CountedStream(io.RawIOBase):
    def __init__(self, response, limit):
        self.response, self.limit, self.bytes = response, limit, 0
        self.hash = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.response.read(len(buffer))
        self.bytes += len(data)
        if self.bytes > self.limit:
            raise RuntimeError('RAID download byte ceiling reached')
        self.hash.update(data)
        buffer[:len(data)] = data
        return len(data)


def raid(directory, *, byte_limit=16_000_000_000):
    """Streaming only; no full-file fallback is attempted. Keep only quota rows."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory/'manifest.json').exists():
        raise ValueError('Preserve previous intake; use a fresh directory')
    url = f'https://huggingface.co/datasets/liamdugan/raid/resolve/{RAID_REVISION}/train.csv'
    quotas, selected, scanned, started = Quotas(), [], 0, time.monotonic()
    manifest = {'source': url, 'revision': RAID_REVISION, 'license': 'MIT', 'split': 'train',
                'selection': 'file order, frozen quotas, max 12/generator/genre', 'fallback': 'disabled; no full-file download',
                'byteCeiling': byte_limit, 'status': 'running'}
    counted = None
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'ToMpathy-public-benchmark'})
        with urllib.request.urlopen(request, timeout=90) as response:
            counted = CountedStream(response, byte_limit)
            text = io.TextIOWrapper(io.BufferedReader(counted), encoding='utf-8', newline='')
            csv.field_size_limit(5_000_000)
            for row in csv.DictReader(text):
                scanned += 1
                if time.monotonic()-started > 2*3600:
                    raise RuntimeError('Two-hour intake ceiling reached')
                if quotas.accept(row):
                    selected.append({**{k: row[k] for k in ('id', 'model', 'domain', 'attack', 'generation', 'source_id', 'adv_source_id')},
                                     'rowIndex': scanned-1, 'sha256': hashlib.sha256(row['generation'].encode()).hexdigest()})
                if scanned % 10000 == 0 or quotas.complete():
                    save_json(directory/'progress.json', {'rowsScanned': scanned, 'bytesRead': counted.bytes,
                              'selected': len(selected), 'quotas': {':'.join(k): v for k, v in quotas.counts.items()}})
                if quotas.complete():
                    break
        manifest['status'] = 'complete' if quotas.complete() else 'incomplete-quotas'
    except (OSError, ValueError, RuntimeError, csv.Error, KeyError) as exc:
        manifest.update(status='stopped', reason=f'{type(exc).__name__}: {exc}')
    finally:
        save_json(directory/'rows.json', selected)
        manifest.update(rowsScanned=scanned, selected=len(selected), rowsPin=sha(directory/'rows.json'),
                        rowIds=[r['id'] for r in selected], quotas={':'.join(k): v for k, v in quotas.counts.items()},
                        bytesRead=counted.bytes if counted else 0,
                        streamedPrefixHash=counted.hash.hexdigest() if counted else None)
        save_json(directory/'manifest.json', manifest)
    return {k: v for k, v in manifest.items() if k != 'rowIds'}


def iterater(directory, output):
    directory = Path(directory)
    manifest = read(directory/'manifest.json')
    for name, expected in manifest['files'].items():
        if not (directory/name).resolve().is_relative_to(directory.resolve()) or sha(directory/name) != expected:
            raise ValueError('Human dataset pin differs')
    if manifest['license'] != 'Apache-2.0':
        raise ValueError('Human dataset license must be explicit')
    rows, duplicates, excluded = [], set(), Counter()
    for split in ('train', 'dev', 'test'):
        for index, line in enumerate((directory/f'{split}.json').read_text(encoding='utf8').splitlines()):
            row = json.loads(line)
            intention = row['labels']
            if intention not in INTENTIONS:
                excluded[intention] += 1
                continue
            identity = digest([row['before_sent'], row['after_sent']])
            if identity in duplicates:
                excluded['duplicate pair'] += 1
                continue
            duplicates.add(identity)
            rows.append({'id': digest([manifest['revision'], split, index]), 'split': split,
                         'sourceRow': index, 'document': row['doc_id'], 'intention': intention,
                         'replaced': row['before_sent'], 'replacement': row['after_sent']})
    selected, coverage = [], {}
    for intention in INTENTIONS:
        group = sorted((r for r in rows if r['intention'] == intention), key=lambda r: digest(['TP9', r['id']]))
        selected.extend(group[:60])
        coverage[intention] = {'available': len(group), 'sampled': min(60, len(group))}
    selected.sort(key=lambda r: digest(['TP9-call-order', r['id']]))
    majority = Counter(r['intention'] for r in rows if r['split'] == 'train').most_common(1)[0][0]
    report = {'dataPin': digest(manifest), 'samplePin': digest(selected), 'coverage': coverage,
              'sourceSplits': dict(Counter(r['split'] for r in selected)), 'excluded': dict(excluded),
              'majorityLabelFromTrain': majority,
              'classifier': 'blocked: EX2 feature data missing; no IteraTeR-trained feature model may be evaluated on its training rows',
              'q8Scope': 'frozen generic reader, no task fitting; balanced sample from all human splits as commissioned'}
    save_json(Path(output)/'human-edits.json', selected)
    save_json(Path(output)/'human-edits-intake.json', report)
    return report


def non_native(directory):
    """The published, licensed 91 human TOEFL essays, never polished variants."""
    directory = Path(directory)
    manifest = read(directory/'manifest.json')
    if manifest['license'] != 'MIT' or manifest['revision'] != 'ca6b48c8ce435b4750efc895d3c40bfab8bd7d9a':
        raise ValueError('Auxiliary essay source/license differs')
    for name, expected in manifest['files'].items():
        if not (directory/name).resolve().is_relative_to(directory.resolve()) or sha(directory/name) != expected:
            raise ValueError('Auxiliary essay source pin differs')
    rows = [{'id': digest([manifest['revision'], i]), 'text': r['text']} for i, r in enumerate(read(directory/'all_data.json'))
            if (r['domain'], r['kind'], r['model']) == ('TOEFL_real_91', 'Human-Written', 'Human')]
    if len(rows) != 91 or any(not r['text'].strip() for r in rows):
        raise ValueError('Auxiliary essay cohort differs')
    return rows, digest([manifest, rows])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('raid', 'iterater'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'iterater' and args.output is None:
        parser.error('--output required for IteraTeR')
    print(json.dumps(raid(args.directory) if args.command == 'raid' else iterater(args.directory, args.output)))


if __name__ == '__main__':
    main()
