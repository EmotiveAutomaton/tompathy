"""Wait on remote releases and run the eligible private CPU readouts serially."""
import json
import msvcrt
import os
import subprocess
import sys
import time
from pathlib import Path

from cb_inputs import pin
from cb_readout import save,verify_exit
from week_collect import LOCAL,ROOT,collect


def check():
    if ((LOCAL/'STOP').exists() or Path('.local/person-teacher/STOP').exists()
        or time.time()>=1795795200):
        raise RuntimeError('Stop or study deadline reached')


def transfer(job):
    if (LOCAL/(job+'-transfer.json')).is_file():
        return True
    process=subprocess.run(['ssh','-o','ConnectTimeout=12','-o','BatchMode=yes','spark',
                            f'test -f {ROOT.as_posix()}/jobs/{job}/released.json'],
                           capture_output=True,timeout=30)
    if process.returncode:
        return False
    result=collect(job)
    if result.get('failed'):
        raise RuntimeError('Review the released Spark failure '+job)
    return result['ready']


def run(card):
    out=LOCAL/(card+'-a')
    if (out/'failed.json').exists():
        raise RuntimeError('Preserve prior failed readout '+card)
    if not (out/'complete.json').exists():
        if Path('.local/bench/two-day-scoring.lock').exists():
            return False
        save(LOCAL/'readout-state.json',dict(pid=os.getpid(),stage=card))
        subprocess.run([sys.executable,'scripts/week_study.py',card,'a'],check=True)
    if json.loads((out/'complete.json').read_bytes())['sourceReceiptPin']!=pin(out/'receipt.json'):
        raise ValueError('Readout source changed')
    if not (out/'exit-verification.json').exists():
        save(out/'exit-verification.json',verify_exit(out))
    return True


def serve():
    with (LOCAL/'readout.lock').open('a+b') as f:
        f.seek(0)
        msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        save(LOCAL/'readout-state.json',dict(pid=os.getpid(),stage='waiting for Q20'))
        while True:
            check()
            if transfer('Q20') and run('TP45-profiles') and run('TP45-openings'):
                if transfer('Q21') and run('TP48') and run('TP45-table6') and transfer('Q22'):
                    save(LOCAL/'readout-state.json',dict(stage='opening, PRIDE and covariance readouts verified',
                                                        aggregateReviewRequired=True))
                    return
            time.sleep(120)


if __name__=='__main__':
    try:
        serve()
    except Exception as exc:
        save(LOCAL/'readout-error.json',dict(error=str(exc)))
        raise
