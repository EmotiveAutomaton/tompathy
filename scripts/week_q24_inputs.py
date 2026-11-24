"""Pin Q24's opaque public opening IDs and whole-author boundaries; keep joins local."""
import gzip
import itertools
import json
from pathlib import Path

from cb_inputs import pin

WEEK = Path(".local/week-20261122")
Q20 = "84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54"
Q19 = "3a5eac345bbc3e738fd817e6b037d0d45ac4acf1c6a5e4eccdb35039627e3dee"


def prepare():
    src = WEEK / "Q20-inputs-a"
    cfg = json.loads((src/"receipt.json").read_bytes())
    joins = src / "local-joins.jsonl.gz"
    q19 = json.loads(Path(".local/person-teacher/Q19-transfer-a.json").read_bytes())
    old = Path(q19["mirror"])/"receipt.json"
    if (pin(old) != Q19 or q19["sourceReceiptPin"] != Q19 or not q19["nativeExited"]
            or not q19["priorFlockReleased"] or json.loads(old.read_bytes())["durableRows"] != 0
            or pin(src/"receipt.json") != Q20 or pin(joins) != cfg["joinsPin"]):
        raise ValueError("Expected verified Q19 empty cutoff and pinned Q20 input")
    out = WEEK/"Q24-roster-a.jsonl.gz"
    previous = ""
    n = authors = 0
    with gzip.open(joins,"rt",encoding="utf8") as f, gzip.open(out,"xt",encoding="utf8") as dest:
        for key,group in itertools.groupby(map(json.loads,f),key=lambda r:r["author"]):
            if key <= previous:
                raise ValueError("TP43 author order differs")
            previous = key
            posts = sorted((r["id"],r["opening"]) for r in group if r["qualifies"] and r["opening"])
            if posts:
                dest.write(json.dumps(posts,separators=(",",":"))+"\n")
                authors += 1
                n += len(posts)
    if n != cfg["counts"]["qualifyingOpenings"]:
        raise ValueError("Coverage differs")
    print(authors,n,out.stat().st_size,pin(out))


if __name__=="__main__":
    prepare()
