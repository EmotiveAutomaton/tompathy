"""Offline EV feature export from certified-fit-1; no research admission.

Run in a fresh process under the consumer's counted CPU supervisor. Input and
output stay in the consumer's private workspace. See docs/ENGINE_FEATURE_EXPORT.md.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from statistics import mean

ENGINE_COMMIT = "5f3ad0a304727fff5e1a6beca592e786ee71b181"
READER_MANIFEST_SHA256 = "7612cbcd48959ed57557d659d6aa3961a8c9e210fd9e4c76f7a8923c1b6a2e8f"
FORMAT = "tompathy-ev-features-1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")


def boundaries(text):
    utf8, utf16 = [0], [0]
    for char in text:
        utf8.append(utf8[-1] + len(char.encode("utf8")))
        utf16.append(utf16[-1] + len(char.encode("utf-16-le")) // 2)
    return utf8, utf16


def span(text, start, end, offsets=None):
    utf8, utf16 = offsets or boundaries(text)
    return {"codepoints": [start, end], "utf8": [utf8[start], utf8[end]],
            "utf16": [utf16[start], utf16[end]], "exact": text[start:end]}


def prepare(record):
    if not isinstance(record, dict) or not isinstance(record.get("text"), str):
        raise TypeError("Input requires exact text")
    text = record["text"]
    encoded = text.encode("utf8")  # Reject unpaired surrogates, never repair them.
    if not text.strip() or len(encoded) > 4_000_000:
        raise ValueError("Text must be nonempty and at most 4 MB")
    if record.get("textSha256") != sha(encoded):
        raise ValueError("Exact UTF-8 textSha256 mismatch")
    if not isinstance(record.get("keys"), dict) or not record["keys"]:
        raise ValueError("Private document keys are required")
    variant = record.get("variant", "final-document")
    if variant not in {"final-document", "writer-typed-fragments"}:
        raise ValueError("Unknown input variant")
    if variant == "writer-typed-fragments" and not record.get("fragmentConstruction"):
        raise ValueError("Fragment variant requires its retained-boundary construction")
    provenance = record.get("provenance", [])
    if not isinstance(provenance, list):
        raise TypeError("Provenance must contain original codepoint intervals")
    for item in provenance:
        if not isinstance(item, dict) or not isinstance(item.get("occurrenceId"), str):
            raise TypeError("Each provenance interval needs an original occurrenceId")
        a, b = item.get("start"), item.get("end")
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text):
            raise ValueError("Invalid original provenance interval")
    regions = record.get("regions")
    if regions is None:
        # Blank-line separation preserves source slices, CRLF and all other
        # whitespace inside each paragraph. Omitted separators stay in text hash.
        regions, start = [], 0
        for match in re.finditer(r"(?:\r\n|\n|\r)[ \t]*(?:\r\n|\n|\r)(?:[ \t]*(?:\r\n|\n|\r))*", text):
            if text[start:match.start()].strip():
                regions.append({"id": f"p{len(regions)}", "start": start, "end": match.start()})
            start = match.end()
        if text[start:].strip():
            regions.append({"id": f"p{len(regions)}", "start": start, "end": len(text)})
    if not isinstance(regions, list) or not regions:
        raise ValueError("Nonempty paragraph regions required")
    seen, previous, capture = set(), 0, {"regions": []}
    for region in regions:
        a, b, ident = region.get("start"), region.get("end"), region.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError("Paragraph identities must be unique")
        if type(a) is not int or type(b) is not int or not previous <= a < b <= len(text):
            raise ValueError("Paragraph spans must be ordered, nonempty and disjoint")
        if text[previous:a].strip():
            raise ValueError("Paragraph partition omitted non-whitespace text")
        seen.add(ident)
        previous = b
        capture["regions"].append({"id": ident, "anchor": {"exact": text[a:b]},
                                   "pageHint": {"section": region.get("section", ident)}})
    if text[previous:].strip():
        raise ValueError("Paragraph partition omitted a non-whitespace suffix")
    return text, regions, capture


def occurrence_matches(text, phrase):
    """Pinned casefold substring support, mapped back to exact original spans.

    This is feature recurrence only, NEVER an EV1 production-occurrence join.
    Expanded codepoints (e.g. ß -> ss) may not be split at an internal boundary.
    """
    folded = ""
    original = {0: 0}
    for index, char in enumerate(text):
        folded += char.casefold()
        original[len(folded)] = index + 1
    needle, start = phrase.casefold(), 0
    while needle:
        found = folded.find(needle, start)
        if found < 0:
            break
        end = found + len(needle)
        if found in original and end in original:
            yield original[found], original[end]
        start = found + 1


def phrase_prefix(rows, statistics, surface):
    """Select the pinned first 15 phrase candidates, without its sentence suffix.

    Every exported prefix is checked against summarize_deviation's result below.
    """
    candidates = []
    for row in rows:
        for i, word in enumerate(row["words"]):
            if word["held"] or not word["content"]:
                continue
            group = row["words"][i:i + 3]
            if any(w["held"] for w in group) or re.search(r"[.!?\n]", row["text"][word["end"]:group[-1]["start"]]):
                group = [word]
            selected = [w for w in group if w["content"]]
            value = mean(w["nats"] for w in selected)
            a, b = group[0]["start"], group[-1]["end"]
            candidates.append({"region": row["region"], "start": surface.utf16_length(row["text"][:a]),
                               "end": surface.utf16_length(row["text"][:b]), "text": row["text"][a:b],
                               "departure": (value - statistics["median"]) / statistics["iqr"] if statistics["iqr"] > 1e-12 else 0.0})
    top = []
    for item in sorted(candidates, key=lambda r: -r["departure"]):
        if not any(p["region"] == item["region"] and p["start"] < item["end"] and p["end"] > item["start"] for p in top):
            top.append(item)
        if len(top) == 15:
            break
    return top


def export_record(record, reader, surface, habits, check=lambda: None):
    text, regions, capture = prepare(record)
    offsets = boundaries(text)
    region_by_id = {r["id"]: r for r in regions}
    raw = habits.describe(capture, check)
    denominator, total = raw["words"], raw["words"] + raw["quotedWords"]
    rates = {name: raw["connectives"].get(name, 0) * 1000 / denominator if denominator else None for name in habits.CONNECTIVES}
    rates.update({name: raw["punctuation"].get(name, 0) * 1000 / denominator if denominator else None for name in (",", ";", ":", "—", "?", "!")})
    result = {"status": "complete", "keys": record["keys"], "variant": record.get("variant", "final-document"),
              "textSha256": record["textSha256"], "inputRecordSha256": sha(canonical(record)),
              "provenance": record.get("provenance", []), "provenanceSha256": sha(canonical(record.get("provenance", []))),
              "productionMappingValidated": False, "regions": regions,
              "fragmentConstruction": record.get("fragmentConstruction"),
              "habits": {"raw": raw, "ratesPer1000UnquotedWords": rates,
                         "rateStatus": "supported" if denominator else "unsupported-empty-denominator",
                         "sentenceMean": raw["sentenceMean"] if raw["sentenceCount"] else None,
                         "sentenceSpread": raw["sentenceSpread"] if raw["sentenceCount"] else None,
                         "quotedWordShare": raw["quotedWords"] / total if total else None}}
    rows = surface.score_page(capture, reader, check)
    try:
        summary = surface.summarize_deviation(rows, check)
    except ValueError as error:
        if str(error) != "No scorable content words after names/numbers/code holdouts":
            raise
        result.update(status="unsupported", reason=str(error), words=[], departurePhrases=[], previewAttention=[])
        return result
    stats = summary["statistics"]
    word_output = []
    for row in rows:
        origin = region_by_id[row["region"]]["start"]
        local8, _ = boundaries(row["text"])
        cp_at_byte = {value: i for i, value in enumerate(local8)}
        for word in row["words"]:
            a, b = origin + word["start"], origin + word["end"]
            eligible = word["content"] and not word["held"]
            word_output.append({"region": row["region"], "span": span(text, a, b, offsets),
                                "allocatedSpan": span(text, a, origin + cp_at_byte[word["byteEnd"]], offsets),
                                "allocatedTokenLossNats": word["nats"], "heldOut": word["held"], "content": word["content"],
                                "departure": ((word["nats"] - stats["median"]) / stats["iqr"] if stats["iqr"] > 1e-12 else 0.0) if eligible else None,
                                "provenanceIntersections": [{"index": i, "codepoints": [max(a, p["start"]), min(b, p["end"])]}
                                    for i, p in enumerate(record.get("provenance", [])) if a < p["end"] and b > p["start"]]})
    def located(item):
        region = region_by_id[item["region"]]
        segment = text[region["start"]:region["end"]]
        _, units = boundaries(segment)
        reverse = {value: i for i, value in enumerate(units)}
        return {"region": item["region"], "departure": item["departure"],
                "span": span(text, region["start"] + reverse[item["start"]], region["start"] + reverse[item["end"]], offsets)}
    prefix = phrase_prefix(rows, stats, surface)
    actual = summary["attention"][:len(prefix)]
    if len(prefix) != len(actual) or any(a.keys() != b.keys() or any(
        not math.isclose(a[k], b[k], rel_tol=1e-12, abs_tol=1e-12) if k == "departure" else a[k] != b[k] for k in a
    ) for a, b in zip(prefix, actual, strict=True)):
        raise RuntimeError("Exporter phrase prefix disagrees with pinned engine")
    phrases = []
    for phrase in prefix:
        occurrences = []
        for region in regions:
            for a, b in occurrence_matches(text[region["start"]:region["end"]], phrase["text"]):
                occurrences.append({"region": region["id"], "section": region.get("section") or region["id"],
                                    "span": span(text, region["start"] + a, region["start"] + b, offsets)})
        section_count = len({o["section"] for o in occurrences})
        phrases.append(located(phrase) | {"occurrences": occurrences, "paragraphSupport": len({o["region"] for o in occurrences}),
                                         "sectionSupport": section_count, "recurring": phrase["departure"] > 0 and section_count >= 2,
                                         "matching": "pinned casefold substring; exact source spans; not production identity"})
    return result | {"normalization": stats, "words": word_output, "departurePhrases": phrases,
                     "previewAttention": [located(item) for item in summary["attention"]]}


def frozen_engine(repo, directory):
    """Load Git objects, never the mutable working tree or its installed package."""
    archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=zip", ENGINE_COMMIT, "engine/tompathy_engine"],
                             check=True, capture_output=True).stdout
    files = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        for info in source.infolist():
            if info.is_dir():
                continue
            target = (directory / info.filename).resolve()
            if not target.is_relative_to(directory.resolve()):
                raise ValueError("Unsafe source archive path")
            data = source.read(info)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files[info.filename] = sha(data)
    if any(key == "tompathy_engine" or key.startswith("tompathy_engine.") for key in sys.modules):
        raise RuntimeError("Use a fresh interpreter; engine was already imported")
    sys.path.insert(0, str(directory / "engine"))
    return {"commit": ENGINE_COMMIT, "files": files, "sourceSha256": sha(canonical(files))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reader", type=Path, help="Installed pinned Qwen directory; no downloads")
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--slot-lease", type=Path, help="Existing counted supervisor lease; checked at every scoring boundary")
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--check-input", action="store_true", help="Validate hashes/offsets only; no reader or feature scores")
    args = parser.parse_args()
    if args.check_input:
        count = 0
        with args.input.open(encoding="utf8", newline="") as source:
            for line in source:
                prepare(json.loads(line))
                count += 1
        print(json.dumps({"inputValidated": count, "featuresComputed": False}))
        return
    if not all((args.output, args.reader, args.slot_lease)):
        parser.error("Export requires --output, --reader and --slot-lease under a counted supervisor")
    if args.output.resolve() == args.input.resolve():
        parser.error("Output must differ from input")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", CUDA_VISIBLE_DEVICES="")
    lease = args.slot_lease.read_bytes()
    if not {"native", "card", "at"} <= json.loads(lease).keys():
        raise ValueError("Unrecognized counted lease")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def check():
        if args.stop_file and args.stop_file.exists() or args.slot_lease.read_bytes() != lease:
            raise RuntimeError("Stop requested or counted lease changed")
        if shutil.disk_usage(args.output.parent).free < 20 * 1024**3:
            raise RuntimeError("Output disk floor reached")
        # The counted parent owns the continuous resource monitor and native PID
        # identity. This child never claims/reclaims slots or stops other jobs.
    check()
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="tompathy-ev-engine-") as root:
        engine = frozen_engine(repo, Path(root))
        from tompathy_engine.preview import habits, surface
        from tompathy_engine.preview.readers import LocalReader
        if sha(canonical(json.loads((args.reader / "manifest.json").read_text(encoding="utf8")))) != READER_MANIFEST_SHA256:
            raise ValueError("EV reader manifest differs from the frozen baseline")
        reader = LocalReader(args.reader, args.cache, device="cpu", threads=1, precision="int8")
        if reader.manifest["model"] != "Qwen/Qwen2.5-0.5B":
            raise ValueError("EV baseline requires the pinned Qwen surface reader")
        manifest = {"format": FORMAT, "engine": engine, "exporterSha256": sha(Path(__file__).read_bytes()),
                    "reader": reader.identity, "readerFiles": reader.manifest["files"],
                    "slotLeaseSha256": sha(lease), "scientificAdmission": False,
                    "units": "Half-open document-global codepoints, UTF-8 bytes and UTF-16 code units",
                    "loss": "Byte-allocated token loss, not normalized word probability",
                    "normalization": "Pinned page content-word median/IQR; held-out and function words excluded; IQR <= 1e-12 gives zero"}
        manifest_sha = sha(canonical(manifest))
        manifest_path = args.output.with_suffix(args.output.suffix + ".manifest.json")
        with manifest_path.open("x", encoding="utf8", newline="\n") as output:
            json.dump(manifest, output, ensure_ascii=False, indent=2)
        counts = {"complete": 0, "unsupported": 0, "error": 0}
        with args.input.open(encoding="utf8", newline="") as source, args.output.open("x", encoding="utf8", newline="\n") as output:
            for number, line in enumerate(source, 1):
                check()
                record = None
                try:
                    record = json.loads(line)
                    result = export_record(record, reader, surface, habits, check)
                except (ValueError, TypeError, KeyError, IndexError, RuntimeError, OverflowError) as error:
                    check()  # Cancellation/resource failures escape, not per-text errors.
                    result = {"status": "error", "errorType": type(error).__name__, "reason": str(error),
                              "keys": record.get("keys") if isinstance(record, dict) else None,
                              "inputLineSha256": sha(line.encode("utf8"))}
                counts[result["status"]] += 1
                output.write(json.dumps(result | {"line": number, "manifestSha256": manifest_sha}, ensure_ascii=False, allow_nan=False) + "\n")
                output.flush()
        receipt = {"format": FORMAT, "counts": counts, "manifestSha256": manifest_sha,
                   "outputSha256": sha(args.output.read_bytes()), "scientificAdmission": False}
        with args.output.with_suffix(args.output.suffix + ".receipt.json").open("x", encoding="utf8", newline="\n") as output:
            json.dump(receipt, output, indent=2)
        print(json.dumps(receipt))
        if counts["error"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
