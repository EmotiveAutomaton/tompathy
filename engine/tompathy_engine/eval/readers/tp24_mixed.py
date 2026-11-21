"""TP24 on two registered report rosters using completed text-derived inputs."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import GroupKFold

from ...packs.trigger import FEATURES, TAGS, table_scores, tense
from ..back_half.reporting import save_json
from .artifacts import seal
from .checkpoint import completed
from .tp23 import sigmoid
from .tp24 import LOSS, evaluate_with_choices, forecasts
from .word_panels import pinned, sha256

ROSTERS = {
    'initial': '01fb294b8ca73da019cefa4583cc23043fe261104d187dcec7eaf940f234ab05',
    'extended': '0fae63302559eaf0a45a6ed588372ab9334bce72872f385a7bbaa3d569886f88',
}
C0 = '85e9b12fb8b8c2318dee928f651a5da80c78f642ca91f17d050d7e47a5d67bd7'
NEEDS = '1d996fdce019a3cbf60bb55ad7cb77fdd0dc6d5481e0f95f8a8c9b4025334bf4'
PROFILE = 'd04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250'
CHANNELS = ('RAGE', 'FEAR', 'SADNESS', 'SHAME', 'DISGUST')
LIMIT = ('Recalled-event feeling words and text-derived feature forecasts. The downstream folds hold out writers. '
         'The five training-report feature folds also hold out writers. The original 1,200-report TP10 test '
         'shares writers with its training set. The fixed table was developed with knowledge of this corpus.')


def checked_artifact(root, name, files):
    path = root/name
    if sha256(path) != files[name]:
        raise ValueError('Source artifact changed: '+name)
    return path


def sources(corpus, c0, needs, profile, check):
    c0, needs, profile = map(Path, (c0, needs, profile))
    for folder, card, digest in ((c0,'TRIGGER-export-need',C0), (needs,'TP23-frozen',NEEDS),
                                  (profile,'TP30-frozen',PROFILE)):
        check()
        completed(folder, card)
        pinned(folder/'receipt.json', digest)
    c0_receipt = pinned(c0/'receipt.json', C0)
    manifest = pinned(c0/'IM2/manifest.json', c0_receipt['IM2ManifestPin'])
    if manifest['sourceReceiptPin'] != NEEDS or manifest['tags'] != list(TAGS) or manifest['tagMapVersion'] != 2:
        raise ValueError('C0 does not bind the qualified need reader and ordered 19 tags')
    exported = pd.read_csv(checked_artifact(c0/'IM2','scores.csv',manifest['files']),
                           dtype={'text_id': str}, float_precision='round_trip')
    need_receipt = pinned(needs/'receipt.json', NEEDS)
    if not need_receipt['qualifies'] or list(exported.columns) != ['text_id', *TAGS]:
        raise ValueError('Need reader or C0 score order differs')
    need_files = pinned(needs/'artifact-manifest.json',need_receipt['artifactsPin'])['files']
    with np.load(checked_artifact(needs,'envent-tags.npz',need_files),allow_pickle=False) as saved:
        ids, logits, scores = saved['text_id'].astype(str), saved['logits'], saved['scores']
    if (logits.shape != (6600,19) or not np.isfinite(logits).all() or not np.array_equal(scores,sigmoid(logits))
            or not np.array_equal(ids,exported.text_id) or not np.array_equal(scores,exported[list(TAGS)].to_numpy())):
        raise ValueError('C0 order or scores differ from the fitted logits')
    receipt = pinned(profile/'receipt.json',PROFILE)
    profile_files = pinned(profile/'artifact-manifest.json',receipt['artifactsPin'])['files']
    generation = Path(corpus)/'corpus/crowd-enVent_generation.tsv'
    if sha256(generation) != receipt['sources']['envent']['files']['generation']:
        raise ValueError('Crowd-enVENT source differs')
    frame = pd.read_csv(generation, sep='\t', quoting=3, dtype={'text_id': str},
                        usecols=['text_id','prolific_id','emotion','hidden_emo_text'])
    if (frame.text_id.duplicated().any() or not np.array_equal(ids,frame.text_id)
            or frame[['prolific_id','emotion']].isna().any().any() or frame.emotion.nunique() != 13):
        raise ValueError('Original report IDs, feeling words or writer join differs')
    with np.load(checked_artifact(profile,'vectors.npz',profile_files),allow_pickle=False) as saved:
        vectors = saved['envent']
    with np.load(checked_artifact(profile,'envent-profile-forecasts.npz',profile_files),allow_pickle=False) as saved:
        if not np.array_equal(saved['ids'].astype(str),ids):
            raise ValueError('TP30 profile report order differs')
        nine = saved['probabilities']
    if (nine.shape != (len(ids),9) or not np.isfinite(nine).all() or not ((0<=nine)&(nine<=1)).all()
            or vectors.shape != (len(ids),384) or not np.isfinite(vectors).all()):
        raise ValueError('Invalid saved TP30 forecasts or direct vectors')
    originals = receipt['protocol']['channels']
    profile_indices = [originals.index('PANIC/GRIEF' if name == 'SADNESS' else name) for name in CHANNELS]
    return frame, logits, vectors, nine[:,profile_indices]


def common_rows(folder, stage):
    folder = Path(folder)
    info = pinned(folder/'receipt.json',ROSTERS[stage])
    if sha256(folder/'features.npz') != info['archivePin']:
        raise ValueError('TP24 feature archive changed')
    with np.load(folder/'features.npz',allow_pickle=False) as data:
        ids, groups, common = data['reportIds'], data['cohorts'], data['common']
        feature_order = data['features'].tolist()
        matrices = {name:data[name] for name in ('mixed','trained','prompted')}
    if (feature_order != list(FEATURES) or groups.shape != ids.shape or len(set(ids)) != len(ids)
            or any(m.shape != (len(ids),8) for m in matrices.values()) or common.dtype != np.bool_):
        raise ValueError('Feature order, shape or report roster differs')
    real_common = np.logical_and.reduce([np.isfinite(m).all(axis=1) for m in matrices.values()])
    if not np.array_equal(common,real_common) or common.sum() != info['coverage']['common']:
        raise ValueError('The comparison denominator differs from the three completed feature views')
    return info, ids[common], groups[common], {k:v[common] for k,v in matrices.items()}


def correlation(left, right):
    if len(left) < 2 or np.ptp(left) == 0 or np.ptp(right) == 0:
        return None
    return float(spearmanr(left,right).statistic)


def table_profile(slots, when, y, writers, include_when, check):
    matrix = np.column_stack((slots,when))
    profile = np.empty((len(y),len(LOSS)))
    for train,test in GroupKFold(5).split(matrix,y,writers):
        check()
        scaled = (matrix[test]-matrix[train].mean(0))/(matrix[train].std(0)+1e-9)
        profile[test] = table_scores(scaled,include_when)
    return profile


def profile_comparison(table, fitted):
    if table.shape != fitted.shape or table.ndim != 2 or table.shape[1] != len(CHANNELS):
        raise ValueError('Table and fitted five-channel profiles must share rows and channel order')
    top, other = table.argmax(axis=1), fitted.argmax(axis=1)
    pairs = confusion_matrix(top,other,labels=list(range(len(CHANNELS))))
    return {'n':len(table), 'channels':list(CHANNELS), 'tableByTP30':pairs.tolist(),
            'disagreements':int((top!=other).sum()), 'agreement':float((top==other).mean()),
            'tableTopTies':int(((table==table.max(axis=1,keepdims=True)).sum(axis=1)>1).sum()),
            'TP30TopTies':int(((fitted==fitted.max(axis=1,keepdims=True)).sum(axis=1)>1).sum()),
            'tieRule':'First maximum in the displayed channel order.',
            'perChannelSpearman':{name:correlation(table[:,i],fitted[:,i]) for i,name in enumerate(CHANNELS)}}


def one_roster(stage, folder, inputs, output, receipt, check):
    info, ids, cohorts, matrices = common_rows(folder,stage)
    frame, all_needs, all_vectors, all_profile = inputs
    index = pd.Index(frame.text_id).get_indexer(ids)
    if (index < 0).any():
        raise ValueError('A comparison report is absent from the original cohort')
    frame, needs, direct = frame.iloc[index], all_needs[index], all_vectors[index]
    y, writers = frame.emotion.to_numpy(str), frame.prolific_id.to_numpy()
    loss = np.isin(y, LOSS)
    directory = output/stage
    directory.mkdir()
    def save():
        save_json(output/'receipt.json',receipt)
    def phase(name):
        check()
        save_json(output/'phase.json', {'cohort':stage,'phase':name})
    result = {'attempted':info['reports'],'coverage':info['coverage'],'byCohort':info['byCohort'],
              'commonReports':len(ids),'writers':int(frame.prolific_id.nunique()),
              'features':info['features'],'featureReaders':info['featureReaders'],'rows':{}}
    receipt['cohorts'][stage] = result
    save()
    original = cohorts != 'Q2'
    result['originalTP10Overlap'] = {'n':int(original.sum()),
        'BVersusTrainedSpearman':{f:correlation(matrices['prompted'][original,i],matrices['trained'][original,i])
                                  for i,f in enumerate(FEATURES)}}
    save()
    def fit(name, matrix):
        phase(name)
        row, probabilities, classes, choices = evaluate_with_choices(matrix,y,writers,check)
        np.savez_compressed(directory/(name+'.npz'),ids=ids,classes=np.asarray(classes),probabilities=probabilities,
                            lossIds=ids[loss],lossForecast=choices)
        result['rows'][name] = row
        save()
        return choices

    fit('direct', direct)
    slots = np.column_stack((matrices['mixed'],needs))
    mixed_choices = fit('mixed-slots',slots)
    for name in matrices:
        values = np.column_stack((matrices[name],needs))
        if name != 'mixed':
            fit(name+'-slots',values)
        fit(name+'-both',np.column_stack((direct,values)))
    direct_score = result['rows']['direct']['five_way']['accuracy']
    mixed_score = result['rows']['mixed-slots']['five_way']['accuracy']
    result['slotBar'] = {'thresholdBelowDirect':.10,'difference':mixed_score-direct_score,
                         'qualified':mixed_score>=direct_score-.10}
    phase('tense')
    times = np.array([tense(t) for t in frame.hidden_emo_text.fillna('')])
    when = np.column_stack((times=='ahead',times=='already')).astype(float)
    pair = np.isin(y,['fear','sadness'])
    target = y[pair]=='fear'
    raw_auc = float(roc_auc_score(target,(when[:,0]+.5*(times=='any'))[pair]))
    _, combined, labels = forecasts(np.column_stack((needs,when))[pair],y[pair],writers[pair],check)
    result['tense'] = {'auc':raw_auc,'bar':.60,'qualified':raw_auc>=.60,'n':int(pair.sum()),
                       'needsPlusTenseAuc':float(roc_auc_score(target,combined[:,labels.index('fear')]))}
    save()
    phase('fixed-table')
    included = raw_auc>=.60
    scores = table_profile(slots,when,y,writers,included,check)
    table_choice = np.asarray(LOSS)[scores.argmax(axis=1)]
    fitted = mixed_choices
    if included:
        fitted, _, _ = forecasts(np.column_stack((slots,when))[loss],y[loss],writers[loss],check)
    loss_choices = table_choice[loss]
    accuracy = float((loss_choices==y[loss]).mean())
    fit_only = (fitted==y[loss]) & (loss_choices!=y[loss])
    result['table'] = {'accuracy':accuracy,'bar':.33,'qualified':accuracy>=.33,'labels':list(LOSS),
        'n':int(loss.sum()),'chance':.20,'tenseIncluded':included,
        'fixedConfusion':confusion_matrix(y[loss],loss_choices,labels=list(LOSS)).tolist(),
        'sameSlotsFittedConfusion':confusion_matrix(y[loss],fitted,labels=list(LOSS)).tolist(),
        'fittedRightTableWrong':confusion_matrix(y[loss][fit_only],loss_choices[fit_only],
                                                 labels=list(LOSS)).tolist()}
    result['profileComparison'] = profile_comparison(scores,all_profile[index])
    np.savez_compressed(directory/'table.npz',ids=ids,writers=writers.astype(str),truth=y,tableScores=scores,
                        lossIds=ids[loss],sameSlotsFitted=fitted,tense=times)
    matrix = np.column_stack((slots,when))
    np.savez(directory/'table-scale.npz',mean=matrix.mean(axis=0),scale=matrix.std(axis=0)+1e-9,when=included)
    save()
    if not result['slotBar']['qualified']:
        result['ablations'] = {}
        for name,columns in [(f,[i]) for i,f in enumerate(FEATURES)]+[('need-tags',list(range(8,27)))]:
            phase('ablate-'+name)
            chosen, _, _ = forecasts(np.delete(slots[loss],columns,axis=1),y[loss],writers[loss],check)
            np.savez_compressed(directory/('ablate-'+name+'.npz'),ids=ids[loss],forecast=chosen)
            result['ablations'][name] = float((chosen==y[loss]).mean())
            save()


def run(corpus, initial, extended, c0, needs, profile, output, check, ledger, protocol):
    output = Path(output)
    receipt = {'card':'TP24-mixed','status':'running','productionAdmission':False,'scope':LIMIT,'ledger':ledger,
               'protocolPin':sha256(protocol),'sources':{'C0':C0,'needs':NEEDS,'TP30':PROFILE,'rosters':ROSTERS},
               'cohorts':{},'chat':'Separate morning prefix, pending.'}
    save_json(output/'receipt.json',receipt)
    inputs = sources(corpus,c0,needs,profile,check)
    for name,folder in [('initial',initial),('extended',extended)]:
        one_roster(name,folder,inputs,output,receipt,check)
    receipt['artifactsPin'] = seal(output,[output/stage for stage in ROSTERS],check)
    receipt['status'] = 'complete'
    save_json(output/'receipt.json',receipt)
