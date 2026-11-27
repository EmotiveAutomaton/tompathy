"""G15. Preserve original W calls; score only unmatched openings from whole Q24 writers."""

import gzip
import json
import os
import time
from collections import Counter
from pathlib import Path

from rapid_marks import digest, protocol, template
from word_table_lane import MODELS, pin, read, write


def new_items(roster, texts, prompt, options):
    """Split the exact roster without changing a post's position or any old missing value."""
    calls = []
    index = []
    for r in roster:
        if "reuse" in r:
            index.append(("historical", None))
            continue
        text = texts[r["opening"]]
        if digest(text) != r["opening"]:
            raise ValueError("Opening content differs from the retained original")
        if (
            not text.strip()
            or len((prompt + text).encode("utf8")) + options["num_predict"] + 64
            > options["num_ctx"]
        ):
            index.append(("context", None))
            continue
        index.append(("new", len(calls)))
        calls.append({"id": r["id"], "text": text})
    return index, calls


def originals(root, cfg, check):
    directory = root / cfg["inputStage"]
    if directory.parent != root or directory.name not in (
        "G15-inputs-b",
        "G15-inputs-c",
    ):
        raise ValueError("Unexpected G15 input directory")
    if (
        pin(directory / "receipt.json") != cfg["inputReceiptPin"]
        or read(directory / "complete.json")
        != {"sourceReceiptPin": cfg["inputReceiptPin"]}
        or pin(directory / "selection.json") != cfg["selectionPin"]
    ):
        raise ValueError("Counted intake receipt differs")
    selection = read(directory / "selection.json")
    if selection != read(directory / "receipt.json")["result"]:
        raise ValueError("Selection differs from the verified input receipt")
    source = directory / "openings.jsonl.gz"
    if pin(source) != selection["rosterPin"]:
        raise ValueError("Opening roster differs")
    with gzip.open(source, "rt", encoding="utf8") as f:
        roster = [json.loads(line) for line in f]
    if (
        len(roster) != selection["posts"]
        or len({r["id"] for r in roster}) != len(roster)
        or any(
            n != 10 for n in Counter((r["ordinal"], r["half"]) for r in roster).values()
        )
        or len({r["ordinal"] for r in roster}) * 20 != len(roster)
    ):
        raise ValueError("Expected ten unique opening rows per date half")
    need = {r["opening"] for r in roster if "reuse" not in r}
    texts = {}
    home = root.parent / "week-20261122/Q20-inputs-a/spark-inputs"
    for name, h in sorted(selection["shards"].items()):
        check()
        if (
            Path(name).name != name
            or not name.endswith(".jsonl.gz")
            or pin(home / name) != h
        ):
            raise ValueError("Q20 opening shard differs")
        with gzip.open(home / name, "rt", encoding="utf8") as f:
            for i, line in enumerate(f):
                if i % 2048 == 0:
                    check()
                k, t = json.loads(line)
                if k in need:
                    if k in texts or digest(t) != k:
                        raise ValueError("Ambiguous Q20 opening")
                    texts[k] = t
    if texts.keys() != need:
        raise ValueError("Unbound G15 opening")
    return selection, roster, texts


def compact(out, roster, index, calls, parse):
    complete = valid = previous = new = missing_context = 0
    counts = Counter()
    for i, r in enumerate(roster):
        kind, j = index[i]
        if kind == "historical":
            previous += 1
            value = r["reuse"]["values"]
        elif kind == "context":
            missing_context += 1
            value = None
        else:
            p = out / "W" / f"from-{j:06d}.json"
            if not p.is_file():
                continue
            rows = read(p)
            if (
                len(rows) != 1
                or rows[0]["id"] != r["id"]
                or rows[0]["id"] != calls[j]["id"]
            ):
                raise ValueError("G15 durable prediction is out of order")
            v = rows[0]
            try:
                value = parse(json.loads(v["response"]))
            except (TypeError, ValueError):
                value = None
            if value != v["values"]:
                raise ValueError(
                    "G15 saved response differs from the parsed prediction"
                )
            new += 1
        counts[r["ordinal"]] += 1
        valid += int(value is not None)
        complete += 1
    return {
        "availableRows": complete,
        "valid": valid,
        "historical": previous,
        "newResponses": new,
        "contextUnavailable": missing_context,
        "wholeAuthors": sum(n == 20 for n in counts.values()),
        "newEligible": len(calls),
        "population": len(roster),
    }


def run(root, out, cfg, guard):
    from rapid_gpu import END, reader_arm

    if os.name != "nt":
        raise RuntimeError("G15 belongs to W")
    selection, roster, texts = originals(root, cfg, guard.check)
    old = selection["sameReaderSettings"]
    opts = {
        "temperature": 0,
        "seed": 23,
        "num_ctx": 4096,
        "num_predict": 256,
        "num_thread": 2,
    }
    bind = {
        "role": "W",
        "modelPin": MODELS["W"][1],
        "think": False,
        "options": opts,
        **protocol("features"),
    }
    if old != bind:
        raise ValueError(
            "G15 prompt, response schema or reader options differ from G11"
        )
    index, calls = new_items(roster, texts, old["prompt"], opts)
    del texts
    write(
        out / "intake.json",
        {
            "sourceReceiptPin": cfg["inputReceiptPin"],
            "originalProtocol": selection["protocolPins"],
            "orderedNewIds": digest("\n".join(c["id"] for c in calls)),
            "new": len(calls),
            "rosterPin": selection["rosterPin"],
            "binding": bind,
        },
    )
    status = "complete"
    if calls:
        try:
            reader_arm(out, calls, "W", "features", 1, guard, "G15", "W")
        except RuntimeError as exc:
            if (
                time.time() < END
                or str(exc)
                not in ("Deadline or owner STOP", "Requested stop or bounded deadline")
                or any(
                    (p / "STOP").exists()
                    for p in (
                        out,
                        root,
                        root.parent / "word-table",
                        root.parent / "person-teacher",
                        root.parent / "week-20261122",
                    )
                )
            ):
                raise
            status = "cutoff"
    result = compact(out, roster, index, calls, template("features")[2])
    if status == "complete" and result["availableRows"] != len(roster):
        raise ValueError("G15 did not account for every opening")
    return {
        **result,
        "status": status,
        "rosterPin": selection["rosterPin"],
        "reuse": selection["reuse"],
        "pilot": read(out / "W/first100.json")
        if (out / "W/first100.json").is_file()
        else None,
    }
