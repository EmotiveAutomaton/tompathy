"""Amendment CU precondition, using only the fixed chat vectors and first original blog shard."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path


def pin(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def bound(path, h):
    if pin(path) != h:
        raise ValueError("Source differs: " + path.name)
    return path


def read(path):
    return json.loads(path.read_bytes())


HEAD = "7f5bfe1ff5ab5e4a0b93072bb7e1f54f73466ab01ade90fc2ad2c4041d12e7ae"
WEEKPIN = "22e90646c03230dd8c00fe1cb98ff38149adc445467fd11c8050916ca8fcfbb9"
Q20 = "d7520ece843c5805b26be7b746c452eedc09b71940b263ed241251bed33bcaef"


def gaps(vectors, head, expected):
    import numpy as np
    from scipy.special import expit

    calculated = expit(vectors @ head["weights"].T + head["bias"])
    if (
        calculated.shape != expected.shape
        or not np.isfinite([calculated, expected]).all()
    ):
        raise ValueError("Misaligned or nonfinite tag matrix")
    return float(np.max(np.abs(calculated - expected)))


def chat():
    import numpy as np
    from tompathy_engine.eval.readers.tp39 import TP28, saved
    from week_pride_inputs import FROZEN, SOURCE

    root = Path(".local/nine-channel/tp28-a")
    baseline = read(bound(FROZEN / "receipt.json", SOURCE))
    targets = read(bound(root / "receipt.json", TP28))
    path = saved(root, "ed/scores.npz", targets)
    with (
        np.load(saved(FROZEN, "vectors.npz", baseline), allow_pickle=False) as vectors,
        np.load(path, allow_pickle=False) as original,
    ):
        with np.load(
            saved(FROZEN, "ed-profile-forecasts.npz", baseline), allow_pickle=False
        ) as roster:
            from tompathy_engine.eval.readers.tp36 import verify_order

            verify_order(path, roster["ids"])
        head = Path(".local/week-20261122/TP58-candidate-b/payload/models/tags.npz")
        with np.load(bound(head, HEAD), allow_pickle=False) as weights:
            scores = original["scores"]
            if scores.shape != (24850, 19):
                raise ValueError("Incomplete chat scores")
            gap = gaps(vectors["ed"], weights, scores)
    return {
        "source": "chat",
        "rows": 24850,
        "columns": 19,
        "maxTagGap": gap,
        "passed": gap <= 1e-5,
        "sourceReceipts": [SOURCE, TP28],
        "headPin": HEAD,
    }


def blog():
    import numpy as np
    from word_table_lane import now

    week = Path("/home/agent/tompathy-open/week-20261122")
    root = week / "jobs/Q20"
    r = read(bound(root / "receipt.json", Q20))
    cfg = read(bound(week / "registration.json", WEEKPIN))
    manifest = read(bound(week / "Q20-inputs.json", cfg["manifests"]["Q20"]))
    name = min(manifest["files"])
    with gzip.open(
        bound(week / "Q20-inputs" / name, manifest["files"][name]),
        "rt",
        encoding="utf8",
    ) as f:
        ids = [json.loads(line)[0] for line in f]
    with (
        np.load(bound(week / "models/tags.npz", HEAD), allow_pickle=False) as head,
        np.load(
            bound(root / "placebo-heads.npz", r["outputs"]["placebo-heads.npz"]),
            allow_pickle=False,
        ) as placebo,
    ):
        pos = 0
        trained = control = 0.0
        while pos < len(ids):
            if (week.parent / "rapid-20261127/STOP").exists():
                raise RuntimeError("Owner STOP")
            suffix = f"{pos:08d}.npz"
            file = "scores-" + suffix
            with (
                np.load(
                    bound(root / file, r["outputs"][file]), allow_pickle=False
                ) as orig,
                np.load(
                    bound(root / "vectors" / suffix, r["vectors"][suffix]),
                    allow_pickle=False,
                ) as data,
            ):
                x = data["x"]
                n = len(x)
                if not n or orig["ids"].tolist() != ids[pos : pos + n]:
                    raise ValueError("First source shard order differs")
                trained = max(trained, gaps(x, head, orig["tags"]))
                diff = np.abs(x @ placebo["weights"].T - orig["placebo"])
                if not np.isfinite(diff).all():
                    raise ValueError("Nonfinite placebo difference")
                control = max(control, float(diff.max()))
            pos += n
    return {
        "source": "first Q20 input shard",
        "rows": pos,
        "columns": 19,
        "maxTagGap": trained,
        "maxPlaceboGap": control,
        "passed": max(trained, control) <= 1e-5,
        "sourceReceiptPin": Q20,
        "shardPin": manifest["files"][name],
        "headPin": HEAD,
        "at": now(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["chat", "blog"])
    parser.add_argument("output", type=Path)
    a = parser.parse_args()
    for key in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[key] = "1"
    result = (chat if a.source == "chat" else blog)()
    with a.output.open("x", encoding="utf8") as f:
        json.dump(result, f, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps(result))
