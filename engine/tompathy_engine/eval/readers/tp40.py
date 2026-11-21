"""Whole-text change, sentence change and cross-reader disagreement, with writer intervals."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..back_half.reporting import save_json
from . import person_halves as halves
from .tp31_teacher import PROMPT, SCHEMA, valid_label
from .tp39 import PACKET, SUPPORT
from .word_panels import pinned, read, sha256

MANIFEST = 'c36d09d12d744fb9822979335fe8d4cc2b98726347b23e730ab2e40cf9869e3d'
COMMIT = 'ff2e4dd0f02fb9488e35ce4acf580ce0bad73d53'
MODEL = {'B':'72aac7c28be8ff9b81c2a270eb489c88e6d822a76ec0cb7bf34d965768848567',
         'W':'6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7'}
STANDING = {'ed':{'content','confident','trusting','faithful','prepared','lonely','nostalgic','sentimental'},
            'envent':{'trust','boredom'}}


def verified_job(root, job):
    audit = read(root/(job+'-transfer-a.json'))
    directory = root/('verified-spark-'+job+'-a') if job != 'G4' else root/'jobs/G4'
    receipt = pinned(directory/'receipt.json', audit['sourceReceiptPin'])
    owner = read(directory/'owner.json')
    if (receipt['status'] != 'complete' or receipt['owner'] != owner or owner != audit['owner']
        or owner['commit'] != COMMIT or owner['job'] != job or receipt['manifestPin'] != MANIFEST
        or not audit['nativeExited'] or not audit['priorFlockReleased']
        or read(directory/'complete.json')['receiptPin'] != audit['sourceReceiptPin']
        or read(directory/'released.json') != audit['release']
        or audit['release']['owner'] != owner or not audit['release']['descriptorClosed']
        or audit['release']['nativeExitCode'] != 0):
        raise ValueError('A complete source with exact owner release is required')
    inventory = pinned(root/(job+'-transfer-a-pins.json'), audit['inventoryPin'])
    return directory, receipt, inventory


def load_labels(job, block, role, items, roster_pin, terminal, check):
    directory, receipt, inventory = terminal
    folder = directory/block/role
    def verified(name):
        path = folder/name
        return pinned(path, inventory[path.relative_to(directory).as_posix()])
    protocol = verified('protocol.json')
    binding = {k:v for k,v in protocol.items() if k not in ('prompt','schema','secondKey')}
    import hashlib
    def digest(s):
        return hashlib.sha256(s.encode()).hexdigest()
    expected = {'commit':COMMIT,'inputPin':roster_pin,'manifestPin':MANIFEST,'job':job,'block':block,
                'role':role,'modelPin':MODEL[role],'think':False,'promptPin':digest(PROMPT),
                'schemaPin':digest(json.dumps(SCHEMA,sort_keys=True)),
                'options':{'temperature':0,'seed':23,'num_ctx':4096,'num_predict':256,'num_thread':2 if role=='W' else 3}}
    if binding != expected or protocol['schema'] != SCHEMA or protocol['prompt'] != PROMPT:
        raise ValueError('Teacher prompt, model or configuration differs')
    result=[]
    for i,item in enumerate(items):
        if i%128==0:
            check()
        row=verified(f'row-{i:06d}.json')
        try:
            value=valid_label(json.loads(row['response']['response']))
        except (TypeError,ValueError,KeyError):
            value=None
        if row['index']!=i or row['binding']!=binding or row['id']!=item['id'] or row['values']!=value:
            raise ValueError('Teacher row or raw response differs')
        result.append(value)
    done=verified('complete.json')
    if receipt[block]!=done or done['rows']!=len(result) or done['valid']!=sum(v is not None for v in result):
        raise ValueError('Teacher completion counts differ')
    return result


def summarize_text(bs, ws):
    common=[(b,w) for b,w in zip(bs,ws,strict=True) if b is not None and w is not None]
    known=[b for b in bs if b is not None]
    unknown=len(bs)-len(known)
    positive=any(b['change'] for b in known)
    return {'texts':1,'noChange':int(not positive and unknown==0),'unknownTexts':int(not positive and unknown>0),
            'sentences':len(bs),'negativeSentences':sum(not b['change'] for b in known),'unknownSentences':unknown,
            'paired':len(common),'changeDisagree':sum(b['change']!=w['change'] for b,w in common),
            'labelDisagree':sum(b!=w for b,w in common),
            'changeShare':np.nan if unknown else sum(b['change'] for b in known)/len(bs),
            'ownShare':np.nan if unknown else sum(b['whose']=='writer' for b in known)/len(bs),
            'aheadShare':np.nan if unknown else sum(b['when']=='ahead' for b in known)/len(bs)}


def ratio(x,y):
    return np.divide(x,y,out=np.full(np.broadcast_shapes(np.shape(x),np.shape(y)),np.nan),where=y!=0)


def source_table(df, check):
    counts=['texts','noChange','unknownTexts','sentences','negativeSentences','unknownSentences',
            'paired','changeDisagree','labelDisagree']
    writers=sorted(df.writer.unique())
    weights=halves.resamples(len(writers))
    table={}
    grouped={}
    for label,part in [*df.groupby('word',sort=True),('standing',df[df.standing]),('other',df[~df.standing])]:
        check()
        data=part.groupby('writer')[counts].sum().reindex(writers,fill_value=0).to_numpy()
        sums=data.sum(axis=0)
        draws=weights @ data
        item=dict(zip(counts,map(int,sums),strict=True))
        for key,i,j in [('textNoChange',1,0),('sentenceNoChange',4,3),('WChangeDisagreement',7,6),('WFullLabelDisagreement',8,6)]:
            point,boot=ratio(sums[i],sums[j]),ratio(draws[:,i],draws[:,j])
            item[key]=halves.summary(point,boot)
        item['textNoChangeUpper']=float((sums[1]+sums[2])/sums[0])
        item['sentenceNoChangeUpper']=float((sums[4]+sums[5])/sums[3])
        table[label]=item
        if label in ('standing','other'):
            grouped[label]=(sums,draws)
    a,ab=grouped['standing']
    b,bb=grouped['other']
    def rr(a,b):
        return ratio(ratio(a[...,1],a[...,0]),ratio(b[...,1]+b[...,2],b[...,0]))
    point,draws=rr(a,b),rr(ab,bb)
    result=halves.summary(point,draws)
    result['passes']=bool(result['value'] is not None and result['interval'] and result['validDraws']==len(weights)
                          and result['value']>=2 and result['interval'][0]>1)
    return table,result,draws


def run(output, check, ledger, protocol):
    if sha256(protocol)!=PACKET:
        raise ValueError('Registered November 21 packet required')
    root=Path('.local/person-teacher')
    manifest=pinned(root/'inputs/manifest.json',MANIFEST)
    support=pinned(root/'tp39-support.json',SUPPORT)
    parents=pinned(root/'private-parents.json',support['parentsPin'])
    meta={p:(s,i,w,word,block) for p,s,i,w,word,block in parents}
    terminals={job:verified_job(root,job) for job in ('Q11','Q12','G4')}
    docs=[]
    for block in ('Q11','Q12'):
        roster_pin=manifest['files'][block]
        items=pinned(root/'inputs'/(block+'.json'),roster_pin)
        b=load_labels(block,block,'B',items,roster_pin,terminals[block],check)
        w=load_labels('G4',block,'W',items,roster_pin,terminals['G4'],check)
        by_parent={}
        for row,br,wr in zip(items,b,w,strict=True):
            p=row['parent']
            source,_,_,word,stage=meta[p]
            if stage!=block or source!=row['source'] or row['standing']!=(word in STANDING[source]):
                raise ValueError('Registered source or word grouping differs')
            group=by_parent.setdefault(p,([],[]))
            group[0].append(br)
            group[1].append(wr)
        for p,(bs,ws) in by_parent.items():
            source,ident,writer,word,_=meta[p]
            docs.append({'source':source,'id':ident,'writer':writer,'word':word,'standing':word in STANDING[source],
                         **summarize_text(bs,ws)})
    frame=pd.DataFrame(docs)
    if len(meta)!=len(parents) or len(frame)!=len(meta) or frame.duplicated(['source','id']).any():
        raise ValueError('Incomplete or duplicated parent coverage')
    q11=terminals['Q11']
    decision=pinned(q11[0]/'decision.json',q11[1]['decisionPin'])
    tables,rows,draws={},{},{}
    for s in STANDING:
        tables[s],rows[s],draws[s]=source_table(frame[frame.source==s],check)
    valid_pool=all(np.all(np.isfinite(draws[s]) & (draws[s]>0)) for s in STANDING)
    pool=None
    if valid_pool:
        variance=np.array([np.var(np.log(draws[s]),ddof=1) for s in STANDING])
        if (variance>0).all():
            weights=1/variance
            vals=np.array([rows[s]['value'] for s in STANDING])
            mean=float(np.average(np.log(vals),weights=weights))
            se=weights.sum()**-.5
            pool={'value':float(np.exp(mean)),'interval':np.exp([mean-1.96*se,mean+1.96*se]).tolist()}
    gate=decision['passes']
    both=all(v['passes'] for v in rows.values())
    outcome=('Reader B meets the amended teaching check. ' if gate else 'Reader B misses the amended teaching check. ')
    outcome+=('The standing-state contrast clears both source thresholds.' if both else
              'The standing-state contrast does not clear both source thresholds.')
    # Store the private change features once. The addendum consumes these without reopening the four matching arms.
    ed=frame[frame.source=='ed']
    path=output/'ed-change-shares.npz'
    np.savez_compressed(path,ids=ed.id.to_numpy(str),shares=ed[['changeShare','ownShare','aheadShare']].to_numpy())
    def cell(v):
        return 'unavailable' if not v['interval'] else f"{v['value']:.3f} [{v['interval'][0]:.3f}, {v['interval'][1]:.3f}]"
    table=['| Source | Standing / other no-change rate ratio | Both bars met |','|---|---:|---|']
    table += [f"| {s} | {cell(r)} | {r['passes']} |" for s,r in rows.items()]
    if pool:
        table.append('| Pooled, inverse variance on log rate ratio | '+cell(pool)+' | descriptive |')
    table += ['', '| Q11 source and words | Texts with change / texts | Sentences with change / sentences |',
              '|---|---:|---:|']
    for source, groups in decision['table'].items():
        for group, rates in groups.items():
            text, sent = rates['text'], rates['sentence']
            table.append(f"| {source} / {group} | {text['positive']}/{text['n']} | {sent['positive']}/{sent['n']} |")
    table += ['', '| Source / feeling word | Texts | No-change texts | No-change sentences | B/W disagree on change |',
              '|---|---:|---:|---:|---:|']
    for s,t in tables.items():
        table += [f"| {s} / {k} | {v['texts']} | {cell(v['textNoChange'])} | {cell(v['sentenceNoChange'])} | {cell(v['WChangeDisagreement'])} |" for k,v in t.items()]
    estimate={'byWord':tables,'ratio':rows,'pooledRatio':pool,'Q11':decision,'both':both,'teacher':gate}
    save_json(output/'receipt.json',{'card':'TP40','status':'complete','protocolPin':PACKET,'productionAdmission':False,
        'ledger':ledger,'sources':{**{j:sha256(t[0]/'receipt.json') for j,t in terminals.items()},'manifest':MANIFEST,
                                    'privateChangeScoresPin':sha256(path)},
        'question':'Which feeling words tend to describe a situation that stays the same?',
        'data':'Two readers judged every sentence in 24,850 chat situations and 6,050 recalled events. One changed sentence counts as a change for the whole report.',
        'scope':'The benchmark measures a model’s definition of change. The words were fixed after the earlier sentence-level miss and before the word breakdown.',
        'estimate':estimate,'interval':{'unit':'writer within source','draws':2000,'ratio':'conservative lower bound if any unresolved texts'},
        'bar':'Standing words have at least twice the no-change rate in each source, with the interval above one. Q11 separately requires 85% change on other words in each source.',
        'verdict':outcome,'table':table})
