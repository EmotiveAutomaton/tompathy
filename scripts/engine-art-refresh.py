"""Complete exact current-capture calls, then populate the normal companion cache."""
import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
import shutil
from pathlib import Path
from time import monotonic

from fastapi.testclient import TestClient
from tompathy_engine.adapters.capture import validate_capture
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import build_preview
from tompathy_engine.preview.fixed_backend import FixedQwen
from tompathy_engine.preview.judgments import goals, fixed_reader, techniques
from tompathy_engine.preview.readers import LocalReader
from tompathy_engine.serve.app import create_app
from tompathy_engine.transcribe.cache import Cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    capture = validate_capture(json.loads((args.run / "capture.json").read_text(encoding="utf8")))
    cache_root = Path(".local/preview-score-cache")
    records = [json.loads(p.read_text(encoding="utf8")) for p in sorted((args.run / "admissions").glob("Q*.json"))]
    if {r["question_id"] for r in records} != {"Q8", "Q9", "Q5", "Q1", "Q3", "Q4", "Q7"}:
        raise ValueError("Complete fresh battery receipt set required")
    active_admissions = Path(".local/engine-question-admissions")
    active_admissions.mkdir(parents=True, exist_ok=True)
    (active_admissions / "complete.receipt").unlink(missing_ok=True)
    hashes = {}
    for source in (args.run / "admissions").glob("Q*.json"):
        temporary = active_admissions / (source.name + ".tmp")
        shutil.copy2(source, temporary)
        temporary.replace(active_admissions / source.name)
        hashes[source.name] = sha256(source.read_bytes()).hexdigest()
    complete = active_admissions / "complete.tmp"
    complete.write_text(json.dumps({"run": str(args.run.resolve()), "files": hashes}, sort_keys=True), encoding="utf8")
    complete.replace(active_admissions / "complete.receipt")
    backend = FixedQwen(args.url, timeout=600)
    cache = Cache(cache_root / "judgments.sqlite")
    reader = fixed_reader(backend, cache, records)
    goal_runner, technique_runner = goals(backend, cache), techniques(reader)
    readers = [LocalReader(Path(".local/preview-readers") / name, cache_root, device="cpu", threads=1) for name in ("qwen", "smol")]
    started = monotonic()
    def check():
        if (args.run / "STOP").exists() or monotonic() - started > 24 * 3600:
            raise RuntimeError("Art preparation stopped at its saved-call boundary")
    def save(packet):
        value = {"at": datetime.now(UTC).isoformat(), "revision": capture["revision"],
                 "modules": packet["preview"]["modules"], "elapsed": monotonic()-started}
        temp = args.run / "art-progress.tmp"
        temp.write_text(json.dumps(value, indent=2), encoding="utf8")
        temp.replace(args.run / "art-progress.json")
    try:
        packet = build_preview(build_packet(capture), readers=readers, goal_runner=goal_runner,
            technique_runner=technique_runner, correction_reader=reader, check=check, partial=save,
            deadline=monotonic() + 24 * 3600)
        Packet.model_validate(packet)
        (args.run / "art-packet.json").write_text(json.dumps(packet), encoding="utf8")
        # Populate the same keyed cache used by Load cached real preview.
        token = "1" * 64
        app = create_app(token=token, origins=[], preview_readers=readers, preview_goals=goal_runner,
            preview_techniques=technique_runner, preview_correction_reader=reader,
            preview_cache=cache_root, preview_budget=600)
        with TestClient(app, base_url="http://127.0.0.1") as client:
            body = {"requestId": "art-refresh", "artifact": capture, "scope": "artifact", "mode": "preview"}
            response = client.post("/v1/analyze", headers={"Authorization": f"Bearer {token}"}, json=body)
            response.raise_for_status()
            saved = response.json()
            replay = client.post("/v1/analyze", headers={"Authorization": f"Bearer {token}"}, json=body | {"requestId": "art-replay", "preferCache": True})
            replay.raise_for_status()
            assert replay.json()["preview"]["cachedAt"]
        report = {"at": datetime.now(UTC).isoformat(), "revision": capture["revision"],
                  "elapsed": monotonic()-started, "modules": saved["preview"]["modules"],
                  "cacheReplayVerified": True, "scientificAdmission": False}
        (args.run / "art-refresh.json").write_text(json.dumps(report, indent=2), encoding="utf8")
        print(json.dumps(report), flush=True)
    finally:
        backend.close(recover=True)

if __name__ == "__main__":
    main()
