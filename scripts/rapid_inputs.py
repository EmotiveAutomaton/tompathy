"""Bind only the three open text rosters commissioned for the Round 37 readers."""

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tompathy_engine.eval.readers.affect_data import ed_situations, verify
from tompathy_engine.eval.readers.tp39 import saved
from tompathy_engine.eval.readers.word_panels import pinned
from week_pride_inputs import FROZEN, SOURCE
from word_table_lane import pin, write


def key(source, original):
    return hashlib.sha256(f"R37:23:{source}:{original}".encode()).hexdigest()


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    data = Path(".local/readers/data")
    old = pinned(FROZEN / "receipt.json", SOURCE)
    ed, ed_info = ed_situations(data / "empathetic-dialogues")
    go = data / "go-emotions"
    if (
        ed_info["intakePin"] != old["sources"]["ed"]["intakePin"]
        or verify(go)["intakePin"] != old["sources"]["go"]["intakePin"]
    ):
        raise ValueError("Original chat or forum intake differs")
    source = data / "crowd-enVent2023/corpus/crowd-enVent_generation.tsv"
    if pin(source) != old["sources"]["envent"]["files"]["generation"]:
        raise ValueError("Event generation table differs")
    events = pd.read_csv(
        source,
        sep="\t",
        quoting=csv.QUOTE_NONE,
        dtype=str,
        keep_default_na=False,
        usecols=["text_id", "hidden_emo_text"],
    )
    comments = pd.concat(
        [
            pd.read_csv(
                go / f"goemotions_{i}.csv",
                dtype=str,
                keep_default_na=False,
                usecols=["id", "text"],
            )
            for i in (1, 2, 3)
        ]
    )
    if comments.groupby("id").text.nunique().max() != 1:
        raise ValueError("Forum text differs between records for the same comment")
    with np.load(
        saved(FROZEN, "go-profile-forecasts.npz", old), allow_pickle=False
    ) as saved_go:
        held = saved_go["ids"].astype(str)
    forum = comments.drop_duplicates("id").set_index("id").loc[held]
    groups = {
        "ed": zip(ed.id, ed.text, strict=True),
        "envent": zip(events.text_id, events.hidden_emo_text, strict=True),
        "go": zip(forum.index, forum.text, strict=True),
    }
    counts = {"ed": 24850, "envent": 6600, "go": 11571}
    files = {}
    for name, rows in groups.items():
        ids = set()
        path = root / (name + ".jsonl.gz")
        with (
            path.open("xb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as target,
        ):
            for native, text in rows:
                item = key(name, native)
                if item in ids:
                    raise ValueError("Duplicate original ID")
                ids.add(item)
                target.write(
                    (
                        json.dumps({"id": item, "text": text}, ensure_ascii=False)
                        + "\n"
                    ).encode()
                )
        if len(ids) != counts[name]:
            raise ValueError(f"Incorrect {name} census")
        files[path.name] = pin(path)
    write(
        root / "inputs.json",
        {
            "files": files,
            "counts": counts,
            "sourceReceiptPin": SOURCE,
            "generationPin": pin(source),
            "edIntakePin": ed_info["intakePin"],
            "goIntakePin": old["sources"]["go"]["intakePin"],
        },
    )


if __name__ == "__main__":
    prepare(Path(sys.argv[1]))
