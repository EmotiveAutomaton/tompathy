"""Full-history trait rows, the original five-by-five contrast, and the two signed maps."""

import numpy as np
from panels import GROUPS, TAGS, TRAITS, UNPLEASANT, correlations, project

MAP = {
    **dict.fromkeys(["curiosity"], "Openness"),
    **dict.fromkeys(
        ["status", "approval", "power", "competition", "honor"], "Extraversion"
    ),
    **dict.fromkeys(["family", "contact", "acceptance"], "Agreeableness"),
    **dict.fromkeys(["order", "savings", "serenity"], "Conscientiousness"),
    **dict.fromkeys(["worry", *UNPLEASANT], "Neuroticism"),
}
PRINT = {
    ("curiosity", "Openness"): 1,
    ("order", "Conscientiousness"): 1,
    ("contact", "Extraversion"): 1,
    ("acceptance", "Neuroticism"): 1,
    ("power", "Agreeableness"): -1,
    ("competition", "Agreeableness"): -1,
}


def clear(values, sign=1):
    draws = sign * values[1:]
    finite = draws[np.isfinite(draws)]
    return bool(len(finite) and np.quantile(finite, 0.025) > 0 and sign * values[0] > 0)


def table(owners, base, worry, target, names, directions, output):
    if len(owners) < 11:
        return
    z = project(base, worry, directions)
    tags = z[:, : len(TAGS)]
    sd = tags.std(0)
    scaled = np.divide(
        tags - tags.mean(0), sd, out=np.full_like(tags, np.nan), where=sd > 0
    )
    composite = [
        scaled[:, [TAGS.index(tag) for tag in group]].mean(1)
        for group in GROUPS.values()
    ]
    x = np.column_stack((z, *composite))
    keys = [*names, *GROUPS]
    trained = output.kind == "trained"
    c = np.stack(
        [
            correlations(x, np.broadcast_to(target[:, j, None], x.shape), trained)
            for j in range(len(TRAITS))
        ],
        axis=2,
    )
    signed = c[0, : len(names)]
    print_pass = {}
    if trained:
        for (name, trait), sign in PRINT.items():
            v = c[:, keys.index(name), TRAITS.index(trait)]
            if name == "contact":
                v = v - c[:, keys.index(name), TRAITS.index("Agreeableness")]
            print_pass[name, trait] = int(clear(v, sign))
    for i, name in enumerate(keys):
        for j, trait in enumerate(TRAITS):
            mapped = MAP.get(name) == trait
            rival = (name, trait) in PRINT
            # Individual TP63 leaders are evaluated against individual outputs.
            # The composite contrast below has its own five-by-five rule.
            leads = False
            if trained and mapped and np.isfinite(signed[i, j]):
                others = np.r_[
                    np.delete(abs(signed[i]), j), np.delete(abs(signed[:, j]), i)
                ]
                others = others[np.isfinite(others)]
                leads = bool(
                    len(others) and signed[i, j] > others.max() and clear(c[:, i, j])
                )
            output.add(
                "traits.csv",
                [name, trait],
                owners,
                c[:, i, j],
                [int(mapped), int(leads), int(rival), print_pass.get((name, trait), 0)],
            )
    indexes = [*[keys.index(key) for key in GROUPS], keys.index("worry")]
    square = c[:, indexes, :]
    diag = np.eye(5, dtype=bool)
    difference = square[:, diag].mean(1) - square[:, ~diag].mean(1)
    heads = square[0]
    leaders = sum(
        int(
            heads[i, i] > 0
            and heads[i, i] > np.delete(heads[:, i], i).max()
            and heads[i, i] > np.delete(heads[i], i).max()
        )
        for i in range(5)
    )
    output.add(
        "contrast.csv",
        ["diagonalMinusOther"],
        owners,
        difference,
        [
            leaders,
            int(leaders >= 4 and trained and clear(difference)),
            int(trained and len(print_pass) == len(PRINT) and all(print_pass.values())),
        ],
    )
    for name in ("amusement", "SEEKING"):
        if name in keys:
            output.add(
                "channels.csv",
                [name],
                owners,
                c[:, keys.index(name), TRAITS.index("Neuroticism")],
            )
