"""Reserve only the Q13/Q7 handoff, preserving all running GPU programs."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import person_teacher_modernbert_check as proof

NEW,OLD=proof.NEW,proof.OLD
TAIL=NEW/'tail'
HOLD=NEW/'jobs/Q7/STOP'
GPU=Path('/home/agent/gpu.lock')
REGISTERED='ff2e4dd0f02fb9488e35ce4acf580ce0bad73d53'
BOOT='17b89c07-ca2a-4328-be23-1079536e9232'
read,pin=proof.read,proof.digest


def files():
    cfg=read(NEW/'q13-copy-registration.json')
    directory=Path(__file__).resolve().parent
    if directory!=NEW/'code'/cfg['commit'] or any(pin(directory/k)!=v for k,v in cfg['files'].items()):
        raise ValueError('Supplementary execution snapshot changed')
    return cfg


def absent(owner):
    if owner['bootId']!=BOOT or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=BOOT:
        raise ValueError('Boot identity changed; host review required')
    proc=Path('/proc')/str(owner['pid'])/'stat'
    return not proc.exists() or proc.read_text().rsplit(') ',1)[1].split()[19]!=str(owner['startTicks'])


def released(folder):
    if not (folder/'released.json').exists():
        return False
    owner=read(folder/'owner.json')
    rel=read(folder/'released.json')
    return owner==rel['owner'] and rel['descriptorClosed'] and absent(owner)


def modules():
    cfg=files()
    sys.path.insert(0,str(OLD/'code'/proof.REPAIR))
    import word_table_fine_runtime as fine
    import word_table_g2_repair as repair
    import word_table_lane as lane
    lane.settings()
    return cfg,lane,repair,fine


def marker(cfg):
    return ('Hold for registered November 21 Q13 copy test and tail '+cfg['commit']+'\n').encode()


def reserve(cfg,lane):
    if (NEW/'jobs/Q7/owner.json').exists() or (NEW/'STOP').exists() or (OLD/'STOP').exists():
        raise ValueError('Owner stop or Q7 already started')
    if read(NEW/'dispatcher.json')!=cfg['priorDispatcher']:
        raise ValueError('Original dispatcher differs; preserve it')
    HOLD.parent.mkdir(parents=True,exist_ok=True)
    if not HOLD.exists():
        with HOLD.open('xb') as out:
            out.write(marker(cfg))
    if HOLD.read_bytes()!=marker(cfg):
        raise ValueError('Independent STOP must be preserved')
    lane.write(TAIL/'reservation.json',{'job':'Q7','reason':'Wait for optional Q13 in packet order',
                                         'commit':cfg['commit'],'at':lane.now(),'markerPin':pin(HOLD)})


def full(cfg,lane,repair,fine):
    folder=TAIL/'Q13-modernbert'
    storage=NEW/'rung-storage/Q13-modernbert-a'
    if not released(NEW/'engineering/Q13-copy-a'):
        raise ValueError('Training-copy native exit is required')
    copy=read(NEW/'engineering/Q13-copy-a/verified.json')
    if (copy['sourcePin']!=proof.ORIGINAL or copy['status']!='verified' or copy['owner']['commit']!=cfg['commit']
            or copy['owner']!=read(NEW/'engineering/Q13-copy-a/owner.json')):
        raise ValueError('No verified optimizer step on the independent copy')
    with lane.lease(GPU):
        folder.mkdir(exist_ok=False)
        owner={**lane.identity(),'job':'Q13-modernbert','commit':cfg['commit'],'lock':str(GPU),'at':lane.now()}
        lane.write(folder/'owner.json',owner)
        receipt={'job':'Q13-modernbert','status':'running','owner':owner,'copyPin':pin(NEW/'engineering/Q13-copy-a/verified.json'),
                 'parentReceiptPin':repair.ORIGINAL,'scientificRuntimeCommit':proof.REPAIR}
        lane.write(folder/'receipt.json',receipt)
        try:
            reg,binding,last=repair.preflight(lane)
            if reg['commit']!=proof.REPAIR or pin(last/'source.json')!=proof.ORIGINAL:
                raise ValueError('Original source or runtime changed')
            storage.mkdir(parents=True,exist_ok=False)
            with lane.core.Guard(folder,float('inf')) as thermal:
                checks=lane.Checks(NEW,folder,thermal)
                class Guard:
                    def check(self):
                        checks.check()
                        if (OLD/'STOP').exists() or (TAIL/'STOP').exists():
                            raise RuntimeError('Owner STOP')
                guard=Guard()
                guard.check()
                rows=fine.run(OLD,storage,binding,lane.core,guard,restored_modernbert=last)
                guard.check()
            # Expose forecasts and control records for readout. Model and optimizer weights remain on Spark.
            compact=folder/'forecasts'
            compact.mkdir()
            all_pins={}
            selected={}
            for path in sorted(storage.rglob('*')):
                if path.is_symlink():
                    raise ValueError('Unexpected linked scientific artifact')
                if not path.is_file():
                    continue
                rel=path.relative_to(storage).as_posix()
                all_pins[rel]=pin(path)
                if path.suffix in ('.npz','.json'):
                    target=compact/rel
                    target.parent.mkdir(parents=True,exist_ok=True)
                    os.link(path,target)
                    selected[rel]=all_pins[rel]
            lane.write(folder/'complete-storage-inventory.json',all_pins)
            lane.write(folder/'forecast-inventory.json',selected)
            receipt.update(status='complete',rows=rows,scienceEntry=binding,
                           sources=pin(folder/'complete-storage-inventory.json'),forecastPin=pin(folder/'forecast-inventory.json'))
            lane.write(folder/'receipt.json',receipt)
            lane.write(folder/'complete.json',{'receiptPin':pin(folder/'receipt.json')})
        except Exception as exc:
            receipt.update(status='failed',reason=str(exc))
            lane.write(folder/'receipt.json',receipt)
            lane.write(folder/'failed.json',{'receiptPin':pin(folder/'receipt.json')})
            raise


def child(command,folder,lane):
    proc=subprocess.Popen(command)
    code=proc.wait()
    if (folder/'owner.json').is_file():
        owner=read(folder/'owner.json')
        if code==74 and owner['pid']!=proc.pid:
            return code
        if owner['pid']!=proc.pid or not absent(owner):
            raise ValueError('Unexpected child identity at release')
        lane.write(folder/'released.json',{'owner':owner,'nativeExitCode':code,'at':lane.now(),'descriptorClosed':True})
    return code


def serve(cfg,lane):
    TAIL.mkdir(exist_ok=True)
    with lane.lease(TAIL/'supervisor.lock'):
        reserve(cfg,lane)
        lane.write(TAIL/'supervisor.json',{**lane.identity(),'commit':cfg['commit'],'at':lane.now()})
        while not (released(NEW/'jobs/Q13') and absent(cfg['priorDispatcher'])):
            if any(p.exists() for p in [NEW/'STOP',OLD/'STOP',TAIL/'STOP']):
                return
            time.sleep(45)
        if (not released(NEW/'jobs/Q12') or read(NEW/'jobs/Q12/receipt.json')['status']!='complete'
                or read(NEW/'jobs/Q13/receipt.json')['status']!='deferred' or HOLD.read_bytes()!=marker(cfg)):
            raise ValueError('Original Q12/Q13 boundary or owned handoff marker differs')
        with lane.lease(NEW/'dispatcher.lock'):
            study=NEW/'engineering/Q13-copy-a'
            for name,folder,cmd in [
                ('copy',study,[sys.executable,str(Path(__file__).with_name('person_teacher_modernbert_check.py'))]),
                ('rung',TAIL/'Q13-modernbert',[sys.executable,__file__,'full'])
            ]:
                if any(p.exists() for p in (NEW/'STOP',OLD/'STOP',TAIL/'STOP')):
                    return
                if folder.exists():
                    raise ValueError('Preserve earlier optional attempt for review')
                while True:
                    code=child(cmd,folder,lane)
                    if code!=74 or folder.exists():
                        break
                    if any(p.exists() for p in (NEW/'STOP',OLD/'STOP',TAIL/'STOP')):
                        return
                    time.sleep(90)
                lane.write(TAIL/(name+'-exit.json'),{'code':code,'at':lane.now()})
                if code:
                    break
            if any(p.exists() for p in (NEW/'STOP',OLD/'STOP',TAIL/'STOP')):
                return
            if HOLD.read_bytes()!=marker(cfg) or not absent(cfg['priorDispatcher']):
                raise ValueError('Preserve independent stop and dispatcher')
            HOLD.rename(TAIL/'completed-handoff-marker.txt')
            out=NEW/'jobs/Q7'
            while not (out/'complete.json').is_file():
                if any(p.exists() for p in (NEW/'STOP',OLD/'STOP',TAIL/'STOP',HOLD)):
                    return
                code=child([sys.executable,str(NEW/'code'/REGISTERED/'person_teacher_lane.py'),
                            'worker',str(NEW),str(OLD),'Q7'],out,lane)
                if code in (74,75):
                    time.sleep(90)
                elif code:
                    raise RuntimeError('Q7 stopped; retain source receipt')
            lane.write(TAIL/'complete.json',{'at':lane.now(),'Q7':pin(out/'receipt.json')})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['check','serve','full'])
    cfg,lane,repair,fine=modules()
    args=parser.parse_args()
    if args.action=='check':
        repair.preflight(lane)
        if read(NEW/'dispatcher.json')!=cfg['priorDispatcher']:
            raise ValueError('Prior dispatcher changed')
    elif args.action=='serve':
        serve(cfg,lane)
    else:
        try:
            full(cfg,lane,repair,fine)
        except lane.Busy:
            sys.exit(74)
