"""Pinned, CPU-only Clef runtime, isolated from the engine's reader environment.

Run with .local/clef-flash/venv's Python. Only this process is terminated by
the memory guard. No research processes or GPU services are inspected or changed.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
import secrets
import select
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local/clef-flash"
MODEL = LOCAL / "model"
REVISION = "8b2e5fd17c09fd49bc2880b805d5323ec7ff4ff3"
MANIFEST = "da20f62b359288afa2d7e15b493557d276a3ab29d6b1bf9acc0c3e56bed3551c"
LIMIT = 4096


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def load():
    os.environ.update(CUDA_VISIBLE_DEVICES="-1", HIP_VISIBLE_DEVICES="-1",
                      HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                      TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_TELEMETRY="1")
    import psutil
    process = psutil.Process()
    if os.name == "nt":
        process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    manifest = json.loads((LOCAL / "manifest.json").read_text(encoding="utf8"))
    if manifest["revision"] != REVISION or sha(LOCAL / "manifest.json") != MANIFEST:
        raise ValueError("Unexpected release revision")
    for name, entry in manifest["files"].items():
        if Path(name).name != name or sha(MODEL / name) != entry["sha256"]:
            raise ValueError(f"Local release checksum mismatch: {name}")
    if psutil.virtual_memory().available < 28 * 2**30:
        raise RuntimeError("Clef needs 28 GiB free to start; research headroom reserved")
    resources = {"peakRssGiB": 0., "minimumAvailableGiB": psutil.virtual_memory().available / 2**30}

    def guard():
        while True:
            available, rss = psutil.virtual_memory().available / 2**30, process.memory_info().rss / 2**30
            resources["peakRssGiB"] = max(resources["peakRssGiB"], rss)
            resources["minimumAvailableGiB"] = min(resources["minimumAvailableGiB"], available)
            if available < 16 or rss > 28:
                print("Clef stopped: reserved memory headroom reached", file=sys.stderr, flush=True)
                os._exit(70)
            time.sleep(1)
    threading.Thread(target=guard, daemon=True).start()
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    if torch.version.cuda is not None:
        raise RuntimeError("Use the isolated CPU-only torch build")
    sys.path.insert(0, str(MODEL))
    import joint_schema_model as release
    started = time.perf_counter()
    model, processor = release.load_release_model(MODEL, device="cpu", dtype=torch.bfloat16,
                                                  local_files_only=True, attn_implementation="sdpa")
    settings = {"release": REVISION, "manifest": sha(LOCAL / "manifest.json"),
                "runtime": sha(Path(__file__)), "device": "cpu", "dtype": "bfloat16", "threads": 1,
                "packages": {p: importlib.metadata.version(p) for p in
                             ("torch", "transformers", "accelerate", "safetensors", "tokenizers")}}
    identity = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    health = {"identity": identity, "settings": settings, "loadSeconds": time.perf_counter() - started,
              "rssGiB": process.memory_info().rss / 2**30, "availableGiB": psutil.virtual_memory().available / 2**30}
    print(json.dumps({"loaded": health}), flush=True)

    @torch.inference_mode()
    def decide(request, cancelled=lambda: False):
        if set(request) != {"model", "state", "questions"} or request["model"] != "Cloudflare/clef-flash":
            raise ValueError("Expected pinned text-only SystemOne request")
        questions = request["questions"]
        if not isinstance(questions, dict) or not 1 <= len(questions) <= 8:
            raise ValueError("Supply 1–8 choice questions")
        for question in questions.values():
            if not isinstance(question, dict) or question.get("type") != "choice" or not isinstance(question.get("criteria"), dict) or not 2 <= len(question["criteria"]) <= 12:
                raise ValueError("Only bounded choice schemas are supported")
        started = time.perf_counter()
        # Encode the whole request before enforcing the bound: no silent state truncation.
        encoded = release.encode_record(processor.tokenizer, request, max_length=100000)
        if len(encoded.input_ids) > LIMIT:
            raise ValueError(f"Request exceeds {LIMIT} tokens; state was not truncated")
        def check_layer(_module, _inputs):
            if cancelled() or time.perf_counter() - started > 120:
                raise TimeoutError("Clef inference cancelled or reached its two-minute call bound")
        handles = [module.register_forward_pre_hook(check_layer) for module in model.modules()
                   if type(module).__name__.endswith("DecoderLayer")]
        try:
            logits = model(release.collate_records([encoded], processor.tokenizer.pad_token_id, torch.device("cpu")))[0]
        finally:
            for handle in handles:
                handle.remove()
        answers = {}
        for question, values in zip(encoded.questions, logits):
            if not torch.isfinite(values).all():
                raise ValueError("Model returned nonfinite logits")
            probabilities = dict(zip(question.option_ids, values.float().softmax(-1).tolist()))
            answers[question.question_id] = release.systemone_answer(questions[question.question_id], probabilities)
        return {"model": request["model"], "answers": answers,
                "usage": {"input_tokens": len(encoded.input_ids), "output_tokens": 0},
                "runtime": {"identity": identity, "seconds": time.perf_counter() - started, **resources}}
    return decide, health


def benchmark(decide, health, fixture, output):
    cases = json.loads(fixture.read_text(encoding="utf8"))
    report = {"scope": "Constructed local smoke check, not natural-text accuracy or research admission",
              "fixtureSha256": sha(fixture), "health": health, "cases": []}
    output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        response = decide(case["request"])
        result = {"id": case["id"], "expected": case["expected"], "response": response,
                  "correct": sum(response["answers"][key]["choice"] == expected for key, expected in case["expected"].items()),
                  "total": len(case["expected"])}
        report["cases"].append(result)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        print(json.dumps(result), flush=True)
    report["completed"] = True
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")


def serve(decide, health, config_path):
    token = secrets.token_hex(32)
    busy = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, value):
            body = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            return not self.headers.get("Origin") and secrets.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}")

        def do_GET(self):
            self.reply(200, health) if self.path == "/v1/health" and self.authorized() else self.reply(403, {"error": "Forbidden"})

        def do_POST(self):
            if self.path != "/v1/systemone" or not self.authorized():
                return self.reply(403, {"error": "Forbidden"})
            if not busy.acquire(blocking=False):
                return self.reply(409, {"error": "Clef is busy; no background queue"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 64000:
                    return self.reply(413, {"error": "Request size limit"})
                self.connection.settimeout(10)
                request = json.loads(self.rfile.read(size))
                disconnected, finished = threading.Event(), threading.Event()
                def watch_connection():
                    while not finished.wait(.25):
                        try:
                            ready, _, _ = select.select([self.connection], [], [], 0)
                            if ready and not self.connection.recv(1, socket.MSG_PEEK):
                                disconnected.set()
                                return
                        except OSError:
                            disconnected.set()
                            return
                threading.Thread(target=watch_connection, daemon=True).start()
                try:
                    response = decide(request, disconnected.is_set)
                finally:
                    finished.set()
                self.reply(200, response)
            except (ValueError, TypeError, KeyError) as error:
                self.reply(400, {"error": str(error)})
            except TimeoutError:
                self.reply(408, {"error": "Clef call cancelled or timed out"})
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                busy.release()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    config = {"url": f"http://127.0.0.1:{server.server_port}", "model": "Cloudflare/clef-flash",
              "revision": f"{REVISION}:cpu-bfloat16-1t", "sha256": health["settings"]["manifest"],
              "token": token, "identity": health["identity"]}
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf8")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("benchmark", "serve"))
    parser.add_argument("--fixture", type=Path, default=ROOT / "scripts/fixtures/clef-smoke.json")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/clef-cpu-benchmark.json")
    parser.add_argument("--config", type=Path, default=LOCAL / "connection.json")
    args = parser.parse_args()
    decide, health = load()
    if args.mode == "benchmark":
        benchmark(decide, health, args.fixture, args.out)
    else:
        serve(decide, health, args.config)
