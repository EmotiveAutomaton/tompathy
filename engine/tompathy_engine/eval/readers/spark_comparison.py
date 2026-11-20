"""Source-bound SP1-v2 comparison of completed panels; no model execution."""
import json
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from .spark_panel import compare_first_passes


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def first_pass(role, paths, payload_pin, items):
    pilot, repeat = Path(paths['pilot']), Path(paths['repeat'])
    public, source, previous = [read_json(p) for p in
                                (paths['aggregate'], repeat/'receipt.json', pilot/'receipt.json')]
    audit, release = read_json(paths['exit']), read_json(repeat/'released.json')
    pin = sha256(repeat/'receipt.json')
    if (public['card'] != f'SP1-v2-reader-{role}-panel' or public['status'] != 'complete' or
            public['productionAdmission'] is not False or public['sourceReceiptPin'] != pin or
            source['status'] != 'complete' or source['protocol'].get('version') != 2 or
            audit.get('sameNativeAlive') is not False or not audit.get('gpuLockFree') or
            audit.get('receiptPin') != pin or audit.get('owner') != source['owner'] or
            release.get('owner') != source['owner'] or not release.get('lockReleased') or
            read_json(repeat/'complete.json')['receiptPin'] != pin or
            previous['status'] != 'complete' or previous['row']['kind'] != 'reader-pilot' or
            previous['row']['texts'] != 500 or source['row']['kind'] != 'reader-repeat' or
            source['row']['firstPassReused'] is not True or
            source['row']['pilotReceiptPin'] != sha256(pilot/'receipt.json') or
            previous['protocol'] != source['protocol'] or
            source['payloadPin'] != payload_pin or previous['payloadPin'] != payload_pin or
            public['protocol'] != source['protocol'] or public['payloadPin'] != payload_pin):
        raise ValueError('Completed v2 panels, exact exits and identical original input/protocol required')
    model = source['row']['model']['digest']
    if (previous['row']['model']['digest'] != model or public['row']['model']['digest'] != model or
            public['row']['panel'] != source['row']['panel'] or
            public['row']['readerQualified'] != source['row']['readerQualified']):
        raise ValueError('Standalone model or gate result changed')
    panel = public['row']['panel']
    qualified = all(panel[k] for k in ('correlationPass', 'repeatabilityPass', 'validityPass'))
    if qualified != public['row']['readerQualified']:
        raise ValueError('Standalone qualification contradicts saved gates')
    manifest = read_json(pilot/'artifacts.json')
    if (sha256(pilot/'artifacts.json') != previous['artifactsPin'] or
            source['row']['pilotArtifactManifestPin'] != previous['artifactsPin']):
        raise ValueError('Original pilot manifest changed')
    rows = []
    features = source['protocol']['features']
    for i, item in enumerate(items[:300]):
        name = f'row-{i:04d}.json'
        if sha256(pilot/name) != manifest['files'][name]:
            raise ValueError('Original first-pass artifact changed')
        row = read_json(pilot/name)
        if row['id'] != item['id'] or row['index'] != i or row['modelPin'] != model:
            raise ValueError('Original first-pass order/model changed')
        try:
            parsed = json.loads(row['response'].get('response', ''))
        except (ValueError, TypeError):
            parsed = None
        valid = (isinstance(parsed, dict) and set(parsed) == set(features) and
                 all(type(parsed[k]) is int and 1 <= parsed[k] <= 5 for k in features))
        values = [parsed[k] for k in features] if valid else None
        if row['values'] != values:
            raise ValueError('Raw/parsed first-pass rating mismatch')
        rows.append(values)
    return rows, qualified, source['protocol'], {
        'panelReceiptPin': pin, 'panelAggregatePin': sha256(paths['aggregate']),
        'pilotReceiptPin': sha256(pilot/'receipt.json'), 'modelDigest': model}


def land_comparison(readers, payload, destination):
    """Compare original first passes, retaining both original standalone gates."""
    payload, destination = Path(payload), Path(destination)
    if set(readers) != {'a', 'b'} or destination.name != 'readers-spark-v2-reader-comparison-2026-11.json':
        raise ValueError('Both reader roles and registered comparison filename required')
    manifest = read_json(payload/'payload.json')
    for name in ('items.json', 'reference.npz'):
        if sha256(payload/name) != manifest['files'][name]:
            raise ValueError('Fixed panel reference or ordered items changed')
    items = read_json(payload/'items.json')
    if len(items) != 500 or len({row['id'] for row in items}) != 500:
        raise ValueError('Original unique 500-report selection required')
    pin = sha256(payload/'payload.json')
    a, b = [first_pass(role, readers[role], pin, items) for role in ('a', 'b')]
    if a[2] != b[2] or a[3]['modelDigest'] == b[3]['modelDigest']:
        raise ValueError('Separate model IDs and identical protocols required')
    with np.load(payload/'reference.npz', allow_pickle=False) as reference:
        result = compare_first_passes(a[0], b[0], reference['feature_truth'][:300],
                                      reference['feature_baseline'][:300], {'a': a[1], 'b': b[1]})
    value = {'schema': 'SP1-comparison-1', 'card': 'SP1-v2-reader-comparison', 'status': 'complete',
             'productionAdmission': False, 'payloadPin': pin, 'protocol': a[2],
             'sources': {'a': a[3], 'b': b[3]}, 'row': result,
             'scope': 'Fixed common valid first-pass reports; standalone gates retained. Higher score alone does not qualify a teacher. No model IDs pooled or post-hoc winner substitution.'}
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError('Preserve previous comparison; use an explicit correction')
    destination.write_bytes(data)
    return value
