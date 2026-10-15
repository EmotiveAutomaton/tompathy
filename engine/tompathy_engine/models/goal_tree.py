"""Cover witnessed leaves before choosing a governing goal; roots are fallible cues."""

from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class GoalCandidate:
    id: str
    leaves: frozenset[str]
    depth: int
    support: float
    cue_match: float = 0.0


def governing_cover(leaves, candidates, *, root_reliability=0.0):
    leaves = frozenset(leaves)
    candidates = sorted(candidates, key=lambda c: c.id)
    if (
        not leaves
        or len({c.id for c in candidates}) != len(candidates)
        or not 0 <= root_reliability <= 1
    ):
        raise ValueError("Invalid governing-goal inputs")
    for c in candidates:
        if (
            not c.leaves
            or not c.leaves <= leaves
            or c.depth < 0
            or not 0 <= c.support <= 1
            or not 0 <= c.cue_match <= 1
        ):
            raise ValueError("Invalid candidate coverage or relative support")

    def score(c):
        return (1 - root_reliability) * c.support + root_reliability * c.cue_match

    whole = [c for c in candidates if c.leaves == leaves]
    if whole:
        # Depth is distance above leaves. A generic higher root cannot defeat a
        # lower complete cover merely because its title sounds convincing.
        best_depth = min(c.depth for c in whole)
        best = sorted((c for c in whole if c.depth == best_depth), key=lambda c: (-score(c), c.id))
        top = score(best[0])
        return {
            "governing": [best[0].id],
            "equivalent": [c.id for c in best if abs(score(c) - top) < 1e-12],
            "relative_support": top,
            "status": "hypothesis",
        }
    if len(candidates) > 20:
        raise ValueError("Exact parallel-cover search is limited to 20 candidates")
    for size in range(1, len(candidates) + 1):
        covers = [
            group
            for group in combinations(candidates, size)
            if frozenset().union(*(c.leaves for c in group)) == leaves
        ]
        if covers:
            group = min(
                covers,
                key=lambda g: (
                    max(c.depth for c in g),
                    -sum(score(c) for c in g),
                    tuple(c.id for c in g),
                ),
            )
            return {
                "governing": [c.id for c in group],
                "equivalent": [],
                "relative_support": sum(score(c) for c in group) / size,
                "status": "hypothesis",
            }
    return {"governing": [], "equivalent": [], "relative_support": None, "status": "unknown"}
