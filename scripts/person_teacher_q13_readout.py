"""Land the optional local-copy rung after both its terminal export and earlier CPU readouts."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import person_teacher_followthrough as follow
import person_teacher_q13_export as export

PY=follow.PY
JOB=follow.OLD/'q13-modernbert-readout-a'


def landing():
    sys.path.insert(0,str(Path('engine').resolve()))
    from tompathy_engine.eval.evidence import append
    from tompathy_engine.eval.readers.reporting import OUTPUTS, land
    from tompathy_engine.packs.registry import sha256
    plan=export.read(JOB/'plan.json')
    for k,v in plan['snapshotFiles'].items():
        if sha256(JOB/'code'/k)!=v:
            raise ValueError('Frozen CPU readout changed')
    for k,v in plan['auxiliaryInputs'].items():
        if sha256(JOB/k)!=v:
            raise ValueError('Frozen protocol changed')
    public=Path('engine/validation')/OUTPUTS['G2-modernbert']
    r=land(JOB,public)
    if r['sourceReceiptPin']!=sha256(JOB/'receipt.json'):
        raise ValueError('Wrong public source')
    c=next(iter(r['rungs'].values()))['comparison']
    verdict=('Every larger-encoder threshold passed.' if c['passesAllThree'] else
             'The larger encoder missed the all-seeds rule.' if c['allThreeMeasured'] else
             'Incomplete seed coverage gives no all-seeds verdict.')
    question='Did the largest encoder recover the assigned word groups more accurately?'
    data='We compared the larger encoder with the frozen reader using the same saved forecasts and writer-word scoring rule used for the earlier rungs.'
    bar='Gain of at least .02 on mean AUC and CARE AUC of at least .70 on each of three registered seeds.'
    lines=['# '+question,'',data,'',verdict,'','| Seed | Mean AUC | Gain | CARE AUC |','|---|---:|---:|---:|']
    for k,v in c['perSeed'].items():
        lines.append(f"| {k} | {v['mean']:.4f} | {v['gain']:+.4f} | {v['care']:.4f} |")
    sheet=follow.SHEETS/'G2-modernbert.md'
    sheet.write_text('\n'.join([*lines,'',bar,'',r['scope'],'',f"[{r['ledger']}](../../../{public.as_posix()})",'']),encoding='utf8')
    append('engine/validation/EVIDENCE_LEDGER.jsonl',{'id':r['ledger'],'date':follow.now()[:10],
        'question':question,'data':data,'estimate':{'sourceReceiptPin':r['sourceReceiptPin'],'seeds':c},
        'interval':{'definition':'Repeated fits on common reports, full seed range displayed.'},
        'bar':bar,'verdict':verdict,'limit':r['scope'],'claims':['M1'],'family':'ModernBERT registered rung'})
    follow.record('G2-modernbert',verdict,r['ledger'])


def main():
    import msvcrt
    for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
        os.environ[name]='2'
    root=follow.ROOT
    cfg=export.read(root/'q13-readout-registration.json')
    for k,v in cfg['files'].items():
        if export.pin(Path(k))!=v:
            raise ValueError('Optional readout registration differs')
    with (root/'q13-readout.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        state=root/'q13-readout-state.json'
        def phase(s):
            p=state.with_suffix('.tmp')
            p.write_text(json.dumps({'state':s,'pid':os.getpid(),'at':follow.now()}),encoding='utf8')
            p.replace(state)
        try:
            phase('waiting for earlier local CPU readouts and terminal optional rung')
            while not (follow.OLD/'tp39-change-a/exit-verification.json').exists():
                if follow.stopped():return
                time.sleep(240)
            while not follow.stopped():
                try:
                    r=export.fetch()
                except subprocess.CalledProcessError as exc:
                    if exc.returncode!=255:raise
                    time.sleep(240)
                    continue
                if r.get('copyReview') or r.get('failed'):
                    phase('optional job stopped; preserve original attempt for review')
                    return
                if r['ready']:break
                time.sleep(240)
            else:
                return
            phase('verified compact forecasts; awaiting counted admission')
            while not (JOB/'complete.json').exists():
                if follow.stopped():return
                if JOB.exists():raise ValueError('Preserve existing partial readout')
                checked=subprocess.run([PY,follow.OLD/'cpu-admission.py','tp39-change-a',JOB.name],capture_output=True,check=True)
                if json.loads(checked.stdout)['smallEligible']:break
                time.sleep(1800)
            for k,v in cfg['files'].items():
                if export.pin(Path(k))!=v:
                    raise ValueError('Optional readout registration changed while waiting')
            if not (JOB/'complete.json').exists():
                child=subprocess.Popen([PY,'scripts/engine-readers-job.py',*cfg['args']])
                while child.poll() is None and not (JOB/'owner.json').exists():
                    time.sleep(1)
                if child.poll() is None and not (JOB/'released.json').exists():
                    subprocess.run([PY,'.local/readers/verify-job.py',JOB],check=True)
                status=child.wait()
                if (JOB/'released.json').exists():
                    subprocess.run([PY,'.local/readers/verify-job.py',JOB,'--exit'],check=True)
                if status:raise ValueError('Preserved optional readout failure')
            landing()
            phase('landed')
        except Exception as exc:
            phase('review required: '+str(exc))
            raise


if __name__=='__main__':
    main()
