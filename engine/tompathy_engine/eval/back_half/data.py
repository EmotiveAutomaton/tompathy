"""Strict local export boundary; timing/labels never become reader input."""
import hashlib
import json
import math
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from ...adapters.replay import replay
from ...preview.surface import WORD


class ReplayMismatch(ValueError):
    def __init__(self, exclusions, total):
        self.exclusions, self.total = exclusions, total
        super().__init__(f"More than 5% of sessions dropped ({len(exclusions)}/{total}); repair replay agreement before scoring")


def normalize(text):
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n")).rstrip()


def text_hash(text):
    return hashlib.sha256(normalize(text).encode("utf8")).hexdigest()


def utf16_to_codepoint(text, offset):
    if type(offset) is not int or offset < 0:
        raise ValueError("Invalid UTF-16 offset")
    used = 0
    for index, char in enumerate(text):
        if used == offset:
            return index
        used += len(char.encode("utf-16-le")) // 2
        if used > offset:
            raise ValueError("Offset splits a surrogate pair")
    if used == offset:
        return len(text)
    raise ValueError("Offset outside text")


def load_bundle(manifest, kind):
    path = Path(manifest).resolve()
    value = json.loads(path.read_text(encoding="utf8"))
    if value.get("schema") != "tompathy.bench.bundle.v1" or value.get("kind") != kind:
        raise ValueError("Export needs a reviewed format adapter and matching manifest")
    if type(value.get("rows")) is not int or value["rows"] <= 0:
        raise ValueError("Export row count must be a positive integer")
    out = {}
    for name in ("records", "readme"):
        entry = value[name]
        source = (path.parent / entry["path"]).resolve()
        if not source.is_relative_to(path.parent):
            raise ValueError("Bundle path escapes its root")
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("Export digest mismatch")
        out[name] = raw.decode("utf8")
    rows = [json.loads(line) for line in out["records"].splitlines() if line.strip()]
    if not rows or len(rows) != value["rows"]:
        raise ValueError("Export row count mismatch")
    return value, rows


def align_session(text, exported):
    text = normalize(text)
    labels = exported["words"]
    previous = 0
    for row in labels:
        if (type(row.get("start")) is not int or type(row.get("end")) is not int or not previous <= row["start"] < row["end"]
                or row.get("source") not in {"writer", "suggestion", "prompt"}):
            raise ValueError("Invalid EX1 code-point spans or source")
        if row["source"] == "writer" and (type(row.get("stop")) is not bool or type(row.get("logPause")) not in (float,int) or not math.isfinite(row["logPause"])):
            raise ValueError("Writer words require finite stop-label evidence")
        previous = row["end"]
    target = list(WORD.finditer(text))
    if text_hash(text) == exported["textSha256"]:
        spans = {(m.start(),m.end()) for m in target}
        if len(labels) != len(target) or any((r["start"],r["end"]) not in spans for r in labels):
            raise ValueError("Hash matches but exported word segmentation differs; adapter required")
        return labels, {"method": "exact-hash", "alignedFraction": 1.}
    matching = SequenceMatcher(None, [r["end"]-r["start"] for r in labels], [m.end()-m.start() for m in target], autojunk=False)
    pairs = [(i+k,j+k) for i,j,n in matching.get_matching_blocks() for k in range(n)]
    fraction = len(pairs)/max(1,len(labels),len(target))
    if fraction < .98:
        return None, {"method": "word-length-sequence", "alignedFraction": fraction}
    return [{**labels[i], "start": target[j].start(), "end": target[j].end()} for i,j in pairs], {
        "method": "word-length-sequence", "alignedFraction": fraction, "warning": "Length agreement is not semantic identity; unmatched words excluded."}


def replay_exports(exports, roster, source_root):
    lookup = {r["session"]: r for r in roster}
    if len(lookup) != len(roster):
        raise ValueError("Duplicate roster session")
    root = Path(source_root).resolve()
    sessions, exclusions, folds, seen = [], [], {}, set()
    for item in exports:
        if item["session"] in seen or type(item["fold"]) is not int or item["fold"] not in range(5):
            raise ValueError("Duplicate session or invalid writer fold")
        seen.add(item["session"])
        writer = item["writer"]
        if writer in folds and folds[writer] != item["fold"]:
            raise ValueError("A writer crosses folds")
        folds[writer] = item["fold"]
        source = lookup[item["session"]]
        if source["writer"] != writer:
            raise ValueError("Writer identity needs a supplied export-to-roster mapping")
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Roster path escapes source root")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["source_sha256"]:
            raise ValueError("Raw replay source hash mismatch")
        events = [json.loads(line) for line in raw.decode("utf8").splitlines() if line.strip()]
        times = [float(e["eventTimestamp"]) for e in events]
        if not times or not all(math.isfinite(t) for t in times) or times != sorted(times):
            raise ValueError("Session chronology unavailable or nonmonotonic")
        result = replay(events)
        if not result["reconstructed"]:
            exclusions.append({"session": item["session"], "reason": "replay failure"})
            continue
        text = normalize(result["final_document"])
        aligned, report = align_session(text, item)
        if aligned is None:
            exclusions.append({"session": item["session"], "reason": "alignment below 98%", **report})
        else:
            sessions.append({"session": item["session"], "writer": writer, "fold": item["fold"], "genre": item["genre"],
                "time": times[0], "text": text, "words": aligned, "alignment": report})
    if len(exclusions)/max(1,len(exports)) > .05:
        raise ReplayMismatch(exclusions,len(exports))
    return sessions, exclusions


def history_contexts(sessions, reader, seed=20261111):
    import numpy as np
    rng = np.random.default_rng(seed)
    writers = sorted({s["writer"] for s in sessions})
    genres = {w: {s["genre"] for s in sessions if s["writer"] == w} for w in writers}
    donors = {}
    for writer in writers:
        choices = [w for w in writers if w != writer and genres[writer] <= genres[w]]
        donors[writer] = choices[int(rng.integers(len(choices)))] if choices else None
    tokens = {s["session"]: reader.encode(s["text"])["input_ids"] for s in sessions}
    output = {}
    for target in sessions:
        pair = []
        for index, writer in enumerate((target["writer"], donors[target["writer"]])):
            earlier = sorted((s for s in sessions if s["writer"] == writer and s["time"] < target["time"]
                and (index == 0 or s["genre"] == target["genre"])), key=lambda s:(s["time"],s["session"]))
            prior = [t for s in earlier for t in tokens[s["session"]]]
            pair.append(prior[-1024:])
        # Compare matched context amounts; history eligibility is explicit.
        own, other = pair
        output[target["session"]] = {"own": own, "other": other[-len(own):] if own and len(other) >= len(own) else [],
            "eligible": len(own) >= 512, "donor": donors[target["writer"]]}
    return output
