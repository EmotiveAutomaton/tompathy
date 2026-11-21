"""Freeze and run one addendum readout under the existing workstation CPU leases."""
import argparse
import hashlib
import json
import runpy
import shutil
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
PACKET = ROOT / 'TOMPATHY_0.3_ENGINE_ADDENDUM_2026-11-21.md'
PIN = '7832e75039bdb5185b3c9bc57684bc30332df41f64e7cb416773262eae5715dc'


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('card', choices=['TP42', 'TP41'])
    parser.add_argument('attempt', choices=['a','b','c'])
    args = parser.parse_args()
    if digest(PACKET) != PIN:
        raise ValueError('Addendum differs from received copy')
    out = ROOT/'.local/word-table'/f'{args.card.lower()}-{args.attempt}'
    out.mkdir(exist_ok=False)
    code = out/'code'
    shutil.copytree(ROOT/'engine/tompathy_engine', code/'tompathy_engine',
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('afternoon_job.py','engine-readers-job.py','engine-two-day-job.py'):
        shutil.copy2(ROOT/'scripts'/name,code/name)
    shutil.copy2(PACKET,out/PACKET.name)
    sys.path.insert(0,str(code))
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard
    from tompathy_engine.eval.back_half.reporting import save_json
    benchmark_priority(2)
    stop = time.monotonic()+3600
    heartbeat = runpy.run_path(str(code/'engine-readers-job.py'))['heartbeat']
    def check():
        if any(p.exists() for p in [ROOT/'.local/person-teacher/STOP', ROOT/'.local/word-table/STOP']):
            raise RuntimeError('Owner STOP')
        heartbeat(out,stop,guard)
    save_json(out/'plan.json',{'card':args.card,'protocolPin':PIN,'hours':1,'threads':2,
              'snapshotFiles':{p.relative_to(code).as_posix():digest(p) for p in code.rglob('*') if p.is_file() and p.suffix!='.pyc'}})
    counted=runpy.run_path(str(code/'engine-two-day-job.py'))
    try:
        with counted['lease'](Path('E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line'),out,card=args.card):
            check()
            from importlib import import_module
            study=import_module('tompathy_engine.eval.readers.'+args.card.lower())
            result=(study.finish_inventory(out,check) if args.card=='TP42' and args.attempt=='b'
                    else study.run(out,check))
            check()
            save_json(out/'receipt.json',dict(result,card=args.card,ledger=f'E-{args.card}-20261121',
                      protocolPin=PIN,status='complete',productionAdmission=False))
        save_json(out/'complete.json',{'receiptPin':digest(out/'receipt.json')})
    except Exception as exc:
        save_json(out/'failed.json',{'error':str(exc)})
        raise


if __name__=='__main__':
    main()
