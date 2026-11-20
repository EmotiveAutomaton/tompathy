"""Aggregate-only SP1 landing after native exit and private artifact verification."""
import json
from pathlib import Path

from ...packs.registry import sha256


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
    if row['kind'] == 'parity' and role is None:
        card, filename = 'SP1-parity', 'readers-spark-parity-2026-11.json'
        allowed = {'kind','n','pilot','maximumProbabilityDifferences','passes','numberFormat','pack'}
        public_row = {k: row[k] for k in allowed}
        public_row['encoder'] = {k: row['encoder'][k] for k in ('id','revision')}
    elif row['kind'] in ('reader-pilot','reader-repeat') and role in ('a','b'):
        stage='panel' if row['kind']=='reader-repeat' else 'pilot'
        card, filename = f'SP1-reader-{role}-{stage}', f'readers-spark-reader-{role}-{stage}-2026-11.json'
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
    value = {'schema':'SP1-aggregate-1','card':card,'status':'complete','productionAdmission':False,
             'sourceReceiptPin':pin,'sourceArtifactManifestPin':receipt['artifactsPin'],
             'sourceCommit':owner['commit'],'scriptPin':owner['scriptPin'],
             'payloadPin':receipt['payloadPin'],'versions':receipt['versions'],
             'protocol':{k:receipt['protocol'][k] for k in protocol_keys},'row':public_row,
             'scope':'Open Crowd-enVENT held-out reports. Numerical parity or timing only; no teacher, serving or maker admission.'}
    if row['kind']=='reader-repeat':
        value['scope']='Fixed open Crowd-enVENT report-held-out repeated panel. Writer ratings are the comparison key; this panel alone establishes no downstream teacher, serving or maker admission.'
    data = (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError('Preserve existing aggregate; use an explicit correction')
    destination.write_bytes(data)
    return {'card':card,'sourceReceiptPin':pin,'publicPin':sha256(destination),
            'artifactsVerified':len(manifest['files'])}
