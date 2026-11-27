"""Q31 and the matched G13 arms, using only the text already present in the Q20 shards."""

import gzip
import json
import os
from pathlib import Path

from rapid_sentences import digest
from word_table_lane import pin


def calendar(plan, directory, split, check):
    wanted = {k for group in ("loss", "sample") for _, k in plan[group]}
    texts = {}
    for name, h in sorted(plan["shards"].items()):
        check()
        if Path(name).name != name or not name.endswith(".jsonl.gz"):
            raise ValueError("Unexpected Q20 shard path")
        file = directory / name
        if pin(file) != h:
            raise ValueError("Original Q20 text shard differs")
        with gzip.open(file, "rt", encoding="utf8") as f:
            for i, line in enumerate(f):
                if i % 2048 == 0:
                    check()
                k, text = json.loads(line)
                if k in wanted:
                    if k in texts or digest(text) != k:
                        raise ValueError("Duplicate or changed registered opening")
                    texts[k] = text
    if wanted != texts.keys():
        raise ValueError("Missing registered opening")
    loss = [{"id": p, "text": texts[k]} for p, k in plan["loss"]]
    items = []
    for parent, k in plan["sample"]:
        parts = split(texts[k])
        if not parts:
            raise ValueError("A selected nonempty opening has no sentences")
        items.extend(
            {"id": digest(f"Q31:{parent}:{j}"), "text": s} for j, s in enumerate(parts)
        )

    def roster(values):
        import hashlib

        enc = hashlib.sha256()
        for row in values:
            for s in (row["id"], row["text"]):
                b = s.encode("utf8")
                enc.update(len(b).to_bytes(8, "big"))
                enc.update(b)
        if len({r["id"] for r in values}) != len(values):
            raise ValueError("Repeated inference unit")
        return {
            "n": len(values),
            "orderedIdPin": digest("\n".join(r["id"] for r in values)),
            "orderedTextPin": enc.hexdigest(),
        }

    return (
        loss,
        items,
        {
            "loss": roster(loss),
            "sentences": roster(items),
            "posts": len(plan["sample"]),
        },
    )


def run(root, out, job, cfg, guard):
    import tp31_teacher
    from rapid_gpu import WEEK, job_width, reader_arm, require_pin
    from rapid_marks import protocol
    from rapid_sentence_gpu import ten_outputs
    from word_table_lane import read, write

    selection = root / "Q31-selection.json"
    require_pin(selection, cfg["selectionPin"])
    directory = (
        root.parent / "week-20261122/Q20-inputs-a/spark-inputs"
        if os.name == "nt"
        else WEEK / "Q20-inputs"
    )
    loss, items, intake = calendar(
        read(selection), directory, tp31_teacher.sentences, guard.check
    )
    if intake != cfg["roster"] or any(
        protocol(k) != cfg["prompts"][k] for k in ("sentence", "loss")
    ):
        raise ValueError(
            "The blog sentence order, text or prompt differs from registration"
        )
    write(out / "intake.json", intake)
    role = "W" if os.name == "nt" else "B"
    width = 1 if role == "W" else job_width(root)
    # B's preregistered order is openings then sentences. W's matched work takes the sentence arm first.
    arms = (
        (("loss", loss), ("sentence", items))
        if role == "B"
        else (("sentence", items), ("loss", loss))
    )
    result = {"intake": intake}
    for name, rows in arms:
        guard.check()
        reader_arm(out, rows, role, name, width, guard, job, name)
        result[name] = read(out / name / "complete.json")
    if role == "B":
        guard.check()
        result["frozen"] = ten_outputs(out, items, cfg, guard)
    pilots = [
        read(out / n / "first100.json")["projectedHours"]
        for n in ("loss", "sentence", "ten")
        if (out / n / "first100.json").exists()
    ]
    result["combinedFirst100"] = {
        "projectedHours": sum(pilots),
        "arms": len(pilots),
        "packetHours": 9.8 if role == "B" else None,
        "overThreeTimes": sum(pilots) > 29.4 if role == "B" else None,
    }
    return result
