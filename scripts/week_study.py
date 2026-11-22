"""Counted workstation CPU analysis for the November 22 packet."""
import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
from cb_inputs import pin

PACKET = ROOT/'TOMPATHY_0.3_ENGINE_WEEK_PACKET_2026-11-22.md'
PACKET_PIN = '9a02029adc1292fe784160a491f0d2629b5c59bebcb4cfd8afd03e6bc63647b8'
WEEK = ROOT/'.local/week-20261122'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('card', choices=['TP55', 'Q20-inputs', 'Q21-inputs','Q22-inputs'])
    parser.add_argument('attempt', choices=['a', 'b', 'c'])
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '2'
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard
    benchmark_priority(2)
    if pin(PACKET) != PACKET_PIN:
        raise ValueError('Registered packet differs')
    output = WEEK/f'{args.card}-{args.attempt}'
    output.mkdir(exist_ok=False)
    deadline = time.monotonic() + 3600
    def check():
        guard()
        if any((p/'STOP').exists() for p in (output, WEEK, ROOT/'.local/person-teacher')) or time.monotonic() >= deadline:
            raise RuntimeError('Stop or deadline reached')
    spec = importlib.util.spec_from_file_location('counted', ROOT/'scripts/engine-two-day-job.py')
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    try:
        with counted.lease(ROOT.parent/'SoundingLine/sounding-line', output, card='ToMpathy-'+args.card):
            check()
            if args.card == 'TP55':
                from tompathy_engine.eval.readers import week_anxiety as study
            elif args.card == 'Q20-inputs':
                import week_blog_inputs as study
            elif args.card == 'Q21-inputs':
                import week_pride_inputs as study
            else:
                import week_news_inputs as study
            source = Path(study.__file__)
            (output/source.name).write_bytes(source.read_bytes())
            result = study.run(check) if args.card == 'TP55' else study.prepare(output,check)
            check()
            save_json(output/'receipt.json', dict(result, status='complete', packetPin=PACKET_PIN,
                      codePin=pin(output/source.name), protocolPin=pin(ROOT/'docs/ENGINE_WEEK_2026-11-22.md')))
            save_json(output/'complete.json', dict(sourceReceiptPin=pin(output/'receipt.json')))
    except Exception as exc:
        save_json(output/'failed.json', dict(reason=str(exc)))
        raise


if __name__ == '__main__':
    main()
