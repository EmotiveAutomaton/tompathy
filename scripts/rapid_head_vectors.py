"""Build the commissioned TP61 vector return from frozen Q20 rows on Spark, without inference."""

import gzip
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path

import numpy as np

WEEK = Path("/home/agent/tompathy-open/week-20261122")
ROOT = WEEK.parent / "rapid-20261127"
JOIN = "325e50a56fd4d84da7d58321c39a88567e5907770bdaaa1b7ba064442710eff2"
Q20 = "d7520ece843c5805b26be7b746c452eedc09b71940b263ed241251bed33bcaef"
REG = "22e90646c03230dd8c00fe1cb98ff38149adc445467fd11c8050916ca8fcfbb9"
COUNTS = [490, 107, 237, 145, 1188, 50, 22, 35]
WORDS = ["sad", "angry", "afraid", "proud", "happy", "lonely", "anxious", "ashamed"]
OTHER = [
    "sadness",
    "anger",
    "scared",
    "pride",
    "happiness",
    "loneliness",
    "anxiety",
    "shame",
]
FORMS = {word: i for forms in (WORDS, OTHER) for i, word in enumerate(forms)}
PATTERN = re.compile(r"\b(?:" + "|".join(FORMS) + r")\b")


def read(path):
    return json.loads(path.read_bytes())


def pin(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bound(path, expected):
    if pin(path) != expected:
        raise ValueError("Changed source: " + path.name)
    return path


def check(out):
    paths = (
        out,
        ROOT,
        WEEK,
        WEEK.parent / "word-table-20261120",
        WEEK.parent / "person-teacher-20261121",
    )
    while True:
        if time.time() >= 1795968000 or any((p / "STOP").exists() for p in paths):
            raise RuntimeError("Owner STOP or registered cutoff")
        large = ROOT / "jobs/Q32"
        if not (large / "owner.json").exists() or (large / "released.json").exists():
            break
        time.sleep(30)
    mem = Path("/proc/meminfo").read_text()
    if int(re.search(r"^MemAvailable:\s+(\d+)", mem, re.MULTILINE)[1]) < 8 * 1024**2:
        raise RuntimeError("Available host RAM below eight GiB")


def dump(path, record):
    with path.open("x", encoding="utf8") as stream:
        json.dump(record, stream, allow_nan=False, indent=2)
        stream.write("\n")


def save(directory, name, **values):
    path = directory / name
    with path.open("xb") as stream:
        np.savez_compressed(stream, **values)
    if path.stat().st_size >= 1_000_000_000:
        raise ValueError("Vector archive exceeds transfer cap")
    return pin(path)


def masks(text):
    return sum(1 << i for i in {FORMS[w] for w in PATTERN.findall(text.casefold())})


def run():
    import fcntl

    os.setpriority(os.PRIO_PROCESS, 0, 15)
    limits = (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "MKL_NUM_THREADS",
    )
    if any(os.environ.get(name) != "1" for name in limits):
        raise ValueError("Launch with one numerical thread before NumPy loads")
    os.sched_setaffinity(0, {max(os.sched_getaffinity(0))})
    probe = np.eye(32) @ np.ones((32, 1))
    if not np.all(probe == 1) or len(list(Path("/proc/self/task").iterdir())) != 1:
        raise RuntimeError("The numerical process did not start with one thread")
    prior_log = ROOT / "TP61-vectors-a.log"
    if (
        ROOT / "TP61-vectors-a"
    ).exists() or "No module named 'threadpoolctl'" not in prior_log.read_text():
        raise ValueError(
            "The retry requires the preserved pre-computation import failure"
        )
    out = ROOT / "TP61-vectors-b"
    with (ROOT / "TP61-vector-cpu.lock").open("ab") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check(out)
        if shutil.disk_usage(ROOT).free < 4_000_000_000:
            raise RuntimeError("Insufficient storage for scratch and the return")
        out.mkdir(exist_ok=False)
        start = time.time()
        owner = {
            "pid": os.getpid(),
            "bootId": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "startTicks": Path("/proc/self/stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()[19],
            "job": "TP61-vectors",
            "codePin": pin(Path(__file__)),
            "initialFailurePin": pin(prior_log),
            "threadsObserved": 1,
        }
        dump(out / "owner.json", owner)
        try:
            result = build(out)
            check(out)
            result.update(
                owner=owner,
                codePin=pin(Path(__file__)),
                seconds=time.time() - start,
                q20SourceReceiptPin=Q20,
                rosterPin=JOIN,
            )
            dump(out / "receipt.json", result)
            dump(out / "complete.json", {"sourceReceiptPin": pin(out / "receipt.json")})
        except Exception as exc:
            dump(out / "failed.json", {"error": str(exc), "at": time.time()})
            raise


def build(out):
    archive = out / "export"
    archive.mkdir()
    cfg = read(bound(WEEK / "registration.json", REG))
    manifest = read(bound(WEEK / "Q20-inputs.json", cfg["manifests"]["Q20"]))
    source = WEEK / "jobs/Q20"
    receipt = read(bound(source / "receipt.json", Q20))
    roster = bound(ROOT / "inputs/TP61-author-order.jsonl.gz", JOIN)
    with gzip.open(roster, "rt", encoding="utf8") as stream:
        authors = [json.loads(line) for line in stream]
    if len(authors) != 5428 or len({a for a, _ in authors}) != len(authors):
        raise ValueError("Author cohort differs")
    keys = sorted({key for _, sides in authors for side in sides for key, _, _ in side})
    lookup = {key: i for i, key in enumerate(keys)}
    count = len(keys)
    tag_masks = np.full(count, -1, dtype=np.int16)
    for name, expected in sorted(manifest["files"].items()):
        check(out)
        with gzip.open(
            bound(WEEK / "Q20-inputs" / name, expected), "rt", encoding="utf8"
        ) as stream:
            for line in stream:
                key, text = json.loads(line)
                dest = lookup.get(key)
                if dest is not None:
                    if (
                        tag_masks[dest] != -1
                        or hashlib.sha256(text.encode()).hexdigest() != key
                    ):
                        raise ValueError("Ambiguous Q20 opening")
                    tag_masks[dest] = masks(text)
    if (tag_masks < 0).any():
        raise ValueError("TP47 opening missing from Q20")

    # Keep this working matrix on Spark. Only TP47's selected individual rows leave.
    x = np.lib.format.open_memmap(
        out / "openings.npy", mode="w+", dtype="float32", shape=(count, 384)
    )
    seen = np.zeros(count, dtype=bool)
    names = sorted(receipt["vectors"])
    for start in range(0, len(names), 20):
        check(out)
        for name in names[start : start + 20]:
            scores = "scores-" + name
            with np.load(
                bound(source / scores, receipt["outputs"][scores]), allow_pickle=False
            ) as batch:
                ids = batch["ids"].tolist()
            positions = [
                (row, lookup[key]) for row, key in enumerate(ids) if key in lookup
            ]
            if not positions:
                continue
            src, dest = map(np.asarray, zip(*positions, strict=True))
            with np.load(
                bound(source / "vectors" / name, receipt["vectors"][name]),
                allow_pickle=False,
            ) as data:
                values = data["x"]
                if (
                    values.shape != (len(ids), 384)
                    or values.dtype != np.float32
                    or not np.isfinite(values[src]).all()
                ):
                    raise ValueError("Frozen Q20 vector dimensions or values differ")
                if seen[dest].any() or len(set(dest.tolist())) != len(dest):
                    raise ValueError("Duplicate Q20 vector")
                x[dest] = values[src]
                seen[dest] = True
        if start % 500 == 0:
            progress = out / "progress.tmp"
            progress.write_text(
                json.dumps(
                    {
                        "vectorBatches": start + min(20, len(names) - start),
                        "total": len(names),
                    }
                )
            )
            progress.replace(out / "progress.json")
    if not seen.all():
        raise ValueError("Incomplete Q20 openings")
    x.flush()
    np.save(out / "opening-ids.npy", np.asarray(keys, dtype="S64"), allow_pickle=False)
    required = np.zeros(count, bool)
    owner_names = []
    word_counts = np.zeros(8, int)
    slots = ["all", "date0", "date1", "worry0", "worry1"] + [
        f"k{k}-{h}" for k in (5, 10, 20, 40) for h in (0, 1)
    ]
    means = {name: np.zeros((len(authors), 384), dtype=np.float64) for name in slots}
    ns = {name: np.zeros(len(authors), dtype=np.int32) for name in slots}
    for i, (author, sides) in enumerate(authors):
        if i % 50 == 0:
            check(out)
        owner_names.append(author)
        ix = [
            np.asarray([lookup[key] for key, _, _ in side], dtype=int) for side in sides
        ]

        def take(slot, indexes, row=i):
            if len(indexes):
                means[slot][row] = x[indexes].mean(0, dtype=np.float64)
                ns[slot][row] = len(indexes)

        take("all", np.concatenate(ix))
        for h in (0, 1):
            take(f"date{h}", ix[h])
        for k in (5, 10, 20, 40):
            if min(len(ix[0]), len(ix[1])) >= k:
                for h in (0, 1):
                    take(f"k{k}-{h}", ix[h][:k])
        if sum(rate is not None for side in sides for _, rate, _ in side) >= 10:
            for h in (0, 1):
                take(
                    f"worry{h}",
                    [
                        lookup[key]
                        for side in sides
                        for key, rate, half in side
                        if rate is not None and half == h
                    ],
                )
        for j in range(8):
            selections = [
                idx[cond]
                for idx in ix[:2]
                for cond in ((tag_masks[idx] & (1 << j)) != 0, tag_masks[idx] == 0)
            ]
            if min(map(len, selections)) >= 2:
                word_counts[j] += 1
                for idx in selections:
                    required[idx] = True
    if (
        word_counts.tolist() != COUNTS
        or int(((ns["date0"] > 0) & (ns["date1"] > 0)).sum()) != 5409
    ):
        raise ValueError("TP46 or TP47 eligible cohort differs")
    files = {
        "author-index.npz": save(
            archive,
            "author-index.npz",
            authors=np.asarray(owner_names, dtype="S64"),
            **ns,
        )
    }
    for slot in slots:
        check(out)
        name = "mean-" + slot + ".npz"
        files[name] = save(archive, name, x=means[slot])
    selected = np.flatnonzero(required)
    for start in range(0, len(selected), 25000):
        check(out)
        dest = selected[start : start + 25000]
        name = f"tp47-{start:06d}.npz"
        files[name] = save(
            archive,
            name,
            ids=np.asarray([keys[j] for j in dest], dtype="S64"),
            masks=tag_masks[dest],
            x=x[dest],
        )
    return {
        "authors": len(authors),
        "uniqueOpenings": count,
        "tp47Openings": len(selected),
        "tp47AuthorsByWord": dict(zip(WORDS, COUNTS, strict=True)),
        "authorsWithMean": {key: int((v > 0).sum()) for key, v in ns.items()},
        "localScratch": {
            "vectors": pin(out / "openings.npy"),
            "ids": pin(out / "opening-ids.npy"),
        },
        "files": files,
    }


if __name__ == "__main__":
    run()
