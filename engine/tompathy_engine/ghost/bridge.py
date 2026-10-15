"""Read a pinned reader bundle. Evaluator truth files are never opened here."""

import json
from pathlib import Path

from ..admission import implementation_hash
from ..ledger.ids import digest
from ..ledger.schema import RECORDS, schema_hash
from ..ledger.store import validate_integrity

# Public reader metadata is explicit. New fields require a schema-versioned
# adapter; a flexible JSON dictionary is not an evaluator sidecar channel.
CONTEXT_KEYS = {
    "document_ref",
    "decision_index",
    "previous_handling",
    "prompt_id",
    "source_ordinal",
    "matched_option_indices",
    "prompt",
    "codebook",
    "fen",
    "ply",
    "clock_resolution",
    "observed_context",
    "available_actions",
    "root_cue",
    "source_label",
}
OUTCOME_KEYS = {
    "reviewed",
    "understood",
    "endorsed",
    "game_result",
    "result_available_at",
    "post_move_engine_score",
    "observed_result",
    "observed_at",
}


def reject_truth_fields(value):
    if isinstance(value, dict):
        for key, child in value.items():
            name = key.lower()
            if name in {
                "truth",
                "latent",
                "oracle",
                "true_preferences",
                "lambda_m",
                "u_m",
                "drive_loadings",
                "creator_predictability",
            } or name.startswith(("truth_", "latent_", "planted_", "oracle_")):
                raise ValueError("Evaluator truth field in reader view")
            reject_truth_fields(child)
    elif isinstance(value, list):
        for child in value:
            reject_truth_fields(child)


def load_reader(path, *, expected_implementation=None):
    path = Path(path)
    value = json.loads(path.read_text(encoding="utf8"))
    reject_truth_fields(value)
    if set(value) != {
        "ledger_schema_hash",
        "implementation_hash",
        "records",
        "texts",
        "reader_hash",
    }:
        raise ValueError("Unexpected reader-bundle field; evaluator sidecars are forbidden")
    expected = expected_implementation or implementation_hash()
    if value["ledger_schema_hash"] != schema_hash() or value["implementation_hash"] != expected:
        raise ValueError("Ghost reader pin mismatch")
    if value["reader_hash"] != digest({k: v for k, v in value.items() if k != "reader_hash"}):
        raise ValueError("Ghost reader payload hash mismatch")
    rows = []
    for raw in value["records"]:
        if set(raw) != {"type", "record"} or raw["type"] not in RECORDS:
            raise ValueError("Invalid canonical reader record")
        record = RECORDS[raw["type"]].model_validate(raw["record"])
        if raw["type"] == "Decision" and (
            not set(record.context) <= CONTEXT_KEYS or not set(record.outcome) <= OUTCOME_KEYS
        ):
            raise ValueError("Reader decision metadata is outside the observable allowlist")
        if raw["type"] == "ContextEvent" and not set(record.payload) <= {
            "observation",
            "clock_s",
            "move",
            "source",
            "available_at",
        }:
            raise ValueError("Context event contains non-observable metadata")
        rows.append(record)
    validate_integrity(rows)
    return rows, value["texts"]


def reader_choices(rows):
    """A constructed world's observable option features use the ordinary model."""
    import numpy as np

    from ..models.backbone import Choice

    result = []
    names = None
    for row in rows:
        if type(row).__name__ != "Decision" or row.taken is None:
            continue
        for option in row.options:
            if names is None:
                names = sorted(option.features)
            if not names or sorted(option.features) != names:
                raise ValueError("Constructed reader needs consistent observable feature names")
        result.append(
            Choice(
                row.decision_id,
                row.maker_id,
                row.t_open,
                row.t_resolve,
                np.array([[o.features[n] for n in names] for o in row.options]),
                next(i for i, o in enumerate(row.options) if o.option_id == row.taken),
            )
        )
    return result


def ingest_reader(path, ledger, *, expected_implementation=None):
    rows, texts = load_reader(path, expected_implementation=expected_implementation)
    for expected, text in texts.items():
        if ledger.put_text(text) != expected:
            raise ValueError("Ghost text hash mismatch")
    ledger.append_new(
        [r for r in rows if type(r).__name__ != "Provenance"],
        [r for r in rows if type(r).__name__ == "Provenance"],
    )
    return {"records": len(rows), "truth_loaded": False}
