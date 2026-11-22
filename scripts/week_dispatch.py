"""Serial Spark handoff after verified local acceptance of the previous packet."""
import subprocess
import sys
import time
from pathlib import Path

from week_spark import ROOT, PREVIOUS
from word_table_lane import Busy, identity, lease, now, pin, read, write


def gone(owner):
    if Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=owner['bootId']:
        raise RuntimeError('Boot changed. Verify the handoff manually.')
    path=Path(f"/proc/{int(owner['pid'])}/stat")
    try:
        ticks=path.read_text().rsplit(')',1)[1].split()[19]
    except FileNotFoundError:
        return True
    return ticks!=str(owner['startTicks'])


def serve(registration):
    cfg=read(ROOT/'registration.json')
    if pin(ROOT/'registration.json')!=registration:
        raise ValueError('Registration changed')
    def guard():
        if any((p/'STOP').exists() for p in (ROOT,PREVIOUS,PREVIOUS/'cb')) or time.time()>=cfg['endUTC']:
            raise RuntimeError('Stop or week deadline')
    with lease(ROOT/'dispatch.lock'):
        write(ROOT/'dispatcher.json',dict(identity(),registration=registration,at=now()))
        while not (ROOT/'earlier-accepted.json').is_file():
            guard()
            time.sleep(45)
        ack=read(ROOT/'earlier-accepted.json')
        if (ack['registration']!=registration or set(ack['localReadoutPins'])!={'TP44','TP43-read'}
            or ack['cbTerminalPin']!=pin(PREVIOUS/'cb/complete.json')):
            raise ValueError('Earlier studies require verified terminal receipts')
        for job in ('Q20','Q21','Q22'):
            out=ROOT/'jobs'/job
            if out.exists():
                raise FileExistsError('Prior job requires verification: '+job)
            while True:
                guard()
                proc=subprocess.Popen([sys.executable,str(Path(__file__).with_name('week_spark.py')),job,registration])
                code=proc.wait()
                if code==74 and not out.exists():
                    time.sleep(45)
                    continue
                break
            owner=read(out/'owner.json')
            if owner['pid']!=proc.pid or owner['registration']!=registration or not gone(owner):
                raise ValueError('Unexpected worker identity at handoff')
            while True:
                try:
                    with lease(Path('/home/agent/gpu.lock')):
                        write(out/'released.json',dict(owner=owner,nativeExitCode=code,descriptorClosed=True,at=now()))
                    break
                except Busy:
                    guard()
                    time.sleep(45)
            if code or read(out/'complete.json')['sourceReceiptPin']!=pin(out/'receipt.json'):
                raise RuntimeError('Preserve and review '+job)
        write(ROOT/'first-three-complete.json',dict(at=now(),registration=registration))


if __name__=='__main__':
    serve(sys.argv[1])
