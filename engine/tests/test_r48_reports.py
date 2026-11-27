import importlib.util
import json
import sys
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[2] / "scripts" / "r48_reports.py"
spec = importlib.util.spec_from_file_location("r48_reports", path)
reports = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reports
spec.loader.exec_module(reports)


def test_generated_digest_and_pages_match():
    store = reports.Store()
    for name, content in reports.build(store).items():
        assert store.read(name).decode().replace("\r\n", "\n") == content
    assert (
        "No estimate, interval or analytical size"
        in store.read(reports.FOLDER + "TMP2-source.md").decode()
    )


@pytest.mark.parametrize(
    "injected",
    [
        {"distinct_people": 10, "estimate": 0.5},
        {"distinct_people": 11, "maximum": 0.5},
        {"person_key": "constructed", "estimate": 0.5},
        {"distinct_people": 11, "estimate": 0.5},
    ],
)
def test_reject_any_row_added_to_the_header_only_sealed_release(injected):
    class ChangedStore(reports.Store):
        def read(self, name):
            raw = super().read(name)
            if name == reports.aggregate("r48-tmp2-source"):
                d = json.loads(raw)
                d["rows"].append(injected)
                return json.dumps(d).encode()
            return raw

    with pytest.raises(ValueError, match="Unreviewed sealed release"):
        reports.build(ChangedStore())
