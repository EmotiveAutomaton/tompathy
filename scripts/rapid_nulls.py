"""Registered R37 ISO and ROT sets. Every index can be regenerated independently."""

import hashlib

import numpy as np


def heads(weights, card, kind, number):
    w = np.asarray(weights, dtype=np.float64)
    if (
        w.ndim != 2
        or not np.isfinite(w).all()
        or np.any(np.linalg.norm(w, axis=1) == 0)
    ):
        raise ValueError("Drop constant or invalid heads before generating nulls")
    seed = int.from_bytes(
        hashlib.sha256(f"{card}:{kind}:{number}".encode()).digest()[:8], "big"
    )
    rng = np.random.default_rng(seed)
    if kind == "iso":
        x = rng.normal(size=w.shape)
        return x / np.linalg.norm(x, axis=1, keepdims=True)
    if kind != "rot":
        raise ValueError("Unknown null family")
    # Preserve the exact registered seeded square QR, including its sign convention.
    q, r = np.linalg.qr(rng.normal(size=(w.shape[1], w.shape[1])))
    return w @ (q * np.sign(np.diag(r)))
