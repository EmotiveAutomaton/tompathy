import json
from copy import deepcopy

import pytest

from tompathy_engine.eval.readers import trigger_export
from tompathy_engine.eval.readers.preflight_scope import METRICS, PAIRS, reproduction
from tompathy_engine.packs.registry import sha256


def source(tmp_path):
    job = tmp_path/'bow'; job.mkdir()
    table = {pair: {metric: .4 if metric != 'gain_from_needs' else .01 for metric in METRICS} for pair in PAIRS}
    expected = tmp_path/'reference.json'
    expected.write_text(json.dumps({'twins': table}))
    receipt = {'card': 'TP23-bow', 'status': 'complete', 'qualifies': False,
               'story': {'development_auc': .7}, 'transfer': {'twins': deepcopy(table), 'transfer_passed': False},
               'preflight': {'reproduced': False, 'sourcePin': sha256(expected),
                             'absolute_differences': {'story:power': .035}}}
    (job/'receipt.json').write_text(json.dumps(receipt))
    decision = tmp_path/'decision.json'
    ruling = {'schema': 'tp23-preflight-scope-1', 'scope': 'packet-five-pair-table',
              'ownerDecision': 'Use the packet\u2019s table scope', 'sourceReceiptPin': sha256(job/'receipt.json'),
              'referenceFile': str(expected), 'referencePin': sha256(expected)}
    decision.write_text(json.dumps(ruling))
    return job, receipt, decision, ruling, expected


def test_table_scope_keeps_original_receipt_and_failed_packing_gate(tmp_path, monkeypatch):
    job, receipt, decision, _, _ = source(tmp_path)
    before = (job/'receipt.json').read_bytes()
    original = deepcopy(receipt)
    check = reproduction(job, receipt, decision)
    assert check['reproduced'] and not check['originalFullCheckReproduced']
    assert len(check['absoluteDifferences']) == 25
    assert receipt == original and (job/'receipt.json').read_bytes() == before
    monkeypatch.setattr(trigger_export, 'verified', lambda *a: (receipt, {}))
    selected, audit = trigger_export.select_need([job], lambda: None, decision)
    assert selected is None and audit['preflightScope']['reproduced']
    with pytest.raises(ValueError, match='both TP23 bars'):
        trigger_export.need_pack(job, tmp_path, tmp_path, tmp_path/'pack', lambda: None)
    assert not (tmp_path/'pack').exists()


@pytest.mark.parametrize('change', ['no_decision', 'source', 'reference', 'scope', 'missing_pair', 'gain_miss', 'nan'])
def test_table_scope_rejects_unbound_or_incomplete_evidence(tmp_path, change):
    job, receipt, decision, ruling, expected = source(tmp_path)
    if change == 'source':
        (job/'receipt.json').write_text('{}')
    elif change == 'reference':
        expected.write_text('{}')
    elif change == 'scope':
        ruling['scope'] = 'any-passing-column'
        decision.write_text(json.dumps(ruling))
    elif change in {'missing_pair', 'gain_miss', 'nan'}:
        if change == 'missing_pair':
            receipt['transfer']['twins'].pop(PAIRS[0])
        else:
            receipt['transfer']['twins'][PAIRS[0]]['gain_from_needs'] = .031 if change == 'gain_miss' else float('nan')
        (job/'receipt.json').write_text(json.dumps(receipt))
        ruling['sourceReceiptPin'] = sha256(job/'receipt.json')
        decision.write_text(json.dumps(ruling))
    with pytest.raises((ValueError, KeyError)):
        reproduction(job, receipt, None if change == 'no_decision' else decision)
