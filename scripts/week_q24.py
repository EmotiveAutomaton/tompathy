"""Preemptible Q24 reader B. Accept only durable whole-author prefixes."""
import gzip
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path("/home/agent/tompathy-open/week-20261122")
PREV = ROOT.parent/"person-teacher-20261121"
LOCK = Path("/home/agent/gpu.lock")
OUT = ROOT/"jobs/Q24"
ROSTER = ROOT/"Q24-roster-a.jsonl.gz"
ROSTER_PIN = "dd5579d130c2fa4b415e862c17aca6574cc78e7ec460d3c4fc45e542e60277fd"
REG = "22e90646c03230dd8c00fe1cb98ff38149adc445467fd11c8050916ca8fcfbb9"
sys.path.insert(0,str(ROOT/"code"))
import word_table_lane as lane

read,write,pin = lane.read,lane.write,lane.pin


def check():
    if time.time()>=1795795200 or any((p/"STOP").exists() for p in (OUT,ROOT,PREV,PREV/"cb",ROOT.parent/"word-table-20261120")):
        raise RuntimeError("Study cutoff or STOP")


def pending():
    # The owner or another queue can park the filler before starting a priority job.
    return (ROOT/"priority.pending").exists() or (OUT/"YIELD").exists()


def load_inputs():
    cfg=read(ROOT/"registration.json")
    if (pin(ROOT/"registration.json")!=REG or read(ROOT/"first-three-complete.json")["registration"]!=REG
        or pin(ROSTER)!=ROSTER_PIN or pin(PREV/"jobs/Q19/receipt.json")!="3a5eac345bbc3e738fd817e6b037d0d45ac4acf1c6a5e4eccdb35039627e3dee"):
        raise ValueError("Changed prerequisite")
    for n in ("word_table_lane.py","spark-reader-job.py"):
        if pin(ROOT/"code"/n)!=cfg["code"][n]:raise ValueError("Changed reader runtime")
    with gzip.open(ROSTER,"rt") as f: authors=list(map(json.loads,f))
    text={h:None for author in authors for _,h in author}
    mf=ROOT/"Q20-inputs.json"
    if pin(mf)!=cfg["manifests"]["Q20"]:raise ValueError("Input manifest differs")
    for name,h in read(mf)["files"].items():
        check()
        path=ROOT/"Q20-inputs"/name
        if pin(path)!=h:raise ValueError("Text shard differs")
        with gzip.open(path,"rt",encoding="utf8") as f:
            for key,value in map(json.loads,f):
                if key in text:
                    if hashlib.sha256(value.encode()).hexdigest()!=key:raise ValueError("Text differs")
                    text[key]=value
    if any(v is None for v in text.values()):raise ValueError("Missing opening")
    return authors,text


def run():
    lane.settings()
    OUT.mkdir(exist_ok=True)
    with lane.lease(OUT/"dispatcher.lock"):
        check()
        authors,text=load_inputs()
        worker=dict(lane.identity(),job="Q24",commit=Path(__file__).parent.name,scriptPin=pin(Path(__file__)),at=lane.now())
        write(OUT/"owner.json",worker)
        total=sum(map(len,authors));done=0
        for ordinal,author in enumerate(authors):
            author_out=OUT/f"author-{ordinal:05d}"
            marker=author_out/"complete.json"
            if marker.exists():
                receipt=read(marker)
                if receipt["rosterPin"]!=ROSTER_PIN or receipt["end"]!=done+len(author):raise ValueError("Bad author prefix")
                done+=len(author);continue
            while True:
                check()
                if pending():
                    time.sleep(15);continue
                try:
                    with lane.lease(LOCK):
                        if pending() or lane.core.api("ps")["models"]:raise lane.Busy()
                        author_out.mkdir(exist_ok=True)
                        with lane.core.Guard(OUT,0,deadline=time.monotonic()+1795795200-time.time()) as guard:
                            class Checks:
                                def check(self):
                                    guard.check();check()
                            cut=100-done
                            spans=[(0,cut),(cut,len(author))] if 0<cut<len(author) else [(0,len(author))]
                            for start,end in spans:
                                block=author_out/f"from-{start}"
                                items=[dict(id=i,text=text[h]) for i,h in author[start:end]]
                                lengths={r["id"]:len((lane.core.CORRECTED_PROMPT+r["text"]).encode()) for r in items}
                                binding=dict(job="Q24",rosterPin=ROSTER_PIN,ordinal=ordinal,start=start,scriptPin=worker["scriptPin"])
                                result=lane.rate(ROOT,block,items,"B","Q24",binding,Checks(),token_lengths=lengths)
                                if done+end==100 and not (OUT/"pilot.json").exists():
                                    seconds=sum(read(f)["seconds"] for f in OUT.glob("author-*/from-*/B/row-*.json"))
                                    write(OUT/"pilot.json",dict(rows=100,modelPin=result["modelPin"],inferenceSeconds=seconds,
                                          projectedInferenceHours=seconds*total/100/3600,total=total))
                        done+=len(author)
                        write(marker,dict(rosterPin=ROSTER_PIN,end=done,rows=len(author)))
                        write(OUT/"progress.json",dict(at=lane.now(),wholeAuthors=ordinal+1,rows=done,total=total))
                    break
                except lane.Busy:
                    time.sleep(30)
            # Let queued GPU users acquire the shared flock before another author.
            time.sleep(5)
        write(OUT/"complete.json",dict(owner=worker,rows=done,rosterPin=ROSTER_PIN,at=lane.now()))


if __name__=="__main__":
    try:run()
    except lane.Busy:raise SystemExit(74)
    except Exception as exc:
        write(OUT/"failed.json",dict(at=lane.now(),reason=str(exc)));raise
