"""Coactive comparisons, with process edits separated from content preferences."""

import numpy as np

from .backbone import Backbone, Choice

CONTENT_EDITS = {"wording", "add content", "remove content", "reorder", "tone"}


def classification(edit_type, changes_claim, *, labels_admitted=False):
    if not labels_admitted or edit_type == "unclear" or changes_claim == "unclear":
        return "unknown"
    if edit_type in {"typo", "grammar", "format"} or changes_claim == "no":
        return "process"
    return "preference" if edit_type in CONTENT_EDITS and changes_claim == "yes" else "unknown"


def fit_corrections(records, features, *, until, dimensions, labels):
    """Labels are admission-checked by the caller; no labels means no updates.

    Each correction constrains only its witnessed feature difference. Kappa is
    fixed at one for scale identification, as in the choice backbone.
    """
    rows = []
    counts = {"process": 0, "preference": 0, "unknown": 0}
    for record in records:
        if record.t >= until:
            continue
        label = labels.get(record.correction_id, {})
        kind = classification(
            label.get("Q8"), label.get("Q9"), labels_admitted=label.get("admitted", False)
        )
        counts[kind] += 1
        if kind != "preference":
            continue
        delta = np.asarray(features(record.after_ref)) - np.asarray(features(record.before_ref))
        if delta.shape != (dimensions,) or not np.isfinite(delta).all():
            raise ValueError("Invalid correction feature difference")
        rows.append(
            Choice(
                record.correction_id,
                record.maker_id,
                record.t,
                record.t,
                np.stack((np.zeros(dimensions), delta)),
                1,
            )
        )
    return Backbone.fit(rows, until=until, dimensions=dimensions), counts
