"""Consume the receiving archive projection and form means before rotating any head."""

import datetime
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from functools import lru_cache

import numpy as np
import registered
from legacy_helpers import FORMS, community, rows, style
from panels import HISTORY, KS, SPLITS, TRAITS, evaluate
from reader import ROOT


def string_list(path, normalize):
    items = json.loads(path.read_bytes())
    if not isinstance(items, list) or any(
        not isinstance(t, str) or not normalize(t) for t in items
    ):
        raise ValueError("Invalid receiver exclusions")
    return {normalize(t) for t in items}


def eligible_rows(source, profiles, excluded, dropped):
    for row in rows(
        source / "comments.csv", ["author", "id", "day", "community", "text"]
    ):
        author, ident = row["author"], row["id"]
        group = community(row["community"])
        if not group or not ident.strip() or not author.strip():
            raise ValueError("Missing projected source key")
        if author not in profiles or group in excluded or ident in dropped:
            continue
        text = html.unescape(re.sub("<[^>]*>", " ", row["text"])).strip()
        if not text:
            continue
        day = datetime.date.fromisoformat(row["day"]).isoformat()
        first = ""
        words = text.split()
        if len(words) >= 30:
            prefix = " ".join(words[:150])
            end = list(re.finditer(r"""[.!?]+["'”’)]*(?=\s|$)""", prefix))
            if end:
                first = prefix[: end[-1].end()]
        yield author, ident, day, text, first


def batches(items, size=16):
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


class VectorCache:
    def __init__(self, model):
        self.model = model
        self.cache = {}

    def get(self, texts):
        unique = list(dict.fromkeys(texts))
        fresh = [s for s in unique if s not in self.cache]
        answer = {s: self.cache[s] for s in unique if s in self.cache}
        for batch in batches(fresh):
            a, b = self.model.encode(batch)
            answer.update(zip(batch, zip(a, b), strict=True))
        if len(self.cache) + len(fresh) > 512:
            self.cache.clear()
        self.cache.update(answer)
        return answer


def prepare(source, frozen, excluded, dropped, check):
    traits = {}
    for row in rows(source / "traits.csv", ["author", *TRAITS]):
        author = row["author"]
        values = np.asarray([float(row[t]) for t in TRAITS])
        if not author.strip() or author in traits or not np.isfinite(values).all():
            raise ValueError("Invalid projected trait row")
        traits[author] = values
    counts = Counter()
    openings = defaultdict(list)
    seen = set()

    def records():
        return eligible_rows(source, traits, excluded, dropped)

    for i, (a, key, day, _, first) in enumerate(records()):
        if i % 2048 == 0:
            check()
        if key in seen:
            raise ValueError("Duplicate retained comment")
        seen.add(key)
        counts[a] += 1
        if first:
            openings[a].append((day, key))
    del seen
    deep = {a for a in openings if counts[a] >= 80}
    outside = set(openings) - deep
    forms = json.loads((ROOT / "style.json").read_bytes())
    vocabulary = Counter()
    if outside:
        for i, (a, _, _, _, first) in enumerate(records()):
            if i % 2048 == 0:
                check()
            if a in outside and first:
                vocabulary.update(FORMS.findall(first.casefold()))
    topics = sorted(vocabulary.keys() - set(forms), key=lambda w: (-vocabulary[w], w))[
        :300
    ]
    topics.extend([""] * (300 - len(topics)))
    vocabulary.clear()

    @lru_cache(maxsize=256)
    def style_row(text):
        return np.asarray(style(text, forms, topics))

    # Per-post indices control both halves. Only author summaries persist after encoding.
    assignments = defaultdict(list)
    frames = defaultdict(dict)
    for a in sorted(
        deep, key=lambda a: hashlib.sha256(("TP39:fold:" + a).encode()).digest()
    ):
        days, keys = zip(*openings[a])
        for split in SPLITS:
            halves = registered.nested_indices(days, keys, split == "gap")
            for k in KS:
                if min(map(len, halves)) < k:
                    continue
                frames[split, k][a] = np.zeros((2, 742))
                for side, order in enumerate(halves):
                    for j in order[:k]:
                        assignments[keys[j]].append((split, k, side))
    owners = tuple(sorted(counts))
    full = {a: np.zeros(768) for a in owners}
    sums = {a: np.zeros(742) for a in openings}
    gram = np.zeros((358, 358))
    cross = np.zeros((358, 384))
    cache = VectorCache(frozen)
    for batch in batches(records()):
        check()
        vectors = cache.get(
            [t for _, _, _, text, first in batch for t in (text, first) if t]
        )
        ox, oy = [], []
        for a, key, _, text, first in batch:
            base, worry = vectors[text]
            full[a][:384] += base
            full[a][384:] += worry
            if not first:
                continue
            x, y = style_row(first), vectors[first][0]
            z = np.r_[x, y]
            sums[a] += z
            for split, k, side in assignments.get(key, ()):
                frames[split, k][a][side] += z / k
            if a in outside:
                ox.append(x)
                oy.append(y)
        if ox:
            x = np.stack(ox)
            gram += x.T @ x
            cross += x.T @ np.asarray(oy, dtype=float)
    totals = sum(sums.values(), np.zeros(742))
    n_open = sum(map(len, openings.values()))
    outside_mean = {}
    for a in openings:
        n = len(openings[a])
        if n_open > n:
            outside_mean[a] = (totals - sums[a]) / (n_open - n)
    n_train = sum(len(openings[a]) for a in outside)
    sx, sy = np.zeros(358), np.zeros(384)
    for a in sorted(outside):
        if a not in outside_mean:
            continue
        n = len(openings[a])
        mx, my = np.split(outside_mean[a], [358])
        ax, ay = np.split(sums[a], [358])
        sx += ax - n * mx
        sy += ay - n * my
        gram += n * np.outer(mx, mx) - np.outer(ax, mx) - np.outer(mx, ax)
        cross += n * np.outer(mx, my) - np.outer(ax, my) - np.outer(mx, ay)
    coef = None
    if n_train and len(deep) >= 11:
        gram -= np.outer(sx, sx) / n_train
        cross -= np.outer(sx, sy) / n_train
        scale = np.sqrt(np.maximum(gram.diagonal() / n_train, 0))
        scale[scale == 0] = 1
        coef = np.linalg.solve(
            gram / np.outer(scale, scale) + np.eye(358), cross / scale[:, None]
        )
    from curves import Frame

    result = {}
    fold = {
        a: i % 2
        for i, a in enumerate(
            sorted(
                deep, key=lambda a: hashlib.sha256(("TP39:fold:" + a).encode()).digest()
            )
        )
    }
    for key, data in frames.items():
        if len(data) < 11:
            continue
        ids = tuple(data)
        z = np.stack([data[a] - outside_mean[a] for a in ids])
        x, y = z[:, :, :358], z[:, :, 358:]
        cleared = (
            y - ((x - sx / n_train) / scale @ coef + sy / n_train)
            if coef is not None
            else None
        )
        result[key] = Frame(
            ids,
            np.array([fold[a] for a in ids]),
            x if coef is not None else None,
            y,
            cleared,
        )
    if not owners:
        return owners, np.empty((0, 768)), np.empty((0, 5)), result
    means = np.stack([full[a] / counts[a] for a in owners])
    return owners, means, np.stack([traits[a] for a in owners]), result


def history(
    source,
    dest,
    frozen,
    check=lambda: None,
    observe=None,
    *,
    excluded=None,
    dropped=None,
):
    # Both lists are receiver-computed. Empty is a legitimate measured list.
    if excluded is None:
        excluded = string_list(source / "excluded_communities.json", community)
    if dropped is None:
        dropped = string_list(source / "dropped_comments.json", str.strip)
    excluded = set(map(community, excluded))
    dropped = set(dropped)
    from curves import learning
    from traits import table

    owners, means, targets, frames = prepare(source, frozen, excluded, dropped, check)

    def calculate(directions, result):
        table(
            owners,
            means[:, :384],
            means[:, 384:],
            targets,
            frozen.names,
            directions,
            result,
        )
        learning(frames, directions[0][:19], result)

    return evaluate(frozen, calculate, dest, HISTORY, check, observe)
