# Ported from Sounding Line, copyright 2026 Abraham Haskins (MIT).
# See engine/NOTICE-SOUNDING-LINE.txt and reference-sources.json.
"""Witnessed production relations, separate from mental-state hypotheses.

DESIGN CHECK: LESSONS 2-5. NULL: identical endpoints have identical blind public
fields despite different histories; absent telemetry cannot establish non-review.
ALTERNATIVE: verified insertion, replacement, continuation and surrounding edits
produce distinct finite facts and surviving/unlocated spans. Exact endpoint replay
and native handling agreement gate every projected source. No model adjudicator.
"""
from difflib import SequenceMatcher
import json
from .quill import units,text_of,delta_ops,apply_delta

ACTORS=('human_writer','model','tool','unknown')
OPERATIONS=('select','insert','format_edit','content_edit','delete','absent','unknown')
RELATIONS=('selects','selected_by','modifies','extends','removes','unrelated','none','unknown')
SLOTS=('selection','entry','change','continuation','surrounding','removal')
SPAN_STATES=('located','unlocated','absent','unknown')
FRAGMENT={'model','fragment_edit'}


def anchors(document):
    return [dict(id=f'a{i//160:03d}',start=i,end=min(i+160,len(document)),text=document[i:i+160])
            for i in range(0,len(document),160)]


def public(event,tier):
    doc=event['end_document']
    out=dict(endpoint=doc,anchors=[{k:a[k] for k in ('id','start','end')} for a in anchors(doc)],
        menu_was_available=True,brief=None,brief_available=False)
    if tier=='alternatives':
        before=event['document'];out.update(before=before,alternatives=[s['original'] for s in event['options']],
            differences=[dict(operation=tag,before=before[i:j],after=doc[k:l])
                         for tag,i,j,k,l in SequenceMatcher(None,before,doc,autojunk=False).get_opcodes() if tag!='equal'])
    elif tier!='artifact':raise ValueError('unknown evidence tier')
    return out


def norm(text):
    return ''.join(c for c in text.casefold() if c.isalnum())


def positions(document,owners,wanted):
    # UTF-16 ownership becomes codepoint offsets only at valid character boundaries.
    out=[];i=0;cp=0;start=None
    while i<len(document):
        width=2 if 0xD800<=document[i]<=0xDBFF else 1
        own=any(o in wanted for o in owners[i:i+width])
        if own and start is None:start=cp
        if not own and start is not None:out.append([start,cp]);start=None
        i+=width;cp+=1
    if start is not None:out.append([start,cp])
    return out


def project(event,source_lines):
    rows=[json.loads(x) if isinstance(x,str) else x for x in source_lines]
    own=rows[event['ordinal']:event['cutoff_ordinal']]
    doc=units(event['document']);owners=['base']*len(doc)
    if doc and doc[-1]==10:owners[-1]='terminal'
    inserted=False;selected=False;changed=False;removed=False;surrounding=False;continued=False
    initial_fragment='';base_deleted=[];base_inserted=[];facts=[];trace=[]
    boundary=max(0,len(doc)-1)
    for offset,e in enumerate(own):
        if e.get('eventName')=='suggestion-select':selected=True
        value=e.get('textDelta')
        if not value:continue
        ops=delta_ops(value);source=e.get('eventSource')
        if source not in ('api','user'):raise ValueError('unidentified delta actor')
        before=text_of(doc)
        after,_,_=apply_delta(doc,[None]*len(doc),value)
        trace.append(dict(event=offset,source=source,operations=ops))
        if source=='api':
            matches=[o for o in event['options'] if before.endswith('\n') and text_of(after)==
                before[:-1]+o['original'].replace('\r\n','\n').replace('\r','\n')+'\n']
            if not selected or inserted or not matches:raise ValueError('unverified/extra API insertion in episode')
            delta=len(after)-len(doc);owners=owners[:-1]+['model']*delta+owners[-1:]
            initial_fragment=matches[0]['original'].replace('\r\n','\n').replace('\r','\n')
            inserted=True;doc=after;boundary=max(0,len(doc)-1);continue
        cursor=0;touched=False
        for op in ops:
            if 'retain' in op:cursor+=op['retain']
            elif 'delete' in op:
                touched |= any(x in FRAGMENT for x in owners[cursor:cursor+op['delete']]);cursor+=op['delete']
            elif 0<cursor<len(owners):touched |= owners[cursor-1] in FRAGMENT and owners[cursor] in FRAGMENT
        output=[];outowners=[];cursor=0;next_boundary=boundary
        for op in ops:
            if 'retain' in op:
                end=cursor+op['retain'];output+=doc[cursor:end];outowners+=owners[cursor:end];cursor=end
            elif 'delete' in op:
                end=cursor+op['delete'];lost=owners[cursor:end]
                next_boundary-=max(0,min(end,boundary)-cursor)
                changed |= any(x in FRAGMENT for x in lost)
                removed |= 'model' in lost
                for char,owner in zip(doc[cursor:end],lost):
                    if owner in ('base','surrounding'):base_deleted.append(char);surrounding=True
                cursor=end
            else:
                new=units(op['insert'])
                if cursor<boundary:next_boundary+=len(new)
                fragment_neighbor=any(x in FRAGMENT for x in owners[max(0,cursor-1):cursor+1])
                inside=0<cursor<len(owners) and owners[cursor-1] in FRAGMENT and owners[cursor] in FRAGMENT
                if inside or (touched and fragment_neighbor):tag='fragment_edit';changed|=bool(new)
                else:
                    if cursor>=boundary:tag='continuation';continued|=bool(new)
                    else:tag='surrounding';surrounding|=bool(new);base_inserted+=new
                output+=new;outowners += [tag]*len(new)
        output+=doc[cursor:];outowners+=owners[cursor:]
        assert output==after and len(output)==len(outowners)
        doc,owners,boundary=output,outowners,next_boundary
    if text_of(doc)!=event['end_document']:raise ValueError('relation projection endpoint differs')
    if inserted!=event['verified_insertion']:raise ValueError('verified entry differs')
    if changed!=(event['decision']=='edit'):raise ValueError('fragment edit differs from native handling')
    spans={name:positions(doc,owners,tags) for name,tags in
           [('fragment',FRAGMENT),('continuation',{'continuation'}),('surrounding',{'surrounding'})]}
    fragment=text_of([c for c,o in zip(doc,owners) if o in FRAGMENT])
    change_op='delete' if not fragment else 'format_edit' if norm(fragment)==norm(initial_fragment) else 'content_edit'
    surrounding_op='format_edit' if norm(text_of(base_deleted))==norm(text_of(base_inserted)) else 'content_edit'
    configs=[('selection',inserted,'human_writer','select','selects','entry','fragment'),
             ('entry',inserted,'model','insert','selected_by','selection','fragment'),
             ('change',changed,'human_writer',change_op,'modifies','entry','fragment'),
             ('continuation',continued,'human_writer','insert','extends' if inserted else 'none','entry' if inserted else '', 'continuation'),
             ('surrounding',surrounding,'human_writer',surrounding_op,'unrelated' if inserted else 'none','entry' if inserted else '', 'surrounding'),
             ('removal',removed,'human_writer','delete','removes','entry',None)]
    endpoint_anchors=anchors(event['end_document'])
    for slot,present,actor,operation,relation,parent,span_name in configs:
        exact=spans.get(span_name,[]) if present else []
        ids=[a['id'] for a in endpoint_anchors if any(a['start']<end and start<a['end'] for start,end in exact)]
        facts.append(dict(slot=slot,actor=actor if present else 'unknown',operation=operation if present else 'absent',
            relation=relation if present else 'none',related_slot=parent if present else '',
            span_ids=ids,span_state='located' if ids else 'unlocated' if present else 'absent',exact_spans=exact))
    return dict(handling=event['decision'],facts=facts,attributes=dict(reviewed='unknown',endorsed='unknown',understood='unknown'),
        trace=trace,source_agreement=True,scope='witnessed record, not total thought or semantic importance')
