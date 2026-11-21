import hashlib
import json

import numpy as np
import pytest

from tompathy_engine.eval.readers import tp24_chat
from tompathy_engine.eval.readers.tp24_chat import assess, prefix


def test_missing_inputs_and_unrepresented_writer_channels_remain_in_denominator():
    labels = ['angry','afraid','caring','hopeful','sad','furious']
    scores = np.array([[3,0,0,0,0], [np.nan]*5, [2,1,0,0,0], [0,3,1,0,0],
                       [0,0,1,0,0], [3,0,0,0,0]])
    calls, row = assess(labels,scores)
    assert list(calls)==['RAGE','','RAGE','FEAR','SADNESS','RAGE']
    assert (row['eligibleWriterWords'],row['eligibleMissingInput'],row['correct'],row['outsideMap'])==(5,1,2,1)
    assert row['accuracyOnAllEligible']==.4
    assert row['byChannel']['CARE']['tableEmitsChannel'] is False
    assert row['byChannel']['PANIC/GRIEF']['correct']==1


def test_empty_prefix_has_no_accuracy():
    _,row = assess([],np.empty((0,5)))
    assert row['attempted']==0 and row['accuracyOnAllEligible'] is None


@pytest.mark.parametrize('stamp,trigger', [('2026-11-21T06:59:59-08:00','owner-turn'),
                                          ('2026-11-21T07:30:00-08:00','heartbeat')])
def test_only_an_eligible_owner_review_can_read_the_terminal(tmp_path,stamp,trigger):
    with pytest.raises(ValueError,match='first eligible owner'):
        prefix(tmp_path,{'ownerTurnAt':stamp,'trigger':trigger},[],lambda:None)


def test_verified_prefix_joins_raw_answers_and_excludes_rows_after_capture(tmp_path,monkeypatch):
    def write(root,name,value):
        path = root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        data = json.dumps(value).encode()
        path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()
    entry = {'commit':'registered','manifest':'source.json','sourcePin':'source','codePins':{}}
    ext = tmp_path/'remaining-extension-a'
    monkeypatch.setattr(tp24_chat,'EXTENSION',write(ext,'extension.json',{'entries':{'Q6':entry}}))
    model = {'modelPin':'model','options':{},'role':'B','think':False,'schemaPin':'schema','promptPin':'prompt'}
    monkeypatch.setattr(tp24_chat,'REFERENCE_PROTOCOL',write(tmp_path,'verified-spark-Q1-a/B/protocol.json',model))
    items = [{'id':str(i)} for i in range(3)]
    binding = {**entry,**model,'job':'Q6','inputPin':write(ext,'inputs/Q6.json',items)}
    mirror = tmp_path/'verified-spark-Q6-a'
    owner = {'job':'Q6'}
    files = {}
    for i in range(3):
        raw = json.dumps(dict.fromkeys(tp24_chat.FEATURES,3)) if i!=1 else ''
        row = {'id':str(i),'index':i,'binding':binding,'response':{'response':raw},'values':([3]*8 if raw else None)}
        name = f'B/row-{i:06d}.json'
        files[name] = write(mirror,name,row)
    receipt = {'owner':owner,'entry':entry,'job':'Q6','lane':'spark','status':'failed'}
    files['receipt.json'] = write(mirror,'receipt.json',receipt)
    release = {'owner':owner,'descriptorClosed':True}
    files['released.json'] = write(mirror,'released.json',release)
    files['failed.json'] = write(mirror,'failed.json',{'receiptPin':files['receipt.json']})
    inventory = write(tmp_path,'Q6-transfer-a-pins.json',files)
    audit = {'sourceReceiptPin':files['receipt.json'],'inventoryPin':inventory,'mirror':str(mirror),'nativeExited':True,
             'priorFlockReleased':True,'verifiedFiles':len(files),'release':release,'owner':owner,'terminal':'failed.json'}
    write(tmp_path,'Q6-transfer-a.json',audit)
    boundary = {'ownerTurnAt':'2026-11-21T07:00:00-08:00','trigger':'owner-turn','owner':owner,'durableRows':2}
    values,_,durable = prefix(tmp_path,boundary,items,lambda:None)
    assert values.shape==(2,8) and np.all(values[0]==3) and np.isnan(values[1]).all() and durable==3
    with pytest.raises(ValueError,match='response ID'):
        prefix(tmp_path,boundary,list(reversed(items)),lambda:None)
