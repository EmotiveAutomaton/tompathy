"""Warm exact real-model calls serially, with a bounded offline CPU budget."""
import argparse
import ctypes
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, sleep

os.environ.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", CUDA_VISIBLE_DEVICES="-1")
if os.name == "nt":
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
        raise OSError("Could not lower owned preparation priority")

    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ("total", "available", "page", "freepage", "virtual", "freevirtual", "extended")]

    def guard():
        while True:
            status = Memory()
            status.length = ctypes.sizeof(status)
            if not kernel.GlobalMemoryStatusEx(ctypes.byref(status)) or status.available < 16 * 2**30:
                print("Preparation stopped to preserve shared memory headroom", flush=True)
                os._exit(70)
            sleep(1)
    threading.Thread(target=guard, daemon=True).start()

from tompathy_engine.adapters.capture import validate_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import build_preview
from tompathy_engine.transcribe.cache import Cache

parser = argparse.ArgumentParser()
parser.add_argument("stage", choices=("readers", "goals", "clef", "payoff"))
parser.add_argument("--capture", default=".local/art-current-capture.json")
parser.add_argument("--url")
parser.add_argument("--config")
parser.add_argument("--seconds", type=int, default=1200)
args = parser.parse_args()
if not 30 <= args.seconds <= 3600:
    raise ValueError("Preparation budget must be 30–3,600 seconds")
capture = validate_capture(json.loads(Path(args.capture).read_text(encoding="utf8")))
started = monotonic()
report = {"stage": args.stage, "startedAt": datetime.now(UTC).isoformat(), "revision": capture["revision"],
          "budgetSeconds": args.seconds, "scientificAdmission": False}
packet = build_preview(build_packet(capture))
backend = None
module = next((m for m in packet["preview"]["modules"] if m["id"] == {"clef": "techniques"}.get(args.stage, args.stage)), None)
if module:
    module.update(status="running", detail="Explicit bounded offline cache preparation")
last_progress = None


def check():
    if monotonic() - started >= args.seconds:
        raise TimeoutError("Offline preparation budget reached; exact completed calls remain cached")


def publish():
    global last_progress
    Packet.model_validate(packet)
    if module and module.get("completed") != last_progress:
        last_progress = module.get("completed")
        print(json.dumps({"stage": args.stage, "completed": last_progress, "total": module.get("total")}), flush=True)


try:
    if args.stage == "clef":
        from tompathy_engine.preview.clef import Clef, techniques
        backend = Clef(json.loads(Path(args.config).read_text(encoding="utf8")))
        runner = techniques(backend, Cache(Path(".local/preview-score-cache/clef.sqlite")))
        runner(packet, check, publish)
    elif args.stage == "goals":
        from tompathy_engine.preview.fixed_backend import FixedQwen
        from tompathy_engine.preview.judgments import goals
        backend = FixedQwen(args.url, timeout=300)
        runner = goals(backend, Cache(Path(".local/preview-score-cache/judgments.sqlite")))
        runner(packet, check, publish)
    else:
        from tompathy_engine.preview.readers import LocalReader
        reader = LocalReader(".local/preview-readers/qwen", ".local/preview-score-cache")
        if args.stage == "readers":
            from tompathy_engine.preview.surface import compare_readers, deviation_map
            second = LocalReader(".local/preview-readers/smol", ".local/preview-score-cache")
            print("Preparing whole-essay departures and reader comparison", flush=True)
            report["statistics"] = deviation_map(capture, reader, check)["statistics"]
            report["agreement"] = compare_readers(capture, [reader, second], check)
            report["metrics"] = [reader.metrics, second.metrics]
        else:
            from tompathy_engine.preview.payoff import payoff_steps
            for _ in payoff_steps(packet, reader, check, publish):
                pass
    report["completed"] = True
    if module:
        module["status"] = "complete"
except TimeoutError as error:
    report.update(completed=False, limit=str(error))
    if module:
        module["status"] = "skipped"
except Exception as error:
    report.update(completed=False, error=type(error).__name__)
    if module:
        module["status"] = "failed"
    raise
finally:
    report.update(seconds=monotonic() - started,
                  modules=packet["preview"]["modules"], goalNodes=len(packet.get("goalHierarchy", {}).get("nodes", [])),
                  payoff=packet["preview"].get("payoff"))
    if backend:
        report["metrics"] = backend.metrics
        if hasattr(backend, "close"):
            backend.close()
    Path(f"evidence/art-preparation-{args.stage}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"statistics", "agreement", "modules"}}), flush=True)
