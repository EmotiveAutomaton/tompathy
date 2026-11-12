"""Exact per-change UTF-16 ownership for explicitly imported CoAuthor logs.

No corpus access, model loading, timing classifier, or research admission here.
"""
import json
import re
from copy import deepcopy

from ..ledger.ids import digest
from .capture import _SPACE, make_capture, normalize, utf16_length
from .coauthor import _time
from .quill import apply_delta, delta_ops, text_of, units
from .replay import replay


def extract_changes(raw_events, *, source="coauthor:import", title="Imported writing session"):
    events = [json.loads(e) if isinstance(e, str) else e for e in raw_events]
    reference = replay(events)
    if not reference["reconstructed"]:
        raise ValueError("CoAuthor changes require exact replay")
    times = [_time(e.get("eventTimestamp", e.get("timestamp"))) for e in events]
    if times != sorted(times):
        raise ValueError("Nonmonotone session chronology")
    document, owners, changes, menus = [], [], [], []
    for step, event in enumerate(events):
        t = times[step].isoformat().replace("+00:00", "Z")
        if event.get("eventName") == "system-initialize":
            document = units(event["currentDoc"]); owners = [None] * len(document)
            continue
        if event.get("eventName", "").startswith("suggestion-"):
            menus.append({"step": step, "t": t, "event": event["eventName"], "position": event.get("currentCursor")})
        delta = event.get("textDelta")
        if delta in (None, ""):
            continue
        position, edits = 0, []
        for op in delta_ops(delta):
            if "insert" in op:
                edits.append({"position": position, "inserted": units(op["insert"]), "deleted": []})
            elif "delete" in op:
                edits.append({"position": position, "inserted": [], "deleted": document[position:position + op["delete"]]})
                position += op["delete"]
            else:
                position += op["retain"]
        document, owners, _ = apply_delta(document, owners, delta, insertion_owner=step)
        changes.append({"step": step, "t": t, "position": edits[0]["position"] if edits else None,
                        "insertedUnits": sum(len(e["inserted"]) for e in edits), "deletedUnits": sum(len(e["deleted"]) for e in edits),
                        "edits": edits, "delta": deepcopy(delta), "regions": []})
    final = text_of(document)
    if final != reference["final_document"] or len(changes) != reference["deltas"]:
        raise ValueError("Per-change reconstruction differs from replay")
    paragraphs = [m for m in re.finditer(r"[^\r\n]+", final) if normalize(m.group())]
    if len(paragraphs) > 1500:
        raise ValueError("CoAuthor import exceeds capture paragraph bound")
    capture = make_capture([p.group() for p in paragraphs], source, title, times[-1].isoformat().replace("+00:00", "Z"))
    offset_map = [None] * len(document)
    utf16_offsets = [0]
    for char in final:
        utf16_offsets.append(utf16_offsets[-1] + (2 if ord(char) > 0xffff else 1))
    for paragraph, region in zip(paragraphs, capture["regions"]):
        raw = paragraph.group(); offset = 0
        # Preserve every surviving original unit's destination after trimming and
        # whitespace collapse. Surrogate pairs occupy two native Quill units.
        parts, cursor = [], 0
        for space in _SPACE.finditer(raw):
            if cursor < space.start():
                parts.append((cursor, space.start()))
            parts.append(space.span()); cursor = space.end()
        if cursor < len(raw):
            parts.append((cursor, len(raw)))
        for begin, end in parts:
            token = raw[begin:end]
            is_space = bool(_SPACE.fullmatch(token))
            if is_space and (begin == 0 or end == len(raw)):
                continue
            start = utf16_offsets[paragraph.start() + begin]
            size = utf16_length(token)
            for unit in range(size):
                offset_map[start + unit] = {"region": region["id"], "offset": offset if is_space else offset + unit}
            offset += 1 if is_space else size
        if offset != utf16_length(region["anchor"]["exact"]):
            raise ValueError("Final-document normalization map disagrees with capture")
    by_step = {c["step"]: c for c in changes}
    for index, owner in enumerate(owners):
        location = offset_map[index]
        if owner is not None and location and location["region"] not in by_step[owner]["regions"]:
            by_step[owner]["regions"].append(location["region"])
    return {"capture": capture, "changes": changes, "menus": menus, "final_document": final,
            "finalOffsetMap": offset_map, "deltas": len(changes)}


def attach_timeline(packet, extracted):
    from ..preview.timeline import entry, relink_timeline
    if packet["artifact"]["revision"] != extracted["capture"]["revision"]:
        raise ValueError("CoAuthor timeline must match the exact final capture")
    eid = digest(["coauthor-event-timeline", packet["artifact"]["revision"]])
    packet["evidence"].append({"id": eid, "source": packet["artifact"]["source"], "excerpt": "",
                               "capturedAt": packet["artifact"]["capturedAt"], "relationship": "Exact per-change replay; no claim of intention or endorsed suggestions."})
    timeline = [entry(packet["makers"][0]["id"], c["step"], c["t"], region, eid)
                for c in extracted["changes"] for region in c["regions"] or [None]]
    packet["attentionTimeline"] = timeline[:2000]
    packet["preview"]["timelineCoverage"] = {"emitted": min(2000, len(timeline)), "total": len(timeline)}
    packet["origin"] = "imported"
    relink_timeline(packet)
    return packet


def main():
    import argparse
    from pathlib import Path

    from ..packet.build import build_packet
    from ..packet.contract import Packet
    from ..preview.build import build_preview
    parser = argparse.ArgumentParser(description="Import an explicitly selected local CoAuthor JSON event array; no model calls.")
    parser.add_argument("events", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; imports never overwrite source files")
    data = extract_changes(json.loads(args.events.read_text(encoding="utf8")))
    packet = attach_timeline(build_preview(build_packet(data["capture"])), data)
    text = json.dumps(Packet.model_validate(packet).wire(), ensure_ascii=False)
    if len(text) > 2_000_000:
        parser.error("Imported reading exceeds the packet bound")
    args.output.write_text(text, encoding="utf8")


if __name__ == "__main__":
    main()
