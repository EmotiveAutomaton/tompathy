"""One counted Sounding Line CPU slot; serial ToMpathy work, native ownership.

The slot file is the coordination channel used by Sounding Line's dispatcher.
Never steals or clears stale slots. Foreign research code is read-only.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import UTC, datetime

ROOT = Path(__file__).resolve().parents[1]
SL = ROOT.parent / "SoundingLine/sounding-line"
sys.path.insert(0, str(SL))
from runners.drive.cards.batch_runtime import claim_slot, release_slot, native_identity, resource_snapshot

os.environ.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                  NUMEXPR_NUM_THREADS="1", CUDA_VISIBLE_DEVICES="-1", PYTHONDONTWRITEBYTECODE="1")

def save(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf8")
    tmp.replace(path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    resources = resource_snapshot()
    if args.preflight:
        print(json.dumps(resources)); return
    if resources["ram_available_GiB"] < 24 or resources["commit_headroom_GiB"] < 24 or resources["disk_free_GiB"] < 20:
        raise RuntimeError("Insufficient shared headroom; nothing started")
    args.run.mkdir(parents=True, exist_ok=True)
    identity = native_identity()
    lease = claim_slot(SL / "results/.cpu-slots-20261017", identity, "ToMpathy-batteries-and-art")
    child = None
    started = time.monotonic()
    state = dict(startedAt=datetime.now(UTC).isoformat(), owner=identity, lease=str(lease[0]), threads=1,
                 gpu=False, resources=resources, phase="starting", scientificAdmission=False)
    try:
        save(args.run / "owner.json", state)
        with (args.run / "stdout.log").open("ab") as stdout, (args.run / "stderr.log").open("ab") as stderr:
            child = subprocess.Popen(["node", "scripts/engine-cpu-session.mjs", str(args.run.resolve()), str(lease[0])],
                                     cwd=ROOT, stdout=stdout, stderr=stderr, creationflags=0x08000000 | 0x4000)
            state.update(child=native_identity(child.pid), phase="running")
            save(args.run / "owner.json", state)
            while child.poll() is None:
                resources = resource_snapshot()
                if resources["ram_available_GiB"] < 16 or resources["commit_headroom_GiB"] < 16 or resources["disk_free_GiB"] < 20:
                    raise RuntimeError("Shared resource floor reached; exact calls retained for resumption")
                if time.monotonic() - started > 48 * 3600 or (args.run / "STOP").exists():
                    raise RuntimeError("Bounded runtime or owner stop reached")
                save(args.run / "heartbeat.json", dict(at=datetime.now(UTC).isoformat(), elapsed=time.monotonic()-started, resources=resources))
                time.sleep(15)
            if child.returncode:
                raise RuntimeError(f"CPU session exited {child.returncode}")
        save(args.run / "complete.json", dict(at=datetime.now(UTC).isoformat(), elapsed=time.monotonic()-started, scientificAdmission=False))
    except BaseException as error:
        if child is not None and child.poll() is None:
            current = native_identity(child.pid)
            if current != state.get("child"):
                raise RuntimeError("Owned process identity changed; cleanup refused") from error
            subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], check=True, creationflags=0x08000000)
            child.wait(timeout=30)
        save(args.run / "failed.json", dict(at=datetime.now(UTC).isoformat(), error=repr(error)))
        raise
    finally:
        if child is None or child.poll() is not None:
            release_slot(*lease)

if __name__ == "__main__":
    main()
