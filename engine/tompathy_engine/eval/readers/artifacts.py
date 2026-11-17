"""Immutable completed-card artifact inventories, separate from public row data."""
import json
from pathlib import Path

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .checkpoint import completed


def model_identity(directory, check=lambda: None):
    root = Path(directory).resolve()
    identity = json.loads((root/'intake.json').read_text(encoding='utf8'))
    for name, pin in identity['files'].items():
        check()
        path = (root/name).resolve()
        if not path.is_relative_to(root) or sha256(path) != pin:
            raise ValueError('Original encoder files changed')
    return identity


def seal(root, paths, check=lambda: None):
    root = Path(root).resolve()
    files = {}
    for item in paths:
        item = Path(item).resolve()
        selected = sorted(p for p in item.rglob('*') if p.is_file()) if item.is_dir() else [item]
        for path in selected:
            check()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError('Artifact must be a saved file within the job')
            files[path.relative_to(root).as_posix()] = sha256(path)
    if not files:
        raise ValueError('No completed artifacts')
    save_json(root/'artifact-manifest.json', {'files': files})
    return sha256(root/'artifact-manifest.json')


def verified(root, card, check=lambda: None):
    root = Path(root).resolve()
    receipt = completed(root, card)
    if sha256(root/'artifact-manifest.json') != receipt['artifactsPin']:
        raise ValueError('Artifact inventory differs from completed receipt')
    files = json.loads((root/'artifact-manifest.json').read_text(encoding='utf8'))['files']
    for name, pin in files.items():
        check()
        path = (root/name).resolve()
        if not path.is_relative_to(root) or sha256(path) != pin:
            raise ValueError('Completed artifact bytes changed')
    return receipt, files
