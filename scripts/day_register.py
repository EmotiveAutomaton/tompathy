"""Freeze a machine-specific job registration from committed source bytes."""

import json
import subprocess
import sys
from pathlib import Path

import rapid_marks
import word_table_lane as lane

ROOT = Path(".local/day-20261128")
OLD = Path(".local/rapid-20261127")
PROTOCOL = Path("docs/exchange/result-sheets/R38-need-protocol.json")
PACKET = Path("TOMPATHY_0.3_ENGINE_ONE_DAY_PACKET_2026-11-28.md")


def protocol():
    return {kind: rapid_marks.protocol(kind) for kind in ("need", "need2", "need3")}


def freeze(machine):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    folder = ROOT / "code" / commit
    folder.mkdir(parents=True, exist_ok=True)
    names = [
        "day_gpu",
        "day_need",
        "rapid_gpu",
        "rapid_marks",
        "word_table_lane",
        "spark-reader-job",
    ]
    if machine == "workstation":
        names.extend(
            ["day_resume", "rapid_windows_follow", "rapid_sentences", "rapid_blog_gpu"]
        )
    sources = {n + ".py": "scripts/" + n + ".py" for n in names}
    if machine == "workstation":
        sources["tp31_teacher.py"] = (
            "engine/tompathy_engine/eval/readers/tp31_teacher.py"
        )
    pins = {}
    for name, path in sources.items():
        data = subprocess.check_output(["git", "show", commit + ":" + path])
        dest = folder / name
        if dest.exists() and dest.read_bytes() != data:
            raise ValueError("Existing snapshot differs")
        if not dest.exists():
            dest.write_bytes(data)
        pins[name] = lane.pin(dest)
    if lane.read(PROTOCOL) != protocol():
        raise ValueError("Filed protocol differs")
    cfg = {
        "commit": commit,
        "code": pins,
        "packetPin": lane.pin(PACKET),
        "prompts": protocol(),
        "inputs": lane.pin(OLD / "inputs/inputs.json"),
        "cutoffUnix": 1795968000,
        "sampling": "SHA-256 ascending Q36:23: plus ID, within corpus; Q36:reword:23: plus ID over the sample",
        "machine": machine,
    }
    if machine == "workstation":
        cfg["originals"] = {}
        for job in ("G12", "G14", "G13-Q29", "G13-Q31"):
            out = OLD / "jobs" / job
            owner = lane.read(out / "owner.json")
            cfg["originals"][job] = {
                k: lane.pin(out / k)
                for k in ("owner.json", "released.json", "failed.json")
            }
            cfg["originals"][job]["registration"] = owner["registration"]
            cfg["originals"][job]["protocol"] = lane.pin(
                out / ("sentence" if job == "G13-Q31" else "W") / "protocol.json"
            )
    dest = ROOT / (machine + ".json")
    if dest.exists() and lane.read(dest) != cfg:
        raise ValueError("Registration path already belongs to a different snapshot")
    if not dest.exists():
        lane.write(dest, cfg)
    print(commit, lane.pin(dest))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "protocol":
        data = json.dumps(protocol(), ensure_ascii=False, indent=2) + "\n"
        if PROTOCOL.exists() and PROTOCOL.read_text(encoding="utf8") != data:
            raise ValueError("Existing protocol differs")
        PROTOCOL.write_text(data, encoding="utf8", newline="\n")
    elif mode in {"spark", "workstation"}:
        freeze(mode)
    else:
        sys.exit("Expected protocol, spark or workstation")
