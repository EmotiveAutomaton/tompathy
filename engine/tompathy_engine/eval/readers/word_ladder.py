"""Score the two finished G2 ladder rungs at the registered morning review."""
import hashlib
import json
from pathlib import Path

import numpy as np

from ..back_half.reporting import save_json
from .checkpoint import completed
from .tp30 import CHANNELS, WRITER_CHANNELS, auc_rows, co_rise, mix, transfer_summary
from .word_panels import CROSSWALK, Mirror, pinned, read, sha256

FROZEN = "d04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250"
MODELS = ("sentence-transformers/all-MiniLM-L6-v2", "sentence-transformers/all-mpnet-base-v2", "answerdotai/ModernBERT-large")
LIMIT = "Held-out writers' words and reader votes are stand-ins. Co-rise describes predictions. ED is research-only."


class Q13Forecasts:
    """Read the compact forecast deliverable. The large checkpoints stay on the Spark."""
    def __init__(self, path):
        self.path = Path(path)
        audit = read(self.path.parent/'Q13-modernbert-transfer.json')
        self.pin = audit['sourceReceiptPin']
        self.receipt = pinned(self.path/'receipt.json',self.pin)
        reg = read(self.path.parent/'q13-copy-registration.json')
        owner = self.receipt['owner']
        parent = read(Path('.local/word-table/verified-spark-G2-a/receipt.json'))
        if (not audit['nativeExited'] or not audit['priorFlockReleased'] or audit['owner'] != owner
                or owner['job'] != 'Q13-modernbert' or owner['commit'] != reg['commit']
                or self.receipt['status'] != 'complete' or audit['release'] != read(self.path/'released.json')
                or audit['release']['owner'] != owner or audit['release']['nativeExitCode'] != 0
                or self.receipt['parentReceiptPin'] != sha256(Path('.local/word-table/verified-spark-G2-a/receipt.json'))
                or parent['status'] != 'failed' or any(self.receipt['scienceEntry'].get(k)!=v for k,v in parent['entry'].items())
                or audit['copy']['sourcePin'] != '51c188e92b3473af802af78fd3ec4b10baceef0b13fc783516c4ef3c445194fe'
                or audit['copy']['status'] != 'verified' or audit['copyExit']['nativeExitCode'] != 0
                or audit['copyExit']['owner'] != audit['copy']['owner'] or read(self.path/'complete.json')['receiptPin'] != self.pin):
            raise ValueError('Compact Q13 source, original goal or verified engineering copy differs')
        self.files = pinned(self.path/'forecast-inventory.json',self.receipt['forecastPin'])
        all_files = pinned(self.path/'complete-storage-inventory.json',self.receipt['sources'])
        if any(all_files.get(k)!=v for k,v in self.files.items()):
            raise ValueError('Forecast differs from complete retained checkpoint inventory')

    def artifact(self,name):
        path=(self.path/'forecasts'/name).resolve()
        if not path.is_relative_to((self.path/'forecasts').resolve()) or sha256(path)!=self.files[name]:
            raise ValueError('Compact prediction artifact differs')
        return path


def collect(job, arm, target, ids, binding, check):
    """The saved batches must tile the expected IDs under one checkpoint contract."""
    seal = read(job.artifact(f"{arm}/prediction-{target}.json"))
    if seal["rows"] != len(ids):
        raise ValueError("Prediction count and expected roster differ")
    attempts = {k.rsplit("/",1)[0] for k in job.files
                if k.startswith(f"{arm}/predict-{target}-attempt-") and "/batch-" in k}
    if not attempts:
        raise ValueError("Missing completed prediction archive")
    prefix = max(attempts) + "/batch-"
    names = sorted(k for k in job.files if k.startswith(prefix) and k.endswith(".npz"))
    probabilities = np.empty((len(ids),9))
    cursor = 0
    contract = None
    for i,name in enumerate(names):
        if i % 64 == 0:
            check()
        with np.load(job.artifact(name),allow_pickle=False) as archive:
            start, end = int(archive["start"]), int(archive["end"])
            raw = str(archive["contract"].item())
            if contract is None:
                spec = json.loads(raw)
                if spec["schema"] != "TP30-prediction-batch-1" or spec["binding"] != binding:
                    raise ValueError("Original prediction contract differs")
                contract = raw
            values = archive["probabilities"]
            if (contract != raw or cursor != start or not start < end <= len(ids)
                    or not np.array_equal(archive["ids"],ids[start:end]) or values.shape != (end-start,9)
                    or not np.isfinite(values).all() or np.any((values < 0) | (values > 1))):
                raise ValueError("Invalid, duplicated or reordered G2 prediction rows")
            probabilities[start:end] = values
            cursor = end
    if cursor != len(ids):
        raise ValueError("Prediction prefix is incomplete")
    return probabilities


def ladder_comparison(summaries, frozen):
    def mean(s):
        a = [s["channels"][c]["profile_auc"] for c in WRITER_CHANNELS]
        if any(v is None for v in a):
            raise ValueError("A seven-channel mean requires all seven measured channels")
        return float(np.mean(a))
    baseline = mean(frozen)
    per_seed = {}
    for seed, result in summaries.items():
        area = mean(result)
        care = result["channels"]["CARE"]["profile_auc"]
        per_seed[str(seed)] = {"mean":area,"gain":area-baseline,"care":care,
                               "clearsBoth":bool(area-baseline >= .02 and care >= .70)}
    eligible = set(per_seed) == {"23","47","71"}
    return {"frozenMean":baseline,"perSeed":per_seed,"allThreeMeasured":eligible,
            "passesAllThree":all(s["clearsBoth"] for s in per_seed.values()) if eligible else None}


def completed_repair_seeds(job):
    components = read(job.artifact("ladder-components.json"))
    if components["completed"]!=job.receipt["rows"]:
        raise ValueError("Repair component inventory and terminal receipt differ")
    finished, missing = [], {}
    for seed in (23,47,71):
        absent = [view+"-"+kind for view in ("go_only","go_plus_envent") for kind in ("profile","control")
                  if f"rung-2/seed-{seed}/{view}-{kind}/completed.json" not in job.files]
        if absent:
            if MODELS[2] not in components["skipped"] and any(
                f"rung-2-seed-{seed}-{arm}" not in components["skipped"] for arm in absent
            ):
                raise ValueError("Unexpected missing repair fits")
            missing[str(seed)] = absent
        else:
            finished.append(seed)
    return finished, {"unavailableComponentsBySeed":missing,"rungSkipped":MODELS[2] in components["skipped"],
                      "rd2Skipped":"RD2-2" in components["skipped"]}


def run(frozen, mirror, base, output, check, ledger, protocol, *, modernbert=False):
    original = completed(frozen,"TP30-frozen")
    if sha256(frozen/"receipt.json") != FROZEN or sha256(protocol) != original_fine_protocol(base):
        raise ValueError("Original frozen controls or registered fine protocol changed")
    files = pinned(frozen/"artifact-manifest.json",original["artifactsPin"])["files"]
    def frozen_array(name):
        if sha256(frozen/name)!=files[name]:
            raise ValueError("Frozen evaluation data changed")
        return np.load(frozen/name,allow_pickle=False)
    if modernbert and Path(mirror).name == 'verified-spark-Q13-modernbert-a':
        g2 = Q13Forecasts(mirror)
    else:
        g2 = Mirror(mirror,"G2-modernbert-a" if modernbert else "G2")
    cfg = read(base/"remaining-extension-a/inputs/G2-contract.json")
    payload = sha256(base/"remaining-extension-a/inputs/G2-contract.json")
    science_entry = g2.receipt["scienceEntry"] if modernbert else g2.receipt["entry"]
    code = hashlib.sha256(json.dumps(science_entry["codePins"],sort_keys=True).encode()).hexdigest()
    if payload != "cc198ace92eea89219ec06811c588c8f072afb2ea410227e777ff1623c9ff793":
        raise ValueError("G2 payload changed")
    aliases = pinned(base/"F2-release-local/local-original-id-map.json",CROSSWALK)
    ids, truth = {}, {}
    for target in ("ed","envent","go"):
        with frozen_array(target+"-profile-forecasts.npz") as a:
            ids[target] = a["ids"]
            truth[target] = a["truth"]
        if target=="envent":
            ids[target] = np.asarray([aliases.get(str(k),str(k)) for k in ids[target]])
    with frozen_array("go-targets.npz") as a:
        test = a["test"]
        if not np.array_equal(ids["go"],a["ids"][test]):
            raise ValueError("Held-out Go roster mismatch")
        disagreement, pairs, shares = (a[k][test] for k in ("disagreement","pair_support","shares"))
    result = {"card":"G2-modernbert" if modernbert else "G2-first-rungs","status":"running","productionAdmission":False,"ledger":ledger,
              "scope":LIMIT,"parentReceiptPin":g2.pin,"frozenReceiptPin":FROZEN,"protocolPin":cfg["protocolPin"],
              "rungs":{},"unmeasured":[] if modernbert else ["ModernBERT-large"]}
    if modernbert:
        result["originalReceiptPin"] = g2.receipt["parentReceiptPin"]
    save_json(output/"receipt.json",result)
    if modernbert:
        seeds, coverage = completed_repair_seeds(g2)
        result["coverage"] = coverage
        if not seeds:
            result["unmeasured"] = ["ModernBERT-large"]
        planned = [(2,seeds)]
    else:
        planned = [(0,(23,)),(1,(23,47,71))]
    for index, seeds in planned:
        root = f"rung-{index}"
        source = read(g2.artifact(root+"/source.json"))
        if source["id"] != MODELS[index]:
            raise ValueError("Encoder registration changed")
        rows = {}
        for seed in seeds:
            across = {"ed":{}, "envent":{}}
            within = {}
            for view in ("go_only","go_plus_envent"):
                for kind in ("profile","control"):
                    check()
                    arm = f"{root}/seed-{seed}/{view}-{kind}"
                    done = read(g2.artifact(arm+"/completed.json"))
                    if done["component"] != view+"-"+kind or done["seed"] != seed:
                        raise ValueError("Wrong training arm")
                    pin = read(g2.artifact(arm+"/full-complete.json"))["checkpointPin"]
                    with frozen_array(view+"-"+kind+"-head.npz") as a:
                        supported = a["supported"]
                    for target in (("ed",) if view=="go_plus_envent" else ("go","envent")):
                        binding = {"payloadPin": payload,"sourceReceiptPin": FROZEN,"protocolPin": cfg["protocolPin"],
                                       "modelCheckpointPin": pin,"implementationPin": code,"target": target}
                        prediction = collect(g2,arm,target,ids[target],binding,check)
                        cells = auc_rows(truth[target],prediction,supported)
                        if target=="go":
                            within[kind] = cells
                            if kind=="profile":
                                mixture = mix(prediction,disagreement,pairs)
                                corise = {"channels":list(CHANNELS),"n":len(shares),
                                          "predicted":co_rise(prediction),"reader_shares":co_rise(shares)}
                        else:
                            across[target][kind] = cells
            rows[str(seed)] = {"within_source":within,"across_sources":across,"summary":transfer_summary(across),
                               "mix":mixture,"co_rise":corise}
        result["rungs"][source["id"]] = {"revision":source["revision"],"rows":rows,
            "comparison":ladder_comparison({s:r["summary"] for s,r in rows.items()},original["rows"]["summary"])}
        save_json(output/"receipt.json",result)
    result["status"] = "complete"
    save_json(output/"receipt.json",result)


def original_fine_protocol(base):
    path = Path(base)/"remaining-extension-a/inputs/G2-contract.json"
    return pinned(path,"cc198ace92eea89219ec06811c588c8f072afb2ea410227e777ff1623c9ff793")["protocolPin"]
