"""Registered within-file writer study using only saved, locally verified forecasts."""
from pathlib import Path

import numpy as np

from ...packs.trigger import FEATURES, TAGS
from ..back_half.reporting import save_json
from . import person_halves as halves
from .affect_data import ed_situations
from .person_repairs import FROZEN, WORRY
from .tp24_chat import EXTENSION, TP28, prefix
from .tp34 import NAMES
from .tp36 import NAMES as NEEDS
from .tp36 import tag_weights, verify_order
from .word_panels import pinned, read, sha256

SUPPORT = 'd58a7956fbe8979aff4ffe8c93bf894a1bd8ab677dc29d124a23427bc0b38261'
PACKET = 'f3ab0fa788be37f6cb17ac8dd3434b3d6832b0ca4be5c4f3d010dfee722ecf28'


def saved(folder, item, receipt):
    files = pinned(folder/'artifact-manifest.json', receipt['artifactsPin'])['files']
    if sha256(folder/item) != files[item]:
        raise ValueError('Changed saved forecasts: ' + item)
    return folder/item


def q6_features(frame, base, check):
    extension = pinned(base/'remaining-extension-a/extension.json', EXTENSION)
    items = pinned(base/'remaining-extension-a/inputs/Q6.json', extension['files']['inputs/Q6.json'])
    audit = read(base/'Q6-transfer-a.json')
    if audit['status'] != 'complete' or audit['terminal'] != 'complete.json':
        raise ValueError('Full Q6 must finish and release before TP39')
    ix = frame.set_index('id').index.get_indexer([r['id'] for r in items])
    if sorted(ix.tolist()) != list(range(len(frame))) or any(
        row['text'] != frame.text.iat[i] for row, i in zip(items, ix, strict=True)
    ):
        raise ValueError('Q6 requires exactly the original text for every ED row')
    # Terminal verification has its own contract; TP24's owner-turn time pertains only to its prefix.
    boundary = {'terminalStudy': 'TP39', 'owner': audit['owner'], 'durableRows': len(frame)}
    q, receipt_pin, count = prefix(base, boundary, items, check, full_terminal=True)
    if count != len(frame):
        raise ValueError('Incomplete Q6 roster')
    return q[np.argsort(ix)], receipt_pin


def run(ed, output, check, ledger, protocol):
    if sha256(protocol) != PACKET:
        raise ValueError('Use the registered person study packet')
    base = Path('.local')
    folder = base/'person-teacher'
    support = pinned(folder/'tp39-support.json', SUPPORT)
    if sha256(folder/'private-parents.json') != support['parentsPin']:
        raise ValueError('Parent join differs from support filing')
    df, source = ed_situations(ed)
    writers, words, ids = [df[k].to_numpy(str) for k in ('writer','label','id')]
    eligible, owner, half = halves.split(writers, ids)
    if (len(eligible), sum(owner >= 0), len(df)) != (
            support['eligibleWriters'], support['eligibleTexts'], support['sourceTexts']):
        raise ValueError('Pre-outcome support changed')
    labels, style = halves.style_features(df.text)
    frozen = base/'nine-channel/tp30-frozen-a'
    old = pinned(frozen/'receipt.json', FROZEN)
    if old['sources']['ed'] != source:
        raise ValueError('Original channel source changed')
    with np.load(saved(frozen,'ed-profile-forecasts.npz',old),allow_pickle=False) as a:
        if not np.array_equal(ids, a['ids']):
            raise ValueError('Channel row order changed')
        channel = a['probabilities'].astype(float)
    tag_folder = base/'nine-channel/tp28-a'
    tag_receipt = pinned(tag_folder/'receipt.json', TP28)
    if tag_receipt['sources']['ed']['identity'] != source or tag_receipt['protocol']['tags'] != list(TAGS):
        raise ValueError('Original tag source changed')
    tags_path = saved(tag_folder,'ed/scores.npz',tag_receipt)
    verify_order(tags_path,ids)
    with np.load(tags_path,allow_pickle=False) as a:
        tags = a['scores'].astype(float)
    if tags.shape != (len(df),len(TAGS)) or channel.shape != (len(df),len(NAMES)) or not (
        np.isfinite(channel).all() and np.isfinite(tags).all() and (tags.std(axis=0)>0).all()
    ):
        raise ValueError('Incomplete frozen input')
    features, q6 = q6_features(df,base/'word-table',check)
    active = np.ptp(channel,axis=0)>0
    names, columns, sets = [], [], {}
    for block, fields, matrix in [('style',labels,style),('channels',np.asarray(NAMES)[active],channel[:,active]),
                                   ('tags',TAGS,tags),('features',FEATURES,features)]:
        sets[block] = list(range(len(names),len(names)+len(fields)))
        names.extend(block+'/'+str(k) for k in fields)
        columns.append(matrix)
    needs = ((tags-tags.mean(axis=0))/tags.std(axis=0)) @ tag_weights()
    columns.append(needs)
    names.extend('need/'+k for k in NEEDS)
    original = pinned(base/'word-table/tp33-a/receipt.json',WORRY)
    worry = base/'trigger/tp26-a/ed-known-group.npz'
    if sha256(worry) != original['knownGroups']['ed']['forecastPin']:
        raise ValueError('Original worry forecasts changed')
    positive = np.isin(words,['anxious','afraid','apprehensive','terrified'])
    known = positive | np.isin(words,['content','joyful','grateful'])
    scores = np.full(len(df),np.nan)
    with np.load(worry, allow_pickle=False) as a:
        if not np.array_equal(a['truth'],positive[known]) or not np.isfinite(a['scores']).all():
            raise ValueError('Saved worry subgroup differs')
        scores[known] = a['scores']
    columns.append(scores[:,None])
    names.append('worry')
    check()
    profiles = halves.half_departures(np.column_stack(columns),words,writers,owner,half)
    weights = halves.resamples(len(eligible))
    readings, stability = halves.stability(profiles,names,sets,weights,check)
    matches, gain = halves.match(profiles,sets,weights,check)
    stable = stability['tags']['value'] >= .15 and stability['tags']['interval'][0] > 0
    added = gain['interval'][0] > 0
    verdict = ('Tag readings repeat and add to style.' if stable and added else
               'Tag readings repeat. The paired test did not establish extra identification beyond style.' if stable else
               'Tag readings did not clear the registered stability rule.')
    table = ['| Reading set | Mean split-half correlation (95% interval) |','|---|---:|']
    def format_cell(row):
        return 'Unavailable' if row['interval'] is None else (
            f"{row['value']:.4f} [{row['interval'][0]:.4f}, {row['interval'][1]:.4f}]")
    table += [f"| {k} | {format_cell(v)} |" for k,v in stability.items()]
    table += ['', '| Set | Likelihood first | Likelihood first ten | Distance first | Distance first ten |','|---|---:|---:|---:|---:|']
    for k,v in matches.items():
        table.append('| '+k+' | '+' | '.join(format_cell(v[m][i]) for m in ['likelihood','squaredDistance'] for i in ['1','10'])+' |')
    table += ['', 'First-ten gain adding tags to style: '+format_cell(gain)+'.',
              f"Chance within each 168-writer fold: first {1/168:.4f}, first ten {10/168:.4f}.",
              '', '| Single reading | Paired writers | Split-half correlation (95% interval) |','|---|---:|---:|']
    table += [f"| {k} | {v['pairedWriters']} | {format_cell(v)} |" for k,v in readings.items()]
    estimate = {'readings':readings,'sets':stability,'matching':matches,'tagGain':gain,
                'stable':bool(stable),'additive':bool(added),'smallGain':0 <= gain['value'] < .03,
                'zeroSpreadChannels':np.asarray(NAMES)[~active].tolist(),'worrySourceTexts':int(sum(known)),
                'Q6MissingTexts':int(sum(~np.isfinite(features).all(axis=1))),
                'eligibleWriters':len(eligible),'eligibleTexts':int(sum(owner>=0)),
                'chance':{'first':1/168,'firstTen':10/168}}
    save_json(output/'receipt.json',{'card':'TP39','status':'complete','ledger':ledger,'productionAdmission':False,
        'protocolPin':PACKET,'sources':{'support':SUPPORT,'frozen':FROZEN,'tags':TP28,'Q6':q6,'worry':sha256(worry)},
        'question':'Does the same writer leave a recognizable pattern after allowing for her assigned word?',
        'data':'We split 23,828 short situations from 336 writers in half and tried to match each writer with her other half among 168 candidates.',
        'estimate':estimate,'interval':{'draws':2000,'unit':'writer','paired':True},
        'scope':'Within-file matching of short assigned situations. Circumstances or a common writing session may explain repetition. Worry covers only seven words.',
        'bar':'Mean tag correlation ≥.15 with its interval above zero. Paired first-ten gain above zero throughout its interval.',
        'verdict':verdict,'table':table})


def change_addendum(ed, teacher, output, check, ledger, protocol):
    from .checkpoint import completed
    if sha256(protocol) != PACKET or teacher is None:
        raise ValueError('Registered protocol and completed TP40 required')
    public = read(Path('engine/validation/readers-change-by-word-2026-11.json'))
    result = completed(teacher, 'TP40')
    source = sha256(teacher/'receipt.json')
    shares_path = teacher/'ed-change-shares.npz'
    if source != public['sourceReceiptPin'] or sha256(shares_path) != result['sources']['privateChangeScoresPin']:
        raise ValueError('Change figures differ from landed TP40')
    frame, identity = ed_situations(ed)
    pinned(Path('.local/person-teacher/tp39-support.json'), SUPPORT)
    manifest = pinned(Path('.local/person-teacher/inputs/manifest.json'), result['sources']['manifest'])
    if identity['intakePin'] != manifest['sourcePins']['ed']:
        raise ValueError('Original chat source differs')
    ids, writers, words = [frame[k].to_numpy(str) for k in ('id','writer','label')]
    with np.load(shares_path, allow_pickle=False) as a:
        ix = frame.set_index('id').index.get_indexer(a['ids'])
        if sorted(ix.tolist()) != list(range(len(ids))) or a['shares'].shape != (len(ids),3):
            raise ValueError('Held text order or dimensions differ')
        values = a['shares'][np.argsort(ix)]
    eligible, owner, half = halves.split(writers,ids)
    profiles = halves.half_departures(values,words,writers,owner,half)
    names = ['change','writersOwnChange','changeAhead']
    rows,_ = halves.stability(profiles,names,{},halves.resamples(len(eligible)),check)
    table = ['| Share of sentences | Paired writers | Correlation (95% interval) |','|---|---:|---:|']
    for k,r in rows.items():
        cell = 'Unavailable' if r['interval'] is None else f"{r['value']:.4f} [{r['interval'][0]:.4f}, {r['interval'][1]:.4f}]"
        table.append(f"| {k} | {r['pairedWriters']} | {cell} |")
    save_json(output/'receipt.json',{'card':'TP39-change','status':'complete','ledger':ledger,'productionAdmission':False,
        'protocolPin':PACKET,'sources':{'support':SUPPORT,'TP40':source,'shares':sha256(shares_path)},
        'question':'Did the same writer repeatedly describe change in similar ways?',
        'data':'We compared each writer’s two halves after subtracting the average for the same assigned word among other writers.',
        'estimate':{'readings':rows,'missingTexts':int(sum(~np.isfinite(values).all(axis=1)))},
        'interval':{'draws':2000,'unit':'writer'},'scope':'One reader’s sentence classifications on a single source.',
        'bar':'Descriptive single readings, outside the matching sets.','verdict':'Three split-half estimates filed.',
        'table':table})
