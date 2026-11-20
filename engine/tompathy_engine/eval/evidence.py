"""Append-only aggregate evidence rows, independent of scientific admission."""
import json
import re
from pathlib import Path

FIELDS = {'id', 'date', 'question', 'data', 'estimate', 'interval', 'bar',
          'verdict', 'limit', 'claims', 'family'}
CLAIMS = {f'{prefix}{i}' for prefix, count in
          (('T', 10), ('N', 5), ('A', 3), ('S', 4), ('W', 1), ('AT', 2), ('TB', 1),
           ('P', 4), ('M', 4), ('LP', 15)) for i in range(1, count+1)}


def append(path, row):
    """Retrying an identical landing is harmless; changing a row is refused."""
    if set(row) != FIELDS or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{1,120}', row['id']):
        raise ValueError('Unexpected ledger fields or result ID')
    if not row['claims'] or not set(row['claims']) <= CLAIMS:
        raise ValueError('Unknown claim; need codes are not claim IDs')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row['date']):
        raise ValueError('Landing date required')
    for key in ('question', 'data', 'bar', 'verdict', 'limit', 'family'):
        if not isinstance(row[key], str) or not row[key].strip():
            raise ValueError('Missing public record text')
    payload = json.dumps(row, ensure_ascii=False, allow_nan=False, sort_keys=True)
    path = Path(path)
    previous = path.read_bytes() if path.exists() else b''
    if previous and not previous.endswith(b'\n'):
        raise ValueError('Preserve malformed previous ledger')
    for line in previous.decode('utf8').splitlines():
        old = json.loads(line)
        if old['id'] == row['id']:
            if old == row:
                return 'unchanged'
            raise ValueError('Result ID already exists; append a separately named correction')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('ab') as stream:
        stream.write((payload+'\n').encode('utf8'))
        stream.flush()
    if path.read_bytes() != previous+(payload+'\n').encode('utf8'):
        raise RuntimeError('Ledger append verification failed')
    return 'appended'
