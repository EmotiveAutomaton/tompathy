"""TP45 paired halves, fixed-forecast matching and growth on author coordinates."""

import numpy as np
import registered as reg
from panels import ARMS, KS, SPLITS, TAGS, correlations, weights


def standardize(v):
    sd = v.std(0)
    return np.divide(v - v.mean(0), sd, out=np.zeros_like(v), where=sd > 0)


def match_block(x, y, test):
    a, b = standardize(x), standardize(y)
    r = np.clip(np.nan_to_num(correlations(a[~test], b[~test], False)[0]), 0, 0.95)
    a, b = a[test], b[test]
    q = r * r / (2 * (1 - r * r))
    return (
        (a * (r / (1 - r * r))) @ b.T - ((a * a) @ q)[:, None] - ((b * b) @ q)[None, :]
    )


class Frame:
    def __init__(self, owners, fold, style, raw, cleared):
        self.owners, self.fold, self.style = owners, fold, style
        self.raw, self.cleared = raw, cleared
        self.lookup = {a: i for i, a in enumerate(owners)}
        self.subsets = {}
        self.base = []
        if style is not None and min(np.bincount(fold, minlength=2)) >= 2:
            for side in (0, 1):
                mask = fold == side
                scores = match_block(style[:, 0], style[:, 1], mask)
                self.base.append((mask, scores, reg.ranks(scores)))

    def subset(self, ids):
        if ids == self.owners:
            return self
        if ids not in self.subsets:
            ix = [self.lookup[a] for a in ids]
            self.subsets[ids] = Frame(
                ids,
                self.fold[ix],
                self.style[ix] if self.style is not None else None,
                self.raw[ix],
                self.cleared[ix] if self.cleared is not None else None,
            )
        return self.subsets[ids]

    def scores(self, arm, heads):
        source = self.raw if arm == "tagsRaw" else self.cleared
        if source is None:
            return None
        v = source @ heads.T
        return v[:, 0], v[:, 1]

    def ranks(self, x, y):
        if not self.base:
            return None
        original, added = np.empty(len(x), dtype=int), np.empty(len(x), dtype=int)
        for mask, scores, fixed in self.base:
            original[mask] = fixed
            added[mask] = reg.ranks(scores + match_block(x, y, mask))
        return original, added


def average(values, trained):
    if trained:
        return weights(len(values)) @ values / len(values)
    return np.array([values.mean()])


def by_tag(output, file, labels, owners, c):
    for j, tag in enumerate(TAGS):
        output.add(file, [*labels, tag], owners, c[:, j])
    output.add(file, [*labels, "mean"], owners, c.mean(1))


def learning(frames, heads, output):
    trained = output.kind == "trained"
    for split in SPLITS:
        for arm in ARMS:
            baselines = {}
            paired = {}

            def measure(frame, paired=paired, arm=arm):
                if id(frame) not in paired:
                    x, y = frame.scores(arm, heads)
                    paired[id(frame)] = correlations(x, y, trained), frame.ranks(x, y)
                return paired[id(frame)]

            for k in KS:
                frame = frames.get((split, k))
                if frame is None or (arm == "tagsPartial" and frame.cleared is None):
                    continue
                owners = frame.owners
                c, ranks = measure(frame)
                by_tag(output, "stability.csv", [split, arm, k], owners, c)
                if k == 5:
                    for target in (0.5, 0.8):
                        p = reg.posts_needed(c, target)
                        for j, tag in enumerate(TAGS):
                            output.add(
                                "posts_needed.csv",
                                [split, arm, target, tag],
                                owners,
                                p[:, j],
                            )
                    for k2 in KS:
                        by_tag(
                            output,
                            "fixed_profile.csv",
                            [split, arm, k2],
                            owners,
                            reg.fixed_profile(c, k2),
                        )
                if ranks is None:
                    continue
                base, plus = ranks
                baselines[k] = {}
                for cut, endpoint in ((1, "firstOne"), (10, "firstTen")):
                    raw, added = (
                        (base <= cut).astype(float),
                        (plus <= cut).astype(float),
                    )
                    baselines[k][endpoint] = raw.mean()
                    for stat, vals in (
                        ("baseline", raw),
                        ("plus", added),
                        ("step", added - raw),
                    ):
                        output.add(
                            "matching.csv",
                            [split, arm, k, cut, stat],
                            owners,
                            average(vals, trained),
                        )
            if 5 not in baselines:
                continue
            endpoint, kmax = reg.choose_endpoint(baselines, sorted(baselines))
            for k in sorted({max(baselines), kmax or 5}):
                lo, hi = frames[split, 5], frames[split, k]
                ids = tuple(a for a in lo.owners if a in hi.lookup)
                if len(ids) < 11:
                    continue
                ca, ra = measure(lo.subset(ids))
                cb, rb = measure(hi.subset(ids))
                if k == max(baselines):
                    output.add(
                        "curve_check.csv",
                        [split, arm, k],
                        ids,
                        (cb - reg.fixed_profile(ca, k)).mean(1),
                    )
                if k == kmax and ra is not None and rb is not None:
                    cut = 10 if endpoint == "firstTen" else 1

                    def step(r, cut=cut):
                        return (r[1] <= cut).astype(float) - (r[0] <= cut).astype(float)

                    output.add(
                        "growth.csv",
                        [split, arm, k, cut],
                        ids,
                        average(step(rb) - step(ra), trained),
                    )
