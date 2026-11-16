"""Explicit local reader benchmark; does not install or enable a live reader."""
import argparse
import importlib.util
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from .run import Sentence, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--sentences', type=Path, required=True,
                        help='JSON list of text/start/end; UTF-16 offsets')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--job-output', type=Path, required=True, help='Fresh private ownership/heartbeat directory')
    parser.add_argument('--sounding-line', type=Path, required=True)
    parser.add_argument('--enable-benchmark-reader', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    job = args.job_output.resolve()
    if not job.is_relative_to(root/'.local') or not args.output.resolve().is_relative_to(job):
        parser.error('A fresh job directory under .local must contain the observations')
    if not args.enable_benchmark_reader:
        parser.error('The benchmark requires explicit enablement')
    from ..eval.back_half.reporting import save_json
    from ..eval.back_half.resources import benchmark_priority, guard
    benchmark_priority(2)
    job.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('counted', root/'scripts/engine-two-day-job.py')
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    deadline = time.monotonic()+3600

    def check():
        if time.monotonic() >= deadline or (job/'STOP').exists():
            raise RuntimeError('Reader benchmark deadline or stop')
        save_json(job/'heartbeat.json', {'at':datetime.now(UTC).isoformat(), **guard()})

    sentences = [Sentence(**row) for row in json.loads(args.sentences.read_text(encoding='utf8'))]
    try:
        with counted.lease(args.sounding_line, job, card='ToMpathy-reader-pack-benchmark'):
            check()
            from threadpoolctl import threadpool_limits
            with threadpool_limits(limits=2):
                value = run(args.pack, sentences, enabled=True, check=check)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf8') as handle:
                json.dump(value, handle, indent=2)
        save_json(job/'complete.json', {'at':datetime.now(UTC).isoformat()})
    except Exception as exc:
        save_json(job/'failed.json', {'at':datetime.now(UTC).isoformat(), 'reason':str(exc)})
        raise


if __name__ == '__main__':
    main()
