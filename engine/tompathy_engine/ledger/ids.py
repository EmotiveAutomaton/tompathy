"""Canonical IDs are independent of dictionary insertion order and local paths."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8", errors="backslashreplace")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


def maker_id(source: str, identity: str) -> str:
    if not source or not identity or ":" in source:
        raise ValueError("A source namespace and nonempty source identity are required")
    return f"{source}:{text_hash(identity)}"
