"""Serial CPU batteries for an explicitly assigned, dedicated ToMpathy service.

Start only after reserving one shared CPU slot. This script never starts a
service, downloads weights, changes another project, or uses a GPU.
"""
import argparse
import ctypes
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

os.environ.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", CUDA_VISIBLE_DEVICES="-1")

from tompathy_engine.preview.fixed_backend import FixedQwen
from tompathy_engine.preview.judgments import fixed_reader
from tompathy_engine.transcribe.admission import battery
from tompathy_engine.transcribe.batteries import constructed
from tompathy_engine.transcribe.cache import Cache
from tompathy_engine.ledger.ids import digest


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Exclusively assigned CPU Ollama service")
    parser.add_argument("--cpu-slot", required=True, help="Operator's confirmed shared CPU slot allocation")
    parser.add_argument("--out", type=Path, default=Path(".local/engine-question-admissions"))
    parser.add_argument("--questions", default="Q8,Q9,Q5,Q1,Q3,Q4,Q7")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    questions = args.questions.split(",")
    if not args.cpu_slot.strip() or any(q not in {"Q8", "Q9", "Q5", "Q1", "Q3", "Q4", "Q7"} for q in questions) or len(set(questions)) != len(questions):
        raise ValueError("Supply a confirmed CPU slot and distinct supported questions")
    if os.name == "nt":
        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise OSError("Could not lower battery process priority")
    args.out.mkdir(parents=True, exist_ok=True)
    backend = FixedQwen(args.url, timeout=600)
    reader = fixed_reader(backend, Cache(args.out / "calls.sqlite"))
    original_ask = reader.ask
    progress = {}
    def tracked_ask(*positional, **keywords):
        if (args.out.parent / "STOP").exists():
            raise RuntimeError("Owner requested a checkpoint stop")
        progress.update(at=datetime.now(UTC).isoformat(), phase="calling")
        atomic(args.out / "progress.status", progress)
        try:
            return original_ask(*positional, **keywords)
        finally:
            progress["completed"] += 1
            progress.update(at=datetime.now(UTC).isoformat(), phase="between-items")
            atomic(args.out / "progress.status", progress)
    reader.ask = tracked_ask
    try:
        for question in questions:
            target = args.out / f"{question}.json"
            # Never replace a prior receipt or treat its pin as current silently.
            items = constructed(question)
            if target.exists():
                previous = json.loads(target.read_text(encoding="utf8"))
                if not args.resume or previous.get("transcriber_pin") != reader.pin or previous.get("battery_hash") != digest(items):
                    raise FileExistsError(f"Existing receipt is not an exact resumable run: {target}")
                continue
            progress.update(question=question, completed=0, total=len(items), pin=reader.pin)
            (args.out / f"{question}.items").write_text(json.dumps(items, indent=2) + "\n", encoding="utf8")
            started = monotonic()
            result = battery(reader, question, items)
            elapsed = monotonic() - started
            target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
            timing = {"question": question, "pin": reader.pin, "completedAt": datetime.now(UTC).isoformat(), "seconds": elapsed, "items": len(items), "passed": result["passed"], "metrics": dict(backend.metrics), "scientificAdmission": False}
            (args.out / f"{question}.timing").write_text(json.dumps(timing, indent=2) + "\n", encoding="utf8")
            print(json.dumps(timing), flush=True)
    finally:
        backend.close(recover=True)


if __name__ == "__main__":
    main()
