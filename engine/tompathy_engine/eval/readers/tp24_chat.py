"""TP24's descriptive second source, using the durable Q6 prefix at the owner review."""
import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.special import logit

from ...packs.trigger import FEATURES, TAGS, table_scores
from ..back_half.reporting import save_json
from .affect_data import ed_situations
from .artifacts import seal
from .envent import RATINGS
from .tp24_mixed import CHANNELS, checked_artifact
from .tp28 import MAP
from .tp30 import WRITER_CHANNELS
from .word_panels import pinned, read, sha256

EXTENSION = '792386aa4c3bb129328599e658bae26790ac7989a624d40ce422383a6f7dad58'
REPORTS = '388b8734e7a9c4513bbd1d37d61e6b0b4f840df6cc6d28ff1ca4f09f579380aa'
TP13 = 'aecfcc8faca2d7eb9411a5de62b6210f5aa62ac3e5d3db93f1c0467dda4c8b59'
ED_VECTORS = 'cc4b5a400a35b9ac3edc67565fbcb33ec274e1b1bc18252ba7b718647359432b'
TP28 = '1bd4094c39de11b271796da1a4b4140c491dd86e483c346982327c51ba3dd56f'
REFERENCE_PROTOCOL = '91c1eadea7dc54710e0576e7dc7dc6b1a2850537a7e5b51dd37e56e2f0bbda7a'
MORNING = datetime.fromisoformat('2026-11-21T07:00:00-08:00')


def assess(labels, scores):
    """Keep every eligible writer word, including missing forecasts and unrepresented channels."""
    mapping = {word: ('SADNESS' if channel == 'PANIC/GRIEF' else channel)
               for channel in WRITER_CHANNELS for word in MAP[channel]['ed']}
    gold = np.array([mapping.get(label, '') for label in labels], dtype=str)
    eligible = gold != ''
    covered = np.isfinite(scores).all(axis=1)
    calls = np.full(len(gold), '', dtype='U8')
    calls[covered] = np.array(CHANNELS)[scores[covered].argmax(axis=1)]
    right = eligible & (gold == calls)
    total = int(eligible.sum())
    rows = {}
    for channel in WRITER_CHANNELS:
        target = 'SADNESS' if channel == 'PANIC/GRIEF' else channel
        mask = gold == target
        rows[channel] = {'eligible':int(mask.sum()), 'withInputs':int((mask & covered).sum()),
                         'correct':int(right[mask].sum()), 'tableEmitsChannel':target in CHANNELS,
                         'calls':{call:int(np.sum(calls[mask] == call)) for call in CHANNELS}}
    return calls, {'attempted':len(labels),'eligibleWriterWords':total,'outsideMap':int((~eligible).sum()),
        'eligibleMissingInput':int((eligible & ~covered).sum()),'correct':int(right.sum()),
        'accuracyOnAllEligible':int(right.sum())/total if total else None,'byChannel':rows}


def prefix(base, boundary, items, check, *, full_terminal=False):
    if boundary.get('job')=='Q6' and 'archivePin' in boundary:
        folder = base.parent/'person-teacher/prefix'
        identity = 'fbd6719f76631b4304a93c34972ead5334a7090b2ed7a3e342dc5d10ccd823a5'
        if boundary!=pinned(folder/'inventory.json',identity):
            raise ValueError('Curator-authorized November 21 prefix differs')
        mirror = folder/'rows'
        entry = pinned(base/'remaining-extension-a/extension.json',EXTENSION)['entries']['Q6']
        if boundary['entry']!=entry or boundary['owner']['commit']!=entry['commit']:
            raise ValueError('Q6 live prefix registration differs')
        inventory = boundary['files']
        names = sorted(inventory)
        count = boundary['durableRows']
        if names!=[f'B/row-{i:06d}.json' for i in range(count)] or count>len(items):
            raise ValueError('Live prefix is incomplete')
        source_pin = identity
    else:
        if full_terminal:
            if boundary.get('terminalStudy') != 'TP39' or boundary['durableRows'] != len(items):
                raise ValueError('The person study requires the entire Q6 roster')
        else:
            stamp = datetime.fromisoformat(boundary['ownerTurnAt'])
            if stamp.tzinfo is None or stamp < MORNING or boundary['trigger'] != 'owner-turn':
                raise ValueError('The first eligible owner turn is required')
        audit = read(base/'Q6-transfer-a.json')
        mirror = base/'verified-spark-Q6-a'
        entry = pinned(base/'remaining-extension-a/extension.json',EXTENSION)['entries']['Q6']
        receipt = pinned(mirror/'receipt.json',audit['sourceReceiptPin'])
        inventory = pinned(base/'Q6-transfer-a-pins.json', audit['inventoryPin'])
        release = pinned(mirror/'released.json',inventory['released.json'])
        terminal = audit['terminal']
        if full_terminal and (terminal != 'complete.json' or receipt['status'] != 'complete'):
            raise ValueError('The person study requires a successful terminal receipt')
        if (Path(audit['mirror']).resolve()!=mirror.resolve() or not audit['nativeExited']
                or not audit['priorFlockReleased'] or len(inventory)!=audit['verifiedFiles']
                or receipt['entry']!=entry or receipt['job']!='Q6' or receipt['lane']!='spark'
                or receipt['owner']!=boundary['owner'] or release!=audit['release'] or not release['descriptorClosed']
                or release['owner']!=receipt['owner'] or receipt['owner']!=audit['owner']
                or terminal not in ('failed.json','complete.json')
                or pinned(mirror/terminal,inventory[terminal])['receiptPin']!=audit['sourceReceiptPin']):
            raise ValueError('Q6 terminal, ownership or transfer differs')
        names = sorted(k for k in inventory if k.startswith('B/row-') and k.endswith('.json'))
        count = boundary['durableRows']
        if (type(count) is not int or not 0 <= count <= len(names) <= len(items)
                or names != [f'B/row-{i:06d}.json' for i in range(len(names))]):
            raise ValueError('Q6 prefix count, order or coverage differs')
        source_pin = audit['sourceReceiptPin']
    answers = np.full((count,len(FEATURES)),np.nan)
    reference = pinned(base/'verified-spark-Q1-a/B/protocol.json',REFERENCE_PROTOCOL)
    binding = {**entry, 'job':'Q6', 'inputPin':sha256(base/'remaining-extension-a/inputs/Q6.json'),
               **{k:reference[k] for k in ('modelPin','options','role','think','schemaPin','promptPin')}}
    for i, name in enumerate(names[:count]):
        if i%64==0:
            check()
        row = pinned(mirror/name,inventory[name])
        if row['id']!=items[i]['id'] or row['index']!=i or row['binding']!=binding:
            raise ValueError('Q6 saved response ID or model, prompt and option binding differs')
        try:
            raw = json.loads(row['response']['response'])
        except (KeyError, ValueError, TypeError):
            raw = None
        valid = isinstance(raw,dict) and set(raw)==set(FEATURES) and all(
            type(value) is int and 1<=value<=5 for value in raw.values())
        values = [raw[key] for key in FEATURES] if valid else None
        if values != row['values']:
            raise ValueError('Q6 response validity differs from its raw answer')
        if valid:
            answers[i] = values
    return answers, source_pin, len(names)


def run(base, ed, tp13, tp28, reports, boundary_path, output, check, ledger, protocol):
    base, tp13, tp28, reports, output = map(Path,(base,tp13,tp28,reports,output))
    boundary = read(boundary_path)
    intake = base/'remaining-extension-a'
    config = pinned(intake/'extension.json',EXTENSION)
    items = pinned(intake/'inputs/Q6.json',config['files']['inputs/Q6.json'])
    prompted, source_pin, durable = prefix(base,boundary,items,check)
    check()
    frame, ed_identity = ed_situations(ed)
    feature_source = pinned(tp13/'receipt.json',TP13)
    tag_source = pinned(tp28/'receipt.json',TP28)
    words = tag_source['sources']['ed']
    if (feature_source['data']['ed']!=ed_identity or words['identity']!=ed_identity
            or tag_source['protocol']['tags']!=list(TAGS) or tag_source['protocol']['mapping']!=MAP):
        raise ValueError('ED identity, word map or tag order differs')
    order = sorted(range(len(frame)), key=lambda i:hashlib.sha256(('TP24:23:'+frame.id.iat[i]).encode()).digest())
    ordered = frame.iloc[order]
    if list(zip(ordered.id,ordered.text,strict=True))!=[(r['id'],r['text']) for r in items]:
        raise ValueError('Registered Q6 texts or order differ')
    indices = order[:len(prompted)]
    features_path = tp13/'ed-vectors.npz'
    if sha256(features_path)!=ED_VECTORS:
        raise ValueError('Saved TP13 ED features changed')
    with np.load(features_path,allow_pickle=False) as saved:
        full = saved['features']
        if full.shape!=(len(frame),len(RATINGS)) or not np.isfinite(full).all():
            raise ValueError('Incomplete trained features')
        trained = full[np.ix_(np.asarray(indices,dtype=int),[RATINGS.index(k) for k in FEATURES])]
    tag_files = pinned(tp28/'artifact-manifest.json',tag_source['artifactsPin'])['files']
    archive = checked_artifact(tp28,'ed/scores.npz',tag_files)
    with zipfile.ZipFile(archive) as files:
        expected = io.BytesIO()
        np.save(expected,frame.id.to_numpy(dtype=object))
        historical_ids_match = files.read('ids.npy')==expected.getvalue()
    with np.load(archive,allow_pickle=False) as saved:
        if ((not historical_ids_match and not np.array_equal(saved['ids'],frame.id)) or saved['scores'].shape!=(len(frame),len(TAGS))
                or not np.array_equal(saved['truth'],np.column_stack([frame.label==word for word in words['labels']]))):
            raise ValueError('Tag rows and writer words do not match ED')
        probabilities = saved['scores'][indices]
    mixed_source = pinned(reports/'receipt.json',REPORTS)
    if sha256(protocol)!=mixed_source['protocolPin']:
        raise ValueError('Filed mixed-feature procedure changed')
    report = mixed_source['cohorts']['extended']
    files = pinned(reports/'artifact-manifest.json',mixed_source['artifactsPin'])['files']
    with np.load(checked_artifact(reports,'extended/table-scale.npz',files),allow_pickle=False) as saved:
        mean,scale,include_tense = saved['mean'],saved['scale'],bool(saved['when'])
    if (include_tense or mean.shape!=(29,) or scale.shape!=(29,) or not np.isfinite(mean).all()
            or not np.isfinite(scale).all() or not (scale>0).all()):
        raise ValueError('Expected the filed 29 columns and omitted tense')
    slots = report['featureReaders']
    if slots!={k:('B' if k in ('pleasantness','unpleasantness') else 'trained') for k in FEATURES}:
        raise ValueError('RD1 source assignments differ')
    mix = np.where([slots[key]=='B' for key in FEATURES],prompted,trained)
    usable_tags = np.isfinite(probabilities).all(axis=1) & ((probabilities>0)&(probabilities<1)).all(axis=1)
    logits = np.full(probabilities.shape,np.nan)
    logits[usable_tags] = logit(probabilities[usable_tags])
    values = np.column_stack((mix,logits,np.zeros((len(mix),2))))
    complete = np.isfinite(values).all(axis=1)
    scores = np.full((len(mix),len(CHANNELS)),np.nan)
    scores[complete] = table_scores((values[complete]-mean)/scale,include_tense=False)
    cohort = frame.iloc[indices]
    calls,row = assess(cohort.label,scores)
    artifact = output/'prefix.npz'
    np.savez_compressed(artifact,ids=cohort.id.to_numpy(str),words=cohort.label.to_numpy(str),scores=scores,calls=calls)
    row.update(**({'durableAtCapture':durable} if 'archivePin' in boundary else {'durableAtExit':durable}),missingB=int((~np.isfinite(prompted).all(axis=1)).sum()),
               missingTrained=int((~np.isfinite(trained).all(axis=1)).sum()),missingNeedLogits=int((~usable_tags).sum()),
               recalledFiveWordAccuracy=report['table']['accuracy'])
    save_json(output/'receipt.json',{'card':'TP24-chat','status':'complete','ledger':ledger,'productionAdmission':False,
        'scope':'Ordered ED prefix, seven writer stand-ins, five emitted channels. Feature validity has no writer rating here. ED research only.',
        'protocolPin':sha256(protocol),'sources':{'Q6':source_pin,'TP13':TP13,'TP28':TP28,'TP24Reports':REPORTS,
        'boundary':sha256(boundary_path),'trainedFeatureFile':ED_VECTORS},'row':row,'artifactsPin':seal(output,[artifact],check)})
