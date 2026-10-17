"""Native released panel records -> explicit exchange, preserving source units.

No timestamp is invented. A manifest may supply source-documented time zones or
independently witnessed event windows; missing chronology stays excluded. Dataset
conversion is software support, not admission of identities or target semantics.
"""

import csv
import hashlib
import json
from collections import defaultdict
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from math import isfinite
from pathlib import Path
from zoneinfo import ZoneInfo

from ..admission import implementation_hash
from ..ledger.ids import digest
from ..ledger.schema import schema_hash
from .panel import DATASETS

EXCHANGE_FORMAT = "tompathy-native-panel-2"


def source_record(record, index, ids, *, unit=None, observed=None):
    """Reversible source coordinates; no claim that released labels are people."""
    return {
        "record_index": index,
        "record_sha256": digest(record),
        "ids": deepcopy(ids),
        "unit": deepcopy(unit or {}),
        "observed": deepcopy(observed or {}),
    }


def timestamp(value, manifest, *, epoch=False):
    if value in (None, ""):
        return None
    t = datetime.fromtimestamp(float(value), UTC) if epoch else datetime.fromisoformat(value)
    if t.tzinfo is None:
        if not manifest.get("timezone") or not manifest.get("timezone_evidence"):
            return None
        zone = ZoneInfo(manifest["timezone"])
        candidates = {
            t.replace(tzinfo=zone, fold=fold).astimezone(UTC)
            for fold in (0, 1)
            if t.replace(tzinfo=zone, fold=fold)
            .astimezone(UTC)
            .astimezone(zone)
            .replace(tzinfo=None)
            == t
        }
        # A timezone name alone cannot resolve a DST fold or a nonexistent hour.
        if len(candidates) != 1:
            return None
        t = candidates.pop()
    return t.astimezone(UTC).isoformat()


def opening_time(end, duration, *, milliseconds=False):
    if duration in (None, ""):
        return None
    seconds = float(duration) / (1000 if milliseconds else 1)
    if not isfinite(seconds) or seconds < 0:
        raise ValueError("Native duration must be finite and nonnegative")
    return (datetime.fromisoformat(end) - timedelta(seconds=seconds)).isoformat() if end else None


def convert(records, manifest):
    dataset = manifest["dataset"]
    if dataset not in DATASETS or len(records) != manifest["expected_source_rows"]:
        raise ValueError("Native dataset or original row count mismatch")
    if not all(
        manifest.get(k) for k in ("codebook", "source_uri", "source_sha256", "license_evidence")
    ):
        raise ValueError("Native conversion needs source, license and codebook pins")
    rows = []
    chronology = manifest.get("chronology", {})
    used_windows = set()

    def add(key, maker, options=(), taken=None, prompt="", **extra):
        item = {
            "id": key,
            "maker": maker,
            "options": list(options),
            "taken": taken,
            "prompt": prompt,
            **extra,
        }
        if str(key) in chronology:
            window = chronology[str(key)]
            if not isinstance(window.get("evidence"), str) or not window["evidence"].strip():
                raise ValueError("Supplied chronology needs an independent source witness")
            start, end = (datetime.fromisoformat(window[k]) for k in ("t_open", "t_resolve"))
            if start.utcoffset() is None or end.utcoffset() is None or end < start:
                raise ValueError("Supplied chronology needs ordered timezone-aware timestamps")
            for field, value in (("t_open", start), ("t_resolve", end)):
                if item.get(field) and datetime.fromisoformat(item[field]) != value:
                    raise ValueError("Supplied chronology contradicts native source time")
            item.update(
                t_open=start.astimezone(UTC).isoformat(),
                t_resolve=end.astimezone(UTC).isoformat(),
                chronology_witness=deepcopy(window),
            )
            used_windows.add(str(key))
        rows.append(item)

    if dataset == "multipref":
        axis = manifest.get("target", "overall")
        if axis not in {"overall", "helpful", "truthful", "harmless"}:
            raise ValueError("Unknown MultiPref target")
        for index, r in enumerate(records):
            for group in ("normal_worker_annotations", "expert_worker_annotations"):
                for annotation_index, a in enumerate(r[group]):
                    pref = a[axis + "_pref"]
                    if pref != "Tie" and not pref.startswith(("A-is-", "B-is-")):
                        raise ValueError("Unknown MultiPref preference label")
                    end = timestamp(a["timestamp"], manifest)
                    start = opening_time(end, a.get("time_spent"))
                    add(
                        digest([r["comparison_id"], group, a["evaluator"], axis]),
                        a["evaluator"],
                        [
                            {"id": k, "text": r["completion_" + k.lower()], "origin": "ai"}
                            for k in ("A", "B")
                        ],
                        None if pref == "Tie" else pref[0],
                        r["text"],
                        tie=pref == "Tie",
                        t_open=start,
                        t_resolve=end,
                        prompt_id=r["prompt_id"],
                        native_source=source_record(
                            r,
                            index,
                            {
                                "comparison_id": r["comparison_id"],
                                "prompt_id": r["prompt_id"],
                                "evaluator": a["evaluator"],
                            },
                            unit={
                                "annotation_group": group,
                                "annotation_index": annotation_index,
                                "target": axis,
                            },
                            observed=a,
                        ),
                    )
    elif dataset == "community-alignment":
        for index, r in enumerate(records):
            for turn in ("first", "second", "third", "fourth"):
                prefix = turn + "_turn_"
                options = [
                    {"id": k, "text": r[prefix + "response_" + k], "origin": "ai"}
                    for k in "abcd"
                    if r.get(prefix + "response_" + k)
                ]
                if not options:
                    continue
                chosen = r.get(prefix + "preferred_response")
                mapping = manifest.get("choice_map", {"response_" + k: k for k in "abcd"})
                if chosen and chosen not in mapping:
                    raise ValueError("Community release needs an explicit choice-label mapping")
                add(
                    f"{r['conversation_id']}:{turn}",
                    r.get("annotator_id"),
                    options,
                    mapping.get(chosen),
                    r.get(prefix + "prompt", ""),
                    prompt_id=r["conversation_id"],
                    native_source=source_record(
                        r,
                        index,
                        {
                            "conversation_id": r["conversation_id"],
                            "annotator_id": r.get("annotator_id"),
                        },
                        unit={"turn": turn},
                        observed={"preferred_response": chosen},
                    ),
                )
    elif dataset == "prism":
        for index, r in enumerate(records):
            if manifest.get("record_kind") == "survey":
                scales = manifest.get("preference_scales")
                if not scales or not manifest.get("scale_evidence"):
                    raise ValueError("PRISM stated preferences need codebook-supported scales")
                prefs = []
                for attribute, scale in scales.items():
                    value = r["stated_prefs"][attribute]
                    if (
                        type(value) not in (int, float)
                        or len(scale) != 2
                        or not scale[0] <= value <= scale[1]
                    ):
                        raise ValueError("PRISM stated preference outside its declared scale")
                    prefs.append(
                        {"attribute": attribute, "value": value, "scale": scale, "source": "survey"}
                    )
                add(
                    "survey:" + str(r["user_id"]),
                    r["user_id"],
                    stated_preferences=prefs,
                    native_source=source_record(
                        r,
                        index,
                        {"user_id": r["user_id"]},
                        unit={"record_kind": "survey"},
                        observed={"generated_datetime": r.get("generated_datetime")},
                    ),
                )
                continue
            if "conversation_history" not in r:
                raise ValueError(
                    "PRISM expects conversation records; utterance rows would duplicate prompts"
                )
            turns = defaultdict(list)
            prompts = {}
            for item in r["conversation_history"]:
                if item["role"] == "model":
                    turns[item["turn"]].append(item)
                elif item["role"] == "user":
                    prompts[item["turn"]] = item["content"]
            for turn, candidates in sorted(turns.items()):
                chosen = [c for c in candidates if c["if_chosen"] is True]
                if len(chosen) > 1:
                    raise ValueError("Multiple selected PRISM responses")
                add(
                    f"{r['conversation_id']}:{turn}",
                    r["user_id"],
                    [
                        {"id": str(c["within_turn_id"]), "text": c["content"], "origin": "ai"}
                        for c in candidates
                    ],
                    str(chosen[0]["within_turn_id"]) if chosen else None,
                    prompts.get(turn, ""),
                    prompt_by_maker=True,
                    prompt_id=r["conversation_id"],
                    native_source=source_record(
                        r,
                        index,
                        {"conversation_id": r["conversation_id"], "user_id": r["user_id"]},
                        unit={
                            "turn": turn,
                            "within_turn_ids": [c["within_turn_id"] for c in candidates],
                        },
                        observed={
                            "generated_datetime": r.get("generated_datetime"),
                            "chosen_within_turn_id": chosen[0]["within_turn_id"]
                            if chosen
                            else None,
                        },
                    ),
                )
    elif dataset == "dices":
        target = manifest.get("target")
        if not target or not target.startswith(("Q2_", "Q3_", "Q4_", "Q5_", "Q6_")):
            raise ValueError("DICES needs a declared individual safety-rating target")
        for index, r in enumerate(records):
            if r[target] not in {"Yes", "No", "Unsure"}:
                raise ValueError("Unknown DICES rating")
            end = timestamp(r["answer_timestamp"], manifest, epoch=True)
            start = opening_time(end, r.get("answer_time_ms"), milliseconds=True)
            add(
                str(r["id"]) + ":" + target,
                r["rater_id"],
                [{"id": k, "text": k} for k in ("Yes", "No", "Unsure")],
                r[target],
                r["context"] + "\n" + r["response"],
                t_open=start,
                t_resolve=end,
                action="rate",
                prompt_id=r["item_id"],
                native_source=source_record(
                    r,
                    index,
                    {"id": r["id"], "rater_id": r["rater_id"], "item_id": r["item_id"]},
                    unit={"target": target},
                    observed={
                        target: r[target],
                        "answer_timestamp": r["answer_timestamp"],
                        "answer_time_ms": r.get("answer_time_ms"),
                    },
                ),
            )
    elif dataset == "summarize-from-feedback":
        for index, r in enumerate(records):
            # Batch labels are exposure groups, never timestamps.
            key = digest([r["info"], r["summaries"], r["worker"], r.get("batch")])
            add(
                key,
                r.get("worker"),
                [
                    {"id": str(i), "text": s["text"], "origin": "ai"}
                    for i, s in enumerate(r["summaries"])
                ],
                str(r["choice"]),
                r["info"].get("post", r["info"].get("article", "")),
                prompt_id=str(r["info"].get("id", "unknown")),
                native_source=source_record(
                    r,
                    index,
                    {
                        "info_id": r["info"].get("id"),
                        "worker": r.get("worker"),
                        "batch": r.get("batch"),
                    },
                    observed={"choice": r["choice"]},
                ),
            )
    else:  # MovieLens Beliefs release 2; no user identity joins outside this release.
        for index, r in enumerate(records):
            seen = int(r["isSeen"])
            if seen not in {-1, 0, 1}:
                raise ValueError("Unknown MovieLens exposure status")
            end = timestamp(r["tstamp"], manifest, epoch=True)
            prefs = []
            if seen == 0:
                for field, scale in (
                    ("userPredictRating", [0.5, 5.0]),
                    ("userCertainty", [1.0, 5.0]),
                ):
                    value = float(r[field])
                    if not scale[0] <= value <= scale[1]:
                        raise ValueError("MovieLens belief outside its scale")
                    prefs.append(
                        {
                            "attribute": str(r["movieId"]) + ":" + field,
                            "value": value,
                            "scale": scale,
                            "source": "survey",
                            "t": end,
                        }
                    )
            rating = float(r["userElicitRating"]) if seen == 1 else None
            options = [{"id": str(v / 2), "text": str(v / 2)} for v in range(1, 11)]
            add(
                digest([r["userId"], r["movieId"], r["tstamp"]]),
                r["userId"],
                options,
                str(rating) if rating is not None else None,
                "Movie " + str(r["movieId"]),
                # The released tstamp is not an opening/resolution window.
                # Preserve it, but require a separate chronology witness.
                t_open=None,
                t_resolve=None,
                action="rate",
                stated_preferences=prefs,
                prompt_id=str(r["movieId"]),
                native_source=source_record(
                    r,
                    index,
                    {"userId": r["userId"], "movieId": r["movieId"], "tstamp": r["tstamp"]},
                    observed={
                        k: r.get(k)
                        for k in (
                            "isSeen",
                            "userElicitRating",
                            "userPredictRating",
                            "userCertainty",
                        )
                    },
                ),
            )
    if set(chronology) != used_windows:
        raise ValueError("Supplied chronology contains unknown observation IDs")
    if len({str(row["id"]) for row in rows}) != len(rows):
        raise ValueError("Duplicate native observation IDs; inspect original source records")
    exchange = {
        "format": EXCHANGE_FORMAT,
        "dataset": dataset,
        "source_uri": manifest["source_uri"],
        "source_sha256": manifest["source_sha256"],
        "codebook": manifest["codebook"],
        "license_evidence": deepcopy(manifest["license_evidence"]),
        "manifest_hash": digest(manifest),
        "mapping": {
            k: deepcopy(manifest[k])
            for k in (
                "target",
                "record_kind",
                "timezone",
                "timezone_evidence",
                "choice_map",
                "preference_scales",
                "scale_evidence",
            )
            if k in manifest
        },
        "expected_rows": len(rows),
        "rows": rows,
    }
    return exchange, {
        "format": EXCHANGE_FORMAT,
        "implementation_hash": implementation_hash(),
        "ledger_schema_hash": schema_hash(),
        "source_sha256": manifest["source_sha256"],
        "exchange_hash": digest(exchange),
        "native_source_rows": len(records),
        "normalized_observation_units": len(rows),
        "manifest_hash": digest(manifest),
        "scientific_admission": False,
    }


def from_manifest(path):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding="utf8"))
    source = (path.parent / manifest["file"]).resolve()
    if not source.is_relative_to(path.parent):
        raise ValueError("Native source escapes its declared bundle")
    if source.stat().st_size > manifest.get("maximum_bytes", 1_000_000_000):
        raise ValueError("Native source exceeds declared bound")
    with source.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != manifest["source_sha256"]:
        raise ValueError("Native source pin mismatch")
    with source.open(encoding="utf8", newline="") as stream:
        rows = (
            list(csv.DictReader(stream))
            if source.suffix == ".csv"
            else [json.loads(line) for line in stream if line.strip()]
        )
    return convert(rows, manifest)
