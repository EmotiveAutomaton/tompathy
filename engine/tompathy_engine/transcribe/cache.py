"""Local literal-label cache; no text is sent on a cache hit."""

import json
import sqlite3
from pathlib import Path

from ..ledger.ids import canonical, digest


class Cache:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS answers (key TEXT PRIMARY KEY, value TEXT NOT NULL, hash TEXT NOT NULL)"
            )

    def get(self, key):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT value, hash FROM answers WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        value = json.loads(row[0])
        if digest(value) != row[1]:
            raise ValueError("Transcriber cache integrity failure")
        return value

    def put(self, key, value):
        with sqlite3.connect(self.path) as db:
            prior = db.execute("SELECT hash FROM answers WHERE key=?", (key,)).fetchone()
            if prior and prior[0] != digest(value):
                raise ValueError("Conflicting deterministic transcriber result")
            db.execute(
                "INSERT OR IGNORE INTO answers VALUES (?, ?, ?)",
                (key, canonical(value).decode(), digest(value)),
            )
