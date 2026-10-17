"""Bounded real-text CPU timing, not a scientific validation study."""
import json
import os
from pathlib import Path
from time import monotonic

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
from tompathy_engine.adapters.capture import make_capture
from tompathy_engine.preview.readers import LocalReader
from tompathy_engine.preview.surface import deviation_map

root = Path(__file__).resolve().parents[1]
source = (root / "src/content/essays-source.txt").read_text(encoding="utf8")
paragraphs, remaining = [], 3000
for paragraph in source.split("\n\n"):
    tokens = paragraph.split()
    if not tokens:
        continue
    paragraphs.append(" ".join(tokens[:remaining]))
    remaining -= len(tokens[:remaining])
    if remaining == 0:
        break
capture = make_capture(paragraphs, "local:curator-essay-benchmark", "First 3,000 words of the supplied curator essay", "2026-10-16T00:00:00Z")
start = monotonic()
reader = LocalReader(root / ".local/preview-readers/qwen", root / ".local/preview-score-cache")
loaded = monotonic()
result = deviation_map(capture, reader)
finished = monotonic()
receipt = {"source": "src/content/essays-source.txt", "captureRevision": capture["revision"], "words": 3000 - remaining,
           "reader": reader.identity, "loadSeconds": loaded - start, "scoreSeconds": finished - loaded,
           "attentionItems": len(result["attention"]), "statistics": result["statistics"],
           "scientificAdmission": False}
(root / "evidence").mkdir(exist_ok=True)
(root / "evidence/preview-cpu-int8-benchmark.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
print(json.dumps(receipt, indent=2))
