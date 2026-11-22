"""Wait for local predecessor verification, then release the waiting Spark queue once."""
import json
import msvcrt
import subprocess
import sys
import time
from pathlib import Path

from cb_inputs import BASE, pin
from cb_readout import stopped,verify_exit

WEEK=Path('.local/week-20261122')
REMOTE='/home/agent/tompathy-open/week-20261122'
OLD='/home/agent/tompathy-open/person-teacher-20261121'


def check_local():
    pubs={}
    for card,task in [('TP43','TP43-read'),('TP44','TP44')]:
        folder=BASE/task
        proof=folder/'exit-verification.json'
        public=Path('engine/validation')/f'readers-{card.lower()}-2026-11.json'
        if not proof.exists() or not public.exists():
            return None
        read=lambda p:json.loads(p.read_bytes())
        h=pin(folder/'receipt.json')
        if (h!=read(folder/'complete.json')['sourceReceiptPin'] or h!=read(public)['sourceReceiptPin']
            or read(proof)['releasePin']!=pin(folder/'released.json')):
            raise ValueError('Earlier source or release mismatch')
        verify_exit(folder)
        pubs[task]=h
    return pubs


def serve(registration):
    with (WEEK/'handoff.lock').open('a+b') as f:
        f.seek(0)
        msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        while not stopped() and not (WEEK/'STOP').exists():
            if time.time()>=1795795200:
                raise RuntimeError('Review the week deadline')
            local=check_local()
            if local:
                p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','spark',
                                  f'test -f {OLD}/cb/complete.json && sha256sum {OLD}/cb/complete.json'],
                                 capture_output=True,text=True,timeout=30)
                if p.returncode==0:
                    h=p.stdout.split()[0]
                    if len(h)!=64:
                        raise ValueError('Invalid CB terminal hash')
                    target=WEEK/'earlier-accepted.json'
                    data=dict(registration=registration,localReadoutPins=local,cbTerminalPin=h)
                    if target.exists() and json.loads(target.read_bytes())!=data:
                        raise ValueError('Conflicting previous handoff')
                    target.write_text(json.dumps(data),encoding='ascii')
                    subprocess.run(['scp',str(target),'spark:'+REMOTE+'/earlier-accepted.tmp'],check=True)
                    reply=subprocess.run(['ssh','spark',f'mv -n {REMOTE}/earlier-accepted.tmp {REMOTE}/earlier-accepted.json && sha256sum {REMOTE}/earlier-accepted.json'],
                                         check=True,capture_output=True,text=True)
                    if reply.stdout.split()[0]!=pin(target):
                        raise ValueError('Remote acknowledgement hash differs')
                    return
            time.sleep(60)


if __name__=='__main__':
    serve(sys.argv[1])
