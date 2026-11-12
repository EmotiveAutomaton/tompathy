"""Constructed software checks; no scientific admission or model benchmark."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ev_export", ROOT / "scripts/export-engine-features.py")
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ConstructedLosses:
    def score(self, text, context, check):
        # Distinct, deterministic losses expose wrong byte/codepoint allocation.
        return [{"start": i, "end": i + 1, "nats": float(i % 11 + 1)} for i in range(len(text))]


def record(text):
    return {"keys": {"session": "constructed-unicode"}, "text": text,
            "textSha256": exporter.sha(text.encode("utf8")),
            "provenance": [{"start": 0, "end": len(text), "occurrenceId": "constructed-event"}]}


def _frozen_outputs(directory):
    """Exercise the exporter's real frozen loader in a fresh interpreter."""
    exporter.frozen_engine(ROOT, Path(directory))
    from tompathy_engine.preview import habits, surface

    class EqualLosses:
        def score(self, text, context, check):
            return [{"start": m.start(), "end": m.end(), "nats": 2.0} for m in surface.WORD.finditer(text)]

    texts = ['  café 😀 repeats unusual words.\r\n\r\nrepeats unusual words; naïve e\u0301 — straße.  ',
             'and but because; unusual words.\n\n"quoted words"', '"unusual quoted passage"',
             "unusual words.\n\nunusual words.", "123 456"]
    return [exporter.export_record(record(text), ConstructedLosses() if i < 3 else EqualLosses(), surface, habits)
            for i, text in enumerate(texts)]


@pytest.fixture(scope="module")
def frozen_outputs(tmp_path_factory):
    directory = tmp_path_factory.mktemp("frozen-export")
    script = "import json,runpy,sys; checks=runpy.run_path(sys.argv[1]); print(json.dumps(checks['_frozen_outputs'](sys.argv[2])))"
    result = subprocess.run([sys.executable, "-X", "utf8", "-B", "-c", script, str(Path(__file__)), str(directory)],
                            check=True, capture_output=True, text=True, encoding="utf8", timeout=60)
    return json.loads(result.stdout)


def test_unicode_offsets_source_and_occurrence_identity(frozen_outputs):
    text = '  café 😀 repeats unusual words.\r\n\r\nrepeats unusual words; naïve e\u0301 — straße.  '
    item = record(text)
    result = frozen_outputs[0]
    assert result["provenance"] == item["provenance"]
    assert result["productionMappingValidated"] is False
    spans = [w["span"] for w in result["words"]] + [w["allocatedSpan"] for w in result["words"]]
    spans += [p["span"] for p in result["previewAttention"]]
    spans += [o["span"] for p in result["departurePhrases"] for o in p["occurrences"]]
    for entry in spans:
        a, b = entry["codepoints"]
        u, v = entry["utf8"]
        s, t = entry["utf16"]
        assert text[a:b] == text.encode()[u:v].decode() == text.encode("utf-16-le")[2*s:2*t].decode("utf-16-le") == entry["exact"]
    repeated = [w for w in result["words"] if w["span"]["exact"] == "repeats"]
    assert len(repeated) == 2 and repeated[0]["span"] != repeated[1]["span"]
    assert result["regions"][0]["start"] == 0
    assert result["regions"][-1]["end"] == len(text)
    assert list(exporter.occurrence_matches("Straße", "strasse")) == [(0, 6)]
    assert list(exporter.occurrence_matches("ß", "s")) == []


def test_habit_vector_denominators_and_source_partition(frozen_outputs):
    result = frozen_outputs[1]
    raw = result["habits"]["raw"]
    assert len(result["habits"]["ratesPer1000UnquotedWords"]) == 14
    assert result["habits"]["ratesPer1000UnquotedWords"]["and"] == 1000 / raw["words"]
    assert result["habits"]["quotedWordShare"] == raw["quotedWords"] / (raw["words"] + raw["quotedWords"])
    only_quotes = frozen_outputs[2]
    assert only_quotes["habits"]["rateStatus"] == "unsupported-empty-denominator"
    assert set(only_quotes["habits"]["ratesPer1000UnquotedWords"].values()) == {None}
    assert only_quotes["habits"]["sentenceMean"] is None


def test_pinned_phrase_prefix_and_zero_spread(frozen_outputs):
    result = frozen_outputs[3]
    assert result["normalization"]["iqr"] == 0
    assert all(w["departure"] == 0 for w in result["words"])
    assert not any(p["recurring"] for p in result["departurePhrases"])
    assert all(p["paragraphSupport"] == 2 for p in result["departurePhrases"])
    unsupported = frozen_outputs[4]
    assert unsupported["status"] == "unsupported"
    assert "normalization" not in unsupported


def test_hash_partition_and_fragment_rejections():
    item = record("real exact text")
    with pytest.raises(ValueError, match="Sha256"):
        exporter.prepare(item | {"text": "changed text"})
    with pytest.raises(ValueError, match="omitted"):
        exporter.prepare(item | {"regions": [{"id": "p", "start": 5, "end": 15}]})
    with pytest.raises(ValueError, match="construction"):
        exporter.prepare(item | {"variant": "writer-typed-fragments"})
    with pytest.raises(ValueError, match="provenance"):
        exporter.prepare(item | {"provenance": [{"occurrenceId": "bad", "start": 0, "end": 999}]})


def test_unicode_fixture():
    path = ROOT / "engine/tests/fixtures/feature-export-unicode.jsonl"
    for line in path.read_text(encoding="utf8").splitlines():
        text, regions, _ = exporter.prepare(json.loads(line))
        assert "😀" in text and len(regions) == 2
