"""Fixed worry-display acceptance using saved windows and independent source-level benchmarks."""
import json
from collections import Counter

import numpy as np
from sklearn.metrics import roc_auc_score

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .checkpoint import completed

WIRE = "6bcd5dae0c463ffb45f1b9b3ac6988d9db745e6943196ca9521544a56152c4d9"
HEAD = "99d507ec9350998b41af76ea95626cd789c78bdc59b607fe24c6ea99dcfb3789"
PACK = "rp-worry-1@59c6bb3e90fc1723e6ac6682107ea91d118eea63ecf719d25b32764fa9785b3a"


def lifted(series):
    if not series:
        raise ValueError("Original page has no scored windows")
    values = np.asarray([w["value"] for w in series])
    spans = [(w["from"], w["to"]) for w in series]
    if (not np.isfinite(values).all() or np.any((values < 0) | (values > 1))
            or any(a < 0 or a >= b for a, b in spans) or len(set(spans)) != len(spans)):
        raise ValueError("Invalid original window")
    differences = (values - np.median(values)) * 8
    return [span for span, difference in zip(spans, differences, strict=True) if difference >= 1]


def run(wire, head, output, check, ledger, protocol):
    base = completed(wire, "TS3-real")
    benchmark = completed(head, "TP26")
    manifest = wire / "artifact-manifest.json"
    if (sha256(wire / "receipt.json") != WIRE or sha256(head / "receipt.json") != HEAD
            or sha256(manifest) != base["artifactsPin"] or base["packs"] != [PACK]):
        raise ValueError("Original worry benchmark or captured window source changed")
    files = json.loads(manifest.read_bytes())["files"]
    sizes = Counter()
    essays, audit = [], {}
    shown = total = 0
    for row in base["rows"]:
        if row["kind"] not in {"theme-free", "public-coauthor"}:
            continue
        check()
        name = row["name"]
        key = f"packets/{name}.json"
        path = wire / key
        if name in audit or sha256(path) != files[key]:
            raise ValueError("Window capture changed or duplicated")
        readings = json.loads(path.read_bytes())["bottom_box"]["on_page"]
        series, = [r["series"] for r in readings if r["pack"] == PACK and r["id"] == "S1"]
        original = {(w["from"], w["to"]) for w in series}
        spans = lifted(series)
        audit[name] = {"selected":spans, "originalCount":len(original)}
        if row["kind"] == "theme-free":
            sizes[len(series)] += 1
            total += len(series)
            shown += len(spans)
        else:
            essays.append({"windows":len(series), "shown":len(spans), "subset":set(spans) <= original})
    if sum(sizes.values()) != 40 or len(essays) != 3:
        raise ValueError("Incomplete fixed acceptance roster")
    groups = {}
    for name in ("envent", "ed", "go"):
        check()
        path = head / (name + "-known-group.npz")
        with np.load(path, allow_pickle=False) as archive:
            score, truth = archive["scores"], archive["truth"]
        group = benchmark["groups"][name]
        if len(score) != group["n"] or int((truth == 1).sum()) != group["positive"]:
            raise ValueError("Known-group denominators changed")
        auc = float(roc_auc_score(truth, score))
        if abs(auc - group["auc"]) > 1e-12:
            raise ValueError("Original source-level AUC changed")
        groups[name] = {"n":len(score), "auc":auc, "forecastPin":sha256(path)}
    save_json(output / "spans.json", audit)
    save_json(output / "receipt.json", {"card":"TP33", "status":"complete", "ledger":ledger,
        "productionAdmission":False, "scope":"Page-relative research display. Source AUCs use the original levels.",
        "protocolPin":sha256(protocol), "sourcePins":[WIRE, HEAD], "pack":PACK, "minimumLift":1.,
        "plain":{"pages":40, "shown":shown, "windows":total, "fraction":shown/total, "sizes":dict(sizes)},
        "essays":essays, "knownGroups":groups, "spansPin":sha256(output / "spans.json"),
        "researchDisplayPasses":shown/total <= .10 and all(e["subset"] for e in essays)})
