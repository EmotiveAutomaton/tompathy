"""TP57 descriptive comparison of early blog words and assigned chat words."""
import gzip
import json
from pathlib import Path
import numpy as np
from cb_inputs import pin
from tompathy_engine.eval.readers.affect_data import ed_situations
from tompathy_engine.eval.readers.tp36 import verify_order
from tompathy_engine.eval.readers.tp39 import TP28,saved
from tompathy_engine.eval.readers.word_panels import pinned
from week_word_departures import WORDS,matches
from week_drift import cosine
from week_people import WEEK,rows
from week_need_losses import standard


def prepare(out,check):
    src=WEEK/"Q20-inputs-a"
    cfg=pinned(src/"receipt.json","84894f9adaa02ad4b51c6078573c6633d8d73be85e91965b5e1644ee646fbb54")
    joins=src/"local-joins.jsonl.gz"
    if pin(joins)!=cfg["joinsPin"]:raise ValueError("Changed joins")
    from collections import Counter
    counts=Counter(r["opening"] for r in rows(joins) if r["qualifies"] and r["opening"])
    masks={}
    for n,h in cfg["shards"].items():
        check();path=src/"spark-inputs"/n
        if pin(path)!=h:raise ValueError("Changed text")
        for key,text in rows(path):
            if key in counts:masks[key]=matches(text)
    audit=json.loads((WEEK/"Q20-transfer.json").read_bytes())
    mirror=Path(audit["mirror"]);rec=pinned(mirror/"receipt.json",audit["sourceReceiptPin"])
    if not audit["nativeExited"] or not audit["priorFlockReleased"]:raise ValueError("Missing exit")
    total=np.zeros(19);squares=total.copy();word=np.zeros((8,19));ns=np.zeros(8)
    for n,h in rec["outputs"].items():
        if not n.startswith("scores-"):continue
        check();p=mirror/n
        if pin(p)!=h:raise ValueError("Changed scores")
        with np.load(p) as f:
            ids=f['ids'].tolist();xx=f['tags'].astype(float)
        w=np.array([counts[k] for k in ids]);m=np.array([masks.get(k,0) for k in ids])
        total+=w@xx;squares+=w@(xx**2)
        for j in range(8):
            ww=w*((m&(1<<j))!=0);word[j]+=ww@xx;ns[j]+=ww.sum()
    mean=total/sum(counts.values());sd=np.sqrt(squares/sum(counts.values())-mean**2)
    ed,ident=ed_situations(Path(".local/readers/data/empathetic-dialogues"))
    folder=Path(".local/nine-channel/tp28-a");r=pinned(folder/"receipt.json",TP28)
    if r["sources"]["ed"]["identity"]!=ident:raise ValueError("Changed ED")
    p=saved(folder,"ed/scores.npz",r);verify_order(p,ed.id)
    with np.load(p) as f:tags=standard(f["scores"].astype(float))
    table={}
    for j,name in enumerate(WORDS):
        chat=tags[ed.label.eq(name)]
        a=(word[j]/ns[j]-mean)/sd if ns[j] else None
        b=chat.mean(0) if len(chat) else None
        table[name]=dict(blogPosts=int(ns[j]),chatSituations=len(chat),
                         blog=a.tolist() if a is not None else None,
                         chat=b.tolist() if b is not None else None,
                         cosine=cosine(a,b) if a is not None and b is not None else None)
    return dict(card="TP57-secondary",source=audit["sourceReceiptPin"],chatSource=TP28,table=table)
