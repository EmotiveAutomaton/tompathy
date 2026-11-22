"""Q22 article-level fallback at the pinned public Empathic Reactions revision."""
import csv
import json
from pathlib import Path

from cb_inputs import digest,pin
from tompathy_engine.eval.readers.tp31_teacher import sentences


def prepare(out,check):
    tree=json.loads(Path('.local/week-20261122/news-tree.json').read_bytes())
    if tree['tree']!='3ddbf6b35c789f99c930a349f3fc26b4b2d9ae2e' or [
        p for p in tree['paths'] if p.startswith('data/') and '.' in Path(p).name
    ]!=['data/responses/data/messages.csv']:
        raise ValueError('Recheck released article availability')
    data=Path('.local/readers/data/empathic-reactions')
    key='data/responses/data/messages.csv'
    h=json.loads((data/'intake.json').read_bytes())['sources'][key]['sha256']
    if pin(data/key)!=h:
        raise ValueError('Essay source differs')
    with (data/key).open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    essays=[];marks=[];local=[]
    for r in rows:
        ident=digest('Q22:'+r['message_id'])
        essays.append(dict(id=ident,text=r['essay']))
        parts=sentences(r['essay'])
        marks.extend(dict(id=digest(ident+':'+str(i)),text=s) for i,s in enumerate(parts))
        local.append([ident,r['response_id'],r['article_id'],len(parts),float(r['empathy']),float(r['distress'])])
    if len(essays)!=1860 or len({r['id'] for r in essays})!=1860 or len({r[1] for r in local})!=372:
        raise ValueError('Original essay roster differs')
    dest=out/'spark-inputs'
    dest.mkdir()
    for p,v in [(out/'joins.json',local),(dest/'essays.json',essays),(dest/'sentences.json',marks)]:
        p.write_text(json.dumps(v,ensure_ascii=False),encoding='utf8')
    return dict(source=h,tree=tree['tree'],counts=dict(articles=len({r[2] for r in local}),articleTexts=0,
                essays=len(essays),sentences=len(marks)),files={p.name:pin(p) for p in dest.iterdir()})
