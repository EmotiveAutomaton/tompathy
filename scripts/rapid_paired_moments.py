"""TP73 cross-products for the matched openings; only aggregate sufficient statistics return."""

import argparse
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path("/home/agent/tompathy-open/rapid-20261127")
SOURCE = "258d14c8405973cb7db874895a18a46e054241c3638e89d39bf73aef7941f02d"
OUT = ROOT / "TP73-paired-moments-a"
THREADS = (
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def pin(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (OUT / name).open("x", encoding="utf8") as f:
        json.dump(value, f, allow_nan=False)


def check():
    if time.time() >= 1795968000 or any(
        (p / "STOP").exists()
        for p in (
            OUT,
            ROOT,
            ROOT.parent / "week-20261122",
            ROOT.parent / "person-teacher-20261121",
            ROOT.parent / "word-table-20261120",
        )
    ):
        raise RuntimeError("Packet cutoff or STOP")
    available = next(
        int(line.split()[1])
        for line in Path("/proc/meminfo").read_text().splitlines()
        if line.startswith("MemAvailable:")
    )
    if available < 8 * 1024**2:
        raise RuntimeError("Spark memory floor")


def cross_products(x, y):
    x = x - x.mean(axis=0)
    y = y - y.mean(axis=0)
    return x.T @ x, x.T @ y, np.sum(y * y, axis=0)


def moments(x, y):
    n, posts, width = x.shape
    if (
        y.shape != (n, posts, 2, 8)
        or n < 2
        or posts != 20
        or not np.isfinite(x).all()
        or not np.isin(y, np.arange(1, 6)).all()
    ):
        raise ValueError("Incomplete paired opening table")
    result = {}
    for level, a, b in (
        ("post", x.reshape(n * posts, width), y.reshape(n * posts, 16)),
        ("author", x.mean(1), y.mean(1).reshape(n, 16)),
    ):
        xx, xy, yy = cross_products(a, b)
        result.update({level + "XX": xx, level + "XY": xy, level + "YY": yy})
    a, b = x[:, :10].mean(1), x[:, 10:].mean(1)
    a -= a.mean(0)
    b -= b.mean(0)
    result.update(left=a.T @ a, between=a.T @ b, right=b.T @ b)
    return result


def run(h):
    import fcntl

    if any(os.environ.get(v) != "1" for v in THREADS):
        raise ValueError("One numerical thread required")
    os.setpriority(os.PRIO_PROCESS, 0, 10)
    os.sched_setaffinity(0, {max(os.sched_getaffinity(0))})
    check()
    with (ROOT / "TP61-vector-cpu.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        OUT.mkdir(exist_ok=False, mode=0o700)
        owner = {
            "pid": os.getpid(),
            "bootId": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "startTicks": Path("/proc/self/stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()[19],
            "job": "TP73-paired-moments",
        }
        save("owner.json", owner)
        try:
            raw = sys.stdin.buffer.read(2_000_001)
            if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != h:
                raise ValueError("Unbound paired input")
            with np.load(io.BytesIO(raw), allow_pickle=False) as d:
                if set(d.files) != {"opening", "values"}:
                    raise ValueError("Unexpected input fields")
                keys = d["opening"]
                y = d["values"]
            if (
                keys.shape != y.shape[:2]
                or keys.shape[0] > 2273
                or keys.dtype != np.dtype("S64")
            ):
                raise ValueError("Invalid opening roster")
            folder = ROOT / "TP61-vectors-b"
            p = folder / "receipt.json"
            if pin(p) != SOURCE or read(folder / "complete.json") != {
                "sourceReceiptPin": SOURCE
            }:
                raise ValueError("Original vector receipt differs")
            scratch = read(p)["localScratch"]
            ip = folder / "opening-ids.npy"
            vp = folder / "openings.npy"
            if pin(ip) != scratch["ids"] or pin(vp) != scratch["vectors"]:
                raise ValueError("Original vector scratch differs")
            ids = np.load(ip, mmap_mode="r", allow_pickle=False)
            v = np.load(vp, mmap_mode="r", allow_pickle=False)
            index = np.searchsorted(ids, keys)
            if np.any(index >= len(ids)) or not np.array_equal(ids[index], keys):
                raise ValueError("Unmatched opening")
            check()
            result = moments(v[index].astype(float), y.astype(float))
            check()
            if len(list(Path("/proc/self/task").iterdir())) != 1:
                raise ValueError("Actual thread count differs")
            f = OUT / "moments.npz"
            with f.open("xb") as stream:
                np.savez_compressed(stream, **result)
            save(
                "receipt.json",
                {
                    "owner": owner,
                    "source": SOURCE,
                    "codePin": pin(Path(__file__)),
                    "inputPin": h,
                    "momentsPin": pin(f),
                    "authors": len(keys),
                    "posts": keys.size,
                    "numericalThreads": 1,
                },
            )
            save("complete.json", {"sourceReceiptPin": pin(OUT / "receipt.json")})
        except Exception as exc:
            save("failed.json", {"reason": str(exc), "owner": owner})
            raise


def verify():
    import fcntl

    with (ROOT / "TP61-vector-cpu.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        p = OUT / "receipt.json"
        r = read(p)
        o = r["owner"]
        if (
            {i.name for i in OUT.iterdir()}
            != {"owner.json", "moments.npz", "receipt.json", "complete.json"}
            or o != read(OUT / "owner.json")
            or r["source"] != SOURCE
            or r["codePin"] != pin(Path(__file__))
            or read(OUT / "complete.json") != {"sourceReceiptPin": pin(p)}
            or pin(OUT / "moments.npz") != r["momentsPin"]
        ):
            raise ValueError("Unexpected result inventory or binding")
        st = Path("/proc") / str(o["pid"]) / "stat"
        if Path("/proc/sys/kernel/random/boot_id").read_text().strip() != o[
            "bootId"
        ] or (
            st.exists()
            and st.read_text().rsplit(")", 1)[1].split()[19] == o["startTicks"]
        ):
            raise ValueError("Exact native exit is unverified")
        print(
            json.dumps(
                {
                    "sourceReceiptPin": pin(p),
                    "nativeExited": True,
                    "cpuLeaseReacquired": True,
                    "receipt": r,
                }
            )
        )


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("action", choices=["run", "verify"])
    args.add_argument("binding", nargs="?")
    a = args.parse_args()
    if a.action == "run":
        run(a.binding)
    else:
        verify()
