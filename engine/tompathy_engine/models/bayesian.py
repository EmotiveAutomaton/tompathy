"""Optional CPU hierarchical posterior, on the canonical offered alternatives.

The effective coefficient has a pooled Normal prior. Its norm in a fixed,
training-standardized basis defines predictability; its unit direction defines
utility orientation. A free multiplier and free coefficient scale are not fitted
together. This convention is explicit and needs its own scientific admission.
"""

import numpy as np

from ..admission import implementation_hash
from ..ledger.schema import schema_hash
from .bundle import input_hash


def fit(
    rows,
    *,
    until,
    method="nuts",
    warmup=300,
    samples=500,
    steps=2000,
    seed=0,
    maximum_records=10000,
    progress=False,
):
    if until.tzinfo is None or method not in {"nuts", "svi"}:
        raise ValueError("Choose a posterior method and aware cutoff")
    rows = sorted([r for r in rows if r.resolved < until], key=lambda r: (r.opened, r.id))
    if not rows or len(rows) > maximum_records or not 1 <= maximum_records <= 100000:
        raise ValueError("Posterior fit record bound exceeded or no earlier data")
    if not 1 <= warmup <= 10000 or not 2 <= samples <= 10000 or not 1 <= steps <= 100000:
        raise ValueError("Posterior fit iteration bound exceeded")
    if len({r.id for r in rows}) != len(rows):
        raise ValueError("Duplicate posterior training examples")
    try:
        import jax
        import jax.numpy as jnp
        import numpyro
        import numpyro.distributions as dist
        from numpyro.infer import MCMC, NUTS, SVI, Trace_ELBO
        from numpyro.infer.autoguide import AutoNormal
        from numpyro.optim import Adam
    except ImportError as exc:
        raise RuntimeError("Posterior fitting requires the optional bayes extra") from exc
    # Explicit CPU device context: never consume a shared research accelerator.
    with jax.default_device(jax.devices("cpu")[0]):
        makers = sorted({r.maker for r in rows})
        d, offered = rows[0].features.shape[1], max(len(r.features) for r in rows)
        if any(r.features.shape[1] != d for r in rows):
            raise ValueError("Posterior feature dimensions disagree")
        centered = [r.features - r.features.mean(0) for r in rows]
        variability = np.std(np.concatenate(centered), axis=0)
        active = variability > 1e-6
        scale = np.maximum(variability, 1e-6)
        x = np.zeros((len(rows), offered, d))
        mask = np.zeros((len(rows), offered), dtype=bool)
        for i, values in enumerate(centered):
            x[i, : len(values)] = values / scale
            mask[i, : len(values)] = True
        x, mask = jnp.asarray(x), jnp.asarray(mask)
        mid = jnp.asarray([makers.index(r.maker) for r in rows])
        taken = jnp.asarray([r.taken for r in rows])
        weight = jnp.asarray([r.weight for r in rows])

        def model():
            beta = numpyro.sample("beta", dist.Normal(0, 1).expand([d]).to_event(1))
            tau = numpyro.sample("tau", dist.HalfNormal(0.5).expand([d]).to_event(1))
            z = numpyro.sample("z", dist.Normal(0, 1).expand([len(makers), d]).to_event(2))
            offset = numpyro.deterministic("offset", z * tau)
            coefficient = beta + offset
            numpyro.deterministic("predictability", jnp.linalg.norm(coefficient * active, axis=1))
            logits = jnp.einsum("nkd,nd->nk", x, coefficient[mid])
            logits = jnp.where(mask, logits, -jnp.inf)
            numpyro.factor(
                "choices", (weight * dist.Categorical(logits=logits).log_prob(taken)).sum()
            )

        key = jax.random.PRNGKey(seed)
        if method == "nuts":
            sampler = MCMC(
                NUTS(model, target_accept_prob=0.9),
                num_warmup=warmup,
                num_samples=samples,
                num_chains=1,
                progress_bar=progress,
            )
            sampler.run(key)
            draws = sampler.get_samples()
            diagnostics = {
                "divergences": int(np.asarray(sampler.get_extra_fields()["diverging"]).sum()),
                "chains": 1,
                "convergence": "requires independent multi-chain assessment",
            }
        else:
            guide = AutoNormal(model)
            svi = SVI(model, guide, Adam(0.01), Trace_ELBO())
            result = svi.run(key, steps, progress_bar=progress)
            draws = guide.sample_posterior(
                jax.random.PRNGKey(seed + 1), result.params, sample_shape=(samples,)
            )
            diagnostics = {
                "final_loss": float(result.losses[-1]),
                "intervals": "mean-field variational approximation; assess coverage",
            }
        values = {k: np.asarray(v) for k, v in draws.items()}
        values["offset"] = values["z"] * values["tau"][:, None, :]
        values["predictability"] = np.linalg.norm(
            (values["beta"][:, None, :] + values["offset"]) * active, axis=2
        )
        if not all(np.isfinite(v).all() for v in values.values()):
            raise ValueError("Nonfinite posterior samples")

        def summary(v):
            return {
                "mean": v.mean(0).tolist(),
                "interval": np.quantile(v, [0.025, 0.975], axis=0).tolist(),
            }

        return {
            "format": "tompathy-posterior-1",
            "method": method,
            "until": until.isoformat(),
            "makers": makers,
            "feature_scale": scale.tolist(),
            "active_features": active.tolist(),
            "train_ids": [r.id for r in rows],
            "input_hash": input_hash(rows, until),
            "implementation_hash": implementation_hash(),
            "ledger_schema_hash": schema_hash(),
            "seed": seed,
            "samples": samples,
            "summary": {k: summary(values[k]) for k in ("beta", "tau", "offset", "predictability")},
            "diagnostics": diagnostics,
            "numpyro_version": numpyro.__version__,
            "jax_version": jax.__version__,
            "scale_convention": "unit utility direction; predictability is coefficient norm in training-standardized basis",
            "admission": "research posterior; no automatic packet contribution",
        }
