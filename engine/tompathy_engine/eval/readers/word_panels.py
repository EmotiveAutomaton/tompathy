"""Local-only RD1 and RD2 comparisons of verified, already saved reader answers."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ...packs.registry import sha256
from ...packs.trigger import FEATURES
from ..back_half.reporting import save_json
from .checkpoint import completed
from .envent import RATINGS, load
from .rd2_panels import _spearman, comparison, panel_masks, research_reader, slot_comparison

TWO = ('standards','social_norms')
CANDIDATES = {'pleasantness','unpleasantness','self_responsblt','other_responsblt'}
SELECTION = '37ccfe31e919be30c47bf92e2b6223b82884941127c53e77ef28e2a3e20c650e'
CROSSWALK = '4917aec33c86337cf68dbd50ec853556a73c6a25c6a763642ca6c726aa0418c0'
OVERLAPS = 'b0fe2b9a5953eeadd8a73823171cfd56d063b0add40888676a22a9fcf63ec078'
PRIOR_USE = '831ddc27a2af2bf4c40687a4833217321dd6eab0f54b9413887d40b6341e7fc3'
MODEL = 'ac5aa48a1e9a83d681969eadf9c7a8268831be97f8fbbc42b259ff72c226b759'
Q1_SOURCE = '17813970705a9b72a64e7054f857f3eac8eb3b8f3a65a4b8ff9a63ecde1fa2db'
# This Q5 worker inventoried the role directories. Its verified all-file transfer
# also covers the three root records used for the held-out comparison.
Q5_SOURCE = '8de7fbb932c02e5829b149c5edfeb1ae7f024899fbc1e02bddfeaa8991af5a5a'
Q5_TRANSFER_RECORDS = {
    'development-selection.json': '351dfedb1338c3905d18368aac9f2e60dfa210e86ec370289966684936a93c30',
    'arm-status.json': '6536f4baa52936e5b1a27ea7d5239bd5b5dc52b5c8bdd936d6bb79d9e36f375f',
    'C-general-checks.json': 'b319c0ad6455d0fcb7f50bcddf90a223ba1ebb7cc72011865bed53b499c643f7',
}
# Canonical queue entries include the registered commit, code hashes and input manifest.
OPENING_ENTRY = '17fa422d6494d19d97a680137d0b7f2d959bd9348941bdd765264f11572edc9a'
ENTRIES = {
    'Q1': OPENING_ENTRY, 'Q2': OPENING_ENTRY,
    'Q5': 'd2566e657571d95fa80c65057ed4da40292e0031bc7712d410ff4a773386ce1d',
    'G2': '101e3fe6f1ca8ea8125be690c3ce9a385f3d742e93d439dd35b8bc4f9276f8cf',
}
READER_IDS = {
    'A': '56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90',
    'B': '72aac7c28be8ff9b81c2a270eb489c88e6d822a76ec0cb7bf34d965768848567',
}


def read(path):
    return json.loads(path.read_bytes())


def pinned(path, expected):
    if sha256(path) != expected:
        raise ValueError('Input does not match the registered digest: '+path.name)
    return read(path)


class Mirror:
    """Verify the Spark receipt, exact release and each artifact used by this analysis."""

    def __init__(self, path, job):
        self.path = Path(path)
        if job == 'G2-modernbert-a':
            self._modernbert()
            return
        if job == 'G2' and (self.path/'failed.json').is_file():
            self._compiler_stop()
            return
        receipt_pin = read(self.path/'complete.json')['receiptPin']
        self.receipt = pinned(self.path/'receipt.json',receipt_pin)
        release = read(self.path/'released.json')
        entry = self.receipt['entry']
        entry_bytes = json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        owner = self.receipt['owner']
        if (self.receipt['job'] != job or self.receipt['status'] != 'complete' or self.receipt['lane'] != 'spark'
                or hashlib.sha256(entry_bytes).hexdigest() != ENTRIES[job]
                or (job == 'Q1' and receipt_pin != Q1_SOURCE)
                or owner['job'] != job or owner['commit'] != entry['commit']
                or release['owner'] != owner or release['nativeExitCode'] != 0
                or not release['descriptorClosed']):
            raise ValueError('Expected a completed Spark job and matching native release')
        self.files = pinned(self.path/'artifacts.json',self.receipt['artifactsPin'])['files']
        self.pin = receipt_pin

    def _modernbert(self):
        job = 'G2-modernbert-a'
        base = self.path.parent
        cfg = pinned(base/'g2-repair-execution-a.json','f187fe3e8a7d18ec5932d02ee829280decf3fd367b310a8d6ca4f92ab22d5f41')
        audit = read(base/(job+'-transfer-a.json'))
        self.pin = audit['sourceReceiptPin']
        self.receipt = pinned(self.path/'receipt.json',self.pin)
        owner = self.receipt['owner']
        release = read(self.path/'released.json')
        parent = Mirror(base/'verified-spark-G2-a','G2')
        if (audit['terminal']!='complete.json' or self.receipt['status']!='complete'
                or not audit['nativeExited'] or not audit['priorFlockReleased'] or release!=audit['release']
                or not release['descriptorClosed'] or release['nativeExitCode']!=0
                or (audit['launcherExit']['pid'],audit['launcherExit']['code'])!=(owner['pid'],0)
                or owner!=audit['owner'] or release['owner']!=owner or self.receipt['job']!=job or owner['job']!=job
                or self.receipt['lane']!='spark' or self.receipt['entry']!=cfg or owner['commit']!=cfg['commit']
                or self.receipt['parentReceiptPin']!=parent.pin or cfg['originalReceiptPin']!=parent.pin
                or any(self.receipt['scienceEntry'].get(k)!=v for k,v in parent.receipt['entry'].items())
                or Path(audit['mirror']).resolve()!=self.path.resolve()
                or read(self.path/'complete.json')['receiptPin']!=self.pin):
            raise ValueError('Expected a verified, source-bound, completed ModernBERT repair')
        self.files = pinned(base/(job+'-transfer-a-pins.json'),audit['inventoryPin'])
        if len(self.files)!=audit['verifiedFiles'] or self.files.get('receipt.json')!=self.pin:
            raise ValueError('Incomplete ModernBERT transfer inventory')

    def _compiler_stop(self):
        # Only this known engineering stop has fully verified MPNet fold seals.
        self.pin = '91f2681cfc76e8a79116a6d38c32bf68bbec31dcef24dc8eefb0cb447cb82267'
        self.receipt = pinned(self.path/'receipt.json',self.pin)
        failure = read(self.path/'failed.json')
        release = read(self.path/'released.json')
        transfer = read(self.path.parent/'G2-transfer-a.json')
        inventory = self.path.parent/'G2-transfer-a-pins.json'
        owner = self.receipt['owner']
        if (self.receipt['status']!='failed' or self.receipt['job']!='G2' or self.receipt['lane']!='spark'
                or failure['receiptPin']!=self.pin or transfer['sourceReceiptPin']!=self.pin
                or owner!=release['owner'] or owner!=transfer['owner'] or transfer['release']!=release
                or release['nativeExitCode']!=1 or not release['descriptorClosed']
                or not transfer['nativeExited'] or not transfer['priorFlockReleased']
                or Path(transfer['mirror']).resolve()!=self.path.resolve()
                or transfer['terminal']!='failed.json' or transfer['verifiedFiles']!=26937
                or transfer['inventoryPin']!='d156ac6a3be107fff57640073b638f62567d6849d24b0ea9207856b7af01d6af'):
            raise ValueError('G2 compiler-stop transfer and exact release required')
        self.files = pinned(inventory,transfer['inventoryPin'])
        if len(self.files)!=transfer['verifiedFiles'] or self.files.get('receipt.json')!=self.pin:
            raise ValueError('G2 partial inventory differs')

    def artifact(self, name):
        path = self.path/name
        expected = self.files.get(name)
        if expected is None and self.pin == Q5_SOURCE:
            expected = Q5_TRANSFER_RECORDS.get(name)
        if expected is None or sha256(path) != expected:
            raise ValueError('Saved Spark artifact differs: '+name)
        return path

    def answers(self, arm, role, ids, features, check):
        prefix = f'{arm}/{role}' if arm else role
        summary = read(self.artifact(prefix+'/complete.json'))
        binding = summary['binding']
        if (summary['rows'] != len(ids) or binding['role'] != role
                or binding['job'] != self.receipt['job'] or binding['commit'] != self.receipt['owner']['commit']
                or binding['sourcePin'] != self.receipt['entry']['sourcePin']
                or binding['codePins'] != self.receipt['entry']['codePins']
                or (role in READER_IDS and binding['modelPin'] != READER_IDS[role])
                or binding.get('arm','') != arm):
            raise ValueError('Response arm, model binding or cohort differs')
        values = np.full((len(ids),len(features)),np.nan)
        for i, ident in enumerate(ids):
            if i%64==0:
                check()
            record = read(self.artifact(f'{prefix}/row-{i:06d}.json'))
            if record['index'] != i or record['id'] != ident or record['binding'] != binding:
                raise ValueError('Saved response does not match its registered report or reader')
            answer = record['values']
            if answer is None:
                continue
            scores = [answer[k] for k in features] if isinstance(answer,dict) else answer
            if len(scores)!=len(features) or any(type(v) is not int or not 1<=v<=5 for v in scores):
                raise ValueError('Invalid saved response marked as usable')
            values[i] = scores
        if np.isfinite(values).all(axis=1).sum()!=summary['valid']:
            raise ValueError('Saved response validity count differs')
        return values


def references(corpus, trained_job, original_ids):
    data = load(corpus)
    job = Path(trained_job)
    r = completed(job,'TP10-L3')
    if sha256(job/'receipt.json')!=MODEL or r['scope']['files']!=data.pins:
        raise ValueError('Trained reader or original writer ratings differ')
    seed = r['selected_seed']
    saved = job/f'seed-{seed}/predictions.npz'
    if sha256(saved)!=r['rows'][str(seed)]['files']['predictions.npz']:
        raise ValueError('Trained comparator predictions changed')
    frame = data.reports.iloc[data.test]
    positions = {key:i for i,key in enumerate(frame.text_id.astype(str))}
    idx = [positions[key] for key in original_ids]
    truth = frame.iloc[idx][list(FEATURES)].to_numpy(float)
    with np.load(saved,allow_pickle=False) as z:
        if z['ratings'].shape!=(1200,21):
            raise ValueError('Original held-out comparator roster differs')
        baseline = z['ratings'][idx][:,[RATINGS.index(f) for f in FEATURES]]
    ratings = pd.read_csv(Path(corpus)/'corpus/crowd-enVent_validation.tsv',sep='\t',
                          usecols=['text_id','prolific_id',*FEATURES],dtype={'text_id':str,'prolific_id':str})
    ratings = ratings[ratings.text_id.isin(original_ids)].copy()
    local_order = {k:i for i,k in enumerate(original_ids)}
    ratings['index'] = ratings.text_id.map(local_order)
    if (len(ratings)!=5*len(original_ids) or ratings.duplicated(['index','prolific_id']).any()
            or not (ratings.groupby('index').size()==5).all()):
        raise ValueError('Expected five distinct rereaders on each original report')
    return baseline,truth,ratings


def human_reference(ratings, truth, keep, features):
    part = ratings[ratings['index'].isin(np.flatnonzero(keep))]
    means = part.groupby('index')[list(features)].mean().sort_index()
    output = {}
    for feature in features:
        j = FEATURES.index(feature)
        single = []
        for _, group in part.groupby('prolific_id'):
            idx = group['index'].to_numpy()
            if len(idx)>=2:
                rho = _spearman(group[feature].to_numpy(),truth[idx,j])
                if np.isfinite(rho):
                    single.append(float(rho))
        ceiling = _spearman(means[feature].to_numpy(),truth[means.index,j])
        output[feature] = {'reports':len(means),'rereaders':int(part.prolific_id.nunique()),
                           'estimableRereaders':len(single),'singleRereaderMean':float(np.mean(single)) if single else None,
                           'meanOfFiveRho':float(ceiling) if np.isfinite(ceiling) else None}
    return output


def trained_rungs(job, ids, check, *, only=None):
    arrays, status = {}, {}
    for index,name in [(1,'mpnet-base'),(2,'ModernBERT-large')]:
        if only is not None and index!=only:
            continue
        root = f'rung-{index}/rd2-trained'
        if any(f'{root}/fold-{f}/complete.json' not in job.files for f in range(5)):
            status[name] = 'No complete five-fold trained predictions at this boundary'
            continue
        forecasts = {}
        for filename in sorted(k for k in job.files if k.startswith(root+'/') and '/forecasts-' in k):
            check()
            with np.load(job.artifact(filename),allow_pickle=False) as z:
                identifiers, ratings, reserved = z['ids'], z['ratings'], z['F2']
                if (identifiers.ndim != 1 or reserved.dtype != np.bool_
                        or reserved.shape != identifiers.shape or ratings.shape != (len(identifiers), len(RATINGS))
                        or not np.isfinite(ratings).all()):
                    raise ValueError('Malformed saved trained forecasts or reserved-panel mask')
                for ident, prediction in zip(identifiers[reserved], ratings[reserved], strict=True):
                    if str(ident) in forecasts:
                        raise ValueError('Duplicate trained F2 forecast')
                    forecasts[str(ident)] = prediction
        if not forecasts:
            status[name] = 'Training used the sealed payload before F2 was released'
            continue
        if set(forecasts)!=set(ids):
            raise ValueError('Incomplete or substituted trained F2 forecast roster')
        arrays[name] = np.array([forecasts[i] for i in ids])[:,[RATINGS.index(f) for f in TWO]]
        status[name] = 'complete'
    return arrays,status


def run(card, corpus, prepared, mirror, trained_job, output, check, ledger, protocol, *, companion=None):
    root = Path(prepared)
    selection = pinned(root/'intake-a/reserved-ids.json',SELECTION)
    source = Mirror(mirror,'Q1' if card=='RD1' else 'Q5')
    common = {'card':card,'status':'complete','productionAdmission':False,'ledger':ledger,
              'protocolPin':sha256(protocol),'readerJobPin':source.pin,'trainedReceiptPin':MODEL}
    if card=='RD1':
        if companion is None:
            raise ValueError('RD1 is scheduled after Q2')
        q2 = Mirror(companion,'Q2')
        ids = selection['F1']
        if len(set(ids))!=350 or set(ids)&set(selection['F2']):
            raise ValueError('F1 roster differs')
        baseline,y,human = references(corpus,trained_job,ids)
        readers = {k:source.answers('',k,ids,FEATURES,check) for k in ('A','B')}
        rows,slots = {},{}
        for j,k in enumerate(FEATURES):
            rows[k] = {role:comparison(p[:,j],baseline[:,j],y[:,j],check) for role,p in readers.items()}
            slots[k] = 'B' if k in CANDIDATES and rows[k]['B']['namedOnF2'] else 'trained'
            for row in rows[k].values():
                row['positiveDifferenceInterval'] = row.pop('namedOnF2')
        common.update(rows=rows,slots=slots,companionPin=q2.pin,human=human_reference(human,y,np.ones(350,bool),FEATURES),
                      scope=("A panel of 350 places a rank correlation within about 0.05 either way. "
                             "Writers' ratings are one person's account of an event, so no reader can be "
                             "expected to match them fully; the human reference says how far a careful stranger gets."))
    elif card=='RD2':
        selection_file = source.artifact('development-selection.json')
        selection_record = read(selection_file)
        winners = selection_record['winners']
        status = read(source.artifact('arm-status.json'))
        if (set(winners)!=set(TWO) or selection_record!=status['developmentSelection']
                or any(v not in {f'V{i}' for i in range(6)} for v in winners.values())):
            raise ValueError('F2 awaits the frozen development winners')
        original = selection['F2']
        crosswalk = pinned(root/'F2-release-local/local-original-id-map.json',CROSSWALK)
        if set(crosswalk) != set(original):
            raise ValueError('F2 crosswalk differs from the registered roster')
        ids = [crosswalk[k] for k in original]
        approved = pinned(root/'F2-release-local/local-overlap-audit.json',OVERLAPS)['affectedOpaqueIds']
        masks = panel_masks(ids,approved)
        baseline,y,human = references(corpus,trained_job,original)
        best = np.empty((350,2))
        for variant in set(winners.values()):
            response = source.answers('F2-'+variant,'B',ids,TWO,check)
            for j,k in enumerate(TWO):
                if winners[k]==variant:
                    best[:,j] = response[:,j]
        candidates = {'developmentWinnerB':best}
        standard = source.answers('F2-standard','B',ids,FEATURES,check)
        size_result = None
        if status['readerCGeneralPass']:
            general = read(source.artifact('C-general-checks.json'))
            if (not general['passes'] or general['pairs'] != 300 or general['outputs'] != 600
                    or general['identicalPairs'] < 297 or general['valid'] < 597):
                raise ValueError('Reader C lacks the registered repeat and validity evidence')
            bindings = [read(source.artifact(arm+'/C/complete.json'))['binding']
                        for arm in ('C-development','C-repeat','F2-C')]
            identity_fields = ('modelPin','options','think','promptPin','schemaPin','codePins','sourcePin')
            if any(binding[key] != bindings[0][key] for binding in bindings[1:] for key in identity_fields):
                raise ValueError('Reader C, its questions or its generation settings changed between panels')
            c = source.answers('F2-C','C',ids,FEATURES,check)
            candidates['C'] = c[:,[FEATURES.index(k) for k in TWO]]
            size_result = research_reader(ids,approved,c,standard,y)
            size_result['features'] = list(FEATURES)
            size_result['featureNamesChanged'] = [FEATURES[i] for i in size_result['featureComparisonsChanged']]
            size_result['modelPin'] = bindings[0]['modelPin']
        trained_status = {'mpnet-base':'pending','ModernBERT-large':'pending'}
        if companion:
            g2 = Mirror(companion,'G2')
            extra,trained_status = trained_rungs(g2,ids,check)
            candidates.update(extra)
            common['companionPin'] = g2.pin
            followup = Path(companion).parent/'G2-modernbert-a-transfer-a.json'
            if followup.exists() and read(followup)['status']=='complete':
                modern = Mirror(followup.parent/'verified-spark-G2-modernbert-a-a','G2-modernbert-a')
                extra,late = trained_rungs(modern,ids,check,only=2)
                candidates.update(extra)
                trained_status.update(late)
                common['modernbertReceiptPin'] = modern.pin
        else:
            common['status'] = 'partial'
        # TP10's frozen all-1200 comparison included every proposed F3 report.
        historical = pinned(root/'F3-prior-use.json',PRIOR_USE)
        if historical['eligibleForSlotConfirmation'] or historical['priorSourceReceiptPin']!=MODEL:
            raise ValueError('F3 historical eligibility proof differs')
        rows,flags = {},[]
        for name,p in candidates.items():
            rows[name] = {}
            for j,k in enumerate(TWO):
                column = FEATURES.index(k)
                row = slot_comparison(ids,approved,p[:,j],baseline[:,column],y[:,column],check)
                rows[name][k] = row
                if row['nominationChanges'] or row['slotConclusionChanges']:
                    flags.append({'candidate':name,'feature':k,'nominationChanges':row['nominationChanges'],
                                  'slotConclusionChanges':row['slotConclusionChanges']})
        common.update(rows=rows,differenceFlags=flags,developmentWinners=winners,trainedArms=trained_status,
                      researchReaderC=size_result,overlapAuditPin=OVERLAPS,primaryReports=350,textFreshReports=348,
                      developmentSelectionPin=sha256(selection_file),
                      f3Status='Prior trained-reader comparison against writer ratings included all 200; slot confirmation unavailable.',
                      human={name:human_reference(human,y,keep,TWO) for name,keep in masks.items()},
                      scope='Two features in one source of recalled events written to a feeling word.')
    else:
        raise ValueError('Unknown comparison')
    save_json(Path(output)/'receipt.json',common)
