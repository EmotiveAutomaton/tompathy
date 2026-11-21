"""Verify the BS Spark terminal records using the frozen, size-capped morning importer."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from afternoon_report import append, pin, put, read

BASE=Path('.local/person-teacher')
COMMIT='a5b9d7c10cf780d6977c49b11c7c43e37d99b644'
TRANSFER='70a051e402c21a3ab0ac074cc4e814aa58da6614fec8f94c9a75df6d7d839c05'


def importer():
    # Freeze the same self-transmitting importer under the addendum's two job names and commit.
    p=Path(__file__).with_name('person_teacher_transfer.py')
    if pin(p)!=TRANSFER:raise ValueError('Registered transfer program changed')
    source=p.read_bytes()
    guard=b"if __name__=='__main__':"
    if source.count(guard)!=1:raise ValueError('Invalid frozen entry point')
    header,main=source.split(guard)
    config=f"COMMIT={COMMIT!r}\nROOTS={{j:'person-teacher-20261121' for j in ('Q14','Q15')}}\n"
    target=BASE/'bs-terminal-transfer.py'
    put(target,header+config.encode()+guard+main)
    return target


def file_job(job):
    d=BASE/('verified-spark-'+job+'-a')
    audit=read(BASE/(job+'-transfer-a.json'))
    receipt=read(d/'receipt.json')
    if (pin(d/'receipt.json')!=audit['sourceReceiptPin'] or not audit['nativeExited'] or
        not audit['priorFlockReleased'] or receipt['owner']['commit']!=COMMIT):
        raise ValueError('Incomplete native verification')
    stat=receipt['status']
    if stat=='failed':raise RuntimeError('Preserved engineering failure in '+job)
    output={'card':job,'ledger':'E-'+job+'-20261121','status':stat,'sourceReceiptPin':audit['sourceReceiptPin'],
            'packetPin':receipt['packetPin'],'productionAdmission':False}
    if job=='Q14':
        decision=read(d/'decision.json')
        if pin(d/'decision.json')!=receipt['decisionPin']:raise ValueError('Decision changed')
        timing=read(d/'first100.json')
        if timing['rows']!=100 or timing['total']!=5014 or (timing['projectedSeconds']>28800)!=(stat=='timing-stop'):
            raise ValueError('Timing boundary inconsistent')
        output.update(decision=decision,timing={k:timing[k] for k in ('rows','total','valid','projectedSeconds')})
        data='Reader C was assigned the same 1,500 chat situations and 1,500 recalled events used for B. Any changed sentence counts as a changed report.'
        if stat=='complete':
            info=receipt['summary']
            if info['rows']!=5014 or info['modelPin']!='8b9d11d807c57feb1e2ecb0d6cbf40334c37dcc3523bed5540af4f927f112a37':
                raise ValueError('Incomplete reader C run')
            groups=[decision['table'][k]['other']['text'] for k in ('ed','envent')]
            passed=decision['oldAgreementPassed'] and decision['oldCeilingPassed'] and all(g['positive']/g['n']>=.85 for g in groups)
            if passed!=decision['passes']:raise ValueError('Decision inconsistent with exact denominators')
            rates=[f"{g['positive']}/{g['n']} ({g['positive']/g['n']:.1%})" for g in groups]
            verdict=('Pass. ' if passed else 'Miss. ')+f"Chat {rates[0]}, recalled events {rates[1]}."
            verdict+=' Q15 is eligible.' if passed else ' TP31 stays blocked; no further reader will be tried.'
        else:verdict='Timing stop after the first 100. No teacher verdict.'
        scope='Second reader on the amended bar at the third teacher attempt. Multiple chances weaken the evidence of a narrow pass. No human change labels.'
        bar='85% whole-report change on the other words in each source; earlier agreement and ceiling checks retained.'
    else:
        q=read(BASE/'verified-spark-Q14-a/receipt.json')
        if receipt['q14Source']!=pin(BASE/'verified-spark-Q14-a/receipt.json'):raise ValueError('Wrong Q14 source')
        decision=read(BASE/'verified-spark-Q14-a/decision.json')
        if (stat=='complete')!=(q['status']=='complete' and decision['passes'] is True):raise ValueError('Q15 dependency differs')
        data='The registered 28,000 teacher sentences following the first 2,000.'
        if stat=='complete':
            summary=receipt['summary'];output.update(rows=summary['rows'],valid=summary['valid'])
            if summary['rows']!=28000:raise ValueError('Incomplete Q15 roster')
            verdict=f"Reader C returned {summary['valid']:,} valid labels in 28,000 sentences."
        else:verdict='Blocked by Q14. No new teacher sentences were scored.'
        scope='Teacher-generated labels. Student accuracy requires a separate evaluation.'
        bar='Q15 runs only after a passing Q14 decision.'
    public=Path('engine/validation')/('readers-'+job.lower()+'-bs-2026-11.json')
    put(public,(json.dumps(output,indent=2,allow_nan=False)+'\n').encode())
    sheet=Path('docs/exchange/result-sheets')/(job+'-BS.md')
    put(sheet,('\n\n'.join(['# '+job+' reader C',data,verdict,bar,scope,f'[Aggregate {output["ledger"]}](../../../{public.as_posix()})'])+'\n').encode())
    append('engine/validation/EVIDENCE_LEDGER.jsonl',{'id':output['ledger'],'date':'2026-11-21','question':'Can reader C supply teacher labels under BS?',
           'data':data,'estimate':output,'interval':'Exact fixed-panel counts.','bar':bar,'verdict':verdict,'limit':scope,'claims':['M2'],'family':'BS teacher'})
    for path,ref in [(Path('STATUS.md'),'docs/exchange/'),(Path('docs/ENGINE_SCOREBOARD.md'),'exchange/'),
                     (Path('docs/exchange/THEORY_RETURN_2026-11-22.md'),''),(Path('docs/ENGINE_PERSON_TEACHER_2026-11-21.md'),'exchange/')]:
        marker='<!-- landed '+output['ledger']+' -->'
        if marker not in path.read_text(encoding='utf8'):
            with path.open('a',encoding='utf8') as f:f.write(f'\n**{job}.** {verdict} [{output["ledger"]}]({ref}result-sheets/{sheet.name}).\n\n{marker}\n')


def main():
    import msvcrt
    transfer=importer()
    with (BASE/'bs-collector.lock').open('a+b') as lock:
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        for job in ('Q14','Q15'):
            phase={'job':job,'pid':os.getpid(),'status':'waiting for verified release'}
            (BASE/'bs-collector.json').write_text(json.dumps(phase))
            while not (BASE/'STOP').exists() and not Path('.local/word-table/STOP').exists():
                p=subprocess.run([sys.executable,str(transfer),job],capture_output=True)
                if p.returncode:
                    if b'exit status 255' not in p.stderr:raise RuntimeError(p.stderr.decode(errors='replace')[-1500:])
                elif json.loads(p.stdout)['verified']:
                    file_job(job)
                    break
                time.sleep(300)
            else:return
        (BASE/'bs-collector.json').write_text(json.dumps({'status':'both terminal and filed','pid':os.getpid()}))


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        (BASE/'bs-collector-error.json').write_text(json.dumps({'pid':os.getpid(),'error':str(exc)}))
        raise
