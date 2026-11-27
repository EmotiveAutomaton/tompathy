"""TP72 frozen coordinates and matched aggregate uncertainty. Runs inside the seal."""

import csv
from collections import defaultdict
from functools import lru_cache

import numpy as np
import registered as reg
from rapid_nulls import heads
from reader import Readers

TAGS = [
    "contact",
    "order",
    "status",
    "family",
    "approval",
    "curiosity",
    "tranquility",
    "competition",
    "savings",
    "indep",
    "food",
    "health",
    "power",
    "romance",
    "honor",
    "serenity",
    "idealism",
    "rest",
    "acceptance",
]
CHANNELS = [
    "SEEKING",
    "amusement",
    "wanting",
    "CARE",
    "SADNESS",
    "RAGE",
    "FEAR",
    "DISGUST",
    "SHAME",
]
TRAITS = [
    "Openness",
    "Extraversion",
    "Agreeableness",
    "Conscientiousness",
    "Neuroticism",
]
UNPLEASANT = ("SADNESS", "RAGE", "FEAR", "DISGUST", "SHAME")
GROUPS = {
    "curiosity_composite": ["curiosity"],
    "respect_composite": ["status", "approval", "power", "competition", "honor"],
    "connection_composite": ["family", "contact", "acceptance"],
    "order_savings_serenity": ["order", "savings", "serenity"],
}
KS = (5, 10, 20, 40)
SPLITS = ("date", "gap")
ARMS = ("tagsRaw", "tagsPartial")
NSETS = 200
ESTIMATE = [
    "n",
    "value",
    "lo",
    "hi",
    "isoN",
    "isoLo",
    "isoMedian",
    "isoHi",
    "isoPct",
    "rotN",
    "rotLo",
    "rotMedian",
    "rotHi",
    "rotPct",
    "verdict",
]
HISTORY = {
    "traits.csv",
    "contrast.csv",
    "channels.csv",
    "stability.csv",
    "fixed_profile.csv",
    "posts_needed.csv",
    "matching.csv",
    "growth.csv",
    "curve_check.csv",
}
CONVERSATION = {"conversation_affect.csv", "conversation_traits.csv"}
MAP_FLAGS = ["mapCell", "mapPass", "printCell", "printPass"]


def contracts(names):
    def categories(**kwargs):
        return {k: list(map(str, v)) for k, v in kwargs.items()}

    readings = [*TAGS, *CHANNELS, "PRIDE", "worry", *GROUPS]
    curve = categories(split=SPLITS, arm=ARMS, k=KS, tag=[*TAGS, "mean"])
    match = categories(split=SPLITS, arm=ARMS, k=KS, cut=[1, 10])
    options = {
        "traits.csv": categories(reading=readings, trait=TRAITS),
        "contrast.csv": categories(stat=["diagonalMinusOther"]),
        "channels.csv": categories(channel=["amusement", "SEEKING"]),
        "stability.csv": curve,
        "fixed_profile.csv": curve,
        "posts_needed.csv": categories(
            split=SPLITS, arm=ARMS, target=[0.5, 0.8], tag=TAGS
        ),
        "matching.csv": {**match, "stat": ["baseline", "plus", "step"]},
        "growth.csv": match,
        "curve_check.csv": categories(split=SPLITS, arm=ARMS, k=KS),
        "conversation_affect.csv": categories(
            reading=["worry", *UNPLEASANT], outcome=["affect", "how_enjoyable"]
        ),
        "conversation_traits.csv": categories(
            reading=TAGS, rater=["self", "partner"], trait=TRAITS
        ),
    }
    result = {}
    for name in sorted(names):
        labels = options[name]
        extra = (
            MAP_FLAGS
            if name == "traits.csv"
            else ["positiveLeaders", "mapPass", "printPass"]
            if name == "contrast.csv"
            else []
        )
        result[name] = [
            [*labels, *ESTIMATE, *extra],
            [["lo", "hi"], ["isoLo", "isoHi"], ["rotLo", "rotHi"]],
            {**labels, "verdict": ["below", "within", "above", "partial"]},
        ]
    return result


@lru_cache(maxsize=2)
def weights(n):
    return np.vstack((np.ones(n), reg.resamples(n)))


def correlations(x, y, trained):
    if trained:
        # Limiting the batch size bounds scratch space for the 2,000 writer draws.
        return np.vstack(
            [reg.correlations(x, y, w) for w in np.array_split(weights(len(x)), 32)]
        )
    a, b = x - x.mean(0), y - y.mean(0)
    den = np.sqrt((a * a).sum(0) * (b * b).sum(0))
    return np.divide(
        (a * b).sum(0), den, out=np.full(den.shape, np.nan), where=den > 0
    )[None, :]


class Frozen:
    def __init__(self):
        self.reader = Readers()
        r = self.reader
        ix = np.arange(len(CHANNELS))[r.channel["active"]]
        selected = np.asarray(ix, dtype=int)
        self.names = [*TAGS, *[CHANNELS[i] for i in selected], "PRIDE", "worry"]
        self.base_heads = np.vstack(
            (r.tags["weights"], r.channel["parameters"][:-1].T, r.pride[:-1])
        )
        self.worry_head = np.asarray(r.worry_head["weights"]).reshape(1, -1)
        if self.base_heads.shape != (
            len(self.names) - 1,
            384,
        ) or self.worry_head.shape != (1, 384):
            raise ValueError("Frozen head/encoder binding differs")

    def encode(self, texts):
        a, b = self.reader.base.encode(texts), self.reader.worry.encode(texts)
        if (
            a.shape != (len(texts), 384)
            or b.shape != a.shape
            or not (np.isfinite(a).all() and np.isfinite(b).all())
        ):
            raise ValueError("Invalid paired frozen vectors")
        return a, b

    def directions(self, kind, index):
        if kind == "trained":
            return self.base_heads, self.worry_head
        return (
            heads(self.base_heads, "TP72:base", kind, index),
            heads(self.worry_head, "TP72:worry", kind, index),
        )


def project(base, worry, directions):
    a, b = directions
    return np.column_stack((base @ a.T, worry @ b.T))


class Results:
    """Rows join by statistic, ordered cohort and original set index before release."""

    def __init__(self, names, observe=None):
        self.contract = contracts(names)
        self.trained = {}
        self.controls = {}
        self.observe = observe
        self.kind = "trained"
        self.index = -1

    def add(self, filename, labels, owners, estimates, flags=()):
        if len(owners) < 11:
            return
        key = (filename, tuple(map(str, labels)))
        v = np.asarray(estimates).reshape(-1)
        if self.kind == "trained":
            draws = v[1:][np.isfinite(v[1:])]
            if len(draws) == 0 or not np.isfinite(v[0]):
                return
            if key in self.trained or len(set(owners)) != len(owners):
                raise ValueError("Ambiguous trained cell or person roster")
            self.trained[key] = (
                owners,
                float(v[0]),
                *np.quantile(draws, [0.025, 0.975]),
                tuple(flags),
            )
            self.controls[key] = np.full((2, NSETS), np.nan)
        elif key in self.trained:
            if self.trained[key][0] != owners:
                raise ValueError("Random-head cohort differs from the trained cell")
            self.controls[key][int(self.kind == "rot"), self.index] = v[0]

    def write(self, dest):
        dest.mkdir(exist_ok=False)
        by_file = defaultdict(list)
        for key, (owners, point, low, high, flags) in self.trained.items():
            name, labels = key
            bands = []
            for samples in self.controls[key]:
                valid = samples[np.isfinite(samples)]
                if not len(valid):
                    break
                q = np.quantile(valid, [0.025, 0.5, 0.975])
                pct = (
                    100
                    * ((valid < point).sum() + 0.5 * (valid == point).sum())
                    / len(valid)
                )
                bands.extend([len(valid), *q, pct])
            if len(bands) != 10:
                continue
            verdict = (
                "partial"
                if min(bands[0], bands[5]) < NSETS
                else (
                    "above"
                    if point > bands[8]
                    else "below"
                    if point < bands[6]
                    else "within"
                )
            )
            if self.observe is not None:
                self.observe(name, labels, frozenset(owners))
            numbers = [point, low, high, *bands]
            by_file[name].append(
                [
                    *labels,
                    len(owners),
                    *(format(x, ".7g") for x in numbers),
                    verdict,
                    *flags,
                ]
            )
        for name, rows in by_file.items():
            with (dest / name).open("x", encoding="utf8", newline="") as f:
                writer = csv.writer(f, lineterminator="\n")
                writer.writerow(self.contract[name][0])
                writer.writerows(rows)
        return {name: len(rows) for name, rows in by_file.items()}


def evaluate(frozen, calculate, dest, names, check=lambda: None, observe=None):
    result = Results(names, observe)
    for kind, numbers in (
        ("trained", [0]),
        ("iso", range(NSETS)),
        ("rot", range(NSETS)),
    ):
        for i in numbers:
            check()
            result.kind, result.index = kind, i
            calculate(frozen.directions(kind, i), result)
    return result.write(dest)
