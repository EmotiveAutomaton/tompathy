"""In-memory TMP3 adapter for ordered turns and the receiver's reciprocal ratings."""

import math
from collections import defaultdict
from types import SimpleNamespace

import numpy as np
from history import VectorCache, batches
from panels import (
    CONVERSATION,
    TAGS,
    TRAITS,
    UNPLEASANT,
    correlations,
    evaluate,
    project,
)

TRAIT_FIELDS = {
    "Openness": "open",
    "Extraversion": "extraversion",
    "Agreeableness": "agreeable",
    "Conscientiousness": "conscientious",
    "Neuroticism": "neurotic",
}


def turn_means(turns, frozen, check=lambda: None):
    """Private, one conversation of (speaker key, ordered turn text) pairs, no ratings needed."""
    grouped = defaultdict(list)
    for key, text in turns:
        grouped[key].append(text)
    speakers = (
        SimpleNamespace(conversation="one", speaker=k, turns=t, outcomes={})
        for k, t in grouped.items()
    )
    panels = speaker_vectors(speakers, frozen, check)
    return {k: (a / n, b / n) for k, [(a, b, n, _)] in panels.items()}


def speaker_vectors(speakers, frozen, check=lambda: None):
    cache = VectorCache(frozen)
    seen = set()
    panels = defaultdict(list)
    for row in speakers:
        key = row.conversation, row.speaker
        if key in seen or not all(isinstance(k, str) and k.strip() for k in key):
            raise ValueError("Duplicate or unidentified speaker in conversation")
        seen.add(key)
        if (
            isinstance(row.turns, str)
            or not row.turns
            or any(not isinstance(t, str) or not t.strip() for t in row.turns)
        ):
            raise ValueError("Expected ordered nonempty turns for one speaker")
        sa, sb = np.zeros(384), np.zeros(384)
        for batch in batches(row.turns):
            check()
            vectors = cache.get(batch)
            for t in batch:
                a, b = vectors[t]
                sa += a
                sb += b
        panels[row.speaker].append((sa, sb, len(row.turns), row.outcomes))
    return panels


def outcome_cohort(panels, field):
    owners, base, worry, values = [], [], [], []
    for speaker, meetings in sorted(panels.items()):
        present = [m for m in meetings if m[3].get(field) is not None]
        if not present:
            continue
        ratings = [m[3][field] for m in present]
        high = 9 if field in ("how_enjoyable", "affect") else 5
        if any(
            isinstance(v, bool) or not math.isfinite(v) or not 1 <= v <= high
            for v in ratings
        ):
            raise ValueError("A receiver rating lies outside the agreed projection")
        owners.append(speaker)
        turns = sum(m[2] for m in present)
        base.append(sum(m[0] for m in present) / turns)
        worry.append(sum(m[1] for m in present) / turns)
        values.append(np.mean(ratings))
    return tuple(owners), np.asarray(base), np.asarray(worry), np.asarray(values)


def conversation(speakers, dest, frozen, check=lambda: None, observe=None):
    panels = speaker_vectors(speakers, frozen, check)
    names = frozen.names
    targets = {}
    for outcome in [
        "affect",
        "how_enjoyable",
        *[f"{r}_{TRAIT_FIELDS[t]}" for r in ("self", "partner") for t in TRAITS],
    ]:
        owners, base, worry, values = outcome_cohort(panels, outcome)
        if len(owners) >= 11:
            targets[outcome] = (owners, base, worry, values)

    def calculate(directions, output):
        for outcome, (owners, base, worry, y) in targets.items():
            z = project(base, worry, directions)
            if outcome in ("how_enjoyable", "affect"):
                wanted = [s for s in ("worry", *UNPLEASANT) if s in names]
                file = "conversation_affect.csv"
            else:
                wanted = TAGS
                file = "conversation_traits.csv"
            x = z[:, [names.index(name) for name in wanted]]
            c = correlations(
                x, np.broadcast_to(y[:, None], x.shape), output.kind == "trained"
            )
            for j, name in enumerate(wanted):
                if file == "conversation_traits.csv":
                    rater, field = outcome.split("_", 1)
                    trait = next(t for t, key in TRAIT_FIELDS.items() if key == field)
                    labels = [name, rater, trait]
                else:
                    labels = [name, outcome]
                output.add(file, labels, owners, c[:, j])

    if not targets:
        # Real frozen passes above still exercise the adapter on the two-person fixture.
        dest.mkdir(exist_ok=False)
        return {}
    return evaluate(frozen, calculate, dest, CONVERSATION, check, observe)
