"""Chronological module comparisons, using the product's exact feature/model code.

Outputs are per-decision proper scores. Error control, scientific stopping and
promotion remain owned by Sounding Line; nothing here creates an admission.
"""

import time

import numpy as np

from ..admission import implementation_hash
from ..ledger.ids import digest
from ..ledger.schema import schema_hash
from ..models.backbone import Backbone
from ..models.bundle import input_hash
from ..models.pipeline import cases, feature_names


def evaluate(
    ledger,
    *,
    domain,
    until,
    labels=None,
    extra_features=None,
    questions=(),
    modules=("population", "backbone", "corrections", "joint"),
    task="options",
    heldout_makers=(),
    heldout_prompts=(),
    maximum_targets=1000,
    progress=None,
    cancel=lambda: False,
):
    allowed = {
        "uniform",
        "population",
        "backbone",
        "corrections",
        "joint",
        "prototypes",
        "diagnosticity",
        "correction-augmented",
    }
    if not modules or not set(modules) <= allowed or task not in {"options", "corrections"}:
        raise ValueError("Unsupported evaluation task/module")
    view = ledger.snapshot()
    options, corrections, kinds, excluded = cases(
        view,
        domain=domain,
        until=until,
        labels=labels,
        questions=questions,
        extra_features=extra_features,
    )
    targets = options if task == "options" else corrections
    targets = sorted(
        (
            r
            for r in targets
            if (not heldout_makers or r.maker in heldout_makers)
            and (not heldout_prompts or r.prompt in heldout_prompts)
        ),
        key=lambda r: (r.opened, r.id),
    )
    if len(targets) > maximum_targets or maximum_targets < 1:
        raise ValueError(
            f"Evaluation has {len(targets)} targets; explicit limit is {maximum_targets}"
        )
    names = feature_names(questions) + (extra_features.names if extra_features else [])
    dimensions = len(names)
    output, start = [], time.monotonic()
    for index, target in enumerate(targets):
        if cancel():
            raise InterruptedError("Module evaluation cancelled")

        def past(rows, target=target):
            return [
                r
                for r in rows
                if r.resolved < target.opened
                and r.maker not in heldout_makers
                and r.prompt not in heldout_prompts
            ]

        choice_past, correction_past = past(options), past(corrections)
        inputs = {
            "population": choice_past,
            "backbone": choice_past,
            "corrections": correction_past,
            "joint": choice_past + correction_past,
            "uniform": [],
            "prototypes": choice_past,
            "diagnosticity": choice_past,
            "correction-augmented": choice_past + correction_past,
        }
        fitted = {}
        for module in modules:
            train = inputs[module]
            weighting = None
            if module == "diagnosticity":
                from ..models.diagnosticity import fit as fit_diagnosticity
                from ..models.pipeline import latency_z, weighted

                z = latency_z(view)
                eligible = [r for r in train if z.get(r.id) is not None]
                if len({r.maker for r in eligible}) >= 3:
                    weighting = fit_diagnosticity(
                        eligible, z, until=target.opened, utility_features=names
                    )
                    if weighting["control_passed"]:
                        train = weighted({"options": train}, view, weighting, names)["options"]
            if module == "correction-augmented":
                from scipy.special import softmax

                if "backbone" not in fitted:
                    fitted["backbone"] = Backbone.fit(
                        choice_past, until=target.opened, dimensions=dimensions
                    )
                if "corrections" not in fitted:
                    fitted["corrections"] = Backbone.fit(
                        correction_past, until=target.opened, dimensions=dimensions
                    )
                coefficient = sum(
                    (m.beta + m.offsets.get(target.maker, np.zeros(dimensions)))
                    for m in (fitted["backbone"], fitted["corrections"])
                )
                p = softmax(target.features @ coefficient)
            elif module == "uniform":
                p = np.ones(len(target.features)) / len(target.features)
            else:
                key = "backbone" if module in {"population", "prototypes"} else module
                if key not in fitted:
                    fitted[key] = Backbone.fit(train, until=target.opened, dimensions=dimensions)
                model = fitted[key]
                # Empty identity forces the pooled coefficient; never a personal offset.
                p = model.predict(
                    "" if module == "population" else target.maker,
                    target.features,
                    at=target.opened,
                )
                if module == "prototypes":
                    from scipy.special import softmax

                    from ..models.prototypes import discover, fit_mix

                    # Other makers define the prototypes; this maker's earlier
                    # comparisons estimate only the mix and small residual.
                    other = [r for r in train if r.maker != target.maker]
                    prototype_fit = Backbone.fit(other, until=target.opened, dimensions=dimensions)
                    if prototype_fit.offsets:
                        vectors = discover(prototype_fit.offsets)
                        mix = fit_mix(
                            train,
                            maker=target.maker,
                            prototypes=vectors,
                            population=prototype_fit.beta,
                            until=target.opened,
                        )
                        p = softmax(target.features @ (prototype_fit.beta + mix["offset"]))
            truth = np.eye(len(p))[target.taken]
            output.append(
                {
                    "decision": target.id,
                    "maker": target.maker,
                    "prompt": target.prompt,
                    "opened": target.opened.isoformat(),
                    "resolved": target.resolved.isoformat(),
                    "module": module,
                    "task": task,
                    "taken": target.taken,
                    "probabilities": p.tolist(),
                    "half_brier": float(np.sum((p - truth) ** 2) / 2),
                    "log_loss": float(-np.log(max(1e-300, p[target.taken]))),
                    "training_records": len(train),
                    "weighting": weighting,
                    "training_hash": input_hash(train, target.opened),
                    "training_makers": sorted({r.maker for r in train}),
                    "training_latest": max((r.resolved.isoformat() for r in train), default=None),
                }
            )
        if progress:
            progress({"decisions": index + 1, "total": len(targets)})
    return output, {
        "decisions": len(targets),
        "seconds": time.monotonic() - start,
        "implementation_hash": implementation_hash(),
        "ledger_schema_hash": schema_hash(),
        "feature_names": names,
        "extra_features_hash": digest(extra_features.model_dump(mode="json"))
        if extra_features
        else None,
        "labels_hash": digest(labels.model_dump(mode="json")) if labels else None,
        "heldout_makers": sorted(heldout_makers),
        "heldout_prompts": sorted(heldout_prompts),
        "exclusions": excluded,
        "correction_classes": kinds,
        "admission": "not established",
    }
