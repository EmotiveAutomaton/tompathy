"""Pairwise movement and correlation of frozen, source-standardized need scores."""
import io
import itertools
import json
import zipfile
from pathlib import Path

import numpy as np

from ...packs.registry import sha256
from ...packs.trigger import TAG_MAP_V2, TAGS
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .checkpoint import completed
from .envent import load

SOURCE = '1bd4094c39de11b271796da1a4b4140c491dd86e483c346982327c51ba3dd56f'
NAMES = ('Competence', 'Meaning', 'Belonging (N3)', 'Respect', 'Compassion (N5)',
         'Body', 'Belonging (N3+N5)')
VIEWS = {'apart': (0,1,2,3,4,5), 'merged': (0,1,6,3,5)}
MEASURES = ('correlation', 'same', 'opposite', 'oneAlone', 'neither')
LIMIT = ("A tag is a word-proxy reader's contrast. Which tag belongs to which need is the map's. "
         "What a text is about is not what moved in its writer.")


def tag_weights():
    mapping = np.zeros((len(TAGS),7))
    for i, tag in enumerate(TAGS):
        code = TAG_MAP_V2.get(tag)
        if code:
            mapping[i,int(code[1:])-1] = 1
            if code in ('N3','N5'):
                mapping[i,6] = 1
    if np.any(mapping.sum(axis=0) == 0):
        raise ValueError('Empty need in fixed tag map')
    return mapping / mapping.sum(axis=0)


def movement(scores, weights):
    """Input is standardized by source. Strict movement thresholds preserve ties."""
    states = (scores>.5).astype(float) - (scores<-.5).astype(float)
    active = np.abs(states)
    both = (weights[:,None]*active).T@active
    signed = (weights[:,None]*states).T@states
    rate = weights@active
    one = rate[:,None] + rate[None,:] - 2*both
    return (both+signed)/2, (both-signed)/2, one, 1-both-one


def statistic(tags, squared, transform, weights):
    weights = np.asarray(weights,float)
    weights = weights / weights.sum()
    mean = weights@tags
    sd = np.sqrt(np.maximum(0, weights@squared-mean*mean))
    if np.any(sd==0):
        raise ValueError('Constant saved tag in source or bootstrap sample')
    kernel = transform/sd[:, None]
    scores = tags@kernel - mean@kernel
    scale = np.sqrt(weights@(scores*scores))
    if np.any(scale==0):
        raise ValueError('Constant need score')
    scores /= scale
    corr = (weights[:,None]*scores).T@scores
    return np.stack((corr, *movement(scores, weights)),axis=-1)


def pair_table(tags, writers, check, *, draws=2000):
    if tags.shape != (len(writers),len(TAGS)) or not np.isfinite(tags).all():
        raise ValueError('Expected 19 finite saved scores per ordered writer')
    _, cluster = np.unique(writers,return_inverse=True)
    nw = cluster.max()+1
    squared = tags**2
    transform = tag_weights()
    point = statistic(tags,squared,transform,np.ones(len(tags)))
    values = np.empty((draws,*point.shape))
    rng = np.random.default_rng(23)
    probs = np.full(nw,1/nw)
    for i in range(draws):
        if i%16 == 0:
            check()
        counts = rng.multinomial(nw,probs)
        values[i] = statistic(tags,squared,transform,counts[cluster])
    ci = np.quantile(values,[.025,.975],axis=0)
    result = {}
    for name, indices in VIEWS.items():
        pairs = {}
        for a,b in itertools.combinations(indices,2):
            cell = {k:{'estimate':float(point[a,b,j]),'interval':ci[:,a,b,j].tolist()}
                    for j,k in enumerate(MEASURES)}
            if not np.isclose(sum(cell[k]['estimate'] for k in MEASURES[1:]),1):
                raise ValueError('Movement shares do not sum to one')
            pairs[NAMES[a]+' / '+NAMES[b]] = cell
        correlations = {k:cell['correlation']['estimate'] for k,cell in pairs.items()}
        largest = max(correlations.values())
        result[name] = {'pairs':pairs,'highest':[k for k,v in correlations.items() if v==largest],
                        'atOrAbovePointEight':[k for k,v in correlations.items() if v>=.8]}
    return result


def verify_order(path, expected):
    # TP28 used an object dtype for its original IDs. Compare the exact stored
    # bytes to locally serialized source strings without executing a pickle.
    stream = io.BytesIO()
    np.save(stream,np.asarray(list(map(str,expected)),dtype=object))
    with zipfile.ZipFile(path) as archive:
        if archive.read('ids.npy') != stream.getvalue():
            raise ValueError('Writer join differs from the original ordered export')


def run(source, ed_dir, go_dir, corpus, output, check, ledger, protocol):
    source, output = Path(source), Path(output)
    original = completed(source,'TP28')
    if sha256(source/'receipt.json') != SOURCE or sha256(source/'artifact-manifest.json') != original['artifactsPin']:
        raise ValueError('Frozen TP28 source changed')
    if original['protocol']['tags'] != list(TAGS) or original['protocol']['tag_map'] != TAG_MAP_V2:
        raise ValueError('Original tag order or mapping differs')
    files = json.loads((source/'artifact-manifest.json').read_bytes())['files']
    receipt = {'card':'TP36','status':'running','productionAdmission':False,'scope':LIMIT,
               'ledger':ledger,'sourceReceiptPinTP28':SOURCE,'protocolPin':sha256(protocol),
               'sources':{},'writerDraws':2000,'tagMapVersion':2}
    for name in ('ed','go','envent'):
        check()
        rel = name+'/scores.npz'
        if sha256(source/rel) != files[rel]:
            raise ValueError('Source score bytes differ')
        if name=='ed':
            frame, identity = ed_situations(ed_dir)
            ids, writers = frame.id.to_numpy(str),frame.writer.to_numpy(str)
            unknown = 0
        elif name=='go':
            frame, _, _, identity = go_comments(go_dir)
            frame = frame[frame.source_split!='unreleased']
            ids = frame.id.to_numpy(str)
            writers = np.array(['author:'+w if known else 'unknown-comment:'+i
                                for w,known,i in zip(frame.writer,frame.writer_known,ids)])
            unknown = int((~frame.writer_known).sum())
        else:
            data = load(corpus)
            ids, writers = data.reports.text_id.astype(str).to_numpy(),data.reports.prolific_id.astype(str).to_numpy()
            identity = {'files':data.pins,'qualificationSetReuse':True}
            unknown=0
        if identity != original['sources'][name]['identity']:
            raise ValueError('Source corpus identity differs')
        verify_order(source/rel,ids)
        with np.load(source/rel,allow_pickle=False) as z:
            scores = np.asarray(z['scores'],dtype=float)
        save_json(output/'phase.json',{'source':name,'phase':'whole-writer intervals'})
        table=pair_table(scores,writers,check)
        receipt['sources'][name] = {'n':len(ids),'clusters':len(set(writers)), 'unknownWriterTexts':unknown,
                                    'scorePin':files[rel],'identity':identity,**table}
        save_json(output/'receipt.json',receipt)
    rows=list(receipt['sources'].values())
    lead=sum('Belonging (N3) / Compassion (N5)' in a['apart']['highest'] for a in rows)
    receipt.update(status='complete',distinctInEverySource=all(not a['apart']['atOrAbovePointEight'] for a in rows),
                   belongingCompassionHighestSources=lead,mergePredictionPasses=lead>=2)
    save_json(output/'receipt.json',receipt)
