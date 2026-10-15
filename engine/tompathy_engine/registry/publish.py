"""Write immutable, revision-addressed packet files and prefix indexes locally."""

import json
import re
from collections import defaultdict
from pathlib import Path

from ..ledger.ids import canonical, text_hash
from ..packet.contract import Packet


def publish(packets, destination, *, private=False):
    destination = Path(destination)
    prepared = []
    for raw in packets:
        packet = Packet.model_validate(raw).wire()
        artifact = packet["artifact"]
        if not re.fullmatch(r"[0-9a-f]{64}", artifact["revision"]):
            raise ValueError("Registry needs a content SHA-256 revision")
        if packet["scope"]["kind"] != "artifact" or packet["scope"]["contextIds"]:
            raise ValueError(
                "Context-conditioned readings are private and cannot enter an artifact registry"
            )
        sources = [artifact["source"]] + [e["source"] for e in packet["evidence"]]
        if not private and (
            not artifact["source"].startswith("https://")
            or any("coauthor:" in s.lower() for s in sources)
        ):
            raise ValueError(
                "Private or unlicensed dataset reading requires a private local registry"
            )
        hashed = text_hash(artifact["id"])
        relative = f"packets/{hashed}/{artifact['revision']}.json"
        prepared.append((relative, canonical(packet)))
    # Preflight every immutable collision before writing any new packet.
    for relative, data in prepared:
        target = destination / relative
        if target.exists() and target.read_bytes() != data:
            raise ValueError("A different packet already occupies this exact artifact revision")
    for relative, data in prepared:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(data)
    buckets = defaultdict(list)
    for folder in sorted((destination / "packets").glob("*")):
        if not folder.is_dir() or not re.fullmatch(r"[0-9a-f]{64}", folder.name):
            continue
        paths = {p.stem: f"packets/{folder.name}/{p.name}" for p in sorted(folder.glob("*.json"))}
        buckets[folder.name[:4]].append(
            {"artifact_id_hash": folder.name, "revisions": list(paths), "packet_paths": paths}
        )
    index = destination / "index"
    index.mkdir(parents=True, exist_ok=True)
    for prefix, rows in buckets.items():
        temp = index / f".{prefix}.pending"
        temp.write_bytes(canonical(rows))
        temp.replace(index / f"{prefix}.json")
    return {
        "packets": len(prepared),
        "buckets": len(buckets),
        "private": private,
        "action": "local-files-only",
    }


def from_directory(source, destination, *, private=False):
    return publish(
        [json.loads(p.read_text(encoding="utf8")) for p in sorted(Path(source).glob("*.json"))],
        destination,
        private=private,
    )
