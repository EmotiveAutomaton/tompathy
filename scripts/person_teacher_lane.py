"""November 21 local-disk GPU jobs. No model pulls or external storage."""
import argparse
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import tp31_teacher as teacher
import word_table_lane as lane

INPUT_PIN='c36d09d12d744fb9822979335fe8d4cc2b98726347b23e730ab2e40cf9869e3d'
PRIOR_GATE='e2fc8b715d5842619c8922d95ff89dce4ee6a5ce778ba54abf99d567744068a3'
ORDER={'workstation':['G4'],'spark':['Q11','Q4','Q12','Q13','Q7']}
read,write,pin=lane.read,lane.write,lane.pin


def check_gate(rows,labels,old):
    docs={}
    counts={}
    for item,value in zip(rows,labels,strict=True):
        group=(item['source'],item['standing'])
        doc=docs.setdefault((group,item['parent']),[])
        doc.append(value['change'] if value is not None else None)
        counts.setdefault(group,[]).append(doc[-1])
    table={}
    for source in ('ed','envent'):
        table[source]={}
        for subset in ('other','standing','all'):
            groups=[(source,x) for x in (False,True) if subset=='all' or x==(subset=='standing')]
            documents=[ys for (g,_),ys in docs.items() if g in groups]
            sentences=[y for g in groups for y in counts.get(g,[])]
            def measure(values):
                return {'n':len(values),'positive':sum(y is True for y in values),
                        'unknown':sum(y is None for y in values),'lowerRate':sum(y is True for y in values)/len(values) if values else None}
            text=[True if True in ys else None if None in ys else False for ys in documents]
            table[source][subset]={'text':measure(text),'sentence':measure(sentences)}
        if table[source]['all']['text']['n']!=1500:
            raise ValueError('Q11 requires 1,500 whole texts from each source')
    agreement=old['checks']['agreement']['passes']
    ceiling=old['checks']['knownGroups']['stack']['passes']
    passed=agreement and ceiling and all(table[s]['other']['text']['lowerRate']>=.85 for s in table)
    return {'passes':passed,'table':table,'oldAgreementPassed':agreement,'oldCeilingPassed':ceiling,
            'oldGatePin':PRIOR_GATE,'postMissAmendment':'BJ','originalGatePassed':old['checks']['qualifiesForStudent']}


def validate(root):
    cfg=read(root/'registration.json')
    code=Path(__file__).resolve().parent
    if code.name!=cfg['commit'] or any(pin(code/k)!=v for k,v in cfg['codePins'].items()):
        raise ValueError('Execution snapshot differs')
    if pin(root/'inputs/manifest.json')!=INPUT_PIN:
        raise ValueError('Roster registration differs')
    return cfg


def worker(root,old,job):
    cfg=validate(root)
    gpu='workstation' if os.name=='nt' else 'spark'
    if job not in ORDER[gpu]:
        raise ValueError('Wrong lane')
    role='W' if gpu=='workstation' else 'B'
    out=root/'jobs'/job
    lock=old/'gpu.lock' if os.name=='nt' else Path('/home/agent/gpu.lock')
    with lane.lease(lock):
        out.mkdir(parents=True,exist_ok=True)
        owner={**lane.identity(),'job':job,'lock':str(lock),'commit':cfg['commit'],'at':lane.now()}
        write(out/'owner.json',owner)
        receipt={'job':job,'status':'running','owner':owner,'manifestPin':INPUT_PIN}
        write(out/'receipt.json',receipt)
        try:
            guard_file=root/'jobs/Q11/decision.json'
            if job in ('Q4','Q7'):
                q=root/'jobs/Q11'
                if read(q/'complete.json')['receiptPin']!=pin(q/'receipt.json') or read(q/'receipt.json')['decisionPin']!=pin(guard_file):
                    raise ValueError('Unverified Q11 decision')
                receipt['decisionPin']=pin(guard_file)
                if not read(guard_file)['passes']:
                    receipt.update(status='blocked',reason='Q11 restated teacher check failed')
            if job=='Q13':
                receipt.update(status='deferred',reason='Copy-based ModernBERT training validation required; compiler probe alone is insufficient')
            if receipt['status']=='running':
                batches=(['Q11','Q12'] if job=='G4' else [job])
                hours=float('inf')
                if job=='Q4':
                    clock=out/'deadline.json'
                    if not clock.exists():write(clock,{'start':lane.now()})
                    elapsed=(datetime.now(UTC)-datetime.fromisoformat(read(clock)['start'])).total_seconds()/3600
                    hours=max(0,8-elapsed)
                with lane.core.Guard(out,hours) as thermal:
                    guard=lane.Checks(root,out,thermal)
                    for batch in batches:
                        guard.check()
                        if batch in ('Q4','Q7'):
                            entry=read(old/'queue.json')['jobs'][batch]
                            items,original=lane.check_entry(old,batch,entry)
                            input_pin=original['inputPin']
                        else:
                            p=root/'inputs'/(batch+'.json')
                            input_pin=read(root/'inputs/manifest.json')['files'][batch]
                            if pin(p)!=input_pin:raise ValueError('Changed sentence list')
                            items=read(p)
                        binding={'job':job,'block':batch,'inputPin':input_pin,'manifestPin':INPUT_PIN,'commit':cfg['commit']}
                        folder=out/batch
                        folder.mkdir(exist_ok=True)
                        template=(teacher.PROMPT,teacher.SCHEMA['properties'],teacher.valid_label,False)
                        receipt[batch]=lane.rate(root,folder,items,role,job,binding,guard,template=template)
                        if job=='Q11':
                            prior=old/'jobs/Q3/teacher-gate.json'
                            if pin(prior)!=PRIOR_GATE:raise ValueError('Original teacher result changed')
                            labels=[]
                            for i,item in enumerate(items):
                                row=read(folder/role/f'row-{i:06d}.json')
                                if row['id']!=item['id'] or row['index']!=i:raise ValueError('Unmatched sentence')
                                labels.append(row['values'])
                            write(guard_file,check_gate(items,labels,read(prior)))
                            receipt['decisionPin']=pin(guard_file)
                receipt['status']='complete'
            write(out/'receipt.json',receipt)
            write(out/'complete.json',{'receiptPin':pin(out/'receipt.json')})
        except lane.Pause as exc:
            receipt.update(status='paused',reason=str(exc))
            write(out/'receipt.json',receipt)
            return 75
        except Exception as exc:  # noqa: BLE001 -- preserve unexpected native worker failures
            receipt.update(status='failed',reason=str(exc))
            write(out/'receipt.json',receipt)
            write(out/'failed.json',{'receiptPin':pin(out/'receipt.json')})
            return 1
    return 0


def serve(root,old):
    cfg=validate(root)
    gpu='workstation' if os.name=='nt' else 'spark'
    with lane.lease(root/'dispatcher.lock'):
        write(root/'dispatcher.json',{**lane.identity(),'at':lane.now(),'commit':cfg['commit']})
        if gpu=='spark':
            source=read(old/'inputs/source-remaining.json')
            import importlib.metadata
            for name,version in source['packages'].items():
                if importlib.metadata.version(name)!=version:raise ValueError('Spark environment changed')
            for name,v in source['environmentPins'].items():
                if pin(Path('/srv/open/pins')/name)!=v:raise ValueError('Spark pins changed')
            while not (old/'jobs/Q6/released.json').exists():
                if (root/'STOP').exists():return
                time.sleep(45)
            q=old/'jobs/Q6'
            if (read(q/'released.json')['owner']!=read(q/'owner.json') or
                    not read(q/'released.json')['descriptorClosed'] or not (q/'complete.json').is_file()):
                raise RuntimeError('Review Q6 exit before proceeding')
        for job in ORDER[gpu]:
            out=root/'jobs'/job
            while not (out/'complete.json').exists():
                if (root/'STOP').exists() or (out/'STOP').exists() or (old/'STOP').exists():return
                if (out/'failed.json').exists():raise RuntimeError('Review preserved failure for '+job)
                child=subprocess.Popen([sys.executable,__file__,'worker',str(root),str(old),job])
                status=child.wait()
                if (out/'owner.json').exists() and (owner:=read(out/'owner.json'))['pid']==child.pid:
                    write(out/'released.json',{'owner':owner,'nativeExitCode':status,'at':lane.now(),'descriptorClosed':True})
                if status in (74,75):time.sleep(90)
                elif status:raise RuntimeError('Review '+job)
        write(root/'completed.json',{'at':lane.now(),'jobs':ORDER[gpu]})


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('action',choices=['serve','worker'])
    a.add_argument('root',type=Path)
    a.add_argument('old',type=Path)
    a.add_argument('job',nargs='?')
    args=a.parse_args()
    lane.settings()
    try:
        sys.exit(serve(args.root,args.old) if args.action=='serve' else worker(args.root,args.old,args.job))
    except lane.Busy:
        sys.exit(74)
