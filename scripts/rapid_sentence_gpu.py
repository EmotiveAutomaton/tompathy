"""Q29's blinded B ratings and frozen channel scores, or W's matched G13 ratings."""

import os
import time

from rapid_gpu import WEEK, job_width, reader_arm, require_pin
from rapid_sentences import prepare
from word_table_lane import read, write


def ten_outputs(out, items, cfg, guard):
    import numpy as np
    import week_spark as week
    from scipy.special import expit

    registration = WEEK / "registration.json"
    require_pin(registration, cfg["weekRegistration"])
    for name, digest in read(registration)["models"].items():
        if name.startswith("base/") or name == "channels.npz":
            guard.check()
            require_pin(week.MODELS / name, digest)
    old = WEEK / "jobs/Q21"
    require_pin(old / "receipt.json", cfg["q21ReceiptPin"])
    source = read(old / "receipt.json")["outputs"]["pride.npz"]
    if source != cfg["pridePin"]:
        raise ValueError("PRIDE source changed")
    require_pin(old / "pride.npz", source)
    with np.load(old / "pride.npz", allow_pickle=False) as saved:
        theta = saved["theta"]
    encode = week.encoder("base", 128)
    folder = out / "ten"
    folder.mkdir()
    started = time.monotonic()
    for i in range(0, len(items), 100):
        guard.check()
        batch = items[i : i + 100]
        vectors = encode([r["text"] for r in batch]).astype(float)
        ten = np.column_stack(
            (week.channels(vectors), expit(vectors @ theta[:-1] + theta[-1]))
        )
        if (
            ten.shape != (len(batch), 10)
            or not np.isfinite(ten).all()
            or not np.all((ten >= 0) & (ten <= 1))
        ):
            raise ValueError("Incomplete frozen sentence forecasts")
        week.persist(
            folder / f"from-{i:06d}.npz",
            ids=np.array([r["id"] for r in batch]),
            ten=ten,
        )
        if i == 0:
            elapsed = time.monotonic() - started
            write(
                folder / "first100.json",
                {
                    "rows": len(batch),
                    "seconds": elapsed,
                    "projectionHours": elapsed * len(items) / len(batch) / 3600,
                },
            )
    return {
        "rows": len(items),
        "columns": 10,
        "seconds": time.monotonic() - started,
        "pridePin": source,
    }


def run(root, out, job, cfg, guard):
    import tp31_teacher as teacher

    guard.check()
    isear = (
        (root.parent / "person-teacher")
        if os.name == "nt"
        else WEEK.parent / "person-teacher-20261121"
    ) / "cb/isear.json"
    items, _, result = prepare(root, isear, teacher.sentences)
    if result != cfg["sentences"]:
        raise ValueError(
            "Sentence census, order or spelling differs from the frozen roster"
        )
    write(out / "intake.json", result)
    role = "W" if job == "G13-Q29" else "B"
    reader_arm(
        out,
        items,
        role,
        "sentence",
        1 if role == "W" else job_width(root),
        guard,
        job,
        role,
    )
    measured = {"intake": result, "reader": read(out / role / "complete.json")}
    if job == "Q29":
        guard.check()
        measured["frozen"] = ten_outputs(out, items, cfg, guard)
        pilot = (
            read(out / role / "first100.json")["projectedHours"]
            + read(out / "ten/first100.json")["projectionHours"]
        )
        measured["combinedFirst100"] = {
            "projectedHours": pilot,
            "packetHours": 3,
            "overThreeTimes": pilot > 9,
        }
    return measured
