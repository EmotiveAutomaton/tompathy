"""TP61(d). Compare the original within-author slope with seeded heads on the same posts."""

import gzip
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from rapid_nulls import heads

ROOT = Path("/home/agent/tompathy-open/rapid-20261127")
PREP = ROOT / "TP61-vectors-b"
PREP_PIN = "258d14c8405973cb7db874895a18a46e054241c3638e89d39bf73aef7941f02d"
TOOL = ROOT / "tools/0239d24e1ceb91fac0bcf9f1d979d93461c24ead"
sys.path.insert(0, str(TOOL))
from rapid_head_vectors import JOIN, WEEK, bound, check, dump, pin, read


def arrays():
    r = read(bound(PREP / "receipt.json", PREP_PIN))
    if read(PREP / "complete.json") != {"sourceReceiptPin": PREP_PIN}:
        raise ValueError("The prepared vector return differs")
    keys = np.load(
        bound(PREP / "opening-ids.npy", r["localScratch"]["ids"]), allow_pickle=False
    )
    x = np.load(
        bound(PREP / "openings.npy", r["localScratch"]["vectors"]),
        allow_pickle=False,
        mmap_mode="r",
    )
    lookup = {k.decode(): i for i, k in enumerate(keys)}
    chunks = []
    ys = []
    starts = []
    n = 0
    with gzip.open(
        bound(ROOT / "inputs/TP61-author-order.jsonl.gz", JOIN), "rt", encoding="utf8"
    ) as stream:
        for line in stream:
            _, sides = json.loads(line)
            entries = [(k, v) for side in sides for k, v, _ in side if v is not None]
            if len(entries) < 10:
                continue
            y = np.asarray([v for _, v in entries])
            if np.ptp(y) == 0:
                continue
            z = x[[lookup[k] for k, _ in entries]].astype(np.float64)
            if not np.any(np.ptp(z, axis=0)):
                continue
            y -= y.mean()
            ys.append(y / np.linalg.norm(y))
            chunks.append(z - z.mean(0))
            starts.append(n)
            n += len(y)
    if (len(starts), n) != (2536, 85591):
        raise ValueError("Trained TP52 author's slope cohort differs")
    return np.concatenate(chunks), np.concatenate(ys), np.asarray(starts)


def slopes(x, numerators, starts, w):
    fitted = x @ w.T
    norm = np.sqrt(np.add.reduceat(fitted * fitted, starts, axis=0))
    valid = norm > 0
    corr = np.divide(numerators @ w.T, norm, out=np.zeros_like(norm), where=valid)
    if (
        not np.isfinite(corr).all()
        or np.any(np.abs(corr) > 1 + 1e-9)
        or not np.all(valid.any(0))
    ):
        raise ValueError("Undefined within-author comparison")
    return (corr.sum(0) / valid.sum(0)).tolist(), valid.sum(0).tolist()


def run():
    import fcntl

    if any(
        os.environ.get(k) != "1"
        for k in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
    ):
        raise ValueError("One numerical thread required")
    os.setpriority(os.PRIO_PROCESS, 0, 15)
    os.sched_setaffinity(0, {max(os.sched_getaffinity(0))})
    out = ROOT / "TP61-slope-a"
    with (ROOT / "TP61-vector-cpu.lock").open("ab") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check(out)
        out.mkdir(exist_ok=False)
        owner = {
            "pid": os.getpid(),
            "startTicks": Path("/proc/self/stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()[19],
            "bootId": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "job": "TP61-slope",
            "codePin": pin(Path(__file__)),
            "nullsPin": pin(Path(__file__).with_name("rapid_nulls.py")),
        }
        dump(out / "owner.json", owner)
        try:
            x, y, starts = arrays()
            num = np.add.reduceat(x * y[:, None], starts, axis=0)
            with np.load(
                bound(
                    WEEK / "models/tags.npz",
                    "7f5bfe1ff5ab5e4a0b93072bb7e1f54f73466ab01ade90fc2ad2c4041d12e7ae",
                )
            ) as h:
                weights = h["weights"]
            results = {"iso": [], "rot": []}
            study_start = time.monotonic()
            for i in range(200):
                for kind in ("iso", "rot"):
                    check(out)
                    values, n = slopes(x, num, starts, heads(weights, "TP61", kind, i))
                    dump(
                        out / f"{kind}-{i:03d}.json",
                        {"set": i, "family": kind, "slopes": values, "authors": n},
                    )
                    results[kind].extend(values)
                if i == 0:
                    dump(
                        out / "pilot.json",
                        {
                            "setsPerFamily": 1,
                            "seconds": time.monotonic() - study_start,
                            "totalSetsPerFamily": 200,
                        },
                    )
            result = {
                "owner": owner,
                "sourceReceiptPin": PREP_PIN,
                "data": {"posts": len(x), "authors": len(starts)},
                "registeredTrainedSlope": 0.12711219968914428,
                "nullSlopes": results,
                "scope": "Null directions use frozen base vectors. The original worry slope uses the worry encoder.",
            }
            dump(out / "receipt.json", result)
            dump(out / "complete.json", {"sourceReceiptPin": pin(out / "receipt.json")})
        except Exception as exc:
            dump(out / "failed.json", {"owner": owner, "error": str(exc)})
            raise


if __name__ == "__main__":
    run()
