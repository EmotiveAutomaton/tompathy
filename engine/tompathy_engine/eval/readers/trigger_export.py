"""Fresh private exports from qualified, exited source jobs. No automatic attachment."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ...packs.trigger import FEATURES, TAG_MAP, TAGS
from ...packs.v2 import code_pin, load_pack
from ..back_half.reporting import save_json
from .artifacts import model_identity, verified
from .checkpoint import completed
from .envent import RATINGS
from .preflight_scope import reproduction


def license_file(root, source, name, description, *, commercial=False):
    target = root/name
    shutil.copyfile(source, target)
    return {'name': description, 'file': name, 'source': description,
            'license': 'source declaration; research-only protocol' if not commercial else 'apache-2.0',
            'license_sha256': sha256(target), 'commercial_use': commercial}


def encoder(root, source, model_card, identity, check, *, kind='sentence-transformers'):
    shutil.copytree(source, root/'encoder')
    files = {}
    for path in sorted((root/'encoder').rglob('*')):
        if path.is_file():
            check()
            files[path.relative_to(root).as_posix()] = sha256(path)
    return {'id': identity, 'revision': 'exact-source-files', 'kind': kind, 'files': files,
            'sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'license': license_file(root, model_card, 'ENCODER_LICENSE.md', identity, commercial=kind != 'tfidf')}


def head(root, weights, bias):
    np.savez(root/'head.npz', weights=weights, bias=bias)
    return {'file': 'head.npz', 'sha256': sha256(root/'head.npz')}


def finish(root, manifest, evidence):
    save_json(root/'evidence.json', evidence)
    manifest.update(version='reader-pack-2', status='research', research_only=True,
                    code_pin=code_pin(), evidence={'file': 'evidence.json', 'sha256': sha256(root/'evidence.json')})
    save_json(root/'pack.json', manifest)
    return load_pack(root)


def base(name, task, labels, encoder_spec, head_spec, training, key, score):
    return {'name': name, 'task': task, 'labels': list(labels), 'encoder': encoder_spec,
            'head': head_spec, 'token_cap': 128, 'key': key, 'score': score,
            'people': {}, 'floor': {}, 'nothing_here': {}, 'training': training,
            'mapping': {'status': 'proposed', 'source': 'November15 trigger reader packet; no maker inference'}}


def need_pack(job, models, story, destination, check):
    job, models, story, destination = map(Path, (job, models, story, destination))
    card = json.loads((job/'receipt.json').read_text(encoding='utf8'))['card']
    receipt, _ = verified(job, card, check)
    if not card.startswith('TP23-') or not receipt.get('qualifies'):
        raise ValueError('A need pack requires both TP23 bars, including for BOW')
    # Check the numbers too; an accidentally set summary boolean cannot qualify.
    transfer = receipt['transfer']
    if (receipt['protocol']['rung'] != 'bow' and receipt['story']['mean_auc'] < .76) or not transfer['transfer_passed']:
        raise ValueError('Need-source bars differ')
    destination.mkdir(parents=True, exist_ok=False)
    rung = receipt['protocol']['rung']
    if rung == 'bow':
        (destination/'source-encoder').mkdir()
        shutil.copyfile(job/'vocabulary.json', destination/'source-encoder/vocabulary.json')
        enc = encoder(destination, destination/'source-encoder', story/'README.txt', 'TP23 fixed TF-IDF', check, kind='tfidf')
        weights = job/'head.npz'
    else:
        model_root = models/('base' if rung == 'base' else 'minilm')
        original = model_identity(model_root, check)
        if any(original.get(k) != receipt['encoder'].get(k) for k in ('id', 'revision', 'files')):
            raise ValueError('Need encoder source changed after evaluation')
        source = job/'full-head/encoder' if rung in {'fine', 'base'} else model_root
        enc = encoder(destination, source, model_root/'README.md', original['id']+' TP23 '+rung, check)
        weights = job/'full-head/head.npz' if rung in {'fine', 'base'} else job/'head.npz'
    with np.load(weights, allow_pickle=False) as d:
        linear = head(destination, d['weights'], d['bias'])
    training = [license_file(destination, story/'README.txt', 'DATA_README.md', 'Story Commonsense archive; license unstated')]
    m = base('rp-need-1', 'tags', TAGS, enc, linear, training,
             {'corpus': 'Story Commonsense', 'labelled_by': 'two-annotator majority, original story folds', 'n': receipt['source']['rows']},
             {'metric': 'mean story-held-out tag AUC', 'value': receipt['story']['mean_auc']})
    m.update(thresholds=dict(zip(TAGS, receipt['story']['thresholds'])), tag_map=TAG_MAP)
    m['people'] = receipt['people']['per_tag_f1']
    return finish(destination, m, {'sourceReceiptPin': sha256(job/'receipt.json'), 'artifactsPin': receipt['artifactsPin'],
        'transfer': transfer, 'fullDataHeadIndependentlyScored': False, 'N5': 'computed; hidden in panel',
        'unmapped': ['romance', 'indep']})


def gate_pack(job, models, story, destination, check, *, corpus, go):
    job, models, story, destination = map(Path, (job, models, story, destination))
    receipt, _ = verified(job, 'TP25', check)
    if (not receipt.get('qualifies') or not receipt['final_validation_qualified']
            or any(not r['validation_qualified'] or r['sensitivity'] < .7 for r in receipt['rows'].values())
            or any(r['silence'] < .8 for r in receipt['neutral'].values())):
        raise ValueError('Gate does not meet fixed held-out/neutral bars')
    destination.mkdir(parents=True, exist_ok=False)
    original = model_identity(models/'minilm', check)
    if any(original.get(k) != receipt['encoder'].get(k) for k in ('id', 'revision', 'files')):
        raise ValueError('Gate encoder source changed after evaluation')
    enc = encoder(destination, models/'minilm', models/'minilm/README.md', 'frozen MiniLM TP25', check)
    with np.load(job/'head.npz', allow_pickle=False) as d:
        linear = head(destination, d['weights'], d['bias'])
    training = [license_file(destination, story/'README.txt', 'DATA_README.md', 'Story Commonsense plus Crowd-enVENT and GoEmotions; restricted by unstated story license')]
    training += [license_file(destination, Path(corpus)/'LICENSE.txt', 'ENVENT_LICENSE.txt', 'Crowd-enVENT source license'),
                 license_file(destination, Path(go)/'LICENSE-CARD.md', 'GO_LICENSE.md', 'GoEmotions source license')]
    m = base('rp-gate-1', 'gate', ['stakes'], enc, linear, training,
             {'corpus': 'Crowd-enVENT, Story Commonsense, GoEmotions', 'labelled_by': 'released human affect/neutral keys',
              'n': sum(r['n'] for r in receipt['rows'].values())},
             {'metric': 'minimum held-out-source sensitivity', 'value': min(r['sensitivity'] for r in receipt['rows'].values())})
    m.update(thresholds={'stakes': receipt['final_threshold']},
             nothing_here={name: r['silence'] for name, r in receipt['neutral'].items()})
    return finish(destination, m, {'sourceReceiptPin': sha256(job/'receipt.json'), 'artifactsPin': receipt['artifactsPin'],
                                   'protocol': receipt['protocol'], 'rows': receipt['rows'], 'neutral': receipt['neutral']})


def l3_source(job, check):
    job = Path(job)
    receipt = completed(job, 'TP10-L3')
    seed = receipt['selected_seed']
    root = job/f'seed-{seed}'
    for name, pin in receipt['rows'][str(seed)]['files'].items():
        check()
        path = (root/name).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path) != pin:
            raise ValueError('Selected feature/label reader bytes changed')
    return root, receipt


def label_pack(job, models, destination, check, *, corpus):
    job, models, destination = map(Path, (job, models, destination))
    source, receipt = l3_source(job, check)
    destination.mkdir(parents=True, exist_ok=False)
    enc = encoder(destination, source/'encoder', models/'minilm/README.md', 'selected TP10 L3 MiniLM', check)
    with np.load(source/'head.npz', allow_pickle=False) as d:
        linear = head(destination, d['weights'], d['bias'])
    training = [license_file(destination, Path(corpus)/'LICENSE.txt', 'DATA_LICENSE.txt', 'Crowd-enVENT source license; research-only TP10 protocol')]
    row = receipt['rows'][str(receipt['selected_seed'])]
    labels = row['labels']
    m = base('rp-label-1', 'channel', labels, enc, linear, training,
             {'corpus': 'Crowd-enVENT', 'labelled_by': 'writer emotion label', 'n': 6600},
             {'metric': 'selected TP10 held-out macro F1; original gate failed', 'value': row['macro_f1']})
    m.update(neutral='no-emotion', label_map={'anger': 'C2', 'fear': 'C3', 'sadness': 'C6', 'shame': 'C9', 'disgust': 'C8'})
    return finish(destination, m, {'sourceReceiptPin': sha256(job/'receipt.json'), 'sourceGates': row['gates'],
                                   'scope': 'Research sentence events only; no aggregation receipt, shares or maker inference'})


def trigger_pack(job, needs, gate, label, reader_job, models, destination, check):
    job, reader_job, models, destination = map(Path, (job, reader_job, models, destination))
    receipt, _ = verified(job, 'TP24', check)
    needs, gate = load_pack(needs), load_pack(gate)
    label = load_pack(label) if label is not None else None
    if needs.manifest.task != 'tags' or gate.manifest.task != 'gate' or (label and label.manifest.task != 'channel'):
        raise ValueError('Wrong composite dependencies')
    need_evidence = json.loads((needs.root/'evidence.json').read_text(encoding='utf8'))
    if need_evidence['sourceReceiptPin'] != receipt['needsReceiptPin']:
        raise ValueError('Trigger needs differ from its measured slots')
    source, _ = l3_source(reader_job, check)
    if receipt['reader']['sourceReceiptPin'] != sha256(reader_job/'receipt.json'):
        raise ValueError('Trigger feature source differs')
    destination.mkdir(parents=True, exist_ok=False)
    # Root placeholder uses the need encoder/head; components have independent pins.
    shutil.copytree(needs.root/'encoder', destination/'encoder')
    shutil.copyfile(needs.root/'ENCODER_LICENSE.md', destination/'ENCODER_LICENSE.md')
    shutil.copyfile(needs.root/'DATA_README.md', destination/'DATA_README.md')
    shutil.copyfile(needs.root/'head.npz', destination/'head.npz')
    shutil.copytree(needs.root, destination/'need')
    (destination/'features').mkdir()
    feature_enc = encoder(destination/'features', source/'encoder', models/'minilm/README.md', 'selected TP10 L3 feature encoder', check)
    with np.load(source/'head.npz', allow_pickle=False) as d:
        indices = [RATINGS.index(n) for n in FEATURES]
        feature_head = head(destination/'features', d['ratings_weights'][indices], d['ratings_bias'][indices])
    shutil.copyfile(job/'trigger-rules.json', destination/'trigger-rules.json')
    m = needs.manifest.model_dump(mode='json')
    m.update(name='rp-trigger-1', task='trigger', thresholds={}, tag_map={},
             gate_pin=gate.pin, label_pin=label.pin if label else None,
             trigger_rules={'file': 'trigger-rules.json', 'sha256': receipt['rulesPin']},
             need_head={'directory': 'need', 'encoder': m['encoder'], 'head': m['head'], 'labels': list(TAGS), 'token_cap': 128},
             feature_head={'directory': 'features', 'encoder': feature_enc, 'head': feature_head, 'labels': list(FEATURES), 'token_cap': 128})
    return finish(destination, m, {'sourceReceiptPin': sha256(job/'receipt.json'), 'artifactsPin': receipt['artifactsPin'],
        'needs': needs.pin, 'gate': gate.pin, 'label': label.pin if label else None,
        'stakesQualified': receipt['stakes_qualified'], 'tense': receipt['tense'], 'table': receipt['table'],
        'scope': receipt['scope']})


def im2(job, pack, destination, check):
    job, destination = Path(job), Path(destination)
    card = json.loads((job/'receipt.json').read_text(encoding='utf8'))['card']
    receipt, _ = verified(job, card, check)
    reader = load_pack(pack)
    evidence = json.loads((reader.root/'evidence.json').read_text(encoding='utf8'))
    if not receipt.get('qualifies') or evidence['sourceReceiptPin'] != sha256(job/'receipt.json'):
        raise ValueError('IM2 requires the exact qualified packed source')
    with np.load(job/'envent-tags.npz', allow_pickle=False) as d:
        if d['scores'].shape != (6600, 19) or not np.isfinite(d['scores']).all():
            raise ValueError('IM2 needs all 6600 finite tag-score rows')
        import pandas as pd
        frame = pd.DataFrame(d['scores'], columns=TAGS)
        frame.insert(0, 'text_id', d['text_id'])
    destination.mkdir(parents=True, exist_ok=False)
    frame.to_csv(destination/'scores.csv', index=False, float_format='%.17g')
    save_json(destination/'manifest.json', {'schema': 'IM2-1', 'files': {'scores.csv': sha256(destination/'scores.csv')},
        'rows': 6600, 'tags': list(TAGS), 'reader': reader.pin, 'encoder': reader.manifest.encoder.sha256,
        'head': reader.manifest.head.sha256, 'sourceReceiptPin': sha256(job/'receipt.json'),
        'scope': 'Private owner-carried exchange; no raw text, writer IDs or cross-chat delivery; no maker admission'})


def qualified_counting(label_directory, counting_job, gate_directory, destination, check):
    label, gate = load_pack(label_directory), load_pack(gate_directory)
    counting_job, destination = Path(counting_job), Path(destination)
    result = completed(counting_job, 'TP12-gated')
    policy = result['policies']['minilm-tuned']
    gate_evidence = json.loads((gate.root/'evidence.json').read_text(encoding='utf8'))
    label_evidence = json.loads((label.root/'evidence.json').read_text(encoding='utf8'))
    if (policy['status'] != 'complete' or policy['minimum'] is None
            or policy['gateReceiptPin'] != gate_evidence['sourceReceiptPin']
            or policy['ladderReceiptPin'] != label_evidence['sourceReceiptPin']):
        raise ValueError('New counting policy or exact reader/gate binding is unqualified')
    if sha256(counting_job/'gated-error-table.json') != result['gatedErrorTablePin'] or policy['gatedErrorTablePin'] != result['gatedErrorTablePin']:
        raise ValueError('New counting calibration bytes differ from completed source')
    check()
    shutil.copytree(label.root, destination)
    selection = dict(policy, gatePackPin=gate.pin)
    save_json(destination/'selection.json', selection)
    shutil.copyfile(counting_job/'gated-error-table.json', destination/'error-table.json')
    manifest = label.manifest.model_dump(mode='json')
    manifest.update(gate_pin=gate.pin, table={'file': 'error-table.json', 'sha256': sha256(destination/'error-table.json')},
        aggregation={'prior': policy['prior'], 'minimum': policy['minimum'], 'bootstrap': policy['bootstrap'],
                     'seed': policy['seed'], 'selection': {'file': 'selection.json', 'sha256': sha256(destination/'selection.json')}})
    return finish(destination, manifest, {**label_evidence, 'countingSourcePin': sha256(counting_job/'receipt.json'),
        'scope': 'Research-only corrected shares with exact qualified gate; maker tier closed', 'gate': gate.pin})


def reseal_worry(job, destination, check):
    """Compatibility export, never mutate the original fitted pack or benchmark."""
    job, destination = Path(job), Path(destination)
    receipt = completed(job, 'TP26')
    source = job/'rp-worry-1'
    if sha256(source/'pack.json') != receipt['pack']['manifestPin'] or sha256(source/'head.npz') != receipt['pack']['headPin']:
        raise ValueError('Original worry pack differs from its completed receipt')
    manifest = json.loads((source/'pack.json').read_text(encoding='utf8'))
    training = json.loads((source/'training.json').read_text(encoding='utf8'))
    if sha256(source/'training.json') != receipt['pack']['trainingPin'] or sha256(job/'full-head/head.npz') != training['sourceHeadPin']:
        raise ValueError('Original worry training provenance changed')
    from ...packs.v2 import Manifest, verify_encoder
    parsed = Manifest.model_validate(manifest)
    verify_encoder(source, parsed.encoder)
    with np.load(job/'full-head/head.npz', allow_pickle=False) as d, np.load(source/'head.npz', allow_pickle=False) as exported:
        if not np.array_equal(exported['weights'], d['weights']*d['scale'][:, None]) or not np.array_equal(exported['bias'], d['bias']*d['scale']+d['mean']):
            raise ValueError('Original worry scaling differs')
        # Known-answer linear parity, no model inference or benchmark rerun.
        vectors = np.random.default_rng(23).normal(size=(19, d['weights'].shape[1])).astype(np.float32)
        expected = (vectors@d['weights'].T+d['bias'])*d['scale']+d['mean']
        actual = vectors@exported['weights'].T+exported['bias']
        if not np.allclose(expected, actual, rtol=1e-5, atol=1e-5):
            raise ValueError('Resealed scalar calculation differs')
    check()
    shutil.copytree(source, destination)
    for name, pin in manifest['encoder']['files'].items():
        check()
        if sha256(destination/name) != pin:
            raise ValueError('Worry encoder copy differs')
    return finish(destination, manifest, {'sourceReceiptPin': sha256(job/'receipt.json'),
        'originalPackPin': receipt['pack']['pin'], 'originalCodePin': manifest['code_pin'],
        'sourceHeadPin': sha256(job/'full-head/head.npz'), 'encoderUnchanged': True, 'headUnchanged': True,
        'compatibility': 'same normalized vectors, exact weights/scaling; constructed linear parity passed; no new accuracy claim'})


def select_need(jobs, check, preflight_decision=None):
    """Seed selection uses development only; failed selected seed is not replaced."""
    sources = {}
    for job in jobs:
        job = Path(job)
        card = json.loads((job/'receipt.json').read_text(encoding='utf8'))['card']
        if card not in {'TP23-bow', 'TP23-frozen', 'TP23-fine-23', 'TP23-fine-47', 'TP23-fine-71', 'TP23-base'} or card in sources:
            raise ValueError('Expected unique completed TP23 rungs')
        receipt, _ = verified(job, card, check)
        sources[card] = (job, receipt)
    if 'TP23-bow' not in sources:
        raise ValueError('Need selection requires successful preflight reproduction')
    preflight = reproduction(*sources['TP23-bow'], preflight_decision)
    candidates = [v for k, v in sources.items() if k in {'TP23-bow', 'TP23-frozen', 'TP23-base'}]
    fine = [sources[k] for k in ('TP23-fine-23', 'TP23-fine-47', 'TP23-fine-71') if k in sources]
    selected_seed = None
    if len(fine) == 3:
        selected = max(fine, key=lambda v: (v[1]['story']['development_auc'], -v[1]['protocol']['seed']))
        selected_seed = selected[1]['protocol']['seed']
        candidates.append(selected)
    qualified = [v for v in candidates if v[1]['qualifies']]
    chosen = max(qualified, key=lambda v: v[1]['story']['development_auc']) if qualified else None
    return chosen[0] if chosen else None, {'sources': {k: sha256(v[0]/'receipt.json') for k, v in sources.items()},
        'selectedFineSeed': selected_seed, 'selectedCard': chosen[1]['card'] if chosen else None,
        'preflightScope': preflight,
        'rule': 'Select fine seed by mean inner-development AUC before applying its gates; then best development AUC among qualified rungs. Incomplete three-seed fine rung is not substituted.'}


def run_export(kind, args, output, check):
    output = Path(output)
    receipt = {'card': 'TRIGGER-export-'+kind, 'status': 'running', 'productionAdmission': False, 'ledger': 'no ledger row',
               'scope': 'Private opt-in research export; no automatic live attachment or release', 'pack': None}
    save_json(output/'receipt.json', receipt)
    destination = output/('rp-'+{'worry': 'worry', 'need': 'need', 'gate': 'gate', 'label': 'label', 'trigger': 'trigger', 'counting': 'label'}[kind]+'-1')
    if kind == 'worry':
        pack = reseal_worry(args.primary_job, destination, check)
    elif kind == 'need':
        chosen, selection = select_need(args.rung_jobs, check, getattr(args, 'preflight_decision', None))
        receipt['selection'] = selection
        if chosen is None:
            receipt.update(status='blocked', reason='No selected need rung clears both unchanged bars')
            save_json(output/'receipt.json', receipt)
            return
        pack = need_pack(chosen, args.models, args.rated_data, destination, check)
        im2(chosen, destination, output/'IM2', check)
        receipt['IM2ManifestPin'] = sha256(output/'IM2/manifest.json')
    elif kind == 'gate':
        pack = gate_pack(args.gate_job, args.models, args.rated_data, destination, check, corpus=args.corpus, go=args.go)
    elif kind == 'label':
        pack = label_pack(args.reader_job, args.models, destination, check, corpus=args.corpus)
    elif kind == 'trigger':
        pack = trigger_pack(args.primary_job, args.need_pack, args.gate_pack, args.label_pack, args.reader_job, args.models, destination, check)
    elif kind == 'counting':
        pack = qualified_counting(args.label_pack, args.counting, args.gate_pack, destination, check)
    else:
        raise ValueError('Unknown trigger export')
    receipt.update(status='complete', pack={'name': pack.manifest.name, 'pin': pack.pin, 'encoder': pack.manifest.encoder.sha256,
        'head': pack.manifest.head.sha256, 'evidencePin': pack.manifest.evidence.sha256, 'researchOnly': True})
    save_json(output/'receipt.json', receipt)
