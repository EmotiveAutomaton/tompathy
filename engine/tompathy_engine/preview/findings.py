"""Aggregate claim wording comes from the pinned receiving snapshot."""
from copy import deepcopy

from .claims import load_snapshot


def findings():
    return deepcopy(load_snapshot()["globalFindings"])
