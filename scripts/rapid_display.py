"""Build TP71 from the immutable TP60 contract, retaining its original evidence."""

import json
from pathlib import Path

from tompathy_engine.packet.research_labels import tag_keys, tag_label
from word_table_lane import pin

PUBLIC = Path("engine/validation")
TP60 = "1505edb2f1f8c65222eee3194c1e679d4d6358c293631c870e0d499cbff93e24"


def prepare():
    path = PUBLIC / "readers-tp60-2026-11.json"
    if pin(path) != TP60:
        raise ValueError("The source display contract differs")
    source = json.loads(path.read_bytes())
    groups = source["tagGroups"]
    groups["Belonging"].remove("belonging")
    groups["Respect"].append("acceptance")
    separate = groups.pop("Meaning")
    for arms in source["authorReliability"]["cells"].values():
        for arm in arms.values():
            arm["tags"] = tag_keys(arm["tags"])
    ordered = [tag_label(key) for group in groups.values() for key in group] + separate
    if len(set(ordered)) != 19 or len(ordered) != 19:
        raise ValueError("A display label was duplicated or dropped")
    names = {"LUST": "wanting", "PLAY": "amusement", "PANIC/GRIEF": "SADNESS"}
    return {
        "card": "TP71",
        "rulings": ["CZ", "R47", "BC"],
        "source": path.as_posix(),
        "sourceAggregatePin": TP60,
        "sourceReceiptPin": source["sourceReceiptPin"],
        "tagGroups": groups,
        "ungroupedTags": separate,
        "inputAliases": {"belonging": "acceptance"},
        "channels": [names.get(n, n) for n in source["channels"]],
        "channelScope": {
            "SHAME": "Silent outside chat in the saved readings until TP64 part 3 measures a varying output."
        },
        "authorReliability": source["authorReliability"],
        "textState": source["textState"],
        "bodySeparate": source["bodySeparate"],
        "unmappedNeedID": None,
        "productionAdmission": False,
    }
