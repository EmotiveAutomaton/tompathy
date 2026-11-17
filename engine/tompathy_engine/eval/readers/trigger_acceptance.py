"""TS3 real private packets on the fixed B13 battery and three public essays."""
import hashlib
import json
from pathlib import Path

from ...adapters.capture import make_capture
from ...adapters.replay import replay
from ...packet.build import build_packet
from ...packs.registry import sha256
from ...packs.v2 import load_pack
from ..back_half.reporting import save_json
from .artifacts import seal


def inputs(config, check):
    battery = Path('engine/validation/q10-empty-v2.items.json')
    items = json.loads(battery.read_text(encoding='utf8'))
    if len(items) != 200 or sum(not r['expected'] for r in items) != 40:
        raise ValueError('TS3 requires the unchanged 160 themed / 40 theme-free battery')
    rows = [{'name': f'b13-{i:03d}', 'text': r['text'], 'kind': 'theme-free' if not r['expected'] else 'themed'} for i, r in enumerate(items)]
    config = json.loads(Path(config).read_text(encoding='utf8'))
    roster_path, root = Path(config['rawRoster']), Path(config['rawRoot']).resolve()
    expected = json.loads(Path('.local/bench/two-day-ex1-intake/intake.json').read_text(encoding='utf8'))['rawRosterPin']
    if sha256(roster_path) != expected:
        raise ValueError('Public CoAuthor roster differs from TP19')
    roster = json.loads(roster_path.read_text(encoding='utf8'))
    selected = sorted((r for r in roster if r['reconstructed']), key=lambda r: hashlib.sha256(r['session'].encode()).hexdigest())[:3]
    sources = []
    for i, row in enumerate(selected):
        check()
        path = (root/row['path']).resolve()
        if not path.is_relative_to(root/'corpora/coauthor') or sha256(path) != row['source_sha256']:
            raise ValueError('Selected public essay source differs')
        events = [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]
        result = replay(events)
        if not result['reconstructed'] or not result['final_document'].strip():
            raise ValueError('Selected essay cannot be reconstructed; do not cherry-pick a replacement')
        rows.append({'name': f'essay-{i+1}', 'text': result['final_document'], 'kind': 'public-coauthor'})
        sources.append(row['source_sha256'])
    return rows, {'batteryPin': sha256(battery), 'rosterPin': expected, 'essaySourcePins': sources,
                  'selection': 'lowest SHA256 session identities among reconstructed original roster, fixed before reading scores'}


def run(directories, config, output, check, *, cache=None):
    output = Path(output)
    packs = [load_pack(p) for p in directories]
    if not packs or any(p is None for p in packs):
        raise ValueError('Acceptance needs actual verified packs')
    rows, sources = inputs(config, check)
    receipt = {'card': 'TS3-real', 'status': 'running', 'productionAdmission': False, 'ledger': 'no ledger row',
        'scope': 'Engineering acceptance on public text, no new accuracy key or maker claim', 'sources': sources,
        'packs': [p.pin for p in packs], 'rows': [], 'defaultOffParity': True,
        'browser': 'separate native Chrome verification required after terminal exit'}
    save = lambda: save_json(output/'receipt.json', receipt)
    save()
    for row in rows:
        check()
        capture = make_capture([row['text']], 'https://example.org/ts3/'+row['name'],
                               'Research acceptance '+row['name'], '2026-11-16T00:00:00Z')
        baseline = build_packet(capture, bottom_box=True)
        off = build_packet(capture, bottom_box=True, packs=directories, research=False)
        if baseline != off:
            raise ValueError('Research-off packet differs from no-pack baseline')
        diagnostic = {}
        packet = build_packet(capture, bottom_box=True, packs=directories, research=True,
            reader_check=check, reader_diagnostics=diagnostic, reader_cache=cache or output/'vector-cache')
        if packet['bottom_box']['about_maker']:
            raise ValueError('Acceptance wrote maker estimates')
        save_json(output/'packets'/(row['name']+'.json'), packet)
        if row['kind'] == 'public-coauthor':
            save_json(output/'default-packets'/(row['name']+'.json'), baseline)
        receipt['rows'].append({'name': row['name'], 'kind': row['kind'], 'readings': len(packet['bottom_box']['on_page']),
                               'events': sum(len(r['events']) for r in packet['bottom_box']['on_page']), 'timing': diagnostic})
        save()
    receipt.update(status='complete', artifactsPin=seal(output, [output/'packets', output/'default-packets'], check))
    save()
