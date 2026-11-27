"""Freeze exact committed job code and input and prompt bindings before launch."""

import argparse
import subprocess
from pathlib import Path

import rapid_marks as marks
from word_table_lane import B, W, pin, write

CODE = (
    "rapid_gpu.py",
    "rapid_marks.py",
    "rapid_worry.py",
    "week_spark.py",
    "word_table_lane.py",
    "spark-reader-job.py",
)


def register(root, commit):
    if (
        subprocess.check_output(["git", "rev-parse", commit], text=True).strip()
        != commit
    ):
        raise ValueError("Full commit required")
    dest = root / "code" / commit
    dest.mkdir(parents=True, exist_ok=False)
    for name in CODE:
        data = subprocess.check_output(["git", "show", f"{commit}:scripts/{name}"])
        (dest / name).write_bytes(data)
    record = {
        "commit": commit,
        "code": {n: pin(dest / n) for n in CODE},
        "inputManifest": pin(root / "inputs/inputs.json"),
        "weekRegistration": pin(Path(".local/week-20261122/registration.json")),
        "packet": pin(Path("TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-27.md")),
        "prompts": {
            k: marks.protocol(k)
            for k in ("standing", "standing2", "standing3", "features")
        },
        "readers": {
            "W": W,
            "B": B,
            "C": [
                "qwen3.5:122b",
                "8b9d11d807c57feb1e2ecb0d6cbf40334c37dcc3523bed5540af4f927f112a37",
            ],
        },
        "options": {
            "temperature": 0,
            "seed": 23,
            "think": False,
            "num_ctx": 4096,
            "num_predict": 256,
        },
        "first100": "Wall time after loading. Q26 measures and compares each arm, in the fixed order 1, 2, 4.",
    }
    if (root / "registration.json").exists():
        raise FileExistsError("Registration already sealed")
    write(root / "registration.json", record)
    print(pin(root / "registration.json"))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("commit")
    a = p.parse_args()
    register(a.root, a.commit)
