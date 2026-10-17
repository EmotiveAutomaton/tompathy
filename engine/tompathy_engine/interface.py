"""Versioned integration contract; no dataset or admission is manufactured."""

from . import __version__
from .adapters.native_panel import EXCHANGE_FORMAT
from .adapters.panel import DATASETS
from .admission import Admission, implementation_hash
from .features.augment import Features
from .features.records import Labels
from .ledger.schema import RECORDS, SCHEMA_VERSION, schema_hash
from .models.goals import GoalInputs
from .models.pipeline import Pipeline
from .transcribe.runner import CATALOGUE
from .version import source_revision


def contract():
    return {
        "format": "tompathy-research-interface-1",
        "engine_version": __version__,
        "commit": source_revision(),
        "implementation_hash": implementation_hash(),
        "ledger_schema_version": SCHEMA_VERSION,
        "ledger_schema_hash": schema_hash(),
        "record_schemas": {k: v.model_json_schema() for k, v in RECORDS.items()},
        "literal_labels_schema": Labels.model_json_schema(),
        "local_features_schema": Features.model_json_schema(),
        "pipeline_schema": Pipeline.model_json_schema(),
        "goal_candidates_schema": GoalInputs.model_json_schema(),
        "admission_schema": Admission.model_json_schema(),
        "literal_questions": CATALOGUE,
        "native_panel": {
            "format": EXCHANGE_FORMAT,
            "datasets": sorted(DATASETS),
            "compatibility": "Additive exchange metadata; unchanged ledger schema and observation IDs",
            "source_coordinates": "native_source: original IDs, record index/hash, observation unit and raw observation",
            "chronology": "Timezone-aware source windows only; explicit independent witnesses retained; unknowns excluded",
            "audit": "native-panel receipt contains source/exchange/implementation/schema hashes; ledger receipt maps every observation to records or an exclusion",
            "migration": "Use a fresh ledger for changed records; do not mutate pinned research capsules",
        },
        "module_gates": {
            "corrections": ["Q8", "Q9"],
            "joint-preferences": ["Q8", "Q9"],
            "literal-preferences": ["each requested question"],
            "diagnosticity": ["shuffled control"],
            "habits": [],
            "source-trust": [],
            "attention": [],
            "expertise": ["Q8", "censored outcome witnesses"],
            "drive-recipes": ["Q10", "admitted choice/correction fit", "full covariance"],
            "population-prior": ["drive-recipes", "zero own-maker observations"],
            "local-features": ["model_pin is digest of the feature model_pins dictionary"],
            "goal-tree": ["goal-candidates with model_pin"],
        },
        "evaluation": {
            "tasks": ["handling", "options", "corrections"],
            "text_modules": [
                "uniform",
                "population",
                "backbone",
                "corrections",
                "joint",
                "prototypes",
                "diagnosticity",
                "correction-augmented",
            ],
            "unit": "decision",
            "format": "Parquet",
            "promotion": "external research only",
        },
        "truth_policy": "Ghost truth sidecars are never read by the product engine",
    }
