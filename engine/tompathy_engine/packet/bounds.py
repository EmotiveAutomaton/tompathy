"""Bound a reading while retaining linked evidence and an explicit omission notice."""


def bound(packet, maximum=1000):
    if len(packet["hypotheses"]) <= maximum:
        return
    rows = packet["hypotheses"]
    # Keep module findings first, then the newest historical nodes. Source
    # records stay in the ledger, and the packet records the display omission.
    selected = sorted(enumerate(rows), key=lambda pair: (pair[1]["status"] != "observed", pair[0]))[
        -maximum:
    ]
    keep = {h["id"] for _, h in selected}
    packet["hypotheses"] = [h for h in rows if h["id"] in keep]
    packet["process"]["nodes"] = [n for n in packet["process"]["nodes"] if n in keep]
    packet["process"]["edges"] = [
        e for e in packet["process"]["edges"] if e["from"] in keep and e["to"] in keep
    ]
    if "population" in packet:
        packet["population"]["items"] = [
            r for r in packet["population"]["items"] if r["hypothesis"] in keep
        ]
    if "currentAttention" in packet:
        frames = []
        for frame in packet["currentAttention"]:
            frame["items"] = [i for i in frame["items"] if i["hypothesis"] in keep]
            if frame["items"]:
                frames.append(frame)
        packet["currentAttention"] = frames
    if "goalHierarchy" in packet:
        nodes = [n for n in packet["goalHierarchy"]["nodes"] if n["id"] in keep]
        for node in nodes:
            if "parentIds" in node:
                node["parentIds"] = [p for p in node["parentIds"] if p in keep]
                if not node["parentIds"]:
                    del node["parentIds"]
        if nodes:
            packet["goalHierarchy"]["nodes"] = nodes
        else:
            del packet["goalHierarchy"]
    packet["provider"]["method"] += (
        f" Display bound omitted {len(rows) - maximum} hypotheses; complete records remain in the ledger."
    )
