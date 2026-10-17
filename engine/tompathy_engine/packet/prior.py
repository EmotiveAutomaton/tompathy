"""Population coverage without converting text themes to personal drives."""


def apply_prior(packet, pipeline, admissions, *, domain):
    if "population-prior" not in admissions.enabled(domain):
        return []
    fit = pipeline.fits.get("joint", pipeline.fits.get("options", pipeline.fits.get("corrections")))
    if fit is None or len(fit.offsets) < 2:
        return []
    packet["population"]["makersPooled"] = len(fit.offsets)
    packet["population"]["description"] = (
        f"Population coverage: {len(fit.offsets)} source-scoped makers. "
        "Personal drive position is unknown: no admitted measurement maps these coefficients to drives. "
        "What would move this estimate: choices under changed needs and constraints, with an independently tested drive measurement."
    )
    return [admissions.require("population-prior", domain).admission_id]
