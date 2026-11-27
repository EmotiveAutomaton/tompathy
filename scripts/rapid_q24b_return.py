"""Export the verified whole-author suffix after Q24b exits. Retain raw responses on Spark."""

import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/agent/tompathy-open/week-20261122")
ROSTER = "dd5579d130c2fa4b415e862c17aca6574cc78e7ec460d3c4fc45e542e60277fd"
MODEL = "72aac7c28be8ff9b81c2a270eb489c88e6d822a76ec0cb7bf34d965768848567"
SCRIPT = "871f7041c04d7a68af3bea6c56dbfde96020a2455c071eaa58dc89337ccc27a1"


def read(path):
    return json.loads(path.read_bytes())


def pin(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def exit_proof(job):
    owner = read(job / "owner.json")
    pid = owner["pid"]
    if (
        owner["scriptPin"] != SCRIPT
        or owner["job"] != "Q24b"
        or type(pid) is not int
        or pid <= 0
        or Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        != owner["bootId"]
    ):
        raise ValueError("Unexpected boot or owner")
    stat = Path("/proc") / str(pid) / "stat"
    if stat.exists() and stat.read_text().rsplit(")", 1)[1].split()[19] == str(
        owner["startTicks"]
    ):
        raise ValueError("Q24 still running")
    locks = [line.split() for line in Path("/proc/locks").read_text().splitlines()]
    import os

    for path in (job / "dispatcher.lock", Path("/home/agent/gpu.lock")):
        st = path.stat()
        for fields in locks:
            if len(fields) > 5 and fields[1] == "FLOCK" and fields[4] == str(pid):
                major, minor, inode = fields[5].split(":")
                if (int(major, 16), int(minor, 16), int(inode)) == (
                    os.major(st.st_dev),
                    os.minor(st.st_dev),
                    st.st_ino,
                ):
                    raise ValueError("Q24 lease still held")
    markers = [p for p in (job / "failed.json", job / "complete.json") if p.is_file()]
    if len(markers) != 1:
        raise ValueError("Need exactly one terminal receipt")
    return owner, markers[0]


def author_rows(folder, roster, ordinal, offset, common, origin):
    boundary = read(folder / "complete.json")
    if boundary != {
        "rosterPin": ROSTER,
        "rows": len(roster),
        "end": offset + len(roster),
    }:
        raise ValueError("Author boundary differs")
    spans = (
        [0, 100 - (offset - origin)]
        if 0 < 100 - (offset - origin) < len(roster)
        else [0]
    )
    for start, end in zip(spans, [*spans[1:], len(roster)], strict=True):
        block = folder / f"from-{start}" / "B"
        complete = read(block / "complete.json")
        binding = dict(common, ordinal=ordinal, start=start)
        if (
            complete["binding"] != binding
            or complete["modelPin"] != MODEL
            or complete["rows"] != end - start
            or len(list(block.glob("row-*.json"))) != end - start
        ):
            raise ValueError("Reader protocol or completed count differs")
        valid = 0
        for index, (key, _) in enumerate(roster[start:end]):
            row_path = block / f"row-{index:06d}.json"
            raw = row_path.read_bytes()
            row = json.loads(raw)
            value = row["values"]
            if row["index"] != index or row["id"] != key or row["binding"] != binding:
                raise ValueError("Misaligned reader row")
            if value is not None:
                if (
                    not isinstance(value, list)
                    or len(value) != 8
                    or any(type(v) is not int or not 1 <= v <= 5 for v in value)
                ):
                    raise ValueError("Invalid reader scale")
                valid += 1
            yield [ordinal, key, value, hashlib.sha256(raw).hexdigest()]
        if valid != complete["valid"]:
            raise ValueError("Valid count differs")


def export(destination):
    job = ROOT / "jobs/Q24b"
    owner, terminal = exit_proof(job)
    roster = ROOT / "Q24-roster-a.jsonl.gz"
    if (
        pin(roster) != ROSTER
        or pin(ROOT / "code/word_table_lane.py")
        != "eb9fd6517debe3f018676e8110b9eacdef309cf18819109537ab4bdf332b953c"
        or pin(ROOT / "code/spark-reader-job.py")
        != "2553ddc84443cf77ae7af8bb743cfbed7c02ef591f6992778db2eb49165b32ea"
    ):
        raise ValueError("Roster or original runtime differs")
    sys.path.insert(0, str(ROOT / "code"))
    import word_table_lane as lane

    prompt, fields, _ = lane.question("Q24b")
    schema = {
        "type": "object",
        "properties": fields,
        "required": list(fields),
        "additionalProperties": False,
    }
    common = {
        "job": "Q24b",
        "rosterPin": ROSTER,
        "scriptPin": SCRIPT,
        "role": "B",
        "modelPin": MODEL,
        "promptPin": lane.string_pin(prompt),
        "schemaPin": lane.string_pin(json.dumps(schema, sort_keys=True)),
        "options": {
            "temperature": 0,
            "seed": 23,
            "num_ctx": 4096,
            "num_predict": 256,
            "num_thread": 3,
        },
        "think": False,
    }
    original = ROOT / "Q24-return-20261127-a"
    previous = read(original / "receipt.json")
    origin, first = owner["startOffset"], owner["startOrdinal"]
    if (
        pin(original / "receipt.json") != owner["originalReturnPin"]
        or not previous["nativeExited"]
        or not previous["priorLocksReleased"]
        or (origin, first) != (previous["rows"], previous["wholeAuthors"])
    ):
        raise ValueError("Unverified original prefix")
    destination.mkdir(exist_ok=False)
    path = destination / "whole-authors.jsonl.gz"
    offset = origin
    people = valid = 0
    with (
        gzip.open(roster, "rt", encoding="utf8") as source,
        gzip.open(path, "xt", encoding="utf8") as out,
    ):
        for ordinal, line in enumerate(source):
            if ordinal < first:
                continue
            group = json.loads(line)
            folder = job / f"author-{ordinal:05d}"
            if not (folder / "complete.json").exists():
                if terminal.name == "complete.json" or any(
                    int(p.parent.name[7:]) > ordinal
                    for p in job.glob("author-*/complete.json")
                ):
                    raise ValueError("Missing author in completed prefix")
                break
            for row in author_rows(folder, group, ordinal, offset, common, origin):
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
                valid += row[2] is not None
            people += 1
            offset += len(group)
    if terminal.name == "complete.json" and read(terminal).get("rows") != offset:
        raise ValueError("Final row count differs")
    if path.stat().st_size >= 1_000_000_000:
        raise ValueError("Compact return exceeds transfer limit")
    result = {
        "owner": owner,
        "terminal": terminal.name,
        "terminalPin": pin(terminal),
        "terminalReceipt": read(terminal),
        "startOrdinal": first,
        "startOffset": origin,
        "originalReturnPin": owner["originalReturnPin"],
        "rows": offset - origin,
        "wholeAuthors": people,
        "valid": valid,
        "compactPin": pin(path),
        "bytes": path.stat().st_size,
        "rosterPin": ROSTER,
        "modelPin": MODEL,
        "nativeExited": True,
        "priorLocksReleased": True,
    }
    (destination / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def verify_local(directory, week):
    """Independently rejoin every returned ID to the local, pinned roster."""
    receipt = read(directory / "receipt.json")
    roster = week / "Q24-roster-a.jsonl.gz"
    path = directory / "whole-authors.jsonl.gz"
    rapid = week.parent / "rapid-20261127"
    prior = read(rapid / "Q24-transfer.json")
    start = read(rapid / "Q24b-start-verified.json")
    if (
        receipt["originalReturnPin"] != prior["receiptPin"]
        or (receipt["startOrdinal"], receipt["startOffset"])
        != (prior["wholeAuthors"], prior["rows"])
        or receipt["owner"]["originalReturnPin"] != prior["receiptPin"]
        or receipt["owner"]["job"] != "Q24b"
    ):
        raise ValueError("Return and verified original boundary differ")
    owner = receipt["owner"]
    if (
        not receipt["nativeExited"]
        or not receipt["priorLocksReleased"]
        or any(
            owner[key] != start[key]
            for key in ("pid", "startTicks", "bootId", "scriptPin", "commit")
        )
        or receipt["rosterPin"] != ROSTER
        or receipt["modelPin"] != MODEL
        or pin(roster) != ROSTER
        or pin(path) != receipt["compactPin"]
        or path.stat().st_size != receipt["bytes"]
        or receipt["terminal"] not in ("complete.json", "failed.json")
    ):
        raise ValueError("Unverified Q24 return")
    rows = valid = authors = 0
    with (
        gzip.open(roster, "rt", encoding="utf8") as source,
        gzip.open(path, "rt", encoding="utf8") as compact,
    ):
        for ordinal, line in enumerate(source):
            if ordinal < receipt["startOrdinal"]:
                continue
            if ordinal == receipt["startOrdinal"] + receipt["wholeAuthors"]:
                break
            for expected, _ in json.loads(line):
                item = json.loads(next(compact))
                group, key, v, row_hash = item
                if (
                    group != ordinal
                    or key != expected
                    or not re.fullmatch("[0-9a-f]{64}", row_hash)
                ):
                    raise ValueError("Returned prefix/ID mismatch")
                if v is not None:
                    if (
                        not isinstance(v, list)
                        or len(v) != 8
                        or any(type(x) is not int or not 1 <= x <= 5 for x in v)
                    ):
                        raise ValueError("Returned scale mismatch")
                    valid += 1
                rows += 1
            authors += 1
        if next(compact, None) is not None or (rows, valid, authors) != (
            receipt["rows"],
            receipt["valid"],
            receipt["wholeAuthors"],
        ):
            raise ValueError("Returned counts differ")
    return {
        "receiptPin": pin(directory / "receipt.json"),
        "filePin": pin(path),
        "rows": rows,
        "valid": valid,
        "wholeAuthors": authors,
        "terminal": receipt["terminal"],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("export", "verify-local"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = (
        export(args.directory)
        if args.mode == "export"
        else verify_local(args.directory, Path(".local/week-20261122"))
    )
    print(json.dumps(result))
