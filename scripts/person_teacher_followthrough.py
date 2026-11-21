"""Serial local readouts after exact GPU terminal signals. No publication or model downloads."""
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import person_teacher_transfer as transfer

ROOT=Path('.local/person-teacher')
OLD=Path('.local/word-table')
PY=Path('.local/readers-venv/Scripts/python.exe').resolve()
PACKET='TOMPATHY_0.3_ENGINE_PERSON_AND_TEACHER_PACKET_2026-11-21.md'
TRANSFER_COMMIT='e60e49394a0425539ca2f217089e476716968f62'
CARDS={'TP39':('tp33-bk-a','tp39-a'),'TP40':('tp39-a','tp40-a'),'TP39-change':('tp40-a','tp39-change-a')}
SHEETS=Path('docs/exchange/result-sheets')
now=lambda:datetime.now(UTC).isoformat()


def stopped():
    return (ROOT/'STOP').exists() or (ROOT/'local-followthrough.STOP').exists() or (OLD/'STOP').exists()


def sources_frozen():
    source=Path('scripts/person_teacher_transfer.py')
    tracked=subprocess.check_output(['git','show',TRANSFER_COMMIT+':'+source.as_posix()])
    if tracked.replace(b'\r\n',b'\n')!=source.read_bytes().replace(b'\r\n',b'\n'):
        raise ValueError('Remote verifier differs from its committed program')
    for name,pin in transfer.read(ROOT/'readout-registration.json')['files'].items():
        if transfer.pin(Path(name))!=pin:
            raise ValueError('Review changed readout dependency: '+name)


def phase(job,state):
    p=ROOT/'local-followthrough.json'
    temp=p.with_suffix('.tmp')
    temp.write_text(json.dumps({'at':now(),'job':job,'state':state,'pid':os.getpid()}),encoding='utf8')
    temp.replace(p)


def append_record(path,marker,message):
    old=path.read_text(encoding='utf8')
    if marker in old:
        return
    with path.open('a',encoding='utf8') as out:
        out.write('\n'+message.rstrip()+'\n\n'+marker+'\n')


def record(card,verdict,ledger):
    relative='result-sheets/'+card+'.md'
    marker='<!-- person-teacher landed '+ledger+' -->'
    for path,ref in [(Path('STATUS.md'),'docs/exchange/'+relative),(Path('docs/ENGINE_SCOREBOARD.md'),'exchange/'+relative),
                     (Path('docs/ENGINE_PERSON_TEACHER_2026-11-21.md'),'exchange/'+relative),
                     (Path('docs/exchange/THEORY_RETURN_2026-11-22.md'),relative)]:
        append_record(path,marker,f'**{card} completed.** {verdict} [{ledger}]({ref}).')


def q11_report():
    root=ROOT/'verified-spark-Q11-a'
    audit=transfer.read(ROOT/'Q11-transfer-a.json')
    receipt=transfer.read(root/'receipt.json')
    if (audit['status']!='complete' or transfer.pin(root/'decision.json')!=receipt['decisionPin']
            or audit['sourceReceiptPin']!=transfer.pin(root/'receipt.json')):
        raise ValueError('Verified terminal Q11 decision required')
    decision=transfer.read(root/'decision.json')
    ledger='E-TP40-Q11-20261121'
    row={s:d['other']['text'] for s,d in decision['table'].items()}
    ok=bool(decision['oldAgreementPassed'] and decision['oldCeilingPassed'] and all(
        cell['positive']/cell['n']>=.85 for cell in row.values()))
    if ok!=decision['passes'] or decision['originalGatePassed']:
        raise ValueError('Q11 decision and original check are inconsistent')
    verdict=('Pass. ' if ok else 'Miss. ')+', '.join(f"{s}: {v['positive']}/{v['n']} ({v['lowerRate']:.1%})"
                                                    for s,v in row.items())+'.'
    data='One reader judged every sentence of 1,500 chat situations and 1,500 recalled events. We counted a report as changed when any of its sentences described change.'
    bar='At least 85% of non-standing-word texts in each source, alongside the filed agreement and question-site checks.'
    scope='The curator changed the unit and word condition after the original sentence-level miss. No human change labels.'
    public=Path('engine/validation/readers-change-teacher-q11-2026-11.json')
    transfer.save(public,{'schema':'person-teacher-Q11-1','ledger':ledger,'sourceReceiptPin':audit['sourceReceiptPin'],
        'decisionPin':receipt['decisionPin'],'decision':decision,'productionAdmission':False,'scope':scope})
    lines=['# Does reader B meet the amended teaching check?','',data,'',verdict,'',
           '| Source and words | Texts with change | Sentences with change |','|---|---:|---:|']
    for s,groups in decision['table'].items():
        for g,d in groups.items():
            lines.append(f"| {s} / {g} | {d['text']['positive']}/{d['text']['n']} | {d['sentence']['positive']}/{d['sentence']['n']} |")
    sheet=SHEETS/'TP40-Q11.md'
    formatted='\n'.join([*lines,'',bar,'',scope,'',f'[{ledger}](../../../{public.as_posix()})',''])
    if sheet.exists() and sheet.read_text(encoding='utf8')!=formatted:
        raise ValueError('Preserve prior Q11 sheet')
    sheet.write_text(formatted,encoding='utf8')
    sys.path.insert(0,str(Path('engine').resolve()))
    from tompathy_engine.eval.evidence import append
    append('engine/validation/EVIDENCE_LEDGER.jsonl',{'id':ledger,'date':'2026-11-21',
        'question':'Does B meet the restated whole-report teaching check?','data':data,
        'estimate':{'sourceReceiptPin':audit['sourceReceiptPin'],'rates':row},
        'interval':{'method':'Exact registered 3,000-text panel; no interval in gate.'},
        'bar':bar,'verdict':verdict,'limit':scope,'claims':['M2'],'family':'Amended TP31 check, TP40 Q11'})
    record('TP40-Q11',verdict,ledger)


def launch_card(card):
    previous,slug=CARDS[card]
    job=OLD/slug
    ledger='E-'+card.upper()+'-20261121'
    if not (job/'complete.json').is_file():
        if job.exists():
            raise ValueError('Preserve started or failed output for review: '+slug)
        while True:
            if stopped():
                return
            result=subprocess.run([PY,OLD/'cpu-admission.py',previous,slug],capture_output=True,check=True)
            if json.loads(result.stdout)['smallEligible']:
                break
            phase(card,'waiting for counted admission')
            time.sleep(1800)
        sources_frozen()
        args=[PY,'scripts/engine-readers-job.py','--sounding-line','E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line',
              '--bundle','.local/preflight-2026-11-15','--corpus','.local/readers/data/crowd-enVent2023',
              '--card',card,'--hours','2','--output',job,'--study-protocol',PACKET,'--ledger-row',ledger]
        if card=='TP39-change':
            args+=['--primary-job',OLD/'tp40-a']
        proc=subprocess.Popen(args)
        phase(card,'guarded scorer started')
        while proc.poll() is None and not (job/'owner.json').is_file():
            time.sleep(1)
        if proc.poll() is None and (job/'owner.json').is_file() and not (job/'released.json').exists():
            checked=subprocess.run([PY,'.local/readers/verify-job.py',job],check=False)
            if checked.returncode and proc.poll() is None and not (job/'released.json').is_file():
                raise ValueError('CPU startup ownership requires review')
        code=proc.wait()
        if (job/'released.json').is_file() and not (job/'exit-verification.json').exists():
            subprocess.run([PY,'.local/readers/verify-job.py',job,'--exit'],check=True)
        if code or not (job/'complete.json').is_file():
            raise ValueError('Preserved CPU engineering or resource stop: '+slug)
    elif not (job/'exit-verification.json').exists():
        subprocess.run([PY,'.local/readers/verify-job.py',job,'--exit'],check=True)
    subprocess.run([PY,'scripts/person_teacher_land.py',job],check=True)
    receipt=transfer.read(job/'receipt.json')
    record(card,receipt['verdict'],ledger)


def wait_job(job):
    phase(job,'waiting for exact terminal release')
    while not stopped():
        sources_frozen()
        try:
            ready=transfer.fetch(job)
        except subprocess.CalledProcessError as exc:
            if exc.returncode!=255:
                raise
            phase(job,'Spark connection interrupted; waiting for reconnection')
            time.sleep(240)
            continue
        if ready:
            base=OLD if job=='Q6' else ROOT
            audit=transfer.read(base/(job+'-transfer-a.json'))
            if audit['status']=='failed':
                raise ValueError('Preserved terminal failure in '+job)
            return True
        time.sleep(240)
    return False


def main():
    import msvcrt
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key]='2'
    os.environ['MPLCONFIGDIR']=str(ROOT.resolve())
    with (ROOT/'local-followthrough.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK,1)
        try:
            if not wait_job('Q6'):
                return
            launch_card('TP39')
            if not wait_job('Q11'):
                return
            q11_report()
            if not wait_job('Q4') or not wait_job('Q12') or not wait_job('G4'):
                return
            launch_card('TP40')
            if stopped():
                return
            launch_card('TP39-change')
            for job in ('Q13','Q7'):
                if not wait_job(job):
                    return
            phase('November 21 local readouts','terminal; review return and any downstream prerequisites')
        except Exception as exc:
            phase('review required',f'{type(exc).__name__}: {exc}')
            raise


if __name__=='__main__':
    main()
