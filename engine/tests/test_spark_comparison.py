import json

import numpy as np
import pytest

from tompathy_engine.eval.readers.spark_comparison import land_comparison
from tompathy_engine.packs.registry import sha256


def save(path, value):
    path.write_text(json.dumps(value))


def fixture(root):
    payload = root/'input'; payload.mkdir()
    items = [{'id': f'private-id-{i}'} for i in range(500)]
    save(payload/'items.json', items)
    truth = np.array([[1+i%5]*8 for i in range(500)])
    np.savez(payload/'reference.npz', feature_truth=truth, feature_baseline=truth)
    save(payload/'payload.json', {'files': {n: sha256(payload/n) for n in ('items.json', 'reference.npz')}})
    payload_pin = sha256(payload/'payload.json')
    protocol = {'version': 2, 'features': [f'f{i}' for i in range(8)], 'promptPin': 'p'*64}
    readers = {}
    for role, values in [('a', truth), ('b', 6-truth)]:
        pilot, repeat = root/(role+'-pilot'), root/(role+'-repeat')
        pilot.mkdir(); repeat.mkdir()
        owner = {'pid': 3, 'startTicks': '12', 'privateHost': 'do not publish'}
        model = role*64
        files = {}
        for i in range(300):
            row = values[i].tolist()
            name = f'row-{i:04d}.json'
            save(pilot/name, {'id': items[i]['id'], 'index': i, 'modelPin': model, 'values': row,
                             'response': {'response': json.dumps(dict(zip(protocol['features'], row)))}})
            files[name] = sha256(pilot/name)
        save(pilot/'artifacts.json', {'files': files})
        save(pilot/'receipt.json', {'status': 'complete', 'protocol': protocol, 'payloadPin': payload_pin,
             'artifactsPin': sha256(pilot/'artifacts.json'),
             'row': {'kind': 'reader-pilot', 'texts': 500, 'model': {'digest': model}}})
        row = {'kind': 'reader-repeat', 'firstPassReused': True, 'model': {'digest': model},
               'pilotReceiptPin': sha256(pilot/'receipt.json'),
               'pilotArtifactManifestPin': sha256(pilot/'artifacts.json'), 'readerQualified': False,
               'panel': {'correlationPass': False, 'repeatabilityPass': True, 'validityPass': True}}
        save(repeat/'receipt.json', {'owner': owner, 'status': 'complete', 'protocol': protocol,
                                    'payloadPin': payload_pin, 'row': row})
        pin = sha256(repeat/'receipt.json')
        save(repeat/'complete.json', {'receiptPin': pin})
        save(repeat/'released.json', {'owner': owner, 'lockReleased': True})
        save(repeat/'exit.json', {'owner': owner, 'receiptPin': pin, 'sameNativeAlive': False, 'gpuLockFree': True})
        save(repeat/'aggregate.json', {'card': f'SP1-v2-reader-{role}-panel', 'status': 'complete',
             'productionAdmission': False, 'sourceReceiptPin': pin, 'payloadPin': payload_pin,
             'protocol': protocol, 'row': row})
        readers[role] = {'pilot': pilot, 'repeat': repeat, 'aggregate': repeat/'aggregate.json', 'exit': repeat/'exit.json'}
    return readers, payload, root/'readers-spark-v2-reader-comparison-2026-11.json'


def test_bound_comparison_retains_failed_winner_and_publishes_only_aggregates(tmp_path):
    readers, payload, output = fixture(tmp_path)
    value = land_comparison(readers, payload, output)
    assert value['row']['selectedRole'] == 'a' and not value['row']['selectedReaderQualified']
    assert value['row']['commonValid'] == 300 and not value['productionAdmission']
    assert 'private-id' not in output.read_text() and 'do not publish' not in output.read_text()
    assert value['sources']['b']['panelReceiptPin'] == sha256(readers['b']['repeat']/'receipt.json')


@pytest.mark.parametrize('tamper', ['raw', 'reference', 'exit', 'gate'])
def test_bound_comparison_refuses_changed_sources(tmp_path, tamper):
    readers, payload, output = fixture(tmp_path)
    if tamper == 'raw':
        (readers['b']['pilot']/'row-0000.json').write_text('{}')
    elif tamper == 'reference':
        (payload/'items.json').write_text('[]')
    else:
        path = readers['b']['exit' if tamper == 'exit' else 'aggregate']
        value = json.loads(path.read_text())
        if tamper == 'exit':
            value['sameNativeAlive'] = True
        else:
            value['row']['readerQualified'] = True
        save(path, value)
    with pytest.raises(ValueError):
        land_comparison(readers, payload, output)
    assert not output.exists()
