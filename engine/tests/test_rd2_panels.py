import hashlib
import json

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from tompathy_engine.eval.readers import word_panels
from tompathy_engine.eval.readers.rd2_panels import (
    comparison,
    panel_masks,
    research_reader,
    slot_comparison,
)
from tompathy_engine.eval.readers.reporting import land
from tompathy_engine.eval.readers.word_panel_sheets import sheet_data


def test_q5_root_records_match_only_the_verified_transfer(tmp_path, monkeypatch):
    def save(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding='utf8')
        return word_panels.sha256(path)

    entry = {'commit': 'registered'}
    owner = {'job': 'Q5', **entry}
    entry_hash = hashlib.sha256(b'{"commit":"registered"}').hexdigest()
    monkeypatch.setitem(word_panels.ENTRIES, 'Q5', entry_hash)
    receipt = {'entry': entry, 'owner': owner, 'job': 'Q5', 'lane': 'spark', 'status': 'complete',
               'artifactsPin': save('artifacts.json', {'files': {}})}
    receipt_pin = save('receipt.json', receipt)
    save('complete.json', {'receiptPin': receipt_pin})
    save('released.json', {'owner': owner, 'nativeExitCode': 0, 'descriptorClosed': True})
    name = 'development-selection.json'
    record_pin = save(name, {'winners': {'standards': 'V4', 'social_norms': 'V0'}})
    monkeypatch.setitem(word_panels.Q5_TRANSFER_RECORDS, name, record_pin)
    mirror = word_panels.Mirror(tmp_path, 'Q5')
    with pytest.raises(ValueError, match='artifact differs'):
        mirror.artifact(name)
    monkeypatch.setattr(word_panels, 'Q5_SOURCE', receipt_pin)
    assert mirror.artifact(name) == tmp_path / name
    save('unregistered.json', {})
    with pytest.raises(ValueError, match='artifact differs'):
        mirror.artifact('unregistered.json')
    save(name, {'winners': {}})
    with pytest.raises(ValueError, match='artifact differs'):
        mirror.artifact(name)


def test_paired_ties_and_missing_use_identical_common_rows():
    y = np.tile([2., 1., 3., 4., 4.], 6)
    candidate = y.copy()
    candidate[0] = np.nan
    baseline = np.roll(y, 2)
    baseline[1] = np.nan
    result = comparison(candidate, baseline, y, lambda: None, draws=100)
    assert result['commonValid'] == 28
    assert result['difference'] == pytest.approx(1-spearmanr(baseline[2:], y[2:]).statistic)
    assert result['finiteDraws'] == 100
    assert comparison(np.ones(5), y[:5], y[:5], lambda: None)['interval'] is None


def test_registered_and_fresh_nomination_still_require_independent_confirmation():
    ids = np.arange(350)
    target = ids % 5
    row = slot_comparison(ids, [14, 110], target, -target, target, lambda: None)
    assert [r['reports'] for r in row['panels'].values()] == [350, 348]
    assert all(r['namedOnF2'] and not r['wouldTakeSlot'] for r in row['panels'].values())
    row = slot_comparison(ids, [14, 110], target, -target, target, lambda: None,
                          f3=(target[:200], target[:200], target[:200]))
    assert all(r['wouldTakeSlot'] for r in row['panels'].values())
    assert not row['nominationChanges'] and not row['slotConclusionChanges']
    with pytest.raises(ValueError):
        panel_masks(ids, [0, 350])


def test_difference_in_six_feature_reader_recommendation_is_flagged():
    ids = np.arange(350)
    truth = np.tile((ids % 5)[:, None], (1, 8))
    c = truth.copy()
    c[[0, 1], :6] = 4
    result = research_reader(ids, [0, 1], c, truth, truth)
    assert result['panels']['registered350']['atOrAboveB'] == 2
    assert result['panels']['textFresh348']['atOrAboveB'] == 8
    assert result['featureComparisonsChanged'] == list(range(6))
    assert result['conclusionChanges']


def test_reserved_panel_receipt_keeps_both_estimates_and_flags_nomination_change(tmp_path, monkeypatch):
    """Exercise the normal analysis and aggregate export with synthetic inputs only."""
    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True), encoding='utf8')
        return word_panels.sha256(path)

    originals = [f'report-{i}' for i in range(350)]
    opaque = {k: f'opaque-{i}' for i, k in enumerate(originals)}
    root = tmp_path / 'inputs'
    mirror = tmp_path / 'mirror'
    protocol = tmp_path / 'protocol.json'
    save(protocol, {'fixture': True})
    pins = {
        'SELECTION': ('intake-a/reserved-ids.json', {'F2': originals}),
        'CROSSWALK': ('F2-release-local/local-original-id-map.json', opaque),
        'OVERLAPS': ('F2-release-local/local-overlap-audit.json',
                     {'affectedOpaqueIds': list(opaque.values())[:2]}),
        'PRIOR_USE': ('F3-prior-use.json', {'eligibleForSlotConfirmation': False,
                                            'priorSourceReceiptPin': word_panels.MODEL}),
    }
    for name, (path, value) in pins.items():
        monkeypatch.setattr(word_panels, name, save(root / path, value))
    entry = {'sourcePin': 'fixture-source', 'commit': 'fixture-commit', 'codePins': {'worker': 'fixture-code'}}
    identity = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    monkeypatch.setitem(word_panels.ENTRIES, 'Q5', identity)
    owner = {'job': 'Q5', 'commit': entry['commit']}
    files = {}
    selection = {'winners': {'standards': 'V1', 'social_norms': 'V0'}}
    files['development-selection.json'] = save(mirror / 'development-selection.json', selection)
    status = {'readerCGeneralPass': False, 'developmentSelection': selection}
    files['arm-status.json'] = save(mirror / 'arm-status.json', status)
    features = word_panels.FEATURES
    target = np.arange(350) % 5 + 1
    truth = np.tile(target[:, None], (1, len(features)))
    baseline = truth.copy()
    baseline[:5, features.index('standards')] = target[:5] % 5 + 1
    human = pd.DataFrame(np.repeat(truth, 5, axis=0), columns=features)
    human['index'] = np.repeat(np.arange(350), 5)
    human['prolific_id'] = np.tile(np.arange(5), 350)

    for arm in ('F2-V0', 'F2-V1', 'F2-standard'):
        prefix = arm + '/B/'
        binding = {**entry, 'arm': arm, 'job': 'Q5', 'role': 'B', 'modelPin': word_panels.READER_IDS['B']}
        name = prefix + 'complete.json'
        files[name] = save(mirror / name, {'rows': 350, 'valid': 350, 'binding': binding})
        for i, ident in enumerate(opaque.values()):
            standard = int(target[i])
            values = ([standard] * len(features) if arm == 'F2-standard' else
                      {'standards': standard if arm == 'F2-V1' else 1,
                       'social_norms': standard if arm == 'F2-V0' else 1})
            name = prefix + f'row-{i:06d}.json'
            files[name] = save(mirror / name, {'id': ident, 'index': i, 'values': values, 'binding': binding})

    def seal():
        receipt = {'entry': entry, 'job': 'Q5', 'lane': 'spark', 'status': 'complete', 'owner': owner,
                   'artifactsPin': save(mirror / 'artifacts.json', {'files': files})}
        save(mirror / 'complete.json', {'receiptPin': save(mirror / 'receipt.json', receipt)})
        save(mirror / 'released.json', {'owner': owner, 'nativeExitCode': 0, 'descriptorClosed': True})

    seal()
    output = tmp_path / 'analysis'
    output.mkdir()
    def references(corpus, job, original_ids):
        assert original_ids == originals
        return baseline, truth, human

    monkeypatch.setattr(word_panels, 'references', references)
    def run():
        word_panels.run('RD2', None, root, mirror, None, output, lambda: None, 'test-row', protocol)

    run()
    save(output / 'plan.json', {'snapshotFiles': {}, 'launcherSha256': 'fixture'})
    save(output / 'complete.json', {'completed': ['RD2']})
    save(output / 'exit-verification.json', dict.fromkeys(
        ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent'), True))
    exported = tmp_path / 'readers-standards-panel-2026-11.json'
    land(output, exported)
    result = word_panels.read(exported)
    row = result['rows']['developmentWinnerB']['standards']
    primary, fresh = (row['panels'][k] for k in ('registered350','textFresh348'))
    assert (primary['commonValid'], fresh['commonValid']) == (350, 348)
    assert primary['namedOnF2'] and not fresh['namedOnF2']
    assert not primary['wouldTakeSlot'] and not fresh['wouldTakeSlot']
    assert result['differenceFlags'] == [{'candidate': 'developmentWinnerB', 'feature': 'standards',
                                          'nominationChanges': True, 'slotConclusionChanges': False}]
    assert result['status'] == 'partial' and result['researchReaderC'] is None
    assert result['human']['textFresh348']['standards']['estimableRereaders'] == 5
    assert result['developmentSelectionPin'] == files['development-selection.json']
    lines, numeric, dots = sheet_data(result)
    assert any('Own standards' in line and 'yes / no' in line and 'F2 nomination' in line for line in lines)
    assert [row[4] for row in numeric if row[1]=='standards'] == [350, 348]
    assert {row[1] for row in dots} == {'Registered 350','Text-fresh 348'}

    # A different selection in the arm receipt must be rejected before opening local writer ratings.
    status['developmentSelection'] = {'winners': {'standards': 'V5', 'social_norms': 'V0'}}
    files['arm-status.json'] = save(mirror / 'arm-status.json', status)
    seal()
    monkeypatch.setattr(word_panels, 'references', lambda *a: pytest.fail('Opened F2 before verified selection'))
    with pytest.raises(ValueError, match='frozen development winners'):
        run()
