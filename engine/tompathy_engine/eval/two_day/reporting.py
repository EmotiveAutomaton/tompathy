"""Land aggregate-only receipts and rebuild the extended engine scoreboard."""
import argparse
import math
import re
from datetime import UTC, datetime
from pathlib import Path

from ...ledger.ids import digest
from ..back_half.protocol import receipt
from ..back_half.reporting import FILES, save_json
from ..back_half.reporting import scoreboard as original_scoreboard
from .exports import read

EXTRA = {'ai-robustness': 'ai-robustness-pilot-2026-11.json',
         'choice': 'choice-pilot-2026-11.json', 'human-edits': 'edit-reasons-human-2026-11.json',
         'human-features': 'edit-reasons-human-features-2026-11.json',
         'weightonly': 'speed-weightonly-2026-11.json', 'first-paint': 'first-paint-2026-11.json'}
SCOPES = {'ai-robustness': 'RAID training pilot; fixed 5% calibration false-alarm threshold; no detector admission',
          'choice': 'Public accepted-answer choice; not values',
          'human-edits': 'IteraTeR balanced human intentions; fixed Q8; no fitting',
          'human-features': 'IteraTeR; EX2-only deterministic-feature control',
          'weightonly': 'W1 converted local base weights; five ordered gates',
          'first-paint': 'Three frozen texts; CPU; no default change'}
PRIVATE = {'id', 'writer', 'author', 'session', 'text', 'question', 'before', 'after', 'label', 'description',
           'reason', 'callKey', 'candidateIdsPin', 'countsByWriterGenre', 'rowIds', 'path', 'url'}
ENUM_KEYS = {'variant', 'status', 'bestRarityBaseline', 'signal', 'population', 'mode', 'stratum', 'name', 'model'}
ENUM_VALUES = {'V0', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'B3', 'B4', 'B5', 'A0', 'A1', 'FD',
               'complete', 'unavailable', 'insufficient-support', 'partial', 'raw', 'normalized',
               'human-heldout', 'machine', 'all', 'genre', 'generator', 'attack', 'none',
               'abstracts', 'books', 'news', 'poetry', 'recipes', 'reddit', 'reviews', 'wiki',
               'homoglyph', 'zero_width_space', 'paraphrase', 'qwen', 'smol'}
ENUM_VALUES.update({'human', 'chatgpt', 'cohere', 'gpt2', 'gpt3', 'llama-chat', 'mistral', 'mistral-chat', 'mpt', 'mpt-chat'})


def aggregates(value, key=''):
    """Numerical summaries only: never free error messages, prose or person IDs."""
    if value is None or type(value) is bool:
        return value
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError('Nonfinite public aggregate')
        return value
    if isinstance(value, str):
        if key in ENUM_KEYS and value in ENUM_VALUES:
            return value
        return None
    if isinstance(value, list):
        return [aggregates(v, key) for v in value]
    if isinstance(value, dict):
        return {k: aggregates(v, k) for k, v in value.items() if k not in PRIVATE and not re.fullmatch(r'[a-f0-9]{32,}', k)}
    raise ValueError('Unsupported aggregate type')


def public(capability, raw):
    result = receipt(capability) if capability in FILES else {
        'schema': 'tompathy.two-day-pilot.v1', 'capability': capability, 'scope': SCOPES[capability]}
    status = str(raw.get('status', 'pending'))
    result.update(status=('complete' if status.startswith('complete') else 'stopped' if status.startswith(('stopped', 'engineering', 'failed', 'cleanup-failed'))
                          else 'partial' if status.startswith('partial') else 'pending'),
                  date=datetime.now(UTC).date().isoformat(), sourceReceiptPin=digest(raw),
                  productionAdmission=False, ledgerRows=[], ledgerStatus='no ledger row')
    for name in ('enginePin', 'readerPin', 'codePin', 'dataPin', 'textPin', 'textsPin', 'ggufPin', 'samplePin', 'trainingPin', 'modelPin',
                 'aggregationCodePin', 'originalReceiptPin', 'readerLadderPin'):
        if name in raw:
            if not isinstance(raw[name], str) or not re.fullmatch('[a-f0-9]{64}', raw[name]):
                raise ValueError('Public source/reader pin must be a SHA-256 digest')
            result[name] = raw[name]
    if 'identity' in raw:
        result['runIdentityPin'] = digest(raw['identity'])
        for name in ('dataPin', 'codePin'):
            if re.fullmatch('[a-f0-9]{64}', raw['identity'].get(name, '')):
                result[name] = raw['identity'][name]
    sections = ('feature', 'direct', 'comparison', 'majority', 'scores', 'sourceSplits', 'sampleCoverage',
                'wordMatchingComparison', 'tfidfBaseline', 'thresholds', 'rates', 'nonNativeWriting', 'all', 'acceptedNotTopScore',
                'gates', 'measurements', 'completed', 'requested', 'completedDocuments', 'totalDocuments',
                'completedQuestions', 'stopsOutsideOwnSet', 'V1AllWords', 'sentences', 'writerGenreCells',
                'defaultChanged', 'productionEnabled', 'omittedParaphrase')
    for name in sections:
        if name in raw:
            result[name] = aggregates(raw[name])
    if 'measurements' in raw:
        for saved, source in zip(result['measurements'], raw['measurements'], strict=True):
            if isinstance(source.get('reader'), dict):
                saved.pop('reader', None)
                saved['readerPin'] = digest(source['reader'])
            name = source.get('text')
            if name in {'manuscript-3000', 'art-6000', 'distill-excerpt-600'}:
                saved['frozenText'] = name
    if 'pilotSummary' in raw:
        result['pilot'] = aggregates(raw['pilotSummary'])
    for name in ('rows', 'exploratory'):
        if name in raw:
            result[name] = [{**aggregates(r), **({'id': r['id']} if r.get('id') in ('1', '2', '3') else {})} for r in raw[name]]
    if capability in {'attention', 'ai-involvement'} and raw.get('evidence') == 'natural-writing':
        result['evidence'] = 'natural-writing'
    if capability == 'edit-reasons':
        result['speedQualification'] = 'unavailable: original supplied-feature generation timings absent'
    if capability == 'weightonly':
        result['productionEnabled'] = False
        result['servingReceipt'] = 'Use the exact private gate receipt; this aggregate summary cannot enable serving.'
    return result


def land(capability, source, directory):
    target = Path(directory)/(FILES | EXTRA)[capability]
    value = public(capability, read(source))
    if target.exists():
        previous = read(target)
        if {**previous, 'date': value['date']} == value:
            return value
        if previous.get('sourceReceiptPin'):
            archive = target.parent/'two-day-history'/f'{target.stem}-{previous["sourceReceiptPin"][:16]}.json'
            if archive.exists() and read(archive) != previous:
                archive = archive.with_name(f'{archive.stem}-{digest(previous)[:16]}.json')
            if not archive.exists():
                save_json(archive, previous)
    save_json(target, value)
    return value


def scoreboard(directory, output):
    original_scoreboard(directory, output)
    path, directory = Path(output), Path(directory)
    lines = ['', '## Two-day pilots', '',
             'These are separate pilot scopes. No row enables a detector, values reading or field label.', '',
             '| Row | Status | Result | Scope / receipt |', '|---|---|---|---|']
    for capability, filename in EXTRA.items():
        value = read(directory/filename) if (directory/filename).exists() else {'status': 'not run'}
        metric = 'pending; no score'
        if capability in {'human-edits', 'human-features'}:
            score = value.get('direct', value.get('scores', {}))
            if score:
                metric = f"macro-F1 {score['macroF1']:.4f}; abstentions {score['abstentions']}/{score['pairs']}"
        elif capability == 'choice' and value.get('all', {}).get('primary'):
            p = value['all']['primary']
            metric = f"E1 − best rarity {p['gain']:+.4f}; 95% [{p['interval'][0]:.4f}, {p['interval'][1]:.4f}]; bar +0.02"
        elif capability == 'ai-robustness' and value.get('rates'):
            metric = f"{value['completedDocuments']}/{value['totalDocuments']} documents; stratified rates and intervals in receipt"
        elif capability == 'weightonly' and value.get('gates'):
            metric = '; '.join(f"{k}: {'pass' if v.get('passed') else 'fail'}" for k, v in value['gates'].items())
        elif capability == 'first-paint' and value.get('measurements'):
            metric = f"{len(value['measurements'])} first-600/whole-text timing pairs"
        lines.append(f"| {capability} {'(pilot)' if capability in {'ai-robustness', 'choice'} else ''} | {value['status']} | {metric} | [{SCOPES[capability]}](../engine/validation/{filename}) |")
    lines += ['', 'Edit-reasons human-labelled lines are separate from the comment-labelled EX2 result.',
              'Goals also report candidate-only TF-IDF, reader-alone and top-five reranking in their receipt.',
              'Live progress and dependencies: [two-day working record](ENGINE_TWO_DAY_2026-11-14.md).', '']
    path.write_text(path.read_text(encoding='utf8')+'\n'.join(lines), encoding='utf8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capability', choices=tuple(FILES | EXTRA))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--directory', type=Path, default=Path('engine/validation'))
    parser.add_argument('--scoreboard', type=Path, default=Path('docs/ENGINE_SCOREBOARD.md'))
    args = parser.parse_args()
    if args.capability:
        if not args.source:
            parser.error('--source required')
        land(args.capability, args.source, args.directory)
    scoreboard(args.directory, args.scoreboard)


if __name__ == '__main__':
    main()
