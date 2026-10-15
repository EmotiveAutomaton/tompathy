from .ids import utc_now
from .schema import ID_FIELDS, Provenance


def provenance_for(rows, adapter, source_hash, version="1"):
    created = utc_now()
    return [
        Provenance(
            record_id=getattr(r, ID_FIELDS[type(r).__name__]),
            record_type=type(r).__name__,
            adapter=adapter,
            adapter_version=version,
            source_file_sha256=source_hash,
            created_at=created,
        )
        for r in rows
    ]
