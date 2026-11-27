"""Build a fresh sealed producer payload from the authenticated TP58 files and TP72 code."""

import ast
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ORIGINAL = REPO / ".local/week-20261122/TP58-candidate-b"
SOURCE = "f2a7a8eb109f9691394305b2409ceede434d0761bc97e328c41d04c677868752"
MODULES = (
    "panels.py",
    "history.py",
    "curves.py",
    "traits.py",
    "conversation.py",
    "run72.py",
    "rehearse72.py",
    "README.md",
)


def pin(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verified(payload, expected):
    if payload.is_symlink() or payload.is_junction():
        raise ValueError("Linked payload root")
    actual = {}
    for p in payload.rglob("*"):
        if p.is_symlink() or p.is_junction():
            raise ValueError("Linked payload member")
        if p.is_file():
            actual[p.relative_to(payload).as_posix()] = pin(p)
    if actual != expected:
        raise ValueError("Payload paths or bytes differ from manifest")


def extract(p, names):
    text = p.read_text(encoding="utf8")
    matches = {
        n.name: n
        for n in ast.parse(text).body
        if isinstance(n, ast.FunctionDef) and n.name in names
    }
    if set(matches) != set(names):
        raise ValueError("Original helper definition differs")
    return "\n\n".join(ast.get_source_segment(text, matches[name]) for name in names)


def build(dest):
    sys.dont_write_bytecode = True
    if pin(ORIGINAL / "manifest.json") != SOURCE:
        raise ValueError("Original TP58 manifest differs")
    original = ORIGINAL / "payload"
    expected = json.loads((ORIGINAL / "manifest.json").read_bytes())
    verified(original, expected)
    dest.mkdir(exist_ok=False)
    payload = dest / "payload"
    payload.mkdir()
    for name in expected:
        if name in ("run.py", "tables.py", "README.md"):
            continue
        target = payload / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original / name, target)
    for name in MODULES:
        shutil.copyfile(HERE / name, payload / name)
    shutil.copyfile(HERE.parent / "rapid_nulls.py", payload / "rapid_nulls.py")
    forms = next(
        line
        for line in (original / "tables.py").read_text().splitlines()
        if line.startswith("FORMS = ")
    )
    helpers = (
        "import csv\nimport re\nfrom collections import Counter\n\n"
        + forms
        + "\n\n"
        + extract(original / "tables.py", ["style"])
        + "\n\n"
        + extract(original / "run.py", ["rows", "community"])
        + "\n"
    )
    (payload / "legacy_helpers.py").write_text(helpers, encoding="utf8")
    expected = {
        p.relative_to(payload).as_posix(): pin(p)
        for p in sorted(payload.rglob("*"))
        if p.is_file()
    }
    (dest / "manifest.json").write_text(
        json.dumps(expected, indent=2) + "\n", encoding="utf8"
    )
    verified(payload, expected)
    return pin(dest / "manifest.json")


if __name__ == "__main__":
    print(build(Path(sys.argv[1])))
