"""TP59 input preparation. Preserve source vocabularies and intersect exact saved IDs."""
import json
from pathlib import Path

import numpy as np

from cb_inputs import pin
from tompathy_engine.eval.readers.affect_data import ed_situations, go_comments
from tompathy_engine.eval.readers.envent import load
from tompathy_engine.eval.readers.tp30 import CHANNELS
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28, saved
from tompathy_engine.packs.trigger import TAGS
from week_pride_inputs import FROZEN, SOURCE

WEEK = Path('.local/week-20261122')
NEED = Path('.local/nine-channel/tp28-a')
DATA = Path('.local/readers/data')


def read(path):
    return json.loads(path.read_bytes())


def align(source_ids, forecast_ids):
    source = dict(zip(source_ids, range(len(source_ids)), strict=True))
    if len(source) != len(source_ids) or len(set(forecast_ids)) != len(forecast_ids):
        raise ValueError('Duplicate source unit')
    right = [i for i,key in enumerate(forecast_ids) if key in source]
    if not right:
        raise ValueError('No shared source units')
    return np.array([source[forecast_ids[i]] for i in right]), np.array(right)


def intake(name):
    if name == 'go':
        frame, truth, words, identity = go_comments(DATA/'go-emotions')
        keep = (frame.source_split != 'unreleased').to_numpy()
        return frame.id.to_numpy(str)[keep], truth[keep], words, identity
    if name == 'ed':
        frame, identity = ed_situations(DATA/'empathetic-dialogues')
        labels, ids = frame.label, frame.id
    else:
        source = load(DATA/'crowd-enVent2023')
        labels, ids = source.reports.emotion, source.reports.text_id
        identity = {'files':source.pins,'qualificationSetReuse':True}
    words = sorted(labels.unique())
    return ids.to_numpy(str), np.column_stack([labels == w for w in words]), words, identity


def prepare(out, check):
    audit = read(WEEK/'Q21-transfer.json')
    mirror = Path(audit['mirror'])
    if (pin(NEED/'receipt.json') != TP28 or pin(FROZEN/'receipt.json') != SOURCE
            or pin(mirror/'receipt.json') != audit['sourceReceiptPin']
            or audit['sourceReceiptPin'] != read(Path('engine/validation/readers-tp48-2026-11.json'))['source']
            or not audit['nativeExited'] or not audit['priorFlockReleased']):
        raise ValueError('Source receipt mismatch')
    needs, original = read(NEED/'receipt.json'), read(FROZEN/'receipt.json')
    if needs['protocol']['tags'] != list(TAGS):
        raise ValueError('Need tag order differs')
    result = {}
    for name in ('ed','envent','go'):
        check()
        ids, truth, words, identity = intake(name)
        if identity != needs['sources'][name]['identity']:
            raise ValueError('Source labels or intake changed')
        fname = name+'-ten.npz'
        if pin(mirror/fname) != audit['files'][fname]:
            raise ValueError('Changed ten-output file')
        tag_path = saved(NEED,name+'/scores.npz',needs)
        verify_order(tag_path,ids)
        with (np.load(tag_path,allow_pickle=False) as tags,
              np.load(saved(FROZEN,name+'-profile-forecasts.npz',original),allow_pickle=False) as nine,
              np.load(mirror/fname,allow_pickle=False) as ten):
            keys = nine['ids'].astype(str)
            if (not np.array_equal(tags['truth'],truth)
                    or not np.array_equal(ten['ten'][:,:9],nine['probabilities'])):
                raise ValueError('Original score binding differs')
            left,right = align(ids,keys)
            if name!='go' and (len(left)!=len(ids) or len(right)!=len(keys)):
                raise ValueError('Incomplete shared cohort')
            matrix = np.column_stack((ten['ten'][right],tags['scores'][left]))
            if matrix.shape!=(len(right),29) or not np.isfinite(matrix).all():
                raise ValueError('Invalid score block')
            path = out/(name+'.npz')
            with path.open('xb') as f:
                np.savez_compressed(f,ids=keys[right],truth=truth[left],words=np.asarray(words,str),scores=matrix)
            result[name]=dict(tagUnits=len(ids),tenUnits=len(keys),matched=len(right),filePin=pin(path))
    return dict(card='TP59-inputs',sources=result,columns=[*CHANNELS,'PRIDE',*TAGS],
                q21=audit['sourceReceiptPin'],tp28=TP28,originalNine=SOURCE,scope='Source-aligned inputs only')
