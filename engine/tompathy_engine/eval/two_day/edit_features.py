"""Recover only EX2-selected features from its authenticated producer checkpoints."""
from pathlib import Path
from time import monotonic

import numpy as np

from ...admission import implementation_hash
from ...features.deterministic import edit_features
from ...ledger.ids import digest
from ..back_half.edits import CATEGORIES, classifier, scores
from ..back_half.metrics import fit_logistic, predict
from ..back_half.reporting import bind_run, save_json
from .exports import read, sha, verify_export


def recover(directory, export_run, analysis_run, feature_run, prepared, check=lambda: None):
    import pyarrow.parquet as pq
    directory, export_run, analysis_run, feature_run, prepared = map(Path, (directory, export_run, analysis_run, feature_run, prepared))
    manifest, pin = verify_export(directory, 'EX2')
    binding = manifest['source_binding']
    for path, expected in ((analysis_run/'COMPLETE.json', binding['analysis_complete']),
                           (feature_run/'COMPLETE.json', binding['feature_complete']),
                           (feature_run/'output/FEATURES.json', binding['feature_report'])):
        if sha(path) != expected:
            raise ValueError('EX2 producer completion differs')
    completed = read(export_run/'COMPLETE.json')
    def bound(name):
        path = (export_run/name).resolve()
        if not path.is_relative_to(export_run.resolve()) or sha(path) != completed['outputs'][name]:
            raise ValueError('EX2 selected checkpoint is not completion-bound')
        return read(path)
    if sha(export_run/'output/bundle/MANIFEST.json') != sha(directory/'MANIFEST.json'):
        raise ValueError('Producer export differs from received bundle')
    state = bound('output/STATE.json')
    if state['binding'] != binding:
        raise ValueError('Selected checkpoint binding differs')
    selected = sorted((entry[3] for heap in state['heaps'].values() for entry in heap), key=lambda r: r['primary_index'])
    raw = read(directory/'EDITS.json')
    if len(selected) != len(raw) or len({r['primary_index'] for r in selected}) != len(raw):
        raise ValueError('Selection identity/count differs')
    requested, joined = {}, {}
    for index, (meta, exported) in enumerate(zip(selected, raw, strict=True)):
        source = bound(f"output/selected_text/{meta['site']}-{meta['source_row']:09d}.json")
        if (source['before'], source['after'], meta['reason'], meta['user_fold'], meta['classifier_output']) != (
                exported['before'], exported['after'], exported['reason_category'], exported['user_fold'], exported['classifier_output']):
            raise ValueError('Selected feature row no longer matches delivered text/fold/label')
        if source['editor'] != meta['editor'] or source['post'] != meta['post'] or meta['site'] != exported['site']:
            raise ValueError('Selected editor/source metadata differs')
        ident = digest([pin, index])
        requested[meta['site'], meta['source_row']] = (ident, meta)
    bank, feature_complete = read(feature_run/'output/FEATURES.json'), read(feature_run/'COMPLETE.json')
    names = [f'diff_{i}' for i in range(14)]+['intent_'+k for k in ('clarity', 'coherence', 'fluency', 'meaning-changed', 'others', 'style')]
    selected_ids = {r['id'] for r in read(prepared/'edits.json')}
    blocks_read = 0
    for block in bank['blocks']:
        wanted = [(offset, requested[block['site'], offset]) for offset in range(block['first_row'], block['first_row']+block['rows'])
                  if (block['site'], offset) in requested and requested[block['site'], offset][0] in selected_ids]
        if not wanted:
            continue
        check()
        name = 'output/'+block['path']
        path = (feature_run/name).resolve()
        if not path.is_relative_to(feature_run.resolve()) or sha(path) != block['sha256'] or block['sha256'] != feature_complete['outputs'][name]:
            raise ValueError('Selected feature block differs')
        table = pq.read_table(path, columns=['editor', 'reason', *names], use_threads=False)
        for offset, (ident, meta) in wanted:
            row = table.slice(offset-block['first_row'], 1).to_pylist()[0]
            if row['editor'] != meta['editor'] or row['reason'] != meta['reason']:
                raise ValueError('Feature identity/label mapping differs')
            joined[ident] = {'writer': row['editor'], 'features': {name: float(row[name]) for name in names}}
        blocks_read += 1
    rows = read(prepared/'edits.json')
    if set(joined) != {r['id'] for r in rows}:
        raise ValueError('Not all eligible exported edits have authenticated features')
    enriched, writers = [], {}
    for row in rows:
        source = joined[row['id']]
        if source['writer'] in writers and writers[source['writer']] != row['fold']:
            raise ValueError('A recovered editor crosses folds')
        writers[source['writer']] = row['fold']
        start = monotonic()
        engine_x = list(edit_features(row['before'], row['after']).values())
        enriched.append({**row, **source, 'x': engine_x+list(source['features'].values()),
                         'engineFeatureSeconds': monotonic()-start})
    save_json(prepared/'edits-enriched.json', enriched)
    report = {'exportPin': pin, 'producerBinding': binding, 'selectedRows': len(enriched), 'writers': len(writers),
              'featureNames': names, 'blocksRead': blocks_read, 'featureRowsPin': digest(enriched),
              'missing': ['original per-edit feature-generation timing'],
              'scope': 'only already-exported EX2 observations; no refit or wider source study'}
    save_json(prepared/'edits-enrichment.json', report)
    return report


def run(prepared, output, check):
    prepared, output = Path(prepared), Path(output)
    rows = read(prepared/'edits-enriched.json')
    intake = read(prepared/'edits-enrichment.json')
    if digest(rows) != intake['featureRowsPin']:
        raise ValueError('Recovered features changed')
    bind_run(output, {'kind': 'TP3-feature', 'dataPin': digest(intake), 'codePin': implementation_hash()})
    check()
    probabilities, gates, timings = classifier(rows)
    result = {'status': 'feature complete; Q8 comparison pending', 'dataPin': digest(intake), 'codePin': implementation_hash(),
              'feature': scores([r['category'] for r in rows], [CATEGORIES[i] for i in probabilities.argmax(axis=1)]),
              'speedQualification': 'unavailable: original supplied-feature generation timings absent',
              'productionAdmission': False}
    save_json(output/'probabilities.json', probabilities.tolist())
    save_json(output/'gates.json', gates)
    save_json(output/'timings.json', timings)
    save_json(output/'receipt.json', result)
    return result


def human_baseline(prepared):
    """Fit only EX2 using engine diff features; exclude IteraTeR-trained sidecars."""
    prepared = Path(prepared)
    source, target = read(prepared/'edits-enriched.json'), read(prepared/'human-edits.json')
    x = [list(edit_features(r['before'], r['after']).values()) for r in source]
    y = [CATEGORIES.index(r['category']) for r in source]
    model = fit_logistic(x, y, classes=5)
    probabilities = predict(model, [list(edit_features(r['replaced'], r['replacement']).values()) for r in target])
    mapping = ['fluency', 'fluency', 'clarity', 'meaning-changed', 'meaning-changed']
    from .pilots import intent_scores
    return {'kind': 'EX2-only feature control', 'status': 'complete', 'codePin': implementation_hash(), 'productionAdmission': False,
            'features': 'engine deterministic diff features only; human-trained intent sidecars excluded',
            'modelPin': digest({k: v.tolist() for k, v in model.items()}), 'trainingPin': digest(source),
            'samplePin': digest(target), 'scores': intent_scores([r['intention'] for r in target], [mapping[int(i)] for i in np.argmax(probabilities, axis=1)])}
