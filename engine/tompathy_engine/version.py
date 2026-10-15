"""Best-effort source checkout identity; the implementation hash is authoritative."""

import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def source_revision():
    root = Path(__file__).resolve().parents[2]
    if not (root / ".git").exists():
        return "unavailable (installed package)"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        head = result.stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--", "engine/tompathy_engine"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        return head + (" + local engine changes" if dirty.stdout else "")
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
