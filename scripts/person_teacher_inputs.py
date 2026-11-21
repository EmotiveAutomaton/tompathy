"""Prepare only the two local open corpora for the November 21 change-reader jobs."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.envent import load
from tompathy_engine.eval.readers.tp31_teacher import sentences

BASE = ROOT/'.local/person-teacher'
STANDING = {'ed':{'content','confident','trusting','faithful','prepared','lonely','nostalgic','sentimental'},
            'envent':{'trust','boredom'}}


def key(value):
    return hashlib.sha256(value.encode()).hexdigest()


def save(path,value):
    raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
    if path.exists():
        if path.read_bytes()!=raw:
            raise ValueError('Preserve existing input '+path.name)
    else:
        with path.open('xb') as stream:
            stream.write(raw)
    return hashlib.sha256(raw).hexdigest()


def prepare():
    data=ROOT/'.local/readers/data'
    ed,ed_pin=ed_situations(data/'empathetic-dialogues')
    ev=load(data/'crowd-enVent2023')
    src=json.loads((ROOT/'.local/readers/tp13-a/receipt.json').read_bytes())
    if ed_pin!=src['data']['ed'] or ev.pins!=src['data']['envent']['files']:
        raise ValueError('Original corpus identity changed')
    sources={'ed':[(str(r.id),r.text,r.label,str(r.writer)) for r in ed.itertuples()],
             'envent':[(str(r.text_id),r.hidden_emo_text,r.emotion,str(r.prolific_id)) for r in ev.reports.itertuples()
                       if r.emotion!='no-emotion']}
    stages={'Q11':[],'Q12':[]};private=[]
    for name,rows in sources.items():
        for i,(ident,text,word,writer) in enumerate(sorted(rows,key=lambda r:key('TP40:23:'+r[0]))):
            stage='Q11' if i<1500 else 'Q12'
            pid=key('TP40:parent:'+name+':'+ident)
            parts=sentences(text)
            if not parts:
                raise ValueError('Empty document in registered roster')
            private.append([pid,name,ident,writer,word,stage])
            stages[stage].extend({'id':key(f'{pid}:{j}'),'parent':pid,'source':name,'standing':word in STANDING[name],
                                  'text':part} for j,part in enumerate(parts))
    folder=BASE/'inputs'
    folder.mkdir(exist_ok=True)
    pins={k:save(folder/(k+'.json'),v) for k,v in stages.items()}
    save(BASE/'private-parents.json',private)
    proof={'sourcePins':{'ed':ed_pin['intakePin'],'envent':ev.pins['generation']},'files':pins,
           'documents':{k:len(v) for k,v in sources.items()},'sentences':{k:len(v) for k,v in stages.items()},
           'maxInputBytes':max(len(r['text'].encode()) for v in stages.values() for r in v)}
    save(folder/'manifest.json',proof)
    print(proof)


if __name__=='__main__':
    prepare()
