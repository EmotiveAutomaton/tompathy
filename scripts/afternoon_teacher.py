"""BS. Serialize the third teacher attempt behind the registered Spark tail."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path('/home/agent/tompathy-open/person-teacher-20261121')
OLD=ROOT.parent/'word-table-20261120'
REGISTERED='ff2e4dd0f02fb9488e35ce4acf580ce0bad73d53'
C=('qwen3.5:122b','8b9d11d807c57feb1e2ecb0d6cbf40334c37dcc3523bed5540af4f927f112a37')
BOOT='17b89c07-ca2a-4328-be23-1079536e9232'
Q11_PIN='eef869091aa69c30cb69a75a7157adae5a5c42239748c15d5d31f8e8a1a82860'
Q11_INPUT='e118aae689fb4127edb09ae142848de4de1c21b3e9553a131cda239f403d05dd'
Q4_INPUT='d9e0477c742734bd546f9e928f48c3f3a6e372fb176195a09702c36d95dd84e4'
ADDENDUM='7832e75039bdb5185b3c9bc57684bc30332df41f64e7cb416773262eae5715dc'
HOME=ROOT/'bs'
GPU=Path('/home/agent/gpu.lock')


def read(p):
    return json.loads(p.read_bytes())


def pin(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def checked(p,expected):
    if pin(p)!=expected:raise ValueError('Bound file differs: '+p.name)
    return read(p)


def native_gone(owner):
    if owner['bootId']!=BOOT or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=BOOT:
        raise ValueError('Host identity changed')
    proc=Path('/proc')/str(owner['pid'])/'stat'
    return not proc.exists() or proc.read_text().rsplit(') ',1)[1].split()[19]!=str(owner['startTicks'])


def terminal(job):
    p=ROOT/'jobs'/job
    r=checked(p/'receipt.json',read(p/'complete.json')['receiptPin'])
    rel=read(p/'released.json')
    if not(rel['owner']==r['owner']==read(p/'owner.json') and rel['nativeExitCode']==0 and rel['descriptorClosed'] and native_gone(r['owner'])):
        raise ValueError('Unverified predecessor '+job)
    return r


def stopped(job):
    return any(p.exists() for p in (OLD/'STOP',ROOT/'STOP',HOME/'STOP',ROOT/'jobs'/job/'STOP'))


def pilot_projection(elapsed,seconds,total):
    return elapsed+(total-100)*seconds/100


def setup():
    directory=Path(__file__).resolve().parent
    if directory.parent!=ROOT/'code' or not re.fullmatch('[a-f0-9]{40}',directory.name):
        raise ValueError('Unregistered code directory')
    cfg=read(HOME/'registration.json')
    if cfg['commit']!=directory.name or pin(Path(__file__))!=cfg['scriptPin'] or cfg['packetPin']!=ADDENDUM:
        raise ValueError('Afternoon registration changed')
    deps=ROOT/'code'/REGISTERED
    for k,h in cfg['morningCodePins'].items():
        if pin(deps/k)!=h:raise ValueError('Morning runtime differs: '+k)
    sys.path.insert(0,str(deps))
    import person_teacher_lane as morning
    morning.validate(ROOT)
    lane=morning.lane
    lane.settings()
    # This process can use the larger reader only for these two explicitly registered jobs.
    lane.MODELS['C']=C
    q=terminal('Q11')
    if pin(ROOT/'jobs/Q11/receipt.json')!=Q11_PIN or checked(ROOT/'jobs/Q11/decision.json',q['decisionPin'])['passes']:
        raise ValueError('Prior B outcome differs')
    lane.core.read_model(*C)
    for p,h,n in [(ROOT/'inputs/Q11.json',Q11_INPUT,5014),(OLD/'inputs/Q4.json',Q4_INPUT,28000)]:
        rows=checked(p,h)
        if len(rows)!=n or len({r['id'] for r in rows})!=n:raise ValueError('Roster mismatch')
    return cfg,lane,morning


class TimingStop(RuntimeError):
    pass


def worker(job,cfg,lane,morning):
    out=ROOT/'jobs'/job
    with lane.lease(GPU):
        if stopped(job):raise RuntimeError('Owner STOP')
        # A crash with existing work requires exact exit review before any continuation.
        if job=='Q15' and not (ROOT/'jobs/Q14/released.json').is_file():raise ValueError('Q14 pending')
        out.mkdir(exist_ok=False)
        owner={**lane.identity(),'job':job,'at':lane.now(),'lock':str(GPU),'commit':cfg['commit']}
        lane.write(out/'owner.json',owner)
        receipt={'job':job,'owner':owner,'status':'running','packetPin':ADDENDUM,'priorB':Q11_PIN,'attempt':3,'readersOnAmendedCheck':2}
        lane.write(out/'receipt.json',receipt)
        try:
            if job=='Q15':
                previous=terminal('Q14')
                decision=checked(ROOT/'jobs/Q14/decision.json',previous['decisionPin'])
                receipt['q14Source']=pin(ROOT/'jobs/Q14/receipt.json')
                if previous['status']!='complete' or decision['passes'] is not True:
                    receipt.update(status='blocked',reason='No passing Q14 decision')
            if receipt['status']=='running':
                h=Q11_INPUT if job=='Q14' else Q4_INPUT
                rows=checked(ROOT/'inputs/Q11.json' if job=='Q14' else OLD/'inputs/Q4.json',h)
                bind={'job':job,'block':job,'inputPin':h,'packetPin':ADDENDUM,'commit':cfg['commit']}
                clock=time.monotonic()
                with lane.core.Guard(out,8) as thermal:
                    class Checks:
                        timed=False
                        def check(self):
                            thermal.check()
                            if stopped(job):raise RuntimeError('Owner STOP')
                            if job=='Q14' and not self.timed and (out/'progress.json').is_file():
                                progress=read(out/'progress.json')
                                if progress['rows']>=100:
                                    if progress['rows']!=100:raise ValueError('Missed timing boundary')
                                    elapsed=time.monotonic()-clock
                                    projection=pilot_projection(elapsed,progress['secondsPer100'],len(rows))
                                    lane.write(out/'first100.json',dict(progress,elapsed=elapsed,projectedSeconds=projection,limit=28800))
                                    self.timed=True
                                    if projection>28800:raise TimingStop('First 100 project beyond eight hours')
                    checks=Checks()
                    t=morning.teacher
                    receipt['summary']=lane.rate(ROOT,out,rows,'C',job,bind,checks,template=(t.PROMPT,t.SCHEMA['properties'],t.valid_label,False))
                    checks.check()
                if job=='Q14':
                    values=[]
                    for i,row in enumerate(rows):
                        prediction=read(out/'C'/f'row-{i:06d}.json')
                        if prediction['binding']!=receipt['summary']['binding'] or prediction['index']!=i or prediction['id']!=row['id']:
                            raise ValueError('Prediction order or binding mismatch')
                        values.append(prediction['values'])
                    old=checked(OLD/'jobs/Q3/teacher-gate.json',morning.PRIOR_GATE)
                    decision=morning.check_gate(rows,values,old)
                    lane.write(out/'decision.json',dict(decision,amendment='BS',reader='C',attempt=3,readersOnAmendedCheck=2))
                    receipt['decisionPin']=pin(out/'decision.json')
                receipt['status']='complete'
        except TimingStop as exc:
            receipt.update(status='timing-stop',reason=str(exc))
            lane.write(out/'decision.json',{'passes':None,'status':'timing-stop','reason':str(exc)})
            receipt['decisionPin']=pin(out/'decision.json')
        except Exception as exc:
            receipt.update(status='failed',reason=str(exc))
            lane.write(out/'receipt.json',receipt);lane.write(out/'failed.json',{'receiptPin':pin(out/'receipt.json')})
            raise
        receipt['ended']=lane.now()
        lane.write(out/'receipt.json',receipt)
        lane.write(out/'complete.json',{'receiptPin':pin(out/'receipt.json')})


def serve(cfg,lane):
    with lane.lease(HOME/'dispatcher.lock'):
        lane.write(HOME/'dispatcher.json',{**lane.identity(),'commit':cfg['commit'],'at':lane.now()})
        while not (ROOT/'tail/complete.json').exists():
            if stopped('Q14'):return
            time.sleep(60)
        if terminal('Q12')['status']!='complete' or terminal('Q7')['status']!='blocked':
            raise ValueError('Earlier queue has unexpected terminal state')
        if read(ROOT/'tail/complete.json')['Q7']!=pin(ROOT/'jobs/Q7/receipt.json'):
            raise ValueError('Tail boundary differs')
        for job in ('Q14','Q15'):
            while True:
                if stopped(job):return
                p=ROOT/'jobs'/job
                if p.exists():raise ValueError('Preserve prior attempt for review: '+job)
                proc=subprocess.Popen([sys.executable,__file__,job])
                code=proc.wait()
                if code==74 and not p.exists():
                    time.sleep(90);continue
                owner=read(p/'owner.json')
                if owner['pid']!=proc.pid or not native_gone(owner):raise ValueError('Child identity or exit differs')
                lane.write(p/'released.json',{'owner':owner,'descriptorClosed':True,'nativeExitCode':code,'at':lane.now()})
                if code:raise RuntimeError('Preserved engineering failure in '+job)
                break
        lane.write(HOME/'complete.json',{'Q14':pin(ROOT/'jobs/Q14/receipt.json'),'Q15':pin(ROOT/'jobs/Q15/receipt.json')})


if __name__=='__main__':
    action,=sys.argv[1:]
    cfg,lane,morning=setup()
    if action=='check':print('Verified committed runtime, teacher inputs and installed C digest.')
    elif action=='serve':serve(cfg,lane)
    elif action in ('Q14','Q15'):
        try:worker(action,cfg,lane,morning)
        except lane.Busy:sys.exit(74)
    else:raise ValueError('Unknown BS action')
