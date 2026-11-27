"""Freeze the additional Q29/G13 snapshot without changing any active registration."""

import argparse
import subprocess
from pathlib import Path

from rapid_marks import protocol
from rapid_register import CODE
from word_table_lane import pin, read, write


def register(root, commit, blog=False):
    if (
        subprocess.check_output(["git", "rev-parse", commit], text=True).strip()
        != commit
    ):
        raise ValueError("Full committed revision required")
    dest = root / "code" / commit
    config = root / ("Q31-registration.json" if blog else "Q29-registration.json")
    if dest.exists() or config.exists():
        raise FileExistsError("Preserve the existing execution snapshot and binding")
    dest.mkdir()
    files = {
        name: "scripts/" + name
        for name in (*CODE, "rapid_sentences.py", "rapid_sentence_gpu.py")
    }
    files["tp31_teacher.py"] = "engine/tompathy_engine/eval/readers/tp31_teacher.py"
    if blog:
        files["rapid_blog_gpu.py"] = "scripts/rapid_blog_gpu.py"
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

    kinds = ["sentence", "loss"] if blog else ["sentence"]
    frozen = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "import json,rapid_marks,sys; print(json.dumps({k:rapid_marks.protocol(k) for k in sys.argv[1:]}))",
            *kinds,
        ],
        cwd=dest,
        text=True,
        encoding="utf8",
    )
    spec = json.loads(frozen)
    if spec != {k: protocol(k) for k in kinds}:
        raise ValueError("Local and committed sentence prompt differ")
    if blog:
        from rapid_cpu_dispatch import confirmed

        folder = root / "Q31-inputs-a"
        receipt = confirmed(folder)
        source = read(folder / "receipt.json")["result"]
        if source["card"] != "Q31-inputs" or source["selectionPin"] != pin(
            folder / "selection.json"
        ):
            raise ValueError("The selected Q31 inputs differ")
        with (root / "Q31-selection.json").open("xb") as f:
            f.write((folder / "selection.json").read_bytes())
        extra = {
            "selectionReceiptPin": receipt,
            "selectionPin": source["selectionPin"],
            "roster": source["roster"],
            "prompts": spec,
            "jobs": ["Q31", "G13-Q31"],
        }
    else:
        extra = {
            "sentences": read(root / "Q29-inputs/manifest.json"),
            "prompt": spec["sentence"],
            "jobs": ["Q29", "G13-Q29"],
        }
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
            **extra,
            "readers": {role: old["readers"][role] for role in ("B", "W")},
            "options": old["options"],
        },
    )
    return pin(config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("commit")
    parser.add_argument("--blog", action="store_true")
    args = parser.parse_args()
    print(register(Path(".local/rapid-20261127"), args.commit, args.blog))
