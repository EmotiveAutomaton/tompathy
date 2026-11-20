import json

import pytest

from tompathy_engine.eval.readers.spark_reporting import land, land_interrupted_audit
from tompathy_engine.packs.registry import sha256


def fixture(root):
    def save(name,value): (root/name).write_text(json.dumps(value))
    owner = {'pid':3,'startTicks':'4','commit':'a'*40,'scriptPin':'b'*64,'host':'private-host'}
    save('artifacts.json',{'files':{}})
    save('receipt.json',{'owner':owner,'status':'complete','artifactsPin':sha256(root/'artifacts.json'),
         'payloadPin':'c'*64,'versions':{},'protocol':dict.fromkeys(('context','features','numericalThreads',
         'outputTokens','promptPin','seed','telemetryThreads','temperature','thermalStopC','thinking'),None),
         'row':{'kind':'parity','n':200,'pilot':{},'maximumProbabilityDifferences':{},'passes':True,
                'numberFormat':'float32','pack':'constructed','encoder':{'id':'fixture','revision':'d'*40},
                'privateText':'never publish this'}})
    pin=sha256(root/'receipt.json')
    save('complete.json',{'receiptPin':pin})
    save('released.json',{'owner':owner,'lockReleased':True})
    save('audit.json',{'sameNativeAlive':False,'gpuLockFree':True,'receiptPin':pin,'owner':owner})
    return root/'readers-spark-parity-2026-11.json'


def test_spark_landing_excludes_private_host_and_per_text_fields(tmp_path):
    output=fixture(tmp_path)
    land(tmp_path,tmp_path/'audit.json',output)
    assert 'private-host' not in output.read_text()
    assert 'never publish' not in output.read_text()
    assert not json.loads(output.read_text())['productionAdmission']


@pytest.mark.parametrize('field,value',[('sameNativeAlive',True),('gpuLockFree',False),('receiptPin','changed')])
def test_spark_landing_requires_exact_exit_release_and_source(tmp_path,field,value):
    output=fixture(tmp_path)
    audit=json.loads((tmp_path/'audit.json').read_text())
    audit[field]=value
    (tmp_path/'audit.json').write_text(json.dumps(audit))
    with pytest.raises(ValueError,match='Exact remote'):
        land(tmp_path,tmp_path/'audit.json',output)


def test_v2_reader_requires_separate_registered_filename(tmp_path):
    fixture(tmp_path)
    receipt=json.loads((tmp_path/'receipt.json').read_text())
    receipt['protocol']['version']=2
    receipt['row']={'kind':'reader-pilot','texts':500,'valid':500,'seconds':10,
                    'secondsPer100':2,'includesRequestLoading':True,'panelCompleted':False,
                    'model':{'name':'fixture','digest':'d'*64,'size':10}}
    (tmp_path/'receipt.json').write_text(json.dumps(receipt))
    pin=sha256(tmp_path/'receipt.json')
    audit=json.loads((tmp_path/'audit.json').read_text());audit['receiptPin']=pin
    (tmp_path/'audit.json').write_text(json.dumps(audit))
    (tmp_path/'complete.json').write_text(json.dumps({'receiptPin':pin}))
    with pytest.raises(ValueError):
        land(tmp_path,tmp_path/'audit.json',tmp_path/'readers-spark-reader-a-pilot-2026-11.json',role='a')
    output=tmp_path/'readers-spark-v2-reader-a-pilot-2026-11.json'
    land(tmp_path,tmp_path/'audit.json',output,role='a')
    assert json.loads(output.read_text())['card']=='SP1-v2-reader-a-pilot'


def test_interrupted_audit_preserves_failure_and_checks_saved_bytes(tmp_path):
    fixture(tmp_path)
    receipt=json.loads((tmp_path/'receipt.json').read_text())
    receipt.update(status='stopped',reason="No module named 'scipy'")
    (tmp_path/'receipt.json').write_text(json.dumps(receipt))
    pin=sha256(tmp_path/'receipt.json')
    audit=json.loads((tmp_path/'audit.json').read_text());audit['receiptPin']=pin
    (tmp_path/'audit.json').write_text(json.dumps(audit))
    (tmp_path/'raw.json').write_text('private saved response')
    (tmp_path/'preservation.json').write_text(json.dumps({'sourceReceiptPin':pin,
        'files':{'raw.json':sha256(tmp_path/'raw.json')}}))
    fields=('n','validFirstPass','validSecondPass','featureSpearman','baselineSpearmanSameRows',
            'meanSpearman','baselineMeanSameRows','identicalPairs','repeatability','structuredValidity',
            'correlationPass','repeatabilityPass','validityPass')
    summary=dict.fromkeys(fields,0)
    output=tmp_path/'readers-spark-reader-a-panel-audit-2026-11.json'
    land_interrupted_audit(tmp_path,tmp_path/'audit.json',tmp_path/'preservation.json',summary,output)
    public=json.loads(output.read_text())
    assert public['status']=='stopped' and not public['readerQualified']
    assert 'private saved response' not in output.read_text() and 'private-host' not in output.read_text()
    with pytest.raises(ValueError,match='Only aggregate'):
        land_interrupted_audit(tmp_path,tmp_path/'audit.json',tmp_path/'preservation.json',
                               dict(summary,text='private'),output)
    (tmp_path/'raw.json').write_text('changed')
    with pytest.raises(ValueError,match='Preserved source changed'):
        land_interrupted_audit(tmp_path,tmp_path/'audit.json',tmp_path/'preservation.json',summary,output)
