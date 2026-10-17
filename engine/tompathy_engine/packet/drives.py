"""Admitted revealed-theme projections; final text cannot move these estimates.

The v0 mapping is an explicit hypothesis tested as drive-recipes. SEEKING is
reserved for separately identified pursuit vigor, never copied from topic tags.
"""

import math

import numpy as np
from scipy.special import ndtr

from ..ledger.ids import digest
from .modules import support

MAPPING = {
    "fear": ("FEAR", {"Q10:danger": 1.0}),
    "care": ("CARE", {"Q10:care": 1.0}),
    "play": ("PLAY", {"Q10:play or humor": 1.0}),
    "rage": ("RAGE", {"Q10:conflict": 1.0}),
    "panic-grief": ("Belonging", {"Q10:loss or separation": 1.0}),
    "lust": ("LUST", {"Q10:desire": 1.0}),
}


def apply_drives(packet, pipeline, fit, admissions, *, tier, domain):
    if (
        tier == "T0"
        or "drive-recipes" not in admissions.enabled(domain)
        or "Q10" not in pipeline.questions
        or not fit.conditional_covariances
    ):
        return []
    pipeline.labels.require("Q10")
    population = packet.get("population")
    if not population:
        return []
    emitted = False
    for maker in packet["makers"]:
        ident = maker["id"]
        if ident not in fit.offsets:
            continue
        evidence = sorted(
            {
                e
                for h in packet["hypotheses"]
                if h["kind"] == "value" and h["makers"] == [ident]
                for e in h["evidence"]
            }
        )
        if not evidence:
            continue
        offset = np.array(fit.offsets[ident])
        covariance = np.array(fit.conditional_covariances[ident])
        strong = []

        def emit(
            key,
            label,
            projection,
            kind,
            description,
            *,
            ident=ident,
            offset=offset,
            covariance=covariance,
            evidence=evidence,
        ):
            nonlocal emitted
            mean = float(projection @ offset)
            variance = float(projection @ covariance @ projection)
            if variance <= 0:
                return None
            se = math.sqrt(variance)
            hid = digest(["drive-recipe", fit.input_hash, ident, key])
            packet["hypotheses"].append(
                {
                    "id": hid,
                    "kind": "value",
                    "interpretation": kind,
                    "valueCategory": "drive" if kind == "drive" else "constructed",
                    "icon": key if kind == "drive" else "value",
                    "label": label,
                    "description": description + f" Conditional contrast {mean:.4g}, 95% interval "
                    f"[{mean - 1.96 * se:.4g}, {mean + 1.96 * se:.4g}]. "
                    "This is a revealed-theme mapping hypothesis; it does not measure neural activity or a private motive.",
                    "makers": [ident],
                    "regions": [],
                    "status": "hypothesis",
                    "evidence": evidence[-16:],
                    "preferenceEstimate": {
                        "quantity": "Revealed-theme contrast from population",
                        "value": mean,
                        "reference": 0.0,
                        "interval": {
                            "lower": mean - 1.96 * se,
                            "upper": mean + 1.96 * se,
                            "level": 0.95,
                            "method": "Conditional Gaussian projection using the full fitted covariance",
                        },
                        "basis": "Scoped revealed-theme mapping from observed choices and corrections. This does not measure neural activity, a private motive or a lifetime set point.",
                    },
                    "support": support(
                        ndtr(mean / se),
                        "Direction confidence: conditional Gaussian sign probability above the population; uncalibrated drive mapping",
                    ),
                }
            )
            population["items"].append(
                {
                    "hypothesis": hid,
                    "populationSupport": support(
                        0.5, "Pooled reference on the same relative scale"
                    ),
                    "makerRecords": fit.counts[ident],
                    "shrinkage": max(
                        0.0,
                        min(
                            1.0,
                            1
                            - variance * 2 * fit.penalties[ident] / float(projection @ projection),
                        ),
                    ),
                    "curve": [
                        {
                            "records": 0,
                            "intervalWidth": 3.92
                            * float(np.linalg.norm(projection))
                            / math.sqrt(2 * fit.penalties[ident]),
                        },
                        {"records": fit.counts[ident], "intervalWidth": 3.92 * se},
                    ],
                }
            )
            emitted = True
            packet["schemaVersion"] = "1.8"
            return mean - 1.96 * se

        for key, (label, weights) in MAPPING.items():
            projection = np.array([weights.get(name, 0.0) for name in pipeline.features])
            lower = emit(
                key,
                label,
                projection,
                "drive",
                "Conditional themed choices and content corrections support this drive-channel hypothesis.",
            )
            if lower is not None and lower > 0:
                strong.append((lower, key, label, projection))
        # A sparse descriptive recipe attaches to already supported directions.
        # Its interval uses covariance; correlated tags are never independent votes.
        if len(strong) >= 2:
            pair = sorted(strong, key=lambda x: (-x[0], x[1]))[:2]
            projection = (pair[0][3] + pair[1][3]) / 2
            emit(
                "recipe:" + pair[0][1] + "+" + pair[1][1],
                pair[0][2] + " and " + pair[1][2] + " preference recipe",
                projection,
                "value",
                "Sparse recipe hypothesis with equal weights on two supported revealed-theme directions. "
                "The recipe label is descriptive; its psychological interpretation requires the scoped admission.",
            )
    return [admissions.require("drive-recipes", domain).admission_id] if emitted else []
