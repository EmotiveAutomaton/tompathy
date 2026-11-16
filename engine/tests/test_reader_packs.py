"""Constructed software controls; no corpus or reader efficacy claims."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tompathy_engine.packet.bottom_box import BottomBox, empty_bottom_box
from tompathy_engine.packet.contract import Packet
from tompathy_engine.packet.names import NAMES
from tompathy_engine.packs.aggregate import AggregationPolicy, correct, shares
from tompathy_engine.packs.registry import code_pin, load_pack, sha256
from tompathy_engine.packs.run import Sentence, run

ROOT = Path(__file__).resolve().parents[2]


def test_correction_fixture_and_minimum_not_raw_count():
    table = np.array([[.8, .1, .1], [.2, .7, .1], [.3, .2, .5]])
    raw = table.T @ [.6, .3, .1]
    np.testing.assert_allclose(raw, [.57, .29, .14])
    np.testing.assert_allclose(correct(raw, table), [.6, .3, .1])
    assert shares([0]*19, table, AggregationPolicy(1, 20, 100)) is None
    result = shares([0]*57+[1]*29+[2]*14, table, AggregationPolicy(1, 20, 100))
    assert result[0]['value'] == pytest.approx(.6)
    assert result[0]['interval'][0] <= .6 <= result[0]['interval'][1]
    assert shares([2]*30, table, AggregationPolicy(1, 20, 100), neutral=2) is None
    with pytest.raises(ValueError):
        correct([1, 2, 3], table.T)


def fixture_pack(root, research=True):
    root.mkdir()
    (root/'encoder').mkdir()
    (root/'encoder/fixture.json').write_text('{}')
    (root/'LICENSE.txt').write_text('Constructed software fixture only')
    np.savez(root/'head.npz', weights=np.array([[3., 0], [0., 3], [-3., -3]]), bias=np.zeros(3))
    (root/'table.json').write_text(json.dumps({'labels': ['fear', 'joy', 'no-emotion'],
        'orientation': 'key-by-reader', 'counts': [[8,1,1],[2,7,1],[3,2,5]],
        'held_out': True, 'smoothing': .5, 'abstention_threshold': .5}))
    (root/'selection.json').write_text(json.dumps({'card': 'TP12', 'status': 'complete',
                                                   'prior': 1, 'minimum': 20}))
    def pin(name):
        return {'file': name, 'sha256': sha256(root/name)}
    files = {'encoder/fixture.json': sha256(root/'encoder/fixture.json')}
    license = {'name': 'constructed', 'source': 'fixture', 'license': 'constructed',
        'file': 'LICENSE.txt', 'license_sha256': sha256(root/'LICENSE.txt'), 'commercial_use': True}
    m = {'name': 'fixture', 'version': 'reader-pack-1', 'task': 'channel',
        'labels': ['fear', 'joy', 'no-emotion'], 'neutral': 'no-emotion',
        'encoder': {'id': 'constructed', 'revision': 'fixture', 'kind': 'constructed',
            'files': files, 'sha256': hashlib.sha256(json.dumps(files, sort_keys=True,
                separators=(',', ':')).encode()).hexdigest(), 'license': license},
        'head': pin('head.npz'), 'table': pin('table.json'), 'token_cap': 128,
        'abstention_threshold': .5, 'unread_share': .1,
        'key': {'corpus': 'constructed', 'labelled_by': 'test author', 'n': 30},
        'score': {'metric': 'accuracy', 'value': .5, 'interval': [.3, .7]},
        'people': {}, 'floor': {}, 'nothing_here': {}, 'training': [license],
        'research_only': research, 'code_pin': code_pin(),
        'aggregation': {'prior': 1, 'minimum': 20, 'bootstrap': 100, 'seed': 3,
                        'selection': pin('selection.json')},
        'label_map': {'fear': 'C3'}, 'mapping': {'status': 'proposed', 'source': 'fixture'},
        'status': 'benchmarked'}
    (root/'pack.json').write_text(json.dumps(m))
    return m


def test_pin_checks_release_and_runtime_default_off(tmp_path):
    root = tmp_path/'pack'
    fixture_pack(root)
    assert load_pack(root).manifest.name == 'fixture'
    assert run(root, [Sentence('Fear.', 0, 5)]) == empty_bottom_box()
    assert run(tmp_path/'absent', [], enabled=True) == empty_bottom_box()
    with pytest.raises(ValueError, match='release'):
        load_pack(root, release=True)
    output = run(root, [Sentence('Fear.', 0, 5)], enabled=True, encoder=lambda t: [[1., 0.]])
    assert output['on_page'][0]['share'] is None
    assert output['on_page'][0]['events'][0]['who'] == 'unclear'
    assert output['about_maker'] == []
    (root/'head.npz').write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash mismatch'):
        load_pack(root)


def test_unpinned_encoder_and_path_escape_refused(tmp_path):
    root = tmp_path/'pack'
    m = fixture_pack(root)
    (root/'encoder/evil.py').write_text('raise AssertionError')
    with pytest.raises(ValueError, match='Unpinned'):
        load_pack(root)
    m['encoder']['files'] = {'../escape': '0'*64}
    (root/'pack.json').write_text(json.dumps(m))
    with pytest.raises(ValueError, match='under encoder'):
        load_pack(root)


def test_legacy_upgrade_keeps_maker_empty_and_names_match():
    raw = json.loads((ROOT/'engine/tests/fixtures/packets/bottom-box-empty.json').read_text(encoding='utf8'))
    upgraded = Packet.model_validate(raw).wire()
    assert upgraded['schemaVersion'] == '1.11'
    assert upgraded['bottom_box'] == empty_bottom_box()
    raw['bottom_box']['readings']['stress']['value'] = .4
    with pytest.raises(ValueError):
        Packet.model_validate(raw)
    assert json.loads((ROOT/'src/core/reader-names.json').read_text()) == NAMES
    with pytest.raises(ValueError):
        BottomBox.model_validate({**empty_bottom_box(), 'about_maker': [{'tier': 'on_page'}]})


def test_current_fixtures_still_validate():
    for path in (ROOT/'engine/tests/fixtures/packets').glob('*.json'):
        Packet.model_validate_json(path.read_text(encoding='utf8'))
