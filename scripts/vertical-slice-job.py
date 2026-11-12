"""One counted CPU slot for a bounded native browser/engine acceptance pass."""
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SL = ROOT.parent / 'SoundingLine/sounding-line'
sys.path.insert(0, str(SL))
from runners.drive.cards.batch_runtime import (
    claim_slot,
    native_identity,
    release_slot,
    resource_snapshot,
)

surface_only = '--surface-only' in sys.argv
run = ROOT / '.local/vertical-slice-20261023'
run.mkdir(exist_ok=True)
resources = resource_snapshot()
floor = 24 if surface_only else 32
if min(resources['ram_available_GiB'], resources['commit_headroom_GiB']) < floor or resources['disk_free_GiB'] < 20:
    raise RuntimeError(f'Need {floor} GiB RAM and commit headroom; no browser or reader started')
lease = claim_slot(SL / 'results/.cpu-slots-20261017', native_identity(), 'ToMpathy-single-blog-acceptance')
child = identity = None
record = {"startedAt": datetime.now(UTC).isoformat(), "lease": str(lease[0]),
          "resources": resources, "threads": 1, "gpu": False, "judgments": not surface_only}
try:
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES='-1', PYTHONDONTWRITEBYTECODE='1',
               TOMPATHY_TEST_SURFACE_ONLY='1' if surface_only else '0')
    if '--cold' in sys.argv:
        env['TOMPATHY_TEST_COLD'] = '1'
    with (run / 'stdout.log').open('ab') as out, (run / 'stderr.log').open('ab') as err:
        child = subprocess.Popen(['node', 'scripts/vertical-slice-validation.mjs'], cwd=ROOT, env=env,
                                 stdout=out, stderr=err, creationflags=0x08000000 | 0x4000)
        identity = native_identity(child.pid)
        record['child'] = identity
        (run / 'owner.json').write_text(json.dumps(record), encoding='utf8')
        start = time.monotonic()
        while child.poll() is None:
            resources = resource_snapshot()
            record['latestResources'] = resources
            if min(resources['ram_available_GiB'], resources['commit_headroom_GiB']) < 16 or resources['disk_free_GiB'] < 20:
                raise RuntimeError('Shared memory/disk floor reached')
            if time.monotonic() - start > 900 or (run / 'STOP').exists():
                raise RuntimeError('Acceptance wall-time bound or STOP reached')
            time.sleep(10)
        if child.returncode:
            raise RuntimeError(f'Acceptance process exited {child.returncode}; see retained stderr')
        record['passed'] = True
except BaseException as error:
    record.update(passed=False, error=repr(error))
    raise
finally:
    if child is not None and child.poll() is None:
        if native_identity(child.pid) != identity:
            raise RuntimeError('Owned child identity changed')
        subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], check=True, creationflags=0x08000000)
        child.wait(timeout=30)
    release_slot(*lease)
    record.update(slotReleased=True, finishedAt=datetime.now(UTC).isoformat())
    (run / 'result.json').write_text(json.dumps(record, indent=2), encoding='utf8')
