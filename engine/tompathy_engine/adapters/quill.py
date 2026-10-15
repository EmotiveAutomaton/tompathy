# Ported from Sounding Line, copyright 2026 Abraham Haskins (MIT).
# See engine/NOTICE-SOUNDING-LINE.txt and reference-sources.json.
import json

def units(text):
    if not isinstance(text, str):
        raise ValueError('non-text document or insertion')
    raw = text.encode('utf-16-le')
    return [int.from_bytes(raw[i:i+2], 'little') for i in range(0, len(raw), 2)]


def text_of(values):
    return b''.join(v.to_bytes(2, 'little') for v in values).decode('utf-16-le')


def delta_ops(value):
    if value in ('', None):
        return []
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict) or set(value) != {'ops'} or not isinstance(value['ops'], list):
        raise ValueError('invalid Quill change delta')
    for op in value['ops']:
        if not isinstance(op, dict) or len(set(op) & {'retain', 'delete', 'insert'}) != 1:
            raise ValueError('delta operation must have one action')
        if set(op) - {'retain', 'delete', 'insert', 'attributes'}:
            raise ValueError('unknown delta operation')
    return value['ops']


def apply_delta(document, provenance, value, *, insertion_owner=None, watched_owner=None):
    """All indexes are UTF-16 code units, as in the released Quill JavaScript.

    Human deletion of any owned character is an edit, including a deletion starting
    before its span. Insertion strictly inside two owned neighbors is an edit;
    appending outside that span is continuation. Earlier unrelated edits shift the
    provenance with the surviving characters. No fuzzy repair of malformed deltas.
    """
    if len(document) != len(provenance):
        raise ValueError('provenance/document disagreement')
    out, owners, position, edited = [], [], 0, False
    for op in delta_ops(value):
        if 'insert' in op:
            new = units(op['insert'])
            if watched_owner is not None and 0 < position < len(document):
                edited |= provenance[position-1] == provenance[position] == watched_owner and bool(new)
            out.extend(new); owners.extend([insertion_owner] * len(new))
        else:
            action = 'retain' if 'retain' in op else 'delete'
            count = op[action]
            if type(count) is not int or count < 0 or position + count > len(document):
                raise ValueError('invalid UTF-16 retain/delete boundary')
            if action == 'retain':
                out.extend(document[position:position+count]); owners.extend(provenance[position:position+count])
            elif watched_owner is not None:
                edited |= watched_owner in provenance[position:position+count]
            position += count
    out.extend(document[position:]); owners.extend(provenance[position:])
    text_of(out)  # An edit cannot silently leave half of a surrogate pair.
    return out, owners, edited


def suggestions(value):
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        raise ValueError('invalid offered suggestion support')
    out = []
    for option in value:
        if not isinstance(option, dict) or type(option.get('index')) is not int:
            raise ValueError('invalid suggestion index')
        if not isinstance(option.get('original'), str) or not isinstance(option.get('trimmed'), str):
            raise ValueError('missing original/display suggestion text')
        out.append({k: option[k] for k in ('index', 'original', 'trimmed')})
    if len({r['index'] for r in out}) != len(out):
        raise ValueError('repeated suggestion index')
    return out
