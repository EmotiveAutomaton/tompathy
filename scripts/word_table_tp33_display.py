"""Bind only the passed, landed TP33 result to its research-view pack."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src/core/worry-lift-decision.json"
PACK = "rp-worry-1@59c6bb3e90fc1723e6ac6682107ea91d118eea63ecf719d25b32764fa9785b3a"


def decision(public, source, exit_proof, event):
    private = json.loads(source)
    pin = hashlib.sha256(source).hexdigest()
    if (public.get("sourceReceiptPin") != pin or public.get("card") != "TP33"
            or public.get("status") != "complete" or public.get("productionAdmission") is not False
            or any(public.get(k) != v for k, v in private.items())
            or event["card"] != "TP33" or event["receiptPin"] != pin or event["ledger"] != public["ledger"]
            or not all(exit_proof.get(k) is True for k in
                       ("nativeExited", "releaseMatches", "sharedLeaseAbsent", "localLeaseAbsent"))):
        raise ValueError("Missing verified TP33 landing")
    plain = public["plain"]
    if (public["minimumLift"] != 1.0 or public["pack"] != PACK or plain["pages"] != 40
            or plain["windows"] <= 0 or plain["fraction"] != plain["shown"] / plain["windows"]
            or len(public["essays"]) != 3 or set(public["knownGroups"]) != {"ed", "go", "envent"}):
        raise ValueError("Unexpected protocol or coverage")
    eligible = plain["fraction"] <= .10 and all(e["subset"] for e in public["essays"])
    if public["researchDisplayPasses"] != eligible:
        raise ValueError("Contradictory display decision")
    return {"pack": PACK if eligible else None, "sourceReceiptPin": pin if eligible else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    local = ROOT / ".local/word-table"
    job = local / "tp33-a"
    public_path = ROOT / "engine/validation/readers-worry-lift-2026-11.json"
    if not public_path.exists():
        if args.apply:
            raise SystemExit("TP33 has no verified public result yet")
        print("Pending TP33 landing.")
        return
    payload = public_path.read_bytes()
    public = json.loads(payload)
    event = json.loads((local / "overnight-cpu-events.json").read_bytes())[public["sourceReceiptPin"]]
    if hashlib.sha256(payload).hexdigest() != event["publicPin"]:
        raise ValueError("Public aggregate changed")
    selected = decision(public, (job / "receipt.json").read_bytes(),
                        json.loads((job / "exit-verification.json").read_bytes()), event)
    old = json.loads(DEST.read_bytes())
    if old != selected and args.apply:
        if old["sourceReceiptPin"] is not None:
            raise ValueError("Preserve the previous research-view decision")
        tmp = DEST.with_suffix(".tmp")
        tmp.write_text(json.dumps(selected) + "\n", encoding="utf8")
        os.replace(tmp, DEST)
    print(json.dumps(selected))


if __name__ == "__main__":
    main()
