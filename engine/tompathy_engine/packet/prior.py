"""Borrow an explicitly admitted population prior without attributing own data."""

import math

import numpy as np

from ..ledger.ids import digest
from .drives import MAPPING
from .modules import support


def apply_prior(packet, pipeline, admissions, *, domain):
    if (
        not {"population-prior", "drive-recipes"} <= set(admissions.enabled(domain))
        or "Q10" not in pipeline.questions
    ):
        return []
    fit = pipeline.fits.get("joint", pipeline.fits.get("options", pipeline.fits.get("corrections")))
    if fit is None or len(fit.offsets) < 2:
        return []
    pipeline.labels.require("Q10")
    population = packet["population"]
    population["makersPooled"] = len(fit.offsets)
    population["description"] = (
        f"Borrowed {domain} population fit from {len(fit.offsets)} source-scoped makers. "
        "These priors use zero observations from this capture's maker. Intervals describe the fitted prior, not a personal finding."
    )
    eid = digest(["population-prior", fit.input_hash])
    packet["evidence"].append(
        {
            "id": eid,
            "source": "ledger:population:" + fit.input_hash,
            "excerpt": f"{len(fit.train_ids)} earlier comparisons; fit cutoff {fit.until.isoformat()}.",
            "capturedAt": fit.until.isoformat().replace("+00:00", "Z"),
            "relationship": "Aggregate borrowed population evidence; no own-maker observation",
        }
    )
    # The product MAP prior is isotropic at the fitted maker penalties. The
    # average prior variance is a declared population convention, not a new fit.
    variance = float(np.mean([1 / (2 * p) for p in fit.penalties.values()]))
    for maker in packet["makers"]:
        for key, (label, weights) in MAPPING.items():
            projection = np.array([weights.get(name, 0) for name in pipeline.features])
            if not np.any(projection):
                continue
            hid = digest(["borrowed-drive", fit.input_hash, maker["id"], key])
            prior = support(0.5, "Borrowed population midpoint; zero own-maker records")
            packet["hypotheses"].append(
                {
                    "id": hid,
                    "kind": "value",
                    "interpretation": "drive",
                    "icon": key,
                    "label": label,
                    "description": "Population prior only. This capture does not establish a personal drive loading. "
                    "The channel is an admitted mapping hypothesis, not a measurement of neural activity.",
                    "makers": [maker["id"]],
                    "regions": [],
                    "status": "hypothesis",
                    "evidence": [eid],
                    "support": prior,
                }
            )
            population["items"].append(
                {
                    "hypothesis": hid,
                    "populationSupport": prior,
                    "makerRecords": 0,
                    "shrinkage": 0.0,
                    "curve": [
                        {
                            "records": 0,
                            "intervalWidth": 3.92
                            * math.sqrt(variance)
                            * float(np.linalg.norm(projection)),
                        }
                    ],
                }
            )
    return [
        admissions.require(m, domain).admission_id for m in ("population-prior", "drive-recipes")
    ] + [pipeline.labels.require("Q10")]
