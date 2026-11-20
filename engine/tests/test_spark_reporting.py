import json

import pytest

from tompathy_engine.eval.readers.spark_reporting import land
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
