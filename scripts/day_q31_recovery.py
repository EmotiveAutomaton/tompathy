"""Certify and package the original Q31 floor-independent summary failure without inference."""

import argparse
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

REG = "6aa593aedf27e353db6751c652a166e0a76955e89185708866f45e0e51e31096"
OWNER = "e7bef0d9b04566a3b793ea82addf7b495107df00affc5a6e03280f0bec5b14ed"
OLD = Path("/home/agent/tompathy-open/rapid-20261127")
DAY = OLD.parent / "day-20261128"
CAP = 1_000_000_000


def pin(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(p):
    return json.loads(p.read_bytes())


def check():
    if time.time() >= 1795968000 or any(
        (p / "STOP").exists()
        for p in (DAY, OLD, OLD / "jobs/Q31", OLD.parent / "week-20261122")
    ):
        raise RuntimeError("Cutoff or owner stop")


def remote():
    import fcntl

    import numpy as np

    check()
    root = OLD / "jobs/Q31"
    owner = read(root / "owner.json")
    cfg = read(OLD / "Q31-registration.json")
    release = read(root / "released.json")
    failed = read(root / "failed.json")
    proc = Path("/proc") / str(owner["pid"]) / "stat"
    if (
        pin(root / "owner.json") != OWNER
        or pin(OLD / "Q31-registration.json") != REG
        or owner["registration"] != REG
        or Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        != owner["bootId"]
        or (
            proc.exists()
            and proc.read_text().rsplit(")", 1)[1].split()[19]
            == str(owner["startTicks"])
        )
        or release["owner"] != owner
        or release["exitCode"] != 1
        or not release["childWaited"]
        or not release["sharedLeaseReacquired"]
        or failed["owner"] != owner
        or failed["error"] != "'projectedHours'"
        or (root / "complete.json").exists()
        or read(root / "intake.json") != cfg["roster"]
    ):
        raise ValueError("Original source, exact exit or registered failure differs")
    code = OLD / "code" / owner["commit"]
    for name, wanted in cfg["code"].items():
        if pin(code / name) != wanted:
            raise ValueError("Frozen original code changed")
    sys.path.insert(0, str(code))
    from rapid_marks import template
    from word_table_lane import B, write

    dest = DAY / "Q31-recovery"
    dest.mkdir(exist_ok=False)
    package = dest / "original.zip"
    with (OLD / "TP61-vector-cpu.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        hashes = {}
        ids = {}
        metrics = {}
        with zipfile.ZipFile(package, "x", zipfile.ZIP_DEFLATED, compresslevel=1) as z:

            def save(p):
                if p.is_symlink() or not p.resolve().is_relative_to(root):
                    raise ValueError("Unexpected source file")
                name = p.relative_to(root).as_posix()
                if name in hashes:
                    raise ValueError("Duplicate source file")
                data = p.read_bytes()
                hashes[name] = hashlib.sha256(data).hexdigest()
                z.writestr(name, data)
                return data

            for arm, roster in (("loss", "loss"), ("sentence", "sentences")):
                folder = root / arm
                summary = read(folder / "complete.json")
                proto = read(folder / "protocol.json")
                contract = cfg["prompts"][arm]
                if (
                    any(proto[k] != v for k, v in contract.items())
                    or proto["modelPin"] != B[1]
                    or proto["model"] != B[0]
                    or proto["think"] is not False
                    or proto["width"] != 1
                    or proto["options"]
                    != {
                        "seed": 23,
                        "num_ctx": 4096,
                        "num_thread": 3,
                        "num_predict": 256,
                        "temperature": 0,
                    }
                    or summary["protocolPin"] != pin(folder / "protocol.json")
                ):
                    raise ValueError("Original arm protocol differs")
                parse = template(arm)[2]
                keys = []
                valid = 0
                for i, p in enumerate(sorted(folder.glob("from-*.json"))):
                    if i % 500 == 0:
                        check()
                    if p.name != f"from-{i:06d}.json":
                        raise ValueError("Non-contiguous original responses")
                    [row] = json.loads(save(p))
                    try:
                        value = parse(json.loads(row["response"]))
                    except (ValueError, TypeError):
                        value = None
                    if value != row["values"]:
                        raise ValueError("Original response and parsed mark differ")
                    keys.append(row["id"])
                    valid += value is not None
                rosterpin = hashlib.sha256("\n".join(keys).encode()).hexdigest()
                if (
                    len(keys) != len(set(keys))
                    or len(keys) != cfg["roster"][roster]["n"]
                    or len(keys) != summary["rows"]
                    or valid != summary["valid"]
                    or rosterpin != cfg["roster"][roster]["orderedIdPin"]
                    or rosterpin != summary["inputPin"]
                    or rosterpin != proto["inputPin"]
                ):
                    raise ValueError("Ordered original reader roster differs")
                ids[arm] = keys
                metrics[arm] = {
                    "rows": len(keys),
                    "valid": valid,
                    "rosterPin": rosterpin,
                }
            keys = ids["sentence"]
            for start in range(0, len(keys), 100):
                check()
                data = save(root / "ten" / f"from-{start:06d}.npz")
                with np.load(io.BytesIO(data), allow_pickle=False) as chunk:
                    values = chunk["ten"]
                    selected = keys[start : start + 100]
                    if (
                        chunk["ids"].astype(str).tolist() != selected
                        or values.shape != (len(selected), 10)
                        or not np.isfinite(values).all()
                        or np.any((values < 0) | (values > 1))
                    ):
                        raise ValueError(
                            "Original frozen outputs or their roster differ"
                        )
            for p in sorted(root.rglob("*")):
                if p.is_file() and p.relative_to(root).as_posix() not in hashes:
                    if p.name.startswith("from-"):
                        raise ValueError("Unexpected additional original batch")
                    save(p)
        if package.stat().st_size > CAP:
            raise ValueError("Return exceeds cap")
        hours = (
            sum(
                read(root / k / "first100.json")["projectedHours"]
                for k in ("loss", "sentence")
            )
            + read(root / "ten/first100.json")["projectionHours"]
        )
        write(
            dest / "derived.json",
            {
                "status": "outputs-verified-after-summary-failure",
                "originalExit": 1,
                "owner": owner,
                "release": release,
                "failure": failed,
                "sourceRegistration": REG,
                "verified": metrics,
                "frozenRows": len(keys),
                "frozenColumns": 10,
                "reconstructedPilotHours": hours,
                "artifacts": hashes,
                "archiveSha256": pin(package),
                "bytes": package.stat().st_size,
                "newInference": False,
            },
        )


def local(dest):
    d = read(dest / "derived.json")
    src = dest / "original.zip"
    if (
        d["sourceRegistration"] != REG
        or d["originalExit"] != 1
        or d["newInference"]
        or d["artifacts"]["owner.json"] != OWNER
        or src.stat().st_size != d["bytes"]
        or d["bytes"] > CAP
        or pin(src) != d["archiveSha256"]
    ):
        raise ValueError("Transferred archive or original identity differs")
    with zipfile.ZipFile(src) as z:
        if sorted(z.namelist()) != sorted(d["artifacts"]):
            raise ValueError("Archive inventory differs")
        for p in z.namelist():
            if Path(p).is_absolute() or ".." in Path(p).parts or "\\" in p or ":" in p:
                raise ValueError("Unsafe member")
            if hashlib.sha256(z.read(p)).hexdigest() != d["artifacts"][p]:
                raise ValueError("Returned original file differs")
    dest.joinpath("local-verification.json").write_text(
        json.dumps(
            {
                "sourcePin": pin(dest / "derived.json"),
                "archivePin": pin(src),
                "verifiedFiles": len(d["artifacts"]),
                "verified": d["verified"],
                "frozenRows": d["frozenRows"],
                "originalExit": 1,
                "newInference": False,
            },
            sort_keys=True,
        )
        + "\n"
    )
    print("Verified", len(d["artifacts"]), "original files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("remote", "local"))
    parser.add_argument("directory", type=Path, nargs="?")
    args = parser.parse_args()
    if args.mode == "remote":
        for k in (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            os.environ[k] = "1"
        os.nice(10)
        remote()
    else:
        local(args.directory)
