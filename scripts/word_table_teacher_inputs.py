"""Freeze the teacher roster locally. Only text and opaque row IDs go to the reader."""
import argparse
import hashlib
import json
import os
from bisect import bisect_left
from collections import Counter, defaultdict
from pathlib import Path

from word_table_inputs import ROOT, pin, write

GROUPS = ('ed', 'envent', 'go', 'story', 'coauthor', 'stack')


def hash_key(value):
    return hashlib.sha256(value.encode()).hexdigest()


def balanced(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['source']].append(row)
    if set(groups) != set(GROUPS):
        raise ValueError('Six registered sources required')
    for group in groups.values():
        group.sort(key=lambda r: hash_key('TP31:23:'+r['key']))
    return [item for start in range(0, max(map(len,groups.values())), 10)
            for source in GROUPS for item in groups[source][start:start+10]]


def build(base, dest):
    import pandas as pd
    from tompathy_engine.eval.readers.affect_data import ed_situations, go_comments
    from tompathy_engine.eval.readers.envent import load
    from tompathy_engine.eval.readers.story import verify
    from tompathy_engine.eval.readers.tp10 import neutral_texts
    from tompathy_engine.eval.readers.tp31_teacher import protected_pins, sentences, text_pin

    data = ROOT/'.local/readers/data'
    frozen = json.loads((ROOT/'.local/nine-channel/tp30-frozen-a/receipt.json').read_bytes())
    prior = json.loads((base/'intake-a/intake.json').read_bytes())
    if pin(ROOT/'.local/nine-channel/tp30-frozen-a/receipt.json') != prior['frozenReceiptPin']:
        raise ValueError('Prior public corpus binding changed')
    ev = load(data/'crowd-enVent2023')
    reserved = set(json.loads((base/'intake-a/reserved-ids.json').read_bytes())['F2'])
    themes, revisions, _ = neutral_texts(ROOT/'.local/readers/prepared-v2')
    if (len(themes),len(revisions),len(reserved)) != (40,191,350):
        raise ValueError('Protected evaluation sets changed')
    reserved_rows = ev.reports.loc[ev.reports.text_id.astype(str).isin(reserved)]
    if len(reserved_rows) != 350 or set(reserved_rows.text_id.astype(str)) != reserved:
        raise ValueError('Cannot bind all 350 reserved reports to their original text')
    # F2's unit of reservation is the original whole report. Other independent
    # documents can share a generic sentence. Both TP31 acceptance tests also
    # protect their constituent sentences under the original student protocol.
    protected = protected_pins(themes+revisions) | {text_pin(text) for text in reserved_rows.hidden_emo_text}
    if ev.pins != frozen['sources']['envent']['files']:
        raise ValueError('Recalled-event source changed')
    rows, parent_docs, exclusions, sources = [], {}, Counter(), {'envent':ev.pins}

    def add(source, ident, group, text, *, known=None, affected=None, words=None):
        key = f'{source}:{ident}'
        parts = sentences(text)
        if text_pin(text) in protected:
            exclusions[source+'-protected-documents'] += 1
            return
        if known and all(text_pin(part) not in protected for part in parts):
            parent_docs[key] = text
        cursor = 0
        ends = [w['end'] for w in words] if words is not None else None
        for position, part in enumerate(parts):
            if words is not None:
                start = text.index(part, cursor)
                cursor = start+len(part)
                index = bisect_left(ends,start+1)
                selected = []
                while index<len(words) and words[index]['start']<cursor:
                    selected.append(words[index])
                    index+=1
                if not selected or any(w['source']!='writer' or w['start']<start or w['end']>cursor for w in selected):
                    exclusions['coauthor-nonwriter-sentences']+=1
                    continue
            if text_pin(part) in protected:
                exclusions[source+'-protected-sentences'] += 1
                continue
            original = f'{key}:{position}'
            rows.append({'key':original,'id':hash_key(original),'source':source,'group':str(group),
                         'parent':key,'known':known,'affected':affected,'text':part})

    ed, ed_identity = ed_situations(data/'empathetic-dialogues')
    if ed_identity != frozen['sources']['ed']:
        raise ValueError('ED source changed')
    sources['ed'] = ed_identity['intakePin']
    for r in ed.itertuples():
        add('ed',r.id,r.writer,r.text,known='ed')
    for r in ev.reports.itertuples():
        add('envent',r.text_id,r.prolific_id,r.hidden_emo_text,known='envent-feeling' if r.emotion!='no-emotion' else None)
    go, _, _, go_identity = go_comments(data/'go-emotions')
    if go_identity != frozen['sources']['go']:
        raise ValueError('Go source changed')
    sources['go'] = go_identity['intakePin']
    for r in go.itertuples():
        add('go',r.id,r.writer if r.writer_known else r.id,r.text)

    story = ROOT/'.local/trigger/data/story-commonsense'
    paths = [story/'csv_version'/s/'emotion/allcharlinepairs.csv' for s in ('dev','test')]
    verify(story,paths)
    sources['story']={p.relative_to(story).as_posix():pin(p) for p in paths}
    raw = pd.concat([pd.read_csv(p,usecols=['storyid','linenum','sentence','affected']) for p in paths])
    for (sid,number), group in raw.groupby(['storyid','linenum'],sort=False):
        if group.sentence.nunique()!=1:
            raise ValueError('Story line has conflicting text')
        # A change concerns any story participant. Keep the original line once.
        flags=set(group.affected.dropna())
        if not flags <= {'yes','no'}:
            raise ValueError('Unrecognized publisher affected flag')
        add('story',f'{sid}:{number}',sid,group.sentence.iloc[0],affected=('yes' in flags) if flags else None)

    ex1 = ROOT/'.local/bench/two-day-ex1-intake/sessions.json'
    sources['coauthor']=pin(ex1)
    if sources['coauthor']!='593354494096a2097f5b93cadfb221ab5a8fa27a7380a821b36818ea109a9d21':
        raise ValueError('Verified public CoAuthor word provenance changed')
    for session in json.loads(ex1.read_bytes()):
        add('coauthor',session['session'],session['writer'],session['text'],words=session['words'])
    stack=ROOT/'.local/bench/EX5/QUESTIONS.json'
    sources['stack']=pin(stack)
    if sources['stack']!='6012ff4f90169697df1d5c661b08456aa5a4a85ac2aa6d8777ad4063ac7cbb32':
        raise ValueError('EX5 public answers changed')
    for q in json.loads(stack.read_bytes()):
        for a in q['answers']:
            add('stack',f"{q['site']}:{a['answer_id']}",f"{q['site']}:{q['question_id']}",a['body'],known='stack')
    roster=balanced(rows)
    if len({r['id'] for r in roster})!=len(roster) or len(roster)<30001:
        raise ValueError('Teacher roster identities or size differ')
    if exclusions['envent-protected-documents'] < len(reserved):
        raise ValueError('Reserved source documents were retained')
    excluded_parents = {'envent:'+item for item in reserved}
    if any(r['parent'] in excluded_parents for r in roster):
        raise ValueError('Reserved report reached the teacher roster')
    dest.mkdir(exist_ok=False)
    # Original source/group keys and author identifiers remain local.
    with (dest/'local-roster.jsonl').open('x',encoding='utf8') as f:
        for r in roster:
            f.write(json.dumps({k:v for k,v in r.items() if k!='text'},ensure_ascii=False)+'\n')
    def minimum(r):
        return {'id':r['id'],'text':r['text']}
    for job,subset in [('Q3',roster[:2000]),('Q4',roster[2000:30000]),('Q7',roster[30000:])]:
        write(dest/(job+'.json'),[minimum(r) for r in subset])
    # Whole parent documents represented by the first 2,000 retain TP31's
    # original known-group unit. Reuse identical B requests from the panel.
    panel=roster[:2000]
    by_text={r['text']:r['id'] for r in panel}
    extra, keys, parents=[],{},set()
    for r in panel:
        if not r['known'] or r['parent'] in parents:
            continue
        parents.add(r['parent'])
        if r['parent'] not in parent_docs:
            # A whole-document question would reproduce protected text. Keep the
            # document in the denominator with an explicitly unknown response.
            keys.setdefault(r['known'],[]).append(None)
            continue
        text=parent_docs[r['parent']]
        if text not in by_text:
            ident=hash_key('parent:'+r['parent'])
            extra.append({'id':ident,'text':text})
            by_text[text]=ident
        keys.setdefault(r['known'],[]).append(by_text[text])
    write(dest/'Q3-docs.json',extra)
    write(dest/'Q3-checks.json',{'groups':keys,'story':{r['id']:r['affected'] for r in panel
                                                       if r['source']=='story' and r['affected'] is not None}})
    counts=Counter(r['source'] for r in roster)
    report={'sources':sources,'rosterRows':len(roster),'sourceCensus':counts,'excluded':exclusions,
            'panelCensus':Counter(r['source'] for r in panel),'protectedPinCount':len(protected),
            'reservedReportCount':len(reserved_rows),
            'wholeDocumentGroups':{k:len(v) for k,v in keys.items()},'newParentRequests':len(extra),
            'files':{p.name:pin(p) for p in dest.iterdir() if p.is_file()}}
    write(dest/'intake.json',report)
    return report


if __name__=='__main__':
    for variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[variable]='2'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    dest = parser.parse_args().output.resolve()
    base = ROOT/'.local/word-table'
    if dest.parent != base.resolve():
        parser.error('Use a fresh immediate child of the private word-table directory')
    print(json.dumps(build(base,dest),indent=2))
