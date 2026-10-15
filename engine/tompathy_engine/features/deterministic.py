"""Text features describe text. They are never direct maker-value evidence."""

import re
from difflib import SequenceMatcher

import numpy as np


def _words(text):
    return set(re.findall(r"\w+", text.casefold()))


def _ngrams(text, n=3):
    return {text[i : i + n].casefold() for i in range(max(0, len(text) - n + 1))}


def overlap(text, context, extractor=_words):
    a, b = extractor(text), extractor(context)
    return len(a & b) / max(1, len(a))


def option_features(text, context, position):
    return {
        "characters": float(len(text)),
        "tokens": float(len(text.split())),
        "position": float(position),
        "word_overlap": overlap(text, context),
        "trigram_overlap": overlap(text, context, _ngrams),
    }


def edit_features(before, after):
    operations = [
        o
        for o in SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
        if o[0] != "equal"
    ]
    return {
        "insertions": sum(d - c for tag, a, b, c, d in operations if tag in ("insert", "replace")),
        "deletions": sum(b - a for tag, a, b, c, d in operations if tag in ("delete", "replace")),
        "replacements": sum(tag == "replace" for tag, *_ in operations),
        "changed_blocks": len(operations),
    }


def cosine(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Embedding shapes or values differ")
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denom) if denom else 0.0
