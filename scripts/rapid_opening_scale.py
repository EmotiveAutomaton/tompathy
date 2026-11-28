"""TP61(a) pooled opening calibration on the frozen Q20 vectors held on Spark."""

import argparse
import gzip
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
import rapid_head_vectors as vectors

SOURCE = "258d14c8405973cb7db874895a18a46e054241c3638e89d39bf73aef7941f02d"
OUT = vectors.ROOT / "TP61-opening-scale-a"
LOCK = vectors.ROOT / "TP61-vector-cpu.lock"
BOOT = Path("/proc/sys/kernel/random/boot_id")


def roster_counts(rows):
    counts = Counter()
    authors = set()
    eligible = 0
    for author, sides in rows:
        if author in authors or len(sides) != 3:
            raise ValueError("Invalid date-half roster")
        authors.add(author)
        if sides[0] and sides[1]:
            eligible += 1
            for side in sides[:2]:
                counts.update(key.encode("ascii") for key, _, _ in side)
    return len(authors), eligible, counts


def pooled(ids, values, counts, check, batch=2048):
    keys = np.asarray(sorted(counts), dtype=ids.dtype)
    indices = np.searchsorted(ids, keys)
    if np.any(indices >= len(ids)) or not np.array_equal(keys, ids[indices]):
        raise ValueError("Missing calibration opening")
    n = sum(counts.values())
    sx = np.zeros(values.shape[1])
    gram = np.zeros((len(sx), len(sx)))
    for start in range(0, len(indices), batch):
        check()
        take = slice(start, start + batch)
        x = values[indices[take]].astype(np.float64)
        w = np.asarray([counts[k] for k in keys[take]], dtype=float)
        wx = x * w[:, None]
        sx += wx.sum(axis=0)
        gram += x.T @ wx
    mean = sx / n
    cov = (gram + gram.T) / (2 * n) - np.outer(mean, mean)
    if not np.isfinite(cov).all() or np.any(cov.diagonal() < -1e-12):
        raise ValueError("Invalid covariance")
    return mean, cov


def start_ticks(path):
    return path.read_text().rsplit(")", 1)[1].split()[19]


def run():
    import fcntl

    if any(
        os.environ.get(k + "_NUM_THREADS") != "1"
        for k in ("MKL", "OMP", "OPENBLAS", "NUMEXPR")
    ):
        raise ValueError("Launch with one numerical thread")
    os.setpriority(os.PRIO_PROCESS, 0, 15)
    os.sched_setaffinity(0, {max(os.sched_getaffinity(0))})
    with LOCK.open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        vectors.check(OUT)
        OUT.mkdir(mode=0o700)
        owner = {
            "pid": os.getpid(),
            "bootId": BOOT.read_text().strip(),
            "startTicks": start_ticks(Path("/proc/self/stat")),
        }
        vectors.dump(OUT / "owner.json", owner)
        try:
            src = vectors.ROOT / "TP61-vectors-b"
            receipt = vectors.read(vectors.bound(src / "receipt.json", SOURCE))
            if (
                vectors.read(src / "complete.json") != {"sourceReceiptPin": SOURCE}
                or receipt["rosterPin"] != vectors.JOIN
            ):
                raise ValueError("Unbound author-vector return")
            roster = vectors.bound(
                vectors.ROOT / "inputs/TP61-author-order.jsonl.gz", vectors.JOIN
            )
            with gzip.open(roster, "rt", encoding="utf8") as f:
                total, eligible, counts = roster_counts(map(json.loads, f))
            if (total, eligible) != (5428, 5409):
                raise ValueError("Dated cohort differs")
            scratch = receipt["localScratch"]
            ids, values = [
                np.load(
                    vectors.bound(src / name, scratch[key]),
                    mmap_mode="r",
                    allow_pickle=False,
                )
                for name, key in (
                    ("opening-ids.npy", "ids"),
                    ("openings.npy", "vectors"),
                )
            ]
            mean, cov = pooled(ids, values, counts, lambda: vectors.check(OUT))
            vectors.check(OUT)
            if len(list(Path("/proc/self/task").iterdir())) != 1:
                raise RuntimeError("Actual thread count differs")
            digest = vectors.save(OUT, "scale.npz", mean=mean, covariance=cov)
            vectors.dump(
                OUT / "receipt.json",
                {
                    "owner": owner,
                    "source": SOURCE,
                    "roster": vectors.JOIN,
                    "authors": eligible,
                    "openings": sum(counts.values()),
                    "distinct": len(counts),
                    "scalePin": digest,
                    "threads": 1,
                    "codePin": vectors.pin(Path(__file__)),
                    "helperPin": vectors.pin(Path(vectors.__file__)),
                },
            )
            vectors.dump(
                OUT / "complete.json",
                {"sourceReceiptPin": vectors.pin(OUT / "receipt.json")},
            )
        except Exception as exc:
            vectors.dump(OUT / "failed.json", {"owner": owner, "reason": str(exc)})
            raise


def verify():
    import fcntl

    with LOCK.open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        files = {p.name: vectors.pin(p) for p in OUT.iterdir()}
        if set(files) != {"scale.npz", "owner.json", "receipt.json", "complete.json"}:
            raise ValueError("Unexpected terminal inventory")
        r = vectors.read(OUT / "receipt.json")
        o = vectors.read(OUT / "owner.json")
        proc = Path("/proc") / str(o["pid"]) / "stat"
        if (
            o != r["owner"]
            or BOOT.read_text().strip() != o["bootId"]
            or (proc.exists() and start_ticks(proc) == o["startTicks"])
            or (r["source"], r["roster"], r["scalePin"], r["codePin"], r["helperPin"])
            != (
                SOURCE,
                vectors.JOIN,
                files["scale.npz"],
                vectors.pin(Path(__file__)),
                vectors.pin(Path(vectors.__file__)),
            )
            or vectors.read(OUT / "complete.json")
            != {"sourceReceiptPin": files["receipt.json"]}
        ):
            raise ValueError("Exit, identity or source binding differs")
        print(
            json.dumps(
                {
                    "nativeExited": True,
                    "cpuLeaseReacquired": True,
                    "files": files,
                    "receipt": r,
                }
            )
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["run", "verify"])
    if p.parse_args().action == "run":
        run()
    else:
        verify()
