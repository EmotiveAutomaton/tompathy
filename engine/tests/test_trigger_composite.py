import json
import shutil

import numpy as np
import pytest
from test_trigger_wire import make_pack

from tompathy_engine.packs.registry import sha256
from tompathy_engine.packs.runtime import run, sentence_rows
from tompathy_engine.packs.trigger import (
    AHEAD,
    ALREADY,
    FEATURES,
    TAG_MAP,
    TAGS,
    table_scores,
    tense,
)
from tompathy_engine.packs.v2 import code_pin


def test_separate_components_exact_gate_and_hidden_unqualified_slots(tmp_path):
    gate = make_pack(tmp_path/'gate', 'gate', 'gate', [[0, 0]], [10], thresholds={'signal': .5})
    make_pack(tmp_path/'label', 'label', 'channel', [[0, 0], [0, 0]], [5, 0],
                      labels=['fear', 'neutral'], neutral='neutral', label_map={'fear': 'C3'})
    need = make_pack(tmp_path/'need-source', 'need-source', 'tags', np.zeros((19, 3)), np.arange(19),
                     labels=list(TAGS), thresholds=dict.fromkeys(TAGS, .5), tag_map=TAG_MAP)
    # Distinct actual encoder pin, distinct dimension, same word stream.
    (tmp_path/'need-source/encoder/fixture.json').write_text('{"different":true}')
    need['encoder']['files']['encoder/fixture.json'] = sha256(tmp_path/'need-source/encoder/fixture.json')
    import hashlib
    need['encoder']['sha256'] = hashlib.sha256(json.dumps(need['encoder']['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (tmp_path/'need-source/pack.json').write_text(json.dumps(need))
    feature = make_pack(tmp_path/'feature-source', 'feature-source', 'tags', np.zeros((8, 2)), [1, 2, 0, 0, 0, 1, 0, 1],
                        labels=list(FEATURES), thresholds=dict.fromkeys(FEATURES, .5))
    root = tmp_path/'trigger'
    manifest = make_pack(root, 'trigger', 'trigger', [[0, 0]], [0])
    for name, spec, src in [('need', need, 'need-source'), ('features', feature, 'feature-source')]:
        shutil.copytree(tmp_path/src, root/name)
        manifest['need_head' if name == 'need' else 'feature_head'] = {
            'directory': name, 'encoder': spec['encoder'], 'head': spec['head'],
            'labels': spec['labels'], 'token_cap': spec['token_cap']}
    manifest.update(gate_pin='gate@'+sha256(tmp_path/'gate/pack.json'), label_pin='label@'+sha256(tmp_path/'label/pack.json'))
    rules = {'version': 'trigger-table-1', 'tag_map': TAG_MAP, 'tense': {'ahead': AHEAD, 'already': ALREADY},
             'mean': [0]*29, 'scale': [1]*29, 'stakes_qualified': True, 'table_qualified': True, 'tense_qualified': True}
    (root/'rules.json').write_text(json.dumps(rules))
    manifest['trigger_rules'] = {'file': 'rules.json', 'sha256': sha256(root/'rules.json')}
    manifest['code_pin'] = code_pin()
    (root/'pack.json').write_text(json.dumps(manifest))
    calls = [0, 0]
    def common(texts):
        calls[0] += len(texts)
        return np.ones((len(texts), 2))
    def separate(texts):
        calls[1] += len(texts)
        return np.ones((len(texts), 3))
    adapters = {gate['encoder']['sha256']: (common, len), need['encoder']['sha256']: (separate, len)}
    rows = sentence_rows('I might lose it.')
    result = run([tmp_path/'gate', tmp_path/'label', root], rows, enabled=True, research=True, adapters=adapters)
    event = result['on_page'][-1]['events'][0]
    assert result['on_page'][-1]['id'] == 'C3'
    assert event['stake']['need'] == 'N3' and event['stake']['when'] == 'ahead'
    assert event['channel_by_table']['version'] == 'trigger-table-1'
    assert calls == [1, 1]
    rules.update(stakes_qualified=False, table_qualified=False, tense_qualified=False)
    (root/'rules.json').write_text(json.dumps(rules))
    manifest['trigger_rules']['sha256'] = sha256(root/'rules.json')
    (root/'pack.json').write_text(json.dumps(manifest))
    hidden = run([tmp_path/'gate', tmp_path/'label', root], rows, enabled=True, research=True, adapters=adapters)
    withheld = hidden['on_page'][-1]['events'][0]
    assert withheld['stake'] is None and withheld['channel_by_table'] is None
    manifest['gate_pin'] = 'gate@'+'0'*64
    (root/'pack.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='gate pin'):
        run([tmp_path/'gate', root], rows, enabled=True, research=True, adapters=adapters)


def test_durable_vector_cache_avoids_forward_and_is_encoder_bound(tmp_path):
    gate = make_pack(tmp_path/'gate', 'gate', 'gate', [[1]], [0], thresholds={'signal': .5})
    make_pack(tmp_path/'tags', 'tags', 'tags', [[1]], [0], thresholds={'signal': .5}, tag_map={'signal': 'N1'})
    calls = []
    def encode(texts):
        calls.extend(texts)
        return np.ones((len(texts), 1))
    adapters = {gate['encoder']['sha256']: (encode, len)}
    paths = [tmp_path/'gate', tmp_path/'tags']
    options = {'enabled': True, 'research': True, 'adapters': adapters,
               'cache_directory': tmp_path/'cache'}
    first = run(paths, sentence_rows('Same. New.'), **options)
    second = run(paths, sentence_rows('Same. New.'), **options)
    assert first == second and calls == ['Same.', 'New.']
    run(paths, sentence_rows('Different.'), **options)
    assert calls[-1] == 'Different.'


def test_unmapped_labels_have_no_invented_need(tmp_path):
    gate = make_pack(tmp_path/'gate', 'gate', 'gate', [[0]], [10], thresholds={'signal': .5})
    make_pack(tmp_path/'tags', 'tags', 'tags', [[0]], [10], labels=['romance'], thresholds={'romance': .5})
    result = run([tmp_path/'gate', tmp_path/'tags'], sentence_rows('A sentence.'), enabled=True, research=True,
                 adapters={gate['encoder']['sha256']: (lambda t: np.ones((len(t), 1)), len)})
    assert result['on_page'][0]['id'] is None
    assert result['on_page'][0]['events'][0]['label'] == 'romance'
    assert result['on_page'][0]['events'][0]['stake'] is None


def test_unit_table_and_fixed_provisional_tense():
    z = np.zeros((1, 29)); z[0, 7] = 2
    assert table_scores(z).tolist() == [[2, 0, 0, 0, -2]]
    assert [tense(t) for t in ['I might lose it.', 'She had left.', 'A blue box.']] == ['ahead', 'already', 'any']
