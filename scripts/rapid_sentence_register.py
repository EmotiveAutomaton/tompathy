"""Freeze the additional Q29/G13 snapshot without changing any active registration."""

import argparse
import subprocess
from pathlib import Path

from rapid_marks import protocol
from rapid_register import CODE
from word_table_lane import pin, read, write


def register(root, commit):
    if (
        subprocess.check_output(["git", "rev-parse", commit], text=True).strip()
        != commit
    ):
        raise ValueError("Full committed revision required")
    dest = root / "code" / commit
    config = root / "Q29-registration.json"
    if dest.exists() or config.exists():
        raise FileExistsError("Preserve the existing execution snapshot and binding")
    dest.mkdir()
    files = {
        name: "scripts/" + name
        for name in (*CODE, "rapid_sentences.py", "rapid_sentence_gpu.py")
    }
    files["tp31_teacher.py"] = "engine/tompathy_engine/eval/readers/tp31_teacher.py"
    for name, repo_path in files.items():
        (dest / name).write_bytes(
            subprocess.check_output(["git", "show", f"{commit}:{repo_path}"])
        )
    ref = root / "registration.json"
    if pin(ref) != "2aaa9e0fc722a48e40e854b61dddc9b9c2a03828233e2c0fc3175afdcffa7f6a":
        raise ValueError("The two-day parent registration differs")
    old = read(ref)
    q21 = read(Path(".local/week-20261122/Q21-transfer.json"))
    if not (q21["nativeExited"] and q21["priorFlockReleased"]):
        raise ValueError("Q21 release is unverified")
    # Compute prompt pins with the module that will actually execute in the snapshot.
    import json
    import sys

    frozen = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "import json,rapid_marks; print(json.dumps(rapid_marks.protocol('sentence')))",
        ],
        cwd=dest,
        text=True,
        encoding="utf8",
    )
    spec = json.loads(frozen)
    if spec != protocol("sentence"):
        raise ValueError("Local and committed sentence prompt differ")
    write(
        config,
        {
            "commit": commit,
            "code": {n: pin(dest / n) for n in files},
            "parentRegistration": pin(ref),
            "packet": old["packet"],
            "weekRegistration": old["weekRegistration"],
            "inputManifest": old["inputManifest"],
            "q21ReceiptPin": q21["sourceReceiptPin"],
            "pridePin": q21["files"]["pride.npz"],
            "sentences": read(root / "Q29-inputs/manifest.json"),
            "prompt": spec,
            "readers": {role: old["readers"][role] for role in ("B", "W")},
            "options": old["options"],
            "jobs": ["Q29", "G13-Q29"],
        },
    )
    return pin(config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("commit")
    args = parser.parse_args()
    print(register(Path(".local/rapid-20261127"), args.commit))
