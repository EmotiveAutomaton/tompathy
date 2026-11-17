"""Hand-set TS3 software answers, before any empirical pack is qualified."""
import hashlib
import json

import numpy as np
import pytest

from tompathy_engine.packet.bottom_box import empty_bottom_box
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packs.registry import load_pack, sha256
from tompathy_engine.packs.runtime import run, sentence_rows, windows
from tompathy_engine.packs.v2 import code_pin


def make_pack(root, name, task, weights, bias, **fields):
    root.mkdir()
    (root/'encoder').mkdir()
    (root/'encoder/fixture.json').write_text('{}')
    (root/'LICENSE.txt').write_text('Constructed software test')
    np.savez(root/'head.npz', weights=np.array(weights, float), bias=np.array(bias, float))
    files = {'encoder/fixture.json': sha256(root/'encoder/fixture.json')}
    license = {'name':'fixture', 'source':'test', 'license':'constructed', 'commercial_use':True,
               'file':'LICENSE.txt', 'license_sha256':sha256(root/'LICENSE.txt')}
    m = {'name':name, 'version':'reader-pack-2', 'task':task, 'labels':['signal'],
         'encoder':{'id':'fixture', 'revision':'1', 'kind':'constructed', 'files':files,
             'sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(), 'license':license},
         'head':{'file':'head.npz','sha256':sha256(root/'head.npz')}, 'token_cap':128,
         'key':{'corpus':'constructed','labelled_by':'test author','n':3},
         'score':{'metric':'constructed','value':1,'interval':None}, 'people':{}, 'floor':{}, 'nothing_here':{},
         'training':[license], 'research_only':True, 'status':'research',
         'mapping':{'status':'proposed','source':'constructed'}, 'code_pin':code_pin(), **fields}
    (root/'pack.json').write_text(json.dumps(m))
    return m


def test_four_pack_wire_and_shared_vectors(tmp_path):
    # Written answers: only first two sentences pass; tag N1 on first, channel C3
    # on first two; one scalar window at .5; neither tags nor channels has a share.
    gate = make_pack(tmp_path/'gate','gate','gate',[[10,0]],[-5],thresholds={'signal':.5})
    make_pack(tmp_path/'tags','tags','tags',[[0,10]],[-5],thresholds={'signal':.5},tag_map={'signal':'N1'})
    make_pack(tmp_path/'channel','channel','channel',[[0,0],[0,0]],[5,0],
              labels=['fear','neutral'],neutral='neutral',label_map={'fear':'C3'})
    make_pack(tmp_path/'scalar','scalar','scalar',[[0,0]],[5],range=[1,9],unit='worry',reading_id='S1')
    calls=[]
    def encode(texts):
        calls.extend(texts)
        return [[int(t.startswith(('Fear','Joy'))),int(t.startswith('Fear'))] for t in texts]
    adapters={gate['encoder']['sha256']:(encode,lambda t:len(t.split()))}
    rows=sentence_rows('Fear 😟. Joy. Plain.')
    assert [(r.start,r.end) for r in rows]==[(0,8),(9,13),(14,20)]
    dirs=[tmp_path/n for n in ('gate','tags','channel','scalar')]
    assert run(dirs,rows)==empty_bottom_box()
    assert run(dirs,rows,enabled=True)==empty_bottom_box()
    diag={}
    result=run(dirs,rows,enabled=True,research=True,adapters=adapters,diagnostics=diag)
    assert result['version']=='bottom-box-2' and result['about_maker']==[]
    by_id={r['id']:r for r in result['on_page']}
    assert set(by_id)=={'N1','C3','S1'}
    assert [e['span'] for e in by_id['N1']['events']]==[[0,8]]
    assert [e['span'] for e in by_id['C3']['events']]==[[0,8],[9,13]]
    assert by_id['S1']['series']==[{'from':0,'to':20,'value':.5}]
    assert all(r['share'] is None for r in result['on_page'])
    assert len(calls)==4 and diag['encoderCount']==1
    # With no gate only the scalar is eligible; channels never encode.
    assert [r['id'] for r in run(dirs[1:],rows,enabled=True,research=True,adapters=adapters)['on_page']]==['S1']
    with pytest.raises(ValueError,match='release'):
        load_pack(dirs[0],release=True)
    (dirs[0]/'head.npz').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):
        load_pack(dirs[0])


def test_window_boundaries_and_non_bmp_spans():
    rows=sentence_rows('One word. Two words. Three words. Four words.')
    out=windows(rows,4,lambda t:len(t.split()))
    assert [r.text for r in out]==['One word. Two words.','Two words. Three words.','Three words. Four words.']
    assert len(windows(sentence_rows('x '*300+'.'),128,lambda t:len(t.split())))==1


def test_default_build_byte_parity(tmp_path):
    from tompathy_engine.adapters.capture import make_capture
    capture=make_capture(['A careful choice. 🌞'], 'https://example.org/fixture',
                         'Constructed fixture', '2026-01-01T00:00:00Z')
    a=build_packet(capture,bottom_box=True)
    b=build_packet(capture,bottom_box=True,packs=[],research=False)
    assert json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
    gate=make_pack(tmp_path/'gate','gate','gate',[[0,0]],[1],thresholds={'signal':.5})
    make_pack(tmp_path/'tags','tags','tags',[[0,0]],[1],thresholds={'signal':.5},tag_map={'signal':'N1'})
    dirs=[tmp_path/'gate',tmp_path/'tags']
    hidden=build_packet(capture,bottom_box=True,packs=dirs,research=False)
    assert hidden==a
    visible=build_packet(capture,bottom_box=True,packs=dirs,research=True,
        reader_adapters={gate['encoder']['sha256']:(lambda ts:[[1,1] for _ in ts],lambda t:len(t.split()))})
    assert visible['bottom_box']['on_page'][0]['id']=='N1'
    assert visible['id']!=a['id']
    assert 'Research readers are present' in visible['provider']['method']
