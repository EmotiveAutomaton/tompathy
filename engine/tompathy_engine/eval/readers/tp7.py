"""Newly received EX5, original TP7 E1 controls. No generative goal reader."""
import json
from pathlib import Path

from ...packs.registry import sha256
from ...preview.readers import LocalReader
from ..back_half.reporting import save_json
from ..two_day.choice import choice_run


def run(source, reader_root, output, check):
    source, output = Path(source), Path(output)
    receipt = {'card': 'TP7', 'status': 'running', 'productionAdmission': False,
        'ledger': 'no ledger row', 'scope': 'Public accepted-answer choice; not values or endorsement',
        'sourcePin': sha256(source/'MANIFEST.json'), 'protocol': None,
        'rows': {}, 'acceptedNotTopScore': {},
        'sourceSelection': '400 questions per site, source-export verified non-self accepted choice; no owner IDs received',
        'E2': 'unrun; local generative reading is outside this week',
        'license': 'Source CC BY-SA 3.0 notice; public attribution URLs retained in private source file'}
    save_json(output/'receipt.json', receipt)
    try:
        reader = LocalReader(reader_root, output/'token-cache', threads=2, precision='float32')
        choice_run(source, output/'pilot', reader, check)
    finally:
        path = output/'pilot/receipt.json'
        if path.exists():
            result = json.loads(path.read_text(encoding='utf8'))
            receipt.update(status=result['status'], protocol=result['identity'], rows=result['all'],
                           acceptedNotTopScore=result['acceptedNotTopScore'])
            if result.get('reason'):
                receipt['reason'] = result['reason']
        save_json(output/'receipt.json', receipt)
