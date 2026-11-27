"""Round 37 public vocabulary. Numerical head positions and source IDs are stable."""


def tag_label(key):
    return "acceptance" if key == "belonging" else key


def tag_keys(values):
    renamed = {tag_label(k): value for k, value in values.items()}
    if len(renamed) != len(values):
        raise ValueError("The tag and its legacy alias both occur in one set of scores")
    return renamed


def label_readings(box):
    for reading in box["on_page"]:
        if reading["id"] is None or reading["id"].startswith("N"):
            for event in reading["events"]:
                event["label"] = tag_label(event["label"])
            for name in ("people", "floor", "nothing_here"):
                reading[name] = tag_keys(reading[name])
    return box
