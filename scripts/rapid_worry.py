"""Q34. Preserve the event and sentence ordering of the registered source files."""

import gzip
import json
import time
from itertools import islice

import numpy as np
import week_spark as week
from word_table_lane import now, pin, read, write


def run(root, out, items, cfg, guard):
    old = week.ROOT / "registration.json"
    if pin(old) != cfg["weekRegistration"]:
        raise ValueError("Original registration differs")
    registration = read(old)
    for path, h in registration["models"].items():
        if path == "worry.npz" or path.startswith("worry/"):
            guard.check()
            if pin(week.MODELS / path) != h:
                raise ValueError("Worry model differs")
    sources = week.ROOT / "Q21-inputs.json"
    if pin(sources) != registration["manifests"]["Q21"]:
        raise ValueError("Q21 sentence manifest differs")
    files = read(sources)["files"]
    encode = week.encoder("worry", 128)
    with np.load(week.MODELS / "worry.npz", allow_pickle=False) as params:
        weights, bias = params["weights"], params["bias"]
    total = 6600 + 51557
    start = time.monotonic()
    count = 0
    parts = {}

    def score(name, texts):
        nonlocal count
        pos = 0
        while batch := list(islice(texts, 100)):
            guard.check()
            vectors = encode(batch)
            week.persist(
                out / f"{name}-{pos:07d}.npz", worry=vectors @ weights.T + bias
            )
            count += len(batch)
            pos += len(batch)
            elapsed = time.monotonic() - start
            progress = {
                "rows": count,
                "total": total,
                "part": name,
                "at": now(),
                "elapsedSeconds": elapsed,
            }
            if count == 100:
                hours = elapsed * total / 100 / 3600
                write(
                    out / "first100.json",
                    dict(
                        **progress,
                        projectedHours=hours,
                        packetHours=1,
                        overThreeTimes=hours > 3,
                    ),
                )
            write(out / "progress.json", progress)
        parts[name] = pos

    score("envent", (r["text"] for r in items))
    for name in ("Q11", "Q12"):
        path = week.ROOT / "Q21-inputs" / (name + "-sentences.jsonl.gz")
        if pin(path) != files[path.name]:
            raise ValueError("Original sentence block differs")
        with gzip.open(path, "rt", encoding="utf8") as f:
            score(name, (json.loads(line) for line in f))
    if count != total or parts["envent"] != 6600:
        raise ValueError("Incomplete worry roster")
    return {
        "parts": parts,
        "rows": count,
        "seconds": time.monotonic() - start,
        "essays": "Held news-reaction release has empathy and distress but no trait scores.",
    }
