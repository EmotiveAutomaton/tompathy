"""Serial, counted private CB readouts; review the native release before aggregate landing."""
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from cb_inputs import BASE, pin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
FROZEN = BASE/'frozen-b'
TASKS = ('TP43-all','TP44','TP43-read')

def read(path):
    return json.loads(path.read_bytes())


def save(path,data):
    from tompathy_engine.eval.back_half.reporting import save_json
    save_json(path,data)


def stopped():
    return any(p.exists() for p in (BASE/'STOP', BASE.parent/'STOP', Path('.local/word-table/STOP')))


def verify_exit(out):
    sys.path.insert(0,'E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line')
    from runners.stage9.process_identity import native_identity
    owner = read(out/'owner.json')
    native = owner['native']
    release = read(out/'released.json')
    for _ in range(30):
        alive = native_identity(native['pid'])
        if not alive or alive['created_ticks']!=native['created_ticks']:
            break
        time.sleep(1)
    if (release['native'] != native or (alive and alive['created_ticks']==native['created_ticks']) or
        owner['output'] != str(out.resolve())):
        raise ValueError('Native readout exit differs')
    for path in (Path(owner['lease']),Path('.local/bench/two-day-scoring.lock')):
        if path.is_file() and read(path).get('native')==native:
            raise ValueError('Original CPU lease still held')
    return dict(owner=native, releasePin=pin(out/'released.json'),verifiedAt=datetime.now(UTC).isoformat())


def score(task):
    import importlib.util
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard
    benchmark_priority(2)
    out=BASE/task
    out.mkdir(exist_ok=False)
    spec=importlib.util.spec_from_file_location('counted',ROOT/'scripts/engine-two-day-job.py')
    counted=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    deadline=time.monotonic()+8*3600
    def check():
        guard()
        if stopped() or (out/'STOP').exists() or time.monotonic()>=deadline:
            raise RuntimeError('Readout stop/deadline reached')
    try:
        with counted.lease(Path('E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line'),out,card='ToMpathy-'+task):
            from cb_tables import blog_tables
            from cb_isear_tables import tables
            check()
            estimate=tables(check) if task=='TP44' else blog_tables(task=='TP43-read',check)
            save(out/'receipt.json',dict(task=task,status='complete',registeredInputs=pin(BASE/'inputs.json'),
                 frozenResult=pin(FROZEN/'complete.json'),code={name:pin(Path(__file__).with_name(name))
                 for name in ('cb_readout.py','cb_isear_tables.py','cb_tables.py','cb_features.py')},estimate=estimate))
            save(out/'complete.json',dict(sourceReceiptPin=pin(out/'receipt.json')))
    except Exception as exc:
        save(out/'failed.json',dict(error=str(exc)))
        raise


def serve():
    import msvcrt
    from cb_transfer import fetch
    def wait(predicate):
        while not predicate():
            if stopped():raise RuntimeError('Owner stop')
            time.sleep(60)
        if stopped():raise RuntimeError('Owner stop')
    def finished():
        if (FROZEN/'failed.json').exists():
            raise RuntimeError('Review frozen scoring failure')
        return (FROZEN/'complete.json').is_file() and (FROZEN/'released.json').is_file()
    def transferred(job):
        fetch(job)
        return (BASE.parent/(job+'-transfer-a.json')).is_file()
    with (BASE/'readout.lock').open('a+b') as f:
        f.seek(0)
        msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        save(BASE/'readout.json',dict(pid=os.getpid(),stage='waiting for frozen readers'))
        wait(finished)
        save(FROZEN/'exit-verification.json',verify_exit(FROZEN))
        for task in TASKS:
            out=BASE/task
            save(BASE/'readout.json',dict(pid=os.getpid(),stage=task))
            if task=='TP44':wait(lambda:transferred('Q18'))
            if task=='TP43-read':
                wait(lambda:time.time()>=datetime(2026,11,22,16,tzinfo=UTC).timestamp())
                wait(lambda:transferred('Q19'))
            if not (out/'complete.json').is_file():
                subprocess.run([sys.executable,__file__,task],check=True)
            if read(out/'complete.json')['sourceReceiptPin']!=pin(out/'receipt.json'):
                raise ValueError('Private result binding differs')
            save(out/'exit-verification.json',verify_exit(out))
            if task in ('TP44','TP43-read'):
                from cb_land import land
                land('TP44' if task=='TP44' else 'TP43')
        save(BASE/'readout.json',dict(stage='private readouts verified; aggregate results filed locally'))


if __name__=='__main__':
    if sys.argv[1]=='serve':
        try:
            serve()
        except Exception as exc:
            save(BASE/'readout-error.json',dict(error=str(exc),pid=os.getpid()))
            raise
    elif sys.argv[1] in TASKS:
        score(sys.argv[1])
    else:
        raise ValueError('Unknown readout')
