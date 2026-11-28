"""Freeze the TP63 report-level inputs and random selections for two independent TP81 builds."""

from pathlib import Path

import numpy as np
import pandas as pd
import rapid_outside as orig
from rapid_cpu_dispatch import confirmed
from word_table_lane import pin, read


def prepare(out, check):
    frame, ids, _, weights, traits, names, census, feeling, writer, _, _ = (
        orig.model_data()
    )
    old = orig.ROOT / "TP63-original-a"
    public = Path("engine/validation/readers-tp63-outside-2026-11.json")
    table = read(public)
    if confirmed(old) != table["sourceReceiptPin"] or census != table["targets"]:
        raise ValueError("TP63 source or available writers changed")
    _, owners = np.unique(writer, return_index=True)
    rows = frame.set_index("text_id").loc[ids]
    if len(ids) != 6600 or len(owners) != 2379 or weights.shape != (28, 384):
        raise ValueError("Unexpected TP63 dimensions")
    cols = list(orig.KEYS.values())
    raw = (
        rows[[k for pair in cols for k in pair]]
        .replace({"": np.nan, "NA": np.nan, "N/A": np.nan, "nan": np.nan})
        .apply(pd.to_numeric, errors="raise")
    )
    lo = raw.groupby(writer, sort=True).min().to_numpy().reshape(len(owners), 5, 2)
    hi = raw.groupby(writer, sort=True).max().to_numpy().reshape(lo.shape)
    pairs = np.where(np.isfinite(traits)[:, :, None], lo, np.nan)
    if np.any(np.abs(hi - lo)[np.isfinite(pairs)] > 1e-9) or not np.allclose(
        (pairs[:, :, 0] + 8 - pairs[:, :, 1]) / 2, traits, equal_nan=True
    ):
        raise ValueError("Trait pairs differ from the original scored population")
    source = orig.read(orig.bound(orig.FROZEN / "receipt.json", orig.SOURCE))
    with np.load(
        orig.saved(orig.FROZEN, "vectors.npz", source), allow_pickle=False
    ) as f:
        vectors = f["envent"].astype(float)
    worry = orig.worry_values(frame, ids)
    names = [*names, "worry"]
    bounds = np.array(
        [
            [table["outputs"][name][trait]["interval"] for trait in orig.KEYS]
            for name in names
        ]
    )
    if bounds.shape != (29, 5, 2) or not np.isfinite(bounds).all():
        raise ValueError("Missing TP63 correlation interval")
    check()
    rot = []
    for j in range(200):
        check()
        rot.append(orig.heads(weights, "TP63", "rot", j))
    rng = np.random.default_rng(23)
    draws = rng.integers(0, len(owners), size=(2000, len(owners)), dtype=np.int32)
    rng = np.random.default_rng(23)
    orders = np.argsort(
        writer[None, :] + rng.random((50, len(writer))), axis=1, kind="stable"
    )
    dest = out / "TP81-inputs.npz"
    with dest.open("xb") as f:
        np.savez(
            f,
            x=vectors,
            w=weights,
            rot=np.array(rot),
            worry=worry,
            feeling=feeling,
            person=writer,
            pairs=pairs,
            names=np.array(names),
            traits=np.array(list(orig.KEYS)),
            bounds=bounds,
            draws=draws,
            orders=orders,
        )
    return {
        "pin": pin(dest),
        "sourceReceiptPin": table["sourceReceiptPin"],
        "TP63AggregatePin": pin(public),
    }
