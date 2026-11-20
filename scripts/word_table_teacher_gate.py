"""Verify the original TP31 checks against saved, ordered responses."""
import json
from pathlib import Path

try:
    import tp31_teacher as contract  # flat committed Spark snapshot
except ModuleNotFoundError:
    from tompathy_engine.eval.readers import tp31_teacher as contract


def read(path):
    return json.loads(Path(path).read_bytes())


def values(folder, items):
    ordered = {}
    for index, item in enumerate(items):
        row = read(folder/f'row-{index:06d}.json')
        if row['index'] != index or row['id'] != item['id'] or item['id'] in ordered:
            raise ValueError('Saved teacher answers differ from the registered panel order')
        ordered[item['id']] = row['values']
    return ordered


def assess(first, second, whole, keys):
    if list(first) != list(second) or first.keys() & whole.keys():
        raise ValueError('Teacher panel identities differ or whole-document keys collide')
    available = {**first, **whole}
    groups = {name:[None if key is None else available[key] for key in ids]
              for name, ids in keys['groups'].items()}
    result = contract.teacher_checks(list(first.values()), list(second.values()), groups)
    pairs = [(first[i]['change'], flag) for i,flag in keys['story'].items() if first[i] is not None]
    result['storyAffected'] = {'n':len(keys['story']),'valid':len(pairs),
        'agreement':sum(a==b for a,b in pairs)/len(pairs) if pairs else None}
    result['withheldParentCounts'] = {name:ids.count(None) for name,ids in keys['groups'].items()}
    return result


def clearance(root, entry, digest):
    folder = root/'jobs'/'Q3'
    if not (folder/'complete.json').is_file():
        return False, 'Q3 has no completed teacher decision'
    receipt = read(folder/'receipt.json')
    gate_file = folder/'teacher-gate.json'
    if (read(folder/'complete.json')['receiptPin'] != digest(folder/'receipt.json')
            or receipt.get('status') != 'complete' or receipt.get('job') != 'Q3'
            or receipt['entry'] != entry['q3Entry'] or receipt['teacherGatePin'] != digest(gate_file)):
        raise ValueError('Teacher prerequisite receipt or source binding differs')
    gate = read(gate_file)
    if gate['modelB'] != entry['teacherPin'] or gate['subject'] != receipt['entry']:
        raise ValueError('Teacher decision refers to another reader or panel')
    return gate['checks']['qualifiesForStudent'] is True, digest(gate_file)
