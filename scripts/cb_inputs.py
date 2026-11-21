"""Private CB source rosters; only opaque report IDs and texts go to GPU readers."""
import csv
import hashlib
import html
import json
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE = Path('.local/person-teacher/cb')
BLOG = Path('.local/readers/data/blogs-b/blogs.zip')
PACKET = Path('TOMPATHY_0.3_ENGINE_ADDENDUM_2_2026-11-21.md')
MARKERS = re.compile(rb'<date>\s*([^<>]*)\s*</date>|<post>(.*?)</post>', re.I | re.S)
END = re.compile(r'''[.!?]+["'”’)]*(?=\s|$)''')


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def pin(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, value):
    data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    path = BASE/name
    if path.exists():
        if pin(path) != hashlib.sha256(data).hexdigest():
            raise ValueError('Roster changed: '+name)
    else:
        with path.open('xb') as stream:
            stream.write(data)
    return pin(path)


def posts(data):
    day = None
    ordinal = 0
    for m in MARKERS.finditer(data):
        if m[1] is not None:
            try:
                day = datetime.strptime(m[1].strip().decode('ascii'), '%d,%B,%Y').date().isoformat()
            except (ValueError, UnicodeError):
                day = None
        else:
            ordinal += 1
            if day and m[2].strip():
                yield ordinal, day, m[2]


def opening(raw):
    text = html.unescape(re.sub(r'<[^>]*>', ' ', raw.decode('utf8', errors='replace')))
    words = text.split()
    if len(words) < 30:
        return ''
    first = ' '.join(words[:150])
    ends = list(END.finditer(first))
    return first[:ends[-1].end()] if ends else ''


def blogs():
    if pin(BLOG) != '1dfa6996663515a4baf8c1b71713ce8fe9a314b13778701447e4663bbc64c983':
        raise ValueError('Blog release changed')
    with zipfile.ZipFile(BLOG) as z:
        members = {}
        eligible = []
        for m in z.infolist():
            if not m.filename.lower().endswith('.xml'):
                continue
            author = Path(m.filename).name.split('.', 1)[0]
            if not author.isdecimal() or author in members:
                raise ValueError('Unrecognized author')
            members[author] = m
            dates = [day for _, day, _ in posts(z.read(m))]
            if len(dates) >= 20 and len(set(dates)) >= 5:
                eligible.append(author)
        chosen = sorted(eligible, key=lambda a: digest('TP43:23:'+a))[:2000]
        if len(chosen) != 2000:
            raise ValueError('Insufficient eligible authors')
        metadata, gpu, boundaries = [], [], []
        for author in chosen:
            rows = list(posts(z.read(members[author])))
            def post_key(row):
                return digest(f'TP43:post:{author}:{row[0]}')
            for ordinal, day, raw in sorted(rows, key=post_key)[:40]:
                text = opening(raw)
                if text:
                    key = digest(f'TP43:post:{author}:{ordinal}')
                    metadata.append([key, digest('TP43:23:'+author), day])
                    gpu.append(dict(id=key, text=text))
            boundaries.append(len(gpu))
    return {'posts': save('blogs.json', gpu), 'metadata': save('blog-meta.json', metadata),
            'boundaries': save('boundaries.json', boundaries), 'chosen': save('selected.json', chosen),
            'eligible': len(eligible), 'authors': len(chosen), 'rows': len(gpu)}


def isear():
    with (BASE/'isear.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = sorted(csv.DictReader(stream), key=lambda r: tuple(r[k] for k in ('COUN','CITY','SUBJ','EMOT')))
    reports, metadata, people = [], [], Counter()
    for r in rows:
        person = digest(json.dumps([r[k] for k in ('COUN','CITY','SUBJ')]))
        key = digest('TP44:'+person+':'+r['EMOT'])
        people[person] += 1
        reports.append(dict(id=key, text=r['SIT'].strip()))
        metadata.append([key, person, r['COUN'], r['CITY'], r['EMOT'], r['PLEA'], r['EXPC'], r['INTS'], r['CAUS']])
    if len({r['id'] for r in reports}) != len(reports) or not all(r['text'] for r in reports):
        raise ValueError('Duplicate person/feeling or empty ISEAR report')
    return {'reports': save('isear.json', reports), 'metadata': save('isear-meta.json', metadata),
            'rows': len(rows), 'personSizeCounts': dict(Counter(people.values()))}


if __name__ == '__main__':
    print('CB manifest', save('inputs.json', dict(packet=pin(PACKET), isear=isear(), blogs=blogs())))
