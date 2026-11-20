"""Aggregate-only local landing, bound to a verified terminal source job."""
import hashlib
import json
from pathlib import Path

from ...packs.registry import sha256
from ..back_half.reporting import save_json

OUTPUTS = {'TP7':'readers-choice-ex5-2026-11.json', 'TP26':'readers-worry-transfer-2026-11.json', 'TP10': 'readers-envent-2026-11.json', 'TP12': 'readers-counting-2026-11.json',
           'TP12-L3':'readers-counting-finetuned-2026-11.json',
           'TP10-L3':'readers-envent-finetuned-2026-11.json','TP11':'readers-stakes-2026-11.json',
           'TP14':'readers-motives-2026-11.json','TP13':'readers-transfer-2026-11.json',
           'TP15':'readers-care-2026-11.json','TP16':'readers-worry-2026-11.json',
           'TP18':'readers-attention-features-2026-11.json','TP20':'readers-priorities-2026-11.json',
           'TP17':'readers-cause-words-2026-11.json',
           'TP4-controls':'readers-goal-controls-2026-11.json',
           'TP18-probe':'readers-attention-probe-2026-11.json','TP1c':'readers-smol135-2026-11.json',
           'TP19':'readers-choices-2026-11.json','TP22':'readers-longitudinal-2026-11.json'}
FIELDS = {
    'TP7':{'card','status','productionAdmission','ledger','scope','sourcePin','protocol','rows','acceptedNotTopScore','sourceSelection','E2','license','reason'},
    'TP26':{'card','status','productionAdmission','ledger','scope','source','benchmarkSourcePin','protocol','groups','training','nothing_here','transferPassed','pack'},
    'TP18-probe':{'card','status','productionAdmission','ledger','scope','sourceReceiptPin','tablesPin','reader','protocol','sessions','words','pack','row','controls'},
    'TP1c':{'card','status','productionAdmission','ledger','scope','sourceModelPin','converter','textPin','pack','protocol','ggufPin','gates','attention','candidate','criteria','q4Pin','q4','aggregatePin'},
    'TP19':{'card','status','productionAdmission','ledger','scope','reader','motives','sourcePin','protocol','rows','gains','pack','controls','continuation'},
    'TP22':{'card','status','productionAdmission','ledger','scope','source','readerReceiptPin','countingReceiptPin','policy','constructed_qualification','pack','protocol','reason','cohort','topic_encoder','reader','supported','withheld','raw','controlled','controls','bars_passed'},
    'TP4-controls':{'card','status','productionAdmission','ledger','scope','inputPin','baselinePin','protocol','rows','baselineReproduced'},
    'TP10':{'card','status','scope','harness','rows','productionAdmission','neutralInputs',
            'continuation','selected_for_L3','selection_basis'},
    'TP12':{'card','status','preflight','ladderReceiptPin','authorFilePin','scope','seed','halves',
            'bagsPerScenarioPerHalf','labels','rows','policies','productionAdmission','estimand',
            'design','unpacked','neutralStress','bars'},
    'TP10-L3':{'card','status','scope','ladderReceiptPin','encoder','hyperparameters','rows',
               'productionAdmission','pack','selected_seed','mean_accuracy','mean_macro_f1'},
    'TP11':{'card','status','scope','twins','left_out','mapping','encoderScope','encoders',
            'productionAdmission','ledger','twins_gates','preflight_comparison','interpretation','pack'},
    'TP14':{'card','status','scope','rows','mapping','twinsControlReceiptPin','threshold',
            'productionAdmission','ledger','human_reference','pack','agreement','instruments','IM1'},
    'TP13':{'card','status','scope','productionAdmission','ledger','reader','data','rows','cross',
            'feature_transfer','mapping','protocol','pack'},
    'TP15':{'card','status','productionAdmission','ledger','scope','source','n','writers','rows','protocol',
            'external_references','encoders','fine_tuned_folds','second_check','continuation'},
    'TP16':{'card','status','productionAdmission','ledger','scope','source','n','writers','rows','protocol',
            'external_references','encoders','fine_tuned_folds','long_text_channels','plans','continuation'},
    'TP18':{'card','status','productionAdmission','ledger','scope','sources','protocol','rows','probe'},
    'TP20':{'card','status','productionAdmission','ledger','scope','source','reader','protocol',
            'excluded_short_perspectives','rows','external_references','chance'},
    'TP17':{'card','status','productionAdmission','ledger','scope','source','ed','reader','headPin',
            'protocol','references','total','completed','excluded_alignment','rows'},
}
FIELDS['TP12-L3']=FIELDS['TP12']|{'carriedControls'}
FIELDS['TP12-gated']=FIELDS['TP12-L3']|{'gate','gatedErrorTablePin'}
OUTPUTS['TP12-gated']='readers-counting-gated-2026-11.json'
FIELDS['TP22-gated']=FIELDS['TP22']|{'gate'}
OUTPUTS['TP22-gated']='readers-longitudinal-gated-2026-11.json'
FIELDS['TP25']={'card','status','productionAdmission','ledger','scope','sources','protocol','rows','pack','encoder',
    'neutral_source','final_threshold','final_validation_qualified','final_development_curves','neutral','qualifies','artifactsPin'}
OUTPUTS['TP25']='readers-stakes-gate-2026-11.json'
FIELDS['TP24']={'card','status','productionAdmission','ledger','scope','needsReceiptPin','rows','pack','protocol',
    'reason','reader','stakes_qualified','tense','table','ablations','rulesPin','artifactsPin','featureReuse'}
OUTPUTS['TP24']='readers-trigger-slots-2026-11.json'
FIELDS['TP27']={'card','status','productionAdmission','ledger','scope','sourceReceiptPin','tablesPin','protocol','row',
    'reader','residual','versus_combined','artifactsPin','baselineForecastPin'}
OUTPUTS['TP27']='readers-pause-remainder-diagnostic-2026-11.json'
FIELDS['TP28']={'card','status','productionAdmission','ledger','scope','reader','protocol','sources',
               'rows','filled','newChannelRowsFilled','tablePassed','artifactsPin'}
OUTPUTS['TP28']='readers-stand-in-table-2026-11.json'
FIELDS['TP29']={'card','status','productionAdmission','ledger','scope','protocolPin','protocol',
               'sources','vectors','rows','verdict','artifactsPin'}
OUTPUTS['TP29']='readers-embarrassment-shame-2026-11.json'
FIELDS['TP30-frozen']={'card','status','productionAdmission','ledger','scope','protocolPin','protocol',
                     'sources','vectors','vectorSourceReceiptPin','map','intake','rows','artifactsPin'}
OUTPUTS['TP30-frozen']='readers-profile-frozen-2026-11.json'
OUTPUTS['TP34']='readers-word-recipes-2026-11.json'
OUTPUTS['TP35']='readers-suddenness-2026-11.json'
OUTPUTS['TP38']='readers-food-topic-2026-11.json'
FIELDS['TP38']={'card','status','productionAdmission','ledger','scope','protocolPin','readerReceiptPin',
                'tp28ReceiptPin','writerDraws','sampled','valid','controlsPopulation','shares','contrasts',
                'originalLifts','kindsByWord','kinds','wordList','bothFellByMoreThanHalf'}
OUTPUTS['RD1']='readers-feature-slots-2026-11.json'
OUTPUTS['RD2']='readers-standards-panel-2026-11.json'
_PANEL_FIELDS={'card','status','productionAdmission','ledger','protocolPin','readerJobPin',
               'companionPin','trainedReceiptPin','scope','rows','human'}
FIELDS['RD1']=_PANEL_FIELDS|{'slots'}
FIELDS['RD2']=_PANEL_FIELDS|{'differenceFlags','developmentWinners','trainedArms','researchReaderC',
                            'overlapAuditPin','primaryReports','textFreshReports','f3Status','developmentSelectionPin'}
OUTPUTS['TP36']='readers-need-pairs-2026-11.json'
FIELDS['TP36']={'card','status','productionAdmission','ledger','scope','sourceReceiptPinTP28','protocolPin',
                'sources','writerDraws','tagMapVersion','distinctInEverySource','belongingCompassionHighestSources',
                'mergePredictionPasses'}
FIELDS['TP35']={'card','status','productionAdmission','ledger','sourcePin','protocolPin','scope',
                'columns','rows','groups','void','bars','writerDraws','releasedReports','writers'}
FIELDS['TP34']={'card','status','scope','productionAdmission','ledger','sourceReceiptPinFrozen','protocolPin',
                'sources','channels','rows','writerDraws','writers','floor','baseline','quietRanking',
                'blindTopTwo','blindTopThree','disappointedSeeking'}
FIELDS['TS3-real']={'card','status','productionAdmission','ledger','scope','sources','packs','rows','defaultOffParity','browser','artifactsPin'}
OUTPUTS['TS3-real']='readers-trigger-wire-2026-11.json'
for rung in ('bow','frozen','fine-23','fine-47','fine-71','base'):
    card='TP23-'+rung
    OUTPUTS[card]='readers-need-'+rung+'-2026-11.json'
    FIELDS[card]={'card','status','productionAdmission','ledger','source','scope','protocol','people','folds','pack',
        'encoder','story','transfer','qualifies','preflight','foldSources','artifactsPin','preflightSourcePin','preflightScope'}
for kind in ('worry','need','gate','label','trigger','counting'):
    card='TRIGGER-export-'+kind
    OUTPUTS[card]='readers-export-'+kind+'-2026-11.json'
    FIELDS[card]={'card','status','productionAdmission','ledger','scope','pack','reason','selection','IM2ManifestPin'}


def land(job, destination, *, tp29_ruling=None):
    job, destination = Path(job), Path(destination)
    verified = json.loads((job/'exit-verification.json').read_text(encoding='utf8'))
    if not all(verified.get(k) for k in ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent')):
        raise ValueError('Native exit and exact releases must be verified')
    if not (job/'complete.json').exists() and not (job/'failed.json').exists():
        raise ValueError('Terminal job receipt required')
    source = job/'receipt.json'
    value = json.loads(source.read_text(encoding='utf8'))
    card = value['card']
    if destination.name != OUTPUTS.get(card):
        raise ValueError('Wrong registered aggregate filename')
    # Private per-text observations live in separate arrays, never these receipts.
    allowed = FIELDS[card]
    if set(value) - allowed or value.get('productionAdmission') is not False:
        raise ValueError('Unexpected aggregate fields/admission')
    plan = json.loads((job/'plan.json').read_text(encoding='utf8'))
    public = {'schema': 'readers-aggregate-1',
        'snapshotPin': hashlib.sha256(json.dumps(plan['snapshotFiles'],sort_keys=True).encode()).hexdigest(),
        'launcherPin': plan['launcherSha256'], 'ledger': 'no ledger row', **value}
    # A dependent source receipt can already cite its upstream experiment.
    # Keep that citation separate from this aggregate's own source binding.
    if 'sourceReceiptPin' in value:
        public['upstreamSourceReceiptPin'] = value['sourceReceiptPin']
    public['sourceReceiptPin'] = sha256(source)
    if card == 'TP29':
        if tp29_ruling is None:
            raise ValueError('TP29 requires the source-bound owner verdict ruling')
        ruling = json.loads(Path(tp29_ruling).read_text(encoding='utf8'))
        ruling_text = Path(__file__).resolve().parents[4]/'docs/TP29_OWNER_RULING_2026-11-19.md'
        if (ruling.get('schema') != 'TP29-owner-verdict-1'
                or ruling.get('originalProtocolPin') != value['protocolPin']
                or ruling.get('rulingPin') != sha256(ruling_text)
                or ruling.get('rule') != 'A=read1+read2+read3; B=appeasement-only; read4=reported-only'):
            raise ValueError('TP29 owner ruling binding differs')
        public['verdictAmendment'] = {key: ruling[key] for key in
            ('schema','receivedAt','originalProtocolPin','rulingPin','rule')}
        public['verdictAmendment']['receiptPin'] = sha256(tp29_ruling)
        public['originalRunnerVerdict'] = public.get('verdict')
        rows = value.get('rows', {})
        if all(key in rows for key in ('ed', 'coefficients', 'go')):
            from .tp29 import conclusions
            public['verdict'] = conclusions(rows['ed'], rows['coefficients'], rows['go'])
        else:
            public['verdict'] = None
    elif tp29_ruling is not None:
        raise ValueError('TP29 ruling cannot modify another card')
    if value['status']=='running':
        public.update(status='partial',sourceStatus='running',
                      terminalOutcome='failed' if (job/'failed.json').exists() else 'incomplete-source')
    if destination.exists():
        old = json.loads(destination.read_text(encoding='utf8'))
        if old == public:
            return {'status':'unchanged', 'sourceReceiptPin': public['sourceReceiptPin']}
        raise ValueError('Preserve the previous public result; use a separately identified stage')
    save_json(destination, public)
    if json.loads(destination.read_text(encoding='utf8')) != public:
        raise RuntimeError('Public binding verification failed')
    return {'status':'landed', 'sourceReceiptPin': public['sourceReceiptPin'], 'publicPin': sha256(destination)}
