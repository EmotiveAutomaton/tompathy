"""Small serial CPU scorer comparison; software measurement, not admission."""
import argparse
import gc
import json
import os
from pathlib import Path
from time import monotonic

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from scipy.stats import spearmanr
from tompathy_engine.ledger.ids import digest
from tompathy_engine.preview.readers import LocalReader
from tompathy_engine.preview.surface import words

parser = argparse.ArgumentParser()
parser.add_argument("--capture", default=".local/preview-live-blog.json")
parser.add_argument("--words", type=int, default=200)
parser.add_argument("--threads", type=int, default=1)
parser.add_argument("--out", default="evidence/reader-parity.json")
parser.add_argument("--compare", choices=("int8", "int8-channel"), default="int8")
args = parser.parse_args()
capture = json.loads(Path(args.capture).read_text(encoding="utf8"))
text = " ".join(" ".join(r["anchor"]["exact"] for r in capture["regions"]).split()[:args.words])
rows, timings = [], []
for precision in ("float32", args.compare):
    start = monotonic()
    reader = LocalReader(".local/preview-readers/qwen", device="cpu", threads=args.threads, precision=precision)
    loaded = monotonic()
    tokens = reader.score(text)
    rows.append({(w["start"], w["end"]): w["nats"] for w in words(text, tokens) if w["content"] and not w["held"]})
    timings.append({"precision": precision, "loadSeconds": loaded - start, "scoreSeconds": monotonic() - loaded, "reader": reader.identity})
    del reader
    gc.collect()
keys = sorted(set(rows[0]) & set(rows[1]))
count = max(1, (len(keys) + 9) // 10)
tops = [set(sorted(keys, key=lambda k: -row[k])[:count]) for row in rows]
result = {"source": capture["source"], "textSha256": digest(text), "words": len(text.split()), "timings": timings,
          "meanNats": [sum(row[k] for k in keys) / len(keys) for row in rows],
          "spearman": float(spearmanr(*[[row[k] for k in keys] for row in rows]).statistic),
          "topDecileJaccard": len(tops[0] & tops[1]) / len(tops[0] | tops[1]),
          "scientificAdmission": False, "scope": "One public excerpt, identical current scoring implementation, no cache and one CPU model resident at a time"}
Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
print(json.dumps(result, indent=2), flush=True)
