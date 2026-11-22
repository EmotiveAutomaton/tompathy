"""Stream Q20's public text shards and keep date/author joins on the workstation."""
import gzip
import hashlib
import html
import json
import re
import zipfile
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

from cb_inputs import BLOG, END, digest, opening, pin, posts

SOURCE = '1dfa6996663515a4baf8c1b71713ce8fe9a314b13778701447e4663bbc64c983'
FIRST_PERSON = {'i', 'me', 'my', 'mine', 'myself'}


def windows(words):
    start = 0
    for _ in range(20):
        if start == len(words):
            break
        limit = min(start + 150, len(words))
        end = limit
        if limit < len(words):
            end = next((i for i in range(limit, start, -1) if END.search(words[i-1])), limit)
        yield ' '.join(words[start:end])
        start = end


def line(stream, value):
    stream.write((json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n').encode())


def prepare(out, check):
    if pin(BLOG) != SOURCE:
        raise ValueError('Blog archive differs')
    directory = out/'spark-inputs'
    directory.mkdir()
    counts = Counter()
    shard = None
    seen = set()
    with zipfile.ZipFile(BLOG) as archive, ExitStack() as stack:
        joins = stack.enter_context(gzip.open(out/'local-joins.jsonl.gz', 'xb'))
        members = {}
        for m in archive.infolist():
            if m.filename.lower().endswith('.xml'):
                author = Path(m.filename).name.partition('.')[0]
                if not author.isdecimal() or author in members:
                    raise ValueError('Author key mismatch')
                members[author] = m
        for index, author in enumerate(sorted(members, key=lambda a:digest('TP43:23:'+a))):
            if index % 8 == 0:
                check()
            key = digest('TP43:23:'+author)
            rows = list(posts(archive.read(members[author])))
            qualifies = len(rows) >= 20 and len({day for _,day,_ in rows}) >= 5
            if qualifies:
                counts['qualifyingAuthors'] += 1
                counts['datedPosts'] += len(rows)
                counts['authorsAt80'] += int(len(rows) >= 80)
                counts['authorsAt40'] += int(len(rows) >= 40)
            else:
                rows = sorted(rows,key=lambda r:digest(f'TP43:post:{author}:{r[0]}'))[:40]
            for ordinal, day, raw in rows:
                lead = opening(raw)
                if not qualifies and not lead:
                    continue
                words = html.unescape(re.sub('<[^>]*>', ' ', raw.decode('utf8', errors='replace'))).split()
                spans = list(windows(words)) if qualifies else []
                keys = []
                for text in [lead, *spans]:
                    if not text:
                        keys.append(None)
                        continue
                    ident = digest(text)
                    keys.append(ident)
                    if ident in seen:
                        continue
                    if len(seen) % 8192 == 0:
                        if shard:
                            shard.close()
                        shard = stack.enter_context(gzip.open(directory/f'{len(seen):08d}.jsonl.gz','xb'))
                        check()
                    seen.add(ident)
                    line(shard, [ident,text])
                # Opening can end midway through the first 150 words. Count the disjoint suffix.
                tail = words[len(lead.split()):]
                first_person = sum(w.casefold() in FIRST_PERSON for w in re.findall(r"\b\w+\b",' '.join(tail)))
                line(joins,dict(id=digest(f'TP43:post:{author}:{ordinal}'), author=key, day=day,
                                qualifies=qualifies, opening=keys[0], windows=keys[1:],
                                words=len(words),suffixWords=len(tail),suffixFirstPerson=first_person))
                counts['qualifyingOpenings' if qualifies else 'referenceOpenings'] += bool(lead)
                counts['windows'] += len(spans)
    if counts['qualifyingAuthors'] != 5428:
        raise ValueError('Qualifying roster differs')
    return dict(source=SOURCE,counts=dict(counts,uniqueTexts=len(seen)),joinsPin=pin(out/'local-joins.jsonl.gz'),
                shards={p.name:pin(p) for p in sorted(directory.iterdir())})
