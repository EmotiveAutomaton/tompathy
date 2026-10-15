"""Read a local clone of a public file history, with explicit license evidence."""

import re
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from ..ledger.ids import text_hash
from .history import ingest_history


def read_repository(
    repository,
    file,
    *,
    source_uri,
    artifact_id,
    license,
    license_file,
    license_sha256,
    limit=100,
    ref="HEAD",
):
    root = Path(repository).resolve()
    path = PurePosixPath(file)
    if path.is_absolute() or ".." in path.parts or file.startswith("-") or not 1 <= limit <= 1000:
        raise ValueError("Invalid repository file or history bound")
    uri = urlsplit(source_uri)
    if uri.scheme != "https" or uri.username or not uri.hostname:
        raise ValueError("Git source must identify its public HTTPS artifact")
    license_path = (root / license_file).resolve()
    if (
        not license_path.is_relative_to(root)
        or text_hash(license_path.read_text(encoding="utf8")) != license_sha256
    ):
        raise ValueError("License evidence file does not match its supplied pin")

    def git(*args):
        return subprocess.run(
            ["git", "-c", "core.quotepath=false", "-C", str(root), *args],
            check=True,
            capture_output=True,
            timeout=60,
        ).stdout

    tip = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", tip):
        raise ValueError("Invalid resolved commit")
    commits = (
        git("log", "--first-parent", f"--max-count={limit}", "--format=%H", tip, "--", file)
        .decode()
        .splitlines()[::-1]
    )
    snapshots = []
    for commit in commits:
        # Use the file's preceding witnessed snapshot, not unrelated tree parents.
        metadata = (
            git("show", "-s", "--format=%ae%x00%an%x00%cI%x00%B", commit)
            .decode("utf8")
            .split("\0", 3)
        )
        text = git("show", f"{commit}:{file}").decode("utf8")
        if "\0" in text:
            raise ValueError("Binary files are not writing histories")
        email, label, time, message = metadata
        snapshots.append(
            {
                "id": commit,
                "parents": [snapshots[-1]["id"]] if snapshots else [],
                "maker": email,
                "label": label,
                "t": time,
                "summary": message.strip(),
                "text": text,
            }
        )
    return {
        "artifact_id": artifact_id,
        "source_uri": source_uri,
        "license": license,
        "license_evidence": f"{license_file} sha256:{license_sha256}",
        "revisions": snapshots,
    }


def ingest(payload, ledger):
    if "repository" in payload:
        payload = read_repository(**payload)
    return ingest_history(payload, ledger, adapter="git")
