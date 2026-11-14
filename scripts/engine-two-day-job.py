"""Explicit, single-scoring-process CPU job. Never launches research implicitly."""
import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


@contextmanager
def lease(sl, output, *, large=False):
    # Reuse the shared native identity and reservation readers, read-only.
    sys.path.insert(0, str(sl))
    from runners.drive.cards.week5_policy_v2 import (
        lease_paths,
        memory_reserve,
        shared_reservation,
    )
    from runners.stage9.process_identity import native_identity
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.back_half.resources import headroom
    native = native_identity()
    value = {'native': native, 'card': 'ToMpathy-two-day-20261112', 'at': datetime.now(UTC).isoformat(),
             'projected_peak_ram_GiB': 14 if large else 6, 'output': str(output.resolve())}
    local = Path.cwd()/'.local/bench/two-day-scoring.lock'
    handle = os.open(local, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(handle, 'w', encoding='utf8') as stream:
        json.dump(value, stream)
    claimed = None
    try:
        paths = lease_paths()
        capacity = 8-int(shared_reservation()['active'])
        if len(paths) >= capacity or min(headroom().values()) < max(20 if large else 8, 8+value['projected_peak_ram_GiB']+memory_reserve(paths)):
            raise RuntimeError('Shared CPU slot or reserved memory unavailable')
        for index in range(8):
            candidate = sl/'results/.cpu-slots-20261107'/f'slot-{index}.json'
            try:
                handle = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            except FileExistsError:
                continue
            claimed = candidate
            with os.fdopen(handle, 'w', encoding='utf8') as stream:
                json.dump(value, stream)
            break
        if claimed is None or len(lease_paths()) > capacity:
            raise RuntimeError('Shared CPU slot changed during admission')
        save_json(output/'owner.json', {**value, 'lease': str(claimed)})
        yield
    finally:
        for path in (claimed, local):
            if path is not None and path.exists():
                if json.loads(path.read_text(encoding='utf8')) != value or native_identity() != native:
                    raise RuntimeError('Lease ownership changed; refusing cleanup')
                path.unlink()
        save_json(output/'released.json', {'native': native, 'at': datetime.now(UTC).isoformat()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sounding-line', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--readers', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--threads', type=int, choices=(1, 2), default=2)
    parser.add_argument('--until', help='Absolute timezone-aware end of the commissioned queue; never resets on restart')
    parser.add_argument('--phases', nargs='+', choices=('window', 'kv', 'smol', 'ladder'), default=['window', 'kv', 'smol', 'ladder'])
    parser.add_argument('--task', choices=('attention', 'edit-features', 'edits', 'human-edits', 'human-features', 'goals', 'goal-baseline', 'robustness', 'choice', 'choice-goals', 'weightonly', 'weightonly-binding', 'first-paint'), default='attention')
    parser.add_argument('--task-args', nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args()
    if args.task != 'attention' and args.threads != 2:
        parser.error('Pilot runtime identities use a maximum of two threads; select --threads 2')
    until = datetime.fromisoformat(args.until) if args.until else None
    if until and until.tzinfo is None:
        parser.error('--until must include a timezone')
    sys.path.insert(0, str(args.snapshot.resolve()))
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard
    benchmark_priority(args.threads)
    from tompathy_engine.eval.two_day.attention import run
    args.output.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+48*3600
    def check():
        if (args.output/'STOP').exists() or time.monotonic() >= deadline or (until and datetime.now(UTC) >= until):
            raise RuntimeError('Requested stop or 48-hour bounded job deadline')
        value = guard()
        save_json(args.output/'heartbeat.json', {'at': datetime.now(UTC).isoformat(), **value})
    try:
        large = args.task in {'edits', 'human-edits', 'goals', 'choice-goals'}
        with lease(args.sounding_line, args.output, large=large):
            check()
            if args.task == 'attention':
                run(args.intake, args.readers, args.output/'attention', check, args.threads, args.phases)
            else:
                from tompathy_engine.eval.two_day.__main__ import main as pilot
                pilot([args.task, '--readers', str(args.readers), '--output', str(args.output/'pilot'), *args.task_args], check=check)
    except Exception as exc:
        save_json(args.output/'failed.json', {'at': datetime.now(UTC).isoformat(), 'type': type(exc).__name__, 'reason': str(exc)})
        raise
    save_json(args.output/'complete.json', {'at': datetime.now(UTC).isoformat()})


if __name__ == '__main__':
    main()
