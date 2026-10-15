"""Scientific admission is supplied evidence, never inferred from passing CI."""

from pathlib import Path
from typing import Literal

from .ledger.ids import digest
from .ledger.schema import Hash, Model, schema_hash


class Admission(Model):
    admission_id: str
    module: str
    status: Literal["admitted", "inconclusive", "killed"]
    implementation_hash: Hash
    ledger_schema_hash: Hash
    domain: str
    ghost_record: str | None = None
    sounding_line_record: str | None = None
    ghost_passed: bool = False
    real_data_passed: bool = False
    explanatory_only: bool = False
    calibration: str | None = None
    model_pin: Hash | None = None
    notes: str


def implementation_hash() -> str:
    root = Path(__file__).parent
    return digest(
        {
            p.relative_to(root).as_posix(): p.read_text(encoding="utf8")
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix in {".py", ".yaml"}
        }
    )


class Admissions:
    def __init__(self, records=(), *, implementation=None):
        self.implementation = implementation or implementation_hash()
        self.records = {}
        for record in records:
            admission = Admission.model_validate(record)
            if admission.module in self.records:
                raise ValueError("Multiple admissions for one module; resolve explicitly")
            self.records[admission.module] = admission

    @classmethod
    def load(cls, path: Path | None):
        if path is None:
            return cls()
        return cls(
            [
                Admission.model_validate_json(p.read_text(encoding="utf8"))
                for p in sorted(path.glob("*.json"))
            ]
        )

    def require(self, module, domain, *, probability=False):
        record = self.records.get(module)
        if record is None or record.status != "admitted":
            raise ValueError(f"Module {module} has no admitted record")
        if (
            record.implementation_hash != self.implementation
            or record.ledger_schema_hash != schema_hash()
        ):
            raise ValueError(f"Module {module} admission pin does not match this implementation")
        if record.domain != domain:
            raise ValueError("Admission domain mismatch")
        if not record.ghost_passed or not record.ghost_record or not record.sounding_line_record:
            raise ValueError("Missing constructed-world and real-data admission witnesses")
        if not (record.real_data_passed or record.explanatory_only):
            raise ValueError("Real-data gate did not pass")
        if probability and (
            record.explanatory_only or not record.calibration or not record.real_data_passed
        ):
            raise ValueError("Probability requires a calibrated real-data admission")
        return record

    def enabled(self, domain):
        out = []
        for module in self.records:
            try:
                self.require(module, domain)
                out.append(module)
            except ValueError:
                continue
        return sorted(out)
