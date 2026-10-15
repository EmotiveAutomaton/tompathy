"""Display admitted, conditional feature preferences from observed alternatives.

Feature coefficients are not drive loadings. Menu position is a process control,
never a value. No scientific admission is supplied by this mapping or its tests.
"""

import math
from datetime import datetime

from scipy.special import ndtr

from ..features.deterministic import option_features
from ..ledger.ids import digest

LABELS = {
    "characters": ("longer text", "shorter text"),
    "tokens": ("more words", "fewer words"),
    "word_overlap": (
        "more vocabulary shared with the draft",
        "less vocabulary shared with the draft",
    ),
    "trigram_overlap": (
        "more phrasing shared with the draft",
        "less phrasing shared with the draft",
    ),
}


def apply_preferences(packet, ledger, bundle, admissions, *, tier, domain):
    # An absent admission is an honest empty display. A supplied admitted model
    # with invalid pins is an error, not a silently accepted or repaired model.
    if bundle is None or tier == "T0" or "backbone-preferences" not in admissions.enabled(domain):
        return []
    admission = admissions.require("backbone-preferences", domain)
    bundle.verify(
        ledger,
        at=datetime.fromisoformat(packet["artifact"]["capturedAt"]),
        implementation=admissions.implementation,
    )
    if (
        bundle.domain != domain
        or bundle.task != "options"
        or domain not in {"writing", "preferences"}
    ):
        raise ValueError("Preference display needs an options model in the capture domain")
    names = list(option_features("", "", 0))
    if len(bundle.beta) != len(names):
        raise ValueError("Unsupported preference feature schema")
    decisions = {
        d.decision_id: d for d in ledger.rows("Decision") if d.decision_id in bundle.train_ids
    }
    population = {
        "populationId": bundle.population,
        "makersPooled": len(bundle.counts),
        "items": [],
        "description": "Pooled observed choices in the "
        + domain
        + " domain. Positions compare each maker with the pooled coefficient (0.5). "
        "Intervals and information shares are conditional Laplace approximations with the population coefficient fixed. "
        "These feature preferences are not calibrated values, drives, or authorship shares.",
    }
    emitted = False
    for maker in packet["makers"]:
        ident = maker["id"]
        if ident not in bundle.offsets:
            continue
        evidence = []
        own = sorted(
            (d for d in decisions.values() if d.maker_id == ident),
            key=lambda d: (d.t_resolve, d.decision_id),
        )
        # Summary witnesses refer to the exact source-scoped decision IDs; no
        # text is re-attributed to the currently open artifact.
        for decision in own[-8:]:
            eid = digest(["model-choice", decision.decision_id])
            packet["evidence"].append(
                {
                    "id": eid,
                    "source": "ledger:decision:" + decision.decision_id,
                    "excerpt": f"Observed {decision.action}; selected option {decision.taken} among {len(decision.options)} offered alternatives.",
                    "capturedAt": decision.t_resolve.isoformat().replace("+00:00", "Z"),
                    "relationship": "Witnessed choice used in the pinned model; acceptance does not establish endorsement",
                }
            )
            evidence.append(eid)
        for index, name in enumerate(names):
            if name not in LABELS:
                continue
            low, high = bundle.conditional_intervals[ident][index]
            if low <= 0 <= high:
                continue
            offset = bundle.offsets[ident][index]
            se = (high - low) / 3.92
            if se <= 0:
                raise ValueError("Degenerate conditional interval")
            positive = offset > 0
            value = float(ndtr(offset / se))
            hid = digest(["preference", bundle.input_hash, ident, name])
            meaning = "Probability-like relative position above the pooled coefficient; conditional Gaussian approximation, not calibrated against stated values."
            packet["hypotheses"].append(
                {
                    "id": hid,
                    "kind": "value",
                    "interpretation": "preference",
                    "icon": "value",
                    "label": "Choice tendency: " + LABELS[name][0 if positive else 1],
                    "description": f"Observed alternatives support a conditional tendency toward {LABELS[name][0 if positive else 1]} relative to this population. "
                    f"Coefficient difference {offset:.5g}; conditional 95% interval [{low:.5g}, {high:.5g}]. Other measured features are held fixed. "
                    "This limited comparison does not identify a broader motive or value. Reference and observed widths use the same fitted pooling penalty.",
                    "makers": [ident],
                    "regions": [],
                    "status": "hypothesis",
                    "support": {
                        "value": value,
                        "scale": [0, 1],
                        "semantics": "relative",
                        "meaning": meaning,
                    },
                    "evidence": evidence,
                }
            )
            population["items"].append(
                {
                    "hypothesis": hid,
                    "populationSupport": {
                        "value": 0.5,
                        "scale": [0, 1],
                        "semantics": "relative",
                        "meaning": meaning,
                    },
                    "makerRecords": bundle.counts[ident],
                    "shrinkage": bundle.information_shares[ident],
                    "curve": [
                        {
                            "records": 0,
                            "intervalWidth": 3.92 / math.sqrt(2 * bundle.penalties[ident]),
                        },
                        {"records": bundle.counts[ident], "intervalWidth": high - low},
                    ],
                }
            )
            emitted = True
    if emitted:
        packet["population"] = population
        return [admission.admission_id]
    return []
