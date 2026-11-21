"""Capture the owner-initiated morning prefix on Spark. Run only on that owner turn."""
import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path('/home/agent/tompathy-open/word-table-20261120')
STUDY = Path(__file__).resolve().parents[1]/'.local/word-table'
MORNING = datetime.fromisoformat('2026-11-21T07:00:00-08:00')


def owner_time(value, now):
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None or not MORNING <= stamp <= now:
        raise ValueError('An observed owner turn on or after the morning boundary is required')
    return stamp


def read(path):
    return json.loads(path.read_bytes())


def put_once(path, data):
    # Link the fully written file atomically. A competing invocation keeps its original boundary.
    import os
    import tempfile
    with tempfile.NamedTemporaryFile('w',encoding='utf8',delete=False,dir=path.parent) as f:
        try:
            json.dump(data,f,indent=2)
            f.flush()
            os.fsync(f.fileno())
        finally:
            temp = Path(f.name)
    try:
        try:
            if os.name=='nt':
                temp.rename(path)  # Windows rename fails if the destination exists.
            else:
                os.link(temp,path)
        except FileExistsError:
            pass
    finally:
        temp.unlink(missing_ok=True)
    return read(path)


def owns_flock(owner):
    import os
    pid = str(owner['pid'])
    proc = Path('/proc',pid,'stat')
    lock = Path('/home/agent/gpu.lock')
    if (owner['bootId']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            or owner['lock']!=str(lock) or not proc.is_file()
            or proc.read_text().rsplit(') ',1)[1].split()[19]!=owner['startTicks']):
        return False
    st = lock.stat()
    for line in Path('/proc/locks').read_text().splitlines():
        fields = line.split()
        if len(fields)>=6 and fields[1]=='FLOCK' and fields[4]==pid:
            major,minor,inode = fields[5].split(':')
            if (int(major,16),int(minor,16),int(inode))==(os.major(st.st_dev),os.minor(st.st_dev),st.st_ino):
                return True
    return False


def capture(base, stamp):
    queue = read(base/'queue.json')['jobs']
    saved = base/'owner-morning-boundary.json'
    if not saved.exists():
        jobs = {}
        for job in ('Q6','Q7'):
            directory = base/'jobs'/job
            if not (directory/'owner.json').exists():
                if job=='Q6':
                    raise ValueError('Expected a Q6 owner')
                jobs[job] = {'status':'unstarted','durableRows':0}
                continue
            owner = read(directory/'owner.json')
            receipt = read(directory/'receipt.json')
            if (owner!=receipt['owner'] or owner['commit']!=queue[job]['commit'] or owner['job']!=job
                    or receipt['entry']!=queue[job]):
                raise ValueError('Unrecognized Spark owner or registered job')
            rows = sorted(p.name for p in (directory/'B').glob('row-*.json'))
            if rows!=[f'row-{i:06d}.json' for i in range(len(rows))]:
                raise ValueError('Durable response prefix has a gap')
            jobs[job] = {'owner':owner,'status':receipt['status'],'durableRows':len(rows)}
        put_once(saved,{'trigger':'owner-turn','ownerTurnAt':stamp,'observedAt':datetime.now(UTC).isoformat(),
                        'jobs':jobs,**jobs['Q6']})
    boundary = read(saved)
    owner_time(boundary['ownerTurnAt'],datetime.now(UTC))
    if boundary['trigger']!='owner-turn':
        raise ValueError('Unexpected saved review')
    for job, record in boundary['jobs'].items():
        directory = base/'jobs'/job
        if record['status']!='running' or (directory/'released.json').exists():
            continue
        if any((directory/f).exists() for f in ('failed.json','complete.json','skipped.json')):
            continue
        owner = read(directory/'owner.json')
        if owner!=record['owner'] or not owns_flock(owner):
            raise ValueError('Verify the current native owner before requesting a stop')
        stop = directory/'STOP'
        if not stop.exists():
            with stop.open('x') as handle:
                handle.write('Owner morning boundary at '+boundary['observedAt']+'\n')
    return boundary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner-turn-at',required=True)
    parser.add_argument('--spark-side',action='store_true')
    args = parser.parse_args()
    stamp = owner_time(args.owner_turn_at,datetime.now(UTC)).isoformat()
    if args.spark_side:
        print(json.dumps(capture(ROOT,stamp)))
        return
    command = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','spark','python3','-',
               '--spark-side','--owner-turn-at',stamp]
    script = Path(__file__).resolve()
    committed = subprocess.check_output(['git','show','HEAD:scripts/'+script.name],cwd=script.parents[1])
    if committed!=script.read_bytes().replace(b'\r\n',b'\n'):
        raise ValueError('Use the reviewed committed morning capture script')
    reply = subprocess.run(command,input=committed,capture_output=True,check=True,timeout=90)
    evidence = json.loads(reply.stdout)
    destination = STUDY/'owner-morning-boundary.json'
    if put_once(destination,evidence)!=evidence:
        raise ValueError('Preserve the existing local boundary and reconcile')
    print(json.dumps({'saved':destination.as_posix(),'observedAt':evidence['observedAt'],
                      'durableRows':evidence['durableRows']}))


if __name__=='__main__':
    main()
