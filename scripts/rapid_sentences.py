"""Q29 and its G13 overlap. Bind sentences in original report order on each machine."""

import gzip
import hashlib
import json
from pathlib import Path

from word_table_lane import pin, read

GO = "0e0ff8c5330f98bd6d73cfa70a597542dee19071c0400dc3084a823f1eb61f78"
ISEAR = "98e1db40cf3f2a08e649ab41a94c617ad66e780c8e74f9b6ff59050cbdc45055"


def digest(text):
    return hashlib.sha256(text.encode("utf8")).hexdigest()


def split_source(name, reports, split):
    ids, items, links = set(), [], []
    empty = 0
    for report in reports:
        if set(report) != {"id", "text"} or report["id"] in ids:
            raise ValueError("Duplicate parent or a field outside the reader allowlist")
        parent = report["id"]
        ids.add(parent)
        parts = split(report["text"])
        empty += int(not parts)
        for j, sentence in enumerate(parts):
            key = digest(f"Q29:{name}:{parent}:{j}")
            items.append({"id": key, "text": sentence})
            links.append([key, parent, j, len(parts)])
    return (
        items,
        links,
        {"reports": len(ids), "sentences": len(items), "emptyReports": empty},
    )


def prepare(root, isear, split):
    forum = root / "inputs/go.jsonl.gz"
    if pin(forum) != GO or pin(isear) != ISEAR:
        raise ValueError("The held-out forum or original ISEAR roster changed")
    items, links, counts = [], {}, {}
    with gzip.open(forum, "rt", encoding="utf8") as f:
        go = (json.loads(line) for line in f)
        for name, reports in [("go", go), ("isear", read(isear))]:
            rows, mapping, n = split_source(name, reports, split)
            items.extend(rows)
            links[name] = mapping
            counts[name] = n
    if [counts[k]["reports"] for k in ("go", "isear")] != [11571, 7666] or (
        len({r["id"] for r in items}) != len(items)
    ):
        raise ValueError("Original sentence roster is incomplete")
    # Length-prefixed text and ID bytes unambiguously bind sentence order and spelling.
    encoded = hashlib.sha256()
    for row in items:
        for value in (row["id"], row["text"]):
            data = value.encode("utf8")
            encoded.update(len(data).to_bytes(8, "big"))
            encoded.update(data)
    result = {
        "sources": {"go": GO, "isear": ISEAR},
        "counts": counts,
        "orderedTextPin": encoded.hexdigest(),
        "orderedIdPin": digest("\n".join(r["id"] for r in items)),
    }
    return items, links, result


def local_manifest(root):
    from rapid_land import put
    from tompathy_engine.eval.readers.tp31_teacher import sentences

    _, links, result = prepare(
        root, Path(".local/person-teacher/cb/isear.json"), sentences
    )
    output = root / "Q29-inputs"
    put(output / "local-parent-joins.json", links)
    put(output / "manifest.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(local_manifest(Path(".local/rapid-20261127"))))
