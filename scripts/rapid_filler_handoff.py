"""After G15's counted input verification, arm W behind the exact G13 blog release."""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import time

from rapid_cpu_dispatch import ROOT, check, confirmed
from word_table_lane import identity, lease, now, pin, read, write

PRIOR = "6aa593aedf27e353db6751c652a166e0a76955e89185708866f45e0e51e31096"
MODULES = (
    "rapid_gpu",
    "rapid_marks",
    "rapid_worry",
    "week_spark",
    "word_table_lane",
    "spark-reader-job",
    "rapid_sentences",
    "rapid_filler_gpu",
    "rapid_after_gpu",
    "rapid_windows_follow",
)


def prepare(revision, intake):
    if (
        not re.fullmatch("[0-9a-f]{40}", revision)
        or subprocess.check_output(["git", "rev-parse", revision], text=True).strip()
        != revision
    ):
        raise ValueError("An exact committed G15 revision is required")
    parent = ROOT / "Q31-registration.json"
    if (
        pin(parent) != PRIOR
        or read(ROOT / "workstation-blog-follow/armed.json")["registration"] != PRIOR
    ):
        raise ValueError("Unknown preceding G13 blog worker")
    selection = read(intake / "selection.json")
    source = confirmed(intake)
    if (
        selection != read(intake / "receipt.json")["result"]
        or pin(intake / "openings.jsonl.gz") != selection["rosterPin"]
    ):
        raise ValueError("G15 ordered input differs from its verified source")
    cfg = ROOT / "G15-registration.json"
    dest = ROOT / "code" / revision
    files = {n + ".py": "scripts/" + n + ".py" for n in MODULES}
    files["tp31_teacher.py"] = "engine/tompathy_engine/eval/readers/tp31_teacher.py"
    dest.mkdir(exist_ok=True)
    pins = {}
    for name, file in files.items():
        data = subprocess.check_output(["git", "show", revision + ":" + file])
        path = dest / name
        if not path.is_file():
            with path.open("xb") as f:
                f.write(data)
        pins[name] = hashlib.sha256(data).hexdigest()
        if pin(path) != pins[name]:
            raise ValueError("Existing code snapshot differs")
    plan = {
        "commit": revision,
        "code": pins,
        "parentRegistration": PRIOR,
        "inputStage": intake.name,
        "inputReceiptPin": source,
        "selectionPin": pin(intake / "selection.json"),
        "inputManifest": read(parent)["inputManifest"],
        "packet": read(parent)["packet"],
        "modelSettings": selection["sameReaderSettings"],
        "absoluteCutoffUTC": "2026-11-29T16:00:00+00:00",
    }
    if cfg.exists():
        if read(cfg) != plan:
            raise ValueError("Existing G15 registration differs")
    else:
        write(cfg, plan)
    return dest, pin(cfg)


def run(revision):
    if os.name != "nt":
        raise RuntimeError("This setup belongs to the registered workstation")
    ctl = ROOT / "filler-setup"
    ctl.mkdir(exist_ok=True)
    gate = ROOT / "filler-counted-wait"
    with lease(ctl / "setup.lock"):
        if (ctl / "armed.json").exists():
            raise ValueError("A filler setup was already armed")
        write(
            ctl / "armed.json",
            {"owner": identity(), "revision": revision, "at": now(), "prior": PRIOR},
        )
        try:
            while not (gate / "complete.json").is_file():
                check()
                if (gate / "stopped.json").is_file() or (ctl / "STOP").exists():
                    raise RuntimeError(
                        "Counted input did not complete or owner stopped setup"
                    )
                time.sleep(30)
            intake = ROOT / "G15-inputs-b"
            if read(gate / "complete.json")["sourceReceiptPin"] != confirmed(intake):
                raise ValueError("Input worker returned a different receipt")
            dest, registration = prepare(revision, intake)
            args = [
                sys.executable,
                "-B",
                str(dest / "rapid_after_gpu.py"),
                str(ROOT.resolve()),
                "--filler-registration",
                registration,
            ]
            write(
                ctl / "verified.json",
                {
                    "registration": registration,
                    "at": now(),
                    "qualification": "ordered intake and frozen code",
                },
            )
            subprocess.run(args, check=True)
            write(
                ctl / "complete.json",
                read(ROOT / "workstation-filler-follow/complete.json"),
            )
        except Exception as exc:
            write(ctl / "stopped.json", {"at": now(), "reason": str(exc)})
            raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("revision")
    run(p.parse_args().revision)
