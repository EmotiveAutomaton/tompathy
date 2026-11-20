"""Paired, development-only output-budget diagnostic for the workstation G3 reader."""
import json
import statistics
from collections import Counter
from pathlib import Path

import word_table_lane as lane
from word_table_rd2 import template

JOB = lane.G3_BUDGET
SPEC = 'G3-thinking-budget-plan.json'
PROTOCOL = 'G3_THINKING_BUDGET_PROTOCOL_2026-11-20.md'
ORIGINAL = 'd713e16e18dbf4cbc13830ab2e62b2b2995299ae'
PROMPT = '654862365fe30f177b9115616816ce6a7dbd652b3e25b24a16c3144b232cdf87'
SCHEMA = 'c2a379343bdbef69682ff5e4917386f597ca5b1a4be8dbf9deaf0e4f8075717e'
ORIGINAL_OPTIONS = {'temperature': 0, 'seed': 23, 'num_ctx': 4096, 'num_predict': 1024, 'num_thread': 2}


def select(items):
    if len(items) != 600 or len({r['id'] for r in items}) != 600:
        raise ValueError('Expected the 600 distinct G3 development reports')
    def key(index):
        report_id = items[index]['id']
        return lane.string_pin('G3:V2:3072:23:' + report_id), report_id
    return sorted(range(len(items)), key=key)[:20]


def prepare(root, destination):
    """Freeze the input before accessing any saved answer."""
    from word_table_register import prepare as freeze
    from word_table_register import save

    entry = lane.read(root/'queue.json')['jobs']['G3']
    if entry['commit'] != ORIGINAL:
        raise ValueError('Wrong G3 source run')
    roster, _ = lane.check_entry(root, 'G3', entry)
    indices = select(roster)
    items = [roster[i] for i in indices]
    lengths = lane.read(root/'inputs/RD2-lengths.json')['V2']
    required = max(lengths[item['id']] for item in items) + 3072 + 64
    if required > ORIGINAL_OPTIONS['num_ctx']:
        raise ValueError('A selected report exceeds the registered context reserve')
    destination.mkdir(parents=True, exist_ok=False)
    docs = Path(__file__).resolve().parents[1]/'docs'
    protocol = docs/PROTOCOL
    plan = {'originalEntry': entry, 'indices': indices, 'originalRows': 600, 'pairedRows': 20,
            'maxReservedContext': required, 'protocolPin': lane.pin(protocol)}
    save(destination/SPEC, plan)
    primary = JOB + '.json'
    save(destination/primary, items)
    files = {SPEC: destination/SPEC, primary: destination/primary, PROTOCOL: protocol}
    spec = {'modules': ['scripts/word_table_g3_budget.py', 'scripts/word_table_g3_follow.py',
                        'scripts/word_table_rd2.py'],
            'pins': {name: lane.pin(path) for name, path in files.items()},
            'jobs': {JOB: {'rows': 20, 'files': files}},
            'provenance': {'originalG3': ORIGINAL, 'variant': 'V2', 'developmentOnly': True,
                           'protocolPin': plan['protocolPin']}}
    return freeze(root, 'workstation', 'g3-budget', spec, destination/'extension')


def source_folder(root, after_resume):
    if after_resume not in (None, 'G3-resume-a', 'G3-resume-b'):
        raise ValueError('Unknown G3 predecessor')
    return root/'jobs'/(after_resume or 'G3')


def terminal_source(root, after_resume=None):
    parent = source_folder(root, after_resume)
    receipt = lane.read(parent/'receipt.json')
    terminal = lane.read(parent/'complete.json')
    owner = lane.read(parent/'owner.json')
    if (receipt['status'] != 'complete' or terminal['receiptPin'] != lane.pin(parent/'receipt.json')
            or owner != receipt['owner'] or owner['job'] != (after_resume or 'G3')
            or Path(owner['lock']).resolve() != (root/'gpu.lock').resolve()):
        raise ValueError('Original G3 completion or owner binding differs')
    if after_resume:
        from word_table_g3_resume import (
            FIRST_RETRY_RECEIPT,
            SECOND,
            SOURCE_RECEIPT,
            previous_retry,
            source,
        )
        prior = source(root)
        execution = lane.read(root/'inputs'/(after_resume+'-execution.json'))
        chain = receipt['continuation']
        if (owner['commit'] != execution['commit'] or chain['executionCommit'] != owner['commit']
                or chain['sourceReceiptPin'] != SOURCE_RECEIPT or receipt['entry'] != prior['entry']
                or chain['sourceOwner'] != prior['owner'] or chain['attempt'] != after_resume
                or chain['restoredInventoryPin'] != lane.pin(parent/'restored.json')
                or set(receipt['roles']) != {f'V{i}' for i in range(6)}
                or any(v['rows'] != 600 for v in receipt['roles'].values())):
            raise ValueError('Completed continuation differs from its pinned original')
        if after_resume == SECOND:
            previous_retry(root)
            if chain['priorEngineeringReceiptPin'] != FIRST_RETRY_RECEIPT:
                raise ValueError('Completed continuation lost the first engineering retry')
    elif owner['commit'] != ORIGINAL:
        raise ValueError('Original G3 execution differs')
    return receipt, terminal['receiptPin']


def paired_inputs(root, items, after_resume=None):
    receipt, receipt_pin = terminal_source(root, after_resume)
    plan = lane.read(root/'inputs'/SPEC)
    source = receipt['entry']
    if (source != plan['originalEntry'] or source != lane.read(root/'queue.json')['jobs']['G3']
            or lane.pin(root/'inputs'/PROTOCOL) != plan['protocolPin']):
        raise ValueError('Original entry or diagnostic registration differs')
    roster, _ = lane.check_entry(root, 'G3', source)
    indices = select(roster)
    if indices != plan['indices'] or items != [roster[i] for i in indices]:
        raise ValueError('Sample differs from the registered hash selection')
    parent = source_folder(root, after_resume)
    artifacts = parent/'artifacts.json'
    if lane.pin(artifacts) != receipt['artifactsPin']:
        raise ValueError('Original G3 artifact inventory differs')
    inventory = lane.read(artifacts)['files']
    baseline = receipt['roles']['V2']
    if baseline['rows'] != 600 or baseline['binding']['variant'] != 'V2':
        raise ValueError('Original V2 is incomplete')
    pins = {}
    for i in indices:
        name = f'V2/W/row-{i:06d}.json'
        pins[name] = lane.pin(parent/name)
        if pins[name] != inventory[name]:
            raise ValueError('Original saved response differs from its terminal inventory')
        if after_resume and pins[name] != lane.pin(root/'jobs/G3'/name):
            raise ValueError('Continued V2 response differs from its original bytes')
        saved = lane.read(parent/name)
        if (saved['index'] != i or saved['id'] != roster[i]['id'] or saved['binding'] != baseline['binding']
                or saved['response']['prompt_eval_count'] + 3072 + 64 > 4096):
            raise ValueError('Original row identity, binding or measured input length differs')
    validator = template(lane.read(root/'inputs/RD2-prompts.json')['V2'])
    if after_resume:
        early = root.parent/'g3-budget-registration-a/paired-baseline.json'
        if (lane.pin(early) != '9d2f10fc976d34f07fd37db1abbcd63b13a57c605b92f6bba26204eb1e3548cb'
                or pins != {'V2/W/'+name:digest for name,digest in lane.read(early)['originalResponsePins'].items()}):
            raise ValueError('Preserved twenty baseline answers differ from their pre-recovery record')
    if lane.pin(Path(__file__).with_name('word_table_rd2.py')) != source['codePins']['word_table_rd2.py']:
        raise ValueError('The diagnostic must use the original V2 validator')
    if lane.string_pin(validator[0]) != PROMPT or validator[3] is not True:
        raise ValueError('Original V2 definition differs')
    return indices, baseline['binding'], pins, receipt_pin, validator


def verify_binding(binding, cap):
    if (binding['modelPin'] != lane.W[1] or binding['role'] != 'W' or binding['variant'] != 'V2'
            or binding['think'] is not True or binding['promptPin'] != PROMPT or binding['schemaPin'] != SCHEMA
            or binding['options'] != {**ORIGINAL_OPTIONS, 'num_predict': cap}):
        raise ValueError('Reader, prompt, schema, thinking or generation settings differ')


def observe(row, index, report_id, binding, validate):
    if (row['index'], row['id'], row['binding']) != (index, report_id, binding):
        raise ValueError('Response differs from its registered position or protocol')
    raw = row['response']
    if not raw or raw.get('model') != lane.W[0] or raw.get('done') is not True:
        raise ValueError('Missing completed inference envelope')
    final = raw['response']
    parsed = None
    if not final.strip():
        outcome = 'empty'
    else:
        try:
            parsed = validate(json.loads(final))
        except ValueError:
            outcome = 'malformedJson'
        else:
            outcome = 'valid' if parsed is not None else 'rejectedValues'
    if parsed != row['values']:
        raise ValueError('Replayed validity disagrees with saved values')
    return {'outcome': outcome, 'reason': raw['done_reason'], 'tokens': raw['eval_count'],
            'seconds': row['seconds'], 'generationSeconds': raw['eval_duration']/1e9}


def summarize(rows, cap):
    outcomes = Counter(r['outcome'] for r in rows)
    tokens = [r['tokens'] for r in rows]
    return {'limit': cap, 'attempted': len(rows),
            **{key: outcomes[key] for key in ('valid', 'empty', 'malformedJson', 'rejectedValues')},
            'doneReasons': dict(Counter(r['reason'] for r in rows)),
            'atTokenCap': tokens.count(cap), 'totalOutputTokens': sum(tokens),
            'medianOutputTokens': statistics.median(tokens) if rows else None,
            'generationSeconds': sum(r['generationSeconds'] for r in rows),
            'wallSecondsInCalls': sum(r['seconds'] for r in rows)}


def compare(root, out, items, binding, after_resume=None):
    indices, old, pins, source_pin, definition = paired_inputs(root, items, after_resume)
    verify_binding(old, 1024)
    base = out/'W'
    protocol = lane.read(base/'protocol.json')
    new = {k: v for k, v in protocol.items() if k not in ('prompt', 'schema', 'secondKey')}
    verify_binding(new, 3072)
    if (any(new.get(k) != v for k, v in binding.items()) or lane.string_pin(protocol['prompt']) != PROMPT
            or lane.string_pin(json.dumps(protocol['schema'], sort_keys=True)) != SCHEMA):
        raise ValueError('New answers have a different input or response contract')
    rows = sorted(base.glob('row-*.json'))
    if len(rows) > len(items):
        raise ValueError('Unexpected extra diagnostic responses')
    arms = ([], [])
    pairs = Counter()
    for j, path in enumerate(rows):
        if path.name != f'row-{j:06d}.json':
            raise ValueError('Diagnostic response sequence has a gap')
        i, report_id = indices[j], items[j]['id']
        saved = lane.read(root/'jobs/G3/V2/W'/f'row-{i:06d}.json')
        low = observe(saved, i, report_id, old, definition[2])
        high = observe(lane.read(path), j, report_id, new, definition[2])
        arms[0].append(low)
        arms[1].append(high)
        key = {(True, True): 'bothValid', (False, True): 'newlyValid',
               (True, False): 'lostValidity', (False, False): 'bothInvalid'}
        pairs[key[low['outcome'] == 'valid', high['outcome'] == 'valid']] += 1
    result = {'study': JOB, 'protocolPin': lane.pin(root/'inputs'/PROTOCOL),
              'originalReceiptPin': source_pin, 'selectionPin': lane.pin(root/'inputs'/(JOB+'.json')),
              'modelPin': lane.W[1], 'registered': len(items), 'paired': len(rows),
              'baseline': summarize(arms[0], 1024), 'higher': summarize(arms[1], 3072),
              'pairs': {k: pairs[k] for k in ('bothValid', 'newlyValid', 'lostValidity', 'bothInvalid')}}
    if after_resume:
        result['priorAttemptReceiptPin'] = lane.pin(root/'jobs/G3/receipt.json')
        if after_resume == 'G3-resume-b':
            result['priorEngineeringReceiptPin'] = lane.pin(root/'jobs/G3-resume-a/receipt.json')
    return result, pins


def run(root, out, items, binding, guard, rate, after_resume=None):
    from word_table_g3_follow import native_alive

    guard.check()
    if native_alive(lane.read(source_folder(root, after_resume)/'owner.json')):
        raise RuntimeError('Original G3 process still owns its native identity')
    _, old, before, _, definition = paired_inputs(root, items, after_resume)
    verify_binding(old, 1024)
    lengths = lane.read(root/'inputs/RD2-lengths.json')['V2']
    if any(lengths[r['id']] + 3072 + 64 > 4096 for r in items):
        raise ValueError('Registered larger output reserve exceeds context')
    directory = out/'comparison'
    directory.mkdir(exist_ok=True)
    pin_file = directory/'baseline-pins.json'
    if pin_file.exists() and lane.read(pin_file) != before:
        raise ValueError('Saved baseline pins changed between admissions')
    if not pin_file.exists():
        lane.write(pin_file, before)
    result = rate(root, out, items, 'W', JOB, {**binding, 'variant': 'V2'}, guard,
                  template=definition, token_lengths=lengths)
    comparison, after = compare(root, out, items, binding, after_resume)
    if comparison['paired'] != 20 or after != before or comparison['higher']['valid'] != result['valid']:
        raise ValueError('Paired coverage, original bytes or saved validity differ')
    lane.write(directory/'aggregate.json', comparison)
    return result
