"""Resume the G11 descriptive lane at its first unsaved row after its first transport timeout."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path('.local/person-teacher').resolve()
OLD = BASE/'jobs/G11'
OUT = BASE/'jobs/G11-b'
COMMIT = '71e719cc6b7063d2f2516040cf8fde3d2863453a'
RECEIPT = '847c6d8ccb85d8e3a383a02f42f8b0decba252f8ae0058dcbdba9bb3ada52d48'
sys.path.insert(0,str(BASE/'code'/COMMIT))
import cb_gpu as cb

lane = cb.lane
read, pin, write = cb.read, cb.pin, cb.write


def assert_gone(owner):
    sys.path.insert(0,'E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line')
    from runners.stage9.process_identity import native_identity
    alive = native_identity(owner['pid'])
    if alive and alive['created_ticks'] == owner['createdTicks']:
        raise RuntimeError('Original native process still alive')


def verify_prefix(rows):
    receipt = read(OLD/'receipt.json')
    owner = receipt['owner']
    release = read(OLD/'released.json')
    if (pin(OLD/'receipt.json')!=RECEIPT or read(OLD/'failed.json')['receiptPin']!=RECEIPT
            or (owner['pid'],owner['createdTicks'])!=(315552,134397760250829142)
            or owner!=read(OLD/'owner.json') or release['owner']!=owner
            or release['nativeExitCode']!=1 or not release['descriptorClosed']
            or Path(owner['lock'])!=cb.LOCK or 'curl: (28)' not in receipt['reason']):
        raise ValueError('G11 failure or release differs')
    assert_gone(owner)
    protocol = read(OLD/'W/protocol.json')
    hashes = {}
    files = sorted((OLD/'W').glob('row-*.json'))
    if len(files)!=9142:
        raise ValueError('Unexpected saved prefix')
    for i,p in enumerate(files):
        if i%100==0:
            cb.check_stop()
        raw = p.read_bytes()
        r = json.loads(raw)
        if (p.name!=f'row-{i:06d}.json' or r['index']!=i or r['id']!=rows[i]['id'] or
                r['binding']!={k:v for k,v in protocol.items() if k not in ('prompt','schema','secondKey')} or
                r['values'] is None or
                lane.core.valid_features(json.loads(r['response']['response']))!=r['values']):
            raise ValueError('G11 saved prefix differs')
        hashes[p.name] = hashlib.sha256(raw).hexdigest()
    return hashes, protocol


def work():
    cfg,manifest = cb.validate()
    inp = cb.HOME/'blogs.json'
    bounds = cb.HOME/'boundaries.json'
    if pin(inp)!=manifest['blogs']['posts'] or pin(bounds)!=manifest['blogs']['boundaries']:
        raise ValueError('Registered cohort differs')
    rows = read(inp)
    with lane.lease(cb.LOCK):
        cb.check_stop()
        if lane.core.api('ps')['models']:
            raise lane.Busy()
        OUT.mkdir(exist_ok=False)
        owner = dict(lane.identity(),job='G11-b',lock=str(cb.LOCK),commit=COMMIT,
                     recoveryCode=pin(Path(__file__)),at=lane.now())
        write(OUT/'owner.json',owner)
        receipt = dict(owner=owner,job='G11-b',sourceReceiptPin=RECEIPT,status='verifying prefix',
                       deadlineUTC='2026-11-22T16:00:00+00:00',descriptiveOnly=True,transportSeconds=300)
        write(OUT/'receipt.json',receipt)
        try:
            hashes,protocol = verify_prefix(rows)
            start = len(hashes)
            write(OUT/'prefix-pins.json',hashes)
            receipt.update(status='running',prefixRows=start,firstSuffixGlobalIndex=start,
                           prefixInventoryPin=pin(OUT/'prefix-pins.json'),inputPin=pin(inp))
            write(OUT/'receipt.json',receipt)
            suffix = rows[start:]
            # Only the HTTP client deadline changes, within this dedicated worker.
            def generate(request,guard):
                if (request['model']!=lane.W[0] or request['options']!=protocol['options']
                        or request['think']!=protocol['think'] or request['format']!=protocol['schema']):
                    raise ValueError('G11 inference options differ')
                return lane.core.guarded_request('generate',request,guard,300)
            if lane.core.CORRECTED_PROMPT!=protocol['prompt']:
                raise ValueError('G11 prompt changed')
            lane.core.guarded_generate = generate
            with lane.core.Guard(OUT,float('inf')) as thermal:
                base = lane.Checks(BASE,OUT,thermal)
                class Checks:
                    def check(self):
                        base.check()
                        cb.check_stop()
                        if (OLD/'STOP').exists():
                            raise RuntimeError('Owner stop')
                        if time.time()>=cb.END:
                            raise cb.Cutoff()
                checks=Checks()
                checks.check()
                lengths={r['id']:len((protocol['prompt']+r['text']).encode()) for r in suffix}
                binding=dict(job='G11',inputPin=pin(inp),packetPin=cb.PACKET,commit=cfg['commit'],
                             firstSuffixGlobalIndex=start,sourceReceiptPin=RECEIPT)
                receipt['summary']=lane.rate(BASE,OUT,suffix,'W','G11',binding,checks,token_lengths=lengths)
                receipt['status']='complete'
        except cb.Cutoff:
            receipt['status']='cutoff'
        except Exception as exc:
            receipt.update(status='failed',reason=str(exc))
            write(OUT/'receipt.json',receipt)
            write(OUT/'failed.json',{'receiptPin':pin(OUT/'receipt.json')})
            raise
        count = len(list((OUT/'W').glob('row-*.json')))
        end = start+count
        limits = read(bounds)
        receipt.update(suffixRows=count,totalDurableRows=end,wholeAuthorsWithTexts=sum(
            hi<=end and hi>lo for lo,hi in zip([0]+limits,limits)),ended=lane.now())
        write(OUT/'receipt.json',receipt)
        write(OUT/'complete.json',{'receiptPin':pin(OUT/'receipt.json')})


def supervise():
    while time.time()<cb.END:
        cb.check_stop()
        if OUT.exists():
            raise RuntimeError('Preserve previous attempt')
        proc=subprocess.run([sys.executable,__file__,'worker'])
        if proc.returncode==74 and not OUT.exists():
            time.sleep(60)
            continue
        owner=read(OUT/'owner.json')
        assert_gone(owner)
        with lane.lease(cb.LOCK):
            write(OUT/'released.json',dict(owner=owner,nativeExitCode=proc.returncode,
                                           descriptorClosed=True,at=lane.now()))
        return proc.returncode


if __name__=='__main__':
    lane.settings()
    try:
        if sys.argv[1:] == ['worker']:
            work()
        elif sys.argv[1:] == ['serve']:
            sys.exit(supervise())
        else:
            raise ValueError('Expected serve or worker')
    except lane.Busy:
        sys.exit(74)
