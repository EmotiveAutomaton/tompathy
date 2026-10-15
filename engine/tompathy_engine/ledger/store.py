"""Atomic append batches, Parquet tables and content-addressed zstd text.

A committed batch is an immutable directory. Renaming a completed pending batch
makes records and their provenance visible together, including after a crash.
Readers ignore pending directories. A single-writer lock prevents lost updates.
"""

import json
import os
import re
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import zstandard as zstd

from .ids import canonical, text_hash
from .schema import ID_FIELDS, RECORDS, SCHEMA_VERSION, Provenance, schema_hash


def validate_integrity(records):
    tables = {kind: {} for kind in RECORDS}
    for row in records:
        kind = type(row).__name__
        ident = getattr(row, ID_FIELDS[kind])
        if kind == "Provenance":
            ident = (row.record_type, ident)
        if ident in tables[kind]:
            raise ValueError(f"Duplicate {kind} identity")
        tables[kind][ident] = row

    def require(kind, ident):
        if ident is not None and ident not in tables[kind]:
            raise ValueError(f"Unresolved {kind} reference: {ident}")

    for kind, rows in tables.items():
        if kind == "Provenance":
            for p in rows.values():
                if p.record_type not in tables or p.record_type == "Provenance":
                    raise ValueError("Invalid provenance subject type")
                require(p.record_type, p.record_id)
            continue
        for ident, row in rows.items():
            if (kind, ident) not in tables["Provenance"]:
                raise ValueError(f"Missing provenance for {kind}")
            if row.supersedes:
                require(kind, row.supersedes)
                if row.supersedes == ident:
                    raise ValueError("Record cannot supersede itself")
            if kind != "Maker" and hasattr(row, "maker_id"):
                require("Maker", row.maker_id)
            if kind in ("Revision", "Session"):
                require("Artifact", row.artifact_id)
            if kind == "Artifact":
                for m in row.maker_ids:
                    require("Maker", m)
                for r in row.revisions:
                    require("Revision", r)
                    if tables["Revision"][r].artifact_id != row.artifact_id:
                        raise ValueError("Artifact references another artifact's revision")
            if hasattr(row, "stated_goal_ids"):
                for g in row.stated_goal_ids:
                    require("StatedGoal", g)
            if kind == "Revision":
                for p in row.parent_revision_ids:
                    require("Revision", p)
                    parent = tables["Revision"][p]
                    if parent.artifact_id != row.artifact_id or parent.t > row.t:
                        raise ValueError("Invalid revision ancestry")
            if kind in ("Decision", "ContextEvent"):
                require("Session", row.session_id)
                session = tables["Session"][row.session_id]
                start = row.t_open if kind == "Decision" else row.t
                end = row.t_resolve if kind == "Decision" else row.t
                if not session.t_start <= start <= end <= session.t_end:
                    raise ValueError("Event outside session chronology")
                if kind == "Decision" and row.maker_id != session.maker_id:
                    raise ValueError("Decision maker differs from session maker")
            if kind == "Correction":
                require("Decision", row.decision_id)
                require("Revision", row.revision_id)
                if row.revision_id:
                    revision = tables["Revision"][row.revision_id]
                    if (
                        revision.maker_id is not None
                        and revision.maker_id != row.maker_id
                        or row.t < revision.t
                    ):
                        raise ValueError("Correction precedes or misattributes its revision")
                if row.decision_id:
                    decision = tables["Decision"][row.decision_id]
                    if decision.maker_id != row.maker_id or row.t < decision.t_open:
                        raise ValueError("Correction precedes or misattributes its decision")
            if kind == "StatedGoal":
                require(row.scope.title(), row.scope_id)

    # Reject cycles even when two records share an identical timestamp.
    for kind, field in [("Revision", "parent_revision_ids")] + [
        (k, "supersedes") for k in RECORDS if k != "Provenance"
    ]:
        visited, active = set(), set()

        def visit(ident, *, active=active, visited=visited, kind=kind, field=field):
            if ident in active:
                raise ValueError("Cyclic revision ancestry")
            if ident in visited:
                return
            active.add(ident)
            parents = getattr(tables[kind][ident], field)
            for parent in [parents] if isinstance(parents, str) else parents or []:
                visit(parent)
            active.remove(ident)
            visited.add(ident)

        for ident in tables[kind]:
            visit(ident)
    return tables


class Ledger:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.batches = self.root / "batches"
        self.batches.mkdir(exist_ok=True)
        self.blobs = self.root / "text"
        self.blobs.mkdir(exist_ok=True)
        expected = {"schema_version": SCHEMA_VERSION, "schema_hash": schema_hash()}
        path = self.root / "schema.json"
        try:
            with path.open("x", encoding="utf-8") as f:
                json.dump(expected, f, sort_keys=True)
        except FileExistsError:
            if json.loads(path.read_text(encoding="utf-8")) != expected:
                raise ValueError("Ledger schema version/hash mismatch")

    def _blob(self, ref):
        if not re.fullmatch(r"[0-9a-f]{64}", ref):
            raise ValueError("Invalid content reference")
        return self.blobs / (ref + ".zst")

    def put_text(self, text: str) -> str:
        ref = text_hash(text)
        path = self._blob(ref)
        data = zstd.ZstdCompressor().compress(text.encode("utf-8"))
        temp = self.blobs / (".pending-" + uuid.uuid4().hex)
        try:
            temp.write_bytes(data)
            # Linking commits without replacing an existing blob.
            try:
                os.link(temp, path)
            except FileExistsError:
                if self.get_text(ref) != text:
                    raise ValueError("Content store collision")
        finally:
            temp.unlink(missing_ok=True)
        return ref

    def get_text(self, ref: str) -> str:
        raw = zstd.ZstdDecompressor().decompress(
            self._blob(ref).read_bytes(), max_output_size=64 * 1024 * 1024
        )
        text = raw.decode("utf-8")
        if text_hash(text) != ref:
            raise ValueError("Content blob hash mismatch")
        return text

    def rows(self, kind: str):
        if kind not in RECORDS:
            raise ValueError("Unknown record type")
        paths = sorted(
            str(p / f"{kind}.parquet")
            for p in self.batches.iterdir()
            if p.is_dir() and not p.name.startswith(".") and (p / f"{kind}.parquet").is_file()
        )
        if not paths:
            return []
        with duckdb.connect(":memory:", config={"threads": 1}) as connection:
            values = connection.execute("SELECT payload FROM read_parquet(?)", [paths]).fetchall()
        return [RECORDS[kind].model_validate_json(value) for (value,) in values]

    def all(self):
        return [row for kind in RECORDS for row in self.rows(kind)]

    def snapshot(self):
        """Pin the visible atomic batches for one analysis, avoiding repeated scans."""
        # Select paths once: concurrent appends cannot produce a mixed view.
        batches = sorted(
            p for p in self.batches.iterdir() if p.is_dir() and not p.name.startswith(".")
        )
        tables = {}
        for kind in RECORDS:
            paths = [
                str(p / f"{kind}.parquet") for p in batches if (p / f"{kind}.parquet").is_file()
            ]
            values = []
            if paths:
                with duckdb.connect(":memory:", config={"threads": 1}) as connection:
                    values = connection.execute(
                        "SELECT payload FROM read_parquet(?)", [paths]
                    ).fetchall()
            tables[kind] = [RECORDS[kind].model_validate_json(v) for (v,) in values]
        return LedgerView(self, tables)

    @contextmanager
    def _writer(self):
        path = self.root / ".writer.lock"
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise RuntimeError(
                "Ledger writer is busy; inspect ownership before removing a stale lock"
            )
        try:
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            yield
        finally:
            path.unlink(missing_ok=True)

    def append(self, records, provenance: list[Provenance]):
        new = list(records) + list(provenance)
        # Revalidate instances so direct mutation cannot bypass the contract.
        new = [RECORDS[type(r).__name__].model_validate(r.model_dump()) for r in new]
        with self._writer():
            old = self.all()
            validate_integrity(old + new)
            for row in new:
                refs = [
                    getattr(row, key, None) for key in ("content_ref", "before_ref", "after_ref")
                ]
                refs.extend(o.content_ref for o in getattr(row, "options", []))
                for ref in filter(None, refs):
                    self.get_text(ref)
            batch = uuid.uuid4().hex
            pending = self.batches / (".pending-" + batch)
            pending.mkdir()
            try:
                for kind in RECORDS:
                    rows = [r for r in new if type(r).__name__ == kind]
                    if rows:
                        pq.write_table(
                            pa.table(
                                {
                                    "record_id": [getattr(r, ID_FIELDS[kind]) for r in rows],
                                    "payload": [
                                        canonical(r.model_dump(mode="json")).decode() for r in rows
                                    ],
                                }
                            ),
                            pending / f"{kind}.parquet",
                            compression="zstd",
                        )
                pending.rename(self.batches / batch)
            finally:
                if pending.exists():
                    shutil.rmtree(pending)
        return batch

    def append_new(self, records, provenance):
        """Idempotent import of identical records; conflicting identities refuse."""
        old = {
            (type(r).__name__, getattr(r, ID_FIELDS[type(r).__name__])): r
            for r in self.all()
            if not isinstance(r, Provenance)
        }
        selected = {}
        for row in records:
            key = (type(row).__name__, getattr(row, ID_FIELDS[type(row).__name__]))
            existing = old.get(key, selected.get(key))
            if existing is not None:
                if existing != row:
                    raise ValueError(f"Conflicting immutable record: {key[0]}")
            else:
                selected[key] = row
        if not selected:
            return None
        proofs = {(p.record_type, p.record_id): p for p in provenance}
        return self.append(selected.values(), [proofs[k] for k in selected])


class LedgerView:
    """Read-only record snapshot backed by immutable, hash-checked text blobs."""

    def __init__(self, ledger, tables):
        self.root, self.tables, self.get_text = ledger.root, tables, ledger.get_text

    def rows(self, kind):
        return list(self.tables[kind])

    def all(self):
        return [r for kind in RECORDS for r in self.tables[kind]]

    def snapshot(self):
        return self
