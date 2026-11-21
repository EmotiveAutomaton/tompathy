"""CB queues. Run from a registered snapshot with an independent, single-lane lease."""
import bisect
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

WINDOWS = os.name == 'nt'
ROOT = Path('.local/person-teacher').resolve() if WINDOWS else Path('/home/agent/tompathy-open/person-teacher-20261121')
OLD = Path('.local/word-table/workstation').resolve() if WINDOWS else ROOT.parent/'word-table-20261120'
HOME = ROOT/'cb'
MORNING = 'ff2e4dd0f02fb9488e35ce4acf580ce0bad73d53'
BS = 'a5b9d7c10cf780d6977c49b11c7c43e37d99b644'
PACKET = 'b5a20efc7b738a06e186039a6976a0c5a1cec4b90c35564b8b26b471dbf90889'
END = datetime(2026, 11, 22, 16, tzinfo=UTC).timestamp()
sys.path.insert(0, str(ROOT/'code'/MORNING))
import person_teacher_lane as morning

lane = morning.lane
read, write, pin = lane.read, lane.write, lane.pin
LOCK = OLD/'gpu.lock' if WINDOWS else Path('/home/agent/gpu.lock')


def check_stop():
    if any(p.exists() for p in (ROOT/'STOP', OLD/'STOP', HOME/'STOP', ROOT/'bs/STOP')):
        raise RuntimeError('Owner stop')


def validate():
    cfg = read(HOME/'registration.json')
    if Path(__file__).resolve().parent != ROOT/'code'/cfg['commit'] or pin(Path(__file__)) != cfg['scriptPin']:
        raise ValueError('CB execution snapshot differs')
    morning.validate(ROOT)
    manifest = read(HOME/'inputs.json')
    if pin(HOME/'inputs.json') != cfg['inputPin'] or manifest['packet'] != PACKET:
        raise ValueError('CB input manifest changed')
    return cfg, manifest


class Cutoff(Exception):
    pass


def features(job):
    cfg, manifest = validate()
    if job not in (('G11',) if WINDOWS else ('Q18', 'Q19')):
        raise ValueError('Incorrect GPU lane')
    blog = job != 'Q18'
    path = HOME/('blogs.json' if blog else 'isear.json')
    expected = manifest['blogs']['posts'] if blog else manifest['isear']['reports']
    if pin(path) != expected:
        raise ValueError('Reader input changed')
    rows = read(path)
    bounds = []
    if blog:
        path = HOME/'boundaries.json'
        if pin(path) != manifest['blogs']['boundaries']:
            raise ValueError('Author boundaries changed')
        bounds = read(path)
        if job == 'Q19':
            n = bisect.bisect_right(bounds, 30000)
            rows = rows[:bounds[n-1]] if n else []
    out = ROOT/'jobs'/job
    role = 'W' if WINDOWS else 'B'
    with lane.lease(LOCK):
        check_stop()
        out.mkdir(exist_ok=False)
        owner = dict(lane.identity(), job=job, lock=str(LOCK), commit=cfg['commit'], at=lane.now())
        write(out/'owner.json', owner)
        receipt = dict(owner=owner, job=job, status='running', packetPin=PACKET, inputPin=expected,
                       descriptiveOnly=(job=='G11'), scheduledRows=len(rows))
        write(out/'receipt.json', receipt)
        try:
            with lane.core.Guard(out, float('inf')) as thermal:
                base_checks = lane.Checks(ROOT, out, thermal)
                class Checks:
                    timed = False
                    def check(self):
                        base_checks.check()
                        check_stop()
                        if blog and time.time() >= END:
                            raise Cutoff()
                        if blog and not self.timed and (out/'progress.json').exists():
                            pr = read(out/'progress.json')
                            if pr['rows'] >= 100:
                                if pr['rows'] != 100:
                                    raise ValueError('First 100 timing boundary missed')
                                remaining = max(0, END-time.time())
                                projected = min(len(rows), 100+int(remaining*100/pr['secondsPer100']))
                                write(out/'first100.json', dict(pr, projectedRows=projected,
                                      projectedWholeAuthors=bisect.bisect_right(bounds, projected)))
                                self.timed = True
                checks = Checks()
                checks.check()
                # Byte count bounds byte-level tokenizer length. Keep the existing output
                # reserve and record any over-bound item as missing, without truncation.
                lengths = {r['id']: len((lane.core.CORRECTED_PROMPT+r['text']).encode()) for r in rows}
                receipt['summary'] = lane.rate(ROOT, out, rows, role, job,
                    dict(job=job, inputPin=expected, packetPin=PACKET, commit=cfg['commit']), checks,
                    token_lengths=lengths)
            receipt['status'] = 'complete'
        except Cutoff:
            receipt['status'] = 'cutoff'
        except Exception as exc:
            receipt.update(status='failed', reason=str(exc))
            write(out/'receipt.json', receipt)
            write(out/'failed.json', {'receiptPin':pin(out/'receipt.json')})
            raise
        count = sum(1 for _ in (out/role).glob('row-*.json'))
        receipt.update(durableRows=count, ended=lane.now())
        if blog:
            receipt['wholeAuthors'] = bisect.bisect_right(bounds, count)
        write(out/'receipt.json', receipt)
        write(out/'complete.json', {'receiptPin':pin(out/'receipt.json')})


def wait_for(predicate):
    while not predicate():
        check_stop()
        time.sleep(30)
    check_stop()


def launch(job, script):
    out = ROOT/'jobs'/job
    if out.exists():
        raise ValueError('Prior attempt requires review: '+job)
    while True:
        check_stop()
        proc = subprocess.Popen([sys.executable, str(script), job])
        code = proc.wait()
        if code == 74 and not out.exists():
            time.sleep(60)
            continue
        owner = read(out/'owner.json')
        if owner['job'] != job or (not WINDOWS and owner['pid'] != proc.pid):
            raise ValueError('Child identity mismatch')
        if WINDOWS:
            import psutil
            if psutil.pid_exists(owner['pid']):
                raise ValueError('Native worker has not exited')
        with lane.lease(LOCK):
            write(out/'released.json', dict(owner=owner, descriptorClosed=True, nativeExitCode=code, at=lane.now()))
        if code:
            raise RuntimeError('Preserve failed '+job)
        return


def serve():
    cfg, _ = validate()
    with lane.lease(HOME/'dispatcher.lock'):
        write(HOME/'dispatcher.json', dict(lane.identity(), at=lane.now(), commit=cfg['commit']))
        if WINDOWS:
            wait_for(lambda: (ROOT/'G4-transfer-a.json').is_file())
            audit = read(ROOT/'G4-transfer-a.json')
            if not audit['nativeExited'] or not audit['priorFlockReleased'] or audit['sourceReceiptPin'] != pin(ROOT/'jobs/G4/receipt.json'):
                raise ValueError('G4 verification mismatch')
            launch('G11', __file__)
        else:
            path = ROOT/'code'/BS/'afternoon_teacher.py'
            if pin(path) != '795a2c7f61fee008fbdc8f75db5242f40c12f0e489f62bf9b994e7005f49d67c':
                raise ValueError('BS runtime changed')
            sys.path.insert(0, str(path.parent))
            import afternoon_teacher as bs
            wait_for(lambda: (ROOT/'tail/complete.json').is_file())
            if (bs.terminal('Q12')['status'] != 'complete' or bs.terminal('Q7')['status'] != 'blocked'
                or read(ROOT/'tail/complete.json')['Q7'] != pin(ROOT/'jobs/Q7/receipt.json')):
                raise ValueError('Predecessor release mismatch')
            launch('Q14', path)
            prior = bs.terminal('Q14')
            decision = bs.checked(ROOT/'jobs/Q14/decision.json', prior['decisionPin'])
            for job in ('Q18','Q19'):
                launch(job, __file__)
            if prior['status']=='complete' and decision['passes'] is True:
                wait_for(lambda: time.time() >= END)
                launch('Q15', path)
            else:
                write(HOME/'Q15-ineligible.json', dict(q14Receipt=pin(ROOT/'jobs/Q14/receipt.json'),
                       reason='Q14 did not qualify', at=lane.now()))
        write(HOME/'complete.json', dict(at=lane.now()))


if __name__ == '__main__':
    lane.settings()
    try:
        if sys.argv[1] == 'serve':
            serve()
        else:
            features(sys.argv[1])
    except lane.Busy:
        sys.exit(74)
