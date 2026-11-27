"""Return only the authorized TP61 author means and TP47 opening vectors from Spark."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

REMOTE = Path("/home/agent/tompathy-open/rapid-20261127")
REG_CODE = "ab411921e41b6f8deff8d4ebe50ef07e5041af9dc02fee8198dbe14f8225ca36"
Q20 = "d7520ece843c5805b26be7b746c452eedc09b71940b263ed241251bed33bcaef"
JOIN = "325e50a56fd4d84da7d58321c39a88567e5907770bdaaa1b7ba064442710eff2"


def pin(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def names(receipt):
    files = receipt["files"]
    if (
        receipt["q20SourceReceiptPin"] != Q20
        or receipt["rosterPin"] != JOIN
        or receipt["codePin"] != REG_CODE
        or receipt["authors"] != 5428
        or any(
            not re.fullmatch(
                r"(author-index|mean-(all|date[01]|worry[01]|k(5|10|20|40)-[01])|tp47-[0-9]{6})\.npz",
                name,
            )
            or not re.fullmatch("[0-9a-f]{64}", h)
            for name, h in files.items()
        )
    ):
        raise ValueError("Unexpected TP61 source or export file")
    return files


def remote():
    import fcntl

    directory = REMOTE / "TP61-vectors-b"
    receipt = read(directory / "receipt.json")
    owner = read(directory / "owner.json")
    if (
        owner != receipt["owner"]
        or owner["job"] != "TP61-vectors"
        or owner["codePin"] != REG_CODE
        or owner["bootId"]
        != Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    ):
        raise ValueError("Original preparation owner differs")
    p = Path("/proc") / str(owner["pid"]) / "stat"
    if (
        p.exists()
        and p.read_text().rsplit(")", 1)[1].split()[19] == owner["startTicks"]
    ):
        raise ValueError("Wait for the exact native preparation worker to exit")
    with (REMOTE / "TP61-vector-cpu.lock").open("rb") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source = pin(directory / "receipt.json")
        if (
            read(directory / "complete.json") != {"sourceReceiptPin": source}
            or (directory / "failed.json").exists()
        ):
            raise ValueError("Terminal proof differs")
        files = names(receipt)
        if set(files) != {p.name for p in (directory / "export").iterdir()}:
            raise ValueError("Unexpected export inventory")
        sizes = {}
        for n, h in files.items():
            path = directory / "export" / n
            if (
                path.is_symlink()
                or not 0 < path.stat().st_size < 1_000_000_000
                or pin(path) != h
            ):
                raise ValueError("Remote TP61 export differs")
            sizes[n] = path.stat().st_size
        print(
            json.dumps(
                {
                    "receiptPin": source,
                    "owner": owner,
                    "nativeExited": True,
                    "cpuLeaseReacquired": True,
                    "bytes": sizes,
                }
            )
        )


def receive(commit):
    if not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("Committed collector required")
    root = Path(".local/rapid-20261127")
    remote_dir = REMOTE.as_posix() + "/TP61-vectors-b"
    proof = json.loads(
        subprocess.check_output(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "spark",
                "/home/agent/venvs/engine/bin/python",
                f"{REMOTE.as_posix()}/tools/{commit}/rapid_vector_return.py",
                "verify",
            ],
            text=True,
        )
    )
    source = proof["receiptPin"]
    if not re.fullmatch("[0-9a-f]{64}", source):
        raise ValueError("Invalid receipt digest")
    out = root / ("verified-TP61-vectors-" + source[:12])
    out.mkdir(exist_ok=True)

    def fetch(name, h):
        path = out / Path(name).name
        if not path.exists():
            part = out / (path.name + ".partial")
            subprocess.run(
                [
                    "scp",
                    "-q",
                    "-o",
                    "BatchMode=yes",
                    "spark:" + remote_dir + "/" + name,
                    str(part),
                ],
                check=True,
            )
            if pin(part) != h:
                raise ValueError("Hash mismatch after transfer")
            part.rename(path)
        elif pin(path) != h:
            raise ValueError("Existing private file differs")
        return path

    receipt = read(fetch("receipt.json", source))
    files = names(receipt)
    if set(proof["bytes"]) != set(files) or receipt["owner"] != proof["owner"]:
        raise ValueError("Transfer and source owner differ")
    for name, h in files.items():
        if fetch("export/" + name, h).stat().st_size != proof["bytes"][name]:
            raise ValueError("Local size differs")
    audit = root / "TP61-vector-transfer.json"
    result = {
        **proof,
        "mirror": str(out.resolve()),
        "fileCount": len(files),
        "collectorPin": pin(Path(__file__)),
    }
    if audit.exists():
        if read(audit) != result:
            raise ValueError("The existing verified transfer differs")
    else:
        with audit.open("x", encoding="utf8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
    print(
        json.dumps(
            {
                "sourceReceiptPin": source,
                "files": len(files),
                "bytes": sum(proof["bytes"].values()),
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["verify", "receive"])
    p.add_argument("--commit")
    a = p.parse_args()
    if a.action == "verify":
        remote()
    else:
        receive(a.commit)
