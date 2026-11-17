"""Explicit owner-ratified TP23 table scope, without rewriting prior results."""
import json
import math
from pathlib import Path

from ...packs.registry import sha256
from .need_transfer import PAIRS

METRICS = ('ratings', 'ratings+needs', 'gain_from_needs', 'needs', 'words')


def reproduction(job, receipt, decision=None):
    """Use the original check or a bound decision; never alter scientific bars."""
    if decision is None:
        if not receipt['preflight']['reproduced']:
            raise ValueError('Successful preflight reproduction or an explicit scope decision is required')
        return {'scope': 'original complete check', 'reproduced': True}
    decision = Path(decision)
    ruling = json.loads(decision.read_text(encoding='utf8'))
    source_pin = sha256(Path(job)/'receipt.json')
    if (ruling.get('schema') != 'tp23-preflight-scope-1'
            or ruling.get('scope') != 'packet-five-pair-table'
            or ruling.get('ownerDecision') != 'Use the packet\u2019s table scope'
            or ruling.get('sourceReceiptPin') != source_pin
            or receipt.get('card') != 'TP23-bow' or receipt.get('status') != 'complete'):
        raise ValueError('TP23 scope decision does not bind this completed BOW source')
    reference = Path(ruling['referenceFile'])
    reference_pin = sha256(reference)
    if reference_pin != ruling.get('referencePin') or reference_pin != receipt['preflight']['sourcePin']:
        raise ValueError('TP23 reference differs from the original preflight binding')
    expected = json.loads(reference.read_text(encoding='utf8'))
    differences = {}
    for pair in PAIRS:
        actual = receipt['transfer']['twins'][pair]
        for metric in METRICS:
            value = float(actual[metric])
            target = float(expected['twins'][pair][metric])
            if not math.isfinite(value) or not math.isfinite(target):
                raise ValueError('TP23 table contains a non-finite value')
            differences[pair+':'+metric] = abs(value-target)
    if any(value > .02 for value in differences.values()):
        raise ValueError('The required TP23 five-pair table does not reproduce within .02')
    return {'scope': ruling['scope'], 'decisionPin': sha256(decision),
            'sourceReceiptPin': source_pin, 'referencePin': reference_pin,
            'originalFullCheckReproduced': receipt['preflight']['reproduced'],
            'absoluteDifferences': differences, 'tolerance': .02, 'reproduced': True,
            'scientificGatesUnchanged': True}
