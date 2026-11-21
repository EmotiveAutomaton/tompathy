"""Metadata census of local research sources. Publish counts only."""
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

DATA=Path('.local/readers/data')
BENCH=Path('.local/bench')


def coverage(rows, dated):
    n=Counter()
    days=defaultdict(set)
    for writer, day in rows:
        if writer in (None,'','[deleted]','[removed]'):
            continue
        n[writer]+=1
        if day:
            days[writer].add(day)
    many=[w for w in n if n[w]>=20]
    repeated=[w for w in n if len(days[w])>=2]
    def cohort(ws):
        return {'authors':len(ws),'medianTexts':median(n[w] for w in ws) if ws else None,
                'medianDates':median(len(days[w]) for w in ws) if ws and dated else None}
    return {'writers':len(n),'textsWithWriter':sum(n.values()),'atLeast20':cohort(many),
            'multipleDates':cohort(repeated) if dated else None,
            'both':cohort([w for w in many if len(days[w])>=2]) if dated else None}


def run(output,check):
    pins={}
    def source(p):
        with p.open('rb') as f:
            pins[str(p)]=hashlib.file_digest(f,'sha256').hexdigest()
        check()
        return p
    def csvrows(p,delimiter=',',**kwargs):
        with source(p).open(encoding='utf-8-sig',newline='') as f:
            yield from csv.DictReader(f,delimiter=delimiter,**kwargs)
    def js(p):
        return json.loads(source(p).read_bytes())
    results={}
    def file(label,rows,dated,unit):
        results[label]={'unit':unit,**coverage(rows,dated)}
    def blogrows():
        archive=source(DATA/'blogs-b/blogs.zip')
        if pins[str(archive)]!='1dfa6996663515a4baf8c1b71713ce8fe9a314b13778701447e4663bbc64c983':
            raise ValueError('Blog release changed')
        pattern=re.compile(rb'<date>\s*([^<>]*)\s*</date>|<post>(.*?)</post>',re.I|re.S)
        with zipfile.ZipFile(archive) as z:
            for i,member in enumerate(z.infolist()):
                if not member.filename.lower().endswith('.xml'):continue
                if i%100==0:check()
                author=Path(member.filename).name.split('.',1)[0]
                if not author.isdecimal():raise ValueError('Unknown blog ID format')
                day=None
                for m in pattern.finditer(z.read(member)):
                    if m[1] is not None:
                        try:day=datetime.strptime(m[1].strip().decode('ascii'),'%d,%B,%Y').date()
                        except (ValueError,UnicodeError):day=None
                    elif m[2].strip():yield author,day
    file('Blog Authorship Corpus',blogrows(),True,'nonempty post; blog ID and published date marker')
    seen={}
    for i in (1,2,3):
        for row in csvrows(DATA/f'go-emotions/goemotions_{i}.csv'):
            pair=(row['author'],datetime.fromtimestamp(float(row['created_utc']),UTC).date())
            if seen.setdefault(row['id'],pair)!=pair:raise ValueError('Conflicting comment metadata')
    file('GoEmotions',seen.values(),True,'unique comment; UTC creation date; unknown authors excluded')
    file('crowd-enVENT',((r['prolific_id'],datetime.strptime(r['timestamp'].split()[0],'%Y/%m/%d').date())
         for r in csvrows(DATA/'crowd-enVent2023/corpus/crowd-enVent_generation.tsv','\t') if r['generated_text'].strip()),
         True,'generated report; recorded submission calendar date')
    ed=[]
    for split in ('train','valid','test'):
        ed.extend((r['speaker_idx'],None) for r in csvrows(DATA/f'empathetic-dialogues/{split}.csv',quoting=csv.QUOTE_NONE) if r['utterance_idx']=='1')
    file('EmpatheticDialogues',ed,False,'one situation per conversation; no date')
    em=emocause(js,csvrows)
    file('EmoCause',em,False,'marked situations joined to original ED split; overlapping source, no date')
    file('Empathic Reactions',((r['response_id'],None) for r in csvrows(DATA/'empathic-reactions/data/responses/data/messages.csv')),
         False,'essay; response ID links the five essays; no date')
    responses=list(csvrows(DATA/'worry/data_phase_1/files/meta/rwwd_full.csv'))
    file('Real World Worry phase 1',((i,r['startdate'].split()[0]) for i,r in enumerate(responses) for field in ('text_long','text_short') if r[field].strip()),
         True,'long and short texts from one dated survey response per participant')
    sessions=js(BENCH/'two-day-ex1-intake/sessions.json')
    file('CoAuthor',((r['writer'],datetime.fromtimestamp(float(r['time'])/1000,UTC).date()) for r in sessions),
         True,'prepared session text; UTC session date')
    proposals=js(BENCH/'EX3/TASK.json')['documents']
    file('Proposal documents',((r['hashed_first_author'],None) for r in proposals),False,'document; hashed first author, no calendar date')
    for label,p,why in [
        ('CaSiNo',DATA/'casino/data/casino.json','dialogue-local roles; no released cross-dialogue author'),
        ('Story Commonsense / ROCStories',Path('.local/trigger/data/story-commonsense/rocstorysubset.csv'),'story IDs and character/annotator fields do not identify authors'),
        ('IteraTeR',DATA/'iterater-doc/train.json','revision/document IDs do not identify authors'),
        ('Stack Exchange edits',BENCH/'EX2/EDITS.json','user fold is shared by multiple writers; release lacks author ID'),
        ('Stack Exchange questions and answers',BENCH/'EX5/QUESTIONS.json','post IDs and posting order only'),
        ('RAID pilot',BENCH/'raid-pilot-20261113/rows.json','generation/source IDs without human author or calendar date')]:
        source(p);results[label]={'unavailable':why}
    return {'sources':pins,'estimate':results,'question':'Which saved sources let us follow the same author on different dates?',
            'interval':'Exact counts in the named local releases. Missing fields are unavailable.',
            'bar':'Inventory only. No qualification threshold.','verdict':'Descriptive count only.',
            'scope':'Engine study sources on local disks. No cross-source identity linkage; related releases overlap.'}


def emocause(js,csvrows):
    ids={r['conv_id'] for split in ('valid','test') for r in js(DATA/f'emocause/{split}.json')}
    authors={r['conv_id']:r['speaker_idx'] for split in ('train','valid','test')
             for r in csvrows(DATA/f'empathetic-dialogues/{split}.csv',quoting=csv.QUOTE_NONE)
             if r['utterance_idx']=='1' and r['conv_id'] in ids}
    if authors.keys()!=ids or len(ids)!=4613:
        raise ValueError('Incomplete EmoCause to dialogue join')
    return [(w,None) for w in authors.values()]


def finish_inventory(out,check):
    prior=out.parent/'tp42-a'
    raw=(prior/'receipt.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!='aa9fd1b45d3e8bcd10639b7142faf2c037b6d9fe7ff90968f3fef89281d0b8f2':
        raise ValueError('Prior census differs')
    d=json.loads(raw)
    def source(p):
        check()
        with p.open('rb') as f: h=hashlib.file_digest(f,'sha256').hexdigest()
        if d['sources'].setdefault(str(p),h)!=h: raise ValueError('Original census input changed')
        return p
    def js(p):return json.loads(source(p).read_bytes())
    def csvrows(p,**kw):
        with source(p).open(encoding='utf8',newline='') as f:yield from csv.DictReader(f,**kw)
    d['estimate']['EmoCause'].update(coverage(emocause(js,csvrows),False),unit='4,613 unique marked situations joined across original dialogue splits; no dates')
    for label,path,why in [
        ('Non-native essay benchmark',BENCH/'non-native-20261113/all_data.json','source, domain and model labels without stable individual or writing date'),
        ('IteraTeR sentence edits',BENCH/'iterater/train.json','document and revision indices without author or calendar date'),
        ('Art manuscript revisions',Path('.local/art-source/revision-index.tsv'),'dated revisions of one work, without a writer field in the local index'),
        ('ToMpathy essay collection',Path('src/content/essays-source.txt'),'authored collection without comparable per-text writing dates')]:
        source(path);d['estimate'][label]={'unavailable':why}
    d['sources']['priorInventory']=hashlib.sha256(raw).hexdigest()
    return {k:d[k] for k in ('sources','estimate','question','interval','bar','verdict','scope')}
