"""Build the two opening queues from the filed open corpora. All row data stay private."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))


def pin(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def ordered(ids, prefix):
    return sorted(ids, key=lambda ident: hashlib.sha256((prefix+ident).encode()).digest())


def panels(all_ids, held, prior):
    if len(set(all_ids)) != len(all_ids) or len(set(prior)) != 500 or not set(prior) <= set(held):
        raise ValueError('Previously rated reports must belong to the held-out fold')
    fresh = ordered(set(held)-set(prior), 'RD1:23:')
    if len(fresh) != 700:
        raise ValueError('RD1 requires two disjoint fresh 350-report panels')
    held_ids = set(held)
    return fresh[:350], fresh[350:], [key for key in all_ids if key not in held_ids]


def build(target):
    from tompathy_engine.eval.readers.affect_data import ed_situations
    from tompathy_engine.eval.readers.checkpoint import completed
    from tompathy_engine.eval.readers.envent import load

    data_dir = ROOT/'.local/readers/data'
    frozen = ROOT/'.local/nine-channel/tp30-frozen-a'
    receipts = completed(frozen, 'TP30-frozen')
    public = json.loads((ROOT/'engine/validation/readers-profile-frozen-2026-11.json').read_bytes())
    if pin(frozen/'receipt.json') != public['sourceReceiptPin']:
        raise ValueError('TP30 source receipt differs from its landed aggregate')
    old = ROOT/'.local/nine-channel/spark/sp1-input-v1'
    if pin(old/'payload.json') != '632745f3fd68ca4e605013c037e3ef099c0c6b70ff740db0b2d88eace1da7bbd':
        raise ValueError('SP1 source manifest changed')
    manifest = json.loads((old/'payload.json').read_bytes())
    if pin(old/'items.json') != manifest['files']['items.json']:
        raise ValueError('SP1 saved report order changed')
    original = json.loads((old/'items.json').read_bytes())
    corpus = load(data_dir/'crowd-enVent2023')
    if corpus.pins != receipts['sources']['envent']['files']:
        raise ValueError('Recalled-event source changed')
    frame = corpus.reports
    text_by_id = dict(zip(frame.text_id.astype(str), frame.hidden_emo_text))
    held = frame.iloc[corpus.test].text_id.astype(str).tolist()
    prior = [row['id'] for row in original]
    if prior != ordered(held, 'SP1:23:')[:500] or any(text_by_id[row['id']] != row['text'] for row in original):
        raise ValueError('Saved SP1 texts or selection differ')
    f1, f2, q2 = panels(list(text_by_id), held, prior)
    ed, ed_source = ed_situations(data_dir/'empathetic-dialogues')
    if ed_source != receipts['sources']['ed']:
        raise ValueError('Chat situation intake changed')
    words = ['ashamed', 'guilty', 'embarrassed', 'disgusted']
    selected = ed.label.isin(words)
    food_ids = ed.loc[selected, 'id'].tolist()+ordered(ed.loc[~selected, 'id'], 'TP38:23:')[:1000]
    food_text = dict(zip(ed.id, ed.text))
    limits = {'spark': {'Q1': (f1, text_by_id), 'Q2': (q2, text_by_id)},
              'workstation': {'G1': (food_ids, food_text)}}
    target.mkdir(parents=True, exist_ok=False)
    write(target/'reserved-ids.json', {'sp1': prior, 'F1': f1, 'F2': f2})
    packet = ROOT/'TOMPATHY_0.3_ENGINE_TEACHER_AND_WORD_TABLE_PACKET_2026-11-20.md'
    summary = {'packetPin': pin(packet), 'oldPayloadPin': pin(old/'payload.json'),
               'frozenReceiptPin': public['sourceReceiptPin'], 'reservedF2': len(f2),
               'g1WordCounts': ed.loc[selected, 'label'].value_counts().to_dict(), 'jobs': {}}
    for lane, jobs in limits.items():
        lane_dir = target/lane
        lane_dir.mkdir()
        for job, (ids, texts) in jobs.items():
            items = [{'id': ident, 'text': texts[ident]} for ident in ids]
            path = lane_dir/(job+'.json')
            write(path, items)
            summary['jobs'][job] = {'rows': len(items), 'filePin': pin(path)}
        write(lane_dir/'source.json', {**{k:v for k,v in summary.items() if k not in ('jobs','g1WordCounts')},
              'lane': lane, 'jobs': {j:summary['jobs'][j] for j in jobs}, 'publicInputsOnly': True,
              'inputPins': corpus.pins if lane == 'spark' else {'ed': ed_source['intakePin']},
              'license': 'public Crowd-enVENT' if lane == 'spark' else ed_source['license'],
              'environmentPins': manifest['environmentPins'] if lane == 'spark' else {},
              'packages': manifest['packages'] if lane == 'spark' else {}})
    write(target/'intake.json', summary)
    return summary


if __name__ == '__main__':
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '2'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if not args.directory.resolve().is_relative_to((ROOT/'.local/word-table').resolve()):
        parser.error('Use a fresh private word-table path')
    print(json.dumps(build(args.directory), indent=2))
