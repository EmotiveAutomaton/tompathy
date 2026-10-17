"""Deterministic surface descriptions, compared only with this page itself."""

import random
import re
from collections import Counter
from statistics import mean, pstdev

from ..ledger.ids import digest

WORDS = re.compile(r"\b[^\W\d_]+(?:['’][^\W\d_]+)*\b", re.UNICODE)
QUOTES = re.compile(r'“[^”]*”|"[^"\n]*"|‘[^’]*’', re.DOTALL)
CONNECTIVES = ("and", "but", "because", "however", "therefore", "although", "yet", "so")


def describe(capture, check=lambda: None):
    regions = capture["regions"]
    plain = "\n".join(r["anchor"]["exact"] for r in regions)
    quoted = " ".join(m.group() for m in QUOTES.finditer(plain))
    unquoted = QUOTES.sub(lambda m: " " * len(m.group()), plain)
    words = WORDS.findall(unquoted.lower())
    counts = Counter(words)
    # Fixed page-derived seed: reproducible controls, not an external population.
    rng = random.Random(digest(["habits-v1", unquoted]))
    out = []
    for size in (3, 4, 5):
        check()
        observed = Counter(tuple(words[i:i + size]) for i in range(len(words) - size + 1))
        repeated = {phrase: count for phrase, count in observed.items() if count > 1}
        expected = Counter()
        for _ in range(12):
            check()
            shuffled = words.copy()
            rng.shuffle(shuffled)
            baseline = Counter(tuple(shuffled[i:i + size]) for i in range(len(shuffled) - size + 1))
            expected.update({phrase: baseline[phrase] for phrase in repeated})
        for phrase, count in repeated.items():
            baseline = expected[phrase] / 12
            if count > baseline:
                out.append({"label": " ".join(phrase), "count": count, "baseline": baseline})
    out.sort(key=lambda r: (-(r["count"] - r["baseline"]), -len(r["label"]), r["label"]))
    # Nested phrases describe one recurring expression; don't fill the panel with it.
    chosen = []
    for item in out:
        if not any(item["label"] in old["label"] for old in chosen):
            chosen.append(item)
        if len(chosen) == 8:
            break
    sentences = [WORDS.findall(s) for s in re.split(r"[.!?]+(?:\s+|$)", unquoted)]
    lengths = [len(s) for s in sentences if s]
    return {
        "repeats": chosen, "words": len(words), "quotedWords": len(WORDS.findall(quoted)),
        "sentenceCount": len(lengths), "sentenceMean": mean(lengths) if lengths else 0,
        "sentenceSpread": pstdev(lengths) if lengths else 0,
        "connectives": {w: counts[w] for w in CONNECTIVES if counts[w]},
        "punctuation": {p: unquoted.count(p) for p in (",", ";", ":", "—", "?", "!") if p in unquoted},
    }
