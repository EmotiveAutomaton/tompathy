"""Read only the receiver's narrow projection. Write aggregate CSVs in fresh private scratch."""
import argparse
import csv
import datetime
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from reader import Readers, ROOT
from tables import TRAITS, Output, learning_tables, profiles, trait_tables
import numpy as np

def rows(path, header):
    with path.open(encoding='utf8',newline='') as stream:
        form = csv.DictReader(stream,strict=True)
        if form.fieldnames != header:
            raise ValueError('Expected documented projection')
        for row in form:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Malformed input row')
            yield row

def community(label):
    return label.casefold().strip().removeprefix('/').removeprefix('r/')

def run(source,dest):
    forbidden = json.loads((source/'excluded_communities.json').read_bytes())
    if not isinstance(forbidden,list) or not forbidden or not all(isinstance(v,str) and community(v) for v in forbidden):
        raise ValueError('Receiver must bind collection communities')
    forbidden = set(map(community,forbidden))
    traits = {}
    for row in rows(source/'traits.csv',['author',*TRAITS]):
        a = row['author']
        scores = [float(row[t]) for t in TRAITS]
        if not a.strip() or a in traits or not np.isfinite(scores).all():
            raise ValueError('Invalid complete trait vector')
        traits[a] = scores
    dictionary = {}
    full,opens = defaultdict(list),defaultdict(list)
    seen = set()
    for row in rows(source/'comments.csv',['author','id','day','community','text']):
        a = row['author']
        if not community(row['community']):
            raise ValueError('Missing community')
        if a not in traits or community(row['community']) in forbidden:
            continue
        day = datetime.date.fromisoformat(row['day']).isoformat()
        ident = row['id']
        if not ident or ident in seen:
            raise ValueError('Invalid unique comment ID')
        seen.add(ident)
        text = html.unescape(re.sub('<[^>]*>',' ',row['text'])).strip()
        if not text:
            continue
        full[a].append(dictionary.setdefault(text,len(dictionary)))
        words = text.split()
        if len(words)>=30:
            first = ' '.join(words[:150])
            ends = list(re.finditer(r"""[.!?]+["'”’)]*(?=\s|$)""",first))
            if ends:
                text = first[:ends[-1].end()]
                opens[a].append((day,ident,dictionary.setdefault(text,len(dictionary))))
    if len(full)<11:
        raise ValueError('Insufficient distinct contributors')
    texts = list(dictionary)
    readers = Readers()
    score = np.vstack([readers.score(texts[i:i+16]) for i in range(0,len(texts),16)])
    if score.shape!=(len(texts),49) or not np.isfinite(score).all():
        raise ValueError('Invalid reader output')
    output = Output()
    trait_tables({a:score[ix].mean(0) for a,ix in full.items()},traits,output)
    deep = {a for a in opens if len(full[a])>=80}
    frames = profiles(opens,deep,texts,score,json.loads((ROOT/'style.json').read_bytes()))
    learning_tables(frames,deep,output)
    output.write(dest)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('projection',type=Path)
    parser.add_argument('scratch',type=Path)
    args = parser.parse_args()
    def forbid(event,unused):
        if event.startswith('socket.'):
            raise RuntimeError('Network use refused')
    sys.addaudithook(forbid)
    run(args.projection,args.scratch)

