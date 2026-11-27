"""TP60. Assemble the proposed display contract entirely from public, landed aggregates."""
import json
from pathlib import Path

from cb_inputs import pin
from tompathy_engine.packs.trigger import TAGS

PUBLIC = Path('engine/validation')
PINS = {
    'tp45-openings':'629fd3ec5b8d140f7b49266e4959c574ed55a976cb249b8b6bf7d0c7bc453eca',
    'tp48':'4b1bfe051c7a51e29bcc8f95c6ac9201035416f0922b11ba095c10998b1b9a74',
    'tp50':'b2d82026e42d063dea2669bda29edcde4e33767ec218551d650910ae0a673823',
}
GROUPS = {'Competence':['curiosity'], 'Respect':['status','approval','power','competition','honor'],
          'Belonging':['family','contact','belonging'], 'Meaning':['order','savings','serenity'],
          'Compassion':['idealism'], 'Body':['food','rest','health','tranquility'],
          'Unplaced':['romance','indep']}


def prepare(out, check):
    ledger = {r['id']:r for r in map(json.loads,(PUBLIC/'EVIDENCE_LEDGER.jsonl').read_text('utf8').splitlines())}
    cards, evidence = {}, {}
    for key,expected in PINS.items():
        check()
        path = PUBLIC/f'readers-{key}-2026-11.json'
        if pin(path)!=expected:
            raise ValueError('Public aggregate differs from reviewed source')
        r = json.loads(path.read_bytes())
        if ledger[r['ledger']]['estimate']['sourceReceiptPin'] != r['sourceReceiptPin']:
            raise ValueError('Ledger binding differs')
        cards[key]=r
        evidence[key]=dict(file=path.as_posix(),sha256=expected,ledger=r['ledger'])
    if sorted(sum(GROUPS.values(),[]))!=sorted(TAGS):
        raise ValueError('Incomplete or duplicated tag grouping')
    channels=cards['tp48']['columns']
    if len(set(channels))!=10 or channels[-1]!='PRIDE':
        raise ValueError('Expected verified tenth PRIDE column')
    states=cards['tp50']
    if not states['proposed'] or len(states['states'])!=32:
        raise ValueError('Required display-state evidence missing')
    lookup={}
    for split in ('date','gap'):
        for k in (5,10,20,40):
            name=f'deep-{split}-{k}'
            cell=cards['tp45-openings']['tables'][name]
            lookup[name]={}
            for arm in ('tagsRaw','tagsPartial'):
                item=cell[arm]
                lookup[name][arm]=dict(pairedAuthors=item['authors'],postsPerSide=k,
                    tags=dict(zip(TAGS,item['correlations'],strict=True)))
    return dict(card='TP60',scope='Proposed display contract. No new reading, test or serving admission.',
        evidence=evidence,channels=channels,tagGroups=GROUPS,displayTagsSeparately=GROUPS['Belonging'],
        optionalMergedView=['Belonging','Compassion'],bodySeparate=True,unmappedNeedID=None,
        textState={'reference':'TP50 chat situations; each block takes its maximum across varying standardized outputs. High means strictly above the reference median maximum.',
                   'bothLow':'nothing at stake','needInBand':'a need in its band','bothHigh':'a need on the move',
                   'channelOnlyUnassigned':None,'basis':'Filed rates by assigned word. Application to a new text needs the frozen reference calibration.'},
        authorReliability={'source':'TP45 Table 1, deep blog cohort, correlations across authors between date halves.',
            'lookup':'Use the measured posts per side, split, and raw or partly cleared arm. A count alone does not establish eligibility. Unsupported counts have no measured entry.',
            'interval':'95% whole-author bootstrap; cohort reliability, not a confidence interval on one person.',
            'cells':lookup})
