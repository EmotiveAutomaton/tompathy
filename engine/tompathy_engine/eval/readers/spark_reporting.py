"""Aggregate-only SP1 landing after native exit and private artifact verification."""
import json
from pathlib import Path

from ...packs.registry import sha256

INTERRUPTED_PANEL_OUTPUT = 'readers-spark-reader-a-panel-audit-2026-11.json'


def land_interrupted_audit(job, exit_audit, preservation, summary, destination):
    """File a verified saved-response audit without converting failure to completion."""
    job,destination=Path(job),Path(destination)
    value=json.loads((job/'receipt.json').read_text())
    audit=json.loads(Path(exit_audit).read_text())
    retained=json.loads(Path(preservation).read_text())
    release=json.loads((job/'released.json').read_text())
    pin=sha256(job/'receipt.json')
    if (destination.name!=INTERRUPTED_PANEL_OUTPUT or value['status']!='stopped' or
            value.get('reason')!="No module named 'scipy'" or
            audit.get('sameNativeAlive') is not False or not audit.get('gpuLockFree') or
            audit.get('receiptPin')!=pin or audit.get('owner')!=value['owner'] or
            release.get('owner')!=value['owner'] or not release.get('lockReleased') or
            retained['sourceReceiptPin']!=pin):
        raise ValueError('Exact interrupted source, exit, release and preservation required')
    for name,expected in retained['files'].items():
        path=(job/name).resolve()
        if not path.is_relative_to(job.resolve()) or sha256(path)!=expected:
            raise ValueError('Preserved source changed')
    fields={'n','validFirstPass','validSecondPass','featureSpearman','baselineSpearmanSameRows',
            'meanSpearman','baselineMeanSameRows','identicalPairs','repeatability','structuredValidity',
            'correlationPass','repeatabilityPass','validityPass'}
    if set(summary)!=fields:
        raise ValueError('Only aggregate panel fields are publishable')
    public={'card':'SP1-v1-reader-a-panel-audit','status':'stopped','postRunAudit':True,
            'productionAdmission':False,'readerQualified':False,'sourceReceiptPin':pin,
            'sourcePreservationPin':sha256(preservation),'sourceCommit':value['owner']['commit'],
            'sourceScriptPin':value['owner']['scriptPin'],'payloadPin':value['payloadPin'],
            'protocol':value['protocol'],'row':summary,
            'scope':'Original prompt reversed norms/standards and loosely defined goal support. Raw comparison is not a valid test of correctly specified reader quality. Original runtime stopped after all responses; no runtime continuation completed before its deadline. No score flips, new inference or admission.'}
    data=(json.dumps(public,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if destination.exists() and destination.read_bytes()!=data:
        raise ValueError('Preserve previous audit')
    destination.write_bytes(data)
    return {'card':public['card'],'sourceReceiptPin':pin,'publicPin':sha256(destination),'status':'stopped'}


def land(job, exit_audit, destination, *, role=None):
    job, destination = Path(job), Path(destination)
    audit = json.loads(Path(exit_audit).read_text())
    receipt = json.loads((job/'receipt.json').read_text())
    pin = sha256(job/'receipt.json')
    released = json.loads((job/'released.json').read_text())
    owner = receipt['owner']
    if (audit.get('sameNativeAlive') is not False or not audit.get('gpuLockFree') or
            audit.get('receiptPin') != pin or audit.get('owner') != owner or
            released.get('owner') != owner or not released.get('lockReleased')):
        raise ValueError('Exact remote exit, source pin and matching release required')
    if receipt['status'] != 'complete' or json.loads((job/'complete.json').read_text())['receiptPin'] != pin:
        raise ValueError('Completed stage required; stopped partial work stays private')
    manifest = json.loads((job/'artifacts.json').read_text())
    if sha256(job/'artifacts.json') != receipt['artifactsPin']:
        raise ValueError('Artifact manifest changed')
    for name, expected in manifest['files'].items():
        path = (job/name).resolve()
        if not path.is_relative_to(job.resolve()) or sha256(path) != expected:
            raise ValueError('Artifact changed or escaped job')
    row = receipt['row']
    version=receipt['protocol'].get('version',1)
    if version not in (1,2):
        raise ValueError('Unregistered SP1 protocol version')
    if row['kind'] == 'parity' and role is None:
        card, filename = 'SP1-parity', 'readers-spark-parity-2026-11.json'
        allowed = {'kind','n','pilot','maximumProbabilityDifferences','passes','numberFormat','pack'}
        public_row = {k: row[k] for k in allowed}
        public_row['encoder'] = {k: row['encoder'][k] for k in ('id','revision')}
    elif row['kind']=='model-pull' and role=='b' and version==2:
        card,filename='SP1-v2-reader-b-setup','readers-spark-v2-reader-b-setup-2026-11.json'
        required={'model.json','models-before.json','models-after.json','pull-result.json'}
        if not required <= set(manifest['files']):
            raise ValueError('Complete pinned model setup artifacts required')
        model=json.loads((job/'model.json').read_text())
        before=json.loads((job/'models-before.json').read_text())
        after=json.loads((job/'models-after.json').read_text())
        current={r['name']:r['digest'] for r in after}
        if (row.get('inferenceRan') is not False or row.get('residentFitVerified') is not False or
                row.get('priorModelIdsPreserved') is not True or row['model']!=model['tag'] or
                row['model']['name']!='qwen3.5:35b' or
                current.get('qwen3.5:35b')!=row['model']['digest'] or
                model['show']['model_info']['general.parameter_count']<27_000_000_000 or
                row['model']['size']>64*1024**3 or
                json.loads((job/'pull-result.json').read_text()).get('status')!='success' or
                any(current.get(r['name'])!=r['digest'] for r in before) or
                any(r['name']=='qwen3.5:35b' for r in before)):
            raise ValueError('Setup must preserve existing IDs without claiming inference or fit')
        public_row={'kind':'model-pull','model':{k:row['model'][k] for k in ('name','digest','size')},
                    'parameters':model['show']['model_info']['general.parameter_count'],
                    'quantization':model['tag']['details']['quantization_level'],
                    'priorModelIdsPreserved':True,'inferenceRan':False,'residentFitVerified':False,
                    'requires500Pilot':True}
    elif row['kind'] in ('reader-pilot','reader-repeat') and role in ('a','b'):
        stage='panel' if row['kind']=='reader-repeat' else 'pilot'
        prefix='SP1-v2' if version==2 else 'SP1'
        file_prefix='readers-spark-v2' if version==2 else 'readers-spark'
        card, filename = f'{prefix}-reader-{role}-{stage}', f'{file_prefix}-reader-{role}-{stage}-2026-11.json'
        allowed = {'kind','texts','valid','seconds','secondsPer100','includesRequestLoading','panelCompleted'}
        public_row = {k: row[k] for k in allowed}
        public_row['model'] = {k:row['model'][k] for k in ('name','digest','size')}
        if stage=='panel':
            for key in ('panel','readerQualified','pilotReceiptPin','pilotArtifactManifestPin','firstPassReused'):
                public_row[key]=row[key]
            if 'continuation' in row:
                public_row['continuation']=row['continuation']
    else:
        raise ValueError('Unregistered SP1 stage')
    if destination.name != filename:
        raise ValueError('Registered aggregate filename required')
    protocol_keys = {'context','features','numericalThreads','outputTokens','promptPin','seed',
                     'telemetryThreads','temperature','thermalStopC','thinking'}
    if row['kind']=='model-pull':
        protocol_keys={'numericalThreads','telemetryThreads','thermalStopC'}
    value = {'schema':'SP1-aggregate-1','card':card,'status':'complete','productionAdmission':False,
             'sourceReceiptPin':pin,'sourceArtifactManifestPin':receipt['artifactsPin'],
             'sourceCommit':owner['commit'],'scriptPin':owner['scriptPin'],
             'payloadPin':receipt['payloadPin'],'versions':receipt['versions'],
             'protocol':{k:receipt['protocol'][k] for k in protocol_keys},'row':public_row,
             'scope':'Open Crowd-enVENT held-out reports. Numerical parity or timing only; no teacher, serving or maker admission.'}
    if version==2:
        value['protocol']['version']=2
    if row['kind']=='reader-repeat':
        value['scope']='Fixed open Crowd-enVENT report-held-out repeated panel. Writer ratings are the comparison key; this panel alone establishes no downstream teacher, serving or maker admission.'
    elif row['kind']=='model-pull':
        value['scope']='One-time reader-B download and frozen model identity only. No inference, measured resident fit, panel qualification, teacher or serving admission.'
    data = (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError('Preserve existing aggregate; use an explicit correction')
    destination.write_bytes(data)
    return {'card':card,'sourceReceiptPin':pin,'publicPin':sha256(destination),
            'artifactsVerified':len(manifest['files'])}
