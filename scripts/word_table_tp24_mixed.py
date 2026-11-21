"""Join RD1's selected features to saved TP10 and G2 forecasts for the two TP24 rosters."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

for setting in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[setting] = '2'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))

import numpy as np
import pandas as pd
from tompathy_engine.eval.readers.checkpoint import completed
from tompathy_engine.eval.readers.envent import RATINGS
from tompathy_engine.eval.readers.word_panels import (
    CROSSWALK,
    FEATURES,
    MODEL,
    Mirror,
    pinned,
    read,
    sha256,
)
from word_table_tp24_prompted import (
    BASE,
    INITIAL_RECEIPT,
    INTAKE,
    ROOT,
    fresh_destination,
)

RD1 = '81fa38a6efe31542522b605b2a7935d609a7fde3510e88731b9727e41bc096bb'
FOLD_COPY = 'a238c07b4900bd97ab2cc84e50ad94216b0896b8c9573e3dcf18dc2090ffb515'


class CompletedMiniLMFolds:
    """A verified copy of closed forecast folds from the still-running parent study."""

    def __init__(self, audit, mirror):
        record = pinned(audit, FOLD_COPY)
        if (record['kind'] != 'G2 completed MiniLM forecast folds' or record['completedFolds'] != 5
                or record['parentStatusAtCopy'] != 'running' or not record['exactNativeAndFlock']
                or record['owner']['job'] != 'G2' or record['entry']['commit'] != record['owner']['commit']):
            raise ValueError('Expected the verified five-fold G2 copy')
        self.path = mirror
        self.files = record['files']

    def artifact(self, name):
        path = self.path/name
        if sha256(path) != self.files[name]:
            raise ValueError('Saved MiniLM fold differs from the remote bytes: '+name)
        return path


def mixed_features(ids, prompted, predictions, slots):
    if (len(set(ids)) != len(ids) or prompted.shape != (len(ids),len(FEATURES))
            or set(slots) != set(FEATURES) or not set(slots.values()) <= {'B','trained'}):
        raise ValueError('Unexpected report, feature order or RD1 assignment')
    trained = np.full(prompted.shape,np.nan)
    for i,key in enumerate(ids):
        if key in predictions:
            values = predictions[key]
            if np.shape(values) != (len(FEATURES),) or not np.isfinite(values).all():
                raise ValueError('Malformed trained feature forecast')
            trained[i] = values
    from_b = np.asarray([slots[f]=='B' for f in FEATURES])
    mixed = np.where(from_b,prompted,trained)
    masks = {name:np.isfinite(values).all(axis=1)
             for name,values in [('prompted',prompted),('trained',trained),('mixed',mixed)]}
    masks['common'] = masks['prompted'] & masks['trained'] & masks['mixed']
    return trained,mixed,masks


def fold_forecasts(g2, fold, expected, reserved, *, require_reserved=False):
    prefix = f'rung-0/rd2-trained/fold-{fold}/'
    terminal = prefix+'complete.json'
    if terminal not in g2.files:
        return {},'unfinished'
    summary = read(g2.artifact(terminal))
    selected = read(g2.artifact(prefix+'selection.json'))['selected']
    if summary['selectedSeed'] != selected['seed']:
        raise ValueError('G2 fold is bound to a different selected seed')
    files = sorted(n for n in g2.files if n.startswith(prefix+'forecasts-') and n.endswith('.npz'))
    found = {}
    reserved_seen = set()
    total = 0
    for name in files:
        if name != prefix+f'forecasts-{total:04d}.npz':
            raise ValueError('G2 forecast batches have a gap')
        with np.load(g2.artifact(name),allow_pickle=False) as z:
            ids,ratings,held = z['ids'],z['ratings'],z['F2']
            if (ids.ndim != 1 or not 0<len(ids)<=16 or held.shape != ids.shape or held.dtype != np.bool_
                    or ratings.shape != (len(ids),len(RATINGS)) or not np.isfinite(ratings).all()):
                raise ValueError('Malformed G2 fold forecast')
            for ident, forecast, is_reserved in zip(ids,ratings,held,strict=True):
                if is_reserved:
                    if ident not in reserved or ident in reserved_seen:
                        raise ValueError('Unexpected or duplicate reserved G2 report')
                    reserved_seen.add(ident)
                else:
                    if ident in found:
                        raise ValueError('Duplicate G2 forecast for a training report')
                    found[str(ident)] = forecast[[RATINGS.index(k) for k in FEATURES]]
            total += len(ids)
    if require_reserved and reserved_seen != reserved:
        raise ValueError('Reserved G2 roster differs from the registered partition')
    if list(found) != list(expected) or total != summary['rows']:
        raise ValueError('G2 forecasts differ from the registered writer-fold roster')
    return found,'complete'


def assemble(prompted_dir, g2_transfer, destination, prompted_pin=None):
    dest = fresh_destination(destination)
    prompted_dir,g2_transfer = prompted_dir.resolve(),g2_transfer.resolve()
    if prompted_dir.parent != BASE.resolve() or g2_transfer.parent != BASE.resolve():
        raise ValueError('Use private TP24 inputs and the verified G2 transfer')
    intake = pinned(BASE/'TP24-mixed-intake-a.json',INTAKE)
    source = read(g2_transfer)
    mirror = (ROOT/source['mirror']).resolve()
    if mirror.parent != BASE.resolve():
        raise ValueError('Unexpected G2 mirror')
    interim = source.get('kind') == 'G2 completed MiniLM forecast folds'
    if interim:
        g2 = CompletedMiniLMFolds(g2_transfer,mirror)
    else:
        g2 = Mirror(mirror,'G2')
        if (source['status'] != 'complete' or not source['nativeExited'] or not source['priorFlockReleased']
                or g2.pin != source['sourceReceiptPin'] or g2.receipt['owner'] != source['owner']):
            raise ValueError('G2 terminal transfer and release required')
    info = pinned(prompted_dir/'receipt.json',prompted_pin or INITIAL_RECEIPT)
    if info['reservedIncluded']==0:
        pinned(prompted_dir/'receipt.json',INITIAL_RECEIPT)
    else:
        transfer_name = info.get('q5TransferFile','Q5-transfer-a.json')
        if (Path(transfer_name).name != transfer_name or info.get('initialReceiptPin') != INITIAL_RECEIPT
                or info['reservedIncluded'] != 350 or info.get('q5TransferPin') != sha256(BASE/transfer_name)):
            raise ValueError('Extended B archive lost its Q5 transfer chain')
    if sha256(prompted_dir/'prompted.npz') != info['archivePin']:
        raise ValueError('Prompted forecast archive changed')
    with np.load(prompted_dir/'prompted.npz',allow_pickle=False) as z:
        ids,cohorts,prompted = z['reportIds'],z['cohorts'],z['ratings']
        if (z['features'].tolist() != list(FEATURES) or len(ids) != 6250+info['reservedIncluded']
                or cohorts.shape != ids.shape or len(set(ids)) != len(ids)):
            raise ValueError('Prompted forecast roster changed')
    public = read(ROOT/'engine/validation/readers-feature-slots-2026-11.json')
    rd1 = pinned(BASE/'rd1-a/receipt.json',RD1)
    if public['sourceReceiptPin'] != RD1 or public['slots'] != rd1['slots']:
        raise ValueError('RD1 feature selection differs from its public receipt')
    model = ROOT/'.local/readers/tp10-l3-a'
    original = completed(model,'TP10-L3')
    if sha256(model/'receipt.json') != MODEL:
        raise ValueError('The original trained reader changed')
    corpus = ROOT/'.local/readers/data/crowd-enVent2023/corpus'
    id_lists = {}
    for kind,digest in original['scope']['files'].items():
        path = corpus/f'crowd-enVent_{kind}.tsv'
        if sha256(path) != digest:
            raise ValueError('The original report roster changed')
        id_lists[kind] = pd.read_csv(path,sep='\t',quoting=3,usecols=['text_id'],dtype=str).text_id.to_numpy()
    whole = id_lists['generation']
    test = whole[np.isin(whole,id_lists['validation'])]
    seed = str(original['selected_seed'])
    original_path = model/f'seed-{seed}/predictions.npz'
    if sha256(original_path) != original['rows'][seed]['files']['predictions.npz']:
        raise ValueError('Original TP10 forecast archive changed')
    with np.load(original_path,allow_pickle=False) as z:
        ratings = z['ratings']
        if len(test)!=1200 or ratings.shape != (1200,len(RATINGS)) or not np.isfinite(ratings).all():
            raise ValueError('Incomplete original held-out ratings')
        predictions = dict(zip(test,ratings[:,[RATINGS.index(k) for k in FEATURES]],strict=True))
    aliases = pinned(BASE/'F2-release-local/local-original-id-map.json',CROSSWALK)
    split = BASE/'remaining-extension-a/inputs/G2-RD2.npz'
    if sha256(split) != intake['foldFilePin']:
        raise ValueError('Registered writer partitions changed')
    fold_status = {}
    with np.load(split,allow_pickle=False) as z:
        train,assignments = z['train_indices'],z['splits']
        partitions = z['folds']
        for i in range(5):
            expected = whole[train[assignments[i,train]==3]]
            reserved = {aliases[key] for key in whole[partitions==i] if key in aliases}
            if len(expected) != intake['trainingFoldSizes'][i]:
                raise ValueError('Registered G2 fold count differs')
            extra,fold_status[i] = fold_forecasts(g2,i,expected,reserved,require_reserved=interim)
            if predictions.keys() & extra.keys():
                raise ValueError('TP10 or G2 supplied the same trained report twice')
            predictions.update(extra)
    trained,mixed,masks = mixed_features(ids,prompted,predictions,rd1['slots'])
    receipt = {'card':'TP24','stage':'mixed input','newInference':False,
               'g2ReceiptPin':None if interim else g2.pin,
               'g2ParentStatusAtTransfer':'running' if interim else 'complete',
               'g2FoldCopyPin':FOLD_COPY if interim else None,
               'originalReaderPin':MODEL,'rd1ReceiptPin':RD1,'promptedReceiptPin':sha256(prompted_dir/'receipt.json'),
               'promptedArchivePin':info['archivePin'],'g2TransferPin':sha256(g2_transfer),
               'g2Folds':fold_status,'featureReaders':rd1['slots'],'features':list(FEATURES),
               'reports':len(ids),'coverage':{key:int(mask.sum()) for key,mask in masks.items()},
               'byCohort':{str(c):{k:int((v & (cohorts==c)).sum()) for k,v in masks.items()} for c in sorted(set(cohorts))}}
    with tempfile.TemporaryDirectory(dir=dest.parent) as temp:
        ready=Path(temp)/'ready'
        ready.mkdir()
        archive=ready/'features.npz'
        np.savez_compressed(archive,reportIds=ids,features=np.array(FEATURES),cohorts=cohorts,
                            prompted=prompted,trained=trained,mixed=mixed,common=masks['common'])
        receipt['archivePin'] = sha256(archive)
        (ready/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
        ready.rename(dest)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('prompted','g2_transfer','destination'):
        parser.add_argument(name,type=Path)
    parser.add_argument('--prompted-pin',help='Verified extended prompted receipt SHA-256; defaults to the fixed initial receipt.')
    args=parser.parse_args()
    print(json.dumps(assemble(args.prompted,args.g2_transfer,args.destination,args.prompted_pin)))
