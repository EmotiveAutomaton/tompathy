"""Serial TP1 measurements using only installed model files and declared texts."""
import argparse
import gc
import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

import numpy as np
from scipy.stats import spearmanr

from ...preview.readers import LocalReader
from ...preview.surface import words
from .resources import benchmark_priority, guard


def comparison(text, old, new):
    left, right = [words(text, tokens) for tokens in (old, new)]
    if [(w["start"], w["end"]) for w in left] != [(w["start"], w["end"]) for w in right] or not left:
        raise ValueError("Parity requires identical nonempty source-word coverage")
    a, b = [np.array([w["nats"] for w in rows]) for rows in (left, right)]
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        raise ValueError("Undefined parity rank correlation")
    return {"spearman": rho, "medianAbsoluteNats": float(np.median(abs(a-b))), "words": len(a)}


def prefix_quantization_probe(reader, text):
    torch = reader.torch
    target = reader.encode(text)["input_ids"][:1024]
    if len(target) < 1024:
        raise ValueError("Quantization probe needs 1,024 tokens")
    values = []
    with torch.inference_mode():
        for count in (512, 1024):
            guard()
            ids = torch.tensor([target[:count]], device=reader.device)
            logits = reader.model(ids, use_cache=False, logits_to_keep=torch.arange(511)).logits[0].float()
            values.append(torch.nn.functional.cross_entropy(logits, torch.tensor(target[1:512]), reduction="none").numpy())
    delta = abs(values[0] - values[1])
    return {"maxAbsoluteTokenNats": float(delta.max()), "medianAbsoluteTokenNats": float(np.median(delta)),
            "definition": "Same first 511 next-token losses in 512-token and 1024-token passes, no BOS."}


def run(directory, texts, output, threads=(1, 2), *, precisions=("float32","int8"), resume=False):
    benchmark_priority(1)
    start = monotonic()
    receipt = {"schema": "tompathy.speed.v1", "date": datetime.now(UTC).isoformat(), "status": "running",
        "machine": {"platform": platform.platform(), "processor": platform.processor()}, "measurements": [], "parity": [],
        "quantizationProbe": [], "targetSeconds": 15, "defaultChanged": False, "bindingAttentionParity": "awaiting EX1/TP2",
        "fourThreads": "not run: packet's shared-host cap is two", "onnx": "pending parity and one-thread result",
        "convention": "KV: BOS until first rebuild, 2048-token limit, rebuild from 1024 preceding tokens; initial context tail <=1536; distinct text and segment cache namespaces.",
        "inputs": [{"id": name, "sha256": hashlib.sha256(text.encode()).hexdigest(), "words": len(text.split())} for name, text in texts.items()]}
    if resume:
        previous = json.loads(output.read_text(encoding="utf8"))
        if previous.get("schema") != receipt["schema"] or previous.get("inputs") != receipt["inputs"] or previous.get("convention") != receipt["convention"]:
            raise ValueError("Resume requires identical speed inputs and scoring convention")
        if any(p["spearman"] < .98 for p in previous.get('parity',[])):
            raise ValueError("Cannot resume beyond a failed parity gate; retain this result and report it")
        previous.setdefault("attempts",[]).append({"status":previous["status"],"reason":previous.get("reason"),"elapsedSeconds":previous.get("elapsedSeconds")})
        receipt = previous
        receipt.update(status="running",reason=None)
    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_suffix(".tmp")
        temp.write_text(json.dumps(receipt, indent=2, allow_nan=False)+"\n", encoding="utf8", newline="\n")
        temp.replace(output)
    def check():
        guard()
        if monotonic() - start > 3600:
            raise RuntimeError("Speed measurement exceeded its one-hour bound")
    save()
    try:
        for precision in precisions:
            guard()
            reader = LocalReader(directory, threads=1, precision=precision)
            prior = receipt.setdefault("readers", {}).get(precision)
            if prior is not None and prior != reader.identity:
                raise ValueError("Resume reader identity differs")
            receipt["readers"][precision] = reader.identity
            probe = prefix_quantization_probe(reader, next(iter(texts.values())))
            receipt["quantizationProbe"].append({"precision": precision, **probe})
            if precision == "float32" and probe["maxAbsoluteTokenNats"] > .001:
                raise RuntimeError("Float32 causal-prefix parity failed")
            for count in threads:
                benchmark_priority(count)
                reader.torch.set_num_threads(count)
                for name, text in texts.items():
                    if any(p["precision"] == precision and p["threads"] == count and p["text"] == name for p in receipt["parity"]):
                        continue
                    outputs = []
                    for scoring in ("window", "kv"):
                        reader.scoring = scoring
                        before = dict(reader.metrics)
                        begin = monotonic()
                        outputs.append(reader.score(text, check=check))
                        receipt["measurements"].append({"text": name, "precision": precision, "threads": count,
                            "path": scoring, "loadSeconds": reader.metrics["loadMs"] / 1000,
                            "scoreSeconds": monotonic()-begin, "inputTokens": reader.metrics["inputTokens"]-before["inputTokens"],
                            "forwardCalls": reader.metrics["forwardCalls"]-before["forwardCalls"]})
                        save()
                        print(json.dumps(receipt["measurements"][-1]), flush=True)
                    parity = comparison(text, *outputs)
                    first = max(abs(a["nats"]-b["nats"]) for a,b in zip(outputs[0][:512],outputs[1][:512],strict=True))
                    first_words = [words(text,t[:512]) for t in outputs]
                    end = min(t[min(511,len(t)-1)]["end"] for t in outputs)
                    word_delta = max((abs(a["nats"]-b["nats"]) for a,b in zip(*first_words,strict=True) if a["end"] <= end),default=0.)
                    receipt["parity"].append({"text": name, "precision": precision, "threads": count, **parity, "firstBlockMaxTokenNats": first,"firstBlockMaxWordNats":word_delta})
                    save()
                    if parity["spearman"] < .98 or precision == "float32" and word_delta > .001:
                        receipt["onnx"] = "not attempted: TP1 parity stop"
                        raise RuntimeError("TP1 parity stop: do not promote or continue optimizing this path")
            del reader
            gc.collect()
        receipt["status"] = "timed; awaiting binding TP2 parity"
        receipt["onnx"] = "not installed; evaluate only if one-thread int8 remains above target"
    except Exception as exc:
        receipt.update(status="stopped", reason=str(exc))
        raise
    finally:
        receipt["elapsedSeconds"] = monotonic()-start
        save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--texts", type=Path, required=True, help="Private JSON object mapping text IDs to strings")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--precision",choices=("all","float32","int8"),default="all")
    parser.add_argument("--resume",action="store_true")
    args = parser.parse_args()
    run(args.reader, json.loads(args.texts.read_text(encoding="utf8")), args.out,
        precisions=("float32","int8") if args.precision == "all" else (args.precision,),resume=args.resume)


if __name__ == "__main__":
    main()
